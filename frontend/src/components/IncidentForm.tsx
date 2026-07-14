import { useState } from 'react';
import { IncidentCreateRequest } from '../types';

interface Props {
  onIncidentCreated: () => void;
}

export default function IncidentForm({ onIncidentCreated }: Props) {
  const [formData, setFormData] = useState<IncidentCreateRequest>({
    title: '',
    description: '',
    incident_type: 'Flood',
    latitude: 34.0522,
    longitude: -118.2437,
    severity: 'medium',
    affected_people: 0,
    injured_people: 0,
    vulnerable_people: 0,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const { api } = await import('../services/api');
      await api.createIncident(formData);
      setSuccess(true);
      setFormData({
        title: '',
        description: '',
        incident_type: 'Flood',
        latitude: 34.0522,
        longitude: -118.2437,
        severity: 'medium',
        affected_people: 0,
        injured_people: 0,
        vulnerable_people: 0,
      });
      onIncidentCreated();
      
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to create incident');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-3">
        <h3 className="font-semibold text-slate-800">Report New Incident</h3>
      </div>
      
      <div className="p-4">
        {success && (
          <div className="mb-4 bg-emerald-50 text-emerald-700 p-3 rounded text-sm border border-emerald-100">
            Incident reported successfully.
          </div>
        )}
        
        {error && (
          <div className="mb-4 bg-red-50 text-red-700 p-3 rounded text-sm border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Title</label>
            <input 
              required
              type="text" 
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="w-full text-sm border border-slate-300 rounded px-3 py-2 focus:ring-brand-primary focus:border-brand-primary"
              placeholder="e.g. Downtown Flash Flood"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Type</label>
            <select 
              name="incident_type"
              value={formData.incident_type}
              onChange={handleChange}
              className="w-full text-sm border border-slate-300 rounded px-3 py-2"
            >
              <option value="Flood">Flood</option>
              <option value="Earthquake">Earthquake</option>
              <option value="Fire">Fire</option>
              <option value="Medical">Medical</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Severity</label>
              <select 
                name="severity"
                value={formData.severity}
                onChange={handleChange}
                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Affected</label>
              <input 
                type="number" 
                min="0"
                name="affected_people"
                value={formData.affected_people}
                onChange={handleChange}
                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Latitude</label>
              <input 
                required
                type="number" 
                step="any"
                min="-90" max="90"
                name="latitude"
                value={formData.latitude}
                onChange={handleChange}
                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Longitude</label>
              <input 
                required
                type="number" 
                step="any"
                min="-180" max="180"
                name="longitude"
                value={formData.longitude}
                onChange={handleChange}
                className="w-full text-sm border border-slate-300 rounded px-3 py-2"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Description</label>
            <textarea 
              required
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="w-full text-sm border border-slate-300 rounded px-3 py-2"
              placeholder="Provide incident details..."
            ></textarea>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-brand-primary text-white font-medium text-sm py-2 px-4 rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Submitting...' : 'Submit Report'}
          </button>
        </form>
      </div>
    </div>
  );
}
