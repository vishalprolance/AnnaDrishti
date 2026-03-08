import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config';
import DeliveryCard from './DeliveryCard';

interface Reservation {
  reservation_id: string;
  society_id: string;
  crop_type: string;
  reserved_quantity_kg: string;
  reservation_timestamp: string;
  delivery_date: string;
  status: string;
}

interface SocietyProfile {
  society_id: string;
  society_name: string;
  location: string;
  delivery_address: string;
  preferred_day: string;
  preferred_time_window: string;
}

interface DeliveryScheduleItem extends Reservation {
  society_name: string;
  delivery_time_window: string;
}

interface SocietyScheduleViewProps {
  fpoId: string;
}

export default function SocietyScheduleView({ fpoId }: SocietyScheduleViewProps) {
  const [deliveries, setDeliveries] = useState<DeliveryScheduleItem[]>([]);
  const [societies, setSocieties] = useState<Record<string, SocietyProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  // Initialize date range to next 7 days
  useEffect(() => {
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    
    setDateRange({
      start: today.toISOString().split('T')[0],
      end: nextWeek.toISOString().split('T')[0],
    });
  }, []);

  // Fetch societies and reservations
  useEffect(() => {
    if (!dateRange.start || !dateRange.end) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch societies
        const societiesResponse = await fetch(`${API_BASE_URL}/api/societies`);
        if (!societiesResponse.ok) {
          throw new Error('Failed to fetch societies');
        }
        const societiesData = await societiesResponse.json();
        
        // Create society lookup map
        const societyMap: Record<string, SocietyProfile> = {};
        societiesData.societies.forEach((society: SocietyProfile) => {
          societyMap[society.society_id] = society;
        });
        setSocieties(societyMap);
        
        // Fetch reservations
        const reservationsResponse = await fetch(
          `${API_BASE_URL}/api/demand/reservations?start_date=${dateRange.start}&end_date=${dateRange.end}`
        );
        if (!reservationsResponse.ok) {
          throw new Error('Failed to fetch reservations');
        }
        const reservationsData = await reservationsResponse.json();
        
        // Combine reservation data with society info
        const deliverySchedule: DeliveryScheduleItem[] = reservationsData.reservations.map(
          (reservation: Reservation) => ({
            ...reservation,
            society_name: societyMap[reservation.society_id]?.society_name || 'Unknown Society',
            delivery_time_window: societyMap[reservation.society_id]?.preferred_time_window || 'TBD',
          })
        );
        
        // Sort by delivery date
        deliverySchedule.sort((a, b) => 
          new Date(a.delivery_date).getTime() - new Date(b.delivery_date).getTime()
        );
        
        setDeliveries(deliverySchedule);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load schedule');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [fpoId, dateRange]);

  // Group deliveries by date
  const deliveriesByDate = deliveries.reduce((acc, delivery) => {
    const date = delivery.delivery_date;
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(delivery);
    return acc;
  }, {} as Record<string, DeliveryScheduleItem[]>);

  // Get unique dates for calendar
  const dates = Object.keys(deliveriesByDate).sort();

  // Filter deliveries by selected date
  const filteredDeliveries = selectedDate 
    ? deliveriesByDate[selectedDate] || []
    : deliveries;

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-3 text-gray-600">Loading schedule...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading schedule</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Society Delivery Schedule</h2>
        <p className="text-sm text-gray-600 mt-1">
          Upcoming deliveries for {deliveries.length} reservation{deliveries.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Date Range Filter */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="start-date" className="block text-xs font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={dateRange.start}
              onChange={(e) => handleDateRangeChange('start', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="flex-1">
            <label htmlFor="end-date" className="block text-xs font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={dateRange.end}
              onChange={(e) => handleDateRangeChange('end', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>
      </div>

      <div className="p-4">
        {deliveries.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="font-semibold">No deliveries scheduled</p>
            <p className="text-sm mt-1">No reservations found for the selected date range</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Calendar View */}
            <div className="lg:col-span-1">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Calendar</h3>
              <div className="space-y-2">
                <button
                  onClick={() => setSelectedDate(null)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selectedDate === null
                      ? 'bg-green-100 text-green-800 font-medium'
                      : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  All Dates ({deliveries.length})
                </button>
                {dates.map((date) => {
                  const count = deliveriesByDate[date].length;
                  const dateObj = new Date(date);
                  const isSelected = selectedDate === date;
                  
                  return (
                    <button
                      key={date}
                      onClick={() => setSelectedDate(date)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                        isSelected
                          ? 'bg-green-100 text-green-800 font-medium'
                          : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">
                            {dateObj.toLocaleDateString('en-US', { 
                              weekday: 'short', 
                              month: 'short', 
                              day: 'numeric' 
                            })}
                          </div>
                          <div className="text-xs text-gray-500">
                            {count} delivery{count !== 1 ? 'ies' : ''}
                          </div>
                        </div>
                        {isSelected && (
                          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Delivery Cards */}
            <div className="lg:col-span-2">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                {selectedDate 
                  ? `Deliveries for ${new Date(selectedDate).toLocaleDateString('en-US', { 
                      weekday: 'long', 
                      month: 'long', 
                      day: 'numeric' 
                    })}`
                  : 'All Upcoming Deliveries'
                }
              </h3>
              <div className="space-y-3">
                {filteredDeliveries.map((delivery) => (
                  <DeliveryCard
                    key={delivery.reservation_id}
                    delivery={delivery}
                    onConfirm={() => {
                      // Handle confirmation
                      console.log('Confirm delivery:', delivery.reservation_id);
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
