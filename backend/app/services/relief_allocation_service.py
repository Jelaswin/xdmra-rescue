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
from app.services.scoring.relief_scoring import (
    ReliefVehicleInput, ReliefScoringInput, rank_relief_warehouses,
)
from app.services.scoring.common import haversine_distance


WEIGHT_STOCK_COVERAGE = 35.0
WEIGHT_ITEM_COVERAGE = 15.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VEHICLE_CAPACITY = 15.0
WEIGHT_ROUTE_SAFETY = 10.0
WEIGHT_WORKLOAD = 10.0


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

    demands = {item.item_type: item.approved_quantity for item in request_items if item.approved_quantity > 0}
    if not demands:
        return ReliefAllocationEvaluationResponse(single_source_recommendations=[])

    total_requested_units = sum(demands.values())

    warehouses = db.query(Warehouse).all()

    scoring_inputs = []
    for wh in warehouses:
        route = get_route_condition(db, incident.id, wh.id)
        inventory = get_warehouse_inventory(db, wh.id)
        vehicles = get_available_vehicles(db, wh.id)

        inv_dict = {inv.item_type: inv.quantity_available - inv.quantity_reserved for inv in inventory}
        vehicle_inputs = [
            ReliefVehicleInput(
                vehicle_id=v.id,
                capacity_units=v.capacity_units,
                availability_status=v.availability_status.value,
            )
            for v in vehicles
        ]

        inp = ReliefScoringInput(
            warehouse_id=wh.id,
            operating_status=wh.operating_status.value,
            warehouse_latitude=wh.latitude,
            warehouse_longitude=wh.longitude,
            incident_latitude=incident.latitude,
            incident_longitude=incident.longitude,
            requested_quantities=demands,
            available_quantities=inv_dict,
            eligible_vehicles=vehicle_inputs,
            warehouse_maximum_dispatch_capacity=wh.maximum_dispatch_capacity,
            warehouse_current_dispatch_workload=wh.current_dispatch_workload,
            route_risk=route.risk_level.value if route else "low",
            route_blocked=bool(route.is_blocked) if route else False,
            estimated_delay_minutes=route.estimated_delay_minutes if route else 0,
        )
        scoring_inputs.append(inp)

    ranked_outputs = rank_relief_warehouses(scoring_inputs)

    recommendations = []
    for out in ranked_outputs:
        wh = next(w for w in warehouses if w.id == out.warehouse_id)
        route = get_route_condition(db, incident.id, wh.id)

        if out.total_supplied_units == 0:
            continue

        covered_items = [
            s.item_type for s in out.per_item_supplies if s.fully_covered
        ]
        missing_items = [
            s.item_type for s in out.per_item_supplies if s.missing > 0
        ]

        reasons = []
        limitations = []

        if out.stock_coverage_pct == 100:
            reasons.append("Can fully supply all requested quantities.")
        else:
            limitations.append(f"Can only supply {out.stock_coverage_pct:.1f}% of requested units.")

        if out.distance_km <= 10:
            reasons.append(f"Very close to incident (Straight-line distance: {out.distance_km:.1f} km).")
        elif out.distance_km > 50:
            limitations.append(f"Far from incident (Straight-line distance: {out.distance_km:.1f} km).")

        total_veh_capacity = sum(
            v.capacity_units for v in get_available_vehicles(db, wh.id)
            if v.availability_status == VehicleAvailability.available
        )
        if total_veh_capacity >= out.total_supplied_units:
            reasons.append("Sufficient delivery vehicle capacity.")
        elif total_veh_capacity > 0:
            limitations.append("Insufficient vehicle capacity for full dispatch at once.")
        else:
            limitations.append("No available delivery vehicles.")

        route_risk_str = route.risk_level.value if route else "low"
        if route:
            if route.risk_level == RouteRisk.low:
                reasons.append("Route is safe.")
            elif route.risk_level == RouteRisk.medium:
                limitations.append(f"Medium route risk: {route.description}")
            else:
                limitations.append(f"High route risk: {route.description}")
        else:
            reasons.append("No known route hazards.")

        workload_ratio = wh.current_dispatch_workload / max(1, wh.maximum_dispatch_capacity)
        if workload_ratio < 0.3:
            reasons.append("Warehouse has low current workload.")
        elif workload_ratio >= 0.8:
            limitations.append("Warehouse is highly loaded.")

        explanation = f"Total Score: {out.total_score:.1f}/100. "
        if reasons:
            explanation += "Pros: " + "; ".join(reasons) + ". "
        if limitations:
            explanation += "Cons: " + "; ".join(limitations) + "."

        recommendations.append(ReliefRecommendationResponse(
            warehouse_id=wh.id,
            warehouse_name=wh.name,
            rank=0,
            total_score=round(out.total_score, 1),
            stock_coverage_percentage=round(out.stock_coverage_pct, 1),
            covered_items=covered_items,
            missing_items=missing_items,
            distance_km=round(out.distance_km, 1),
            vehicle_availability=len([
                v for v in get_available_vehicles(db, wh.id)
                if v.availability_status == VehicleAvailability.available
            ]) > 0,
            route_risk=route_risk_str,
            positive_reasons=reasons,
            limitations=limitations,
            explanation=explanation
        ))

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