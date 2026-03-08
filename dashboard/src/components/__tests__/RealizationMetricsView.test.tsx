import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import RealizationMetricsView from '../RealizationMetricsView';

// Mock fetch
global.fetch = vi.fn();

describe('RealizationMetricsView', () => {
  const mockAllocation = {
    allocation_id: 'ALLOC001',
    fpo_id: 'FPO001',
    crop_type: 'tomato',
    allocation_date: '2024-03-15T10:00:00Z',
    channel_allocations: [
      {
        channel_type: 'society',
        channel_id: 'SOC001',
        channel_name: 'Green Valley Society',
        quantity_kg: 500,
        price_per_kg: 50,
        revenue: 25000,
        priority: 1,
      },
      {
        channel_type: 'processing',
        channel_id: 'PROC001',
        channel_name: 'Fresh Foods Ltd',
        quantity_kg: 300,
        price_per_kg: 40,
        revenue: 12000,
        priority: 2,
      },
      {
        channel_type: 'mandi',
        channel_id: 'MANDI001',
        channel_name: 'City Mandi',
        quantity_kg: 200,
        price_per_kg: 38,
        revenue: 7600,
        priority: 3,
      },
    ],
    total_quantity_kg: 1000,
    blended_realization_per_kg: 44.6,
    status: 'completed',
  };

  const mockHistoryData = [
    {
      allocation_id: 'ALLOC000',
      fpo_id: 'FPO001',
      crop_type: 'tomato',
      allocation_date: '2024-03-10T10:00:00Z',
      channel_allocations: [
        {
          channel_type: 'society',
          channel_id: 'SOC001',
          channel_name: 'Green Valley Society',
          quantity_kg: 400,
          price_per_kg: 48,
          revenue: 19200,
          priority: 1,
        },
        {
          channel_type: 'mandi',
          channel_id: 'MANDI001',
          channel_name: 'City Mandi',
          quantity_kg: 600,
          price_per_kg: 36,
          revenue: 21600,
          priority: 3,
        },
      ],
      total_quantity_kg: 1000,
      blended_realization_per_kg: 40.8,
      status: 'completed',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    expect(screen.getByText('Loading realization metrics...')).toBeInTheDocument();
  });

  it('should display error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading realization metrics')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should display blended realization rate', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Blended Realization Rate')).toBeInTheDocument();
      expect(screen.getByText('₹44.60')).toBeInTheDocument();
      // Use getAllByText for /kg since it appears multiple times
      const kgElements = screen.getAllByText('/kg');
      expect(kgElements.length).toBeGreaterThan(0);
    });
  });

  it('should display total revenue', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText(/Total Revenue: ₹44,600.00/)).toBeInTheDocument();
    });
  });

  it('should display comparison to best single channel (negative)', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('vs Best Single Channel')).toBeInTheDocument();
      // Best single channel is 50, blended is 44.6, difference is -5.4
      expect(screen.getByText('₹-5.40')).toBeInTheDocument();
      expect(screen.getByText('-10.8%')).toBeInTheDocument();
      expect(screen.getByText('Best single channel would have yielded higher realization')).toBeInTheDocument();
    });
  });

  it('should display comparison to best single channel (positive)', async () => {
    const allocationWithBetterBlended = {
      ...mockAllocation,
      blended_realization_per_kg: 52,
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(allocationWithBetterBlended),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('+₹2.00')).toBeInTheDocument();
      expect(screen.getByText('+4.0%')).toBeInTheDocument();
      expect(screen.getByText('Collective selling achieved better realization than best single channel')).toBeInTheDocument();
    });
  });

  it('should display channel breakdown cards', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel-wise Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Green Valley Society')).toBeInTheDocument();
      expect(screen.getByText('Fresh Foods Ltd')).toBeInTheDocument();
      expect(screen.getByText('City Mandi')).toBeInTheDocument();
    });
  });

  it('should display trend chart when historical data is available', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Historical Trend')).toBeInTheDocument();
      expect(screen.getByText('Historical realization rates across channels (last 10 allocations)')).toBeInTheDocument();
    });
  });

  it('should not display trend chart when no historical data', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.queryByText('Historical Trend')).not.toBeInTheDocument();
    });
  });

  it('should display summary statistics', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Total Quantity')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument();
      
      expect(screen.getByText('Channels Used')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      
      expect(screen.getByText('Best Channel Rate')).toBeInTheDocument();
      // Use getAllByText since ₹50.00 appears in multiple places
      const priceElements = screen.getAllByText((content, element) => {
        return element?.textContent === '₹50.00/kg';
      });
      expect(priceElements.length).toBeGreaterThan(0);
      
      expect(screen.getByText('Allocation Date')).toBeInTheDocument();
    });
  });

  it('should handle allocation with equal blended and best single channel rate', async () => {
    const allocationWithEqualRates = {
      ...mockAllocation,
      blended_realization_per_kg: 50,
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(allocationWithEqualRates),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      // Use text matcher function since the text is split across elements
      expect(screen.getByText((content, element) => {
        return element?.textContent === '+₹0.00';
      })).toBeInTheDocument();
      expect(screen.getByText((content, element) => {
        return element?.textContent === '+0.0%';
      })).toBeInTheDocument();
      expect(screen.getByText('Blended realization matches best single channel rate')).toBeInTheDocument();
    });
  });

  it('should display crop type in header', async () => {
    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/allocations/ALLOC001')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllocation),
        });
      }
      if (url.includes('/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockHistoryData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<RealizationMetricsView allocationId="ALLOC001" />);

    await waitFor(() => {
      expect(screen.getByText('Revenue analysis for tomato')).toBeInTheDocument();
    });
  });
});
