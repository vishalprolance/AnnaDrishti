import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface PaymentMetrics {
  total_workflows: number;
  payment_status_breakdown: {
    pending: number;
    confirmed: number;
    failed: number;
    delayed: number;
    no_payment_info: number;
  };
  total_amount_pending: number;
  total_amount_confirmed: number;
  total_amount_failed: number;
  delayed_payments: Array<{
    workflow_id: string;
    farmer_name: string;
    amount?: number;
    created_at: string;
    status: string;
  }>;
  recent_payments: Array<{
    workflow_id: string;
    farmer_name: string;
    amount: number;
    payment_date: string;
    transaction_id: string;
  }>;
}

export default function PaymentMetrics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['paymentMetrics'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/payments/metrics`);
      return response.data.metrics as PaymentMetrics;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Payment Tracking</h2>
        <div className="text-gray-500">Loading payment metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Payment Tracking</h2>
        <div className="text-red-500">Failed to load payment metrics</div>
      </div>
    );
  }

  if (!data) return null;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Payment Tracking</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">Confirmed</div>
          <div className="text-2xl font-bold text-green-700 mt-1">
            {formatCurrency(data.total_amount_confirmed)}
          </div>
          <div className="text-xs text-green-600 mt-1">
            {data.payment_status_breakdown.confirmed} payments
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="text-sm text-yellow-600 font-medium">Pending</div>
          <div className="text-2xl font-bold text-yellow-700 mt-1">
            {formatCurrency(data.total_amount_pending)}
          </div>
          <div className="text-xs text-yellow-600 mt-1">
            {data.payment_status_breakdown.pending} payments
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium">Delayed</div>
          <div className="text-2xl font-bold text-red-700 mt-1">
            {data.delayed_payments.length}
          </div>
          <div className="text-xs text-red-600 mt-1">
            {'>'}48 hours overdue
          </div>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Payment Status</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">Confirmed</span>
            </div>
            <span className="text-sm font-medium">{data.payment_status_breakdown.confirmed}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">Pending</span>
            </div>
            <span className="text-sm font-medium">{data.payment_status_breakdown.pending}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">Delayed</span>
            </div>
            <span className="text-sm font-medium">{data.delayed_payments.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">No Info</span>
            </div>
            <span className="text-sm font-medium">{data.payment_status_breakdown.no_payment_info}</span>
          </div>
        </div>
      </div>

      {/* Delayed Payments Alert */}
      {data.delayed_payments.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-red-700 mb-3 flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Delayed Payments ({data.delayed_payments.length})
          </h3>
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 max-h-48 overflow-y-auto">
            <div className="space-y-2">
              {data.delayed_payments.slice(0, 5).map((payment) => (
                <div key={payment.workflow_id} className="flex items-center justify-between text-sm">
                  <div>
                    <div className="font-medium text-gray-900">{payment.farmer_name}</div>
                    <div className="text-xs text-gray-500">
                      Created: {formatDate(payment.created_at)}
                    </div>
                  </div>
                  {payment.amount && (
                    <div className="text-red-700 font-medium">
                      {formatCurrency(payment.amount)}
                    </div>
                  )}
                </div>
              ))}
              {data.delayed_payments.length > 5 && (
                <div className="text-xs text-gray-500 text-center pt-2">
                  +{data.delayed_payments.length - 5} more delayed payments
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recent Payments */}
      {data.recent_payments.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Payments</h3>
          <div className="space-y-2">
            {data.recent_payments.slice(0, 3).map((payment) => (
              <div key={payment.workflow_id} className="flex items-center justify-between text-sm border-b border-gray-100 pb-2">
                <div>
                  <div className="font-medium text-gray-900">{payment.farmer_name}</div>
                  <div className="text-xs text-gray-500">
                    {formatDate(payment.payment_date)} • {payment.transaction_id}
                  </div>
                </div>
                <div className="text-green-700 font-medium">
                  {formatCurrency(payment.amount)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
