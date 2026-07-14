import { Incident, IncidentCreateRequest, DashboardSummary, RescueTeam, PriorityResult, TeamRecommendation, Allocation, MLPredictionResponse, PriorityComparisonResponse, ModelInfo, GeocodingResult, MapOverviewResponse, ReallocationRecommendationResult, ReallocationEventResponse, RouteConditionCreate, OperationalStatusUpdate } from '../types';

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
  },

  searchLocations: async (query: string): Promise<GeocodingResult[]> => {
    const response = await fetch(`${API_BASE_URL}/locations/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search locations');
    return response.json();
  },
  
  getMapOverview: async (): Promise<MapOverviewResponse> => {
    const response = await fetch(`${API_BASE_URL}/map/overview`);
    if (!response.ok) throw new Error('Failed to fetch map overview');
    return response.json();
  },

  // Phase 5: Reallocation Endpoints
  evaluateReallocation: async (incidentId: number, triggerType: string, description?: string): Promise<ReallocationRecommendationResult> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/evaluate-reallocation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trigger_type: triggerType, trigger_description: description })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to evaluate reallocation');
    }
    return response.json();
  },

  approveReallocation: async (incidentId: number, replacementTeamId: number, triggerType: string, reason: string): Promise<Allocation> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/reallocate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ replacement_team_id: replacementTeamId, trigger_type: triggerType, reason })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to approve reallocation');
    }
    return response.json();
  },

  getReallocationHistory: async (incidentId: number): Promise<ReallocationEventResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/reallocation-history`);
    if (!response.ok) throw new Error('Failed to fetch reallocation history');
    return response.json();
  },

  createRouteCondition: async (incidentId: number, data: RouteConditionCreate): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/incidents/${incidentId}/route-conditions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update route condition');
    return response.json();
  },

  updateTeamStatus: async (teamId: number, status: string, reason?: string): Promise<RescueTeam> => {
    const response = await fetch(`${API_BASE_URL}/teams/${teamId}/operational-status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ availability_status: status, reason })
    });
    if (!response.ok) throw new Error('Failed to update team operational status');
    return response.json();
  }

,
  // Phase 6 Relief APIs
  getWarehouses: async () => {
    const res = await fetch(`${API_BASE_URL}/warehouses`);
    return { data: await res.json() };
  },
  getWarehouseInventory: async (id: number) => {
    const res = await fetch(`${API_BASE_URL}/warehouses/${id}/inventory`);
    return { data: await res.json() };
  },
  getDeliveryVehicles: async () => {
    const res = await fetch(`${API_BASE_URL}/delivery-vehicles`);
    return { data: await res.json() };
  },
  suggestReliefDemand: async (incidentId: number, days: number = 1) => {
    const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/relief-demand/suggest?support_duration_days=${days}`, { method: 'POST' });
    return { data: await res.json() };
  },
  createReliefRequest: async (incidentId: number, data: any) => {
    const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/relief-requests`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },
  getReliefRequests: async (incidentId: number) => {
    const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/relief-requests`);
    return { data: await res.json() };
  },
  getReliefRecommendations: async (requestId: number) => {
    const res = await fetch(`${API_BASE_URL}/relief-requests/${requestId}/recommendations`, { method: 'POST' });
    return { data: await res.json() };
  },
  approveDispatch: async (requestId: number, data: any) => {
    const res = await fetch(`${API_BASE_URL}/relief-requests/${requestId}/approve-dispatch`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },
  getReliefDashboardSummary: async () => {
    const res = await fetch(`${API_BASE_URL}/relief/dashboard-summary`);
    return { data: await res.json() };
  },
  getInventoryAlerts: async () => {
    const res = await fetch(`${API_BASE_URL}/relief/inventory-alerts`);
    return { data: await res.json() };
  }
};
