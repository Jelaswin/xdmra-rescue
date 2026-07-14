import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { GeocodingResult } from '../../types';

interface LocationPickerMapProps {
  initialLat: number;
  initialLon: number;
  onLocationChange: (lat: number, lon: number) => void;
  searchedLocation?: GeocodingResult | null;
}

const MapEvents = ({ onLocationChange }: { onLocationChange: (lat: number, lon: number) => void }) => {
  useMapEvents({
    click(e) {
      onLocationChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

const MapController = ({ searchedLocation }: { searchedLocation?: GeocodingResult | null }) => {
  const map = useMap();
  useEffect(() => {
    if (searchedLocation) {
      map.setView([searchedLocation.latitude, searchedLocation.longitude], 14);
    }
  }, [searchedLocation, map]);
  return null;
};

export const LocationPickerMap: React.FC<LocationPickerMapProps> = ({ 
  initialLat, 
  initialLon, 
  onLocationChange,
  searchedLocation
}) => {
  const [position, setPosition] = useState<L.LatLngExpression>([initialLat, initialLon]);

  useEffect(() => {
    setPosition([initialLat, initialLon]);
  }, [initialLat, initialLon]);

  return (
    <div className="h-[300px] w-full rounded-md overflow-hidden border border-gray-300">
      <MapContainer center={position} zoom={13} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker 
          position={position}
          draggable={true}
          eventHandlers={{
            dragend: (e) => {
              const marker = e.target;
              const position = marker.getLatLng();
              onLocationChange(position.lat, position.lng);
            }
          }}
        />
        <MapEvents onLocationChange={onLocationChange} />
        <MapController searchedLocation={searchedLocation} />
      </MapContainer>
    </div>
  );
};
