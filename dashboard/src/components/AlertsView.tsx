import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config';

interface Alert {
  alert_id: string;
  alert_type: 'inventory_shortage' | 'unfulfilled_reservation';
  priority: 'high' | 'medium' | 'low';
  crop_type: string;
  message: string;
  details: {
    society_id?: string;
    society_name?: string;
    requested_quantity_kg?: number;
    available_quantity_kg?: number;
    shortage_kg?: number;
    reservation_id?: string;
    delivery_date?: string;
  };
  timestamp: string;
  status: 'active' | 'resolved' | 'acknowledged';
}

interface AlertsViewProps {
  fpoId: string;
}

export default function AlertsView({ fpoId }: AlertsViewProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved'>('active');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/api/alerts/${fpoId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch alerts');
        }
        
        const data = await response.json();
        setAlerts(data.alerts || []);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load alerts');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    
    // Poll for new alerts every 30 seconds
    const pollInterval = setInterval(fetchAlerts, 30000);
    
    return () => clearInterval(pollInterval);
  }, [fpoId]);

  const handleResolve = async (alertId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/resolve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to resolve alert');
      }
      
      // Update local state
      setAlerts(alerts.map(alert => 
        alert.alert_id === alertId 
          ? { ...alert, status: 'resolved' as const }
          : alert
      ));
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to acknowledge alert');
      }
      
      // Update local state
      setAlerts(alerts.map(alert => 
        alert.alert_id === alertId 
          ? { ...alert, status: 'acknowledged' as const }
          : alert
      ));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'inventory_shortage':
        return '⚠️';
      case 'unfulfilled_reservation':
        return '📋';
      default:
        return '🔔';
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'active') return alert.status === 'active' || alert.status === 'acknowledged';
    if (filter === 'resolved') return alert.status === 'resolved';
    return true;
  });

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading alerts...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading alerts</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Alerts</h2>
            <p className="text-sm text-gray-600 mt-1">
              {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}
            </p>
          </div>
          
          {/* Filter Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('active')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'active'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'resolved'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Resolved
            </button>
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'all'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
          </div>
        </div>
      </div>

      <div className="p-4">
        {filteredAlerts.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="font-semibold">No alerts</p>
            <p className="text-sm mt-1">
              {filter === 'active' ? 'All clear! No active alerts.' : 'No alerts found.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.alert_id}
                className={`border-2 rounded-lg p-4 ${getPriorityColor(alert.priority)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Alert Header */}
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{getAlertIcon(alert.alert_type)}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {alert.alert_type === 'inventory_shortage' 
                            ? 'Inventory Shortage' 
                            : 'Unfulfilled Reservation'}
                        </h3>
                        <p className="text-xs text-gray-600">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    {/* Alert Message */}
                    <p className="text-sm text-gray-800 mb-3">{alert.message}</p>

                    {/* Alert Details */}
                    <div className="bg-white bg-opacity-50 rounded p-3 text-sm space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Crop Type:</span>
                        <span className="font-medium capitalize">{alert.crop_type}</span>
                      </div>
                      
                      {alert.details.society_name && (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Society:</span>
                          <span className="font-medium">{alert.details.society_name}</span>
                        </div>
                      )}
                      
                      {alert.details.requested_quantity_kg !== undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Requested:</span>
                          <span className="font-medium">
                            {alert.details.requested_quantity_kg.toLocaleString()} kg
                          </span>
                        </div>
                      )}
                      
                      {alert.details.available_quantity_kg !== undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Available:</span>
                          <span className="font-medium">
                            {alert.details.available_quantity_kg.toLocaleString()} kg
                          </span>
                        </div>
                      )}
                      
                      {alert.details.shortage_kg !== undefined && (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Shortage:</span>
                          <span className="font-medium text-red-700">
                            {alert.details.shortage_kg.toLocaleString()} kg
                          </span>
                        </div>
                      )}
                      
                      {alert.details.delivery_date && (
                        <div className="flex items-center justify-between">
                          <span className="text-gray-600">Delivery Date:</span>
                          <span className="font-medium">
                            {new Date(alert.details.delivery_date).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Priority Badge */}
                  <div className="ml-4">
                    <span className={`px-2 py-1 text-xs font-bold uppercase rounded ${
                      alert.priority === 'high' ? 'bg-red-200 text-red-900' :
                      alert.priority === 'medium' ? 'bg-yellow-200 text-yellow-900' :
                      'bg-blue-200 text-blue-900'
                    }`}>
                      {alert.priority}
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                {alert.status === 'active' && (
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => handleAcknowledge(alert.alert_id)}
                      className="px-4 py-2 text-sm bg-white text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => handleResolve(alert.alert_id)}
                      className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Mark as Resolved
                    </button>
                  </div>
                )}
                
                {alert.status === 'acknowledged' && (
                  <div className="mt-4 flex gap-2">
                    <span className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      Acknowledged
                    </span>
                    <button
                      onClick={() => handleResolve(alert.alert_id)}
                      className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Mark as Resolved
                    </button>
                  </div>
                )}
                
                {alert.status === 'resolved' && (
                  <div className="mt-4">
                    <span className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded">
                      ✓ Resolved
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
