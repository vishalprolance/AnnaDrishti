import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import AlertsView from '../AlertsView';

// Mock fetch
global.fetch = vi.fn();

describe('AlertsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  const mockAlerts = {
    alerts: [
      {
        alert_id: 'alert-001',
        alert_type: 'inventory_shortage',
        priority: 'high',
        crop_type: 'tomato',
        message: 'Insufficient inventory to fulfill all society reservations',
        details: {
          society_id: 'soc-001',
          society_name: 'Green Valley Apartments',
          requested_quantity_kg: 500,
          available_quantity_kg: 300,
          shortage_kg: 200,
          delivery_date: '2026-03-15',
        },
        timestamp: '2026-03-08T10:00:00Z',
        status: 'active',
      },
      {
        alert_id: 'alert-002',
        alert_type: 'unfulfilled_reservation',
        priority: 'medium',
        crop_type: 'onion',
        message: 'Reservation could not be fully allocated',
        details: {
          society_id: 'soc-002',
          society_name: 'Sunrise Society',
          requested_quantity_kg: 300,
          available_quantity_kg: 150,
          shortage_kg: 150,
          reservation_id: 'res-002',
          delivery_date: '2026-03-10',
        },
        timestamp: '2026-03-07T15:30:00Z',
        status: 'acknowledged',
      },
    ],
  };

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<AlertsView fpoId="fpo-001" />);
    
    expect(screen.getByText('Loading alerts...')).toBeInTheDocument();
  });

  it('should fetch and display alerts', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
      expect(screen.getByText('Unfulfilled Reservation')).toBeInTheDocument();
    });

    expect(screen.getByText('Green Valley Apartments')).toBeInTheDocument();
    expect(screen.getByText('Sunrise Society')).toBeInTheDocument();
  });

  it('should display error state on fetch failure', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading alerts')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should display empty state when no alerts', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('No alerts')).toBeInTheDocument();
      expect(screen.getByText('All clear! No active alerts.')).toBeInTheDocument();
    });
  });

  it('should filter alerts by status', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Initially shows active alerts (both active and acknowledged)
    expect(screen.getByText('2 alerts')).toBeInTheDocument();

    // Click "Resolved" filter
    const resolvedButton = screen.getByRole('button', { name: 'Resolved' });
    fireEvent.click(resolvedButton);

    await waitFor(() => {
      expect(screen.getByText('No alerts found.')).toBeInTheDocument();
    });

    // Click "All" filter
    const allButton = screen.getByRole('button', { name: 'All' });
    fireEvent.click(allButton);

    await waitFor(() => {
      expect(screen.getByText('2 alerts')).toBeInTheDocument();
    });
  });

  it('should display alert details correctly', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Check first alert details
    expect(screen.getByText('tomato')).toBeInTheDocument();
    expect(screen.getByText('Green Valley Apartments')).toBeInTheDocument();
    expect(screen.getByText('500 kg')).toBeInTheDocument();
    expect(screen.getByText('300 kg')).toBeInTheDocument();
    expect(screen.getByText('200 kg')).toBeInTheDocument();

    // Check priority badges
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  it('should handle acknowledge action', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Mock acknowledge API call
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const acknowledgeButtons = screen.getAllByRole('button', { name: 'Acknowledge' });
    fireEvent.click(acknowledgeButtons[0]);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/alert-001/acknowledge'),
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  it('should handle resolve action', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Mock resolve API call
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const resolveButtons = screen.getAllByRole('button', { name: 'Mark as Resolved' });
    fireEvent.click(resolveButtons[0]);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/alert-001/resolve'),
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  it('should display correct alert icons', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('⚠️')).toBeInTheDocument(); // inventory_shortage
      expect(screen.getByText('📋')).toBeInTheDocument(); // unfulfilled_reservation
    });
  });

  it('should show acknowledged status badge', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Acknowledged')).toBeInTheDocument();
    });
  });

  it('should apply correct priority colors', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    const { container } = render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Check for priority color classes
    const alertCards = container.querySelectorAll('[class*="border-2"]');
    expect(alertCards[0].className).toContain('bg-red-100'); // high priority
    expect(alertCards[1].className).toContain('bg-yellow-100'); // medium priority
  });

  it('should poll for new alerts', async () => {
    vi.useFakeTimers();

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Inventory Shortage')).toBeInTheDocument();
    });

    // Clear previous calls
    vi.clearAllMocks();

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/alerts/fpo-001')
      );
    });

    vi.useRealTimers();
  });

  it('should display delivery date when available', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAlerts,
    });

    render(<AlertsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('3/15/2026')).toBeInTheDocument();
      expect(screen.getByText('3/10/2026')).toBeInTheDocument();
    });
  });
});
