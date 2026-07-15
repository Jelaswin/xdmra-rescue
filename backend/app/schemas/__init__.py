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
    rescue_team_id: Optional[int] = None
    warehouse_id: Optional[int] = None

class AllocationResponse(BaseModel):
    id: int
    incident_id: int
    rescue_team_id: Optional[int] = None
    warehouse_id: Optional[int] = None
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
    rescue_team_id: Optional[int] = None
    warehouse_id: Optional[int] = None
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


# --- Phase 6 Relief Schemas ---

class WarehouseBase(BaseModel):
    name: str
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    warehouse_type: Optional[str] = None
    maximum_dispatch_capacity: int = 0

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: int
    operating_status: str
    current_dispatch_workload: int
    contact_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReliefInventoryBase(BaseModel):
    item_type: str
    display_name: str
    unit: str
    quantity_available: int = 0
    reorder_level: int = 0
    batch_reference: Optional[str] = None
    expiry_date: Optional[datetime] = None

class ReliefInventoryCreate(ReliefInventoryBase):
    pass

class ReliefInventoryResponse(ReliefInventoryBase):
    id: int
    warehouse_id: int
    quantity_reserved: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReliefRequestItemBase(BaseModel):
    item_type: str
    requested_quantity: int
    source_type: str
    calculation_reason: Optional[str] = None

class ReliefRequestBase(BaseModel):
    support_duration_days: int = 1
    total_people: int = 0
    notes: Optional[str] = None

class ReliefRequestCreate(ReliefRequestBase):
    items: List[ReliefRequestItemBase]

class ReliefRequestItemResponse(ReliefRequestItemBase):
    id: int
    relief_request_id: int
    approved_quantity: int
    model_config = ConfigDict(from_attributes=True)

class ReliefRequestResponse(ReliefRequestBase):
    id: int
    incident_id: int
    status: str
    generated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[ReliefRequestItemResponse] = []
    # We will fetch items dynamically or via relationship
    model_config = ConfigDict(from_attributes=True)

class ReliefDemandSuggestionItem(BaseModel):
    item_type: str
    quantity: int
    unit: str
    reason: str

class ReliefDemandSuggestion(BaseModel):
    support_duration_days: int
    suggested_items: List[ReliefDemandSuggestionItem]

class DeliveryVehicleBase(BaseModel):
    name: str
    vehicle_type: Optional[str] = None
    capacity_units: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DeliveryVehicleCreate(DeliveryVehicleBase):
    warehouse_id: Optional[int] = None

class DeliveryVehicleResponse(DeliveryVehicleBase):
    id: int
    warehouse_id: Optional[int] = None
    availability_status: str
    current_workload: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReliefRecommendationResponse(BaseModel):
    warehouse_id: int
    warehouse_name: str
    rank: int
    total_score: float
    stock_coverage_percentage: float
    covered_items: List[str]
    missing_items: List[str]
    distance_km: float
    vehicle_availability: bool
    route_risk: Optional[str] = None
    positive_reasons: List[str]
    limitations: List[str]
    explanation: str

class SplitAllocationWarehouse(BaseModel):
    warehouse_id: int
    warehouse_name: str
    provided_items: Dict[str, int]
    distance_km: float
    explanation: str

class SplitAllocationResponse(BaseModel):
    is_split: bool
    warehouses_involved: List[SplitAllocationWarehouse]
    remaining_shortages: Dict[str, int]
    explanation: str

class ReliefAllocationEvaluationResponse(BaseModel):
    single_source_recommendations: List[ReliefRecommendationResponse]
    split_allocation_plan: Optional[SplitAllocationResponse] = None

class ReliefDispatchItemBase(BaseModel):
    inventory_id: int
    item_type: str
    allocated_quantity: int
    unit: str

class ReliefDispatchCreate(BaseModel):
    warehouse_id: int
    vehicle_id: Optional[int] = None
    items: List[ReliefDispatchItemBase]
    recommendation_score: Optional[float] = None
    explanation: Optional[str] = None

class ReliefDispatchItemResponse(ReliefDispatchItemBase):
    id: int
    relief_dispatch_id: int
    model_config = ConfigDict(from_attributes=True)

