"""
Pure rescue team scoring functions for X-DMRA research evaluation.

Copies exact production allocation_service.py scoring behavior.
No database access, no writes, no allocation logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.services.scoring.common import (
    haversine_distance,
    normalize_string_set,
    RouteRiskLevel,
)


@dataclass(frozen=True)
class RescueScoringInput:
    """Complete typed input for rescue team scoring."""
    team_id: int
    availability_status: str
    team_latitude: float
    team_longitude: float
    team_capacity: int
    team_current_workload: int
    team_skills: List[str]
    team_equipment: List[str]
    incident_latitude: float
    incident_longitude: float
    affected_people: int
    required_skills: List[str]
    required_equipment: List[str]
    route_risk: str
    route_blocked: bool
    estimated_delay_minutes: int


@dataclass(frozen=True)
class RescueScoringOutput:
    """Complete typed output from rescue team scoring."""
    team_id: int
    eligible: bool
    eligibility_reason: Optional[str]
    distance_km: float
    skill_match_pct: float
    equipment_match_pct: float
    skill_score: float
    equipment_score: float
    capacity_score: float
    workload_score: float
    distance_score: float
    route_risk_penalty: float
    total_score: float


def score_rescue_team(inp: RescueScoringInput) -> RescueScoringOutput:
    """
    Compute rescue team eligibility and multi-factor score.

    Exact production behavior from allocation_service.py:
    - Skill match: 0-30 pts
    - Equipment match: 0-20 pts
    - Capacity: 0-10 pts
    - Workload: 0-10 pts
    - Distance: 0-30 pts
    - Route risk penalty: 0-15 + delay*0.5 pts (subtracted)

    Eligibility:
    - Team availability_status must be "available"
    - Route must not be blocked
    """
    team_id = inp.team_id

    if inp.availability_status != "available":
        return RescueScoringOutput(
            team_id=team_id,
            eligible=False,
            eligibility_reason="Team availability_status is not 'available'",
            distance_km=0.0,
            skill_match_pct=0.0,
            equipment_match_pct=0.0,
            skill_score=0.0,
            equipment_score=0.0,
            capacity_score=0.0,
            workload_score=0.0,
            distance_score=0.0,
            route_risk_penalty=0.0,
            total_score=0.0,
        )

    if inp.route_blocked:
        return RescueScoringOutput(
            team_id=team_id,
            eligible=False,
            eligibility_reason="Route to incident is blocked",
            distance_km=0.0,
            skill_match_pct=0.0,
            equipment_match_pct=0.0,
            skill_score=0.0,
            equipment_score=0.0,
            capacity_score=0.0,
            workload_score=0.0,
            distance_score=0.0,
            route_risk_penalty=0.0,
            total_score=0.0,
        )

    req_skills = normalize_string_set(inp.required_skills)
    team_skills = normalize_string_set(inp.team_skills)
    req_equip = normalize_string_set(inp.required_equipment)
    team_equip = normalize_string_set(inp.team_equipment)

    if req_skills:
        matched_skills = req_skills.intersection(team_skills)
        skill_match_pct = (len(matched_skills) / len(req_skills)) * 100.0
    else:
        skill_match_pct = 100.0
    skill_score = (skill_match_pct / 100.0) * 30.0

    if req_equip:
        matched_equip = req_equip.intersection(team_equip)
        equip_match_pct = (len(matched_equip) / len(req_equip)) * 100.0
    else:
        equip_match_pct = 100.0
    equipment_score = (equip_match_pct / 100.0) * 20.0

    if inp.affected_people > 0:
        if inp.team_capacity >= inp.affected_people:
            capacity_score = 10.0
        else:
            capacity_score = (inp.team_capacity / inp.affected_people) * 10.0
    else:
        capacity_score = 10.0

    workload_score = max(0.0, 10.0 - inp.team_current_workload)

    dist_km = haversine_distance(
        inp.team_latitude, inp.team_longitude,
        inp.incident_latitude, inp.incident_longitude
    )
    distance_score = max(0.0, 30.0 - (dist_km / 50.0) * 30.0)

    route_risk_penalty = 0.0
    if inp.route_risk == "medium":
        route_risk_penalty = 5.0
    elif inp.route_risk == "high":
        route_risk_penalty = 15.0
    route_risk_penalty += inp.estimated_delay_minutes * 0.5

    total_score = (
        skill_score
        + equipment_score
        + capacity_score
        + workload_score
        + distance_score
        - route_risk_penalty
    )

    return RescueScoringOutput(
        team_id=team_id,
        eligible=True,
        eligibility_reason=None,
        distance_km=round(dist_km, 2),
        skill_match_pct=round(skill_match_pct, 2),
        equipment_match_pct=round(equip_match_pct, 2),
        skill_score=round(skill_score, 4),
        equipment_score=round(equipment_score, 4),
        capacity_score=round(capacity_score, 4),
        workload_score=round(workload_score, 4),
        distance_score=round(distance_score, 4),
        route_risk_penalty=round(route_risk_penalty, 4),
        total_score=round(total_score, 4),
    )


def rank_rescue_teams(
    inputs: List[RescueScoringInput],
) -> List[RescueScoringOutput]:
    """
    Score and rank all rescue teams for an incident.
    Returns sorted list (highest score first).
    """
    scored = [score_rescue_team(inp) for inp in inputs]
    eligible = [s for s in scored if s.eligible]
    eligible.sort(key=lambda x: x.total_score, reverse=True)
    return eligible