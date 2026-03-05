import { useEffect, useState } from 'react';
import { DEMO_DATA } from '../config';

interface IncomeComparisonProps {
  workflowId: string | null;
}

export default function IncomeComparison({ workflowId }: IncomeComparisonProps) {
  const [showData, setShowData] = useState(false);

  useEffect(() => {
    if (!workflowId) {
      setShowData(false);
      return;
    }

    const timer = setTimeout(() => {
      setShowData(true);
    }, 17000); // Show after negotiation completes

    return () => clearTimeout(timer);
  }, [workflowId]);

  if (!showData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900">Income Comparison</h2>
        <div className="mt-4 text-center py-8 text-gray-500">
          <p>Calculating income...</p>
        </div>
      </div>
    );
  }

  // Calculate incomes
  const quantity = DEMO_DATA.farmerInput.estimated_quantity;
  const nearestMandiPrice = Math.max(...DEMO_DATA.marketPrices.map(m => m.net_price));
  const mandiIncome = quantity * nearestMandiPrice;

  // Anna Drishti: 22kg fresh at negotiated price + 10kg processing at avg processor rate
  const freshQty = (quantity * DEMO_DATA.surplus.fresh_allocation) / DEMO_DATA.surplus.total_volume;
  const processingQty = (quantity * DEMO_DATA.surplus.processing_allocation) / DEMO_DATA.surplus.total_volume;
  const avgProcessorRate = DEMO_DATA.processors.reduce((sum, p) => sum + p.rate, 0) / DEMO_DATA.processors.length;
  const annaDrishtiIncome = (freshQty * DEMO_DATA.negotiation.final_price) + (processingQty * avgProcessorRate);

  const difference = annaDrishtiIncome - mandiIncome;
  const percentageIncrease = ((difference / mandiIncome) * 100).toFixed(0);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Income Comparison</h2>
        <p className="text-sm text-gray-600 mt-1">For {DEMO_DATA.farmerInput.farmer_name}</p>
      </div>

      <div className="p-4 space-y-4">
        {/* Nearest Mandi */}
        <div className="p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Nearest Mandi</span>
            <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded">
              Traditional
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            ₹{mandiIncome.toLocaleString('en-IN')}
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {quantity} kg × ₹{nearestMandiPrice}/kg
          </p>
        </div>

        {/* Anna Drishti */}
        <div className="p-4 bg-green-50 rounded-lg border-2 border-green-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-green-900">Anna Drishti</span>
            <span className="px-2 py-1 bg-green-200 text-green-800 text-xs font-medium rounded">
              AI-Assisted
            </span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            ₹{annaDrishtiIncome.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-green-700 mt-1 space-y-0.5">
            <p>{freshQty.toFixed(0)} kg fresh × ₹{DEMO_DATA.negotiation.final_price}/kg</p>
            <p>{processingQty.toFixed(0)} kg processing × ₹{avgProcessorRate.toFixed(0)}/kg</p>
          </div>
        </div>

        {/* Difference */}
        <div className="p-4 bg-gradient-to-r from-green-500 to-green-600 rounded-lg text-white">
          <p className="text-sm font-medium opacity-90">Additional Income</p>
          <div className="text-3xl font-bold mt-1">
            +₹{difference.toLocaleString('en-IN')}
          </div>
          <p className="text-sm opacity-90 mt-1">
            {percentageIncrease}% increase
          </p>
        </div>

        {/* Breakdown */}
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs font-medium text-blue-900 mb-2">How Anna Drishti Helps:</p>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>✓ AI negotiation for better prices</li>
            <li>✓ Surplus diverted to processing</li>
            <li>✓ Prevents market crash</li>
            <li>✓ Collective bargaining power</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
