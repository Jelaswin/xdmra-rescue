from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app import schemas, models
from app.services import (
    get_dashboard_summary, 
    create_incident, 
    get_incidents, 
    get_incident, 
    get_teams, 
    get_team,
    process_priority_calculation,
    get_recommendations_for_incident,
    create_allocation,
    get_allocations_for_incident,
    get_allocation,
    priority_predictor,
    priority_service,
    geocoding_service,
    allocation_service,
    reallocation_service
)

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "application": "X-DMRA Rescue"}

@router.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    return get_dashboard_summary(db)

@router.get("/incidents", response_model=List[schemas.Incident])
def read_incidents(db: Session = Depends(get_db)):
    return get_incidents(db)

@router.post("/incidents", response_model=schemas.Incident, status_code=status.HTTP_201_CREATED)
def add_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db)):
    return create_incident(db, incident)

@router.get("/incidents/{incident_id}", response_model=schemas.Incident)
def read_incident(incident_id: int, db: Session = Depends(get_db)):
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident

@router.post("/incidents/{incident_id}/calculate-priority", response_model=schemas.PriorityResult)
def calculate_priority(incident_id: int, db: Session = Depends(get_db)):
    result = process_priority_calculation(db, incident_id)
    if not result:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result

@router.get("/incidents/{incident_id}/team-recommendations", response_model=List[schemas.TeamRecommendation])
def read_recommendations(incident_id: int, db: Session = Depends(get_db)):
    recs = get_recommendations_for_incident(db, incident_id)
    if recs is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return recs

@router.post("/incidents/{incident_id}/allocations", response_model=schemas.AllocationResponse, status_code=status.HTTP_201_CREATED)
def allocate_team(incident_id: int, req: schemas.AllocationCreate, db: Session = Depends(get_db)):
    try:
        allocation = create_allocation(db, incident_id, req)
        return allocation
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/incidents/{incident_id}/allocations", response_model=List[schemas.AllocationResponse])
def read_incident_allocations(incident_id: int, db: Session = Depends(get_db)):
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_allocations_for_incident(db, incident_id)

@router.get("/allocations/{allocation_id}", response_model=schemas.AllocationResponse)
def read_allocation(allocation_id: int, db: Session = Depends(get_db)):
    allocation = get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return allocation

@router.get("/teams", response_model=List[schemas.RescueTeam])
def read_teams(db: Session = Depends(get_db)):
    return get_teams(db)

