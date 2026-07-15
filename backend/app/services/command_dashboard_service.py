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
    IncidentOperationalSummary, TimelineEvent
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
