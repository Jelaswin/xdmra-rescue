import { useState, useEffect } from 'react';
import { Incident, PriorityResult, TeamRecommendation, Allocation } from '../types';
import { api } from '../services/api';

interface Props {
  incident: Incident;
  onAllocationApproved: () => void;
  onClose: () => void;
}

export default function IncidentDecisionPanel({ incident, onAllocationApproved, onClose }: Props) {
  const [priorityResult, setPriorityResult] = useState<PriorityResult | null>(null);
  const [recommendations, setRecommendations] = useState<TeamRecommendation[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  
  const [loadingPriority, setLoadingPriority] = useState(false);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [approvingTeam, setApprovingTeam] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If the incident already has priority stored, we can try to fetch it,
    // but the requirement says "Calculate Priority button".
    // We'll also fetch history.
    const loadHistory = async () => {
      try {
        const hist = await api.fetchIncidentAllocations(incident.id);
        setAllocations(hist);
        
        if (incident.priority_score !== null && incident.priority_level) {
          setPriorityResult({
            priority_score: incident.priority_score,
            priority_level: incident.priority_level,
            reasons: incident.priority_reasons || [],
            factor_breakdown: {}
          });
        }
      } catch (e) {
        console.error("Failed to load history", e);
      }
    };
    loadHistory();
  }, [incident]);

  const handleCalculatePriority = async () => {
    setLoadingPriority(true);
    setError(null);
    try {
      const res = await api.calculatePriority(incident.id);
      setPriorityResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate priority');
    } finally {
      setLoadingPriority(false);
    }
  };

  const handleGenerateRecommendations = async () => {
    setLoadingRecs(true);
    setError(null);
    try {
      const res = await api.getTeamRecommendations(incident.id);
      setRecommendations(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate recommendations');
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleApproveTeam = async (teamId: number) => {
    if (!window.confirm("Are you sure you want to approve this allocation?")) return;
    
    setApprovingTeam(teamId);
    setError(null);
    try {
      await api.createAllocation(incident.id, teamId);
      onAllocationApproved();
      // Reload history
      const hist = await api.fetchIncidentAllocations(incident.id);
      setAllocations(hist);
    } catch (err: any) {
      setError(err.message || 'Failed to allocate team');
    } finally {
      setApprovingTeam(null);
    }
  };

  const getPriorityColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-xl font-bold text-slate-800">Incident Decision Support</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Incident Info */}
            <div className="border border-slate-200 rounded-lg p-4">
              <h3 className="font-semibold text-slate-800 mb-3">Incident Information</h3>
              <div className="space-y-2 text-sm text-slate-600">
                <p><span className="font-medium text-slate-800">Title:</span> {incident.title}</p>
                <p><span className="font-medium text-slate-800">Type:</span> {incident.incident_type}</p>
                <p><span className="font-medium text-slate-800">Status:</span> 
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 capitalize">
                    {incident.status.replace('_', ' ')}
                  </span>
                </p>
                <div className="grid grid-cols-2 gap-2 mt-4">
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <p className="text-xs text-slate-500">Affected</p>
                    <p className="font-semibold text-slate-800">{incident.affected_people}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <p className="text-xs text-slate-500">Trapped</p>
                    <p className="font-semibold text-slate-800">{incident.trapped_people}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <p className="text-xs text-slate-500">Injured</p>
                    <p className="font-semibold text-slate-800">{incident.injured_people}</p>
                  </div>
                  <div className="bg-slate-50 p-2 rounded border border-slate-100">
                    <p className="text-xs text-slate-500">Vulnerable</p>
                    <p className="font-semibold text-slate-800">
                      {incident.vulnerable_people + incident.children_count + incident.elderly_count}
                    </p>
                  </div>
                </div>
                
                <div className="mt-4">
                  <p className="font-medium text-slate-800 mb-1">Required Skills:</p>
                  <div className="flex flex-wrap gap-1">
                    {incident.required_skills.length > 0 ? incident.required_skills.map(s => (
                      <span key={s} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded border border-blue-100">{s}</span>
                    )) : <span className="text-xs text-slate-400">None</span>}
                  </div>
                </div>
                <div className="mt-2">
                  <p className="font-medium text-slate-800 mb-1">Required Equipment:</p>
                  <div className="flex flex-wrap gap-1">
                    {incident.required_equipment.length > 0 ? incident.required_equipment.map(e => (
                      <span key={e} className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded border border-purple-100">{e}</span>
                    )) : <span className="text-xs text-slate-400">None</span>}
                  </div>
                </div>
              </div>
            </div>

            {/* Priority Section */}
            <div className="border border-slate-200 rounded-lg p-4 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800">Priority Engine</h3>
                <button
                  onClick={handleCalculatePriority}
                  disabled={loadingPriority || incident.status === 'resolved'}
                  className="px-3 py-1.5 bg-slate-800 text-white text-sm font-medium rounded hover:bg-slate-700 disabled:opacity-50 transition-colors"
                >
                  {loadingPriority ? 'Calculating...' : 'Calculate Priority'}
                </button>
              </div>

              {priorityResult ? (
                <div className="flex-1 flex flex-col">
                  <div className="flex items-end gap-4 mb-6 pb-6 border-b border-slate-100">
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-1">Score (0-100)</p>
                      <p className="text-4xl font-black text-slate-800">{priorityResult.priority_score}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-1">Level</p>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border capitalize ${getPriorityColor(priorityResult.priority_level)}`}>
                        {priorityResult.priority_level}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800 mb-2">Priority Reasons:</p>
                    <ul className="space-y-1">
                      {priorityResult.reasons.map((r, i) => (
                        <li key={i} className="text-sm text-slate-600 flex items-start">
                          <span className="text-brand-primary mr-2">•</span>
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
                  Click 'Calculate Priority' to analyze this incident.
                </div>
              )}
            </div>
          </div>

          {/* Allocation Section */}
          <div className="mb-8 border border-slate-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-800">Rescue Team Recommendations</h3>
              <button
                onClick={handleGenerateRecommendations}
                disabled={loadingRecs || incident.status === 'resolved'}
                className="px-4 py-2 bg-brand-primary text-white text-sm font-medium rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
              >
                {loadingRecs ? 'Generating...' : 'Generate Recommendations'}
              </button>
            </div>

            {recommendations.length > 0 ? (
              <div className="space-y-4">
                {recommendations.map(rec => (
                  <div key={rec.team_id} className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors bg-white shadow-sm">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 text-white text-xs font-bold">
                            #{rec.rank}
                          </span>
                          <h4 className="font-bold text-slate-800 text-lg">{rec.team_name}</h4>
                        </div>
                        <p className="text-sm text-slate-500">
                          Score: <span className="font-semibold text-slate-800">{rec.total_score}</span>
                          <span className="mx-2">•</span>
                          Distance: <span className="font-semibold text-slate-800">{rec.distance_km} km</span>
                        </p>
                      </div>
                      <button
                        onClick={() => handleApproveTeam(rec.team_id)}
                        disabled={approvingTeam === rec.team_id || incident.status !== 'reported' && incident.status !== 'verified'}
                        className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                      >
                        {approvingTeam === rec.team_id ? 'Approving...' : 'Approve Team'}
                      </button>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                      <div className="bg-slate-50 rounded p-2 text-center text-xs border border-slate-100">
                        <p className="text-slate-500">Skills</p>
                        <p className="font-semibold text-slate-800">{rec.skill_match_percentage}%</p>
                      </div>
                      <div className="bg-slate-50 rounded p-2 text-center text-xs border border-slate-100">
                        <p className="text-slate-500">Equipment</p>
                        <p className="font-semibold text-slate-800">{rec.equipment_match_percentage}%</p>
                      </div>
                      <div className="bg-slate-50 rounded p-2 text-center text-xs border border-slate-100">
                        <p className="text-slate-500">Capacity</p>
                        <p className="font-semibold text-slate-800">{rec.capacity_score}/10</p>
                      </div>
                      <div className="bg-slate-50 rounded p-2 text-center text-xs border border-slate-100">
                        <p className="text-slate-500">Workload</p>
                        <p className="font-semibold text-slate-800">{rec.workload_score}/10</p>
                      </div>
                    </div>

                    <div className="text-sm">
                      <p className="font-medium text-slate-800 mb-1">Explanation:</p>
                      <p className="text-slate-600 mb-2">{rec.explanation}</p>
                      
                      <div className="flex gap-4">
                        <div className="flex-1">
                          <p className="text-xs font-semibold text-emerald-700 mb-1 uppercase tracking-wider">Pros</p>
                          <ul className="text-xs text-slate-600 space-y-1">
                            {rec.positive_reasons.map((r, i) => <li key={i} className="flex"><span className="text-emerald-500 mr-1">✓</span>{r}</li>)}
                          </ul>
                        </div>
                        {rec.limitations.length > 0 && (
                          <div className="flex-1">
                            <p className="text-xs font-semibold text-red-700 mb-1 uppercase tracking-wider">Cons / Limitations</p>
                            <ul className="text-xs text-slate-600 space-y-1">
                              {rec.limitations.map((r, i) => <li key={i} className="flex"><span className="text-red-500 mr-1">!</span>{r}</li>)}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-sm">
                No recommendations generated yet or no available teams found.
              </div>
            )}
          </div>

          {/* Allocation History */}
          {allocations.length > 0 && (
            <div className="border border-slate-200 rounded-lg p-4">
              <h3 className="font-semibold text-slate-800 mb-4">Allocation History</h3>
              <div className="space-y-3">
                {allocations.map(alloc => (
                  <div key={alloc.id} className="flex items-center justify-between text-sm p-3 bg-slate-50 rounded border border-slate-100">
                    <div>
                      <p className="font-medium text-slate-800">Team ID: {alloc.rescue_team_id}</p>
                      <p className="text-xs text-slate-500">{new Date(alloc.created_at).toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-slate-800 capitalize">{alloc.status}</p>
                      <p className="text-xs text-slate-500">Score: {alloc.recommendation_score}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
