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
  
  // Phase 2
  trapped_people: number;
  children_count: number;
  elderly_count: number;
  required_skills: string[];
  required_equipment: string[];
  priority_score: number | null;
  priority_level: string | null;
  priority_reasons: string[];

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
