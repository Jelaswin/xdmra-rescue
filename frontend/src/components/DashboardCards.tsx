import { DashboardSummary, ReliefDashboardSummary } from '../types';

interface Props {
  summary: DashboardSummary | null;
  reliefSummary?: ReliefDashboardSummary | null;
}

export default function DashboardCards({ summary, reliefSummary }: Props) {
  if (!summary) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white p-4 rounded-lg shadow-sm border border-slate-100 animate-pulse h-24"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <h3 className="text-sm font-medium text-slate-500">Total Incidents</h3>
        <p className="text-3xl font-bold text-slate-800 mt-1">{summary.total_incidents}</p>
      </div>
      <div className="bg-red-50 p-4 rounded-lg shadow-sm border border-red-100">
        <h3 className="text-sm font-medium text-red-600">Critical Incidents</h3>
        <p className="text-3xl font-bold text-red-700 mt-1">{summary.critical_incidents}</p>
      </div>
      <div className="bg-emerald-50 p-4 rounded-lg shadow-sm border border-emerald-100">
        <h3 className="text-sm font-medium text-emerald-700">Available Teams</h3>
        <p className="text-3xl font-bold text-emerald-800 mt-1">{summary.available_teams}</p>
      </div>
      <div className="bg-blue-50 p-4 rounded-lg shadow-sm border border-blue-100">
        <h3 className="text-sm font-medium text-blue-700">Active Allocations</h3>
        <p className="text-3xl font-bold text-blue-800 mt-1">{summary.active_allocations}</p>
      </div>
      
      {reliefSummary && (
        <>
          <div className="bg-purple-50 p-4 rounded-lg shadow-sm border border-purple-100">
            <h3 className="text-sm font-medium text-purple-700">Active Relief Req</h3>
            <p className="text-3xl font-bold text-purple-800 mt-1">{reliefSummary.active_requests}</p>
          </div>
          <div className="bg-indigo-50 p-4 rounded-lg shadow-sm border border-indigo-100">
            <h3 className="text-sm font-medium text-indigo-700">Dispatches Pending</h3>
            <p className="text-3xl font-bold text-indigo-800 mt-1">{reliefSummary.dispatches_in_progress}</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg shadow-sm border border-yellow-100">
            <h3 className="text-sm font-medium text-yellow-700">Low Stock Items</h3>
            <p className="text-3xl font-bold text-yellow-800 mt-1">{reliefSummary.low_stock_items}</p>
          </div>
        </>
      )}
    </div>
  );
}
