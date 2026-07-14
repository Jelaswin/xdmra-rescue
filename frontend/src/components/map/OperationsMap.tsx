import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import { MapIncident, MapTeam } from '../../types';
import { MapMarkerPopup } from './MapMarkerPopup';

interface OperationsMapProps {
  incidents: MapIncident[];
  teams: MapTeam[];
}

const getIncidentColor = (severity: string) => {
  switch (severity) {
    case 'critical': return '#dc2626'; // red-600
    case 'high': return '#ea580c'; // orange-600
    case 'medium': return '#eab308'; // yellow-500
    default: return '#3b82f6'; // blue-500
  }
};

const createIncidentIcon = (severity: string, title: string) => {
  const color = getIncidentColor(severity);
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${color};
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
};

const createTeamIcon = (status: string) => {
  const bgColor = status === 'unavailable' ? '#9ca3af' : (status === 'assigned' ? '#3b82f6' : '#22c55e');
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${bgColor};
      width: 24px;
      height: 24px;
      border-radius: 4px;
      border: 2px solid white;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 14px;
    ">T</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
};

export const OperationsMap: React.FC<OperationsMapProps> = ({ incidents, teams }) => {
  const [center, setCenter] = useState<L.LatLngExpression>([11.0168, 76.9558]); // Default Coimbatore
  
  useEffect(() => {
    if (incidents.length > 0) {
      setCenter([incidents[0].latitude, incidents[0].longitude]);
    } else if (teams.length > 0) {
      setCenter([teams[0].latitude, teams[0].longitude]);
    }
  }, [incidents, teams]);

  return (
    <div className="h-full w-full relative z-0">
      <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {incidents.map((incident) => (
          <Marker 
            key={`incident-${incident.id}`}
            position={[incident.latitude, incident.longitude]}
            icon={createIncidentIcon(incident.severity, incident.title)}
          >
            <MapMarkerPopup type="incident" data={incident} />
          </Marker>
        ))}

        {teams.map((team) => (
          <Marker 
            key={`team-${team.id}`}
            position={[team.latitude, team.longitude]}
            icon={createTeamIcon(team.availability_status)}
          >
            <MapMarkerPopup type="team" data={team} />
          </Marker>
        ))}
      </MapContainer>
      
      {/* Legend overlay */}
      <div className="absolute bottom-6 left-6 bg-white p-3 rounded-md shadow-lg z-[1000] text-xs">
        <h4 className="font-bold mb-2">Map Legend</h4>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-sm bg-[#22c55e] border border-white"></div>
            <span>Team Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-sm bg-[#3b82f6] border border-white"></div>
            <span>Team Assigned</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-sm bg-[#9ca3af] border border-white"></div>
            <span>Team Unavailable</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#dc2626] border border-white"></div>
            <span>Critical Incident</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#ea580c] border border-white"></div>
            <span>High Priority</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#eab308] border border-white"></div>
            <span>Medium Priority</span>
          </div>
        </div>
      </div>
    </div>
  );
};
