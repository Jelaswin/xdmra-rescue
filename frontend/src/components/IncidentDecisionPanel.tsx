import { useState, useEffect } from 'react';
import { Incident, PriorityResult, TeamRecommendation, Allocation, PriorityComparisonResponse } from '../types';
import { api } from '../services/api';
import { ReallocationRecommendationResult, ReallocationEventResponse, ReliefRequest, ReliefDemandSuggestion, ReliefAllocationEvaluation, ReliefRecommendation, SplitAllocationPlan } from '../types';

interface Props {
  incident: Incident;
  onAllocationApproved: () => void;
  onClose: () => void;
}

export default function IncidentDecisionPanel({ incident, onAllocationApproved, onClose }: Props) {
  const [priorityResult, setPriorityResult] = useState<PriorityResult | null>(null);
  const [mlComparison, setMlComparison] = useState<PriorityComparisonResponse | null>(null);
  const [recommendations, setRecommendations] = useState<TeamRecommendation[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [reallocationEval, setReallocationEval] = useState<ReallocationRecommendationResult | null>(null);
  const [reallocationHistory, setReallocationHistory] = useState<ReallocationEventResponse[]>([]);
  const [simTriggerType, setSimTriggerType] = useState('route_blocked');
  const [simReason, setSimReason] = useState('Route blocked by debris');

  const [activeSubTab, setActiveSubTab] = useState<'rescue' | 'relief'>('rescue');
  const [reliefRequest, setReliefRequest] = useState<ReliefRequest | null>(null);
  const [demandSuggestion, setDemandSuggestion] = useState<ReliefDemandSuggestion | null>(null);
  const [reliefEval, setReliefEval] = useState<ReliefAllocationEvaluation | null>(null);
  const [loadingRelief, setLoadingRelief] = useState(false);
  const [reliefItems, setReliefItems] = useState<any[]>([]);

  
  const [loadingPriority, setLoadingPriority] = useState(false);
  const [loadingMl, setLoadingMl] = useState(false);
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
        
        try {
          const reallocs = await api.getReallocationHistory(incident.id);
          setReallocationHistory(reallocs);
        } catch (e) {
          console.error("Failed to load reallocation history", e);
        }

        try {
          const reqs = await api.getReliefRequests(incident.id);
          if (reqs.data.length > 0) {
            setReliefRequest(reqs.data[0]);
            // Format items for the UI
            setReliefItems(reqs.data[0].items.map((i: any) => ({
              item_type: i.item_type,
              quantity: i.approved_quantity,
              unit: i.unit || 'units',
              reason: i.calculation_reason,
              source_type: i.source_type
            })));
          }
        } catch(e) { console.error(e); }

        
        if (incident.priority_score !== null && incident.priority_level) {
          setPriorityResult({
            priority_score: incident.priority_score,
            priority_level: incident.priority_level,
            reasons: incident.priority_reasons || [],
            factor_breakdown: {}
          });
        }
        
        if (incident.ml_priority_level && incident.priority_agreement_status) {
          setMlComparison({
            rule_priority: incident.priority_level || '',
            rule_score: incident.priority_score || 0,
            ml_priority: incident.ml_priority_level,
            ml_confidence: incident.ml_priority_confidence || 0,
            agreement_status: incident.priority_agreement_status,
            requires_officer_review: incident.requires_priority_review,
            comparison_message: ''
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

  const handlePredictMl = async () => {
    setLoadingMl(true);
    setError(null);
    try {
      const res = await api.predictPriorityML(incident.id);
      setMlComparison(res);
      // Ensure rule-based is also showing since ML fetches it
      setPriorityResult({
        priority_score: res.rule_score,
        priority_level: res.rule_priority,
        reasons: incident.priority_reasons || [],
        factor_breakdown: {}
      });
    } catch (err: any) {
      setError(err.message || 'Failed to predict ML priority');
    } finally {
      setLoadingMl(false);
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
    if (mlComparison?.requires_officer_review) {
      if (!window.confirm("WARNING: The ML model strongly disagrees with the predefined priority. Are you sure you want to proceed with this allocation?")) return;
    } else {
      if (!window.confirm("Are you sure you want to approve this allocation?")) return;
    }
    
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

  const handleSimulateUpdate = async () => {
    setError(null);
    try {
      const activeAlloc = allocations.find(a => a.status === 'approved' || a.status === 'dispatched');
      if (!activeAlloc) throw new Error("No active allocation found to simulate update on.");
      
      if (simTriggerType === 'route_blocked') {
        await api.createRouteCondition(incident.id, {
          rescue_team_id: activeAlloc.rescue_team_id,
          risk_level: 'high',
          is_blocked: true,
          estimated_delay_minutes: 30,
          description: simReason
        });
      } else {
        await api.updateTeamStatus(activeAlloc.rescue_team_id, 'unavailable', simReason);
      }
      
      const evalRes = await api.evaluateReallocation(incident.id, simTriggerType, simReason);
      setReallocationEval(evalRes);
      
    } catch (e: any) {
      setError(e.message || "Failed to simulate operational update");
    }
  };

  const handleApproveReallocation = async () => {
    if (!reallocationEval?.recommended_replacement) return;
    setError(null);
    try {
      await api.approveReallocation(incident.id, reallocationEval.recommended_replacement.team_id, reallocationEval.trigger_type, reallocationEval.reason);
      onAllocationApproved(); 
      const hist = await api.fetchIncidentAllocations(incident.id);
      setAllocations(hist);
      const reallocs = await api.getReallocationHistory(incident.id);
      setReallocationHistory(reallocs);
      setReallocationEval(null); 
    } catch (e: any) {
       setError(e.message || "Failed to approve reallocation");
    }
  };



  const handleSuggestDemand = async () => {
    setLoadingRelief(true);
    try {
      const res = await api.suggestReliefDemand(incident.id, 2); // 2 days support
      setDemandSuggestion(res.data);
      setReliefItems(res.data.suggested_items.map((i: any) => ({...i, source_type: 'system_suggested'})));
    } catch(e: any) { setError(e.message); }
    setLoadingRelief(false);
  };

  const handleConfirmRequest = async () => {
    setLoadingRelief(true);
    try {
      const payload = {
        support_duration_days: demandSuggestion?.support_duration_days || 2,
        total_people: incident.affected_people,
        items: reliefItems.map(i => ({
          item_type: i.item_type,
          requested_quantity: i.quantity,
          source_type: i.source_type,
          calculation_reason: i.reason
        }))
      };
      const res = await api.createReliefRequest(incident.id, payload);
      setReliefRequest(res.data);
    } catch(e: any) { setError(e.message); }
    setLoadingRelief(false);
  };

  const handleGetReliefRecs = async () => {
    if (!reliefRequest) return;
    setLoadingRelief(true);
    try {
      const res = await api.getReliefRecommendations(reliefRequest.id);
      setReliefEval(res.data);
    } catch(e: any) { setError(e.message); }
    setLoadingRelief(false);
  };

  const handleApproveRelief = async (warehouseId: number, isSplit: boolean = false) => {
    if (!reliefRequest) return;
    if (!window.confirm("Approve this relief allocation?")) return;
    setLoadingRelief(true);
    try {
      if (!isSplit) {
        // Single source
        const rec = reliefEval?.single_source_recommendations.find(r => r.warehouse_id === warehouseId);
        const payload = {
          warehouse_id: warehouseId,
          items: reliefItems.filter(i => rec?.covered_items.includes(i.item_type)).map(i => ({
            inventory_id: 0, // Backend resolves it for now or we ignore it in this mock
            item_type: i.item_type,
            allocated_quantity: i.quantity,
            unit: i.unit
          })),
          recommendation_score: rec?.total_score,
          explanation: rec?.explanation
        };
        await api.approveDispatch(reliefRequest.id, payload);
      } else {
        // Split source
        for (const wh of reliefEval!.split_allocation_plan!.warehouses_involved) {
           const payload = {
            warehouse_id: wh.warehouse_id,
            items: Object.keys(wh.provided_items).map(item_type => ({
              inventory_id: 0, 
              item_type,
              allocated_quantity: wh.provided_items[item_type],
              unit: 'units'
            })),
            explanation: wh.explanation
          };
          await api.approveDispatch(reliefRequest.id, payload);
        }
      }
      alert("Dispatch Approved Successfully!");
      onAllocationApproved();
    } catch(e: any) { setError(e.message); }
    setLoadingRelief(false);
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


        <div className="flex px-6 bg-slate-50 border-b border-slate-200 gap-4 pt-2">
           <button onClick={() => setActiveSubTab('rescue')} className={`px-4 py-2 font-bold text-sm ${activeSubTab === 'rescue' ? 'border-b-2 border-blue-600 text-blue-700' : 'text-slate-500 hover:text-slate-700'}`}>Rescue Allocation</button>
           <button onClick={() => setActiveSubTab('relief')} className={`px-4 py-2 font-bold text-sm ${activeSubTab === 'relief' ? 'border-b-2 border-purple-600 text-purple-700' : 'text-slate-500 hover:text-slate-700'}`}>Relief Supply</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          {activeSubTab === 'rescue' ? (
          <>
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
                
                <div className="mt-3 p-3 bg-slate-50 border border-slate-100 rounded">
                  <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Location Details</p>
                  <p><span className="font-medium text-slate-800">Coordinates:</span> {incident.latitude.toFixed(4)}, {incident.longitude.toFixed(4)}</p>
                  {incident.location_name && <p><span className="font-medium text-slate-800">Area/Name:</span> {incident.location_name}</p>}
                  {incident.location_accuracy && <p><span className="font-medium text-slate-800">Accuracy:</span> <span className="capitalize">{incident.location_accuracy.replace('_', ' ')}</span></p>}
                  {incident.location_source && <p><span className="font-medium text-slate-800">Source:</span> <span className="capitalize">{incident.location_source.replace('_', ' ')}</span></p>}
                </div>
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
            <div className="flex flex-col gap-4">
              {/* Predefined Engine */}
              <div className="border border-slate-200 rounded-lg p-4 flex flex-col bg-white">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-800">Predefined Priority Engine</h3>
                  <button
                    onClick={handleCalculatePriority}
                    disabled={loadingPriority || incident.status === 'resolved'}
                    className="px-3 py-1.5 bg-slate-800 text-white text-sm font-medium rounded hover:bg-slate-700 disabled:opacity-50 transition-colors"
                  >
                    {loadingPriority ? 'Calculating...' : 'Calculate'}
                  </button>
                </div>

                {priorityResult ? (
                  <div className="flex-1 flex flex-col">
                    <div className="flex items-end gap-4 mb-4 pb-4 border-b border-slate-100">
                      <div>
                        <p className="text-xs text-slate-500 font-medium mb-1">Score (0-100)</p>
                        <p className="text-3xl font-black text-slate-800">{priorityResult.priority_score}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 font-medium mb-1">Level</p>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border capitalize ${getPriorityColor(priorityResult.priority_level)}`}>
                          {priorityResult.priority_level}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-4">
                    Click 'Calculate' to run predefined rules.
                  </div>
                )}
              </div>

              {/* ML Engine */}
              <div className="border border-slate-200 rounded-lg p-4 flex flex-col bg-slate-50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                    Machine-Learning Prediction
                  </h3>
                  <button
                    onClick={handlePredictMl}
                    disabled={loadingMl || incident.status === 'resolved'}
                    className="px-3 py-1.5 bg-purple-600 text-white text-sm font-medium rounded hover:bg-purple-700 disabled:opacity-50 transition-colors shadow-sm"
                  >
                    {loadingMl ? 'Predicting...' : 'Predict with ML'}
                  </button>
                </div>

                {mlComparison ? (
                  <div className="flex-1 flex flex-col">
                    <div className="flex items-end gap-4 mb-4 pb-4 border-b border-slate-200">
                      <div>
                        <p className="text-xs text-slate-500 font-medium mb-1">Confidence</p>
                        <p className="text-3xl font-black text-purple-700">{Math.round(mlComparison.ml_confidence * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 font-medium mb-1">Predicted Level</p>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border capitalize ${getPriorityColor(mlComparison.ml_priority)}`}>
                          {mlComparison.ml_priority}
                        </span>
                      </div>
                    </div>

                    <div className="mt-2">
                      {mlComparison.agreement_status === 'agreement' ? (
                        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-md text-sm">
                          <p className="font-semibold flex items-center gap-2">
                            <span>✓</span> Agreement
                          </p>
                          <p className="text-xs mt-1 text-emerald-600">The ML model agrees with the rule-based priority.</p>
                        </div>
                      ) : mlComparison.agreement_status === 'minor_disagreement' ? (
                        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-3 rounded-md text-sm">
                          <p className="font-semibold flex items-center gap-2">
                            <span>⚠</span> Minor Disagreement
                          </p>
                          <p className="text-xs mt-1 text-yellow-700">{mlComparison.comparison_message || 'Officer review is required before allocation.'}</p>
                        </div>
                      ) : (
                        <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded-md text-sm">
                          <p className="font-semibold flex items-center gap-2">
                            <span>!</span> Major Disagreement
                          </p>
                          <p className="text-xs mt-1 text-red-700">{mlComparison.comparison_message || 'Officer review is strongly required.'}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-4">
                    Click 'Predict' to run ML model.
                  </div>
                )}
              </div>
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

          {/* Dynamic Reallocation / Simulation Section */}
          {(allocations.some(a => a.status === 'approved' || a.status === 'dispatched')) && incident.status !== 'resolved' && (
            <div className="mb-8 border border-slate-200 rounded-lg p-4 bg-orange-50">
              <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                Operational Update & Reallocation
              </h3>
              
              <div className="flex gap-4 mb-4">
                <select 
                  value={simTriggerType} 
                  onChange={e => setSimTriggerType(e.target.value)}
                  className="px-3 py-2 border rounded-md text-sm"
                >
                  <option value="route_blocked">Route Blocked</option>
                  <option value="team_unavailable">Team Unavailable/Breakdown</option>
                  <option value="increased_workload">Increased Workload</option>
                </select>
                <input 
                  type="text" 
                  value={simReason}
                  onChange={e => setSimReason(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md text-sm"
                  placeholder="Reason (e.g. Debris on road)"
                />
                <button
                  onClick={handleSimulateUpdate}
                  className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded hover:bg-orange-700 transition-colors"
                >
                  Simulate Update & Evaluate
                </button>
              </div>

              {reallocationEval && (
                <div className="bg-white p-4 rounded-md border border-orange-200 shadow-sm">
                  <h4 className="font-semibold text-slate-800 mb-2">Reallocation Proposal</h4>
                  <p className="text-sm text-slate-700 mb-4">{reallocationEval.explanation}</p>
                  
                  {reallocationEval.recommended_replacement ? (
                    <div className="flex items-center justify-between bg-orange-50 p-3 rounded border border-orange-100">
                      <div>
                        <p className="font-bold text-slate-800">Recommend Replacement: {reallocationEval.recommended_replacement.team_name}</p>
                        <p className="text-xs text-slate-600">Score: {reallocationEval.recommended_replacement.score} | Distance: {reallocationEval.recommended_replacement.distance_km} km</p>
                      </div>
                      <button
                        onClick={handleApproveReallocation}
                        className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded hover:bg-emerald-700"
                      >
                        Approve Reallocation
                      </button>
                    </div>
                  ) : (
                    <div className="text-sm text-red-600 font-medium">
                      No available replacements found!
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Allocation History */}
            <div className="border border-slate-200 rounded-lg p-4 mb-8">
              <h3 className="font-semibold text-slate-800 mb-4">Allocation Timeline</h3>
              <div className="space-y-3 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                {allocations.map((alloc, i) => (
                  <div key={alloc.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-100 group-[.is-active]:bg-blue-500 text-slate-500 group-[.is-active]:text-emerald-50 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                      <span className="text-xs">{i+1}</span>
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-slate-200 bg-white shadow-sm">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-bold text-slate-800 capitalize">Team {alloc.rescue_team_id} {alloc.status}</div>
                        <time className="text-xs text-slate-500">{new Date(alloc.created_at).toLocaleTimeString()}</time>
                      </div>
                      <div className="text-xs text-slate-600">
                        {alloc.status === 'superseded' && alloc.termination_reason && (
                          <span className="text-red-600">Failed: {alloc.termination_reason}</span>
                        )}
                        {alloc.explanation && <p className="mt-1">{alloc.explanation}</p>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>


          </>
          ) : (
          <div className="space-y-6">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-bold text-purple-800 mb-2">Relief Demand Suggestion</h3>
              {!demandSuggestion && !reliefRequest ? (
                <div className="text-center py-4">
                  <p className="text-sm text-purple-600 mb-3">Calculate estimated relief supplies required based on affected population.</p>
                  <button onClick={handleSuggestDemand} disabled={loadingRelief} className="px-4 py-2 bg-purple-600 text-white rounded font-medium text-sm hover:bg-purple-700">
                    {loadingRelief ? 'Calculating...' : 'Generate Demand'}
                  </button>
                </div>
              ) : (
                <div>
                  <table className="w-full text-sm text-left mb-4 bg-white rounded">
                    <thead className="bg-purple-100 text-purple-800">
                      <tr>
                        <th className="p-2">Item</th>
                        <th className="p-2">Quantity</th>
                        <th className="p-2">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reliefItems.map((item, idx) => (
                        <tr key={idx} className="border-b">
                          <td className="p-2 font-medium">{item.item_type.replace(/_/g, ' ')}</td>
                          <td className="p-2">
                            <input 
                              type="number" 
                              value={item.quantity} 
                              disabled={!!reliefRequest}
                              onChange={(e) => {
                                const newItems = [...reliefItems];
                                newItems[idx].quantity = parseInt(e.target.value);
                                newItems[idx].source_type = 'officer_modified';
                                setReliefItems(newItems);
                              }}
                              className="w-20 border rounded p-1" 
                            /> {item.unit}
                            {item.source_type === 'officer_modified' && <span className="text-xs text-orange-600 block">Modified</span>}
                          </td>
                          <td className="p-2 text-xs text-gray-600">{item.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!reliefRequest && (
                    <button onClick={handleConfirmRequest} disabled={loadingRelief} className="px-4 py-2 bg-purple-600 text-white rounded font-medium text-sm hover:bg-purple-700">
                      Confirm Relief Request
                    </button>
                  )}
                  {reliefRequest && (
                    <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold">Request Confirmed</span>
                  )}
                </div>
              )}
            </div>

            {reliefRequest && (
              <div className="border border-slate-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-slate-800">Warehouse Recommendations</h3>
                  <button onClick={handleGetReliefRecs} disabled={loadingRelief} className="px-4 py-2 bg-brand-primary text-white text-sm rounded hover:bg-blue-600">
                    Generate Warehouse Options
                  </button>
                </div>

                {reliefEval && (
                  <div className="space-y-6">
                    {/* Split Allocation Plan */}
                    {reliefEval.split_allocation_plan && (
                       <div className="bg-orange-50 border border-orange-200 rounded p-4">
                         <h4 className="font-bold text-orange-800 mb-2">Recommended: Split Allocation Plan</h4>
                         <p className="text-sm mb-3">{reliefEval.split_allocation_plan.explanation}</p>
                         <div className="space-y-2 mb-4">
                           {reliefEval.split_allocation_plan.warehouses_involved.map(w => (
                             <div key={w.warehouse_id} className="bg-white p-2 rounded shadow-sm text-sm">
                               <strong>{w.warehouse_name}</strong> (Distance: {w.distance_km}km) <br/>
                               Provides: {Object.entries(w.provided_items).map(([k,v]) => `${k} (${v})`).join(', ')}
                             </div>
                           ))}
                         </div>
                         <button onClick={() => handleApproveRelief(0, true)} disabled={loadingRelief} className="px-4 py-2 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 font-bold">
                           Approve Split Plan
                         </button>
                       </div>
                    )}

                    {/* Single Sources */}
                    <div>
                      <h4 className="font-bold text-slate-700 mb-3">Single-Source Alternatives</h4>
                      <div className="grid gap-4">
                        {reliefEval.single_source_recommendations.map(rec => (
                          <div key={rec.warehouse_id} className="border border-slate-200 p-3 rounded">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h5 className="font-bold">#{rec.rank} {rec.warehouse_name}</h5>
                                <p className="text-xs text-slate-600">Score: {rec.total_score} | Coverage: {rec.stock_coverage_percentage}% | Distance: {rec.distance_km}km</p>
                              </div>
                              <button onClick={() => handleApproveRelief(rec.warehouse_id, false)} disabled={loadingRelief} className="px-3 py-1 bg-emerald-600 text-white text-xs rounded font-bold hover:bg-emerald-700">
                                Approve
                              </button>
                            </div>
                            <p className="text-xs text-slate-700 mb-1"><strong>Reasoning:</strong> {rec.explanation}</p>
                            <div className="text-xs">
                              <span className="text-emerald-600 block">Pros: {rec.positive_reasons.join(', ')}</span>
                              {rec.limitations.length > 0 && <span className="text-red-600 block">Cons: {rec.limitations.join(', ')}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          )}

        </div>
      </div>
    </div>
  );
}
