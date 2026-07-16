from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any
from datetime import datetime, timezone
from app.models import (
    Incident, RescueTeam, Allocation, ReliefRequest, ReliefDispatch, 
    Warehouse, EmergencyShelter, ShelterRequest, ShelterReservation, 
    ShelterRouteCondition, OperationalAlert, AlertStatus, AlertSeverity,
    DispatchStatus, ShelterReservationStatus
)
from app.schemas import (
    CommandDashboardSummary, PendingDecisionResponse, 
    IncidentOperationalSummary, TimelineEvent,
    ActiveIncident, ResourceStatusSummary, ResourceStatusItem, RecentActivityItem, CommandMapOverview
)

def get_dashboard_summary(db: Session) -> CommandDashboardSummary:
    now = datetime.now(timezone.utc)
    
    # Incidents
    active_incs = db.query(Incident).filter(Incident.status.in_(["reported", "verified", "assigned", "in_progress"]))
    total_active_incidents = active_incs.count()
    critical_incidents = active_incs.filter(Incident.priority_level == "critical").count()
    high_priority_incidents = active_incs.filter(Incident.priority_level == "high").count()
    
    # Rescue
    active_allocs = db.query(Allocation).filter(Allocation.status == "approved").count()
    
    assigned_inc_ids = db.query(Allocation.incident_id).filter(Allocation.status == "approved").subquery()
    unassigned_incidents = active_incs.filter(Incident.id.notin_(assigned_inc_ids)).count()
    
    incidents_awaiting_rescue = db.query(OperationalAlert).filter(
        OperationalAlert.category == "officer_approval_pending",
        OperationalAlert.status == AlertStatus.active
    ).count() # simplistic, will refine later
    
    rescue_reallocations_pending = db.query(OperationalAlert).filter(OperationalAlert.category == "rescue_route_blocked", OperationalAlert.status == AlertStatus.active).count()
    
    # Relief
    active_relief = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["pending", "partially_allocated"])).count()
    relief_shortages = db.query(OperationalAlert).filter(OperationalAlert.category == "relief_shortage", OperationalAlert.status == AlertStatus.active).count()
    
    dispatches_preparing = db.query(ReliefDispatch).filter(ReliefDispatch.status == DispatchStatus.preparing).count()
    dispatches_in_transit = db.query(ReliefDispatch).filter(ReliefDispatch.status == DispatchStatus.dispatched).count()
    low_stock_alerts = db.query(OperationalAlert).filter(OperationalAlert.category == "warehouse_low_stock", OperationalAlert.status == AlertStatus.active).count()
    
    # Shelter
    active_shelter = db.query(ShelterRequest).filter(ShelterRequest.status.in_(["pending", "partially_allocated"])).count()
    
    # Uncovered displaced people
    s_reqs = db.query(ShelterRequest).filter(ShelterRequest.status != "allocated").all()
    uncovered = sum(sr.total_displaced_people for sr in s_reqs)
    
    res_in_transit = db.query(ShelterReservation).filter(ShelterReservation.status == ShelterReservationStatus.in_transit).all()
    transit_people = sum(r.reserved_people for r in res_in_transit)
    
    shelters = db.query(EmergencyShelter).all()
    high_risk_shelters = sum(1 for s in shelters if s.total_capacity > 0 and (s.occupied_capacity + s.reserved_capacity)/s.total_capacity >= 0.85)
    
    # Routes
    blocked_routes = db.query(ShelterRouteCondition).filter(ShelterRouteCondition.is_blocked == 1).count()
    high_risk_routes = db.query(ShelterRouteCondition).filter(ShelterRouteCondition.risk_level == "high").count()
    
    pending_decisions = db.query(OperationalAlert).filter(
        OperationalAlert.category == "officer_approval_pending",
        OperationalAlert.status == AlertStatus.active
    ).count()
    
    return CommandDashboardSummary(
        total_active_incidents=total_active_incidents,
        critical_incidents=critical_incidents,
        high_priority_incidents=high_priority_incidents,
        unassigned_incidents=unassigned_incidents,
        incidents_awaiting_rescue=incidents_awaiting_rescue,
        active_rescue_allocations=active_allocs,
        rescue_reallocations_pending=rescue_reallocations_pending,
        active_relief_requests=active_relief,
        relief_shortages=relief_shortages,
        dispatches_preparing=dispatches_preparing,
        dispatches_in_transit=dispatches_in_transit,
        low_stock_alerts=low_stock_alerts,
        active_shelter_requests=active_shelter,
        uncovered_displaced_people=uncovered,
        shelter_reservations_in_transit=transit_people,
        high_overcrowding_risk_shelters=high_risk_shelters,
        blocked_routes=blocked_routes,
        high_risk_routes=high_risk_routes,
        pending_officer_decisions=pending_decisions
    )

