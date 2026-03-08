import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config';
import ChannelBreakdownCard from './ChannelBreakdownCard';

interface ChannelAllocation {
  channel_type: string;
  channel_id: string;
  channel_name: string;
  quantity_kg: number;
  price_per_kg: number;
  revenue: number;
  priority: number;
}

interface AllocationData {
  allocation_id: string;
  fpo_id: string;
  crop_type: string;
  allocation_date: string;
  channel_allocations: ChannelAllocation[];
  total_quantity_kg: number;
  blended_realization_per_kg: number;
  status: string;
}

interface RealizationMetricsViewProps {
  allocationId: string;
}

interface TrendDataPoint {
  date: string;
  blended_rate: number;
  society_rate: number;
  processing_rate: number;
  mandi_rate: number;
}

export default function RealizationMetricsView({ allocationId }: RealizationMetricsViewProps) {
  const [allocation, setAllocation] = useState<AllocationData | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAllocationData = async () => {
      try {
        setLoading(true);

        // Fetch current allocation
        const response = await fetch(`${API_BASE_URL}/api/allocations/${allocationId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch allocation');
        }

        const data: AllocationData = await response.json();
        setAllocation(data);

        // Fetch historical data for trend chart
        const historyResponse = await fetch(
          `${API_BASE_URL}/api/allocations/${data.fpo_id}/history?crop_type=${data.crop_type}&limit=10`
        );
        
        if (historyResponse.ok) {
          const historyData: AllocationData[] = await historyResponse.json();
          
          // Transform to trend data
          const trend = historyData.map((alloc) => {
            const societyAlloc = alloc.channel_allocations.find(c => c.channel_type === 'society');
            const processingAlloc = alloc.channel_allocations.find(c => c.channel_type === 'processing');
            const mandiAlloc = alloc.channel_allocations.find(c => c.channel_type === 'mandi');

            return {
              date: new Date(alloc.allocation_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              blended_rate: alloc.blended_realization_per_kg,
              society_rate: societyAlloc?.price_per_kg || 0,
              processing_rate: processingAlloc?.price_per_kg || 0,
              mandi_rate: mandiAlloc?.price_per_kg || 0,
            };
          }).reverse(); // Reverse to show oldest to newest

          setTrendData(trend);
        }

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load allocation data');
      } finally {
        setLoading(false);
      }
    };

    fetchAllocationData();
  }, [allocationId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading realization metrics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading realization metrics</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!allocation) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-gray-500">
          <p className="font-semibold">No allocation data</p>
          <p className="text-sm mt-1">Create an allocation to see realization metrics</p>
        </div>
      </div>
    );
  }

  // Calculate best single-channel rate
  const bestSingleChannelRate = Math.max(
    ...allocation.channel_allocations.map(c => c.price_per_kg)
  );

  const blendedRate = allocation.blended_realization_per_kg;
  const difference = blendedRate - bestSingleChannelRate;
  const differencePercentage = ((difference / bestSingleChannelRate) * 100);

  // Calculate total revenue
  const totalRevenue = allocation.channel_allocations.reduce(
    (sum, c) => sum + c.revenue,
    0
  );

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Blended Realization Metrics</h2>
        <p className="text-sm text-gray-600 mt-1">
          Revenue analysis for {allocation.crop_type}
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Blended Realization Summary */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6 border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-green-700 font-medium mb-1">Blended Realization Rate</div>
              <div className="text-4xl font-bold text-green-900">
                ₹{blendedRate.toFixed(2)}
                <span className="text-lg font-normal text-green-700 ml-1">/kg</span>
              </div>
              <div className="text-sm text-green-600 mt-2">
                Total Revenue: ₹{totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-green-700 font-medium mb-1">vs Best Single Channel</div>
              <div className={`text-2xl font-bold ${
                difference >= 0 ? 'text-green-900' : 'text-red-600'
              }`}>
                {difference >= 0 ? '+' : ''}₹{difference.toFixed(2)}
              </div>
              <div className={`text-sm mt-1 ${
                difference >= 0 ? 'text-green-600' : 'text-red-500'
              }`}>
                {difference >= 0 ? '+' : ''}{differencePercentage.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Comparison Message */}
          <div className="mt-4 pt-4 border-t border-green-200">
            {difference > 0 && (
              <div className="flex items-center text-sm text-green-700">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Collective selling achieved better realization than best single channel
              </div>
            )}
            {difference < 0 && (
              <div className="flex items-center text-sm text-red-600">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                Best single channel would have yielded higher realization
              </div>
            )}
            {difference === 0 && (
              <div className="flex items-center text-sm text-green-700">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-11a1 1 0 112 0v3.586l2.707 2.707a1 1 0 01-1.414 1.414l-3-3A1 1 0 019 11V7z" clipRule="evenodd" />
                </svg>
                Blended realization matches best single channel rate
              </div>
            )}
          </div>
        </div>

        {/* Channel-wise Breakdown */}
        <div>
          <h3 className="text-md font-semibold text-gray-900 mb-4">Channel-wise Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {allocation.channel_allocations
              .sort((a, b) => a.priority - b.priority)
              .map((channel) => (
                <ChannelBreakdownCard
                  key={channel.channel_id}
                  channel={channel}
                  totalQuantity={allocation.total_quantity_kg}
                  totalRevenue={totalRevenue}
                />
              ))}
          </div>
        </div>

        {/* Trend Chart */}
        {trendData.length > 0 && (
          <div>
            <h3 className="text-md font-semibold text-gray-900 mb-4">Historical Trend</h3>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                    label={{ value: 'Rate (₹/kg)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.5rem',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [`₹${value.toFixed(2)}/kg`, '']}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: '12px' }}
                    iconType="line"
                  />
                  <Line
                    type="monotone"
                    dataKey="blended_rate"
                    stroke="#10b981"
                    strokeWidth={3}
                    name="Blended Rate"
                    dot={{ fill: '#10b981', r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="society_rate"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Society Rate"
                    dot={{ fill: '#3b82f6', r: 3 }}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="processing_rate"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    name="Processing Rate"
                    dot={{ fill: '#8b5cf6', r: 3 }}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="mandi_rate"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Mandi Rate"
                    dot={{ fill: '#f59e0b', r: 3 }}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="text-xs text-gray-500 text-center mt-2">
                Historical realization rates across channels (last 10 allocations)
              </div>
            </div>
          </div>
        )}

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="text-xs text-blue-600 font-medium mb-1">Total Quantity</div>
            <div className="text-xl font-bold text-blue-900">
              {allocation.total_quantity_kg.toLocaleString()}
              <span className="text-sm font-normal text-blue-700 ml-1">kg</span>
            </div>
          </div>

          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <div className="text-xs text-purple-600 font-medium mb-1">Channels Used</div>
            <div className="text-xl font-bold text-purple-900">
              {allocation.channel_allocations.length}
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="text-xs text-green-600 font-medium mb-1">Best Channel Rate</div>
            <div className="text-xl font-bold text-green-900">
              ₹{bestSingleChannelRate.toFixed(2)}
              <span className="text-sm font-normal text-green-700 ml-1">/kg</span>
            </div>
          </div>

          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <div className="text-xs text-amber-600 font-medium mb-1">Allocation Date</div>
            <div className="text-sm font-bold text-amber-900">
              {new Date(allocation.allocation_date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
