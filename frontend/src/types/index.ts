export interface Incident {
  id: number;
  title: string;
  description: string;
  incident_type: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_people: number;
  injured_people: number;
  vulnerable_people: number;
  
  // Phase 4 Location Fields
  location_name?: string;
  location_accuracy?: string;
  location_source?: string;
  location_notes?: string;
  
  // Phase 2
  trapped_people: number;
  children_count: number;
  elderly_count: number;
  required_skills: string[];
  required_equipment: string[];
  priority_score: number | null;
  priority_level: string | null;
  priority_reasons: string[];
  
  ml_priority_level: string | null;
  ml_priority_confidence: number | null;
  ml_model_name: string | null;
  ml_model_version: string | null;
  ml_predicted_at: string | null;
  priority_agreement_status: string | null;
  requires_priority_review: boolean;

  status: 'reported' | 'verified' | 'assigned' | 'in_progress' | 'resolved';
  created_at: string;
  updated_at: string;
}

export interface IncidentCreateRequest {
  title: string;
  description: string;
  incident_type: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_people: number;
  injured_people: number;
  vulnerable_people: number;
  
  // Phase 4 Location Fields
  location_name?: string;
  location_accuracy?: string;
  location_source?: string;
  location_notes?: string;
  
  // Phase 2
  trapped_people: number;
  children_count: number;
  elderly_count: number;
  required_skills: string[];
  required_equipment: string[];
}

export interface DashboardSummary {
  total_incidents: number;
  critical_incidents: number;
  available_teams: number;
  active_allocations: number;
}

export interface RescueTeam {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  skills: string[];
  equipment: string[];
  capacity: number;
  current_workload: number;
  availability_status: 'available' | 'assigned' | 'unavailable';
  created_at: string;
  updated_at: string;
}

export interface TeamRecommendation {
  team_id: number;
  team_name: string;
  rank: number;
  total_score: number;
  distance_km: number;
  skill_match_percentage: number;
  equipment_match_percentage: number;
  capacity_score: number;
  distance_score: number;
  workload_score: number;
  route_risk_score: number;
  positive_reasons: string[];
  limitations: string[];
  explanation: string;
}

export interface PriorityResult {
  priority_score: number;
  priority_level: string;
  reasons: string[];
  factor_breakdown: Record<string, number>;
}

export interface Allocation {
  id: number;
  incident_id: number;
  rescue_team_id: number;
  status: 'recommended' | 'approved' | 'dispatched' | 'completed' | 'cancelled' | 'superseded' | 'reallocated';
  recommendation_score: number | null;
  explanation: string | null;

  superseded_by_allocation_id?: number;
  supersedes_allocation_id?: number;
  ended_at?: string;
  termination_reason?: string;
  reallocation_reason?: string;
  approved_by?: string;

  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  loaded: boolean;
  message?: string;
  model_name?: string;
  model_version?: string;
  features?: string[];
  classes?: string[];
  evaluation_metrics?: Record<string, number>;
  training_dataset_type?: string;
  training_dataset_size?: number;
}

export interface MLPredictionResponse {
  predicted_priority: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  model_name: string;
  model_version: string;
}

export interface PriorityComparisonResponse {
  rule_priority: string;
  rule_score: number;
  ml_priority: string;
  ml_confidence: number;
  agreement_status: string;
  requires_officer_review: boolean;
  comparison_message: string;
}

export interface GeocodingResult {
  display_name: string;
  latitude: number;
  longitude: number;
  provider: string;
  bounding_box?: number[];
}

export interface MapIncident {
  id: number;
  title: string;
  incident_type: string;
  latitude: number;
  longitude: number;
  severity: string;
  status: string;
  affected_people: number;
  priority_level?: string | null;
  ml_priority_level?: string | null;
}

export interface MapTeam {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  availability_status: string;
  capacity: number;
  current_workload: number;
  skills: string[];
  equipment: string[];
}

export interface MapOverviewResponse {
  incidents: MapIncident[];
  teams: MapTeam[];
}

// Phase 5 Reallocation Types
export interface ReallocationEvaluateRequest {
  trigger_type: string;
  trigger_description?: string;
}

export interface ReallocationApprovalRequest {
  replacement_team_id: number;
  trigger_type: string;
  reason: string;
}

export interface OperationalStatusUpdate {
  availability_status: string;
  reason?: string;
}

export interface RouteConditionCreate {
  rescue_team_id: number;
  risk_level: string;
  is_blocked: boolean;
  estimated_delay_minutes: number;
  description?: string;
}

