import { useState } from 'react';
import axios from 'axios';
import { API_URL, DEMO_DATA } from '../config';

interface DemoControlsProps {
  onWorkflowStart: (workflowId: string) => void;
}

export default function DemoControls({ onWorkflowStart }: DemoControlsProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startWorkflow = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_URL}/workflow/start`, DEMO_DATA.farmerInput);
      
      if (response.data.success) {
        onWorkflowStart(response.data.workflow_id);
      } else {
        setError('Failed to start workflow');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Demo Controls</h2>
          <p className="text-sm text-gray-600 mt-1">
            Start a new workflow for {DEMO_DATA.farmerInput.farmer_name}
          </p>
        </div>
        <button
          onClick={startWorkflow}
          disabled={loading}
          className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Starting...' : 'Start Demo Workflow'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
        <div>
          <span className="text-gray-600">Farmer:</span>
          <p className="font-medium">{DEMO_DATA.farmerInput.farmer_name}</p>
        </div>
        <div>
          <span className="text-gray-600">Crop:</span>
          <p className="font-medium capitalize">{DEMO_DATA.farmerInput.crop_type}</p>
        </div>
        <div>
          <span className="text-gray-600">Quantity:</span>
          <p className="font-medium">{DEMO_DATA.farmerInput.estimated_quantity} kg</p>
        </div>
        <div>
          <span className="text-gray-600">Location:</span>
          <p className="font-medium">{DEMO_DATA.farmerInput.location}</p>
        </div>
      </div>
    </div>
  );
}
