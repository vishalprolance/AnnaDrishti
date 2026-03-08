import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

interface ReportFilters {
  startDate: string;
  endDate: string;
  cropType: string;
  channel: string;
}

interface AllocationReport {
  allocation_id: string;
  allocation_date: string;
  crop_type: string;
  total_quantity_kg: number;
  blended_realization_per_kg: number;
  total_revenue: number;
  channel_breakdown: {
    channel_type: string;
    channel_name: string;
    quantity_kg: number;
    price_per_kg: number;
    revenue: number;
  }[];
}

interface ReportsViewProps {
  fpoId: string;
}

export default function ReportsView({ fpoId }: ReportsViewProps) {
  const [filters, setFilters] = useState<ReportFilters>({
    startDate: getDefaultStartDate(),
    endDate: getDefaultEndDate(),
    cropType: 'all',
    channel: 'all',
  });
  
  const [reports, setReports] = useState<AllocationReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cropTypes, setCropTypes] = useState<string[]>([]);

  // Fetch available crop types
  useEffect(() => {
    const fetchCropTypes = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/inventory/${fpoId}/summary`);
        if (response.ok) {
          const data = await response.json();
          setCropTypes(data.crop_types || []);
        }
      } catch (err) {
        console.error('Failed to fetch crop types:', err);
      }
    };

    fetchCropTypes();
  }, [fpoId]);

  // Fetch reports based on filters
  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const params = new URLSearchParams({
          start_date: filters.startDate,
          end_date: filters.endDate,
        });
        
        if (filters.cropType !== 'all') {
          params.append('crop_type', filters.cropType);
        }
        
        if (filters.channel !== 'all') {
          params.append('channel', filters.channel);
        }
        
        const response = await fetch(
          `${API_BASE_URL}/api/allocations/${fpoId}/history?${params.toString()}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch reports');
        }
        
        const data = await response.json();
        setReports(data.allocations || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [fpoId, filters]);

  const handleFilterChange = (field: keyof ReportFilters, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleExportCSV = () => {
    if (reports.length === 0) {
      alert('No data to export');
      return;
    }

    // Generate CSV content
    const headers = [
      'Allocation ID',
      'Date',
      'Crop Type',
      'Total Quantity (kg)',
      'Blended Rate (₹/kg)',
      'Total Revenue (₹)',
      'Channel',
      'Channel Name',
      'Channel Quantity (kg)',
      'Channel Price (₹/kg)',
      'Channel Revenue (₹)',
    ];

    const rows = reports.flatMap(report =>
      report.channel_breakdown.map(channel => [
        report.allocation_id,
        new Date(report.allocation_date).toLocaleDateString(),
        report.crop_type,
        report.total_quantity_kg,
        report.blended_realization_per_kg.toFixed(2),
        report.total_revenue.toFixed(2),
        channel.channel_type,
        channel.channel_name,
        channel.quantity_kg,
        channel.price_per_kg.toFixed(2),
        channel.revenue.toFixed(2),
      ])
    );

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
    ].join('\n');

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `allocation_report_${filters.startDate}_to_${filters.endDate}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Calculate summary statistics
  const summary = reports.reduce(
    (acc, report) => ({
      totalQuantity: acc.totalQuantity + report.total_quantity_kg,
      totalRevenue: acc.totalRevenue + report.total_revenue,
      societyQuantity: acc.societyQuantity + report.channel_breakdown
        .filter(c => c.channel_type === 'society')
        .reduce((sum, c) => sum + c.quantity_kg, 0),
      processingQuantity: acc.processingQuantity + report.channel_breakdown
        .filter(c => c.channel_type === 'processing')
        .reduce((sum, c) => sum + c.quantity_kg, 0),
      mandiQuantity: acc.mandiQuantity + report.channel_breakdown
        .filter(c => c.channel_type === 'mandi')
        .reduce((sum, c) => sum + c.quantity_kg, 0),
    }),
    {
      totalQuantity: 0,
      totalRevenue: 0,
      societyQuantity: 0,
      processingQuantity: 0,
      mandiQuantity: 0,
    }
  );

  const avgBlendedRate = summary.totalQuantity > 0 
    ? summary.totalRevenue / summary.totalQuantity 
    : 0;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Allocation Reports</h2>
        <p className="text-sm text-gray-600 mt-1">
          Filter and export allocation data
        </p>
      </div>

      <div className="p-4">
        {/* Filters */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Filters</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Start Date */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-green-500 focus:border-green-500"
              />
            </div>

            {/* Crop Type */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Crop Type
              </label>
              <select
                value={filters.cropType}
                onChange={(e) => handleFilterChange('cropType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-green-500 focus:border-green-500"
              >
                <option value="all">All Crops</option>
                {cropTypes.map(crop => (
                  <option key={crop} value={crop} className="capitalize">
                    {crop}
                  </option>
                ))}
              </select>
            </div>

            {/* Channel */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Channel
              </label>
              <select
                value={filters.channel}
                onChange={(e) => handleFilterChange('channel', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-green-500 focus:border-green-500"
              >
                <option value="all">All Channels</option>
                <option value="society">Society</option>
                <option value="processing">Processing</option>
                <option value="mandi">Mandi</option>
              </select>
            </div>
          </div>

          {/* Export Button */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleExportCSV}
              disabled={reports.length === 0}
              className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <span>📥</span>
              Export CSV
            </button>
          </div>
        </div>

        {/* Summary Statistics */}
        {!loading && reports.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="text-sm text-blue-600 font-medium mb-1">Total Quantity</div>
              <div className="text-2xl font-bold text-blue-900">
                {summary.totalQuantity.toLocaleString()}
                <span className="text-sm font-normal ml-1">kg</span>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="text-sm text-green-600 font-medium mb-1">Total Revenue</div>
              <div className="text-2xl font-bold text-green-900">
                ₹{summary.totalRevenue.toLocaleString()}
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="text-sm text-purple-600 font-medium mb-1">Avg Blended Rate</div>
              <div className="text-2xl font-bold text-purple-900">
                ₹{avgBlendedRate.toFixed(2)}
                <span className="text-sm font-normal ml-1">/kg</span>
              </div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <div className="text-sm text-orange-600 font-medium mb-1">Allocations</div>
              <div className="text-2xl font-bold text-orange-900">
                {reports.length}
              </div>
            </div>
          </div>
        )}

        {/* Channel Distribution */}
        {!loading && reports.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Channel Distribution</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Society:</span>
                <span className="font-semibold text-blue-700">
                  {summary.societyQuantity.toLocaleString()} kg
                  <span className="text-xs text-gray-500 ml-1">
                    ({summary.totalQuantity > 0 
                      ? ((summary.societyQuantity / summary.totalQuantity) * 100).toFixed(1) 
                      : 0}%)
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Processing:</span>
                <span className="font-semibold text-purple-700">
                  {summary.processingQuantity.toLocaleString()} kg
                  <span className="text-xs text-gray-500 ml-1">
                    ({summary.totalQuantity > 0 
                      ? ((summary.processingQuantity / summary.totalQuantity) * 100).toFixed(1) 
                      : 0}%)
                  </span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Mandi:</span>
                <span className="font-semibold text-green-700">
                  {summary.mandiQuantity.toLocaleString()} kg
                  <span className="text-xs text-gray-500 ml-1">
                    ({summary.totalQuantity > 0 
                      ? ((summary.mandiQuantity / summary.totalQuantity) * 100).toFixed(1) 
                      : 0}%)
                  </span>
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
            <span className="ml-3 text-gray-600">Loading reports...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center text-red-600 py-8">
            <p className="font-semibold">Error loading reports</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && reports.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <p className="font-semibold">No reports found</p>
            <p className="text-sm mt-1">
              Try adjusting your filters or date range
            </p>
          </div>
        )}

        {/* Reports Table */}
        {!loading && !error && reports.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Crop Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity (kg)
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Blended Rate
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channels
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reports.map((report) => (
                  <tr key={report.allocation_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {new Date(report.allocation_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 capitalize">
                      {report.crop_type}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {report.total_quantity_kg.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      ₹{report.blended_realization_per_kg.toFixed(2)}/kg
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-green-700">
                      ₹{report.total_revenue.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      <div className="flex flex-wrap gap-1">
                        {report.channel_breakdown.map((channel, idx) => (
                          <span
                            key={idx}
                            className={`px-2 py-1 text-xs rounded ${
                              channel.channel_type === 'society' ? 'bg-blue-100 text-blue-800' :
                              channel.channel_type === 'processing' ? 'bg-purple-100 text-purple-800' :
                              'bg-green-100 text-green-800'
                            }`}
                          >
                            {channel.channel_type}: {channel.quantity_kg.toLocaleString()}kg
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper functions
function getDefaultStartDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 30); // 30 days ago
  return date.toISOString().split('T')[0];
}

function getDefaultEndDate(): string {
  const date = new Date();
  return date.toISOString().split('T')[0];
}
