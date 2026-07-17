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
    shelters: List[Dict[str, Any]]  # Each with capacity and features


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
    failure_reason: Optional[str] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line Haversine distance in km."""
    R = 6371.0
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


class NearestAvailableShelterBaseline:
    """Select nearest shelter with available capacity."""
    
    name = "nearest_available_shelter"
    
    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            
            available_capacity = shelter.get("total_capacity", 0) - shelter.get("occupied_capacity", 0) - shelter.get("reserved_capacity", 0)
            if available_capacity <= 0:
                continue
            
            distance = haversine_distance(scenario.latitude, scenario.longitude, shelter["latitude"], shelter["longitude"])
            eligible.append((shelter, distance, available_capacity))
        
        if not eligible:
            return ShelterBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=scenario.displaced_people,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No shelters with available capacity"
            )
        
        eligible.sort(key=lambda x: x[1])
        selected_shelter, distance, available = eligible[0]
        
        coverage = min(100, (available / scenario.displaced_people * 100)) if scenario.displaced_people > 0 else 0
        uncovered = max(0, scenario.displaced_people - available)
        
        return ShelterBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            shelters_used=[selected_shelter["id"]],
            population_coverage_pct=coverage,
            uncovered_people=uncovered,
            overcrowding_violations=0,
            requirement_match_pct=self._check_requirements(scenario, selected_shelter),
            distance_km=distance,
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _check_requirements(self, scenario: ShelterScenario, shelter: Dict) -> float:
        score = 100.0
        if scenario.medical_required and not shelter.get("has_medical_support"):
            score -= 50
        if scenario.accessibility_required and not shelter.get("has_accessibility_support"):
            score -= 50
        return max(0, score)


class LargestCapacityShelterBaseline:
    """Select shelter with largest available capacity."""
    
    name = "largest_capacity_shelter"
    
    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            
            available_capacity = shelter.get("total_capacity", 0) - shelter.get("occupied_capacity", 0) - shelter.get("reserved_capacity", 0)
            if available_capacity <= 0:
                continue
            
            distance = haversine_distance(scenario.latitude, scenario.longitude, shelter["latitude"], shelter["longitude"])
            eligible.append((shelter, available_capacity, distance))
        
        if not eligible:
            return ShelterBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=scenario.displaced_people,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No shelters with available capacity"
            )
        
        eligible.sort(key=lambda x: (-x[1], x[2]))
        selected_shelter, available, distance = eligible[0]
        
        coverage = min(100, (available / scenario.displaced_people * 100)) if scenario.displaced_people > 0 else 0
        uncovered = max(0, scenario.displaced_people - available)
        
        return ShelterBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            shelters_used=[selected_shelter["id"]],
            population_coverage_pct=coverage,
            uncovered_people=uncovered,
            overcrowding_violations=0,
            requirement_match_pct=self._check_requirements(scenario, selected_shelter),
            distance_km=distance,
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _check_requirements(self, scenario: ShelterScenario, shelter: Dict) -> float:
        score = 100.0
        if scenario.medical_required and not shelter.get("has_medical_support"):
            score -= 50
        if scenario.accessibility_required and not shelter.get("has_accessibility_support"):
            score -= 50
        return max(0, score)


class FirstAvailableShelterBaseline:
    """Select first available shelter by sorted ID."""
    
    name = "first_available_shelter"
    
    def select(self, scenario: ShelterScenario) -> ShelterBaselineResult:
        import time
        start_time = time.perf_counter()
        
        eligible = []
        for shelter in scenario.shelters:
            if shelter.get("operating_status") != "open":
                continue
            
            available_capacity = shelter.get("total_capacity", 0) - shelter.get("occupied_capacity", 0) - shelter.get("reserved_capacity", 0)
            if available_capacity > 0:
                eligible.append(shelter)
        
        if not eligible:
            return ShelterBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=scenario.displaced_people,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No shelters with available capacity"
            )
        
        eligible.sort(key=lambda x: x["id"])
        selected_shelter = eligible[0]
        distance = haversine_distance(scenario.latitude, scenario.longitude, selected_shelter["latitude"], selected_shelter["longitude"])
        available = selected_shelter.get("total_capacity", 0) - selected_shelter.get("occupied_capacity", 0) - selected_shelter.get("reserved_capacity", 0)
        
        coverage = min(100, (available / scenario.displaced_people * 100)) if scenario.displaced_people > 0 else 0
        uncovered = max(0, scenario.displaced_people - available)
        
        return ShelterBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            shelters_used=[selected_shelter["id"]],
            population_coverage_pct=coverage,
            uncovered_people=uncovered,
            overcrowding_violations=0,
            requirement_match_pct=self._check_requirements(scenario, selected_shelter),
            distance_km=distance,
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _check_requirements(self, scenario: ShelterScenario, shelter: Dict) -> float:
        score = 100.0
        if scenario.medical_required and not shelter.get("has_medical_support"):
            score -= 50
        if scenario.accessibility_required and not shelter.get("has_accessibility_support"):
            score -= 50
        return max(0, score)


class CapacityOnlyBaseline:
    """Select based solely on raw capacity, ignoring distance."""
    
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
            return ShelterBaselineResult(
                algorithm=self.name,
                scenario_id=scenario.scenario_id,
                success=False,
                shelters_used=[],
                population_coverage_pct=0.0,
                uncovered_people=scenario.displaced_people,
                overcrowding_violations=0,
                requirement_match_pct=0.0,
                distance_km=0.0,
                computation_time_ms=(time.perf_counter() - start_time) * 1000,
                failure_reason="No shelters available"
            )
        
        candidates.sort(key=lambda x: -x["total_capacity"])
        selected_shelter = candidates[0]
        distance = haversine_distance(scenario.latitude, scenario.longitude, selected_shelter["latitude"], selected_shelter["longitude"])
        available = selected_shelter.get("total_capacity", 0) - selected_shelter.get("occupied_capacity", 0) - selected_shelter.get("reserved_capacity", 0)
        
        coverage = min(100, (available / scenario.displaced_people * 100)) if scenario.displaced_people > 0 else 0
        uncovered = max(0, scenario.displaced_people - available)
        
        return ShelterBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            shelters_used=[selected_shelter["id"]],
            population_coverage_pct=coverage,
            uncovered_people=uncovered,
            overcrowding_violations=0,
            requirement_match_pct=self._check_requirements(scenario, selected_shelter),
            distance_km=distance,
            computation_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _check_requirements(self, scenario: ShelterScenario, shelter: Dict) -> float:
        score = 100.0
        if scenario.medical_required and not shelter.get("has_medical_support"):
            score -= 50
        if scenario.accessibility_required and not shelter.get("has_accessibility_support"):
            score -= 50
        return max(0, score)


def get_all_shelter_baselines() -> Dict[str, Any]:
    """Return all available shelter baseline algorithms."""
    return {
        "nearest_available_shelter": NearestAvailableShelterBaseline(),
        "largest_capacity_shelter": LargestCapacityShelterBaseline(),
        "first_available_shelter": FirstAvailableShelterBaseline(),
        "capacity_only": CapacityOnlyBaseline()
    }