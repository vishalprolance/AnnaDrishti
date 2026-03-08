import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import CollectiveInventoryView from '../CollectiveInventoryView';

// Mock fetch
global.fetch = vi.fn();

describe('CollectiveInventoryView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    );

    render(<CollectiveInventoryView fpoId="fpo-001" />);
    
    expect(screen.getByText('Loading inventory...')).toBeInTheDocument();
  });

  it('should display inventory data after loading', async () => {
    const mockSummaryData = {
      fpo_id: 'fpo-001',
      crop_types: ['tomato', 'onion'],
      total_crop_types: 2,
    };

    const mockTomatoData = {
      fpo_id: 'fpo-001',
      crop_type: 'tomato',
      total_quantity_kg: '1000',
      available_quantity_kg: '600',
      reserved_quantity_kg: '200',
      allocated_quantity_kg: '200',
      contributions: [
        {
          contribution_id: 'c1',
          farmer_id: 'f1',
          farmer_name: 'Ramesh Patil',
          quantity_kg: '500',
          quality_grade: 'A',
          timestamp: '2024-01-01T10:00:00Z',
          allocated: false,
        },
        {
          contribution_id: 'c2',
          farmer_id: 'f2',
          farmer_name: 'Suresh Kumar',
          quantity_kg: '500',
          quality_grade: 'B',
          timestamp: '2024-01-01T11:00:00Z',
          allocated: false,
        },
      ],
      farmer_count: 2,
      last_updated: '2024-01-01T12:00:00Z',
    };

    const mockOnionData = {
      fpo_id: 'fpo-001',
      crop_type: 'onion',
      total_quantity_kg: '800',
      available_quantity_kg: '500',
      reserved_quantity_kg: '150',
      allocated_quantity_kg: '150',
      contributions: [
        {
          contribution_id: 'c3',
          farmer_id: 'f3',
          farmer_name: 'Vijay Singh',
          quantity_kg: '800',
          quality_grade: 'A',
          timestamp: '2024-01-01T09:00:00Z',
          allocated: false,
        },
      ],
      farmer_count: 1,
      last_updated: '2024-01-01T12:00:00Z',
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/summary')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSummaryData),
        });
      } else if (url.includes('/tomato')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTomatoData),
        });
      } else if (url.includes('/onion')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOnionData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<CollectiveInventoryView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Collective Inventory')).toBeInTheDocument();
    });

    expect(screen.getByText(/Real-time inventory across 2 crop types/)).toBeInTheDocument();
  });

  it('should display error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<CollectiveInventoryView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading inventory')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should display empty state when no inventory exists', async () => {
    const mockEmptyData = {
      fpo_id: 'fpo-001',
      crop_types: [],
      total_crop_types: 0,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockEmptyData),
    });

    render(<CollectiveInventoryView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('No inventory data')).toBeInTheDocument();
    });

    expect(screen.getByText('Add farmer contributions to see inventory')).toBeInTheDocument();
  });

  it('should display per-farmer breakdown when crop is selected', async () => {
    const mockSummaryData = {
      fpo_id: 'fpo-001',
      crop_types: ['tomato'],
      total_crop_types: 1,
    };

    const mockTomatoData = {
      fpo_id: 'fpo-001',
      crop_type: 'tomato',
      total_quantity_kg: '1000',
      available_quantity_kg: '600',
      reserved_quantity_kg: '200',
      allocated_quantity_kg: '200',
      contributions: [
        {
          contribution_id: 'c1',
          farmer_id: 'f1',
          farmer_name: 'Ramesh Patil',
          quantity_kg: '500',
          quality_grade: 'A',
          timestamp: '2024-01-01T10:00:00Z',
          allocated: false,
        },
        {
          contribution_id: 'c2',
          farmer_id: 'f2',
          farmer_name: 'Suresh Kumar',
          quantity_kg: '500',
          quality_grade: 'B',
          timestamp: '2024-01-01T11:00:00Z',
          allocated: true,
        },
      ],
      farmer_count: 2,
      last_updated: '2024-01-01T12:00:00Z',
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/summary')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSummaryData),
        });
      } else if (url.includes('/tomato')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTomatoData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    const { container } = render(<CollectiveInventoryView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Collective Inventory')).toBeInTheDocument();
    });

    // Click on the inventory card to show breakdown
    const inventoryCard = container.querySelector('[class*="cursor-pointer"]');
    if (inventoryCard) {
      inventoryCard.click();
    }

    await waitFor(() => {
      expect(screen.getByText('Farmer Contributions - Tomato')).toBeInTheDocument();
    });

    expect(screen.getByText('Ramesh Patil')).toBeInTheDocument();
    expect(screen.getByText('Suresh Kumar')).toBeInTheDocument();
    expect(screen.getByText('Grade A')).toBeInTheDocument();
    expect(screen.getByText('Grade B')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('Allocated')).toBeInTheDocument();
  });

  it('should poll for real-time updates', async () => {
    vi.useFakeTimers();

    const mockSummaryData = {
      fpo_id: 'fpo-001',
      crop_types: ['tomato'],
      total_crop_types: 1,
    };

    const mockTomatoData = {
      fpo_id: 'fpo-001',
      crop_type: 'tomato',
      total_quantity_kg: '1000',
      available_quantity_kg: '600',
      reserved_quantity_kg: '200',
      allocated_quantity_kg: '200',
      contributions: [],
      farmer_count: 2,
      last_updated: '2024-01-01T12:00:00Z',
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/summary')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSummaryData),
        });
      } else if (url.includes('/tomato')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTomatoData),
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(<CollectiveInventoryView fpoId="fpo-001" />);

    await waitFor(() => {
      expect(screen.getByText('Collective Inventory')).toBeInTheDocument();
    });

    const initialCallCount = (global.fetch as any).mock.calls.length;

    // Fast-forward 5 seconds to trigger polling
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect((global.fetch as any).mock.calls.length).toBeGreaterThan(initialCallCount);
    });

    vi.useRealTimers();
  });
});
