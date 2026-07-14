import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Warehouse, ReliefInventory, DeliveryVehicle } from '../types';

export const ReliefManagementDashboard: React.FC = () => {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [vehicles, setVehicles] = useState<DeliveryVehicle[]>([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<number | null>(null);
  const [inventory, setInventory] = useState<ReliefInventory[]>([]);

  useEffect(() => {
    fetchWarehouses();
    fetchVehicles();
  }, []);

  useEffect(() => {
    if (selectedWarehouseId) {
      fetchInventory(selectedWarehouseId);
    }
  }, [selectedWarehouseId]);

  const fetchWarehouses = async () => {
    try {
      const res = await api.getWarehouses();
      setWarehouses(res.data);
      if (res.data.length > 0 && !selectedWarehouseId) {
        setSelectedWarehouseId(res.data[0].id);
      }
    } catch (error) {
      console.error("Failed to fetch warehouses", error);
    }
  };

  const fetchVehicles = async () => {
    try {
      const res = await api.getDeliveryVehicles();
      setVehicles(res.data);
    } catch (error) {
      console.error("Failed to fetch vehicles", error);
    }
  };

  const fetchInventory = async (id: number) => {
    try {
      const res = await api.getWarehouseInventory(id);
      setInventory(res.data);
    } catch (error) {
      console.error("Failed to fetch inventory", error);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Relief Supply Management</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Warehouses</h2>
          <div className="space-y-4">
            {warehouses.map(w => (
              <div 
                key={w.id} 
                className={`p-4 border rounded cursor-pointer ${selectedWarehouseId === w.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'}`}
                onClick={() => setSelectedWarehouseId(w.id)}
              >
                <div className="flex justify-between items-center">
                  <h3 className="font-bold">{w.name}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${w.operating_status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                    {w.operating_status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-2">{w.location_name} • Type: {w.warehouse_type}</p>
                <p className="text-sm text-gray-600">Workload: {w.current_dispatch_workload} / {w.maximum_dispatch_capacity}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Delivery Vehicles</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="py-2 px-4">Name</th>
                  <th className="py-2 px-4">Type</th>
                  <th className="py-2 px-4">Capacity</th>
                  <th className="py-2 px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map(v => (
                  <tr key={v.id} className="border-b">
                    <td className="py-2 px-4">{v.name}</td>
                    <td className="py-2 px-4">{v.vehicle_type}</td>
                    <td className="py-2 px-4">{v.capacity_units} units</td>
                    <td className="py-2 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${v.availability_status === 'available' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {v.availability_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {selectedWarehouseId && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Inventory for {warehouses.find(w => w.id === selectedWarehouseId)?.name}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="py-2 px-4">Item Type</th>
                  <th className="py-2 px-4">Available</th>
                  <th className="py-2 px-4">Reserved</th>
                  <th className="py-2 px-4">Reorder Level</th>
                  <th className="py-2 px-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map(item => {
                  const isLow = item.quantity_available <= item.reorder_level;
                  return (
                    <tr key={item.id} className="border-b">
                      <td className="py-2 px-4 font-medium">{item.display_name}</td>
                      <td className="py-2 px-4">{item.quantity_available} {item.unit}</td>
                      <td className="py-2 px-4">{item.quantity_reserved} {item.unit}</td>
                      <td className="py-2 px-4">{item.reorder_level} {item.unit}</td>
                      <td className="py-2 px-4">
                        {isLow ? (
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">Low Stock</span>
                        ) : (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Healthy</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {inventory.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-gray-500">No inventory found for this warehouse.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
