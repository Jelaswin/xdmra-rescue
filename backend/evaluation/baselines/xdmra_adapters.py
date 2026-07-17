"""
X-DMRA Production Service Adapters for Evaluation.

These adapters allow the evaluation framework to call existing production
allocation services using in-memory scenario objects, without modifying
operational database state.

All adapters return results in the same format as baseline algorithms.
Haversine distances are explicitly labelled as straight-line distance.
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.services.allocation_service import (
    calculate_team_recommendations as production_rescue_recommendations,
)
from app.services.scoring.common import haversine_distance
from app.services.scoring.rescue_scoring import RescueScoringInput, rank_rescue_teams
from app.services.scoring.relief_scoring import (
    ReliefVehicleInput, ReliefScoringInput, rank_relief_warehouses,
)
from app.services.scoring.shelter_scoring import (
    ShelterScoringInput, rank_shelters,
)

from app.models import TeamAvailability, RouteRisk


def _str_to_set(str_list: List[str]) -> set:
    """Normalize strings to lowercase set."""
    if not str_list:
        return set()
    return set(s.lower().replace("-", "_").replace(" ", "_") for s in str_list)


class _FakeTeam:
    """Lightweight team adapter that mimics SQLAlchemy RescueTeam interface."""
    def __init__(
        self,
        team_id: int,
        name: str,
        latitude: float,
        longitude: float,
        availability_status: str,
        skills: List[str],
        equipment: List[str],
        capacity: int,
        current_workload: int = 0
    ):
        self.id = team_id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.availability_status = TeamAvailability(availability_status)
        self.skills = skills
        self.equipment = equipment
        self.capacity = capacity
        self.current_workload = current_workload


class _FakeIncident:
    """Lightweight incident adapter that mimics SQLAlchemy Incident interface."""
    def __init__(
        self,
        incident_id: int,
        latitude: float,
        longitude: float,
        affected_people: int,
        required_skills: List[str],
        required_equipment: List[str]
    ):
        self.id = incident_id
        self.latitude = latitude
        self.longitude = longitude
        self.affected_people = affected_people
        self.required_skills = required_skills
        self.required_equipment = required_equipment


class _FakeRouteCondition:
    """Lightweight route condition adapter."""
    def __init__(
        self,
        incident_id: int,
        rescue_team_id: int,
        risk_level: str = "low",
        is_blocked: bool = False,
        estimated_delay_minutes: int = 0
    ):
        self.incident_id = incident_id
        self.rescue_team_id = rescue_team_id
        self.risk_level = RouteRisk(risk_level)
        self.is_blocked = 1 if is_blocked else 0
        self.estimated_delay_minutes = estimated_delay_minutes


class XDMRAExplainableAdapter:
    """Evaluation adapter that calls production rescue recommendation service.

    Reuses existing production scoring and explanation logic.
    Returns results in baseline-compatible format.
    """

    name = "xdmra_explainable"

    def select(self, scenario) -> "XDMRAExplainableResult":
        """Execute X-DMRA rescue allocation for a scenario."""
        start_time = time.perf_counter()

        available_teams = [
            t for t in scenario.available_teams
            if t.get("availability_status", "available") == "available"
        ]

        if not available_teams:
            return XDMRAExplainableResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                selected_team_id=None,
                selected_team_name=None,
                distance_km=0.0,
                skill_match_pct=0.0,
                equipment_match_pct=0.0,
                route_blocked=False,
                score=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No available teams",
                explanation="No available teams could be found for this incident."
            )

        fake_teams = [
            _FakeTeam(
                team_id=t["id"],
                name=t["name"],
                latitude=t["latitude"],
                longitude=t["longitude"],
                availability_status=t.get("availability_status", "available"),
                skills=t.get("skills", []),
                equipment=t.get("equipment", []),
                capacity=t.get("capacity", 10),
                current_workload=t.get("current_workload", 0)
            )
            for t in available_teams
        ]

        fake_incident = _FakeIncident(
            incident_id=scenario.incident_id,
            latitude=scenario.latitude,
            longitude=scenario.longitude,
            affected_people=scenario.affected_people,
            required_skills=scenario.required_skills,
            required_equipment=scenario.required_equipment
        )

        route_conditions = [
            _FakeRouteCondition(
                incident_id=scenario.incident_id,
                rescue_team_id=t["id"],
                risk_level="low",
                is_blocked=t.get("route_blocked", False),
                estimated_delay_minutes=0
            )
            for t in available_teams
        ]

        recommendations = production_rescue_recommendations(
            fake_incident, fake_teams, route_conditions
        )

        if not recommendations:
            return XDMRAExplainableResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                selected_team_id=None,
                selected_team_name=None,
                distance_km=0.0,
                skill_match_pct=0.0,
                equipment_match_pct=0.0,
                route_blocked=False,
                score=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="X-DMRA could not generate recommendations",
                explanation="X-DMRA allocation algorithm could not produce a recommendation for this scenario."
            )

        top = recommendations[0]

        return XDMRAExplainableResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=top.team_id,
            selected_team_name=top.team_name,
            distance_km=top.distance_km,
            skill_match_pct=top.skill_match_percentage,
            equipment_match_pct=top.equipment_match_percentage,
            route_blocked=False,
            score=top.total_score,
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            explanation=top.explanation
        )


@dataclass
class XDMRAExplainableResult:
    """Result from X-DMRA explainable rescue evaluation."""
    algorithm: str
    scenario_id: str
    success: bool
    selected_team_id: Optional[int]
    selected_team_name: Optional[str]
    distance_km: float
    skill_match_pct: float
    equipment_match_pct: float
    route_blocked: bool
    score: float
    computation_time_ms: float
    failure_reason: Optional[str] = None
    explanation: Optional[str] = None


class XDMRAExplainableResultAdapter:
    """Convert XDMRAExplainableResult to baseline-compatible RescueBaselineResult format."""

    @staticmethod
    def convert(xdmra_result: XDMRAExplainableResult) -> Dict[str, Any]:
        return {
            "algorithm": xdmra_result.algorithm,
            "scenario_id": xdmra_result.scenario_id,
            "success": xdmra_result.success,
            "selected_team_id": xdmra_result.selected_team_id,
            "selected_team_name": xdmra_result.selected_team_name,
            "distance_km": xdmra_result.distance_km,
            "skill_match_pct": xdmra_result.skill_match_pct,
            "equipment_match_pct": xdmra_result.equipment_match_pct,
            "route_blocked": xdmra_result.route_blocked,
            "score": xdmra_result.score,
            "computation_time_ms": xdmra_result.computation_time_ms,
            "failure_reason": xdmra_result.failure_reason,
            "explanation": xdmra_result.explanation,
            "selected_team_workload": 0,
            "priority_level": "unknown",
        }


def get_all_rescue_algorithms_with_xdmra() -> Dict[str, Any]:
    """Return all rescue algorithms including X-DMRA."""
    from evaluation.baselines.rescue_baselines import (
        RandomAvailableBaseline, FirstAvailableBaseline, NearestAvailableBaseline,
        SkillMatchOnlyBaseline, PriorityDistanceOnlyBaseline
    )
    return {
        "random_available": RandomAvailableBaseline(seed=42),
        "first_available": FirstAvailableBaseline(),
        "nearest_available": NearestAvailableBaseline(),
        "skill_match_only": SkillMatchOnlyBaseline(),
        "priority_distance_only": PriorityDistanceOnlyBaseline(),
        "xdmra_explainable": XDMRAExplainableAdapter(),
    }


def run_rescue_with_xdmra(scenarios: List, algorithms: List[str], repeat: int = 1, seed: int = 42) -> Dict[str, Any]:
    """Run rescue experiment with X-DMRA included."""
    from evaluation.baselines.rescue_baselines import get_all_rescue_baselines
    import random
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)

    all_baselines = get_all_rescue_algorithms_with_xdmra()

    all_results = []
    all_metrics = {}

    for algo_name in algorithms:
        if algo_name not in all_baselines:
            continue
        baseline = all_baselines[algo_name]
        rng = random.Random(seed)

        algo_results = []
        for iteration in range(repeat):
            for scenario in scenarios:
                if hasattr(baseline, 'select'):
                    result = baseline.select(scenario)
                    scenario_result = XDMRAExplainableResultAdapter.convert(result)
                    scenario_result["iteration"] = iteration
                    scenario_result["priority_level"] = getattr(scenario, "priority_level", "unknown")
                    algo_results.append(scenario_result)
                else:
                    continue

        if algo_results:
            from evaluation.metrics import calculate_rescue_metrics
            algo_metrics = calculate_rescue_metrics(algo_results)
            all_metrics[algo_name] = algo_metrics
            all_results.extend(algo_results)

    return {
        "results": all_results,
        "metrics": all_metrics,
        "scenario_count": len(scenarios),
        "algorithms": algorithms,
    }


# ============================================================================
# X-DMRA Relief Adapter
# Uses exact production scoring via shared scoring module:
# WEIGHT_STOCK_COVERAGE=35, WEIGHT_ITEM_COVERAGE=15, WEIGHT_DISTANCE=15,
# WEIGHT_VEHICLE_CAPACITY=15, WEIGHT_ROUTE_SAFETY=10, WEIGHT_WORKLOAD=10
# ============================================================================


class XDMRAReliefAdapter:
    """X-DMRA relief allocation using exact production scoring.

    Calls shared scoring module which mirrors production behavior.
    """

    name = "xdmra_relief_allocation"

    def select(self, scenario) -> "XDMRAReliefResult":
        """Execute X-DMRA relief allocation for a scenario.

        Implements true split allocation across multiple warehouses:
        1. Score and rank all warehouses using production scoring.
        2. Allocate per-item min(requested, available) from each ranked warehouse
           until all demand is fulfilled or no warehouses remain.
        3. Per-item demand is capped: no item ever receives more than requested.
        4. Per-item supply from each warehouse is capped at that warehouse's stock.
        """
        start_time = time.perf_counter()

        total_requested = sum(scenario.items.values()) if scenario.items else 0

        if not scenario.warehouses or total_requested == 0:
            return XDMRAReliefResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=total_requested,
                distance_km=0.0,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No warehouses available" if not scenario.warehouses else "No demand",
                total_requested=total_requested
            )

        scoring_inputs = []
        for wh in scenario.warehouses:
            inv = wh.get("inventory", {})
            vehicles = wh.get("vehicles", [])
            route_risk_str = wh.get("route_risk", "low")

            inp = ReliefScoringInput(
                warehouse_id=wh["id"],
                operating_status=wh.get("operating_status", "active"),
                warehouse_latitude=wh["latitude"],
                warehouse_longitude=wh["longitude"],
                incident_latitude=scenario.latitude,
                incident_longitude=scenario.longitude,
                requested_quantities=scenario.items,
                available_quantities=inv,
                eligible_vehicles=[
                    ReliefVehicleInput(
                        vehicle_id=v.get("id", 0),
                        capacity_units=v.get("capacity_units", 0),
                        availability_status=v.get("availability_status", "available"),
                    )
                    for v in vehicles
                ],
                warehouse_maximum_dispatch_capacity=wh.get("maximum_dispatch_capacity", 0),
                warehouse_current_dispatch_workload=wh.get("current_workload", 0),
                route_risk=route_risk_str,
                route_blocked=wh.get("route_blocked", False),
                estimated_delay_minutes=wh.get("estimated_delay_minutes", 0),
            )
            scoring_inputs.append(inp)

        ranked = rank_relief_warehouses(scoring_inputs)

        if not ranked:
            return XDMRAReliefResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                warehouses_used=[],
                fulfilment_pct=0.0,
                shortage=total_requested,
                distance_km=0.0,
                stock_violations=0,
                split_allocation=False,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No eligible warehouse found",
                total_requested=total_requested
            )

        remaining_demand = {k: v for k, v in scenario.items.items() if v > 0}
        selected_warehouses = []
        total_supplied = 0
        split = False

        for scored_wh in ranked:
            if not remaining_demand:
                break
            wh_output = scored_wh
            wh_id = wh_output.warehouse_id

            allocated_from_wh = {}
            warehouse_supplied = 0

            for item_supply in wh_output.per_item_supplies:
                item = item_supply.item_type
                if item not in remaining_demand:
                    continue
                can_give = min(item_supply.supplied, remaining_demand[item])
                if can_give <= 0:
                    continue
                allocated_from_wh[item] = can_give
                remaining_demand[item] -= can_give
                warehouse_supplied += can_give
                total_supplied += can_give

            if allocated_from_wh:
                selected_warehouses.append(wh_id)
                if len(selected_warehouses) > 1:
                    split = True

        total_shortage = sum(remaining_demand.values())
        if total_supplied > 0 and total_requested > 0:
            fulfilment_pct = (total_supplied / total_requested) * 100.0
        else:
            fulfilment_pct = 0.0

        avg_distance = 0.0
        if selected_warehouses:
            dists = [scored_wh.distance_km for scored_wh in ranked if scored_wh.warehouse_id in selected_warehouses]
            avg_distance = sum(dists) / len(dists) if dists else 0.0

        return XDMRAReliefResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=total_supplied > 0,
            warehouses_used=selected_warehouses,
            fulfilment_pct=round(fulfilment_pct, 4),
            shortage=int(total_shortage),
            distance_km=round(avg_distance, 2),
            stock_violations=0,
            split_allocation=split,
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            failure_reason=None,
            total_requested=total_requested
        )


@dataclass
class XDMRAReliefResult:
    algorithm: str
    scenario_id: str
    success: bool
    warehouses_used: List[int]
    fulfilment_pct: float
    shortage: int
    distance_km: float
    stock_violations: int
    split_allocation: bool
    computation_time_ms: float
    total_requested: int
    failure_reason: Optional[str] = None


class XDMRAReliefResultAdapter:
    @staticmethod
    def convert(result: XDMRAReliefResult) -> Dict[str, Any]:
        return {
            "algorithm": result.algorithm,
            "scenario_id": result.scenario_id,
            "success": result.success,
            "warehouses_used": result.warehouses_used,
            "fulfilment_pct": result.fulfilment_pct,
            "shortage": result.shortage,
            "total_requested": result.total_requested,
            "distance_km": result.distance_km,
            "stock_violations": result.stock_violations,
            "split_allocation": result.split_allocation,
            "computation_time_ms": result.computation_time_ms,
            "failure_reason": result.failure_reason,
        }


def get_all_relief_algorithms_with_xdmra() -> Dict[str, Any]:
    """Return all relief algorithms including X-DMRA."""
    from evaluation.baselines.relief_baselines import (
        FirstStockedWarehouseBaseline, NearestStockedWarehouseBaseline,
        HighestStockCoverageBaseline, SingleWarehouseOnlyBaseline
    )
    return {
        "first_stocked_warehouse": FirstStockedWarehouseBaseline(),
        "nearest_stocked_warehouse": NearestStockedWarehouseBaseline(),
        "highest_stock_coverage": HighestStockCoverageBaseline(),
        "single_warehouse_only": SingleWarehouseOnlyBaseline(),
        "xdmra_relief_allocation": XDMRAReliefAdapter(),
    }


# ============================================================================
# X-DMRA Shelter Adapter
# Uses exact production scoring via shared scoring module:
# WEIGHT_CAPACITY=30, WEIGHT_DISTANCE=15, WEIGHT_VULNERABILITY=20,
# WEIGHT_UTILITIES=15, WEIGHT_OVERCROWDING=10, WEIGHT_ROUTE_SAFETY=5, WEIGHT_WORKLOAD=5
# ============================================================================


class XDMRAShelterAdapter:
    """X-DMRA shelter allocation using exact production scoring.

    Calls shared scoring module which mirrors production behavior.
    """

    name = "xdmra_shelter_allocation"

    def select(self, scenario) -> "XDMRAShelterResult":
        """Execute X-DMRA shelter allocation for a scenario.

        Implements true split allocation across multiple shelters:
        1. Score and rank all shelters using production scoring.
        2. Greedily allocate from each ranked shelter until demand is met.
        3. allocated never exceeds min(demand remaining, available capacity).
        4. Coverage is actual allocated / displaced.
        5. Overcrowding >= 95% projected occupancy = critical.
        """
        start_time = time.perf_counter()

        total_displaced = scenario.displaced_people

        if not scenario.shelters:
            return XDMRAShelterResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=total_displaced,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                total_displaced_people=total_displaced,
                total_allocated_population=0,
                overcrowding_risk_level="low",
                medical_requirement_satisfied=False,
                accessibility_requirement_satisfied=False,
                failure_reason="No shelters available",
            )

        scoring_inputs = []
        for shelter in scenario.shelters:
            inp = ShelterScoringInput(
                shelter_id=shelter["id"],
                operating_status=shelter.get("operating_status", "open"),
                shelter_latitude=shelter["latitude"],
                shelter_longitude=shelter["longitude"],
                incident_latitude=scenario.latitude,
                incident_longitude=scenario.longitude,
                total_displaced_people=total_displaced,
                total_capacity=shelter.get("total_capacity", 0),
                occupied_capacity=shelter.get("occupied_capacity", 0),
                reserved_capacity=shelter.get("reserved_capacity", 0),
                maximum_daily_intake=shelter.get("maximum_daily_intake", 0),
                current_intake_workload=shelter.get("current_workload", 0),
                has_medical_support=bool(shelter.get("has_medical_support", False)),
                has_accessibility_support=bool(shelter.get("has_accessibility_support", False)),
                has_women_child_safe_area=bool(shelter.get("has_women_child_safe_area", False)),
                has_food=bool(shelter.get("has_food", False)),
                has_drinking_water=bool(shelter.get("has_drinking_water", False)),
                has_sanitation=bool(shelter.get("has_sanitation", False)),
                has_power_backup=bool(shelter.get("has_power_backup", False)),
                supports_long_term_stay=bool(shelter.get("supports_long_term_stay", False)),
                mandatory_medical_required=bool(scenario.medical_required),
                mandatory_accessibility_required=bool(scenario.accessibility_required),
                route_risk=shelter.get("route_risk", "low"),
                route_blocked=shelter.get("route_blocked", False),
                estimated_delay_minutes=shelter.get("estimated_delay_minutes", 0),
            )
            scoring_inputs.append(inp)

        ranked = rank_shelters(scoring_inputs)

        if not ranked:
            return XDMRAShelterResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=total_displaced,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                total_displaced_people=total_displaced,
                total_allocated_population=0,
                overcrowding_risk_level="low",
                medical_requirement_satisfied=False,
                accessibility_requirement_satisfied=False,
                failure_reason="No eligible shelter found",
            )

        remaining = total_displaced
        allocated_total = 0
        selected_shelter_ids = []
        max_overcrowding_risk = "low"
        med_req_sat = False
        acc_req_sat = False

        for scored_shelter in ranked:
            if remaining <= 0:
                break
            shelter_output = scored_shelter
            proposed = min(remaining, shelter_output.proposed_people_count)
            if proposed <= 0:
                continue
            allocated_total += proposed
            remaining -= proposed
            selected_shelter_ids.append(shelter_output.shelter_id)
            if shelter_output.overcrowding_risk_level == "critical":
                max_overcrowding_risk = "critical"
            elif shelter_output.overcrowding_risk_level == "high" and max_overcrowding_risk != "critical":
                max_overcrowding_risk = "high"
            if shelter_output.eligible:
                if scenario.medical_required:
                    med_req_sat = shelter_output.medical_support_score > 0
                else:
                    med_req_sat = True
                if scenario.accessibility_required:
                    acc_req_sat = shelter_output.accessibility_support_score > 0
                else:
                    acc_req_sat = True

        coverage = (allocated_total / total_displaced * 100) if total_displaced > 0 else 0.0
        uncovered = max(0, total_displaced - allocated_total)
        overcrowded = 1 if max_overcrowding_risk == "critical" else 0

        avg_distance = 0.0
        if selected_shelter_ids:
            dists = [s.distance_km for s in ranked if s.shelter_id in selected_shelter_ids]
            avg_distance = sum(dists) / len(dists) if dists else 0.0

        both_sat = med_req_sat and acc_req_sat
        one_sat = med_req_sat or acc_req_sat
        req_match = 100.0 if both_sat else (50.0 if one_sat else 0.0)

        return XDMRAShelterResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=allocated_total > 0,
            shelters_used=selected_shelter_ids,
            population_coverage_pct=round(coverage, 4),
            uncovered_people=int(uncovered),
            overcrowding_violations=overcrowded,
            requirement_match_pct=req_match,
            distance_km=round(avg_distance, 2),
            computation_time_ms=(time.perf_counter() - start_time) * 1000,
            total_displaced_people=total_displaced,
            total_allocated_population=allocated_total,
            overcrowding_risk_level=max_overcrowding_risk,
            medical_requirement_satisfied=med_req_sat,
            accessibility_requirement_satisfied=acc_req_sat,
            failure_reason=None,
        )


@dataclass
class XDMRAShelterResult:
    algorithm: str
    scenario_id: str
    success: bool
    shelters_used: List[int]
    population_coverage_pct: float
    uncovered_people: int
    overcrowding_violations: int
    requirement_match_pct: float
    distance_km: float
    computation_time_ms: float
    total_displaced_people: int
    total_allocated_population: int
    overcrowding_risk_level: str
    medical_requirement_satisfied: bool
    accessibility_requirement_satisfied: bool
    failure_reason: Optional[str] = None


class XDMRAShelterResultAdapter:
    @staticmethod
    def convert(result: XDMRAShelterResult) -> Dict[str, Any]:
        return {
            "algorithm": result.algorithm,
            "scenario_id": result.scenario_id,
            "success": result.success,
            "shelters_used": result.shelters_used,
            "population_coverage_pct": result.population_coverage_pct,
            "uncovered_people": result.uncovered_people,
            "overcrowding_violations": result.overcrowding_violations,
            "requirement_match_pct": result.requirement_match_pct,
            "distance_km": result.distance_km,
            "computation_time_ms": result.computation_time_ms,
            "total_displaced_people": result.total_displaced_people,
            "total_allocated_population": result.total_allocated_population,
            "overcrowding_risk_level": result.overcrowding_risk_level,
            "medical_requirement_satisfied": result.medical_requirement_satisfied,
            "accessibility_requirement_satisfied": result.accessibility_requirement_satisfied,
            "failure_reason": result.failure_reason,
        }


def get_all_shelter_algorithms_with_xdmra() -> Dict[str, Any]:
    """Return all shelter algorithms including X-DMRA."""
    from evaluation.baselines.shelter_baselines import (
        NearestAvailableShelterBaseline, LargestCapacityShelterBaseline,
        FirstAvailableShelterBaseline, CapacityOnlyBaseline
    )
    return {
        "nearest_available_shelter": NearestAvailableShelterBaseline(),
        "largest_capacity_shelter": LargestCapacityShelterBaseline(),
        "first_available_shelter": FirstAvailableShelterBaseline(),
        "capacity_only": CapacityOnlyBaseline(),
        "xdmra_shelter_allocation": XDMRAShelterAdapter(),
    }