export interface ReallocationRecommendationResult {
  reallocation_required: boolean;
  trigger_type: string;
  current_team: Record<string, any>;
  reason: string;
  recommended_replacement?: Record<string, any>;
  explanation: string;
  alternatives: TeamRecommendation[];
}

export interface ReallocationEventResponse {
  id: number;
  incident_id: number;
  previous_allocation_id: number;
  previous_team_id: number;
  replacement_team_id?: number;
  trigger_type: string;
  trigger_description?: string;
  old_recommendation_score?: number;
  new_recommendation_score?: number;
  explanation?: string;
  status: string;
  created_at: string;
  approved_at?: string;
  rejected_at?: string;
}

// ==========================================
// PHASE 6: RELIEF-SUPPLY ALLOCATION TYPES
// ==========================================

export interface Warehouse {
  id: number;
  name: string;
  location_name?: string;
  latitude: number;
  longitude: number;
  warehouse_type?: string;
  operating_status: string;
  maximum_dispatch_capacity: number;
  current_dispatch_workload: number;
  contact_reference?: string;
  created_at: string;
  updated_at: string;
}

export interface ReliefInventory {
  id: number;
  warehouse_id: number;
  item_type: string;
  display_name: string;
  unit: string;
  quantity_available: number;
  quantity_reserved: number;
  reorder_level: number;
  batch_reference?: string;
  expiry_date?: string;
  updated_at: string;
}

export interface DeliveryVehicle {
  id: number;
  warehouse_id?: number;
  name: string;
  vehicle_type?: string;
  capacity_units: number;
  availability_status: string;
  current_workload: number;
  latitude?: number;
  longitude?: number;
  updated_at: string;
}

export interface ReliefDemandSuggestionItem {
  item_type: string;
  quantity: number;
  unit: string;
  reason: string;
}

export interface ReliefDemandSuggestion {
  support_duration_days: number;
  suggested_items: ReliefDemandSuggestionItem[];
}

export interface ReliefRequestItem {
  id?: number;
  relief_request_id?: number;
  item_type: string;
  requested_quantity: number;
  approved_quantity: number;
  source_type: string;
  calculation_reason?: string;
}

export interface ReliefRequest {
  id: number;
  incident_id: number;
  support_duration_days: number;
  total_people: number;
  notes?: string;
  status: string;
  generated_by?: string;
  created_at: string;
  updated_at: string;
  items: ReliefRequestItem[];
}

export interface ReliefRecommendation {
  warehouse_id: number;
  warehouse_name: string;
  rank: number;
  total_score: number;
  stock_coverage_percentage: number;
  covered_items: string[];
  missing_items: string[];
  distance_km: number;
  vehicle_availability: boolean;
  route_risk?: string;
  positive_reasons: string[];
  limitations: string[];
  explanation: string;
}

export interface SplitAllocationWarehouse {
  warehouse_id: number;
  warehouse_name: string;
  provided_items: Record<string, number>;
  distance_km: number;
  explanation: string;
}

export interface SplitAllocationPlan {
  is_split: boolean;
  warehouses_involved: SplitAllocationWarehouse[];
  remaining_shortages: Record<string, number>;
  explanation: string;
}

export interface ReliefAllocationEvaluation {
  single_source_recommendations: ReliefRecommendation[];
  split_allocation_plan?: SplitAllocationPlan;
}

export interface ReliefDispatchItem {
  id?: number;
  inventory_id: number;
  item_type: string;
  allocated_quantity: number;
  unit: string;
}

export interface ReliefDispatch {
  id: number;
  relief_request_id: number;
  warehouse_id: number;
  vehicle_id?: number;
  status: string;
  dispatch_reference?: string;
  total_allocated_units: number;
  recommendation_score?: number;
  explanation?: string;
  approved_at?: string;
  dispatched_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  items: ReliefDispatchItem[];
}

export interface ReliefDashboardSummary {
  active_requests: number;
  dispatches_in_progress: number;
  warehouses_active: number;
  low_stock_items: number;
}

// ==========================================
// PHASE 7: SHELTER ALLOCATION TYPES
// ==========================================

export interface EmergencyShelter {
  id: number;
  name: string;
  shelter_type?: string;
  location_name?: string;
  latitude: number;
  longitude: number;
  operating_status: string;
  total_capacity: number;
  occupied_capacity: number;
  reserved_capacity: number;
  maximum_daily_intake: number;
  has_medical_support: number;
  has_accessibility_support: number;
  has_women_child_safe_area: number;
  has_food: number;
  has_drinking_water: number;
  has_power_backup: number;
  has_sanitation: number;
  supports_long_term_stay: number;
  contact_reference?: string;
  created_at: string;
  updated_at: string;
}

