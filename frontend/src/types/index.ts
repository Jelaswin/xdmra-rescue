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
  status: 'recommended' | 'approved' | 'dispatched' | 'completed' | 'cancelled';
  recommendation_score: number | null;
  explanation: string | null;
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
