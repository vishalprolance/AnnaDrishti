import React from 'react';

interface DeliveryScheduleItem {
  reservation_id: string;
  society_id: string;
  society_name: string;
  crop_type: string;
  reserved_quantity_kg: string;
  delivery_date: string;
  delivery_time_window: string;
  status: string;
}

interface DeliveryCardProps {
  delivery: DeliveryScheduleItem;
  onConfirm: () => void;
}

export default function DeliveryCard({ delivery, onConfirm }: DeliveryCardProps) {
  const quantity = parseFloat(delivery.reserved_quantity_kg);
  const deliveryDate = new Date(delivery.delivery_date);
  
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'predicted':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'confirmed':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'fulfilled':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status.toLowerCase()) {
      case 'predicted':
        return 'Predicted';
      case 'confirmed':
        return 'Confirmed';
      case 'fulfilled':
        return 'Fulfilled';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  };

  const canConfirm = delivery.status.toLowerCase() === 'predicted';

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="text-base font-semibold text-gray-900">
            {delivery.society_name}
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            {delivery.crop_type.charAt(0).toUpperCase() + delivery.crop_type.slice(1)}
          </p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded border ${getStatusColor(delivery.status)}`}>
          {getStatusLabel(delivery.status)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Quantity</p>
          <p className="text-lg font-semibold text-gray-900">
            {quantity.toLocaleString()}
            <span className="text-sm font-normal text-gray-600 ml-1">kg</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Delivery Date</p>
          <p className="text-sm font-medium text-gray-900">
            {deliveryDate.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric',
              year: 'numeric'
            })}
          </p>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">Time Window</p>
        <div className="flex items-center text-sm text-gray-900">
          <svg className="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {delivery.delivery_time_window}
        </div>
      </div>

      {canConfirm && (
        <div className="flex gap-2 pt-3 border-t border-gray-200">
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            Confirm Order
          </button>
          <button
            className="px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-md border border-gray-300 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Edit
          </button>
        </div>
      )}

      {delivery.status.toLowerCase() === 'confirmed' && (
        <div className="pt-3 border-t border-gray-200">
          <button
            className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            View Details
          </button>
        </div>
      )}
    </div>
  );
}
