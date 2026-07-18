import { Incident, IncidentCreateRequest, DashboardSummary, RescueTeam, PriorityResult, TeamRecommendation, Allocation, MLPredictionResponse, PriorityComparisonResponse, ModelInfo, GeocodingResult, MapOverviewResponse, ReallocationRecommendationResult, ReallocationEventResponse, RouteConditionCreate, OperationalStatusUpdate, CommandDashboardSummary, PendingDecision, OperationalAlert, IncidentOperationalSummary, TimelineEvent, CommandMapOverview, LoginRequest, LoginResponse, User } from '../types';

function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_URL as string | undefined;
  if (envUrl && envUrl.trim() !== "") {
    return envUrl.replace(/\/+$/, "");
  }
  return "http://127.0.0.1:8000/api";
}

const API_BASE_URL = getApiBaseUrl();

const TOKEN_KEY = 'xdmra_access_token';
const REFRESH_TOKEN_KEY = 'xdmra_refresh_token';

export const auth = {
  getAccessToken: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  getRefreshToken: (): string | null => sessionStorage.getItem(REFRESH_TOKEN_KEY),

  setTokens: (accessToken: string, refreshToken: string): void => {
    sessionStorage.setItem(TOKEN_KEY, accessToken);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  clearTokens: (): void => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isAuthenticated: (): boolean => {
    return !!sessionStorage.getItem(TOKEN_KEY);
  },
};

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = auth.getAccessToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    auth.clearTokens();
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  return response;
}