@router.get("/teams/{team_id}", response_model=schemas.RescueTeam)
def read_team(team_id: int, db: Session = Depends(get_db)):
    db_team = get_team(db, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team

# --- ML Endpoints Phase 3 ---

@router.get("/ml/model-info", response_model=schemas.ModelInfoResponse)
def get_model_info():
    info = priority_predictor.get_model_info()
    return info

@router.post("/ml/retrain")
def retrain_model():
    # Only for development
    try:
        from ml.training.train_priority_model import train_models
        train_models()
        return {"status": "success", "message": "Model retrained successfully. Please restart server to load new model."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@router.post("/incidents/{incident_id}/predict-priority-ml", response_model=schemas.PriorityComparisonResponse)
def predict_incident_priority_ml(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # ML Prediction
    ml_res = priority_predictor.predict_priority(incident)
    if not ml_res:
        raise HTTPException(status_code=503, detail="ML Model not available or failed to predict")
        
    # Rule-based calculation if not present
    if not incident.priority_score or not incident.priority_level:
        rule_res = priority_service.calculate_incident_priority(incident)
        incident.priority_score = rule_res.priority_score
        incident.priority_level = rule_res.priority_level
        incident.priority_reasons = rule_res.reasons
        
    # Comparison
    comparison = priority_predictor.compare_priorities(incident.priority_level, ml_res.predicted_priority)
    
    # Store ML prediction metadata in Incident
    incident.ml_priority_level = ml_res.predicted_priority
    incident.ml_priority_confidence = ml_res.confidence
    incident.ml_model_name = ml_res.model_name
    incident.ml_model_version = ml_res.model_version
    incident.ml_predicted_at = datetime.now(timezone.utc)
    incident.priority_agreement_status = comparison["agreement_status"]
    incident.requires_priority_review = int(comparison["requires_officer_review"])
    
    db.commit()
    
    return schemas.PriorityComparisonResponse(
        rule_priority=incident.priority_level,
        rule_score=incident.priority_score,
        ml_priority=ml_res.predicted_priority,
        ml_confidence=ml_res.confidence,
        agreement_status=comparison["agreement_status"],
        requires_officer_review=comparison["requires_officer_review"],
        comparison_message=comparison["comparison_message"]
    )

# --- Phase 4 Map and Location Endpoints ---

@router.get("/locations/search", response_model=List[schemas.GeocodingResult])
async def search_locations(q: str):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = await geocoding_service.search_location(q)
    return results

@router.patch("/incidents/{incident_id}/location", response_model=schemas.Incident)
def update_incident_location(incident_id: int, req: schemas.IncidentLocationUpdate, db: Session = Depends(get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident.latitude = req.latitude
    incident.longitude = req.longitude
    if req.location_name is not None:
        incident.location_name = req.location_name
    if req.location_accuracy is not None:
        incident.location_accuracy = req.location_accuracy
    if req.location_source is not None:
        incident.location_source = req.location_source
    if req.location_notes is not None:
        incident.location_notes = req.location_notes
        
    db.commit()
    db.refresh(incident)
    return incident

@router.patch("/teams/{team_id}/location", response_model=schemas.RescueTeam)
def update_team_location(team_id: int, req: schemas.TeamLocationUpdate, db: Session = Depends(get_db)):
    team = db.query(models.RescueTeam).filter(models.RescueTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    team.latitude = req.latitude
    team.longitude = req.longitude
    team.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(team)
    return team

@router.get("/map/overview", response_model=schemas.MapOverviewResponse)
def get_map_overview(db: Session = Depends(get_db)):
    incidents = db.query(models.Incident).filter(
        models.Incident.status.in_([
            models.IncidentStatus.reported,
            models.IncidentStatus.verified,
            models.IncidentStatus.assigned,
            models.IncidentStatus.in_progress
        ])
    ).all()
    
    teams = db.query(models.RescueTeam).all()
    
    return schemas.MapOverviewResponse(incidents=incidents, teams=teams)

# ================= Phase 5 Reallocation Endpoints =================

@router.post("/incidents/{incident_id}/evaluate-reallocation", response_model=schemas.ReallocationRecommendationResult)
def evaluate_reallocation(incident_id: int, req: schemas.ReallocationEvaluateRequest, db: Session = Depends(get_db)):
    return reallocation_service.evaluate_reallocation(db, incident_id, req.trigger_type, req.trigger_description)

@router.post("/incidents/{incident_id}/reallocate", response_model=schemas.AllocationResponse)
def approve_reallocation(incident_id: int, req: schemas.ReallocationApprovalRequest, db: Session = Depends(get_db)):
    return reallocation_service.approve_reallocation(
        db, incident_id, req.replacement_team_id, req.trigger_type, req.reason
    )

@router.get("/incidents/{incident_id}/reallocation-history", response_model=List[schemas.ReallocationEventResponse])
def get_reallocation_history(incident_id: int, db: Session = Depends(get_db)):
    events = db.query(models.ReallocationEvent).filter(models.ReallocationEvent.incident_id == incident_id).order_by(models.ReallocationEvent.created_at.desc()).all()
    return events

@router.post("/incidents/{incident_id}/route-conditions", response_model=schemas.RouteConditionCreate)
def create_route_condition(incident_id: int, req: schemas.RouteConditionCreate, db: Session = Depends(get_db)):
    rc = db.query(models.RouteCondition).filter(
        models.RouteCondition.incident_id == incident_id,
        models.RouteCondition.rescue_team_id == req.rescue_team_id
    ).first()
    
    if rc:
        rc.risk_level = req.risk_level
        rc.is_blocked = int(req.is_blocked)
        rc.estimated_delay_minutes = req.estimated_delay_minutes
        rc.description = req.description
    else:
        rc = models.RouteCondition(
            incident_id=incident_id,
            rescue_team_id=req.rescue_team_id,
            risk_level=req.risk_level,
            is_blocked=int(req.is_blocked),
            estimated_delay_minutes=req.estimated_delay_minutes,
            description=req.description
        )
        db.add(rc)
    db.commit()
    return req

@router.patch("/route-conditions/{route_condition_id}")
def update_route_condition(route_condition_id: int, req: schemas.RouteConditionCreate, db: Session = Depends(get_db)):
    rc = db.query(models.RouteCondition).filter(models.RouteCondition.id == route_condition_id).first()
    if not rc:
        raise HTTPException(status_code=404, detail="Route condition not found")
    rc.risk_level = req.risk_level
    rc.is_blocked = int(req.is_blocked)
    rc.estimated_delay_minutes = req.estimated_delay_minutes
    rc.description = req.description
    db.commit()
    return {"status": "ok"}

@router.patch("/teams/{team_id}/operational-status", response_model=schemas.RescueTeam)
def update_team_operational_status(team_id: int, req: schemas.OperationalStatusUpdate, db: Session = Depends(get_db)):
    team = db.query(models.RescueTeam).filter(models.RescueTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.availability_status = req.availability_status
    db.commit()
    db.refresh(team)
    return team
