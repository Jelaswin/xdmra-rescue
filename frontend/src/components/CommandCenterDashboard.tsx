import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { CommandDashboardSummary, PendingDecision, OperationalAlert, IncidentOperationalSummary, TimelineEvent, CommandMapOverview, MapIncident, MapTeam, Warehouse, EmergencyShelter } from '../types';
import { OperationsMap } from './map/OperationsMap';

type TabSection = 'overview' | 'incidents' | 'decisions' | 'alerts' | 'activity' | 'command';

export function CommandCenterDashboard() {
  const [summary, setSummary] = useState<CommandDashboardSummary | null>(null);
  const [pendingDecisions, setPendingDecisions] = useState<PendingDecision[]>([]);
  const [alerts, setAlerts] = useState<OperationalAlert[]>([]);
  const [activeSection, setActiveSection] = useState<TabSection>('overview');
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null);
  const [incidentSummary, setIncidentSummary] = useState<IncidentOperationalSummary | null>(null);
  const [incidentTimeline, setIncidentTimeline] = useState<TimelineEvent[]>([]);
  const [mapOverview, setMapOverview] = useState<CommandMapOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const filterSeverity = useState<string>('')[0];
  const filterStatus = useState<string>('')[0];
  const filterPriority = useState<string>('')[0];

  const fetchAllData = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError(null);
    try {
      const [sumData, decisionsData, alertsData, mapData] = await Promise.all([
        api.getCommandDashboardSummary(),
        api.getCommandPendingDecisions(),
        api.getCommandAlerts(),
        api.getCommandMapOverview()
      ]);
      setSummary(sumData);
      setPendingDecisions(decisionsData);
      setAlerts(alertsData);
      setMapOverview(mapData);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to fetch command data');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(() => {
      fetchAllData(false);
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchAllData(false);
  };

  const handleAlertAcknowledge = async (alertId: number) => {
    try {
      await api.acknowledgeAlert(alertId);
      fetchAllData(false);
    } catch (err: any) {
      setError(err.message || 'Failed to acknowledge alert');
    }
  };

  const handleAlertResolve = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      fetchAllData(false);
    } catch (err: any) {
      setError(err.message || 'Failed to resolve alert');
    }
  };

  const handleSelectIncident = async (incidentId: number) => {
    setSelectedIncidentId(incidentId);
    try {
      const [summaryData, timelineData] = await Promise.all([
        api.getIncidentOperationalSummary(incidentId),
        api.getIncidentTimeline(incidentId)
      ]);
      setIncidentSummary(summaryData);
      setIncidentTimeline(timelineData);
      setActiveSection('command');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch incident details');
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-600 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'warning': return 'bg-yellow-500 text-white';
      case 'info': return 'bg-blue-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Command Center...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
        <strong>Error:</strong> {error}
        <button onClick={handleRefresh} className="ml-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">Emergency Command Center</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Last updated: {lastRefresh.toLocaleTimeString()} (Auto-refresh: 60s)
          </span>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <SummaryCard label="Active Incidents" value={summary?.total_active_incidents ?? 0} color="blue" />
        <SummaryCard label="Critical" value={summary?.critical_incidents ?? 0} color="red" />
        <SummaryCard label="Unassigned" value={summary?.unassigned_incidents ?? 0} color="orange" />
        <SummaryCard label="Rescue Deployments" value={summary?.active_rescue_allocations ?? 0} color="green" />
        <SummaryCard label="Reallocation Pending" value={summary?.rescue_reallocations_pending ?? 0} color="yellow" />
        <SummaryCard label="Pending Decisions" value={summary?.pending_officer_decisions ?? 0} color="purple" />
        <SummaryCard label="Active Relief" value={summary?.active_relief_requests ?? 0} color="teal" />
        <SummaryCard label="Relief Shortages" value={summary?.relief_shortages ?? 0} color="red" />
        <SummaryCard label="Dispatches" value={(summary?.dispatches_in_transit ?? 0) + (summary?.dispatches_preparing ?? 0)} color="cyan" />
        <SummaryCard label="Shelter Requests" value={summary?.active_shelter_requests ?? 0} color="indigo" />
        <SummaryCard label="Uncovered" value={summary?.uncovered_displaced_people ?? 0} color="pink" />
        <SummaryCard label="Overcrowding Risk" value={summary?.high_overcrowding_risk_shelters ?? 0} color="red" />
      </div>

      <div className="flex gap-2 border-b pb-2">
        <TabButton active={activeSection === 'overview'} onClick={() => setActiveSection('overview')}>Overview</TabButton>
        <TabButton active={activeSection === 'incidents'} onClick={() => setActiveSection('incidents')}>Incidents</TabButton>
        <TabButton active={activeSection === 'decisions'} onClick={() => setActiveSection('decisions')}>Decisions</TabButton>
        <TabButton active={activeSection === 'alerts'} onClick={() => setActiveSection('alerts')}>Alerts</TabButton>
        <TabButton active={activeSection === 'activity'} onClick={() => setActiveSection('activity')}>Activity</TabButton>
        <TabButton active={activeSection === 'command'} onClick={() => setActiveSection('command')}>Command View</TabButton>
      </div>

      {activeSection === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold text-lg mb-4">Command Map</h3>
            <div className="h-[400px] border rounded">
              {mapOverview && (
                <OperationsMap
                  incidents={mapOverview.incidents}
                  teams={mapOverview.teams}
                  warehouses={mapOverview.warehouses}
                  shelters={mapOverview.shelters}
                />
              )}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold text-lg mb-4">Pending Decisions</h3>
            {pendingDecisions.length === 0 ? (
              <p className="text-gray-500">No pending decisions</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {pendingDecisions.slice(0, 10).map((d) => (
                  <div key={d.id} className="p-3 border rounded hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(d.severity)}`}>{d.severity}</span>
                        <span className={`ml-2 px-2 py-1 text-xs rounded ${getPriorityColor(d.priority)}`}>{d.priority}</span>
                      </div>
                      <span className="text-sm text-gray-500">{formatDuration(d.waiting_duration_minutes)}</span>
                    </div>
                    <p className="mt-1 font-medium">{d.incident_title}</p>
                    <p className="text-sm text-gray-600">{d.reason}</p>
                    <button
                      onClick={() => handleSelectIncident(d.incident_id)}
                      className="mt-2 text-sm text-blue-600 hover:underline"
                    >
                      Open Decision
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeSection === 'incidents' && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-4">Priority Incidents</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Title</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Priority</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Waiting</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pendingDecisions.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">{d.incident_title}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(d.priority)}`}>{d.priority}</span>
                    </td>
                    <td className="px-4 py-2">{d.decision_type}</td>
                    <td className="px-4 py-2">{formatDuration(d.waiting_duration_minutes)}</td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => handleSelectIncident(d.incident_id)}
                        className="text-blue-600 hover:underline text-sm"
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeSection === 'decisions' && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-4">Pending Officer Decisions</h3>
          {pendingDecisions.length === 0 ? (
            <p className="text-gray-500">No pending decisions</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pendingDecisions.map((d) => (
                <div key={d.id} className="border rounded-lg p-4 hover:shadow-md">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex gap-2">
                      <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(d.severity)}`}>{d.severity}</span>
                      <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(d.priority)}`}>{d.priority}</span>
                    </div>
                    <span className="text-sm text-gray-500">{formatDuration(d.waiting_duration_minutes)}</span>
                  </div>
                  <h4 className="font-medium">{d.incident_title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{d.reason}</p>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => handleSelectIncident(d.incident_id)}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      Open Decision
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeSection === 'alerts' && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-4">Operational Alerts</h3>
          <div className="mb-4 flex gap-4">
            <select className="border rounded px-3 py-2">
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
            <select className="border rounded px-3 py-2">
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
          {alerts.length === 0 ? (
            <p className="text-gray-500">No active alerts</p>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex gap-2">
                      <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(alert.severity)}`}>{alert.severity}</span>
                      <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">{alert.category}</span>
                      <span className={`px-2 py-1 text-xs rounded ${alert.status === 'active' ? 'bg-green-100 text-green-700' : alert.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'}`}>{alert.status}</span>
                    </div>
                    <span className="text-sm text-gray-500">{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                  <h4 className="font-medium mt-2">{alert.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  {alert.recommended_action && (
                    <p className="text-sm text-blue-600 mt-2">Recommended action: {alert.recommended_action}</p>
                  )}
                  <div className="mt-3 flex gap-2">
                    {alert.status === 'active' && (
                      <button
                        onClick={() => handleAlertAcknowledge(alert.id)}
                        className="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600"
                      >
                        Acknowledge
                      </button>
                    )}
                    {alert.status === 'acknowledged' && (
                      <button
                        onClick={() => handleAlertResolve(alert.id)}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeSection === 'activity' && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold text-lg mb-4">Recent Activity</h3>
          <div className="space-y-2">
            {incidentTimeline.length === 0 ? (
              <p className="text-gray-500">Select an incident to view activity timeline</p>
            ) : (
              incidentTimeline.map((event, idx) => (
                <div key={event.id} className="flex gap-4 p-3 border-b last:border-0">
                  <div className="w-2 h-2 mt-2 rounded-full bg-blue-500"></div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span className="font-medium">{event.title}</span>
                      <span className="text-sm text-gray-500">{new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-gray-600">{event.description}</p>
                    <span className="text-xs text-gray-400">{event.event_category} | {event.source}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeSection === 'command' && selectedIncidentId && incidentSummary && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold">{incidentSummary.title}</h3>
                <p className="text-gray-600">{incidentSummary.incident_type} - {incidentSummary.location}</p>
              </div>
              <button onClick={() => setActiveSection('overview')} className="text-gray-500 hover:text-gray-700">
                Close
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className={`p-3 rounded ${getPriorityColor(incidentSummary.rule_priority)}`}>
                <span className="text-xs">Rule Priority</span>
                <p className="font-bold">{incidentSummary.rule_priority}</p>
              </div>
              {incidentSummary.ml_priority && (
                <div className={`p-3 rounded ${getPriorityColor(incidentSummary.ml_priority)}`}>
                  <span className="text-xs">ML Priority</span>
                  <p className="font-bold">{incidentSummary.ml_priority}</p>
                </div>
              )}
              <div className="p-3 rounded bg-gray-100">
                <span className="text-xs">Status</span>
                <p className="font-bold">{incidentSummary.current_status}</p>
              </div>
              <div className="p-3 rounded bg-gray-100">
                <span className="text-xs">Waiting</span>
                <p className="font-bold">{formatDuration(incidentSummary.waiting_duration_minutes)}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded p-3">
                <h4 className="font-medium mb-2">Rescue</h4>
                <p>Assigned: {incidentSummary.assigned_team || 'None'}</p>
                <p>Status: {incidentSummary.allocation_status || 'N/A'}</p>
              </div>
              <div className="border rounded p-3">
                <h4 className="font-medium mb-2">Relief</h4>
                <p>Status: {incidentSummary.relief_request_status || 'None'}</p>
                <p>Dispatches: {incidentSummary.active_dispatches}</p>
              </div>
              <div className="border rounded p-3">
                <h4 className="font-medium mb-2">Shelter</h4>
                <p>Status: {incidentSummary.shelter_request_status || 'None'}</p>
                <p>Displaced: {incidentSummary.displaced_population}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="font-semibold text-lg mb-4">Unified Timeline</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {incidentTimeline.map((event) => (
                <div key={event.id} className="flex gap-4 p-3 border-b last:border-0">
                  <div className="w-2 h-2 mt-2 rounded-full bg-blue-500"></div>
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span className="font-medium">{event.title}</span>
                      <span className="text-sm text-gray-500">{new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-gray-600">{event.description}</p>
                    {event.explanation && <p className="text-sm text-blue-600 mt-1">{event.explanation}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    red: 'bg-red-50 border-red-200 text-red-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
    teal: 'bg-teal-50 border-teal-200 text-teal-800',
    pink: 'bg-pink-50 border-pink-200 text-pink-800',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-800',
    cyan: 'bg-cyan-50 border-cyan-200 text-cyan-800',
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color as keyof typeof colorClasses] || colorClasses.blue}`}>
      <p className="text-sm opacity-75">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 font-medium rounded-t ${
        active ? 'bg-white border-t-2 border-x border-gray-200 text-blue-600' : 'text-gray-600 hover:text-gray-800'
      }`}
    >
      {children}
    </button>
  );
}