class ReliefDispatchResponse(BaseModel):
    id: int
    relief_request_id: int
    warehouse_id: int
    vehicle_id: Optional[int] = None
    status: str
    dispatch_reference: Optional[str] = None
    total_allocated_units: int
    recommendation_score: Optional[float] = None
    explanation: Optional[str] = None
    approved_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Phase 7 Shelter Schemas ---

class EmergencyShelterBase(BaseModel):
    name: str
    shelter_type: Optional[str] = None
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    operating_status: str = "open"
    total_capacity: int = 0
    maximum_daily_intake: int = 0
    has_medical_support: int = 0
    has_accessibility_support: int = 0
    has_women_child_safe_area: int = 0
    has_food: int = 0
    has_drinking_water: int = 0
    has_power_backup: int = 0
    has_sanitation: int = 0
    supports_long_term_stay: int = 0
    contact_reference: Optional[str] = None

class EmergencyShelterCreate(EmergencyShelterBase):
    pass

class EmergencyShelterUpdate(BaseModel):
    operating_status: Optional[str] = None
    has_medical_support: Optional[int] = None
    has_accessibility_support: Optional[int] = None
    has_women_child_safe_area: Optional[int] = None
    has_food: Optional[int] = None
    has_drinking_water: Optional[int] = None
    has_power_backup: Optional[int] = None
    has_sanitation: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    occupied_capacity: Optional[int] = None # For dev controls

class EmergencyShelterResponse(EmergencyShelterBase):
    id: int
    occupied_capacity: int
    reserved_capacity: int
    current_intake_workload: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShelterRequestBase(BaseModel):
    total_displaced_people: int = 0
    adults: int = 0
    children: int = 0
    elderly_people: int = 0
    injured_people: int = 0
    accessibility_required: int = 0
    pregnant_women: int = 0
    medical_observation_required: int = 0
    household_count: int = 0
    expected_stay_days: int = 1
    notes: Optional[str] = None

class ShelterRequestCreate(ShelterRequestBase):
    pass

class ShelterRequestUpdate(ShelterRequestBase):
    status: Optional[str] = None

class ShelterRequestResponse(ShelterRequestBase):
    id: int
    incident_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShelterRecommendationResponse(BaseModel):
    shelter_id: int
    shelter_name: str
    rank: int
    total_score: float
    available_capacity: int
    proposed_people_count: int
    projected_occupancy_percentage: float
    overcrowding_risk_level: str
    distance_km: float
    capacity_score: float
    distance_score: float
    medical_support_score: float
    vulnerability_support_score: float
    utility_score: float
    overcrowding_risk_score: float
    route_risk: Optional[str] = None
    positive_reasons: List[str]
    limitations: List[str]
    explanation: str

class SplitShelterAllocationPlan(BaseModel):
    is_split: bool
    shelters_involved: List[ShelterRecommendationResponse]
    remaining_uncovered_people: int
    explanation: str

class ShelterAllocationEvaluationResponse(BaseModel):
    single_source_recommendations: List[ShelterRecommendationResponse]
    split_allocation_plan: Optional[SplitShelterAllocationPlan] = None

class ShelterReservationCreate(BaseModel):
    shelter_id: int
    reserved_people: int
    recommendation_score: Optional[float] = None
    explanation: Optional[str] = None

class ShelterReservationResponse(BaseModel):
    id: int
    shelter_request_id: int
    shelter_id: int
    reserved_people: int
    status: str
    recommendation_score: Optional[float] = None
    explanation: Optional[str] = None
    approved_at: Optional[datetime] = None
    admitted_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShelterRouteConditionCreate(BaseModel):
    shelter_id: int
    risk_level: str
    is_blocked: int
    estimated_delay_minutes: int = 0
    description: Optional[str] = None

class ShelterRouteConditionResponse(ShelterRouteConditionCreate):
    id: int
    incident_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShelterDashboardSummary(BaseModel):
    total_shelters: int
    open_shelters: int
    available_spaces: int
    reserved_spaces: int
    occupied_spaces: int
    high_overcrowding_risk_shelters: int
    active_reservations: int
    people_in_transit: int
