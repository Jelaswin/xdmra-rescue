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


# ==========================================
# PHASE 6: RELIEF-SUPPLY ALLOCATION ENDPOINTS
# ==========================================
from app.models import (
    Incident, Warehouse, ReliefInventory, ReliefRequest, ReliefRequestItem, DeliveryVehicle,
    ReliefRecommendation, ReliefDispatch, ReliefDispatchItem, InventoryMovement,
    WarehouseOperatingStatus, ReliefRequestStatus, ReliefSourceType, VehicleAvailability,
    DispatchStatus, RouteCondition, RouteRisk
)
from app.schemas import (
    WarehouseResponse, WarehouseCreate, ReliefInventoryResponse, ReliefInventoryCreate,
    DeliveryVehicleResponse, DeliveryVehicleCreate, ReliefRequestResponse, ReliefRequestCreate,
    ReliefDemandSuggestion, ReliefAllocationEvaluationResponse, ReliefDispatchResponse,
    ReliefDispatchCreate, RouteConditionCreate
)
from app.services.relief_demand_service import generate_relief_demand
from app.services.relief_allocation_service import evaluate_relief_allocation
from app.services.inventory_service import approve_dispatch, transition_dispatch_status

@router.get("/warehouses", response_model=List[WarehouseResponse])
def get_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(wh: WarehouseCreate, db: Session = Depends(get_db)):
    new_wh = Warehouse(**wh.model_dump())
    db.add(new_wh)
    db.commit()
    db.refresh(new_wh)
    return new_wh

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return wh

