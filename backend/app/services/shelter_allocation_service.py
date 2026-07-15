import math
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models import (
    Incident, EmergencyShelter, ShelterRequest, ShelterRouteCondition,
    ShelterOperatingStatus, ShelterRequestStatus, RouteRisk
)
from app.schemas import (
    ShelterRecommendationResponse, SplitShelterAllocationPlan,
    ShelterAllocationEvaluationResponse
)

# Configurable Weights
WEIGHT_CAPACITY = 30.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VULNERABILITY = 20.0
WEIGHT_UTILITIES = 15.0
WEIGHT_OVERCROWDING = 10.0
WEIGHT_ROUTE_SAFETY = 5.0
WEIGHT_WORKLOAD = 5.0

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def calculate_overcrowding_risk(occupancy_percentage: float) -> str:
    if occupancy_percentage < 70.0:
        return "low"
    elif occupancy_percentage < 85.0:
        return "moderate"
    elif occupancy_percentage < 95.0:
        return "high"
    return "critical"

def evaluate_shelter_allocation(db: Session, request_id: int) -> ShelterAllocationEvaluationResponse:
    request_obj = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not request_obj:
        raise ValueError(f"ShelterRequest {request_id} not found.")

    incident = db.query(Incident).filter(Incident.id == request_obj.incident_id).first()
    shelters = db.query(EmergencyShelter).all()
    
    total_requested = request_obj.total_displaced_people
    
    recommendations = []
    
    for shelter in shelters:
        # 1. Eligibility Check
        if shelter.operating_status not in [ShelterOperatingStatus.open, ShelterOperatingStatus.limited]:
            continue
            
        available_capacity = shelter.total_capacity - shelter.occupied_capacity - shelter.reserved_capacity
        if available_capacity <= 0:
            continue
            
        route = db.query(ShelterRouteCondition).filter(
            ShelterRouteCondition.incident_id == incident.id,
            ShelterRouteCondition.shelter_id == shelter.id
        ).first()
        
        if route and route.is_blocked:
            continue
            
        # Mandatory Requirements Check
        if request_obj.accessibility_required > 0 and not shelter.has_accessibility_support:
            continue
        if request_obj.medical_observation_required > 0 and not shelter.has_medical_support:
            continue
            
        # 2. Scoring
        positive_reasons = []
        limitations = []
        
        # Capacity (30 points)
        proposed_allocation = min(total_requested, available_capacity)
        capacity_score = (proposed_allocation / total_requested) * WEIGHT_CAPACITY if total_requested > 0 else 0
        if capacity_score == WEIGHT_CAPACITY:
            positive_reasons.append("Can accommodate the entire requested population.")
        else:
            limitations.append(f"Can only accommodate {proposed_allocation} out of {total_requested} people.")
            
        # Distance (15 points)
        distance = haversine_distance(incident.latitude, incident.longitude, shelter.latitude, shelter.longitude)
        if distance <= 10.0:
            dist_score = WEIGHT_DISTANCE
            positive_reasons.append("Located within optimal distance (<10km).")
        elif distance <= 50.0:
            dist_score = WEIGHT_DISTANCE * 0.7
        else:
            dist_score = WEIGHT_DISTANCE * 0.3
            limitations.append("Located far from the incident (>50km).")
            
        # Medical & Vulnerability (20 points)
        vuln_score = 0.0
        if shelter.has_medical_support:
            vuln_score += 10.0
            positive_reasons.append("Has medical support.")
        if shelter.has_accessibility_support:
            vuln_score += 5.0
            positive_reasons.append("Has accessibility support.")
        if shelter.has_women_child_safe_area:
            vuln_score += 5.0
            positive_reasons.append("Has women and child safe area.")
            
        # Utilities (15 points)
        util_score = 0.0
        if shelter.has_food and shelter.has_drinking_water:
            util_score += 7.5
            positive_reasons.append("Provides food and drinking water.")
        if shelter.has_sanitation:
            util_score += 5.0
        if shelter.has_power_backup:
            util_score += 2.5
            
        # Route Risk (5 points)
        route_score = WEIGHT_ROUTE_SAFETY
        route_risk_str = "low"
        if route:
            route_risk_str = route.risk_level.value
            if route.risk_level == RouteRisk.medium:
                route_score *= 0.5
                limitations.append("Medium risk route.")
            elif route.risk_level == RouteRisk.high:
                route_score *= 0.2
                limitations.append("High risk route.")
                
        # Workload (5 points)
        workload_score = WEIGHT_WORKLOAD
        if shelter.maximum_daily_intake > 0:
            workload_ratio = shelter.current_intake_workload / shelter.maximum_daily_intake
            if workload_ratio > 0.8:
                workload_score *= 0.2
                limitations.append("High current intake workload.")
            elif workload_ratio > 0.5:
                workload_score *= 0.5
                
        # Overcrowding Risk (10 points)
        projected_total = shelter.occupied_capacity + shelter.reserved_capacity + proposed_allocation
        projected_occupancy_percentage = (projected_total / shelter.total_capacity * 100) if shelter.total_capacity > 0 else 100
        overcrowding_level = calculate_overcrowding_risk(projected_occupancy_percentage)
        
        overcrowding_score = WEIGHT_OVERCROWDING
        if overcrowding_level == "critical":
            overcrowding_score = 0.0
            limitations.append("Allocation would push shelter to critical overcrowding.")
        elif overcrowding_level == "high":
            overcrowding_score *= 0.3
            limitations.append("Allocation causes high overcrowding risk.")
        elif overcrowding_level == "moderate":
            overcrowding_score *= 0.8
        else:
            positive_reasons.append("Low overcrowding risk after allocation.")
            
        # Total Score
        total_score = capacity_score + dist_score + vuln_score + util_score + route_score + workload_score + overcrowding_score
        
        explanation = f"{shelter.name} scored {total_score:.1f}/100. It can accommodate {proposed_allocation} people. Overcrowding risk is {overcrowding_level}."
        
        recommendations.append(ShelterRecommendationResponse(
            shelter_id=shelter.id,
            shelter_name=shelter.name,
            rank=0, # assigned later
            total_score=round(total_score, 2),
            available_capacity=available_capacity,
            proposed_people_count=proposed_allocation,
            projected_occupancy_percentage=round(projected_occupancy_percentage, 1),
            overcrowding_risk_level=overcrowding_level,
            distance_km=round(distance, 1),
            capacity_score=round(capacity_score, 1),
            distance_score=round(dist_score, 1),
            medical_support_score=round(vuln_score, 1),
            vulnerability_support_score=round(vuln_score, 1),
            utility_score=round(util_score, 1),
            overcrowding_risk_score=round(overcrowding_score, 1),
            route_risk=route_risk_str,
            positive_reasons=positive_reasons,
            limitations=limitations,
            explanation=explanation
        ))

    # Sort recommendations by score descending
    recommendations.sort(key=lambda x: x.total_score, reverse=True)
    
    # Assign ranks
    for idx, rec in enumerate(recommendations):
        rec.rank = idx + 1
        
    single_source = []
    split_plan = None
    
    if len(recommendations) > 0:
        if recommendations[0].proposed_people_count == total_requested:
            # We have a valid single source
            single_source = recommendations
        else:
            single_source = recommendations
            # Generate Split Plan
            split_shelters = []
            remaining = total_requested
            
            for rec in recommendations:
                if remaining <= 0:
                    break
                allocation = min(remaining, rec.available_capacity)
                rec.proposed_people_count = allocation
                # Re-eval projected occupancy for the split fraction
                shelter = next(s for s in shelters if s.id == rec.shelter_id)
                proj = shelter.occupied_capacity + shelter.reserved_capacity + allocation
                rec.projected_occupancy_percentage = round((proj / shelter.total_capacity * 100), 1) if shelter.total_capacity > 0 else 100
                rec.overcrowding_risk_level = calculate_overcrowding_risk(rec.projected_occupancy_percentage)
                
                split_shelters.append(rec)
                remaining -= allocation
                
            split_plan = SplitShelterAllocationPlan(
                is_split=True,
                shelters_involved=split_shelters,
                remaining_uncovered_people=remaining,
                explanation=f"Split allocation across {len(split_shelters)} shelters. {remaining} people remain uncovered." if remaining > 0 else f"Split allocation across {len(split_shelters)} shelters covers all {total_requested} people."
            )
            
    return ShelterAllocationEvaluationResponse(
        single_source_recommendations=single_source,
        split_allocation_plan=split_plan
    )
