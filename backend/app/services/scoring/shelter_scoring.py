"""
Pure shelter scoring functions for X-DMRA research evaluation.

Copies exact production shelter_allocation_service.py scoring behavior.
No database access, no writes, no allocation logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from app.services.scoring.common import haversine_distance


@dataclass(frozen=True)
class ShelterScoringInput:
    """Complete typed input for shelter scoring."""
    shelter_id: int
    operating_status: str
    shelter_latitude: float
    shelter_longitude: float
    incident_latitude: float
    incident_longitude: float
    total_displaced_people: int
    total_capacity: int
    occupied_capacity: int
    reserved_capacity: int
    maximum_daily_intake: int
    current_intake_workload: int
    has_medical_support: bool
    has_accessibility_support: bool
    has_women_child_safe_area: bool
    has_food: bool
    has_drinking_water: bool
    has_sanitation: bool
    has_power_backup: bool
    supports_long_term_stay: bool
    mandatory_medical_required: bool
    mandatory_accessibility_required: bool
    route_risk: str
    route_blocked: bool
    estimated_delay_minutes: int


@dataclass(frozen=True)
class ShelterScoringOutput:
    """Complete typed output from shelter scoring."""
    shelter_id: int
    eligible: bool
    eligibility_reason: Optional[str]
    distance_km: float
    available_capacity: int
    proposed_people_count: int
    projected_occupancy_pct: float
    overcrowding_risk_level: str
    capacity_score: float
    distance_score: float
    medical_support_score: float
    accessibility_support_score: float
    women_child_score: float
    vulnerability_score: float
    utility_score: float
    overcrowding_score: float
    route_score: float
    workload_score: float
    total_score: float


WEIGHT_CAPACITY = 30.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VULNERABILITY = 20.0
WEIGHT_UTILITIES = 15.0
WEIGHT_OVERCROWDING = 10.0
WEIGHT_ROUTE_SAFETY = 5.0
WEIGHT_WORKLOAD = 5.0


def calculate_overcrowding_risk(projected_occupancy_pct: float) -> str:
    """
    Exact production overcrowding risk classification.
    < 70%: low, 70-<85%: moderate, 85-<95%: high, >=95%: critical
    """
    if projected_occupancy_pct < 70.0:
        return "low"
    elif projected_occupancy_pct < 85.0:
        return "moderate"
    elif projected_occupancy_pct < 95.0:
        return "high"
    return "critical"


def score_shelter(inp: ShelterScoringInput) -> ShelterScoringOutput:
    """
    Compute shelter eligibility and multi-factor score.

    Exact production behavior from shelter_allocation_service.py:
    - Capacity: 0-30 pts
    - Distance: 15 / 10.5 / 4.5 pts (tiered)
    - Vulnerability: medical=10, accessibility=5, women_child=5
    - Utilities: food+water=7.5, sanitation=5, power=2.5
    - Overcrowding: 10/8/3/0 pts based on projected %
    - Route safety: 5/2.5/1 pts (tiered)
    - Workload: 5/2.5/1 pts (ratio-based)

    Eligibility:
    - operating_status must be "open" or "limited"
    - route must not be blocked
    - available_capacity must be > 0
    - mandatory medical required must be satisfied if set
    - mandatory accessibility required must be satisfied if set
    """
    shelter_id = inp.shelter_id

    if inp.operating_status not in ("open", "limited"):
        return ShelterScoringOutput(
            shelter_id=shelter_id,
            eligible=False,
            eligibility_reason="Shelter operating_status is not 'open' or 'limited'",
            distance_km=0.0,
            available_capacity=0,
            proposed_people_count=0,
            projected_occupancy_pct=0.0,
            overcrowding_risk_level="critical",
            capacity_score=0.0,
            distance_score=0.0,
            medical_support_score=0.0,
            accessibility_support_score=0.0,
            women_child_score=0.0,
            vulnerability_score=0.0,
            utility_score=0.0,
            overcrowding_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    available_capacity = inp.total_capacity - inp.occupied_capacity - inp.reserved_capacity
    if available_capacity <= 0:
        return ShelterScoringOutput(
            shelter_id=shelter_id,
            eligible=False,
            eligibility_reason="Shelter has no available capacity",
            distance_km=0.0,
            available_capacity=0,
            proposed_people_count=0,
            projected_occupancy_pct=100.0,
            overcrowding_risk_level="critical",
            capacity_score=0.0,
            distance_score=0.0,
            medical_support_score=0.0,
            accessibility_support_score=0.0,
            women_child_score=0.0,
            vulnerability_score=0.0,
            utility_score=0.0,
            overcrowding_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    if inp.route_blocked:
        return ShelterScoringOutput(
            shelter_id=shelter_id,
            eligible=False,
            eligibility_reason="Route to shelter is blocked",
            distance_km=0.0,
            available_capacity=available_capacity,
            proposed_people_count=0,
            projected_occupancy_pct=0.0,
            overcrowding_risk_level="low",
            capacity_score=0.0,
            distance_score=0.0,
            medical_support_score=0.0,
            accessibility_support_score=0.0,
            women_child_score=0.0,
            vulnerability_score=0.0,
            utility_score=0.0,
            overcrowding_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    if inp.mandatory_medical_required and not inp.has_medical_support:
        return ShelterScoringOutput(
            shelter_id=shelter_id,
            eligible=False,
            eligibility_reason="Shelter lacks mandatory medical support",
            distance_km=0.0,
            available_capacity=available_capacity,
            proposed_people_count=0,
            projected_occupancy_pct=0.0,
            overcrowding_risk_level="low",
            capacity_score=0.0,
            distance_score=0.0,
            medical_support_score=0.0,
            accessibility_support_score=0.0,
            women_child_score=0.0,
            vulnerability_score=0.0,
            utility_score=0.0,
            overcrowding_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    if inp.mandatory_accessibility_required and not inp.has_accessibility_support:
        return ShelterScoringOutput(
            shelter_id=shelter_id,
            eligible=False,
            eligibility_reason="Shelter lacks mandatory accessibility support",
            distance_km=0.0,
            available_capacity=available_capacity,
            proposed_people_count=0,
            projected_occupancy_pct=0.0,
            overcrowding_risk_level="low",
            capacity_score=0.0,
            distance_score=0.0,
            medical_support_score=0.0,
            accessibility_support_score=0.0,
            women_child_score=0.0,
            vulnerability_score=0.0,
            utility_score=0.0,
            overcrowding_score=0.0,
            route_score=0.0,
            workload_score=0.0,
            total_score=0.0,
        )

    proposed_people = min(inp.total_displaced_people, available_capacity)

    if inp.maximum_daily_intake > 0:
        proposed_people = min(proposed_people, inp.maximum_daily_intake)

    capacity_score = 0.0
    if inp.total_displaced_people > 0:
        capacity_score = (proposed_people / inp.total_displaced_people) * WEIGHT_CAPACITY

    dist_km = haversine_distance(
        inp.shelter_latitude, inp.shelter_longitude,
        inp.incident_latitude, inp.incident_longitude
    )
    if dist_km <= 10.0:
        distance_score = WEIGHT_DISTANCE
    elif dist_km <= 50.0:
        distance_score = WEIGHT_DISTANCE * 0.7
    else:
        distance_score = WEIGHT_DISTANCE * 0.3

    medical_support_score = 10.0 if inp.has_medical_support else 0.0
    accessibility_support_score = 5.0 if inp.has_accessibility_support else 0.0
    women_child_score = 5.0 if inp.has_women_child_safe_area else 0.0
    vulnerability_score = medical_support_score + accessibility_support_score + women_child_score

    util_score = 0.0
    if inp.has_food and inp.has_drinking_water:
        util_score += 7.5
    if inp.has_sanitation:
        util_score += 5.0
    if inp.has_power_backup:
        util_score += 2.5

    projected_total = inp.occupied_capacity + inp.reserved_capacity + proposed_people
    if inp.total_capacity > 0:
        projected_occupancy_pct = (projected_total / inp.total_capacity) * 100.0
    else:
        projected_occupancy_pct = 100.0

    overcrowding_level = calculate_overcrowding_risk(projected_occupancy_pct)

    if overcrowding_level == "critical":
        overcrowding_score = 0.0
    elif overcrowding_level == "high":
        overcrowding_score = WEIGHT_OVERCROWDING * 0.3
    elif overcrowding_level == "moderate":
        overcrowding_score = WEIGHT_OVERCROWDING * 0.8
    else:
        overcrowding_score = WEIGHT_OVERCROWDING

    if inp.route_risk == "low":
        route_score = WEIGHT_ROUTE_SAFETY
    elif inp.route_risk == "medium":
        route_score = WEIGHT_ROUTE_SAFETY * 0.5
    elif inp.route_risk == "high":
        route_score = WEIGHT_ROUTE_SAFETY * 0.2
    else:
        route_score = WEIGHT_ROUTE_SAFETY

    workload_score = WEIGHT_WORKLOAD
    if inp.maximum_daily_intake > 0:
        workload_ratio = inp.current_intake_workload / inp.maximum_daily_intake
        if workload_ratio > 0.8:
            workload_score = WEIGHT_WORKLOAD * 0.2
        elif workload_ratio > 0.5:
            workload_score = WEIGHT_WORKLOAD * 0.5

    total_score = (
        capacity_score
        + distance_score
        + vulnerability_score
        + util_score
        + overcrowding_score
        + route_score
        + workload_score
    )

    return ShelterScoringOutput(
        shelter_id=shelter_id,
        eligible=True,
        eligibility_reason=None,
        distance_km=round(dist_km, 2),
        available_capacity=available_capacity,
        proposed_people_count=proposed_people,
        projected_occupancy_pct=round(projected_occupancy_pct, 4),
        overcrowding_risk_level=overcrowding_level,
        capacity_score=round(capacity_score, 4),
        distance_score=round(distance_score, 4),
        medical_support_score=round(medical_support_score, 4),
        accessibility_support_score=round(accessibility_support_score, 4),
        women_child_score=round(women_child_score, 4),
        vulnerability_score=round(vulnerability_score, 4),
        utility_score=round(util_score, 4),
        overcrowding_score=round(overcrowding_score, 4),
        route_score=round(route_score, 4),
        workload_score=round(workload_score, 4),
        total_score=round(total_score, 4),
    )


def rank_shelters(
    inputs: List[ShelterScoringInput],
) -> List[ShelterScoringOutput]:
    """
    Score and rank all shelters for a shelter request.
    Returns sorted list (highest score first), eligible only.
    """
    scored = [score_shelter(inp) for inp in inputs]
    eligible = [s for s in scored if s.eligible]
    eligible.sort(key=lambda x: x.total_score, reverse=True)
    return eligible