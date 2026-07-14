from sqlalchemy.orm import Session
from app import models, schemas

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
        vulnerable_people=incident.vulnerable_people
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
