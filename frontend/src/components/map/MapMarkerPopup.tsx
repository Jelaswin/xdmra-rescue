import React from 'react';
import { Popup } from 'react-leaflet';
import { MapIncident, MapTeam, Warehouse } from '../../types';

interface MapMarkerPopupProps {
  type: 'incident' | 'team' | 'warehouse';
  data: MapIncident | MapTeam | Warehouse;
}

export const MapMarkerPopup: React.FC<MapMarkerPopupProps> = ({ type, data }) => {
  if (type === 'incident') {
    const incident = data as MapIncident;
    return (
      <Popup>
        <div className="p-1 min-w-[200px]">
          <h3 className="font-bold text-gray-900 mb-1">{incident.title}</h3>
          <p className="text-sm text-gray-600 mb-2">{incident.incident_type} &middot; {incident.status.replace('_', ' ')}</p>
          <div className="text-xs space-y-1">
            <p><strong>Severity:</strong> {incident.severity}</p>
            <p><strong>Affected:</strong> {incident.affected_people} people</p>
            {incident.priority_level && (
              <p>
                <strong>Priority:</strong> <span className="uppercase font-semibold">{incident.priority_level}</span>
              </p>
            )}
          </div>
        </div>
      </Popup>
    );
  } else if (type === 'warehouse') {
    const warehouse = data as Warehouse;
    return (
      <Popup>
        <div className="p-1 min-w-[200px]">
          <h3 className="font-bold text-gray-900 mb-1">{warehouse.name}</h3>
          <p className="text-sm text-gray-600 mb-2">{warehouse.location_name}</p>
          <div className="text-xs space-y-1">
            <p><strong>Status:</strong> <span className="capitalize">{warehouse.operating_status}</span></p>
            <p><strong>Workload:</strong> {warehouse.current_dispatch_workload} / {warehouse.maximum_dispatch_capacity}</p>
          </div>
        </div>
      </Popup>
    );
  } else {
    const team = data as MapTeam;
    return (
      <Popup>
        <div className="p-1 min-w-[200px]">
          <h3 className="font-bold text-gray-900 mb-1">{team.name}</h3>
          <p className="text-sm text-gray-600 mb-2">{team.availability_status}</p>
          <div className="text-xs space-y-1">
            <p><strong>Capacity:</strong> {team.capacity}</p>
            <p><strong>Workload:</strong> {team.current_workload}</p>
          </div>
        </div>
      </Popup>
    );
  }
};
