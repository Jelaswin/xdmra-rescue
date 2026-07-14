from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import schemas
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
    get_allocation
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
