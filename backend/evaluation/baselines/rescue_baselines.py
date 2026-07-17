"""
Rescue Team Baseline Evaluation Strategies.

These are evaluation-only baseline algorithms that do NOT modify
the production X-DMRA allocation system.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2


@dataclass
class RescueScenario:
    """A test scenario for rescue evaluation."""
    scenario_id: str
    incident_id: int
    incident_title: str
    incident_type: str
    latitude: float
    longitude: float
    priority_level: str
    required_skills: List[str]
    required_equipment: List[str]
    affected_people: int
    trapped_people: int
    available_teams: List[Dict[str, Any]]


@dataclass
class RescueBaselineResult:
    """Result from a rescue baseline strategy."""
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


class RandomAvailableBaseline:
    """Select a random eligible available team."""
    
    name = "random_available"
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
    
    def select(self, scenario: RescueScenario) -> RescueBaselineResult:
        start_time = __import__("time").perf_counter()
        
        available = [t for t in scenario.available_teams if t.get("availability_status") == "available"]
        
        if not available:
            return RescueBaselineResult(
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
                computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000,
                failure_reason="No available teams"
            )
        
        team = self.rng.choice(available)
        distance = haversine_distance(scenario.latitude, scenario.longitude, team["latitude"], team["longitude"])
        
        skill_match = self._calculate_skill_match(scenario, team)
        equip_match = self._calculate_equipment_match(scenario, team)
        
        return RescueBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=team["id"],
            selected_team_name=team["name"],
            distance_km=distance,
            skill_match_pct=skill_match,
            equipment_match_pct=equip_match,
            route_blocked=False,
            score=0.0,
            computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000
        )
    
    def _calculate_skill_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_skills:
            return 100.0
        team_skills = set(team.get("skills", []))
        required = set(scenario.required_skills)
        if not required:
            return 100.0
        return (len(team_skills & required) / len(required)) * 100
    
    def _calculate_equipment_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_equipment:
            return 100.0
        team_equip = set(team.get("equipment", []))
        required = set(scenario.required_equipment)
        if not required:
            return 100.0
        return (len(team_equip & required) / len(required)) * 100


class FirstAvailableBaseline:
    """Select the first eligible team by sorted ID."""
    
    name = "first_available"
    
    def select(self, scenario: RescueScenario) -> RescueBaselineResult:
        start_time = __import__("time").perf_counter()
        
        available = [t for t in scenario.available_teams if t.get("availability_status") == "available"]
        
        if not available:
            return RescueBaselineResult(
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
                computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000,
                failure_reason="No available teams"
            )
        
        available.sort(key=lambda t: t["id"])
        team = available[0]
        distance = haversine_distance(scenario.latitude, scenario.longitude, team["latitude"], team["longitude"])
        
        skill_match = self._calculate_skill_match(scenario, team)
        equip_match = self._calculate_equipment_match(scenario, team)
        
        return RescueBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=team["id"],
            selected_team_name=team["name"],
            distance_km=distance,
            skill_match_pct=skill_match,
            equipment_match_pct=equip_match,
            route_blocked=False,
            score=0.0,
            computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000
        )
    
    def _calculate_skill_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_skills:
            return 100.0
        team_skills = set(team.get("skills", []))
        required = set(scenario.required_skills)
        if not required:
            return 100.0
        return (len(team_skills & required) / len(required)) * 100
    
    def _calculate_equipment_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_equipment:
            return 100.0
        team_equip = set(team.get("equipment", []))
        required = set(scenario.required_equipment)
        if not required:
            return 100.0
        return (len(team_equip & required) / len(required)) * 100


class NearestAvailableBaseline:
    """Select the eligible team with minimum straight-line Haversine distance."""
    
    name = "nearest_available"
    
    def select(self, scenario: RescueScenario) -> RescueBaselineResult:
        start_time = __import__("time").perf_counter()
        
        available = [t for t in scenario.available_teams if t.get("availability_status") == "available"]
        
        if not available:
            return RescueBaselineResult(
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
                computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000,
                failure_reason="No available teams"
            )
        
        for team in available:
            team["_distance"] = haversine_distance(scenario.latitude, scenario.longitude, team["latitude"], team["longitude"])
        
        available.sort(key=lambda t: t["_distance"])
        team = available[0]
        
        skill_match = self._calculate_skill_match(scenario, team)
        equip_match = self._calculate_equipment_match(scenario, team)
        
        return RescueBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=team["id"],
            selected_team_name=team["name"],
            distance_km=team["_distance"],
            skill_match_pct=skill_match,
            equipment_match_pct=equip_match,
            route_blocked=False,
            score=0.0,
            computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000
        )
    
    def _calculate_skill_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_skills:
            return 100.0
        team_skills = set(team.get("skills", []))
        required = set(scenario.required_skills)
        if not required:
            return 100.0
        return (len(team_skills & required) / len(required)) * 100
    
    def _calculate_equipment_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_equipment:
            return 100.0
        team_equip = set(team.get("equipment", []))
        required = set(scenario.required_equipment)
        if not required:
            return 100.0
        return (len(team_equip & required) / len(required)) * 100


class SkillMatchOnlyBaseline:
    """Rank using skill and equipment compatibility only."""
    
    name = "skill_match_only"
    
    def select(self, scenario: RescueScenario) -> RescueBaselineResult:
        start_time = __import__("time").perf_counter()
        
        available = [t for t in scenario.available_teams if t.get("availability_status") == "available"]
        
        if not available:
            return RescueBaselineResult(
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
                computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000,
                failure_reason="No available teams"
            )
        
        for team in available:
            team["_skill_match"] = self._calculate_skill_match(scenario, team)
            team["_equip_match"] = self._calculate_equipment_match(scenario, team)
            team["_total_score"] = team["_skill_match"] + team["_equip_match"]
        
        available.sort(key=lambda t: (-t["_total_score"], t["id"]))
        team = available[0]
        
        return RescueBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=team["id"],
            selected_team_name=team["name"],
            distance_km=haversine_distance(scenario.latitude, scenario.longitude, team["latitude"], team["longitude"]),
            skill_match_pct=team["_skill_match"],
            equipment_match_pct=team["_equip_match"],
            route_blocked=False,
            score=team["_total_score"],
            computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000
        )
    
    def _calculate_skill_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_skills:
            return 50.0
        team_skills = set(team.get("skills", []))
        required = set(scenario.required_skills)
        if not required:
            return 50.0
        return (len(team_skills & required) / len(required)) * 50
    
    def _calculate_equipment_match(self, scenario: RescueScenario, team: Dict) -> float:
        if not scenario.required_equipment:
            return 50.0
        team_equip = set(team.get("equipment", []))
        required = set(scenario.required_equipment)
        if not required:
            return 50.0
        return (len(team_equip & required) / len(required)) * 50


class PriorityDistanceOnlyBaseline:
    """Rank using incident priority and distance without workload or route risk."""
    
    name = "priority_distance_only"
    
    PRIORITY_WEIGHTS = {"critical": 100, "high": 75, "medium": 50, "low": 25}
    
    def select(self, scenario: RescueScenario) -> RescueBaselineResult:
        start_time = __import__("time").perf_counter()
        
        available = [t for t in scenario.available_teams if t.get("availability_status") == "available"]
        
        if not available:
            return RescueBaselineResult(
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
                computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000,
                failure_reason="No available teams"
            )
        
        priority_weight = self.PRIORITY_WEIGHTS.get(scenario.priority_level, 50)
        
        for team in available:
            distance = haversine_distance(scenario.latitude, scenario.longitude, team["latitude"], team["longitude"])
            distance_score = max(0, 50 - distance)
            team["_score"] = priority_weight + distance_score
            team["_distance"] = distance
        
        available.sort(key=lambda t: (-t["_score"], t["id"]))
        team = available[0]
        
        return RescueBaselineResult(
            algorithm=self.name,
            scenario_id=scenario.scenario_id,
            success=True,
            selected_team_id=team["id"],
            selected_team_name=team["name"],
            distance_km=team["_distance"],
            skill_match_pct=0.0,
            equipment_match_pct=0.0,
            route_blocked=False,
            score=team["_score"],
            computation_time_ms=(__import__("time").perf_counter() - start_time) * 1000
        )


def get_all_rescue_baselines() -> Dict[str, Any]:
    """Return all available rescue baseline algorithms."""
    return {
        "random_available": RandomAvailableBaseline(seed=42),
        "first_available": FirstAvailableBaseline(),
        "nearest_available": NearestAvailableBaseline(),
        "skill_match_only": SkillMatchOnlyBaseline(),
        "priority_distance_only": PriorityDistanceOnlyBaseline()
    }