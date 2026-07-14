import { RescueTeam } from '../types';

interface Props {
  teams: RescueTeam[];
}

export default function TeamList({ teams }: Props) {
  if (teams.length === 0) {
    return (
      <div className="bg-white p-8 text-center rounded-lg shadow-sm border border-slate-200">
        <p className="text-slate-500">No rescue teams found.</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'available': return <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-0.5 rounded-full font-medium">Available</span>;
      case 'assigned': return <span className="bg-amber-100 text-amber-800 text-xs px-2.5 py-0.5 rounded-full font-medium">Assigned</span>;
      case 'unavailable': return <span className="bg-red-100 text-red-800 text-xs px-2.5 py-0.5 rounded-full font-medium">Unavailable</span>;
      default: return null;
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {teams.map((team) => (
        <div key={team.id} className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h3 className="font-semibold text-slate-900">{team.name}</h3>
              <p className="text-xs text-slate-500 mt-0.5">Loc: {team.latitude.toFixed(4)}, {team.longitude.toFixed(4)}</p>
            </div>
            {getStatusBadge(team.availability_status)}
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
            <div>
              <p className="text-slate-500 text-xs mb-1">Capacity</p>
              <p className="font-medium text-slate-800">{team.capacity} pax</p>
            </div>
            <div>
              <p className="text-slate-500 text-xs mb-1">Workload</p>
              <p className="font-medium text-slate-800">{team.current_workload} active tasks</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div>
              <p className="text-slate-500 text-xs mb-1">Skills</p>
              <div className="flex flex-wrap gap-1">
                {team.skills.map((s, i) => (
                  <span key={i} className="bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded uppercase font-medium">
                    {s.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-slate-500 text-xs mb-1">Equipment</p>
              <div className="flex flex-wrap gap-1">
                {team.equipment.map((e, i) => (
                  <span key={i} className="bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded uppercase font-medium">
                    {e.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
