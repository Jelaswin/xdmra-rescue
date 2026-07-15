import React, { useState, useEffect } from 'react';
import { Incident, ShelterRequest, ShelterAllocationEvaluationResponse, ShelterReservation } from '../types';
import { api } from '../services/api';

interface Props {
  incident: Incident;
  onAllocationApproved: () => void;
}

export const IncidentShelterPanel: React.FC<Props> = ({ incident, onAllocationApproved }) => {
  const [request, setRequest] = useState<ShelterRequest | null>(null);
  const [evaluation, setEvaluation] = useState<ShelterAllocationEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [peopleCount, setPeopleCount] = useState(incident.affected_people);
  const [medReq, setMedReq] = useState(incident.injured_people);
  const [accReq, setAccReq] = useState(incident.elderly_count);
  const [safeReq, setSafeReq] = useState(incident.children_count);

  useEffect(() => {
    // Attempt to load existing request
    // We don't have a specific endpoint for get_shelter_requests by incident in the API client yet,
    // wait, we can just let them create one, or we can assume no request exists until created for simplicity
    // in this prototype.
  }, [incident]);

  const handleCreateRequest = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        total_displaced_people: peopleCount,
        medical_observation_required: medReq,
        accessibility_required: accReq,
        women_child_safe_area_required: safeReq,
        notes: "Generated from Decision Panel"
      };
      const res = await api.createShelterRequest(incident.id, payload);
      setRequest(res.data);
    } catch (e: any) {
      setError(e.message || "Failed to create request");
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!request) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getShelterRecommendations(request.id);
      setEvaluation(res.data);
    } catch (e: any) {
      setError(e.message || "Failed to get recommendations");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveSingle = async (shelterId: number, count: number, score: number, explanation: string) => {
    if (!request) return;
    setLoading(true);
    setError(null);
    try {
      await api.approveShelterReservations(request.id, [{
        shelter_id: shelterId,
        reserved_people: count,
        recommendation_score: score,
        explanation
      }]);
      alert("Reservation Approved!");
      onAllocationApproved();
    } catch (e: any) {
      setError(e.message || "Failed to approve reservation");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveSplit = async () => {
    if (!request || !evaluation?.split_allocation_plan) return;
    setLoading(true);
    setError(null);
    try {
      const reservations = evaluation.split_allocation_plan.shelters_involved.map(s => ({
        shelter_id: s.shelter_id,
        reserved_people: s.proposed_people_count,
        recommendation_score: null,
        explanation: s.explanation
      }));
      await api.approveShelterReservations(request.id, reservations);
      alert("Split Reservations Approved!");
      onAllocationApproved();
    } catch (e: any) {
      setError(e.message || "Failed to approve split reservations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {/* Request Form */}
      <div className="border border-slate-200 rounded-lg p-6 bg-white">
        <h3 className="text-lg font-bold text-slate-800 mb-4">Shelter Request</h3>
        {!request ? (
          <div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Total Displaced People</label>
                <input type="number" value={peopleCount} onChange={e => setPeopleCount(parseInt(e.target.value))} className="w-full border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Requiring Medical Ops</label>
                <input type="number" value={medReq} onChange={e => setMedReq(parseInt(e.target.value))} className="w-full border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Requiring Accessibility</label>
                <input type="number" value={accReq} onChange={e => setAccReq(parseInt(e.target.value))} className="w-full border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Requiring Safe Area (Women/Children)</label>
                <input type="number" value={safeReq} onChange={e => setSafeReq(parseInt(e.target.value))} className="w-full border-slate-300 rounded-md shadow-sm focus:border-emerald-500 focus:ring-emerald-500" />
              </div>
            </div>
            <button 
              onClick={handleCreateRequest} 
              disabled={loading}
              className="px-4 py-2 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700 disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Create Shelter Request'}
            </button>
          </div>
        ) : (
          <div>
            <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-md mb-4 flex justify-between items-center">
              <div>
                <p className="font-bold text-emerald-800">Request #{request.id} Created</p>
                <p className="text-sm text-emerald-700">Needs shelter for {request.total_displaced_people} people.</p>
              </div>
              <button 
                onClick={handleEvaluate} 
                disabled={loading}
                className="px-4 py-2 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700 disabled:opacity-50"
              >
                {loading ? 'Evaluating...' : 'Find Shelters'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Evaluation Results */}
      {evaluation && (
        <div className="space-y-6">
          
          {/* Split Plan */}
          {evaluation.split_allocation_plan && evaluation.split_allocation_plan.is_split && (
            <div className="border border-blue-200 rounded-lg p-6 bg-blue-50">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-blue-800">Split Allocation Recommended</h3>
                  <p className="text-sm text-blue-600">No single shelter can safely accommodate all {request?.total_displaced_people} people.</p>
                </div>
                <button 
                  onClick={handleApproveSplit}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700"
                >
                  Approve Split Plan
                </button>
              </div>
              <p className="text-sm text-slate-700 mb-4 bg-white p-3 rounded border border-blue-100">{evaluation.split_allocation_plan.explanation}</p>
              <div className="grid gap-2">
                {evaluation.split_allocation_plan.shelters_involved.map(s => (
                  <div key={s.shelter_id} className="bg-white p-3 rounded border border-blue-100 flex justify-between items-center">
                    <div>
                      <p className="font-bold">{s.shelter_name}</p>
                      <p className="text-xs text-slate-500">{s.distance_km}km away</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-blue-700">{s.proposed_people_count} people</p>
                      <p className="text-xs text-slate-500">{s.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Single Recommendations */}
          <div className="border border-slate-200 rounded-lg p-6 bg-white">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Alternative Shelters</h3>
            <div className="space-y-4">
              {evaluation.single_source_recommendations.map(rec => (
                <div key={rec.shelter_id} className="border border-slate-200 rounded p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-bold text-lg">#{rec.rank} {rec.shelter_name}</h4>
                      <div className="flex gap-4 text-xs text-slate-500 mt-1">
                        <span>Score: {rec.total_score}</span>
                        <span>Distance: {rec.distance_km}km</span>
                        <span>Risk: <span className={`font-bold uppercase ${
                          rec.overcrowding_risk_level === 'high' ? 'text-red-500' : 
                          rec.overcrowding_risk_level === 'medium' ? 'text-yellow-500' : 'text-green-500'
                        }`}>{rec.overcrowding_risk_level}</span></span>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleApproveSingle(rec.shelter_id, rec.proposed_people_count, rec.total_score, rec.explanation)}
                      disabled={loading || rec.overcrowding_risk_level === 'high'}
                      className="px-3 py-1.5 bg-emerald-600 text-white text-sm font-bold rounded hover:bg-emerald-700 disabled:opacity-50 disabled:bg-slate-400"
                    >
                      {rec.overcrowding_risk_level === 'high' ? 'Unsafe to Approve' : 'Approve'}
                    </button>
                  </div>
                  <p className="text-sm text-slate-700 mb-2">{rec.explanation}</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-emerald-50 text-emerald-700 p-2 rounded">
                      <strong>Pros:</strong> {rec.positive_reasons.join(', ')}
                    </div>
                    {rec.limitations.length > 0 && (
                      <div className="bg-red-50 text-red-700 p-2 rounded">
                        <strong>Cons:</strong> {rec.limitations.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

    </div>
  );
};
