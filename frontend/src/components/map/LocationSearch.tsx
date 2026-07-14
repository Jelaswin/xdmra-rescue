import React, { useState } from 'react';
import { GeocodingResult } from '../../types';
import { api } from '../../services/api';

interface LocationSearchProps {
  onLocationSelect: (location: GeocodingResult) => void;
}

export const LocationSearch: React.FC<LocationSearchProps> = ({ onLocationSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<GeocodingResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchLocations(query);
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Failed to search location');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full relative">
      <div className="flex gap-2">
        <input 
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search location (e.g., Coimbatore)"
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button 
          onClick={handleSearch}
          disabled={loading}
          className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      
      {results.length > 0 && (
        <ul className="absolute z-[1000] w-full mt-1 max-h-60 overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5">
          {results.map((res, i) => (
            <li 
              key={i}
              onClick={() => {
                onLocationSelect(res);
                setResults([]);
                setQuery(res.display_name);
              }}
              className="cursor-pointer px-4 py-2 text-sm text-gray-700 hover:bg-blue-50"
            >
              <div className="font-medium text-xs mb-1 text-gray-900">{res.display_name}</div>
              <div className="text-[10px] text-gray-500">Lat: {res.latitude.toFixed(4)}, Lon: {res.longitude.toFixed(4)}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
