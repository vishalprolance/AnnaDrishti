import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config';
import FarmerIncomeCard from './FarmerIncomeCard';

interface FarmerIncome {
  farmer_id: string;
  contribution_kg: string;
  blended_rate_per_kg: string;
  total_revenue: string;
  channel_breakdown: Array<{
    channel: string;
    channel_name: string;
    quantity_kg: string;
    revenue: string;
    rate_per_kg: string;
  }>;
  vs_best_single_channel: {
    single_channel_revenue: string;
    improvement: string;
    improvement_percentage: string;
  };
}

interface FarmerContributionViewProps {
  allocationId: string;
}

export default function FarmerContributionView({ allocationId }: FarmerContributionViewProps) {
  const [farmerIncomes, setFarmerIncomes] = useState<FarmerIncome[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'contribution' | 'income'>('income');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    const fetchFarmerIncomes = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/allocations/${allocationId}/realization`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch farmer income data');
        }
        
        const data = await response.json();
        setFarmerIncomes(data.farmer_incomes || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load farmer income data');
      } finally {
        setLoading(false);
      }
    };

    fetchFarmerIncomes();
  }, [allocationId]);

  // Filter farmers based on search term
  const filteredFarmers = farmerIncomes.filter((farmer) => {
    const searchLower = searchTerm.toLowerCase();
    return farmer.farmer_id.toLowerCase().includes(searchLower);
  });

  // Sort farmers
  const sortedFarmers = [...filteredFarmers].sort((a, b) => {
    let compareValue = 0;
    
    if (sortBy === 'name') {
      compareValue = a.farmer_id.localeCompare(b.farmer_id);
    } else if (sortBy === 'contribution') {
      compareValue = parseFloat(a.contribution_kg) - parseFloat(b.contribution_kg);
    } else if (sortBy === 'income') {
      compareValue = parseFloat(a.total_revenue) - parseFloat(b.total_revenue);
    }
    
    return sortOrder === 'asc' ? compareValue : -compareValue;
  });

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading farmer income data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading farmer income data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (farmerIncomes.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-gray-500">
          <p className="font-semibold">No farmer income data</p>
          <p className="text-sm mt-1">Complete an allocation to see farmer income tracking</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Farmer Income Tracking</h2>
        <p className="text-sm text-gray-600 mt-1">
          Income breakdown for {farmerIncomes.length} farmer{farmerIncomes.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="p-4">
        {/* Search and Filter Controls */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          {/* Search Input */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by farmer ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          {/* Sort Controls */}
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'contribution' | 'income')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="income">Sort by Income</option>
              <option value="contribution">Sort by Contribution</option>
              <option value="name">Sort by Name</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-green-500"
              title={sortOrder === 'asc' ? 'Sort Descending' : 'Sort Ascending'}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>

        {/* Results Count */}
        {searchTerm && (
          <div className="mb-4 text-sm text-gray-600">
            Showing {sortedFarmers.length} of {farmerIncomes.length} farmers
          </div>
        )}

        {/* Farmer Income Cards Grid */}
        {sortedFarmers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedFarmers.map((farmer) => (
              <FarmerIncomeCard key={farmer.farmer_id} farmerIncome={farmer} />
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            <p>No farmers match your search criteria</p>
          </div>
        )}
      </div>
    </div>
  );
}
