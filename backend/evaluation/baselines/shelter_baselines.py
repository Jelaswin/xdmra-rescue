"""
Shelter Baseline Evaluation Strategies.

These are evaluation-only baseline algorithms that do NOT modify
the production X-DMRA allocation system.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass
class ShelterScenario:
    """A test scenario for shelter evaluation."""
    scenario_id: str
    incident_id: int
    displaced_people: int
    medical_required: bool
    accessibility_required: bool
    latitude: float
    longitude: float
    shelters: List[Dict[str, Any]]


@dataclass
class ShelterBaselineResult:
    """Result from a shelter baseline strategy."""
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


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def _compute_shelter_allocation(
    scenario: ShelterScenario,
    selected_shelter: Dict[str, Any],
    distance: float,
    name: str,
    start_time,
) -> ShelterBaselineResult:
    import time
    total_displaced = scenario.displaced_people
    available = (selected_shelter.get("total_capacity", 0)
                 - selected_shelter.get("occupied_capacity", 0)
                 - selected_shelter.get("reserved_capacity", 0))
    allocated = min(available, total_displaced)
    coverage = (allocated / total_displaced * 100) if total_displaced > 0 else 0.0
    uncovered = max(0, total_displaced - allocated)

    med_sat = (not scenario.medical_required) or bool(selected_shelter.get("has_medical_support"))
    acc_sat = (not scenario.accessibility_required) or bool(selected_shelter.get("has_accessibility_support"))
    req_match = 100.0 if (med_sat and acc_sat) else (50.0 if (med_sat or acc_sat) else 0.0)

    req_cap = selected_shelter.get("total_capacity", 0)
    occ = selected_shelter.get("occupied_capacity", 0)
    res = selected_shelter.get("reserved_capacity", 0)
    projected = (occ + res + allocated) / req_cap * 100 if req_cap > 0 else 100.0
    overcrowded = 1 if projected >= 95.0 else 0
    risk = "critical" if projected >= 95.0 else ("high" if projected >= 85.0 else ("moderate" if projected >= 70.0 else "low"))

    return ShelterBaselineResult(
        algorithm=name,
        scenario_id=scenario.scenario_id,
        success=True,
        shelters_used=[selected_shelter["id"]],
        population_coverage_pct=coverage,
        uncovered_people=uncovered,
        overcrowding_violations=overcrowded,
        requirement_match_pct=req_match,
        distance_km=distance,
        computation_time_ms=(time.perf_counter() - start_time) * 1000,
        total_displaced_people=total_displaced,
        total_allocated_population=allocated,
        overcrowding_risk_level=risk,
        medical_requirement_satisfied=med_sat,
        accessibility_requirement_satisfied=acc_sat,
    )


def _shelter_not_found_result(scenario: ShelterScenario, name: str, reason: str, start_time) -> ShelterBaselineResult:
    import time
    return ShelterBaselineResult(
        algorithm=name,
        scenario_id=scenario.scenario_id,
        success=False,
        shelters_used=[],
        population_coverage_pct=0.0,
        uncovered_people=scenario.displaced_people,
        overcrowding_violations=0,
        requirement_match_pct=0.0,
        distance_km=0.0,
        computation_time_ms=(time.perf_counter() - start_time) * 1000,
        total_displaced_people=scenario.displaced_people,
        total_allocated_population=0,
        overcrowding_risk_level="low",
        medical_requirement_satisfied=False,
        accessibility_requirement_satisfied=False,
        failure_reason=reason,
    )


class NearestAvailableShelterBaseline:
    name = "nearest_available_shelter"

    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            available = (shelter.get("total_capacity", 0)
                        - shelter.get("occupied_capacity", 0)
                        - shelter.get("reserved_capacity", 0))
            if available <= 0:
                continue
            distance = haversine_distance(scenario.latitude, scenario.longitude, shelter["latitude"], shelter["longitude"])
            eligible.append((shelter, distance, available))

        if not eligible:
            return _shelter_not_found_result(scenario, self.name, "No shelters with available capacity", start_time)

        eligible.sort(key=lambda x: x[1])
        selected_shelter, distance, available = eligible[0]
        return _compute_shelter_allocation(scenario, selected_shelter, distance, self.name, start_time)


class LargestCapacityShelterBaseline:
    name = "largest_capacity_shelter"

    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            available = (shelter.get("total_capacity", 0)
                        - shelter.get("occupied_capacity", 0)
                        - shelter.get("reserved_capacity", 0))
            if available <= 0:
                continue
            distance = haversine_distance(scenario.latitude, scenario.longitude, shelter["latitude"], shelter["longitude"])
            eligible.append((shelter, available, distance))

        if not eligible:
            return _shelter_not_found_result(scenario, self.name, "No shelters with available capacity", start_time)

        eligible.sort(key=lambda x: (-x[1], x[2]))
        selected_shelter, available, distance = eligible[0]
        return _compute_shelter_allocation(scenario, selected_shelter, distance, self.name, start_time)


class FirstAvailableShelterBaseline:
    name = "first_available_shelter"

    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            available = (shelter.get("total_capacity", 0)
                        - shelter.get("occupied_capacity", 0)
                        - shelter.get("reserved_capacity", 0))
            if available > 0:
                eligible.append(shelter)

        if not eligible:
            return _shelter_not_found_result(scenario, self.name, "No shelters with available capacity", start_time)

        eligible.sort(key=lambda x: x["id"])
        selected_shelter = eligible[0]
        distance = haversine_distance(scenario.latitude, scenario.longitude, selected_shelter["latitude"], selected_shelter["longitude"])
        return _compute_shelter_allocation(scenario, selected_shelter, distance, self.name, start_time)


class CapacityOnlyBaseline:
    name = "capacity_only"

    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        candidates = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            total_cap = shelter.get("total_capacity", 0)
            if total_cap > 0:
                candidates.append(shelter)

        if not candidates:
            return _shelter_not_found_result(scenario, self.name, "No shelters available", start_time)

        candidates.sort(key=lambda x: -x["total_capacity"])
        selected_shelter = candidates[0]
        distance = haversine_distance(scenario.latitude, scenario.longitude, selected_shelter["latitude"], selected_shelter["longitude"])
        return _compute_shelter_allocation(scenario, selected_shelter, distance, self.name, start_time)


def get_all_shelter_baselines() -> Dict[str, Any]:
    return {
        "nearest_available_shelter": NearestAvailableShelterBaseline(),
        "largest_capacity_shelter": LargestCapacityShelterBaseline(),
        "first_available_shelter": FirstAvailableShelterBaseline(),
        "capacity_only": CapacityOnlyBaseline(),
    }