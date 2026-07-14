import math
from typing import List, Tuple
from app.models import Incident, RescueTeam, TeamAvailability, RouteRisk, RouteCondition
from app.schemas import TeamRecommendation

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Radius of Earth in km
    R = 6371.0
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def normalize_string(s: str) -> str:
    return s.lower().replace("-", "_").replace(" ", "_")

def calculate_team_recommendations(incident: Incident, all_teams: List[RescueTeam], route_conditions: List[RouteCondition]) -> List[TeamRecommendation]:
    recommendations = []
    
    req_skills = set(normalize_string(s) for s in incident.required_skills)
    req_equip = set(normalize_string(e) for e in incident.required_equipment)
    
    for team in all_teams:
        if team.availability_status != TeamAvailability.available:
            continue
            
        route_risk = RouteRisk.low
        route_blocked = False
        delay_minutes = 0
        
        for rc in route_conditions:
            if rc.incident_id == incident.id and rc.rescue_team_id == team.id:
                route_risk = rc.risk_level
                route_blocked = bool(rc.is_blocked)
                delay_minutes = rc.estimated_delay_minutes
                break
        
        if route_blocked:
            continue
            
        team_skills = set(normalize_string(s) for s in team.skills)
        team_equip = set(normalize_string(e) for e in team.equipment)
        
        # Skill Match (0 - 30 points)
        skill_match_pct = 100.0
        if req_skills:
            matched_skills = req_skills.intersection(team_skills)
            skill_match_pct = (len(matched_skills) / len(req_skills)) * 100.0
        skill_score = (skill_match_pct / 100.0) * 30.0
        
        # Equipment Match (0 - 20 points)
        equip_match_pct = 100.0
        if req_equip:
            matched_equip = req_equip.intersection(team_equip)
            equip_match_pct = (len(matched_equip) / len(req_equip)) * 100.0
        equip_score = (equip_match_pct / 100.0) * 20.0
        
        # Capacity Match (0 - 10 points)
        capacity_score = 10.0
        if incident.affected_people > 0:
            if team.capacity < incident.affected_people:
                capacity_score = (team.capacity / incident.affected_people) * 10.0
                
        # Workload (0 - 10 points)
        # Less workload = higher score
        workload_score = max(0.0, 10.0 - team.current_workload)
        
        # Distance Score (0 - 30 points)
        # Max points for 0 km, 0 points for >= 50 km
        dist_km = haversine_distance(incident.latitude, incident.longitude, team.latitude, team.longitude)
        distance_score = max(0.0, 30.0 - (dist_km / 50.0) * 30.0)
        
        # Route Risk Penalty
        route_risk_score = 0.0 # penalty
        if route_risk == RouteRisk.medium:
            route_risk_score = 5.0
        elif route_risk == RouteRisk.high:
            route_risk_score = 15.0
        
        # Additional penalty for delay (e.g. 0.5 points per minute of delay)
        route_risk_score += (delay_minutes * 0.5)
        
        total_score = skill_score + equip_score + capacity_score + workload_score + distance_score - route_risk_score
        
        positive_reasons = []
        limitations = []
        
        if skill_match_pct == 100:
            positive_reasons.append("All required skills are available.")
        elif skill_match_pct > 0:
            limitations.append("Missing some required skills.")
        else:
            if req_skills: limitations.append("Lacks all required skills.")
            
        if equip_match_pct == 100:
            positive_reasons.append("All required equipment is available.")
        elif equip_match_pct > 0:
            limitations.append("Missing some required equipment.")
            
        if dist_km < 10:
            positive_reasons.append(f"Team is very close ({dist_km:.1f} km).")
            
        if team.capacity >= incident.affected_people and incident.affected_people > 0:
            positive_reasons.append("Team capacity is sufficient for affected population.")
            
        if team.current_workload == 0:
            positive_reasons.append("Team has no current workload.")
        elif team.current_workload > 5:
            limitations.append("Team currently has a high workload.")
            
        if route_risk == RouteRisk.low:
            positive_reasons.append("Route risk is low and accessible.")
        elif route_risk == RouteRisk.medium:
            limitations.append("Route has medium risk/traffic.")
        elif route_risk == RouteRisk.high:
            limitations.append("Route has high risk.")
            
        if delay_minutes > 0:
            limitations.append(f"Estimated delay of {delay_minutes} minutes.")
            
        explanation = f"{team.name} is recommended because they match {skill_match_pct:.0f}% of skills and are {dist_km:.1f} km away."
        if limitations:
            explanation += " However, consider the limitations: " + ", ".join(limitations) + "."
            
        rec = TeamRecommendation(
            team_id=team.id,
            team_name=team.name,
            rank=0, # will set after sorting
            total_score=round(total_score, 1),
            distance_km=round(dist_km, 1),
            skill_match_percentage=round(skill_match_pct, 1),
            equipment_match_percentage=round(equip_match_pct, 1),
            capacity_score=round(capacity_score, 1),
            distance_score=round(distance_score, 1),
            workload_score=round(workload_score, 1),
            route_risk_score=round(route_risk_score, 1),
            positive_reasons=positive_reasons,
            limitations=limitations,
            explanation=explanation
        )
        recommendations.append(rec)
        
    recommendations.sort(key=lambda x: x.total_score, reverse=True)
    
    # Set ranks and explain why lower ranked teams are lower
    for i, rec in enumerate(recommendations):
        rec.rank = i + 1
        if i > 0:
            higher_team = recommendations[i-1]
            if rec.distance_km < higher_team.distance_km:
                rec.limitations.append(f"Although closer than {higher_team.team_name}, lower skill/equipment match or capacity reduced overall rank.")

    return recommendations
