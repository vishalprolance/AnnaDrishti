import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SatelliteDataProps {
  workflowId: string | null;
}

interface NDVIPoint {
  date: string;
  ndvi: number;
  status: string;
  color: string;
  cloud_cover: number;
}

interface CropHealth {
  score: number;
  status: string;
  trend: string;
  latest_ndvi: number;
}

interface SatelliteData {
  location: {
    lat: number;
    lon: number;
  };
  ndvi_time_series: NDVIPoint[];
  crop_health: CropHealth;
  last_updated: string;
  data_source: string;
  note: string;
}

export default function SatelliteData({ workflowId }: SatelliteDataProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['satelliteData', workflowId],
    queryFn: async () => {
      if (!workflowId) return null;
      const response = await axios.post(`${API_BASE_URL}/satellite`, {
        workflow_id: workflowId,
      });
      return response.data.satellite_data as SatelliteData;
    },
    enabled: !!workflowId,
    refetchInterval: 60000, // Refresh every minute
  });

  if (!workflowId) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Satellite Data
        </h2>
        <div className="text-gray-500 text-sm">
          Start a workflow to view satellite crop health data
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Satellite Data
        </h2>
        <div className="text-gray-500">Loading satellite data...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Satellite Data
        </h2>
        <div className="text-red-500">Failed to load satellite data</div>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'text-green-700 bg-green-100';
      case 'good':
        return 'text-lime-700 bg-lime-100';
      case 'moderate':
        return 'text-yellow-700 bg-yellow-100';
      case 'poor':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') {
      return (
        <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      );
    } else if (trend === 'declining') {
      return (
        <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return (
        <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Satellite Data
        <span className="ml-2 text-xs text-gray-500 font-normal">Sentinel-2</span>
      </h2>

      {/* Crop Health Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Crop Health Score</span>
          <div className="flex items-center space-x-2">
            {getTrendIcon(data.crop_health.trend)}
            <span className="text-xs text-gray-600 capitalize">{data.crop_health.trend}</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-4xl font-bold text-gray-900">{data.crop_health.score}</div>
          <div className="flex-1">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full ${
                  data.crop_health.score >= 70
                    ? 'bg-green-500'
                    : data.crop_health.score >= 50
                    ? 'bg-lime-500'
                    : data.crop_health.score >= 30
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${data.crop_health.score}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Poor</span>
              <span>Excellent</span>
            </div>
          </div>
        </div>
        <div className="mt-2">
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium capitalize ${getHealthColor(data.crop_health.status)}`}>
            {data.crop_health.status}
          </span>
        </div>
      </div>

      {/* NDVI Chart */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">NDVI Trend (30 Days)</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data.ndvi_time_series}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              labelFormatter={(value) => `Date: ${value}`}
              formatter={(value: number | undefined) => value !== undefined ? [`${value.toFixed(3)}`, 'NDVI'] : ['', 'NDVI']}
            />
            <Line
              type="monotone"
              dataKey="ndvi"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ fill: '#22c55e', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Latest NDVI */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Latest NDVI</span>
          <span className="font-medium">{data.crop_health.latest_ndvi.toFixed(3)}</span>
        </div>
        <div className="flex items-center justify-between text-sm mt-2">
          <span className="text-gray-600">Location</span>
          <span className="font-medium">
            {data.location.lat.toFixed(4)}°N, {data.location.lon.toFixed(4)}°E
          </span>
        </div>
      </div>

      {/* Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start">
          <svg className="w-4 h-4 text-blue-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <p className="text-xs text-blue-800">{data.note}</p>
        </div>
      </div>
    </div>
  );
}
