import React from 'react';
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config';
import InventoryCard from './InventoryCard';

interface FarmerContribution {
  contribution_id: string;
  farmer_id: string;
  farmer_name: string;
  quantity_kg: string;
  quality_grade: string;
  timestamp: string;
  allocated: boolean;
}

interface InventoryBreakdown {
  fpo_id: string;
  crop_type: string;
  total_quantity_kg: string;
  available_quantity_kg: string;
  reserved_quantity_kg: string;
  allocated_quantity_kg: string;
  contributions: FarmerContribution[];
  farmer_count: number;
  last_updated: string;
}

interface CollectiveInventoryViewProps {
  fpoId: string;
}

export default function CollectiveInventoryView({ fpoId }: CollectiveInventoryViewProps) {
  const [inventoryData, setInventoryData] = useState<Record<string, InventoryBreakdown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Fetch inventory summary
  useEffect(() => {
    const fetchInventory = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/inventory/${fpoId}/summary`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch inventory');
        }
        
        const data = await response.json();
        
        // Fetch detailed breakdown for each crop type
        const detailedData: Record<string, InventoryBreakdown> = {};
        for (const cropType of data.crop_types) {
          const detailResponse = await fetch(`${API_BASE_URL}/api/inventory/${fpoId}/${cropType}`);
          if (detailResponse.ok) {
            detailedData[cropType] = await detailResponse.json();
          }
        }
        
        setInventoryData(detailedData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load inventory');
      } finally {
        setLoading(false);
      }
    };

    fetchInventory();
  }, [fpoId]);

  // WebSocket for real-time updates
  useEffect(() => {
    // Note: WebSocket URL would need to be configured based on your backend
    // For now, we'll use polling as a fallback
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/inventory/${fpoId}/summary`);
        if (response.ok) {
          const data = await response.json();
          
          // Update detailed data for each crop
          const detailedData: Record<string, InventoryBreakdown> = {};
          for (const cropType of data.crop_types) {
            const detailResponse = await fetch(`${API_BASE_URL}/api/inventory/${fpoId}/${cropType}`);
            if (detailResponse.ok) {
              detailedData[cropType] = await detailResponse.json();
            }
          }
          
          setInventoryData(detailedData);
        }
      } catch (err) {
        console.error('Failed to poll inventory updates:', err);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [fpoId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading inventory...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading inventory</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const cropTypes = Object.keys(inventoryData);

  if (cropTypes.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-gray-500">
          <p className="font-semibold">No inventory data</p>
          <p className="text-sm mt-1">Add farmer contributions to see inventory</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Collective Inventory</h2>
        <p className="text-sm text-gray-600 mt-1">
          Real-time inventory across {cropTypes.length} crop type{cropTypes.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="p-4">
        {/* Inventory Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {cropTypes.map((cropType) => (
            <InventoryCard
              key={cropType}
              cropType={cropType}
              inventory={inventoryData[cropType]}
              onClick={() => setSelectedCrop(selectedCrop === cropType ? null : cropType)}
              isSelected={selectedCrop === cropType}
            />
          ))}
        </div>

        {/* Per-Farmer Breakdown */}
        {selectedCrop && inventoryData[selectedCrop] && (
          <div className="mt-6 border-t border-gray-200 pt-6">
            <h3 className="text-md font-semibold text-gray-900 mb-4">
              Farmer Contributions - {selectedCrop.charAt(0).toUpperCase() + selectedCrop.slice(1)}
            </h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Farmer
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity (kg)
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {inventoryData[selectedCrop].contributions.map((contribution) => (
                    <tr key={contribution.contribution_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {contribution.farmer_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {parseFloat(contribution.quantity_kg).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          contribution.quality_grade === 'A' ? 'bg-green-100 text-green-800' :
                          contribution.quality_grade === 'B' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-orange-100 text-orange-800'
                        }`}>
                          Grade {contribution.quality_grade}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          contribution.allocated ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {contribution.allocated ? 'Allocated' : 'Available'}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {new Date(contribution.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 text-sm text-gray-600">
              Total: {inventoryData[selectedCrop].farmer_count} farmer{inventoryData[selectedCrop].farmer_count !== 1 ? 's' : ''} contributing
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