def get_pending_decisions(db: Session) -> List[PendingDecisionResponse]:
    # Pending decisions are generated into a unified queue from various sources.
    # For this implementation, we will query alerts of specific categories, or directly query missing allocations.
    decisions = []
    
    # Unassigned Critical Incidents -> Decision to allocate
    unassigned = db.query(Incident).filter(Incident.status.in_(["pending", "active"])).all()
    for inc in unassigned:
        alloc = db.query(Allocation).filter(Allocation.incident_id == inc.id, Allocation.status == "approved").first()
        if not alloc:
            waiting = int((datetime.now(timezone.utc) - inc.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60)
            decisions.append(PendingDecisionResponse(
                id=f"rescue_alloc_{inc.id}",
                decision_type="initial_rescue_allocation",
                incident_id=inc.id,
                incident_title=inc.title,
                priority=inc.priority_level,
                resource_type="rescue_team",
                resource_id=None,
                reason="Incident requires rescue team",
                recommendation_summary="Recommend generating allocation",
                waiting_duration_minutes=waiting,
                severity="critical" if inc.priority_level == "critical" else "high",
                action_route=f"/incidents/{inc.id}/rescue",
                created_at=inc.created_at
            ))
            
    # Rescue reallocation triggers (e.g. from Route conditions)
    # Placeholder for logic extracting reallocations
    
    # Sort primarily by severity/criticality, then priority, then waiting
    priority_val = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    decisions.sort(key=lambda x: (priority_val.get(x.severity, 4), priority_val.get(x.priority, 4), -x.waiting_duration_minutes))
    
    return decisions

def get_incident_operational_summary(db: Session, incident_id: int) -> IncidentOperationalSummary:
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        return None
        
    waiting = int((datetime.now(timezone.utc) - inc.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60)
    
    # Rescue
    alloc = db.query(Allocation).filter(Allocation.incident_id == inc.id, Allocation.status == "approved").first()
    assigned_team = None
    if alloc:
        team = db.query(RescueTeam).filter(RescueTeam.id == alloc.rescue_team_id).first()
        if team:
            assigned_team = team.name
            
    # Summary
    summary = IncidentOperationalSummary(
        incident_id=inc.id,
        title=inc.title,
        incident_type=inc.incident_type,
        location=f"{inc.latitude}, {inc.longitude}",
        rule_priority=inc.priority_level or "unassigned",
        ml_priority=inc.ml_priority_level,
        rule_ml_agreement=(inc.priority_level == inc.ml_priority_level) if inc.ml_priority_level else True,
        current_status=inc.status,
        waiting_duration_minutes=waiting,
        last_updated=inc.updated_at,
        assigned_team=assigned_team,
        allocation_status=alloc.status if alloc else "unassigned"
    )
    return summary

def get_incident_timeline(db: Session, incident_id: int) -> List[TimelineEvent]:
    events = []
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc:
        events.append(TimelineEvent(
            id=f"inc_created_{inc.id}",
            timestamp=inc.created_at,
            event_category="incident_creation",
            title="Incident Created",
            description=f"{inc.title} created.",
            source="system",
            status=inc.status
        ))
        
    # Allocations
    allocs = db.query(Allocation).filter(Allocation.incident_id == incident_id).all()
    for a in allocs:
        events.append(TimelineEvent(
            id=f"alloc_{a.id}",
            timestamp=a.created_at,
            event_category="rescue_allocation",
            title="Rescue Team Assigned" if a.status == "assigned" else "Rescue Team Reallocated",
            description=f"Team {a.rescue_team_id} assigned.",
            source="officer",
            status=a.status
        ))
        
    events.sort(key=lambda x: x.timestamp, reverse=True)
    return events


def get_active_incidents(
    db: Session,
    priority: Optional[str] = None,
    incident_type: Optional[str] = None,
    incident_status: Optional[str] = None,
    location: Optional[str] = None,
    rescue_status: Optional[str] = None
) -> List[ActiveIncident]:
    query = db.query(Incident).filter(
        Incident.status.in_(["reported", "verified", "assigned", "in_progress"])
    )
    
    if priority:
        query = query.filter(Incident.priority_level == priority)
    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)
    if incident_status:
        query = query.filter(Incident.status == incident_status)
    if location:
        query = query.filter(
            or_(
                Incident.location_name.ilike(f"%{location}%"),
                Incident.latitude.is_(None)
            )
        )
    
    incidents = query.order_by(Incident.created_at.desc()).all()
    result = []
    
    for inc in incidents:
        waiting = int((datetime.now(timezone.utc) - inc.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60)
        
        # Get rescue status
        alloc = db.query(Allocation).filter(
            Allocation.incident_id == inc.id,
            Allocation.status == "approved"
        ).first()
        rescue_status_val = "assigned" if alloc else "unassigned"
        
        if rescue_status and rescue_status != rescue_status_val:
            continue
        
        # Get relief status
        relief_req = db.query(ReliefRequest).filter(
            ReliefRequest.incident_id == inc.id
        ).order_by(ReliefRequest.created_at.desc()).first()
        relief_status_val = relief_req.status if relief_req else None
        
        # Get shelter status
        shelter_req = db.query(ShelterRequest).filter(
            ShelterRequest.incident_id == inc.id
        ).order_by(ShelterRequest.created_at.desc()).first()
        shelter_status_val = shelter_req.status if shelter_req else None
        
        # Get active alert count
        active_alerts = db.query(OperationalAlert).filter(
            OperationalAlert.incident_id == inc.id,
            OperationalAlert.status == AlertStatus.active
        ).count()
        
        # Get latest event
        latest_alloc = db.query(Allocation).filter(
            Allocation.incident_id == inc.id
        ).order_by(Allocation.created_at.desc()).first()
        latest_event = None
        if latest_alloc:
            latest_event = f"Rescue {latest_alloc.status}"
        
        result.append(ActiveIncident(
            incident_id=inc.id,
            title=inc.title,
            incident_type=inc.incident_type,
            location=f"{inc.latitude:.4f}, {inc.longitude:.4f}",
            latitude=inc.latitude,
            longitude=inc.longitude,
            severity=inc.severity.value if hasattr(inc.severity, 'value') else inc.severity,
            rule_priority=inc.priority_level,
            ml_priority=inc.ml_priority_level,
            current_status=inc.status.value if hasattr(inc.status, 'value') else inc.status,
            rescue_status=rescue_status_val,
            relief_status=relief_status_val,
            shelter_status=shelter_status_val,
            active_alert_count=active_alerts,
            waiting_duration_minutes=waiting,
            latest_event=latest_event
        ))
    
    return result


def get_resource_status(
    db: Session,
    resource_type: Optional[str] = None,
    status: Optional[str] = None
) -> ResourceStatusSummary:
    from app.models import (
        DeliveryVehicle, ReliefInventory, ShelterRouteCondition,
        VehicleAvailability, RouteRisk
    )
    
    summary = ResourceStatusSummary()
    
    # Rescue Teams
    teams = db.query(RescueTeam).all()
    for t in teams:
        s = t.availability_status.value if hasattr(t.availability_status, 'value') else t.availability_status
        if s == "available":
            summary.rescue_teams_available += 1
        elif s == "assigned":
            summary.rescue_teams_assigned += 1
        else:
            summary.rescue_teams_unavailable += 1
        
        if resource_type == "rescue_team":
            if status is None or s == status:
                summary.resources.append(ResourceStatusItem(
                    resource_type="rescue_team",
                    resource_id=t.id,
                    resource_name=t.name,
                    status=s
                ))
    
    # Warehouses
    warehouses = db.query(Warehouse).all()
    for w in warehouses:
        s = w.operating_status.value if hasattr(w.operating_status, 'value') else w.operating_status
        if s == "active":
            summary.warehouses_active += 1
        elif s == "limited":
            summary.warehouses_limited += 1
        else:
            summary.warehouses_unavailable += 1
        
        if resource_type == "warehouse":
            if status is None or s == status:
                summary.resources.append(ResourceStatusItem(
                    resource_type="warehouse",
                    resource_id=w.id,
                    resource_name=w.name,
                    status=s
                ))
    
    # Delivery Vehicles
    vehicles = db.query(DeliveryVehicle).all()
    for v in vehicles:
        s = v.availability_status.value if hasattr(v.availability_status, 'value') else v.availability_status
        if s == "available":
            summary.vehicles_available += 1
        elif s == "assigned":
            summary.vehicles_assigned += 1
        else:
            summary.vehicles_unavailable += 1
        
        if resource_type == "vehicle":
            if status is None or s == status:
                summary.resources.append(ResourceStatusItem(
                    resource_type="vehicle",
                    resource_id=v.id,
                    resource_name=v.name,
                    status=s
                ))
    
    # Low Stock Items
    low_stock = db.query(ReliefInventory).filter(
        ReliefInventory.quantity_available < ReliefInventory.reorder_level
    ).count()
    summary.low_stock_items = low_stock
    
    # Shelters
    shelters = db.query(EmergencyShelter).all()
    for s in shelters:
        os_val = s.operating_status.value if hasattr(s.operating_status, 'value') else s.operating_status
        if os_val == "open":
            summary.shelters_open += 1
        elif os_val == "limited":
            summary.shelters_limited += 1
        elif os_val == "full":
            summary.shelters_full += 1
        else:
            summary.shelters_unavailable += 1
        
        if s.total_capacity > 0:
            pct = (s.occupied_capacity + s.reserved_capacity) / s.total_capacity
            if pct >= 0.85:
                summary.high_overcrowding_risk += 1
        
        if resource_type == "shelter":
            if status is None or os_val == status:
                pct = (s.occupied_capacity + s.reserved_capacity) / s.total_capacity if s.total_capacity > 0 else 0
                summary.resources.append(ResourceStatusItem(
                    resource_type="shelter",
                    resource_id=s.id,
                    resource_name=s.name,
                    status=os_val,
                    details=f"Capacity: {pct*100:.1f}%"
                ))
    
    # Route Conditions
    summary.blocked_routes = db.query(ShelterRouteCondition).filter(
        ShelterRouteCondition.is_blocked == 1
    ).count()
    summary.high_risk_routes = db.query(ShelterRouteCondition).filter(
        ShelterRouteCondition.risk_level == RouteRisk.high
    ).count()
    
    return summary


def get_recent_activity(
    db: Session,
    limit: int = 50,
    resource_type: Optional[str] = None,
    incident_id: Optional[int] = None
) -> List[RecentActivityItem]:
    events = []
    
    # Incident events
    if resource_type is None or resource_type == "incident":
        incidents_query = db.query(Incident)
        if incident_id:
            incidents_query = incidents_query.filter(Incident.id == incident_id)
        incidents = incidents_query.order_by(Incident.created_at.desc()).limit(limit).all()
        for inc in incidents:
            events.append(RecentActivityItem(
                id=f"inc_{inc.id}",
                timestamp=inc.created_at,
                resource_type="incident",
                event_category="incident_creation",
                title=f"Incident Created: {inc.title}",
                description=inc.description[:100] if inc.description else "",
                source="system",
                incident_id=inc.id,
                status=inc.status.value if hasattr(inc.status, 'value') else inc.status
            ))
    
    # Allocation events
    if resource_type is None or resource_type == "allocation":
        allocs_query = db.query(Allocation)
        if incident_id:
            allocs_query = allocs_query.filter(Allocation.incident_id == incident_id)
        allocs = allocs_query.order_by(Allocation.created_at.desc()).limit(limit).all()
        for a in allocs:
            events.append(RecentActivityItem(
                id=f"alloc_{a.id}",
                timestamp=a.created_at,
                resource_type="allocation",
                event_category="rescue_allocation",
                title=f"Allocation: {a.status}",
                description=f"Team {a.rescue_team_id} - Incident {a.incident_id}",
                source="officer",
                incident_id=a.incident_id,
                status=a.status
            ))
    
    # Relief Request events
    if resource_type is None or resource_type == "relief_request":
        rel_req_query = db.query(ReliefRequest)
        if incident_id:
            rel_req_query = rel_req_query.filter(ReliefRequest.incident_id == incident_id)
        rel_reqs = rel_req_query.order_by(ReliefRequest.created_at.desc()).limit(limit).all()
        for r in rel_reqs:
            events.append(RecentActivityItem(
                id=f"rel_req_{r.id}",
                timestamp=r.created_at,
                resource_type="relief_request",
                event_category="relief_request",
                title=f"Relief Request: {r.status}",
                description=f"Incident {r.incident_id} - {r.total_people} people",
                source="system",
                incident_id=r.incident_id,
                status=r.status
            ))
    
    # Relief Dispatch events
    if resource_type is None or resource_type == "relief_dispatch":
        dispatches_query = db.query(ReliefDispatch)
        if incident_id:
            dispatches_query = dispatches_query.join(ReliefRequest).filter(ReliefRequest.incident_id == incident_id)
        dispatches = dispatches_query.order_by(ReliefDispatch.created_at.desc()).limit(limit).all()
        for d in dispatches:
            events.append(RecentActivityItem(
                id=f"dispatch_{d.id}",
                timestamp=d.created_at,
                resource_type="relief_dispatch",
                event_category="relief_dispatch",
                title=f"Dispatch: {d.status}",
                description=f"Warehouse {d.warehouse_id} - {d.total_allocated_units} units",
                source="officer" if d.approved_at else "system",
                status=d.status
            ))
    
    # Shelter Request events
    if resource_type is None or resource_type == "shelter_request":
        shel_req_query = db.query(ShelterRequest)
        if incident_id:
            shel_req_query = shel_req_query.filter(ShelterRequest.incident_id == incident_id)
        shel_reqs = shel_req_query.order_by(ShelterRequest.created_at.desc()).limit(limit).all()
        for s in shel_reqs:
            events.append(RecentActivityItem(
                id=f"shelter_req_{s.id}",
                timestamp=s.created_at,
                resource_type="shelter_request",
                event_category="shelter_request",
                title=f"Shelter Request: {s.status}",
                description=f"Incident {s.incident_id} - {s.total_displaced_people} people",
                source="system",
                incident_id=s.incident_id,
                status=s.status
            ))
    
    # Shelter Reservation events
    if resource_type is None or resource_type == "shelter_reservation":
        res_query = db.query(ShelterReservation)
        res_query = res_query.join(ShelterRequest).filter(ShelterRequest.incident_id == incident_id) if incident_id else res_query
        reservations = res_query.order_by(ShelterReservation.created_at.desc()).limit(limit).all()
        for r in reservations:
            events.append(RecentActivityItem(
                id=f"shelter_res_{r.id}",
                timestamp=r.created_at,
                resource_type="shelter_reservation",
                event_category="shelter_reservation",
                title=f"Reservation: {r.status}",
                description=f"Shelter {r.shelter_id} - {r.reserved_people} people",
                source="officer" if r.approved_at else "system",
                status=r.status
            ))
    
    # Alert events
    if resource_type is None or resource_type == "alert":
        alerts_query = db.query(OperationalAlert)
        if incident_id:
            alerts_query = alerts_query.filter(OperationalAlert.incident_id == incident_id)
        alerts = alerts_query.order_by(OperationalAlert.created_at.desc()).limit(limit).all()
        for a in alerts:
            events.append(RecentActivityItem(
                id=f"alert_{a.id}",
                timestamp=a.created_at,
                resource_type="alert",
                event_category=f"alert_{a.status}",
                title=f"Alert: {a.title}",
                description=a.description[:100] if a.description else "",
                source="system",
                incident_id=a.incident_id,
                status=a.status
            ))
    
    # Sort all events by timestamp descending
    events.sort(key=lambda x: x.timestamp, reverse=True)
    return events[:limit]


def get_command_map_overview(db: Session) -> Dict[str, Any]:
    from app.models import ShelterRouteCondition, RouteRisk
    
    # Get incidents
    incidents = db.query(Incident).filter(
        Incident.status.in_(["reported", "verified", "assigned", "in_progress"])
    ).all()
    
    # Get teams
    teams = db.query(RescueTeam).all()
    
    # Get warehouses
    warehouses = db.query(Warehouse).all()
    
    # Get shelters
    shelters = db.query(EmergencyShelter).all()
    
    # Get blocked/high-risk routes
    routes = db.query(ShelterRouteCondition).filter(
        or_(
            ShelterRouteCondition.is_blocked == 1,
            ShelterRouteCondition.risk_level == RouteRisk.high
        )
    ).all()
    
    return {
        "incidents": [
            {
                "id": i.id,
                "title": i.title,
                "incident_type": i.incident_type,
                "latitude": i.latitude,
                "longitude": i.longitude,
                "severity": i.severity.value if hasattr(i.severity, 'value') else i.severity,
                "status": i.status.value if hasattr(i.status, 'value') else i.status,
                "priority_level": i.priority_level,
                "ml_priority_level": i.ml_priority_level
            }
            for i in incidents
        ],
        "teams": [
            {
                "id": t.id,
                "name": t.name,
                "latitude": t.latitude,
                "longitude": t.longitude,
                "availability_status": t.availability_status.value if hasattr(t.availability_status, 'value') else t.availability_status,
                "capacity": t.capacity,
                "current_workload": t.current_workload,
                "skills": t.skills,
                "equipment": t.equipment
            }
            for t in teams
        ],
        "warehouses": [
            {
                "id": w.id,
                "name": w.name,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "operating_status": w.operating_status.value if hasattr(w.operating_status, 'value') else w.operating_status
            }
            for w in warehouses
        ],
        "shelters": [
            {
                "id": s.id,
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "operating_status": s.operating_status.value if hasattr(s.operating_status, 'value') else s.operating_status,
                "total_capacity": s.total_capacity,
                "occupied_capacity": s.occupied_capacity,
                "reserved_capacity": s.reserved_capacity
            }
            for s in shelters
        ],
        "blocked_routes": [
            {
                "incident_id": r.incident_id,
                "shelter_id": r.shelter_id,
                "rescue_team_id": r.rescue_team_id,
                "risk_level": r.risk_level.value if hasattr(r.risk_level, 'value') else r.risk_level,
                "is_blocked": r.is_blocked,
                "estimated_delay_minutes": r.estimated_delay_minutes
            }
            for r in routes
        ]
    }
