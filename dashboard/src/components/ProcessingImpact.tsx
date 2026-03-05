import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ProcessingImpact() {
  const [scenario, setScenario] = useState<'without' | 'with'>('without');

  // Simulate 14 farmers in FPO
  const farmersWithout = Array.from({ length: 14 }, (_, i) => ({
    name: `F${i + 1}`,
    income: 35000 + Math.random() * 5000, // ₹35-40k
  }));

  const farmersWith = Array.from({ length: 14 }, (_, i) => ({
    name: `F${i + 1}`,
    income: 60000 + Math.random() * 8000, // ₹60-68k
  }));

  const data = scenario === 'without' ? farmersWithout : farmersWith;
  const totalIncome = data.reduce((sum, f) => sum + f.income, 0);
  const avgIncome = totalIncome / data.length;

  const totalWithout = 2100000; // ₹21 lakh
  const totalWith = 3400000; // ₹34 lakh
  const difference = totalWith - totalWithout;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Processing Impact</h2>
        <p className="text-sm text-gray-600 mt-1">FPO-level collective benefit (14 farmers)</p>
      </div>

      <div className="p-4 space-y-4">
        {/* Scenario Toggle */}
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => setScenario('without')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              scenario === 'without'
                ? 'bg-red-100 text-red-800 border-2 border-red-500'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Without Anna Drishti
          </button>
          <button
            onClick={() => setScenario('with')}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              scenario === 'with'
                ? 'bg-green-100 text-green-800 border-2 border-green-500'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            With Anna Drishti
          </button>
        </div>

        {/* Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number | undefined) => value ? `₹${value.toLocaleString('en-IN')}` : '₹0'}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar
                dataKey="income"
                fill={scenario === 'without' ? '#ef4444' : '#10b981'}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">Avg per Farmer</p>
            <p className="text-lg font-bold text-gray-900">
              ₹{avgIncome.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600">Total FPO Income</p>
            <p className="text-lg font-bold text-gray-900">
              ₹{(scenario === 'without' ? totalWithout : totalWith).toLocaleString('en-IN')}
            </p>
          </div>
        </div>

        {/* Comparison */}
        {scenario === 'with' && (
          <div className="p-4 bg-gradient-to-r from-green-500 to-green-600 rounded-lg text-white">
            <p className="text-sm font-medium opacity-90">Collective Benefit</p>
            <div className="text-2xl font-bold mt-1">
              +₹{(difference / 100000).toFixed(1)} Lakh
            </div>
            <p className="text-xs opacity-90 mt-1">
              {((difference / totalWithout) * 100).toFixed(0)}% increase for entire FPO
            </p>
          </div>
        )}

        {/* Explanation */}
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs font-medium text-blue-900 mb-1">
            {scenario === 'without' ? 'Without Processing:' : 'With Processing:'}
          </p>
          <p className="text-xs text-blue-800">
            {scenario === 'without'
              ? 'All 32T sold to mandi → Price crash → Lower income'
              : '22T fresh + 10T processing → No crash → Higher income'}
          </p>
        </div>
      </div>
    </div>
  );
}
