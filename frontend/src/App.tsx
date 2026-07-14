import { useEffect, useState } from 'react';
import { api } from './services/api';
import { DashboardSummary, Incident, RescueTeam } from './types';
import DashboardCards from './components/DashboardCards';
import IncidentList from './components/IncidentList';
import TeamList from './components/TeamList';
import IncidentForm from './components/IncidentForm';
import IncidentDecisionPanel from './components/IncidentDecisionPanel';
import { OperationsMap } from './components/map/OperationsMap';

function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [teams, setTeams] = useState<RescueTeam[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setBackendStatus('checking');
      await api.checkHealth();
      setBackendStatus('connected');
      
      const [sumData, incData, teamData] = await Promise.all([
        api.getDashboardSummary(),
        api.getIncidents(),
        api.getTeams()
      ]);
      
      setSummary(sumData);
      setIncidents(incData);
      setTeams(teamData);
      setError(null);
    } catch (err: any) {
      setBackendStatus('error');
      setError(err.message || 'Failed to connect to backend.');
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleIncidentCreated = () => {
    fetchData(); // Refresh all data when a new incident is created
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-brand-dark text-white p-4 shadow-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">X-DMRA Rescue</h1>
            <p className="text-sm text-slate-400">An Explainable Dynamic Rescue-Team Allocation System for Disaster Response</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Backend:</span>
            {backendStatus === 'checking' && <span className="text-yellow-400 text-sm">Checking...</span>}
            {backendStatus === 'connected' && <span className="text-emerald-400 text-sm flex items-center"><span className="w-2 h-2 rounded-full bg-emerald-400 mr-2"></span> Connected</span>}
            {backendStatus === 'error' && <span className="text-red-400 text-sm flex items-center"><span className="w-2 h-2 rounded-full bg-red-400 mr-2"></span> Error</span>}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-6 space-y-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
            <strong>Error:</strong> {error}
          </div>
        )}

        <section>
          <h2 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Operational Dashboard</h2>
          <DashboardCards summary={summary} />
          
          <div className="mt-6 h-[400px] border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <OperationsMap incidents={incidents} teams={teams} />
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <section>
              <h2 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Active Incidents</h2>
              <IncidentList incidents={incidents} onIncidentSelect={setSelectedIncident} />
            </section>

            <section>
              <h2 className="text-xl font-semibold mb-4 text-slate-800 border-b pb-2">Rescue Teams</h2>
              <TeamList teams={teams} />
            </section>
          </div>

          <div className="lg:col-span-1">
            <section className="sticky top-24">
              <IncidentForm onIncidentCreated={handleIncidentCreated} />
            </section>
          </div>
        </div>
      </main>

      {selectedIncident && (
        <IncidentDecisionPanel
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onAllocationApproved={() => {
            fetchData();
          }}
        />
      )}
    </div>
  );
}

export default App;