export interface ShelterRequest {
  id: number;
  incident_id: number;
  total_displaced_people: number;
  medical_observation_required: number;
  accessibility_required: number;
  women_child_safe_area_required: number;
  notes?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ShelterRecommendation {
  shelter_id: number;
  shelter_name: string;
  rank: number;
  total_score: number;
  capacity_score: number;
  distance_score: number;
  vulnerability_score: number;
  utilities_score: number;
  overcrowding_score: number;
  route_safety_score: number;
  workload_score: number;
  proposed_people_count: number;
  distance_km: number;
  overcrowding_risk_level: string;
  positive_reasons: string[];
  limitations: string[];
  explanation: string;
}

export interface ShelterSplitAllocationWarehouse {
  shelter_id: number;
  shelter_name: string;
  proposed_people_count: number;
  distance_km: number;
  explanation: string;
}

export interface ShelterSplitAllocationPlan {
  is_split: boolean;
  shelters_involved: ShelterSplitAllocationWarehouse[];
  remaining_uncovered_people: number;
  explanation: string;
}

export interface ShelterAllocationEvaluationResponse {
  single_source_recommendations: ShelterRecommendation[];
  split_allocation_plan?: ShelterSplitAllocationPlan;
}

export interface ShelterReservation {
  id: number;
  shelter_request_id: number;
  shelter_id: number;
  reserved_people: number;
  status: string;
  recommendation_score?: number;
  explanation?: string;
  approved_at?: string;
  admitted_at?: string;
  cancelled_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  shelter?: EmergencyShelter;
}

export interface ShelterDashboardSummary {
  total_shelters: number;
  available_spaces: number;
  people_sheltered: number;
  active_requests: number;
}

// ==========================================
// PHASE 8: COMMAND CENTER TYPES
// ==========================================

export interface CommandDashboardSummary {
  total_active_incidents: number;
  critical_incidents: number;
  high_priority_incidents: number;
  unassigned_incidents: number;
  incidents_awaiting_rescue: number;
  active_rescue_allocations: number;
  rescue_reallocations_pending: number;
  active_relief_requests: number;
  relief_shortages: number;
  dispatches_preparing: number;
  dispatches_in_transit: number;
  low_stock_alerts: number;
  active_shelter_requests: number;
  uncovered_displaced_people: number;
  shelter_reservations_in_transit: number;
  high_overcrowding_risk_shelters: number;
  blocked_routes: number;
  high_risk_routes: number;
  pending_officer_decisions: number;
}

export interface PendingDecision {
  id: string;
  decision_type: string;
  incident_id: number;
  incident_title: string;
  priority: string;
  resource_type: string;
  resource_id?: number;
  reason: string;
  recommendation_summary: string;
  waiting_duration_minutes: number;
  severity: string;
  action_route: string;
  created_at: string;
}

export interface OperationalAlert {
  id: number;
  category: string;
  severity: string;
  title: string;
  description: string;
  incident_id?: number;
  resource_type?: string;
  resource_id?: number;
  recommended_action?: string;
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  acknowledged_at?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event_category: string;
  title: string;
  description: string;
  source: string;
  resource_type?: string;
  resource_name?: string;
  officer_action: boolean;
  status?: string;
  explanation?: string;
  score?: number;
}

export interface IncidentOperationalSummary {
  incident_id: number;
  title: string;
  incident_type: string;
  location: string;
  rule_priority: string;
  ml_priority?: string;
  rule_ml_agreement: boolean;
  current_status: string;
  waiting_duration_minutes: number;
  last_updated: string;
  assigned_team?: string;
  allocation_status?: string;
  rescue_score?: number;
  team_availability?: string;
  route_risk?: string;
  reallocation_status?: string;
  relief_request_status?: string;
  requested_items: string[];
  allocated_items: string[];
  shortages: string[];
  active_dispatches: number;
  warehouse_sources: string[];
  shelter_request_status?: string;
  displaced_population: number;
  reserved_population: number;
  admitted_population: number;
  uncovered_population: number;
  selected_shelters: string[];
  overcrowding_risks: string[];
  active_alerts: number;
  highest_alert_severity?: string;
  pending_decisions: number;
  blocked_routes: number;
}

export interface CommandMapOverview {
  incidents: MapIncident[];
  teams: MapTeam[];
  warehouses: Warehouse[];
  shelters: EmergencyShelter[];
  blocked_routes: Array<{
    incident_id: number;
    shelter_id?: number;
    rescue_team_id?: number;
    risk_level: string;
    is_blocked: boolean;
  }>;
}
