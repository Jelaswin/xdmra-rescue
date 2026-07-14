import { DashboardSummary, Incident, IncidentCreateRequest, RescueTeam } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchWithConfig(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}/api${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // Ignore JSON parse errors for non-JSON responses
    }
    throw new ApiError(response.status, typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
  }

  return response.json();
}

export const api = {
  checkHealth: () => fetchWithConfig('/health'),
  
  getDashboardSummary: (): Promise<DashboardSummary> => 
    fetchWithConfig('/dashboard/summary'),

  getIncidents: (): Promise<Incident[]> => 
    fetchWithConfig('/incidents'),

  getIncident: (id: number): Promise<Incident> => 
    fetchWithConfig(`/incidents/${id}`),

  createIncident: (incident: IncidentCreateRequest): Promise<Incident> => 
    fetchWithConfig('/incidents', {
      method: 'POST',
      body: JSON.stringify(incident),
    }),

  getTeams: (): Promise<RescueTeam[]> => 
    fetchWithConfig('/teams'),

  getTeam: (id: number): Promise<RescueTeam> => 
    fetchWithConfig(`/teams/${id}`),
};
