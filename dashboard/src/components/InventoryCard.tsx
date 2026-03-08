import React from 'react';

interface InventoryBreakdown {
  fpo_id: string;
  crop_type: string;
  total_quantity_kg: string;
  available_quantity_kg: string;
  reserved_quantity_kg: string;
  allocated_quantity_kg: string;
  farmer_count: number;
  last_updated: string;
}

interface InventoryCardProps {
  cropType: string;
  inventory: InventoryBreakdown;
  onClick: () => void;
  isSelected: boolean;
}

export default function InventoryCard({ cropType, inventory, onClick, isSelected }: InventoryCardProps) {
  const totalQty = parseFloat(inventory.total_quantity_kg);
  const availableQty = parseFloat(inventory.available_quantity_kg);
  const reservedQty = parseFloat(inventory.reserved_quantity_kg);
  const allocatedQty = parseFloat(inventory.allocated_quantity_kg);

  // Calculate inventory level for color coding
  const availablePercentage = (availableQty / totalQty) * 100;
  
  const getInventoryLevelColor = () => {
    if (availablePercentage > 50) {
      return 'bg-green-100 border-green-300 text-green-800';
    } else if (availablePercentage > 20) {
      return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    } else {
      return 'bg-red-100 border-red-300 text-red-800';
    }
  };

  const getInventoryStatus = () => {
    if (availablePercentage > 50) {
      return { label: 'Healthy', color: 'text-green-600' };
    } else if (availablePercentage > 20) {
      return { label: 'Moderate', color: 'text-yellow-600' };
    } else {
      return { label: 'Low', color: 'text-red-600' };
    }
  };

  const status = getInventoryStatus();
  const lastUpdated = new Date(inventory.last_updated);
  const timeAgo = getTimeAgo(lastUpdated);

  return (
    <div
      onClick={onClick}
      className={`
        border-2 rounded-lg p-4 cursor-pointer transition-all
        ${isSelected ? 'ring-2 ring-green-500 border-green-500' : 'border-gray-200 hover:border-green-300'}
        ${getInventoryLevelColor()}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold capitalize">
          {cropType}
        </h3>
        <span className={`text-xs font-medium ${status.color}`}>
          {status.label}
        </span>
      </div>

      {/* Total Quantity */}
      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900">
          {totalQty.toLocaleString()}
          <span className="text-lg font-normal text-gray-600 ml-1">kg</span>
        </div>
        <div className="text-xs text-gray-600 mt-1">
          Total Inventory
        </div>
      </div>

      {/* Quantity Breakdown */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Available:</span>
          <span className="font-semibold text-green-700">
            {availableQty.toLocaleString()} kg
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Reserved:</span>
          <span className="font-semibold text-blue-700">
            {reservedQty.toLocaleString()} kg
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Allocated:</span>
          <span className="font-semibold text-purple-700">
            {allocatedQty.toLocaleString()} kg
          </span>
        </div>
      </div>

      {/* Visual Progress Bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div className="h-full flex">
            <div
              className="bg-green-500"
              style={{ width: `${(availableQty / totalQty) * 100}%` }}
              title={`Available: ${availablePercentage.toFixed(1)}%`}
            />
            <div
              className="bg-blue-500"
              style={{ width: `${(reservedQty / totalQty) * 100}%` }}
              title={`Reserved: ${((reservedQty / totalQty) * 100).toFixed(1)}%`}
            />
            <div
              className="bg-purple-500"
              style={{ width: `${(allocatedQty / totalQty) * 100}%` }}
              title={`Allocated: ${((allocatedQty / totalQty) * 100).toFixed(1)}%`}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-300">
        <span>{inventory.farmer_count} farmers</span>
        <span title={lastUpdated.toLocaleString()}>
          Updated {timeAgo}
        </span>
      </div>
    </div>
  );
}

// Helper function to calculate time ago
function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}
