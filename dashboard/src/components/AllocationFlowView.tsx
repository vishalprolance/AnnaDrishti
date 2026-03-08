import React, { useEffect, useState } from 'react';
import { Sankey, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config';
import {
  transformToSankeyFormat,
  calculateChannelPercentages,
  getChannelColor,
  type AllocationData,
  type SankeyData,
} from '../utils/allocationFlowTransform';

interface AllocationFlowViewProps {
  allocationId: string;
}

interface TooltipPayload {
  name?: string;
  value?: number;
  payload?: {
    source?: { name: string };
    target?: { name: string };
    value?: number;
  };
}

export default function AllocationFlowView({ allocationId }: AllocationFlowViewProps) {
  const [allocation, setAllocation] = useState<AllocationData | null>(null);
  const [sankeyData, setSankeyData] = useState<SankeyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAllocation = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/allocations/${allocationId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch allocation');
        }

        const data: AllocationData = await response.json();
        setAllocation(data);

        // Transform to Sankey format
        const sankey = transformToSankeyFormat(data);
        setSankeyData(sankey);

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load allocation');
      } finally {
        setLoading(false);
      }
    };

    fetchAllocation();
  }, [allocationId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading allocation flow...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading allocation</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!allocation || !sankeyData) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-gray-500">
          <p className="font-semibold">No allocation data</p>
          <p className="text-sm mt-1">Create an allocation to see the flow visualization</p>
        </div>
      </div>
    );
  }

  const percentages = calculateChannelPercentages(allocation);

  // Custom tooltip for Sankey diagram
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0];
      
      // Handle link tooltip
      if (data.payload?.source && data.payload?.target) {
        const value = data.payload.value || 0;
        const percentage = ((value / allocation.total_quantity_kg) * 100).toFixed(1);
        
        return (
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
            <p className="text-sm font-semibold text-gray-900">
              {data.payload.source.name} → {data.payload.target.name}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              {value.toLocaleString()} kg ({percentage}%)
            </p>
          </div>
        );
      }
      
      // Handle node tooltip
      if (data.name) {
        return (
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
            <p className="text-sm font-semibold text-gray-900">{data.name}</p>
            {data.value && (
              <p className="text-sm text-gray-600 mt-1">
                {data.value.toLocaleString()} kg
              </p>
            )}
          </div>
        );
      }
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Allocation Flow</h2>
        <p className="text-sm text-gray-600 mt-1">
          Distribution of {allocation.crop_type} across channels
        </p>
      </div>

      <div className="p-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="text-sm text-blue-600 font-medium mb-1">Total Inventory</div>
            <div className="text-2xl font-bold text-blue-900">
              {allocation.total_quantity_kg.toLocaleString()}
              <span className="text-sm font-normal text-blue-700 ml-1">kg</span>
            </div>
          </div>

          {allocation.channel_allocations.map((channel) => {
            const channelType = channel.channel_type;
            const color = getChannelColor(channelType);
            const bgColor = channelType === 'society' ? 'bg-green-50' :
                           channelType === 'processing' ? 'bg-purple-50' : 'bg-amber-50';
            const borderColor = channelType === 'society' ? 'border-green-200' :
                               channelType === 'processing' ? 'border-purple-200' : 'border-amber-200';
            const textColor = channelType === 'society' ? 'text-green-600' :
                             channelType === 'processing' ? 'text-purple-600' : 'text-amber-600';
            const textDarkColor = channelType === 'society' ? 'text-green-900' :
                                 channelType === 'processing' ? 'text-purple-900' : 'text-amber-900';

            return (
              <div key={channel.channel_id} className={`${bgColor} rounded-lg p-4 border ${borderColor}`}>
                <div className={`text-sm ${textColor} font-medium mb-1 capitalize`}>
                  {channelType}
                </div>
                <div className={`text-2xl font-bold ${textDarkColor}`}>
                  {channel.quantity_kg.toLocaleString()}
                  <span className={`text-sm font-normal ${textColor} ml-1`}>kg</span>
                </div>
                <div className={`text-xs ${textColor} mt-1`}>
                  {percentages[channelType]?.toFixed(1)}% of total
                </div>
              </div>
            );
          })}
        </div>

        {/* Sankey Diagram */}
        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
          <h3 className="text-md font-semibold text-gray-900 mb-4">Flow Visualization</h3>
          
          <ResponsiveContainer width="100%" height={400}>
            <Sankey
              data={sankeyData}
              node={{ fill: '#8884d8', fillOpacity: 1 }}
              link={{ stroke: '#77c878', strokeOpacity: 0.5 }}
              nodePadding={50}
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <Tooltip content={<CustomTooltip />} />
            </Sankey>
          </ResponsiveContainer>

          <div className="mt-4 text-xs text-gray-500 text-center">
            Flow shows distribution from collective inventory to sales channels
          </div>
        </div>

        {/* Channel Breakdown Table */}
        <div className="mt-6">
          <h3 className="text-md font-semibold text-gray-900 mb-4">Channel Details</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity (kg)
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Percentage
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price/kg
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {allocation.channel_allocations
                  .sort((a, b) => a.priority - b.priority)
                  .map((channel) => {
                    const percentage = ((channel.quantity_kg / allocation.total_quantity_kg) * 100).toFixed(1);
                    const channelColor = getChannelColor(channel.channel_type);
                    
                    return (
                      <tr key={channel.channel_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span
                            className="inline-flex items-center px-2 py-1 text-xs font-medium rounded capitalize"
                            style={{
                              backgroundColor: `${channelColor}20`,
                              color: channelColor,
                            }}
                          >
                            {channel.channel_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          {channel.channel_name}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          {channel.quantity_kg.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                          {percentage}%
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right">
                          ₹{channel.price_per_kg.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                          ₹{channel.revenue.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                            channel.priority === 1 ? 'bg-green-100 text-green-800' :
                            channel.priority === 2 ? 'bg-purple-100 text-purple-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {channel.priority}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan={2} className="px-4 py-3 text-sm font-semibold text-gray-900">
                    Total
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    {allocation.total_quantity_kg.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    100%
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    ₹{allocation.blended_realization_per_kg.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-900 text-right">
                    ₹{allocation.channel_allocations.reduce((sum, c) => sum + c.revenue, 0).toLocaleString()}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
