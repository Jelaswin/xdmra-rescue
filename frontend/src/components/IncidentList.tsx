import { Incident } from '../types';

interface Props {
  incidents: Incident[];
}

export default function IncidentList({ incidents }: Props) {
  if (incidents.length === 0) {
    return (
      <div className="bg-white p-8 text-center rounded-lg shadow-sm border border-slate-200">
        <p className="text-slate-500">No active incidents reported.</p>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'reported': return 'bg-slate-100 text-slate-800';
      case 'verified': return 'bg-blue-100 text-blue-800';
      case 'assigned': return 'bg-purple-100 text-purple-800';
      case 'in_progress': return 'bg-amber-100 text-amber-800';
      case 'resolved': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-600 uppercase bg-slate-50 border-b">
            <tr>
              <th className="px-4 py-3">Title / Type</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Affected (Injured)</th>
              <th className="px-4 py-3">Reported At</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id} className="border-b last:border-b-0 hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-900">{incident.title}</div>
                  <div className="text-slate-500 text-xs mt-0.5">{incident.incident_type}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getSeverityColor(incident.severity)}`}>
                    {incident.severity}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(incident.status)}`}>
                    {incident.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="text-slate-900">{incident.affected_people} total</div>
                  <div className="text-red-600 text-xs font-medium mt-0.5">{incident.injured_people} injured</div>
                </td>
                <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">
                  {new Date(incident.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
