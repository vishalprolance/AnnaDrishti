import { useEffect, useState } from 'react';
import { DEMO_DATA } from '../config';

interface SurplusPanelProps {
  workflowId: string | null;
}

export default function SurplusPanel({ workflowId }: SurplusPanelProps) {
  const [showData, setShowData] = useState(false);

  useEffect(() => {
    if (!workflowId) {
      setShowData(false);
      return;
    }

    const timer = setTimeout(() => {
      setShowData(true);
    }, 3000);

    return () => clearTimeout(timer);
  }, [workflowId]);

  if (!showData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900">Surplus Detection</h2>
        <div className="mt-4 text-center py-8 text-gray-500">
          <p>Analyzing FPO volume...</p>
        </div>
      </div>
    );
  }

  const surplusPercentage = (DEMO_DATA.surplus.surplus / DEMO_DATA.surplus.total_volume) * 100;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Surplus Detection</h2>
        <p className="text-sm text-gray-600 mt-1">FPO-level volume analysis</p>
      </div>

      <div className="p-4 space-y-4">
        {/* Volume Breakdown */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-gray-600">Total Volume</p>
            <p className="text-lg font-bold text-gray-900">{(DEMO_DATA.surplus.total_volume / 1000).toFixed(1)}T</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg">
            <p className="text-xs text-gray-600">Mandi Capacity</p>
            <p className="text-lg font-bold text-gray-900">{(DEMO_DATA.surplus.mandi_capacity / 1000).toFixed(1)}T</p>
          </div>
          <div className="p-3 bg-red-50 rounded-lg">
            <p className="text-xs text-gray-600">Surplus</p>
            <p className="text-lg font-bold text-red-600">{(DEMO_DATA.surplus.surplus / 1000).toFixed(1)}T</p>
          </div>
        </div>

        {/* Surplus Alert */}
        <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-sm font-medium text-orange-900">Surplus Detected</p>
              <p className="text-xs text-orange-700 mt-1">
                {surplusPercentage.toFixed(0)}% surplus - Risk of price crash if sold to mandi
              </p>
            </div>
          </div>
        </div>

        {/* Recommended Split */}
        <div>
          <p className="text-sm font-medium text-gray-900 mb-2">Recommended Allocation:</p>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Fresh (Mandi)</span>
                <span>{(DEMO_DATA.surplus.fresh_allocation / 1000).toFixed(1)}T</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${(DEMO_DATA.surplus.fresh_allocation / DEMO_DATA.surplus.total_volume) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Processing</span>
                <span>{(DEMO_DATA.surplus.processing_allocation / 1000).toFixed(1)}T</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full"
                  style={{ width: `${(DEMO_DATA.surplus.processing_allocation / DEMO_DATA.surplus.total_volume) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Processors */}
        <div>
          <p className="text-sm font-medium text-gray-900 mb-2">Available Processors:</p>
          <div className="space-y-2">
            {DEMO_DATA.processors.map((processor, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div>
                  <p className="text-sm font-medium text-gray-900">{processor.name}</p>
                  <p className="text-xs text-gray-600">Capacity: {(processor.capacity / 1000).toFixed(1)}T</p>
                </div>
                <span className="text-sm font-bold text-green-600">₹{processor.rate}/kg</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