export const api = {
  checkHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },

  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Login failed');
    }
    const data: LoginResponse = await response.json();
    auth.setTokens(data.access_token, data.refresh_token);
    return data;
  },

  refreshToken: async (): Promise<boolean> => {
    const refreshToken = auth.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        auth.clearTokens();
        return false;
      }

      const data: LoginResponse = await response.json();
      auth.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      auth.clearTokens();
      return false;
    }
  },

  getMe: async (): Promise<User> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/auth/me`);
    if (!response.ok) throw new Error('Failed to fetch current user');
    return response.json();
  },

  logout: async (): Promise<void> => {
    try {
      await fetchWithAuth(`${API_BASE_URL}/auth/logout`, { method: 'POST' });
    } finally {
      auth.clearTokens();
    }
  },

  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/dashboard/summary`);
    if (!response.ok) throw new Error('Failed to fetch dashboard summary');
    return response.json();
  },

  getIncidents: async (): Promise<Incident[]> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents`);
    if (!response.ok) throw new Error('Failed to fetch incidents');
    return response.json();
  },

  createIncident: async (data: IncidentCreateRequest): Promise<Incident> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create incident');
    return response.json();
  },

  getTeams: async (): Promise<RescueTeam[]> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/teams`);
    if (!response.ok) throw new Error('Failed to fetch teams');
    return response.json();
  },

  calculatePriority: async (incidentId: number): Promise<PriorityResult> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/calculate-priority`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to calculate priority');
    return response.json();
  },

  getTeamRecommendations: async (incidentId: number): Promise<TeamRecommendation[]> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/team-recommendations`);
    if (!response.ok) throw new Error('Failed to fetch team recommendations');
    return response.json();
  },

  createAllocation: async (incidentId: number, teamId: number): Promise<Allocation> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/allocations`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/allocations`);
    if (!response.ok) throw new Error('Failed to fetch allocations');
    return response.json();
  },

  predictPriorityML: async (incidentId: number): Promise<PriorityComparisonResponse> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/predict-priority-ml`, {
      method: 'POST'
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to predict ML priority');
    }
    return response.json();
  },

  getModelInfo: async (): Promise<ModelInfo> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/ml/model-info`);
    if (!response.ok) throw new Error('Failed to fetch ML model info');
    return response.json();
  },

  searchLocations: async (query: string): Promise<GeocodingResult[]> => {
    const response = await fetch(`${API_BASE_URL}/locations/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search locations');
    return response.json();
  },

  getMapOverview: async (): Promise<MapOverviewResponse> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/map/overview`);
    if (!response.ok) throw new Error('Failed to fetch map overview');
    return response.json();
  },

  evaluateReallocation: async (incidentId: number, triggerType: string, description?: string): Promise<ReallocationRecommendationResult> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/evaluate-reallocation`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/reallocate`, {
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
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/reallocation-history`);
    if (!response.ok) throw new Error('Failed to fetch reallocation history');
    return response.json();
  },

  createRouteCondition: async (incidentId: number, data: RouteConditionCreate): Promise<any> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/route-conditions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update route condition');
    return response.json();
  },

  updateTeamStatus: async (teamId: number, status: string, reason?: string): Promise<RescueTeam> => {
    const response = await fetchWithAuth(`${API_BASE_URL}/teams/${teamId}/operational-status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ availability_status: status, reason })
    });
    if (!response.ok) throw new Error('Failed to update team operational status');
    return response.json();
  },

  getWarehouses: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/warehouses`);
    return { data: await res.json() };
  },
  getWarehouseInventory: async (id: number) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/warehouses/${id}/inventory`);
    return { data: await res.json() };
  },
  getDeliveryVehicles: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/delivery-vehicles`);
    return { data: await res.json() };
  },
  suggestReliefDemand: async (incidentId: number, days: number = 1) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/relief-demand/suggest?support_duration_days=${days}`, { method: 'POST' });
    return { data: await res.json() };
  },
  createReliefRequest: async (incidentId: number, data: any) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/relief-requests`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },
  getReliefRequests: async (incidentId: number) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/relief-requests`);
    return { data: await res.json() };
  },
  getReliefRecommendations: async (requestId: number) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/relief-requests/${requestId}/recommendations`, { method: 'POST' });
    return { data: await res.json() };
  },
  approveDispatch: async (requestId: number, data: any) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/relief-requests/${requestId}/approve-dispatch`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },
  getReliefDashboardSummary: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/relief/dashboard-summary`);
    return { data: await res.json() };
  },
  getInventoryAlerts: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/relief/inventory-alerts`);
    return { data: await res.json() };
  },

  getShelters: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/shelters`);
    return { data: await res.json() };
  },
  getShelterDashboardSummary: async () => {
    const res = await fetchWithAuth(`${API_BASE_URL}/shelter/dashboard-summary`);
    return { data: await res.json() };
  },
  createShelterRequest: async (incidentId: number, data: any) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/incidents/${incidentId}/shelter-requests`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },
  getShelterRecommendations: async (requestId: number) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/shelter-requests/${requestId}/recommendations`, { method: 'POST' });
    return { data: await res.json() };
  },
  approveShelterReservations: async (requestId: number, data: any) => {
    const res = await fetchWithAuth(`${API_BASE_URL}/shelter-requests/${requestId}/approve-reservations`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
    });
    return { data: await res.json() };
  },

  getCommandDashboardSummary: async (): Promise<CommandDashboardSummary> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/dashboard-summary`);
    if (!res.ok) throw new Error('Failed to fetch command dashboard summary');
    return res.json();
  },

  getCommandPendingDecisions: async (): Promise<PendingDecision[]> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/pending-decisions`);
    if (!res.ok) throw new Error('Failed to fetch pending decisions');
    return res.json();
  },

  getCommandAlerts: async (params?: { severity?: string; status?: string }): Promise<OperationalAlert[]> => {
    const queryParams = new URLSearchParams();
    if (params?.severity) queryParams.set('severity', params.severity);
    if (params?.status) queryParams.set('status', params.status);
    const query = queryParams.toString();
    const url = `${API_BASE_URL}/command/alerts${query ? `?${query}` : ''}`;
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  acknowledgeAlert: async (alertId: number): Promise<OperationalAlert> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/alerts/${alertId}/acknowledge`, { method: 'PATCH' });
    if (!res.ok) throw new Error('Failed to acknowledge alert');
    return res.json();
  },

  resolveAlert: async (alertId: number): Promise<OperationalAlert> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/alerts/${alertId}/resolve`, { method: 'PATCH' });
    if (!res.ok) throw new Error('Failed to resolve alert');
    return res.json();
  },

  triggerAlertGeneration: async (): Promise<{ status: string; message: string }> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/alerts/generate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger alert generation');
    return res.json();
  },

  getIncidentOperationalSummary: async (incidentId: number): Promise<IncidentOperationalSummary> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/incidents/${incidentId}/operational-summary`);
    if (!res.ok) throw new Error('Failed to fetch operational summary');
    return res.json();
  },

  getIncidentTimeline: async (incidentId: number): Promise<TimelineEvent[]> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/incidents/${incidentId}/timeline`);
    if (!res.ok) throw new Error('Failed to fetch incident timeline');
    return res.json();
  },

  getCommandMapOverview: async (): Promise<CommandMapOverview> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/command/map-overview`);
    if (!res.ok) throw new Error('Failed to fetch command map overview');
    return res.json();
  },

  getActiveIncidents: async (params?: {
    priority?: string;
    incident_type?: string;
    incident_status?: string;
    location?: string;
    rescue_status?: string;
  }): Promise<any[]> => {
    const queryParams = new URLSearchParams();
    if (params?.priority) queryParams.set('priority', params.priority);
    if (params?.incident_type) queryParams.set('incident_type', params.incident_type);
    if (params?.incident_status) queryParams.set('incident_status', params.incident_status);
    if (params?.location) queryParams.set('location', params.location);
    if (params?.rescue_status) queryParams.set('rescue_status', params.rescue_status);
    const query = queryParams.toString();
    const url = `${API_BASE_URL}/command/active-incidents${query ? `?${query}` : ''}`;
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Failed to fetch active incidents');
    return res.json();
  },

  getResourceStatus: async (params?: { resource_type?: string; status?: string }): Promise<any> => {
    const queryParams = new URLSearchParams();
    if (params?.resource_type) queryParams.set('resource_type', params.resource_type);
    if (params?.status) queryParams.set('status', params.status);
    const query = queryParams.toString();
    const url = `${API_BASE_URL}/command/resource-status${query ? `?${query}` : ''}`;
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Failed to fetch resource status');
    return res.json();
  },

  getRecentActivity: async (params?: {
    limit?: number;
    resource_type?: string;
    incident_id?: number;
  }): Promise<any[]> => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.resource_type) queryParams.set('resource_type', params.resource_type);
    if (params?.incident_id) queryParams.set('incident_id', params.incident_id.toString());
    const query = queryParams.toString();
    const url = `${API_BASE_URL}/command/recent-activity${query ? `?${query}` : ''}`;
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Failed to fetch recent activity');
    return res.json();
  },

  getEvaluationAlgorithms: async (): Promise<any[]> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/algorithms`);
    if (!res.ok) throw new Error('Failed to fetch evaluation algorithms');
    return res.json();
  },

  getEvaluationScenarios: async (module?: string): Promise<any[]> => {
    const url = `${API_BASE_URL}/evaluation/scenarios${module ? `?module=${module}` : ''}`;
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Failed to fetch evaluation scenarios');
    return res.json();
  },

  runEvaluationExperiment: async (params: {
    module: string;
    seed?: number;
    scenario_limit?: number;
    repeat_count?: number;
    algorithms?: string[];
    output_subdir?: string;
  }): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/experiments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) throw new Error('Failed to run evaluation experiment');
    return res.json();
  },

  listEvaluationExperiments: async (): Promise<any[]> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/experiments`);
    if (!res.ok) throw new Error('Failed to list experiments');
    return res.json();
  },

  getEvaluationExperiment: async (experimentId: string): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/experiments/${experimentId}`);
    if (!res.ok) throw new Error('Failed to get experiment');
    return res.json();
  },

  getExperimentResults: async (experimentId: string): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/experiments/${experimentId}/results`);
    if (!res.ok) throw new Error('Failed to get experiment results');
    return res.json();
  },

  getExperimentMetrics: async (experimentId: string): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/experiments/${experimentId}/metrics`);
    if (!res.ok) throw new Error('Failed to get experiment metrics');
    return res.json();
  },

  getPriorityModelEvaluation: async (): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/priority-model`);
    if (!res.ok) throw new Error('Failed to get priority model evaluation');
    return res.json();
  },

  getPerformanceBenchmark: async (): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/performance`);
    if (!res.ok) throw new Error('Failed to get performance benchmark');
    return res.json();
  },

  getExplainabilityCoverage: async (): Promise<any> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/explainability`);
    if (!res.ok) throw new Error('Failed to get explainability coverage');
    return res.json();
  },

  exportExperimentResults: async (experimentId: string, format: 'csv' | 'json' | 'markdown' | 'latex'): Promise<Blob> => {
    const res = await fetchWithAuth(`${API_BASE_URL}/evaluation/export/${experimentId}?format=${format}`);
    if (!res.ok) throw new Error(`Failed to export ${format}`);
    return res.blob();
  }
};