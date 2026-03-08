import React from 'react';

interface ChannelAllocation {
  channel_type: string;
  channel_id: string;
  channel_name: string;
  quantity_kg: number;
  price_per_kg: number;
  revenue: number;
  priority: number;
}

interface ChannelBreakdownCardProps {
  channel: ChannelAllocation;
  totalQuantity: number;
  totalRevenue: number;
}

export default function ChannelBreakdownCard({
  channel,
  totalQuantity,
  totalRevenue,
}: ChannelBreakdownCardProps) {
  // Calculate percentages
  const quantityPercentage = ((channel.quantity_kg / totalQuantity) * 100).toFixed(1);
  const revenuePercentage = ((channel.revenue / totalRevenue) * 100).toFixed(1);

  // Get channel-specific colors
  const getChannelColors = (channelType: string) => {
    switch (channelType) {
      case 'society':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-600',
          textDark: 'text-blue-900',
          badge: 'bg-blue-100 text-blue-800',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
          ),
        };
      case 'processing':
        return {
          bg: 'bg-purple-50',
          border: 'border-purple-200',
          text: 'text-purple-600',
          textDark: 'text-purple-900',
          badge: 'bg-purple-100 text-purple-800',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd" />
            </svg>
          ),
        };
      case 'mandi':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          text: 'text-orange-600',
          textDark: 'text-orange-900',
          badge: 'bg-orange-100 text-orange-800',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3zM16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
            </svg>
          ),
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-600',
          textDark: 'text-gray-900',
          badge: 'bg-gray-100 text-gray-800',
          icon: (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm3 1h6v4H7V5zm6 6H7v2h6v-2z" clipRule="evenodd" />
            </svg>
          ),
        };
    }
  };

  const colors = getChannelColors(channel.channel_type);

  return (
    <div className={`${colors.bg} rounded-lg p-4 border ${colors.border} hover:shadow-md transition-shadow`}>
      {/* Header with Icon and Channel Type */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={colors.text}>
            {colors.icon}
          </div>
          <span className={`px-2 py-1 rounded text-xs font-semibold ${colors.badge} capitalize`}>
            {channel.channel_type}
          </span>
        </div>
        <div className={`text-xs font-bold ${colors.text}`}>
          Priority {channel.priority}
        </div>
      </div>

      {/* Channel Name */}
      <div className="mb-3">
        <div className={`text-sm font-semibold ${colors.textDark} truncate`} title={channel.channel_name}>
          {channel.channel_name}
        </div>
      </div>

      {/* Quantity */}
      <div className="mb-3">
        <div className={`text-xs ${colors.text} font-medium mb-1`}>Quantity</div>
        <div className={`text-2xl font-bold ${colors.textDark}`}>
          {channel.quantity_kg.toLocaleString()}
          <span className={`text-sm font-normal ${colors.text} ml-1`}>kg</span>
        </div>
        <div className={`text-xs ${colors.text} mt-1`}>
          {quantityPercentage}% of total
        </div>
      </div>

      {/* Revenue */}
      <div className="mb-3 pb-3 border-b" style={{ borderColor: colors.border.replace('border-', '') }}>
        <div className={`text-xs ${colors.text} font-medium mb-1`}>Revenue</div>
        <div className={`text-xl font-bold ${colors.textDark}`}>
          ₹{channel.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className={`text-xs ${colors.text} mt-1`}>
          {revenuePercentage}% of total
        </div>
      </div>

      {/* Rate */}
      <div>
        <div className={`text-xs ${colors.text} font-medium mb-1`}>Rate per kg</div>
        <div className={`text-lg font-bold ${colors.textDark}`}>
          ₹{channel.price_per_kg.toFixed(2)}
        </div>
      </div>

      {/* Visual Percentage Bar */}
      <div className="mt-3">
        <div className="w-full bg-white rounded-full h-2 overflow-hidden">
          <div
            className={`h-full ${colors.badge.split(' ')[0]} transition-all duration-300`}
            style={{ width: `${quantityPercentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}
