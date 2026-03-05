import { useEffect, useState } from 'react';

interface Activity {
  id: string;
  timestamp: string;
  agent: 'sell' | 'process' | 'system';
  action: string;
  details?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

interface ActivityStreamProps {
  workflowId: string | null;
}

export default function ActivityStream({ workflowId }: ActivityStreamProps) {
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    if (!workflowId) {
      setActivities([]);
      return;
    }

    // Simulate activity stream for demo
    const demoActivities: Activity[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        agent: 'system',
        action: 'Workflow Started',
        details: 'Processing farmer input for Ramesh Patil',
        status: 'completed',
      },
      {
        id: '2',
        timestamp: new Date(Date.now() + 1000).toISOString(),
        agent: 'system',
        action: 'Market Scan Initiated',
        details: 'Scanning 4 mandis for tomato prices',
        status: 'in_progress',
      },
    ];

    setActivities(demoActivities);

    // Simulate progressive updates
    const timer1 = setTimeout(() => {
      setActivities(prev => [
        ...prev.map(a => a.id === '2' ? { ...a, status: 'completed' as const } : a),
        {
          id: '3',
          timestamp: new Date().toISOString(),
          agent: 'sell',
          action: 'Surplus Detected',
          details: '10,000 kg surplus identified',
          status: 'completed',
        },
      ]);
    }, 2000);

    const timer2 = setTimeout(() => {
      setActivities(prev => [
        ...prev,
        {
          id: '4',
          timestamp: new Date().toISOString(),
          agent: 'process',
          action: 'Processing Allocation',
          details: 'Diverting surplus to processors',
          status: 'completed',
        },
      ]);
    }, 4000);

    const timer3 = setTimeout(() => {
      setActivities(prev => [
        ...prev,
        {
          id: '5',
          timestamp: new Date().toISOString(),
          agent: 'sell',
          action: 'Negotiation Started',
          details: 'AI agent negotiating with buyers',
          status: 'in_progress',
        },
      ]);
    }, 6000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [workflowId]);

  const getAgentColor = (agent: Activity['agent']) => {
    switch (agent) {
      case 'sell':
        return 'bg-blue-100 text-blue-800';
      case 'process':
        return 'bg-green-100 text-green-800';
      case 'system':
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: Activity['status']) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⟳';
      case 'failed':
        return '✗';
      case 'pending':
        return '○';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Activity Stream</h2>
        <p className="text-sm text-gray-600 mt-1">Real-time workflow updates</p>
      </div>

      <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
        {activities.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No active workflow</p>
            <p className="text-sm mt-1">Start a demo workflow to see activity</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0 mt-1">
                <span className="text-lg">{getStatusIcon(activity.status)}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${getAgentColor(activity.agent)}`}>
                    {activity.agent.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-900 mt-1">{activity.action}</p>
                {activity.details && (
                  <p className="text-sm text-gray-600 mt-0.5">{activity.details}</p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
