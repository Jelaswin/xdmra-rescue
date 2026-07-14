from pydantic import BaseModel, Field, ConfigDict, root_validator, model_validator
from typing import List, Optional, Any, Dict
from datetime import datetime
from app.models import IncidentSeverity, IncidentStatus, TeamAvailability, AllocationStatus, RouteRisk, LocationAccuracy, LocationSource

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    incident_type: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: IncidentSeverity
    affected_people: int = Field(0, ge=0)
    injured_people: int = Field(0, ge=0)
    vulnerable_people: int = Field(0, ge=0)
    
    # Phase 2 extensions
    trapped_people: int = Field(0, ge=0)
    children_count: int = Field(0, ge=0)
    elderly_count: int = Field(0, ge=0)
    required_skills: List[str] = Field(default_factory=list)
    required_equipment: List[str] = Field(default_factory=list)

    # Phase 4 extensions
    location_name: Optional[str] = None
    location_accuracy: Optional[LocationAccuracy] = None
    location_source: Optional[LocationSource] = None
    location_notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_people_counts(self):
        if self.injured_people > self.affected_people:
            raise ValueError('injured_people cannot exceed affected_people')
        if self.trapped_people > self.affected_people:
            raise ValueError('trapped_people cannot exceed affected_people')
        return self

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    status: IncidentStatus
    priority_score: Optional[float] = None
    priority_level: Optional[str] = None
    priority_reasons: List[str] = Field(default_factory=list)
    
    ml_priority_level: Optional[str] = None
    ml_priority_confidence: Optional[float] = None
    ml_model_name: Optional[str] = None
    ml_model_version: Optional[str] = None
    ml_predicted_at: Optional[datetime] = None
    priority_agreement_status: Optional[str] = None
    requires_priority_review: bool = False
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RescueTeam(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    skills: List[str]
    equipment: List[str]
    capacity: int
    current_workload: int
    availability_status: TeamAvailability
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DashboardSummary(BaseModel):
    total_incidents: int
    critical_incidents: int
    available_teams: int
    active_allocations: int

class AllocationCreate(BaseModel):
    rescue_team_id: int

class AllocationResponse(BaseModel):
    id: int
    incident_id: int
    rescue_team_id: int
    status: AllocationStatus
    recommendation_score: Optional[float] = None
    explanation: Optional[str] = None
    
    # Phase 5 Added fields
    superseded_by_allocation_id: Optional[int] = None
    supersedes_allocation_id: Optional[int] = None
    ended_at: Optional[datetime] = None
    termination_reason: Optional[str] = None
    reallocation_reason: Optional[str] = None
    approved_by: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TeamRecommendation(BaseModel):
    team_id: int
    team_name: str
    rank: int
    total_score: float
    distance_km: float
    skill_match_percentage: float
    equipment_match_percentage: float
    capacity_score: float
    distance_score: float
    workload_score: float
    route_risk_score: float
    positive_reasons: List[str]
    limitations: List[str]
    explanation: str

class PriorityResult(BaseModel):
    priority_score: float
    priority_level: str
    reasons: List[str]
    factor_breakdown: Dict[str, float]

class MLPredictionResponse(BaseModel):
    predicted_priority: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_name: str
    model_version: str

class PriorityComparisonResponse(BaseModel):
    rule_priority: str
    rule_score: float
    ml_priority: str
    ml_confidence: float
    agreement_status: str
    requires_officer_review: bool
    comparison_message: str

class ModelInfoResponse(BaseModel):
    loaded: bool
    message: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    features: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    evaluation_metrics: Optional[Dict[str, float]] = None
    training_dataset_type: Optional[str] = None
    training_dataset_size: Optional[int] = None

# Phase 4 Map and Location Schemas
class GeocodingResult(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    provider: str
    bounding_box: Optional[List[float]] = None

class IncidentLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: Optional[str] = None
    location_accuracy: Optional[LocationAccuracy] = None
    location_source: Optional[LocationSource] = None
    location_notes: Optional[str] = None

class TeamLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class MapIncident(BaseModel):
    id: int
    title: str
    incident_type: str
    latitude: float
    longitude: float
    severity: IncidentSeverity
    status: IncidentStatus
    affected_people: int
    priority_level: Optional[str] = None
    ml_priority_level: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class MapTeam(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    availability_status: TeamAvailability
    capacity: int
    current_workload: int
    skills: List[str]
    equipment: List[str]
    
    model_config = ConfigDict(from_attributes=True)

class MapOverviewResponse(BaseModel):
    incidents: List[MapIncident]
    teams: List[MapTeam]

# Phase 5 Reallocation Schemas
class ReallocationEvaluateRequest(BaseModel):
    trigger_type: str
    trigger_description: Optional[str] = None
    
class ReallocationApprovalRequest(BaseModel):
    replacement_team_id: int
    trigger_type: str
    reason: str

class OperationalStatusUpdate(BaseModel):
    availability_status: TeamAvailability
    reason: Optional[str] = None

class RouteConditionCreate(BaseModel):
    rescue_team_id: int
    risk_level: RouteRisk
    is_blocked: bool
    estimated_delay_minutes: int = 0
    description: Optional[str] = None

class ReallocationRecommendationResult(BaseModel):
    reallocation_required: bool
    trigger_type: str
    current_team: Dict[str, Any]
    reason: str
    recommended_replacement: Optional[Dict[str, Any]] = None
    explanation: str
    alternatives: List[TeamRecommendation]

class ReallocationEventResponse(BaseModel):
    id: int
    incident_id: int
    previous_allocation_id: int
    previous_team_id: int
    replacement_team_id: Optional[int] = None
    trigger_type: str
    trigger_description: Optional[str] = None
    old_recommendation_score: Optional[float] = None
    new_recommendation_score: Optional[float] = None
    explanation: Optional[str] = None
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
