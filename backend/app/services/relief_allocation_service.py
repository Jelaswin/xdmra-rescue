import math
from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session
from app.models import (
    Warehouse, ReliefRequest, ReliefRequestItem, RouteCondition,
    ReliefInventory, DeliveryVehicle, Incident, RouteRisk, WarehouseOperatingStatus, VehicleAvailability
)
from app.schemas import (
    ReliefAllocationEvaluationResponse, ReliefRecommendationResponse,
    SplitAllocationResponse, SplitAllocationWarehouse, TeamRecommendation
)

# Configurable Weights
WEIGHT_STOCK_COVERAGE = 35.0
WEIGHT_ITEM_COVERAGE = 15.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VEHICLE_CAPACITY = 15.0
WEIGHT_ROUTE_SAFETY = 10.0
WEIGHT_WORKLOAD = 10.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_route_condition(db: Session, incident_id: int, warehouse_id: int) -> RouteCondition:
    return db.query(RouteCondition).filter(
        RouteCondition.incident_id == incident_id,
        RouteCondition.warehouse_id == warehouse_id
    ).first()

def get_warehouse_inventory(db: Session, warehouse_id: int) -> List[ReliefInventory]:
    return db.query(ReliefInventory).filter(ReliefInventory.warehouse_id == warehouse_id).all()

def get_available_vehicles(db: Session, warehouse_id: int) -> List[DeliveryVehicle]:
    return db.query(DeliveryVehicle).filter(
        DeliveryVehicle.warehouse_id == warehouse_id,
        DeliveryVehicle.availability_status == VehicleAvailability.available
    ).all()

def evaluate_relief_allocation(db: Session, request_id: int) -> ReliefAllocationEvaluationResponse:
    relief_request = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not relief_request:
        raise ValueError("Relief request not found")
        
    incident = db.query(Incident).filter(Incident.id == relief_request.incident_id).first()
    request_items = db.query(ReliefRequestItem).filter(ReliefRequestItem.relief_request_id == request_id).all()
    
    # Base requirements
    demands = {item.item_type: item.approved_quantity for item in request_items if item.approved_quantity > 0}
    if not demands:
        return ReliefAllocationEvaluationResponse(single_source_recommendations=[])

    total_requested_units = sum(demands.values())
    
    warehouses = db.query(Warehouse).all()
    recommendations = []
    
    for wh in warehouses:
        if wh.operating_status not in [WarehouseOperatingStatus.active, WarehouseOperatingStatus.limited]:
            continue
            
        route = get_route_condition(db, incident.id, wh.id)
        if route and route.is_blocked:
            continue
            
        inventory = get_warehouse_inventory(db, wh.id)
        vehicles = get_available_vehicles(db, wh.id)
        
        # Check stock coverage
        inv_dict = {inv.item_type: inv.quantity_available - inv.quantity_reserved for inv in inventory}
        
        covered_items = []
        missing_items = []
        supplied_units = 0
        
        for item_type, req_qty in demands.items():
            avail = inv_dict.get(item_type, 0)
            if avail > 0:
                supplied_units += min(req_qty, avail)
                if avail >= req_qty:
                    covered_items.append(item_type)
                else:
                    missing_items.append(item_type)
            else:
                missing_items.append(item_type)
                
        if supplied_units == 0:
            continue # Can't supply anything
            
        stock_coverage_percentage = (supplied_units / total_requested_units) * 100.0
        
        # Score factors
        score = 0.0
        reasons = []
        limitations = []
        
        # 1. Stock Coverage (35 points)
        stock_score = (stock_coverage_percentage / 100.0) * WEIGHT_STOCK_COVERAGE
        score += stock_score
        
        # 2. Item Coverage (15 points)
        item_coverage = len(covered_items) / len(demands)
        item_score = item_coverage * WEIGHT_ITEM_COVERAGE
        score += item_score
        
        if stock_coverage_percentage == 100:
            reasons.append("Can fully supply all requested quantities.")
        else:
            limitations.append(f"Can only supply {stock_coverage_percentage:.1f}% of requested units.")
            
        # 3. Distance (15 points)
        distance = haversine_distance(wh.latitude, wh.longitude, incident.latitude, incident.longitude)
        if distance <= 10:
            dist_score = WEIGHT_DISTANCE
            reasons.append(f"Very close to incident (Straight-line distance: {distance:.1f} km).")
        elif distance <= 50:
            dist_score = WEIGHT_DISTANCE * 0.7
        else:
            dist_score = WEIGHT_DISTANCE * 0.3
            limitations.append(f"Far from incident (Straight-line distance: {distance:.1f} km).")
        score += dist_score
        
        # 4. Vehicle Capacity (15 points)
        total_veh_capacity = sum(v.capacity_units for v in vehicles)
        if total_veh_capacity >= supplied_units:
            veh_score = WEIGHT_VEHICLE_CAPACITY
            reasons.append("Sufficient delivery vehicle capacity.")
        elif total_veh_capacity > 0:
            veh_score = WEIGHT_VEHICLE_CAPACITY * (total_veh_capacity / supplied_units)
            limitations.append("Insufficient vehicle capacity for full dispatch at once.")
        else:
            veh_score = 0
            limitations.append("No available delivery vehicles.")
            continue # Ineligible if no transport
        score += veh_score
        
        # 5. Route Safety (10 points)
        if route:
            if route.risk_level == RouteRisk.low:
                route_score = WEIGHT_ROUTE_SAFETY
                reasons.append("Route is safe.")
            elif route.risk_level == RouteRisk.medium:
                route_score = WEIGHT_ROUTE_SAFETY * 0.5
                limitations.append(f"Medium route risk: {route.description}")
            else:
                route_score = WEIGHT_ROUTE_SAFETY * 0.2
                limitations.append(f"High route risk: {route.description}")
        else:
            route_score = WEIGHT_ROUTE_SAFETY
            reasons.append("No known route hazards.")
        score += route_score
        
        # 6. Workload (10 points)
        workload_ratio = wh.current_dispatch_workload / max(1, wh.maximum_dispatch_capacity)
        if workload_ratio < 0.3:
            wl_score = WEIGHT_WORKLOAD
            reasons.append("Warehouse has low current workload.")
        elif workload_ratio < 0.8:
            wl_score = WEIGHT_WORKLOAD * 0.5
        else:
            wl_score = WEIGHT_WORKLOAD * 0.1
            limitations.append("Warehouse is highly loaded.")
        score += wl_score
        
        explanation = f"Total Score: {score:.1f}/100. "
        if reasons:
            explanation += "Pros: " + "; ".join(reasons) + ". "
        if limitations:
            explanation += "Cons: " + "; ".join(limitations) + "."
            
        recommendations.append(ReliefRecommendationResponse(
            warehouse_id=wh.id,
            warehouse_name=wh.name,
            rank=0,
            total_score=round(score, 1),
            stock_coverage_percentage=round(stock_coverage_percentage, 1),
            covered_items=covered_items,
            missing_items=missing_items,
            distance_km=round(distance, 1),
            vehicle_availability=len(vehicles) > 0,
            route_risk=route.risk_level if route else "unknown",
            positive_reasons=reasons,
            limitations=limitations,
            explanation=explanation
        ))
        
    recommendations.sort(key=lambda x: x.total_score, reverse=True)
    for i, rec in enumerate(recommendations):
        rec.rank = i + 1
        
    split_plan = None
    if recommendations and recommendations[0].stock_coverage_percentage < 100:
        split_plan = _generate_split_allocation(db, incident, demands, recommendations)
        
    return ReliefAllocationEvaluationResponse(
        single_source_recommendations=recommendations,
        split_allocation_plan=split_plan
    )

