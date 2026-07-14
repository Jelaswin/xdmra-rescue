from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import (
    Incident, RescueTeam, Allocation, AllocationStatus,
    RouteCondition, ReallocationEvent, ReallocationStatus, TeamAvailability, utcnow
)
from app.schemas import ReallocationRecommendationResult, TeamRecommendation
from app.services.allocation_service import calculate_team_recommendations

def evaluate_reallocation(
    db: Session,
    incident_id: int,
    trigger_type: str,
    trigger_description: Optional[str] = None
) -> ReallocationRecommendationResult:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    active_allocation = db.query(Allocation).filter(
        Allocation.incident_id == incident_id,
        Allocation.status.in_([AllocationStatus.recommended, AllocationStatus.approved, AllocationStatus.dispatched])
    ).first()
    
    if not active_allocation:
        raise HTTPException(status_code=400, detail="No active allocation exists for this incident.")
        
    current_team = db.query(RescueTeam).filter(RescueTeam.id == active_allocation.rescue_team_id).first()
    
    # We fetch all teams EXCEPT the currently assigned team, unavailable teams, and assigned teams.
    # Note: calculate_team_recommendations already excludes unavailable/assigned teams, but we must exclude the current team explicitly.
    all_teams = db.query(RescueTeam).filter(RescueTeam.id != current_team.id).all()
    route_conditions = db.query(RouteCondition).filter(RouteCondition.incident_id == incident_id).all()
    
    alternatives = calculate_team_recommendations(incident, all_teams, route_conditions)
    
    if not alternatives:
        return ReallocationRecommendationResult(
            reallocation_required=True,
            trigger_type=trigger_type,
            current_team={"id": current_team.id, "name": current_team.name},
            reason=trigger_description or f"Triggered by {trigger_type}",
            recommended_replacement=None,
            explanation=f"Reallocation requested due to '{trigger_type}', but NO available replacement teams were found.",
            alternatives=[]
        )
        
    best_alt = alternatives[0]
    
    explanation = (
        f"The existing allocation is no longer suitable because of '{trigger_type}'. "
        f"{best_alt.team_name} is recommended as a replacement because it remains available, "
        f"matches {best_alt.skill_match_percentage}% of required skills, has a safe route, "
        f"and is {best_alt.distance_km} km from the incident. Its total score is {best_alt.total_score}."
    )
    
    return ReallocationRecommendationResult(
        reallocation_required=True,
        trigger_type=trigger_type,
        current_team={"id": current_team.id, "name": current_team.name},
        reason=trigger_description or f"Triggered by {trigger_type}",
        recommended_replacement={
            "team_id": best_alt.team_id,
            "team_name": best_alt.team_name,
            "score": best_alt.total_score,
            "distance_km": best_alt.distance_km
        },
        explanation=explanation,
        alternatives=alternatives
    )

def approve_reallocation(
    db: Session,
    incident_id: int,
    replacement_team_id: int,
    trigger_type: str,
    reason: str,
    officer_name: str = "System"
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    active_allocation = db.query(Allocation).filter(
        Allocation.incident_id == incident_id,
        Allocation.status.in_([AllocationStatus.recommended, AllocationStatus.approved, AllocationStatus.dispatched])
    ).first()
    
    if not active_allocation:
        raise HTTPException(status_code=400, detail="No active allocation exists for this incident.")
        
    replacement_team = db.query(RescueTeam).filter(RescueTeam.id == replacement_team_id).first()
    if not replacement_team:
        raise HTTPException(status_code=404, detail="Replacement team not found")
        
    if replacement_team.availability_status != TeamAvailability.available:
        raise HTTPException(status_code=400, detail="Replacement team is no longer available.")
        
    # Check if replacement team's route is blocked
    route = db.query(RouteCondition).filter(
        RouteCondition.incident_id == incident_id,
        RouteCondition.rescue_team_id == replacement_team_id,
        RouteCondition.is_blocked == 1
    ).first()
    if route:
        raise HTTPException(status_code=400, detail="Replacement team's route is blocked.")
        
    current_team = db.query(RescueTeam).filter(RescueTeam.id == active_allocation.rescue_team_id).first()
    
    try:
        # 1. Supersede old allocation
        active_allocation.status = AllocationStatus.superseded
        active_allocation.ended_at = utcnow()
        active_allocation.termination_reason = reason
        active_allocation.reallocation_reason = trigger_type
        
        # 2. Release previous team workload
        if current_team.current_workload > 0:
            current_team.current_workload -= 1
            
        # 3. Update previous team status if it was assigned (if it failed due to breakdown, it's already unavailable, so we only reset if it is 'assigned')
        if current_team.availability_status == TeamAvailability.assigned:
            current_team.availability_status = TeamAvailability.available
            
        # 4. Create new allocation
        new_allocation = Allocation(
            incident_id=incident_id,
            rescue_team_id=replacement_team_id,
            status=AllocationStatus.approved,
            superseded_by_allocation_id=None,
            supersedes_allocation_id=active_allocation.id,
            approved_by=officer_name,
            explanation=f"Reallocated due to {trigger_type}."
        )
        db.add(new_allocation)
        db.flush() # get new_allocation.id
        
        active_allocation.superseded_by_allocation_id = new_allocation.id
        
        # 5. Update replacement team
        replacement_team.availability_status = TeamAvailability.assigned
        replacement_team.current_workload += 1
        
        # 6. Create ReallocationEvent
        event = ReallocationEvent(
            incident_id=incident_id,
            previous_allocation_id=active_allocation.id,
            previous_team_id=current_team.id,
            replacement_team_id=replacement_team_id,
            trigger_type=trigger_type,
            trigger_description=reason,
            old_recommendation_score=active_allocation.recommendation_score,
            new_recommendation_score=None, # we don't recalculate perfectly here unless passed
            explanation=f"Officer approved reallocation due to {trigger_type}.",
            status=ReallocationStatus.approved,
            approved_at=utcnow()
        )
        db.add(event)
        
        db.commit()
        db.refresh(new_allocation)
        return new_allocation
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process reallocation: {str(e)}")
