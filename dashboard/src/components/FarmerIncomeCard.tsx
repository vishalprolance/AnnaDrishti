import React from 'react';

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

interface FarmerIncomeCardProps {
  farmerIncome: FarmerIncome;
}

export default function FarmerIncomeCard({ farmerIncome }: FarmerIncomeCardProps) {
  const contribution = parseFloat(farmerIncome.contribution_kg);
  const totalRevenue = parseFloat(farmerIncome.total_revenue);
  const blendedRate = parseFloat(farmerIncome.blended_rate_per_kg);
  const improvement = parseFloat(farmerIncome.vs_best_single_channel.improvement);
  const improvementPercentage = parseFloat(farmerIncome.vs_best_single_channel.improvement_percentage);

  // Determine improvement color
  const getImprovementColor = () => {
    if (improvement > 0) {
      return 'text-green-600';
    } else if (improvement < 0) {
      return 'text-red-600';
    } else {
      return 'text-gray-600';
    }
  };

  // Get channel color
  const getChannelColor = (channel: string) => {
    switch (channel) {
      case 'society':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-purple-100 text-purple-800';
      case 'mandi':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="mb-4 pb-3 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 truncate" title={farmerIncome.farmer_id}>
          {farmerIncome.farmer_id}
        </h3>
        <div className="mt-1 text-sm text-gray-600">
          Contribution: {contribution.toLocaleString()} kg
        </div>
      </div>

      {/* Income Summary */}
      <div className="mb-4">
        <div className="text-2xl font-bold text-gray-900">
          ₹{totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Total Income
        </div>
        <div className="text-sm text-gray-500 mt-1">
          @ ₹{blendedRate.toFixed(2)}/kg (blended)
        </div>
      </div>

      {/* Channel Breakdown */}
      <div className="mb-4">
        <div className="text-xs font-medium text-gray-700 mb-2">Channel Breakdown</div>
        <div className="space-y-2">
          {farmerIncome.channel_breakdown.map((channel, index) => {
            const channelQty = parseFloat(channel.quantity_kg);
            const channelRevenue = parseFloat(channel.revenue);
            const channelRate = parseFloat(channel.rate_per_kg);

            return (
              <div key={index} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 flex-1">
                  <span className={`px-2 py-1 rounded font-medium ${getChannelColor(channel.channel)}`}>
                    {channel.channel}
                  </span>
                  <span className="text-gray-600">
                    {channelQty.toFixed(1)} kg
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-gray-900">
                    ₹{channelRevenue.toFixed(2)}
                  </div>
                  <div className="text-gray-500">
                    @ ₹{channelRate.toFixed(2)}/kg
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Improvement vs Single Channel */}
      <div className="pt-3 border-t border-gray-200">
        <div className="text-xs text-gray-600 mb-1">vs Best Single Channel</div>
        <div className={`text-sm font-semibold ${getImprovementColor()}`}>
          {improvement >= 0 ? '+' : ''}₹{improvement.toFixed(2)}
          {improvementPercentage !== 0 && (
            <span className="ml-1">
              ({improvement >= 0 ? '+' : ''}{improvementPercentage.toFixed(1)}%)
            </span>
          )}
        </div>
        {improvement > 0 && (
          <div className="text-xs text-green-600 mt-1">
            Better with collective selling
          </div>
        )}
        {improvement < 0 && (
          <div className="text-xs text-red-600 mt-1">
            Single channel would be better
          </div>
        )}
        {improvement === 0 && (
          <div className="text-xs text-gray-600 mt-1">
            Same as single channel
          </div>
        )}
      </div>
    </div>
  );
}
