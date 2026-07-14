export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentStatus = 'reported' | 'verified' | 'assigned' | 'in_progress' | 'resolved';
export type TeamAvailability = 'available' | 'assigned' | 'unavailable';

export interface Incident {
  id: number;
  title: string;
  description: string;
  incident_type: string;
  latitude: number;
  longitude: number;
  severity: IncidentSeverity;
  affected_people: number;
  injured_people: number;
  vulnerable_people: number;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
}

export interface IncidentCreateRequest {
  title: string;
  description: string;
  incident_type: string;
  latitude: number;
  longitude: number;
  severity: IncidentSeverity;
  affected_people: number;
  injured_people: number;
  vulnerable_people: number;
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
  availability_status: TeamAvailability;
  created_at: string;
  updated_at: string;
}

export interface DashboardSummary {
  total_incidents: number;
  critical_incidents: number;
  available_teams: number;
  active_allocations: number;
}

export interface ApiError {
  detail: string | Array<{loc: string[], msg: string, type: string}>;
}
