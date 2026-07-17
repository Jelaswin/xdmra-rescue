import math
from typing import List, Tuple
from app.models import Incident, RescueTeam, TeamAvailability, RouteRisk, RouteCondition
from app.schemas import TeamRecommendation
from app.services.scoring.rescue_scoring import (
    RescueScoringInput, RescueScoringOutput, rank_rescue_teams,
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def calculate_team_recommendations(incident: Incident, all_teams: List[RescueTeam], route_conditions: List[RouteCondition]) -> List[TeamRecommendation]:
    scoring_inputs = []
    team_map = {}

    for team in all_teams:
        route_risk_val = RouteRisk.low
        route_blocked = False
        delay_minutes = 0

        for rc in route_conditions:
            if rc.incident_id == incident.id and rc.rescue_team_id == team.id:
                route_risk_val = rc.risk_level
                route_blocked = bool(rc.is_blocked)
                delay_minutes = rc.estimated_delay_minutes
                break

        inp = RescueScoringInput(
            team_id=team.id,
            availability_status=team.availability_status.value,
            team_latitude=team.latitude,
            team_longitude=team.longitude,
            team_capacity=team.capacity,
            team_current_workload=team.current_workload,
            team_skills=team.skills if isinstance(team.skills, list) else [],
            team_equipment=team.equipment if isinstance(team.equipment, list) else [],
            incident_latitude=incident.latitude,
            incident_longitude=incident.longitude,
            affected_people=incident.affected_people,
            required_skills=incident.required_skills if isinstance(incident.required_skills, list) else [],
            required_equipment=incident.required_equipment if isinstance(incident.required_equipment, list) else [],
            route_risk=route_risk_val.value,
            route_blocked=route_blocked,
            estimated_delay_minutes=delay_minutes,
        )
        scoring_inputs.append(inp)
        team_map[team.id] = team

    ranked_outputs = rank_rescue_teams(scoring_inputs)

    recommendations = []
    for out in ranked_outputs:
        team = team_map[out.team_id]
        route_risk_val = RouteRisk.low
        route_blocked = False
        delay_minutes = 0
        for rc in route_conditions:
            if rc.incident_id == incident.id and rc.rescue_team_id == team.id:
                route_risk_val = rc.risk_level
                route_blocked = bool(rc.is_blocked)
                delay_minutes = rc.estimated_delay_minutes
                break

        positive_reasons = []
        limitations = []

        if out.skill_match_pct == 100:
            positive_reasons.append("All required skills are available.")
        elif out.skill_match_pct > 0:
            limitations.append("Missing some required skills.")
        else:
            if scoring_inputs[0].required_skills:
                limitations.append("Lacks all required skills.")

        if out.equipment_match_pct == 100:
            positive_reasons.append("All required equipment is available.")
        elif out.equipment_match_pct > 0:
            limitations.append("Missing some required equipment.")

        if out.distance_km < 10:
            positive_reasons.append(f"Team is very close ({out.distance_km:.1f} km).")

        if team.capacity >= incident.affected_people and incident.affected_people > 0:
            positive_reasons.append("Team capacity is sufficient for affected population.")

        if team.current_workload == 0:
            positive_reasons.append("Team has no current workload.")
        elif team.current_workload > 5:
            limitations.append("Team currently has a high workload.")

        if route_risk_val == RouteRisk.low:
            positive_reasons.append("Route risk is low and accessible.")
        elif route_risk_val == RouteRisk.medium:
            limitations.append("Route has medium risk/traffic.")
        elif route_risk_val == RouteRisk.high:
            limitations.append("Route has high risk.")

        if delay_minutes > 0:
            limitations.append(f"Estimated delay of {delay_minutes} minutes.")

        explanation = f"{team.name} is recommended because they match {out.skill_match_pct:.0f}% of skills and are {out.distance_km:.1f} km away."
        if limitations:
            explanation += " However, consider the limitations: " + ", ".join(limitations) + "."

        rec = TeamRecommendation(
            team_id=team.id,
            team_name=team.name,
            rank=0,
            total_score=round(out.total_score, 1),
            distance_km=round(out.distance_km, 1),
            skill_match_percentage=round(out.skill_match_pct, 1),
            equipment_match_percentage=round(out.equipment_match_pct, 1),
            capacity_score=round(out.capacity_score, 1),
            distance_score=round(out.distance_score, 1),
            workload_score=round(out.workload_score, 1),
            route_risk_score=round(out.route_risk_penalty, 1),
            positive_reasons=positive_reasons,
            limitations=limitations,
            explanation=explanation
        )
        recommendations.append(rec)

    for i, rec in enumerate(recommendations):
        rec.rank = i + 1
        if i > 0:
            higher_team = recommendations[i - 1]
            if rec.distance_km < higher_team.distance_km:
                rec.limitations.append(
                    f"Although closer than {higher_team.team_name}, lower skill/equipment match or capacity reduced overall rank."
                )

    return recommendations