@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(warehouse_id: int, payload: dict, db: Session = Depends(get_db)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    for k, v in payload.items():
        setattr(wh, k, v)
    db.commit()
    db.refresh(wh)
    return wh

@router.get("/warehouses/{warehouse_id}/inventory", response_model=List[ReliefInventoryResponse])
def get_warehouse_inventory(warehouse_id: int, db: Session = Depends(get_db)):
    return db.query(ReliefInventory).filter(ReliefInventory.warehouse_id == warehouse_id).all()

@router.post("/warehouses/{warehouse_id}/inventory", response_model=ReliefInventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(warehouse_id: int, payload: ReliefInventoryCreate, db: Session = Depends(get_db)):
    inv = ReliefInventory(**payload.model_dump())
    inv.warehouse_id = warehouse_id
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

@router.patch("/inventory/{inventory_id}", response_model=ReliefInventoryResponse)
def update_inventory(inventory_id: int, payload: dict, db: Session = Depends(get_db)):
    inv = db.query(ReliefInventory).filter(ReliefInventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")
    for k, v in payload.items():
        setattr(inv, k, v)
    db.commit()
    db.refresh(inv)
    return inv

@router.get("/delivery-vehicles", response_model=List[DeliveryVehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(DeliveryVehicle).all()

@router.post("/delivery-vehicles", response_model=DeliveryVehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: DeliveryVehicleCreate, db: Session = Depends(get_db)):
    v = DeliveryVehicle(**payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

@router.patch("/delivery-vehicles/{vehicle_id}", response_model=DeliveryVehicleResponse)
def update_vehicle(vehicle_id: int, payload: dict, db: Session = Depends(get_db)):
    v = db.query(DeliveryVehicle).filter(DeliveryVehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for k, v_val in payload.items():
        setattr(v, k, v_val)
    db.commit()
    db.refresh(v)
    return v

@router.post("/incidents/{incident_id}/relief-demand/suggest", response_model=ReliefDemandSuggestion)
def suggest_relief_demand(incident_id: int, support_duration_days: int = 1, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return generate_relief_demand(incident, support_duration_days)

@router.post("/incidents/{incident_id}/relief-requests", response_model=ReliefRequestResponse, status_code=status.HTTP_201_CREATED)
def create_relief_request(incident_id: int, payload: ReliefRequestCreate, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    req = ReliefRequest(
        incident_id=incident_id,
        support_duration_days=payload.support_duration_days,
        total_people=payload.total_people,
        notes=payload.notes,
        status=ReliefRequestStatus.draft
    )
    db.add(req)
    db.flush()
    
    for item in payload.items:
        req_item = ReliefRequestItem(
            relief_request_id=req.id,
            item_type=item.item_type,
            requested_quantity=item.requested_quantity,
            approved_quantity=item.requested_quantity, # Default to requested
            source_type=item.source_type,
            calculation_reason=item.calculation_reason
        )
        db.add(req_item)
        
    db.commit()
    db.refresh(req)
    # The response schema handles items dynamically if we set up relationship,
    # but since we didn't add relationship to models directly we can fetch them.
    req.items = db.query(ReliefRequestItem).filter(ReliefRequestItem.relief_request_id == req.id).all()
    return req

@router.get("/incidents/{incident_id}/relief-requests", response_model=List[ReliefRequestResponse])
def get_relief_requests(incident_id: int, db: Session = Depends(get_db)):
    reqs = db.query(ReliefRequest).filter(ReliefRequest.incident_id == incident_id).all()
    for req in reqs:
        req.items = db.query(ReliefRequestItem).filter(ReliefRequestItem.relief_request_id == req.id).all()
    return reqs

@router.get("/relief-requests/{request_id}", response_model=ReliefRequestResponse)
def get_relief_request(request_id: int, db: Session = Depends(get_db)):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Relief request not found")
    req.items = db.query(ReliefRequestItem).filter(ReliefRequestItem.relief_request_id == req.id).all()
    return req

@router.patch("/relief-requests/{request_id}", response_model=ReliefRequestResponse)
def update_relief_request(request_id: int, payload: dict, db: Session = Depends(get_db)):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Relief request not found")
    for k, v in payload.items():
        setattr(req, k, v)
    db.commit()
    db.refresh(req)
    req.items = db.query(ReliefRequestItem).filter(ReliefRequestItem.relief_request_id == req.id).all()
    return req

@router.post("/relief-requests/{request_id}/recommendations", response_model=ReliefAllocationEvaluationResponse)
def get_relief_recommendations(request_id: int, db: Session = Depends(get_db)):
    return evaluate_relief_allocation(db, request_id)

@router.post("/relief-requests/{request_id}/approve-dispatch", response_model=ReliefDispatchResponse)
def create_dispatch(request_id: int, payload: ReliefDispatchCreate, db: Session = Depends(get_db)):
    # Inventory reservation is handled in the service
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    items_dict = [i.model_dump() for i in payload.items]
    dispatch = approve_dispatch(
        db=db,
        request_id=request_id,
        warehouse_id=payload.warehouse_id,
        vehicle_id=payload.vehicle_id,
        items_payload=items_dict,
        recommendation_score=payload.recommendation_score,
        explanation=payload.explanation
    )
    
    # Update request status
    req.status = ReliefRequestStatus.partially_allocated # Simplified
    db.commit()
    
    dispatch.items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == dispatch.id).all()
    return dispatch

@router.get("/relief-requests/{request_id}/dispatches", response_model=List[ReliefDispatchResponse])
def get_request_dispatches(request_id: int, db: Session = Depends(get_db)):
    dispatches = db.query(ReliefDispatch).filter(ReliefDispatch.relief_request_id == request_id).all()
    for d in dispatches:
        d.items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == d.id).all()
    return dispatches

@router.patch("/relief-dispatches/{dispatch_id}/status", response_model=ReliefDispatchResponse)
def update_dispatch_status(dispatch_id: int, status: str, db: Session = Depends(get_db)):
    try:
        new_status = DispatchStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    dispatch = transition_dispatch_status(db, dispatch_id, new_status)
    dispatch.items = db.query(ReliefDispatchItem).filter(ReliefDispatchItem.relief_dispatch_id == dispatch.id).all()
    return dispatch

@router.post("/incidents/{incident_id}/warehouse-route-conditions")
def create_warehouse_route_condition(incident_id: int, condition: RouteConditionCreate, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Check if exists
    rc = db.query(RouteCondition).filter(
        RouteCondition.incident_id == incident_id,
        RouteCondition.warehouse_id == condition.warehouse_id
    ).first()
    
    if rc:
        rc.risk_level = condition.risk_level
        rc.is_blocked = condition.is_blocked
        rc.estimated_delay_minutes = condition.estimated_delay_minutes
        rc.description = condition.description
    else:
        rc = RouteCondition(
            incident_id=incident_id,
            warehouse_id=condition.warehouse_id,
            risk_level=condition.risk_level,
            is_blocked=condition.is_blocked,
            estimated_delay_minutes=condition.estimated_delay_minutes,
            description=condition.description
        )
        db.add(rc)
    db.commit()
    db.refresh(rc)
    return rc

@router.get("/relief/dashboard-summary")
def get_relief_dashboard_summary(db: Session = Depends(get_db)):
    active_requests = db.query(ReliefRequest).filter(ReliefRequest.status.in_([ReliefRequestStatus.confirmed, ReliefRequestStatus.partially_allocated])).count()
    dispatches_in_progress = db.query(ReliefDispatch).filter(ReliefDispatch.status.in_([DispatchStatus.approved, DispatchStatus.preparing, DispatchStatus.dispatched])).count()
    warehouses_active = db.query(Warehouse).filter(Warehouse.operating_status == WarehouseOperatingStatus.active).count()
    
    # Low stock
    low_stock_items = db.query(ReliefInventory).filter(ReliefInventory.quantity_available <= ReliefInventory.reorder_level).count()
    
    return {
        "active_requests": active_requests,
        "dispatches_in_progress": dispatches_in_progress,
        "warehouses_active": warehouses_active,
        "low_stock_items": low_stock_items
    }

@router.get("/relief/inventory-alerts")
def get_inventory_alerts(db: Session = Depends(get_db)):
    low_stock = db.query(ReliefInventory).filter(ReliefInventory.quantity_available <= ReliefInventory.reorder_level).all()
    res = []
    for inv in low_stock:
        wh = db.query(Warehouse).filter(Warehouse.id == inv.warehouse_id).first()
        res.append({
            "inventory_id": inv.id,
            "warehouse_name": wh.name if wh else "Unknown",
            "item": inv.display_name,
            "available": inv.quantity_available,
            "reorder_level": inv.reorder_level
        })
    return res

# --- Phase 7 Shelter Endpoints ---
from app.models import (
    EmergencyShelter, ShelterRequest, ShelterReservation, 
    ShelterCapacityMovement, ShelterCapacityMovementType, ShelterRouteCondition,
    ShelterOperatingStatus, ShelterRequestStatus, ShelterReservationStatus
)
from app.schemas import (
    EmergencyShelterResponse, EmergencyShelterCreate, EmergencyShelterUpdate,
    ShelterRequestResponse, ShelterRequestCreate, ShelterRequestUpdate,
    ShelterAllocationEvaluationResponse, ShelterReservationResponse,
    ShelterReservationCreate, ShelterRouteConditionCreate, ShelterRouteConditionResponse, ShelterDashboardSummary
)
from app.services.shelter_allocation_service import evaluate_shelter_allocation

@router.get("/shelters", response_model=List[EmergencyShelterResponse])
def get_shelters(db: Session = Depends(get_db)):
    return db.query(EmergencyShelter).all()

@router.post("/shelters", response_model=EmergencyShelterResponse, status_code=status.HTTP_201_CREATED)
def create_shelter(shelter: EmergencyShelterCreate, db: Session = Depends(get_db)):
    db_shelter = EmergencyShelter(**shelter.model_dump())
    db.add(db_shelter)
    db.commit()
    db.refresh(db_shelter)
    return db_shelter

@router.get("/shelters/{shelter_id}", response_model=EmergencyShelterResponse)
def get_shelter(shelter_id: int, db: Session = Depends(get_db)):
    db_shelter = db.query(EmergencyShelter).filter(EmergencyShelter.id == shelter_id).first()
    if not db_shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    return db_shelter

@router.patch("/shelters/{shelter_id}", response_model=EmergencyShelterResponse)
def update_shelter(shelter_id: int, updates: EmergencyShelterUpdate, db: Session = Depends(get_db)):
    db_shelter = db.query(EmergencyShelter).filter(EmergencyShelter.id == shelter_id).first()
    if not db_shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    update_data = updates.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_shelter, k, v)
    db.commit()
    db.refresh(db_shelter)
    return db_shelter

@router.post("/incidents/{incident_id}/shelter-requests", response_model=ShelterRequestResponse, status_code=status.HTTP_201_CREATED)
def create_shelter_request(incident_id: int, request: ShelterRequestCreate, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db_req = ShelterRequest(incident_id=incident_id, **request.model_dump())
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

@router.get("/incidents/{incident_id}/shelter-requests", response_model=List[ShelterRequestResponse])
def get_incident_shelter_requests(incident_id: int, db: Session = Depends(get_db)):
    return db.query(ShelterRequest).filter(ShelterRequest.incident_id == incident_id).all()

@router.get("/shelter-requests/{request_id}", response_model=ShelterRequestResponse)
def get_shelter_request(request_id: int, db: Session = Depends(get_db)):
    req = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Shelter Request not found")
    return req

@router.patch("/shelter-requests/{request_id}", response_model=ShelterRequestResponse)
def update_shelter_request(request_id: int, updates: ShelterRequestUpdate, db: Session = Depends(get_db)):
    req = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Shelter Request not found")
    update_data = updates.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(req, k, v)
    db.commit()
    db.refresh(req)
    return req

@router.post("/shelter-requests/{request_id}/recommendations", response_model=ShelterAllocationEvaluationResponse)
def get_shelter_recommendations(request_id: int, db: Session = Depends(get_db)):
    req = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Shelter Request not found")
    return evaluate_shelter_allocation(db, request_id)

@router.post("/shelter-requests/{request_id}/approve-reservations", response_model=List[ShelterReservationResponse], status_code=status.HTTP_201_CREATED)
def approve_shelter_reservations(request_id: int, reservations: List[ShelterReservationCreate], db: Session = Depends(get_db)):
    req = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Shelter Request not found")
    
    total_requested_alloc = sum(r.reserved_people for r in reservations)
    if total_requested_alloc > req.total_displaced_people:
        raise HTTPException(status_code=400, detail="Cannot allocate more people than requested")
        
    created_reservations = []
    
    try:
        for res_req in reservations:
            shelter = db.query(EmergencyShelter).filter(EmergencyShelter.id == res_req.shelter_id).with_for_update().first()
            if not shelter:
                raise HTTPException(status_code=404, detail=f"Shelter {res_req.shelter_id} not found")
            
            avail = shelter.total_capacity - shelter.occupied_capacity - shelter.reserved_capacity
            if res_req.reserved_people > avail:
                raise HTTPException(status_code=400, detail=f"Shelter {shelter.name} has insufficient capacity. Requested: {res_req.reserved_people}, Available: {avail}")
            
            db_res = ShelterReservation(
                shelter_request_id=request_id,
                shelter_id=res_req.shelter_id,
                reserved_people=res_req.reserved_people,
                recommendation_score=res_req.recommendation_score,
                explanation=res_req.explanation,
                approved_at=datetime.now(timezone.utc)
            )
            db.add(db_res)
            db.flush() # get id
            
            # Record movement
            mv = ShelterCapacityMovement(
                shelter_id=shelter.id,
                shelter_reservation_id=db_res.id,
                movement_type=ShelterCapacityMovementType.reserved,
                people_count=res_req.reserved_people,
                occupied_before=shelter.occupied_capacity,
                occupied_after=shelter.occupied_capacity,
                reserved_before=shelter.reserved_capacity,
                reserved_after=shelter.reserved_capacity + res_req.reserved_people,
                reason=f"Approved reservation for request {request_id}"
            )
            db.add(mv)
            
            # Update shelter
            shelter.reserved_capacity += res_req.reserved_people
            created_reservations.append(db_res)
            
        req.status = ShelterRequestStatus.allocated if total_requested_alloc == req.total_displaced_people else ShelterRequestStatus.partially_allocated
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    for cr in created_reservations:
        db.refresh(cr)
    return created_reservations

@router.get("/shelter-requests/{request_id}/reservations", response_model=List[ShelterReservationResponse])
def get_shelter_reservations(request_id: int, db: Session = Depends(get_db)):
    return db.query(ShelterReservation).filter(ShelterReservation.shelter_request_id == request_id).all()

@router.patch("/shelter-reservations/{reservation_id}/status", response_model=ShelterReservationResponse)
def update_shelter_reservation_status(reservation_id: int, status_update: dict, db: Session = Depends(get_db)):
    new_status_str = status_update.get("status")
    if not new_status_str:
        raise HTTPException(status_code=400, detail="status is required")
        
    res = db.query(ShelterReservation).filter(ShelterReservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
        
    shelter = db.query(EmergencyShelter).filter(EmergencyShelter.id == res.shelter_id).with_for_update().first()
    old_status = res.status
    
    if old_status == new_status_str:
        return res
        
    # Admitted
    if new_status_str == ShelterReservationStatus.admitted:
        if old_status not in [ShelterReservationStatus.approved, ShelterReservationStatus.preparing, ShelterReservationStatus.in_transit]:
            raise HTTPException(status_code=400, detail="Invalid transition to admitted")
        
        # Move from reserved to occupied
        shelter.reserved_capacity -= res.reserved_people
        shelter.occupied_capacity += res.reserved_people
        
        mv = ShelterCapacityMovement(
            shelter_id=shelter.id,
            shelter_reservation_id=res.id,
            movement_type=ShelterCapacityMovementType.admitted,
            people_count=res.reserved_people,
            occupied_before=shelter.occupied_capacity - res.reserved_people,
            occupied_after=shelter.occupied_capacity,
            reserved_before=shelter.reserved_capacity + res.reserved_people,
            reserved_after=shelter.reserved_capacity,
            reason="Admitted to shelter"
        )
        db.add(mv)
        res.admitted_at = datetime.now(timezone.utc)
        
    # Cancelled before admission
    elif new_status_str == ShelterReservationStatus.cancelled:
        if old_status in [ShelterReservationStatus.admitted, ShelterReservationStatus.completed]:
            raise HTTPException(status_code=400, detail="Cannot cancel after admission")
            
        shelter.reserved_capacity -= res.reserved_people
        mv = ShelterCapacityMovement(
            shelter_id=shelter.id,
            shelter_reservation_id=res.id,
            movement_type=ShelterCapacityMovementType.reservation_released,
            people_count=res.reserved_people,
            occupied_before=shelter.occupied_capacity,
            occupied_after=shelter.occupied_capacity,
            reserved_before=shelter.reserved_capacity + res.reserved_people,
            reserved_after=shelter.reserved_capacity,
            reason="Reservation cancelled"
        )
        db.add(mv)
        res.cancelled_at = datetime.now(timezone.utc)
        
    # Completed/Discharged after admission
    elif new_status_str == ShelterReservationStatus.completed:
        if old_status != ShelterReservationStatus.admitted:
            raise HTTPException(status_code=400, detail="Cannot complete if not admitted")
            
        shelter.occupied_capacity -= res.reserved_people
        mv = ShelterCapacityMovement(
            shelter_id=shelter.id,
            shelter_reservation_id=res.id,
            movement_type=ShelterCapacityMovementType.discharged,
            people_count=res.reserved_people,
            occupied_before=shelter.occupied_capacity + res.reserved_people,
            occupied_after=shelter.occupied_capacity,
            reserved_before=shelter.reserved_capacity,
            reserved_after=shelter.reserved_capacity,
            reason="Stay completed, discharged"
        )
        db.add(mv)
        res.completed_at = datetime.now(timezone.utc)
        
    res.status = new_status_str
    db.commit()
    db.refresh(res)
    return res

@router.post("/incidents/{incident_id}/shelter-route-conditions", response_model=ShelterRouteConditionResponse)
def create_shelter_route_condition(incident_id: int, condition: ShelterRouteConditionCreate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    rc = db.query(ShelterRouteCondition).filter(
        ShelterRouteCondition.incident_id == incident_id,
        ShelterRouteCondition.shelter_id == condition.shelter_id
    ).first()
    
    if rc:
        rc.risk_level = condition.risk_level
        rc.is_blocked = condition.is_blocked
        rc.estimated_delay_minutes = condition.estimated_delay_minutes
        rc.description = condition.description
    else:
        rc = ShelterRouteCondition(
            incident_id=incident_id,
            shelter_id=condition.shelter_id,
            risk_level=condition.risk_level,
            is_blocked=condition.is_blocked,
            estimated_delay_minutes=condition.estimated_delay_minutes,
            description=condition.description
        )
        db.add(rc)
    db.commit()
    db.refresh(rc)
    return rc

@router.get("/shelter/dashboard-summary", response_model=ShelterDashboardSummary)
def get_shelter_dashboard_summary(db: Session = Depends(get_db)):
    shelters = db.query(EmergencyShelter).all()
    total = len(shelters)
    open_s = sum(1 for s in shelters if s.operating_status == ShelterOperatingStatus.open)
    avail = sum(s.total_capacity - s.occupied_capacity - s.reserved_capacity for s in shelters)
    resv = sum(s.reserved_capacity for s in shelters)
    occ = sum(s.occupied_capacity for s in shelters)
    
    high_risk = sum(1 for s in shelters if s.total_capacity > 0 and (s.occupied_capacity + s.reserved_capacity) / s.total_capacity >= 0.85)
    
    active_res = db.query(ShelterReservation).filter(ShelterReservation.status.in_([
        ShelterReservationStatus.approved, ShelterReservationStatus.preparing, ShelterReservationStatus.in_transit
    ])).count()
    
    in_transit_res = db.query(ShelterReservation).filter(ShelterReservation.status == ShelterReservationStatus.in_transit).all()
    in_transit_people = sum(r.reserved_people for r in in_transit_res)
    
    return ShelterDashboardSummary(
        total_shelters=total,
        open_shelters=open_s,
        available_spaces=avail,
        reserved_spaces=resv,
        occupied_spaces=occ,
        high_overcrowding_risk_shelters=high_risk,
        active_reservations=active_res,
        people_in_transit=in_transit_people
    )


@router.post("/shelters", response_model=schemas.EmergencyShelterResponse, status_code=status.HTTP_201_CREATED)
def create_shelter(shelter: schemas.EmergencyShelterCreate, db: Session = Depends(get_db)):
    db_shelter = models.EmergencyShelter(**shelter.model_dump())
    db.add(db_shelter)
    db.commit()
    db.refresh(db_shelter)
    return db_shelter

@router.patch("/shelters/{shelter_id}/operational-status", response_model=schemas.EmergencyShelterResponse)
def update_shelter_op_status(shelter_id: int, status_update: schemas.ShelterOperationalStatusUpdate, db: Session = Depends(get_db)):
    shelter = db.query(models.EmergencyShelter).filter(models.EmergencyShelter.id == shelter_id).first()
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    shelter.operating_status = status_update.operating_status
    db.commit()
    db.refresh(shelter)
    return shelter

@router.patch("/shelters/{shelter_id}/location", response_model=schemas.EmergencyShelterResponse)
def update_shelter_location(shelter_id: int, loc: schemas.ShelterLocationUpdate, db: Session = Depends(get_db)):
    shelter = db.query(models.EmergencyShelter).filter(models.EmergencyShelter.id == shelter_id).first()
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
    shelter.latitude = loc.latitude
    shelter.longitude = loc.longitude
    db.commit()
    db.refresh(shelter)
    return shelter

@router.get("/shelters/{shelter_id}/capacity-history", response_model=List[schemas.ShelterCapacityMovementResponse])
def get_shelter_capacity_history(shelter_id: int, db: Session = Depends(get_db)):
    return db.query(models.ShelterCapacityMovement).filter(models.ShelterCapacityMovement.shelter_id == shelter_id).order_by(models.ShelterCapacityMovement.created_at.desc()).all()

@router.patch("/shelter-route-conditions/{condition_id}", response_model=schemas.ShelterRouteConditionResponse)
def update_shelter_route_condition(condition_id: int, updates: schemas.ShelterRouteConditionUpdate, db: Session = Depends(get_db)):
    rc = db.query(models.ShelterRouteCondition).filter(models.ShelterRouteCondition.id == condition_id).first()
    if not rc:
        raise HTTPException(status_code=404, detail="Route condition not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(rc, k, v)
        
    db.commit()
    db.refresh(rc)
    return rc

@router.post("/shelter-requests/{request_id}/evaluate-reallocation", response_model=schemas.ShelterReallocationRecommendationResult)
def evaluate_shelter_reallocation(request_id: int, payload: schemas.ShelterReallocationEvaluateRequest, db: Session = Depends(get_db)):
    req = db.query(models.ShelterRequest).filter(models.ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    unavailable_shelter = db.query(models.EmergencyShelter).filter(models.EmergencyShelter.id == payload.unavailable_shelter_id).first()
    if not unavailable_shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")
        
    evaluation = evaluate_shelter_allocation(db, request_id, exclude_shelter_ids=[payload.unavailable_shelter_id])
    
    return schemas.ShelterReallocationRecommendationResult(
        reallocation_required=True,
        trigger_type=payload.trigger_type,
        unavailable_shelter={"id": unavailable_shelter.id, "name": unavailable_shelter.name},
        reason=payload.trigger_description or "Shelter became unavailable",
        recommended_replacements=evaluation,
        explanation="Replacement evaluation completed excluding the unavailable shelter."
    )

@router.post("/shelter-requests/{request_id}/reallocate", response_model=List[schemas.ShelterReservationResponse])
def execute_shelter_reallocation(request_id: int, payload: schemas.ShelterReallocationApprovalRequest, db: Session = Depends(get_db)):
    req = db.query(models.ShelterRequest).filter(models.ShelterRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    old_reservations = db.query(models.ShelterReservation).filter(
        models.ShelterReservation.shelter_request_id == request_id,
        models.ShelterReservation.shelter_id == payload.unavailable_shelter_id,
        models.ShelterReservation.status.in_([models.ShelterReservationStatus.approved, models.ShelterReservationStatus.preparing, models.ShelterReservationStatus.in_transit])
    ).with_for_update().all()
    
    if not old_reservations:
        raise HTTPException(status_code=400, detail="No active reservations found for this shelter to reallocate")
        
    try:
        for old_res in old_reservations:
            shelter = db.query(models.EmergencyShelter).filter(models.EmergencyShelter.id == old_res.shelter_id).with_for_update().first()
            shelter.reserved_capacity -= old_res.reserved_people
            mv = models.ShelterCapacityMovement(
                shelter_id=shelter.id,
                shelter_reservation_id=old_res.id,
                movement_type=models.ShelterCapacityMovementType.reservation_released,
                people_count=old_res.reserved_people,
                occupied_before=shelter.occupied_capacity,
                occupied_after=shelter.occupied_capacity,
                reserved_before=shelter.reserved_capacity + old_res.reserved_people,
                reserved_after=shelter.reserved_capacity,
                reason=f"Reallocation: {payload.reason}"
            )
            db.add(mv)
            old_res.status = models.ShelterReservationStatus.cancelled
            old_res.cancelled_at = datetime.now(timezone.utc)
            
        db.flush()
        new_reservations = approve_shelter_reservations(request_id, payload.reservations, db)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    return new_reservations

@router.get("/shelter/capacity-alerts", response_model=List[schemas.ShelterCapacityAlertResponse])
def get_shelter_capacity_alerts(db: Session = Depends(get_db)):
    shelters = db.query(models.EmergencyShelter).all()
    alerts = []
    for s in shelters:
        if s.total_capacity > 0:
            pct = (s.occupied_capacity + s.reserved_capacity) / s.total_capacity
            if pct >= 0.85:
                alerts.append(schemas.ShelterCapacityAlertResponse(
                    shelter_id=s.id,
                    shelter_name=s.name,
                    capacity_percentage=pct,
                    message=f"Critical overcrowding risk: {pct*100:.1f}% capacity" if pct >= 0.95 else f"High overcrowding risk: {pct*100:.1f}% capacity"
                ))
    return alerts
