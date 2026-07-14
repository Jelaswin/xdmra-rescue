from sqlalchemy.orm import Session
from app import models, schemas
from app.services.priority_service import calculate_incident_priority
from app.services.allocation_service import calculate_team_recommendations

def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
    total_incidents = db.query(models.Incident).count()
    critical_incidents = db.query(models.Incident).filter(models.Incident.severity == models.IncidentSeverity.critical).count()
    available_teams = db.query(models.RescueTeam).filter(models.RescueTeam.availability_status == models.TeamAvailability.available).count()
    active_allocations = db.query(models.Allocation).filter(
        models.Allocation.status.in_([models.AllocationStatus.approved, models.AllocationStatus.dispatched, models.AllocationStatus.recommended])
    ).count()

    return schemas.DashboardSummary(
        total_incidents=total_incidents,
        critical_incidents=critical_incidents,
        available_teams=available_teams,
        active_allocations=active_allocations
    )

def create_incident(db: Session, incident: schemas.IncidentCreate) -> models.Incident:
    db_incident = models.Incident(
        title=incident.title,
        description=incident.description,
        incident_type=incident.incident_type,
        latitude=incident.latitude,
        longitude=incident.longitude,
        severity=incident.severity,
        affected_people=incident.affected_people,
        injured_people=incident.injured_people,
        vulnerable_people=incident.vulnerable_people,
        trapped_people=incident.trapped_people,
        children_count=incident.children_count,
        elderly_count=incident.elderly_count,
        required_skills=incident.required_skills,
        required_equipment=incident.required_equipment
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incidents(db: Session):
    return db.query(models.Incident).order_by(models.Incident.created_at.desc()).all()

def get_incident(db: Session, incident_id: int):
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()

def get_teams(db: Session):
    return db.query(models.RescueTeam).all()

def get_team(db: Session, team_id: int):
    return db.query(models.RescueTeam).filter(models.RescueTeam.id == team_id).first()

def process_priority_calculation(db: Session, incident_id: int):
    incident = get_incident(db, incident_id)
    if not incident:
        return None
        
    result = calculate_incident_priority(incident)
    
    incident.priority_score = result.priority_score
    incident.priority_level = result.priority_level
    incident.priority_reasons = result.reasons
    
    db.commit()
    db.refresh(incident)
    return result

def get_recommendations_for_incident(db: Session, incident_id: int):
    incident = get_incident(db, incident_id)
    if not incident:
        return None
        
    # Auto-calculate priority if missing
    if incident.priority_score is None:
        process_priority_calculation(db, incident_id)
        db.refresh(incident)
        
    all_teams = get_teams(db)
    # Fetch route conditions (assuming fetch all for simple naive approach)
    route_conditions = db.query(models.RouteCondition).all()
    
    recs = calculate_team_recommendations(incident, all_teams, route_conditions)
    return recs

def create_allocation(db: Session, incident_id: int, req: schemas.AllocationCreate):
    incident = get_incident(db, incident_id)
    if not incident:
        raise ValueError("Incident not found")
        
    team = get_team(db, req.rescue_team_id)
    if not team:
        raise ValueError("Rescue team not found")
        
    if team.availability_status != models.TeamAvailability.available:
        raise ValueError("Team is not available")
        
    # Prevent duplicate active allocations for same incident
    existing = db.query(models.Allocation).filter(
        models.Allocation.incident_id == incident_id,
        models.Allocation.status.in_([models.AllocationStatus.recommended, models.AllocationStatus.approved, models.AllocationStatus.dispatched])
    ).first()
    if existing:
        raise ValueError("Incident already has an active allocation")
        
    # Recalculate recommendation to get score and explanation
    recs = get_recommendations_for_incident(db, incident_id)
    rec = next((r for r in recs if r.team_id == req.rescue_team_id), None)
    if not rec:
        raise ValueError("Team is ineligible for allocation")
        
    allocation = models.Allocation(
        incident_id=incident_id,
        rescue_team_id=team.id,
        status=models.AllocationStatus.approved,
        recommendation_score=rec.total_score,
        explanation=rec.explanation
    )
    
    # State changes
    incident.status = models.IncidentStatus.assigned
    team.availability_status = models.TeamAvailability.assigned
    team.current_workload += 1
    
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation

def get_allocations_for_incident(db: Session, incident_id: int):
    return db.query(models.Allocation).filter(models.Allocation.incident_id == incident_id).order_by(models.Allocation.created_at.desc()).all()

def get_allocation(db: Session, allocation_id: int):
    return db.query(models.Allocation).filter(models.Allocation.id == allocation_id).first()
