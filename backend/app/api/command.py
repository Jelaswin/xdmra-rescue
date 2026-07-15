from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CommandDashboardSummary, PendingDecisionResponse, 
    IncidentOperationalSummary, TimelineEvent,
    OperationalAlertResponse
)
from app.models import OperationalAlert, Incident
from app.services.command_dashboard_service import (
    get_dashboard_summary, get_pending_decisions, 
    get_incident_operational_summary, get_incident_timeline
)
from app.services.operational_alert_service import (
    generate_alerts, acknowledge_alert, resolve_alert
)

router = APIRouter(prefix="/command", tags=["Unified Command Dashboard"])

@router.post("/alerts/generate", status_code=status.HTTP_200_OK)
def trigger_alert_generation(db: Session = Depends(get_db)):
    """Manually trigger alert generation (for demonstration and testing)."""
    generate_alerts(db)
    return {"status": "success", "message": "Alerts generated"}

@router.get("/dashboard-summary", response_model=CommandDashboardSummary)
def read_dashboard_summary(db: Session = Depends(get_db)):
    generate_alerts(db) # Auto-refresh alerts on load
    return get_dashboard_summary(db)

@router.get("/pending-decisions", response_model=List[PendingDecisionResponse])
def read_pending_decisions(db: Session = Depends(get_db)):
    return get_pending_decisions(db)

@router.get("/alerts", response_model=List[OperationalAlertResponse])
def get_alerts(severity: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    generate_alerts(db)
    query = db.query(OperationalAlert)
    if severity:
        query = query.filter(OperationalAlert.severity == severity)
    if status:
        query = query.filter(OperationalAlert.status == status)
    return query.order_by(OperationalAlert.created_at.desc()).all()

@router.patch("/alerts/{alert_id}/acknowledge", response_model=OperationalAlertResponse)
def acknowledge_alert_endpoint(alert_id: int, db: Session = Depends(get_db)):
    alert = acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    return alert

@router.patch("/alerts/{alert_id}/resolve", response_model=OperationalAlertResponse)
def resolve_alert_endpoint(alert_id: int, db: Session = Depends(get_db)):
    alert = resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/incidents/{incident_id}/operational-summary", response_model=IncidentOperationalSummary)
def read_incident_operational_summary(incident_id: int, db: Session = Depends(get_db)):
    summary = get_incident_operational_summary(db, incident_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Incident not found")
    return summary

@router.get("/incidents/{incident_id}/timeline", response_model=List[TimelineEvent])
def read_incident_timeline(incident_id: int, db: Session = Depends(get_db)):
    # Check if incident exists to throw 404
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_incident_timeline(db, incident_id)
