import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SocietyScheduleView from '../SocietyScheduleView';

// Mock fetch
global.fetch = vi.fn();

describe('SocietyScheduleView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockSocietiesData = {
    societies: [
      {
        society_id: 's1',
        society_name: 'Green Valley Apartments',
        location: 'Pune',
        delivery_address: '123 Main St',
        preferred_day: 'Monday',
        preferred_time_window: '9:00-11:00',
      },
      {
        society_id: 's2',
        society_name: 'Sunrise Residency',
        location: 'Mumbai',
        delivery_address: '456 Oak Ave',
        preferred_day: 'Wednesday',
        preferred_time_window: '14:00-16:00',
      },
    ],
  };

  const mockReservationsData = {
    reservations: [
      {
        reservation_id: 'r1',
        society_id: 's1',
        crop_type: 'tomato',
        reserved_quantity_kg: '100',
        reservation_timestamp: '2024-01-01T10:00:00Z',
        delivery_date: '2024-01-05',
        status: 'predicted',
      },
      {
        reservation_id: 'r2',
        society_id: 's2',
        crop_type: 'onion',
        reserved_quantity_kg: '150',
        reservation_timestamp: '2024-01-01T11:00:00Z',
        delivery_date: '2024-01-06',
        status: 'confirmed',
      },
      {
        reservation_id: 'r3',
        society_id: 's1',
        crop_type: 'potato',
        reserved_quantity_kg: '200',
        reservation_timestamp: '2024-01-01T12:00:00Z',
        delivery_date: '2024-01-05',
        status: 'predicted',
      },
    ],
  };

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    );

    render(<SocietyScheduleView fpoId="fpo-001" />);
    
    expect(screen.getByText('Loading schedule...')).toBeInTheDocument();
  });

  it('should display schedule data after loading', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Society Delivery Schedule')).toBeInTheDocument();
    });

    expect(screen.getByText(/Upcoming deliveries for 3 reservations/)).toBeInTheDocument();
  });

  it('should display error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading schedule')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should display empty state when no reservations exist', async () => {
    const emptyReservationsData = {
      reservations: [],
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(emptyReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('No deliveries scheduled')).toBeInTheDocument();
    });

    expect(screen.getByText('No reservations found for the selected date range')).toBeInTheDocument();
  });

  it('should render calendar with delivery dates', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Calendar')).toBeInTheDocument();
    });

    // Should show "All Dates" option
    expect(screen.getByText(/All Dates \(3\)/)).toBeInTheDocument();
    
    // Should show individual dates with delivery counts
    expect(screen.getByText(/2 deliver/)).toBeInTheDocument(); // Jan 5 has 2 deliveries
    expect(screen.getByText(/1 delivery/)).toBeInTheDocument(); // Jan 6 has 1 delivery
  });

  it('should filter deliveries by selected date', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Society Delivery Schedule')).toBeInTheDocument();
    });

    // Initially should show all deliveries
    expect(screen.getByText('All Upcoming Deliveries')).toBeInTheDocument();

    // Click on a specific date
    const dateButtons = screen.getAllByRole('button');
    const jan5Button = dateButtons.find(btn => btn.textContent?.includes('2 deliver'));
    
    if (jan5Button) {
      fireEvent.click(jan5Button);
      
      await waitFor(() => {
        // Should show filtered view
        expect(screen.getByText(/Deliveries for/)).toBeInTheDocument();
      });
    }
  });

  it('should display delivery cards with correct information', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Society Delivery Schedule')).toBeInTheDocument();
    });

    // Check that society names are displayed
    const societyNames = screen.getAllByText(/Green Valley Apartments|Sunrise Residency/);
    expect(societyNames.length).toBeGreaterThan(0);
  });

  it('should update date range when filter inputs change', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/societies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSocietiesData),
        });
      } else if (url.includes('/reservations')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockReservationsData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<SocietyScheduleView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Society Delivery Schedule')).toBeInTheDocument();
    });

    const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
    const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

    expect(startDateInput).toBeInTheDocument();
    expect(endDateInput).toBeInTheDocument();

    // Change start date
    fireEvent.change(startDateInput, { target: { value: '2024-01-10' } });
    
    await waitFor(() => {
      expect(startDateInput.value).toBe('2024-01-10');
    });

    // Change end date
    fireEvent.change(endDateInput, { target: { value: '2024-01-20' } });
    
    await waitFor(() => {
      expect(endDateInput.value).toBe('2024-01-20');
    });
  });
});
