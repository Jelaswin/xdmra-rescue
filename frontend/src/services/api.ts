import { Incident, IncidentCreateRequest, DashboardSummary, RescueTeam, PriorityResult, TeamRecommendation, Allocation, MLPredictionResponse, PriorityComparisonResponse, ModelInfo } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  checkHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },

  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
    if (!response.ok) throw new Error('Failed to fetch dashboard summary');
    return response.json();
  },

  getIncidents: async (): Promise<Incident[]> => {
    const response = await fetch(`${API_BASE_URL}/incidents`);
    if (!response.ok) throw new Error('Failed to fetch incidents');
    return response.json();
  },

  createIncident: async (data: IncidentCreateRequest): Promise<Incident> => {
    const response = await fetch(`${API_BASE_URL}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create incident');
    return response.json();
  },

  getTeams: async (): Promise<RescueTeam[]> => {
    const response = await fetch(`${API_BASE_URL}/teams`);
    if (!response.ok) throw new Error('Failed to fetch teams');
    return response.json();
  },

  calculatePriority: async (incidentId: number): Promise<PriorityResult> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/calculate-priority`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to calculate priority');
    return response.json();
  },

  getTeamRecommendations: async (incidentId: number): Promise<TeamRecommendation[]> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/team-recommendations`);
    if (!response.ok) throw new Error('Failed to fetch team recommendations');
    return response.json();
  },

  createAllocation: async (incidentId: number, teamId: number): Promise<Allocation> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/allocations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rescue_team_id: teamId })
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to create allocation');
    }
    return response.json();
  },

  fetchIncidentAllocations: async (incidentId: number): Promise<Allocation[]> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/allocations`);
    if (!response.ok) throw new Error('Failed to fetch allocations');
    return response.json();
  },

  predictPriorityML: async (incidentId: number): Promise<PriorityComparisonResponse> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/predict-priority-ml`, {
      method: 'POST'
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to predict ML priority');
    }
    return response.json();
  },

  getModelInfo: async (): Promise<ModelInfo> => {
    const response = await fetch(`${API_BASE_URL}/ml/model-info`);
    if (!response.ok) throw new Error('Failed to fetch ML model info');
    return response.json();
  }
};
