import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import FarmerContributionView from '../FarmerContributionView';

// Mock fetch
global.fetch = vi.fn();

describe('FarmerContributionView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const mockRealizationData = {
    allocation_id: 'alloc-001',
    fpo_id: 'fpo-001',
    crop_type: 'tomato',
    blended_realization_per_kg: '45.28',
    total_revenue: '8150.00',
    total_quantity_kg: '180',
    channel_breakdown: [
      {
        channel: 'society',
        quantity_kg: '100',
        revenue: '5000',
        rate_per_kg: '50',
      },
      {
        channel: 'processing',
        quantity_kg: '50',
        revenue: '2000',
        rate_per_kg: '40',
      },
      {
        channel: 'mandi',
        quantity_kg: '30',
        revenue: '1150',
        rate_per_kg: '38.33',
      },
    ],
    farmer_incomes: [
      {
        farmer_id: 'FARMER001',
        contribution_kg: '100',
        blended_rate_per_kg: '45.28',
        total_revenue: '4528.00',
        channel_breakdown: [
          {
            channel: 'society',
            channel_name: 'Green Valley Society',
            quantity_kg: '55.56',
            revenue: '2778.00',
            rate_per_kg: '50',
          },
          {
            channel: 'processing',
            channel_name: 'Fresh Foods Ltd',
            quantity_kg: '27.78',
            revenue: '1111.20',
            rate_per_kg: '40',
          },
          {
            channel: 'mandi',
            channel_name: 'City Mandi',
            quantity_kg: '16.67',
            revenue: '638.80',
            rate_per_kg: '38.33',
          },
        ],
        vs_best_single_channel: {
          single_channel_revenue: '5000.00',
          improvement: '-472.00',
          improvement_percentage: '-9.44',
        },
      },
      {
        farmer_id: 'FARMER002',
        contribution_kg: '50',
        blended_rate_per_kg: '45.28',
        total_revenue: '2264.00',
        channel_breakdown: [
          {
            channel: 'society',
            channel_name: 'Green Valley Society',
            quantity_kg: '27.78',
            revenue: '1389.00',
            rate_per_kg: '50',
          },
          {
            channel: 'processing',
            channel_name: 'Fresh Foods Ltd',
            quantity_kg: '13.89',
            revenue: '555.60',
            rate_per_kg: '40',
          },
          {
            channel: 'mandi',
            channel_name: 'City Mandi',
            quantity_kg: '8.33',
            revenue: '319.40',
            rate_per_kg: '38.33',
          },
        ],
        vs_best_single_channel: {
          single_channel_revenue: '2500.00',
          improvement: '-236.00',
          improvement_percentage: '-9.44',
        },
      },
      {
        farmer_id: 'FARMER003',
        contribution_kg: '30',
        blended_rate_per_kg: '45.28',
        total_revenue: '1358.40',
        channel_breakdown: [
          {
            channel: 'society',
            channel_name: 'Green Valley Society',
            quantity_kg: '16.67',
            revenue: '833.50',
            rate_per_kg: '50',
          },
          {
            channel: 'processing',
            channel_name: 'Fresh Foods Ltd',
            quantity_kg: '8.33',
            revenue: '333.20',
            rate_per_kg: '40',
          },
          {
            channel: 'mandi',
            channel_name: 'City Mandi',
            quantity_kg: '5.00',
            revenue: '191.70',
            rate_per_kg: '38.33',
          },
        ],
        vs_best_single_channel: {
          single_channel_revenue: '1500.00',
          improvement: '-141.60',
          improvement_percentage: '-9.44',
        },
      },
    ],
    num_farmers: 3,
  };

  it('should display loading state initially', () => {
    (global.fetch as any).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    );

    render(<FarmerContributionView allocationId="alloc-001" />);
    
    expect(screen.getByText('Loading farmer income data...')).toBeInTheDocument();
  });

  it('should display farmer list after loading', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    expect(screen.getByText(/Income breakdown for 3 farmers/)).toBeInTheDocument();
    expect(screen.getByText('FARMER001')).toBeInTheDocument();
    expect(screen.getByText('FARMER002')).toBeInTheDocument();
    expect(screen.getByText('FARMER003')).toBeInTheDocument();
  });

  it('should display error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading farmer income data')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should display empty state when no farmer income data exists', async () => {
    const emptyData = {
      ...mockRealizationData,
      farmer_incomes: [],
      num_farmers: 0,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('No farmer income data')).toBeInTheDocument();
    });

    expect(screen.getByText('Complete an allocation to see farmer income tracking')).toBeInTheDocument();
  });

  it('should filter farmers based on search term', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // All farmers should be visible initially
    expect(screen.getByText('FARMER001')).toBeInTheDocument();
    expect(screen.getByText('FARMER002')).toBeInTheDocument();
    expect(screen.getByText('FARMER003')).toBeInTheDocument();

    // Search for FARMER001
    const searchInput = screen.getByPlaceholderText('Search by farmer ID...');
    fireEvent.change(searchInput, { target: { value: 'FARMER001' } });

    await waitFor(() => {
      expect(screen.getByText('FARMER001')).toBeInTheDocument();
      expect(screen.queryByText('FARMER002')).not.toBeInTheDocument();
      expect(screen.queryByText('FARMER003')).not.toBeInTheDocument();
    });

    expect(screen.getByText('Showing 1 of 3 farmers')).toBeInTheDocument();
  });

  it('should sort farmers by income', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    const { container } = render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // Default sort should be by income (descending)
    const farmerCards = container.querySelectorAll('[class*="border border-gray-200 rounded-lg"]');
    expect(farmerCards.length).toBe(3);

    // FARMER001 has highest income (4528), should be first
    expect(farmerCards[0].textContent).toContain('FARMER001');
    expect(farmerCards[1].textContent).toContain('FARMER002');
    expect(farmerCards[2].textContent).toContain('FARMER003');
  });

  it('should sort farmers by contribution', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    const { container } = render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // Change sort to contribution
    const sortSelect = screen.getByDisplayValue('Sort by Income');
    fireEvent.change(sortSelect, { target: { value: 'contribution' } });

    await waitFor(() => {
      const farmerCards = container.querySelectorAll('[class*="border border-gray-200 rounded-lg"]');
      // FARMER001 has highest contribution (100 kg), should be first in descending order
      expect(farmerCards[0].textContent).toContain('FARMER001');
      expect(farmerCards[1].textContent).toContain('FARMER002');
      expect(farmerCards[2].textContent).toContain('FARMER003');
    });
  });

  it('should toggle sort order', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    const { container } = render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // Click sort order button to change to ascending
    const sortOrderButton = screen.getByTitle('Sort Ascending');
    fireEvent.click(sortOrderButton);

    await waitFor(() => {
      const farmerCards = container.querySelectorAll('[class*="border border-gray-200 rounded-lg"]');
      // In ascending order by income, FARMER003 (lowest income) should be first
      expect(farmerCards[0].textContent).toContain('FARMER003');
      expect(farmerCards[2].textContent).toContain('FARMER001');
    });
  });

  it('should display income calculation correctly', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // Check FARMER001's income is displayed
    expect(screen.getByText('₹4,528.00')).toBeInTheDocument();
    
    // Check contribution is displayed
    expect(screen.getByText('Contribution: 100 kg')).toBeInTheDocument();
  });

  it('should show no results message when search has no matches', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRealizationData),
    });

    render(<FarmerContributionView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Farmer Income Tracking')).toBeInTheDocument();
    });

    // Search for non-existent farmer
    const searchInput = screen.getByPlaceholderText('Search by farmer ID...');
    fireEvent.change(searchInput, { target: { value: 'NONEXISTENT' } });

    await waitFor(() => {
      expect(screen.getByText('No farmers match your search criteria')).toBeInTheDocument();
    });
  });
});
