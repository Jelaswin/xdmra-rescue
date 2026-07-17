"""
Pure relief warehouse scoring functions for X-DMRA research evaluation.

Copies exact production relief_allocation_service.py scoring behavior.
No database access, no writes, no allocation logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.services.scoring.common import haversine_distance, normalize_string_set


@dataclass(frozen=True)
class ReliefVehicleInput:
    """Delivery vehicle for relief scoring."""
    vehicle_id: int
    capacity_units: int
    availability_status: str


@dataclass(frozen=True)
class ReliefScoringInput:
    """Complete typed input for relief warehouse scoring."""
    warehouse_id: int
    operating_status: str
    warehouse_latitude: float
    warehouse_longitude: float
    incident_latitude: float
    incident_longitude: float
    requested_quantities: Dict[str, int]
    available_quantities: Dict[str, int]
    eligible_vehicles: List[ReliefVehicleInput]
    warehouse_maximum_dispatch_capacity: int
    warehouse_current_dispatch_workload: int
    route_risk: str
    route_blocked: bool
    estimated_delay_minutes: int


@dataclass(frozen=True)
class ReliefItemSupply:
    """Per-item supply result."""
    item_type: str
    requested: int
    supplied: int
    missing: int
    fully_covered: bool


@dataclass(frozen=True)
class ReliefScoringOutput:
    """Complete typed output from relief warehouse scoring."""
    warehouse_id: int
    eligible: bool
    eligibility_reason: Optional[str]
    distance_km: float
    per_item_supplies: Tuple[ReliefItemSupply, ...]
    total_requested_units: int
    total_supplied_units: int
    stock_coverage_pct: float
    covered_item_count: int
    total_demand_item_count: int
    item_coverage_pct: float
    stock_score: float
    item_score: float
    distance_score: float
    vehicle_score: float
    route_score: float
    workload_score: float
    total_score: float


WEIGHT_STOCK_COVERAGE = 35.0
WEIGHT_ITEM_COVERAGE = 15.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VEHICLE_CAPACITY = 15.0
WEIGHT_ROUTE_SAFETY = 10.0
WEIGHT_WORKLOAD = 10.0


def score_relief_warehouse(inp: ReliefScoringInput) -> ReliefScoringOutput:
    """
    Compute relief warehouse eligibility and multi-factor score.

    Exact production behavior from relief_allocation_service.py:
    - Stock coverage: 0-35 pts
    - Item coverage: 0-15 pts
    - Distance: 15 / 10.5 / 4.5 pts (tiered)
    - Vehicle capacity: 0-15 pts
    - Route safety: 10 / 5 / 2 pts (tiered)
    - Workload: 10 / 5 / 1 pts (ratio-based)

    Eligibility:
    - operating_status must be "active" or "limited"
    - route must not be blocked
    - at least one eligible vehicle required
    - positive supplied quantity required

    Per-item supply: min(available[item], requested[item])
    Excess of one item NEVER compensates for shortage of another.
    """
    warehouse_id = inp.warehouse_id

    if inp.operating_status not in ("active", "limited"):
        return ReliefScoringOutput(
            warehouse_id=warehouse_id,
            eligible=False,
            eligibility_reason="Warehouse operating_status is not 'active' or 'limited'",
            distance_km=0.0,
            per_item_supplies=(),
            total_requested_units=0,
            total_supplied_units=0,
            stock_coverage_pct=0.0,
            covered_item_count=0,
            total_demand_item_count=0,
            item_coverage_pct=0.0,
            stock_score=0.0,
            item_score=0.0,
            distance_score=0.0,
            vehicle_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    if inp.route_blocked:
        return ReliefScoringOutput(
            warehouse_id=warehouse_id,
            eligible=False,
            eligibility_reason="Route to incident is blocked",
            distance_km=0.0,
            per_item_supplies=(),
            total_requested_units=0,
            total_supplied_units=0,
            stock_coverage_pct=0.0,
            covered_item_count=0,
            total_demand_item_count=0,
            item_coverage_pct=0.0,
            stock_score=0.0,
            item_score=0.0,
            distance_score=0.0,
            vehicle_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    eligible_vehicles = [
        v for v in inp.eligible_vehicles
        if v.availability_status == "available"
    ]
    if not eligible_vehicles:
        return ReliefScoringOutput(
            warehouse_id=warehouse_id,
            eligible=False,
            eligibility_reason="No available delivery vehicles at warehouse",
            distance_km=0.0,
            per_item_supplies=(),
            total_requested_units=0,
            total_supplied_units=0,
            stock_coverage_pct=0.0,
            covered_item_count=0,
            total_demand_item_count=0,
            item_coverage_pct=0.0,
            stock_score=0.0,
            item_score=0.0,
            distance_score=0.0,
            vehicle_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    demands = {k: v for k, v in inp.requested_quantities.items() if v > 0}
    if not demands:
        return ReliefScoringOutput(
            warehouse_id=warehouse_id,
            eligible=False,
            eligibility_reason="No positive-demand items in relief request",
            distance_km=0.0,
            per_item_supplies=(),
            total_requested_units=0,
            total_supplied_units=0,
            stock_coverage_pct=0.0,
            covered_item_count=0,
            total_demand_item_count=0,
            item_coverage_pct=0.0,
            stock_score=0.0,
            item_score=0.0,
            distance_score=0.0,
            vehicle_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    total_requested_units = sum(demands.values())

    item_supplies: List[ReliefItemSupply] = []
    covered_items: List[str] = []
    total_supplied = 0

    for item_type, req_qty in demands.items():
        avail = inp.available_quantities.get(item_type, 0)
        if avail > 0:
            supplied = min(req_qty, avail)
            total_supplied += supplied
            fully_covered = avail >= req_qty
            if fully_covered:
                covered_items.append(item_type)
            item_supplies.append(ReliefItemSupply(
                item_type=item_type,
                requested=req_qty,
                supplied=supplied,
                missing=max(0, req_qty - avail),
                fully_covered=fully_covered,
            ))
        else:
            item_supplies.append(ReliefItemSupply(
                item_type=item_type,
                requested=req_qty,
                supplied=0,
                missing=req_qty,
                fully_covered=False,
            ))

    if total_supplied == 0:
        return ReliefScoringOutput(
            warehouse_id=warehouse_id,
            eligible=False,
            eligibility_reason="Warehouse cannot supply any requested items",
            distance_km=0.0,
            per_item_supplies=tuple(item_supplies),
            total_requested_units=total_requested_units,
            total_supplied_units=0,
            stock_coverage_pct=0.0,
            covered_item_count=0,
            total_demand_item_count=len(demands),
            item_coverage_pct=0.0,
            stock_score=0.0,
            item_score=0.0,
            distance_score=0.0,
            vehicle_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    stock_coverage_pct = (total_supplied / total_requested_units) * 100.0
    stock_score = (stock_coverage_pct / 100.0) * WEIGHT_STOCK_COVERAGE

    item_coverage_pct = (len(covered_items) / len(demands)) * 100.0
    item_score = (item_coverage_pct / 100.0) * WEIGHT_ITEM_COVERAGE

    dist_km = haversine_distance(
        inp.warehouse_latitude, inp.warehouse_longitude,
        inp.incident_latitude, inp.incident_longitude
    )
    if dist_km <= 10.0:
        distance_score = WEIGHT_DISTANCE
    elif dist_km <= 50.0:
        distance_score = WEIGHT_DISTANCE * 0.7
    else:
        distance_score = WEIGHT_DISTANCE * 0.3

    total_veh_capacity = sum(v.capacity_units for v in eligible_vehicles)
    if total_veh_capacity >= total_supplied:
        vehicle_score = WEIGHT_VEHICLE_CAPACITY
    elif total_veh_capacity > 0:
        vehicle_score = WEIGHT_VEHICLE_CAPACITY * (total_veh_capacity / total_supplied)
    else:
        vehicle_score = 0.0

    if inp.route_risk == "low":
        route_score = WEIGHT_ROUTE_SAFETY
    elif inp.route_risk == "medium":
        route_score = WEIGHT_ROUTE_SAFETY * 0.5
    elif inp.route_risk == "high":
        route_score = WEIGHT_ROUTE_SAFETY * 0.2
    else:
        route_score = WEIGHT_ROUTE_SAFETY

    denom = max(1, inp.warehouse_maximum_dispatch_capacity)
    workload_ratio = inp.warehouse_current_dispatch_workload / denom
    if workload_ratio < 0.3:
        workload_score = WEIGHT_WORKLOAD
    elif workload_ratio < 0.8:
        workload_score = WEIGHT_WORKLOAD * 0.5
    else:
        workload_score = WEIGHT_WORKLOAD * 0.1

    total_score = stock_score + item_score + distance_score + vehicle_score + route_score + workload_score

    return ReliefScoringOutput(
        warehouse_id=warehouse_id,
        eligible=True,
        eligibility_reason=None,
        distance_km=round(dist_km, 2),
        per_item_supplies=tuple(item_supplies),
        total_requested_units=total_requested_units,
        total_supplied_units=total_supplied,
        stock_coverage_pct=round(stock_coverage_pct, 4),
        covered_item_count=len(covered_items),
        total_demand_item_count=len(demands),
        item_coverage_pct=round(item_coverage_pct, 4),
        stock_score=round(stock_score, 4),
        item_score=round(item_score, 4),
        distance_score=round(distance_score, 4),
        vehicle_score=round(vehicle_score, 4),
        route_score=round(route_score, 4),
        workload_score=round(workload_score, 4),
        total_score=round(total_score, 4),
    )


def rank_relief_warehouses(
    inputs: List[ReliefScoringInput],
) -> List[ReliefScoringOutput]:
    """
    Score and rank all warehouses for a relief request.
    Returns sorted list (highest score first), eligible only.
    """
    scored = [score_relief_warehouse(inp) for inp in inputs]
    eligible = [s for s in scored if s.eligible]
    eligible.sort(key=lambda x: x.total_score, reverse=True)
    return eligible