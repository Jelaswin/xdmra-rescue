import math
from typing import List
from sqlalchemy.orm import Session
from app.models import (
    Incident, EmergencyShelter, ShelterRequest, ShelterRouteCondition,
    ShelterOperatingStatus, ShelterRequestStatus, RouteRisk
)
from app.schemas import (
    ShelterRecommendationResponse, SplitShelterAllocationPlan,
    ShelterAllocationEvaluationResponse
)
from app.services.scoring.shelter_scoring import (
    ShelterScoringInput, score_shelter, rank_shelters,
    calculate_overcrowding_risk,
)
from app.services.scoring.common import haversine_distance


WEIGHT_CAPACITY = 30.0
WEIGHT_DISTANCE = 15.0
WEIGHT_VULNERABILITY = 20.0
WEIGHT_UTILITIES = 15.0
WEIGHT_OVERCROWDING = 10.0
WEIGHT_ROUTE_SAFETY = 5.0
WEIGHT_WORKLOAD = 5.0


def evaluate_shelter_allocation(db: Session, request_id: int, exclude_shelter_ids: List[int] = None) -> ShelterAllocationEvaluationResponse:
    if exclude_shelter_ids is None:
        exclude_shelter_ids = []

    request_obj = db.query(ShelterRequest).filter(ShelterRequest.id == request_id).first()
    if not request_obj:
        raise ValueError(f"ShelterRequest {request_id} not found.")

    incident = db.query(Incident).filter(Incident.id == request_obj.incident_id).first()
    shelters = db.query(EmergencyShelter).filter(EmergencyShelter.id.notin_(exclude_shelter_ids)).all()

    total_requested = request_obj.total_displaced_people

    scoring_inputs = []
    for shelter in shelters:
        route = db.query(ShelterRouteCondition).filter(
            ShelterRouteCondition.incident_id == incident.id,
            ShelterRouteCondition.shelter_id == shelter.id
        ).first()

        inp = ShelterScoringInput(
            shelter_id=shelter.id,
            operating_status=shelter.operating_status.value,
            shelter_latitude=shelter.latitude,
            shelter_longitude=shelter.longitude,
            incident_latitude=incident.latitude,
            incident_longitude=incident.longitude,
            total_displaced_people=total_requested,
            total_capacity=shelter.total_capacity,
            occupied_capacity=shelter.occupied_capacity,
            reserved_capacity=shelter.reserved_capacity,
            maximum_daily_intake=shelter.maximum_daily_intake,
            current_intake_workload=shelter.current_intake_workload,
            has_medical_support=bool(shelter.has_medical_support),
            has_accessibility_support=bool(shelter.has_accessibility_support),
            has_women_child_safe_area=bool(shelter.has_women_child_safe_area),
            has_food=bool(shelter.has_food),
            has_drinking_water=bool(shelter.has_drinking_water),
            has_sanitation=bool(shelter.has_sanitation),
            has_power_backup=bool(shelter.has_power_backup),
            supports_long_term_stay=bool(shelter.supports_long_term_stay),
            mandatory_medical_required=bool(request_obj.medical_observation_required > 0),
            mandatory_accessibility_required=bool(request_obj.accessibility_required > 0),
            route_risk=route.risk_level.value if route else "low",
            route_blocked=bool(route.is_blocked) if route else False,
            estimated_delay_minutes=route.estimated_delay_minutes if route else 0,
        )
        scoring_inputs.append(inp)

    ranked_outputs = rank_shelters(scoring_inputs)
    shelter_map = {s.id: s for s in shelters}

    recommendations = []

    for out in ranked_outputs:
        shelter = shelter_map[out.shelter_id]
        route = db.query(ShelterRouteCondition).filter(
            ShelterRouteCondition.incident_id == incident.id,
            ShelterRouteCondition.shelter_id == shelter.id
        ).first()

        positive_reasons = []
        limitations = []

        if out.capacity_score == WEIGHT_CAPACITY:
            positive_reasons.append("Can accommodate the entire requested population.")
        else:
            limitations.append(f"Can only accommodate {out.proposed_people_count} out of {total_requested} people.")

        if out.distance_km <= 10.0:
            positive_reasons.append("Located within optimal distance (<10km).")
        elif out.distance_km > 50.0:
            limitations.append("Located far from the incident (>50km).")

        if shelter.has_medical_support:
            positive_reasons.append("Has medical support.")
        if shelter.has_accessibility_support:
            positive_reasons.append("Has accessibility support.")
        if shelter.has_women_child_safe_area:
            positive_reasons.append("Has women and child safe area.")

        if shelter.has_food and shelter.has_drinking_water:
            positive_reasons.append("Provides food and drinking water.")

        route_risk_str = route.risk_level.value if route else "low"
        if route:
            if route.risk_level == RouteRisk.medium:
                limitations.append("Medium risk route.")
            elif route.risk_level == RouteRisk.high:
                limitations.append("High risk route.")

        if shelter.maximum_daily_intake > 0:
            workload_ratio = shelter.current_intake_workload / shelter.maximum_daily_intake
            if workload_ratio > 0.8:
                limitations.append("High current intake workload.")

        projected_total = shelter.occupied_capacity + shelter.reserved_capacity + out.proposed_people_count
        projected_occupancy_pct = (projected_total / shelter.total_capacity * 100) if shelter.total_capacity > 0 else 100

        overcrowding_level = calculate_overcrowding_risk(projected_occupancy_pct)
        if overcrowding_level == "critical":
            limitations.append("Allocation would push shelter to critical overcrowding.")
        elif overcrowding_level == "high":
            limitations.append("Allocation causes high overcrowding risk.")
        elif overcrowding_level == "low":
            positive_reasons.append("Low overcrowding risk after allocation.")

        explanation = f"{shelter.name} scored {out.total_score:.1f}/100. It can accommodate {out.proposed_people_count} people. Overcrowding risk is {overcrowding_level}."

        recommendations.append(ShelterRecommendationResponse(
            shelter_id=shelter.id,
            shelter_name=shelter.name,
            rank=0,
            total_score=round(out.total_score, 2),
            available_capacity=out.available_capacity,
            proposed_people_count=out.proposed_people_count,
            projected_occupancy_percentage=round(out.projected_occupancy_pct, 1),
            overcrowding_risk_level=overcrowding_level,
            distance_km=round(out.distance_km, 1),
            capacity_score=round(out.capacity_score, 1),
            distance_score=round(out.distance_score, 1),
            medical_support_score=round(out.medical_support_score, 1),
            vulnerability_support_score=round(out.vulnerability_score, 1),
            utility_score=round(out.utility_score, 1),
            overcrowding_risk_score=round(out.overcrowding_score, 1),
            route_risk=route_risk_str,
            positive_reasons=positive_reasons,
            limitations=limitations,
            explanation=explanation
        ))

    for idx, rec in enumerate(recommendations):
        rec.rank = idx + 1

    single_source = []
    split_plan = None

    if len(recommendations) > 0:
        if recommendations[0].proposed_people_count == total_requested:
            single_source = recommendations
        else:
            single_source = recommendations
            split_shelters = []
            remaining = total_requested

            for rec in recommendations:
                if remaining <= 0:
                    break
                allocation = min(remaining, rec.available_capacity)
                rec.proposed_people_count = allocation
                shelter = shelter_map[rec.shelter_id]
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