import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ReportsView from '../ReportsView';

// Mock fetch
global.fetch = vi.fn();

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-url');

describe('ReportsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  const mockCropTypes = {
    crop_types: ['tomato', 'onion', 'potato'],
  };

  const mockReports = {
    allocations: [
      {
        allocation_id: 'alloc-001',
        allocation_date: '2026-03-01T00:00:00Z',
        crop_type: 'tomato',
        total_quantity_kg: 1000,
        blended_realization_per_kg: 28.5,
        total_revenue: 28500,
        channel_breakdown: [
          {
            channel_type: 'society',
            channel_name: 'Green Valley Apartments',
            quantity_kg: 400,
            price_per_kg: 32,
            revenue: 12800,
          },
          {
            channel_type: 'processing',
            channel_name: 'Sai Agro Processing',
            quantity_kg: 300,
            price_per_kg: 28,
            revenue: 8400,
          },
          {
            channel_type: 'mandi',
            channel_name: 'Nashik Mandi',
            quantity_kg: 300,
            price_per_kg: 25,
            revenue: 7500,
          },
        ],
      },
      {
        allocation_id: 'alloc-002',
        allocation_date: '2026-03-05T00:00:00Z',
        crop_type: 'onion',
        total_quantity_kg: 800,
        blended_realization_per_kg: 22.5,
        total_revenue: 18000,
        channel_breakdown: [
          {
            channel_type: 'society',
            channel_name: 'Sunrise Society',
            quantity_kg: 300,
            price_per_kg: 26,
            revenue: 7800,
          },
          {
            channel_type: 'mandi',
            channel_name: 'Pune Mandi',
            quantity_kg: 500,
            price_per_kg: 20.4,
            revenue: 10200,
          },
        ],
      },
    ],
  };

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ReportsView fpoId="fpo-001" />);
    
    expect(screen.getByText('Loading reports...')).toBeInTheDocument();
  });

  it('should fetch and display reports', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('tomato')).toBeInTheDocument();
      expect(screen.getByText('onion')).toBeInTheDocument();
    });

    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('800')).toBeInTheDocument();
  });

  it('should display error state on fetch failure', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockRejectedValueOnce(new Error('Network error'));

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading reports')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should display empty state when no reports', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ allocations: [] }),
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('No reports found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your filters or date range')).toBeInTheDocument();
    });
  });

  it('should display summary statistics', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Total Quantity')).toBeInTheDocument();
      expect(screen.getByText('1,800')).toBeInTheDocument(); // 1000 + 800
      
      expect(screen.getByText('Total Revenue')).toBeInTheDocument();
      expect(screen.getByText('₹46,500')).toBeInTheDocument(); // 28500 + 18000
      
      expect(screen.getByText('Avg Blended Rate')).toBeInTheDocument();
      expect(screen.getByText('₹25.83')).toBeInTheDocument(); // 46500 / 1800
      
      expect(screen.getByText('Allocations')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('should display channel distribution', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Distribution')).toBeInTheDocument();
      
      // Society: 400 + 300 = 700 kg
      expect(screen.getByText('700 kg')).toBeInTheDocument();
      
      // Processing: 300 kg
      expect(screen.getByText('300 kg')).toBeInTheDocument();
      
      // Mandi: 300 + 500 = 800 kg
      expect(screen.getByText('800 kg')).toBeInTheDocument();
    });
  });

  it('should filter by date range', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('tomato')).toBeInTheDocument();
    });

    // Change start date
    const startDateInput = screen.getByLabelText('Start Date');
    fireEvent.change(startDateInput, { target: { value: '2026-03-01' } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2026-03-01')
      );
    });
  });

  it('should filter by crop type', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('tomato')).toBeInTheDocument();
    });

    // Change crop type filter
    const cropTypeSelect = screen.getByLabelText('Crop Type');
    fireEvent.change(cropTypeSelect, { target: { value: 'tomato' } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('crop_type=tomato')
      );
    });
  });

  it('should filter by channel', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('tomato')).toBeInTheDocument();
    });

    // Change channel filter
    const channelSelect = screen.getByLabelText('Channel');
    fireEvent.change(channelSelect, { target: { value: 'society' } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('channel=society')
      );
    });
  });

  it('should export CSV', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    // Mock document.createElement and appendChild
    const mockLink = {
      setAttribute: vi.fn(),
      click: vi.fn(),
      style: {},
    };
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('tomato')).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /Export CSV/i });
    fireEvent.click(exportButton);

    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(mockLink.setAttribute).toHaveBeenCalledWith('href', expect.any(String));
    expect(mockLink.setAttribute).toHaveBeenCalledWith('download', expect.stringContaining('.csv'));
    expect(mockLink.click).toHaveBeenCalled();
    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it('should disable export button when no data', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ allocations: [] }),
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('No reports found')).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /Export CSV/i });
    expect(exportButton).toBeDisabled();
  });

  it('should display channel badges in table', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('society: 400kg')).toBeInTheDocument();
      expect(screen.getByText('processing: 300kg')).toBeInTheDocument();
      expect(screen.getByText('mandi: 300kg')).toBeInTheDocument();
    });
  });

  it('should display blended rates correctly', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('₹28.50/kg')).toBeInTheDocument();
      expect(screen.getByText('₹22.50/kg')).toBeInTheDocument();
    });
  });

  it('should populate crop type dropdown', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      const cropTypeSelect = screen.getByLabelText('Crop Type');
      expect(cropTypeSelect).toBeInTheDocument();
      
      // Check that options are populated
      const options = (cropTypeSelect as HTMLSelectElement).options;
      expect(options.length).toBeGreaterThan(1); // "All Crops" + crop types
    });
  });

  it('should calculate percentages correctly in channel distribution', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCropTypes,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockReports,
      });

    render(<ReportsView fpoId="fpo-001" />);

    await waitFor(() => {
      // Society: 700/1800 = 38.9%
      expect(screen.getByText('(38.9%)')).toBeInTheDocument();
      
      // Processing: 300/1800 = 16.7%
      expect(screen.getByText('(16.7%)')).toBeInTheDocument();
      
      // Mandi: 800/1800 = 44.4%
      expect(screen.getByText('(44.4%)')).toBeInTheDocument();
    });
  });
});
