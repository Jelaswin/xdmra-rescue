import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { EmergencyShelter, ShelterDashboardSummary } from '../types';

export const ShelterManagementDashboard: React.FC = () => {
  const [shelters, setShelters] = useState<EmergencyShelter[]>([]);
  const [summary, setSummary] = useState<ShelterDashboardSummary | null>(null);

  useEffect(() => {
    fetchShelters();
    fetchSummary();
  }, []);

  const fetchShelters = async () => {
    try {
      const res = await api.getShelters();
      setShelters(res.data);
    } catch (error) {
      console.error("Failed to fetch shelters", error);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await api.getShelterDashboardSummary();
      setSummary(res.data);
    } catch (error) {
      console.error("Failed to fetch shelter summary", error);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Shelter Management</h1>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Total Shelters</h3>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_shelters}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Available Spaces</h3>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.available_spaces}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">People Sheltered</h3>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.people_sheltered}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Active Requests</h3>
            <p className="text-2xl font-bold text-gray-900 mt-1">{summary.active_requests}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Shelter Directory</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-left">
            <thead className="bg-gray-100 text-gray-600">
              <tr>
                <th className="py-2 px-4">Name</th>
                <th className="py-2 px-4">Type</th>
                <th className="py-2 px-4">Capacity</th>
                <th className="py-2 px-4">Occupancy</th>
                <th className="py-2 px-4">Reserved</th>
                <th className="py-2 px-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {shelters.map(s => (
                <tr key={s.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-4 font-medium">{s.name}</td>
                  <td className="py-2 px-4">{s.shelter_type || 'General'}</td>
                  <td className="py-2 px-4">{s.total_capacity}</td>
                  <td className="py-2 px-4">{s.occupied_capacity}</td>
                  <td className="py-2 px-4">{s.reserved_capacity}</td>
                  <td className="py-2 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      s.operating_status === 'open' ? 'bg-green-100 text-green-800' : 
                      s.operating_status === 'full' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {s.operating_status}
                    </span>
                  </td>
                </tr>
              ))}
              {shelters.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-gray-500">No shelters found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