def _generate_split_allocation(db: Session, incident: Incident, demands: Dict[str, int], recommendations: List[ReliefRecommendationResponse]) -> SplitAllocationResponse:
    # Greedy approach: pick top ranked warehouses until demand is met.
    remaining_demands = demands.copy()
    warehouses_involved = []
    
    for rec in recommendations:
        if not remaining_demands:
            break
            
        wh = db.query(Warehouse).filter(Warehouse.id == rec.warehouse_id).first()
        inventory = get_warehouse_inventory(db, wh.id)
        inv_dict = {inv.item_type: inv.quantity_available - inv.quantity_reserved for inv in inventory}
        
        provided_items = {}
        for item_type, req_qty in list(remaining_demands.items()):
            avail = inv_dict.get(item_type, 0)
            if avail > 0:
                supplied = min(req_qty, avail)
                provided_items[item_type] = supplied
                remaining_demands[item_type] -= supplied
                if remaining_demands[item_type] <= 0:
                    del remaining_demands[item_type]
                    
        if provided_items:
            warehouses_involved.append(SplitAllocationWarehouse(
                warehouse_id=wh.id,
                warehouse_name=wh.name,
                provided_items=provided_items,
                distance_km=rec.distance_km,
                explanation=f"Sourcing {len(provided_items)} item types from this warehouse."
            ))
            
    is_split = len(warehouses_involved) > 1
    exp = "Split allocation required because no single warehouse has sufficient stock." if is_split else "Single warehouse can partially supply."
    if remaining_demands:
        exp += " Warning: Total regional stock is insufficient to meet full demand."
        
    return SplitAllocationResponse(
        is_split=is_split,
        warehouses_involved=warehouses_involved,
        remaining_shortages=remaining_demands,
        explanation=exp
    )
