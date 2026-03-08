import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AllocationFlowView from '../AllocationFlowView';

describe('AllocationFlowView', () => {
  const mockAllocationData = {
    allocation_id: 'alloc-001',
    fpo_id: 'fpo-001',
    crop_type: 'tomato',
    allocation_date: '2026-03-08T00:00:00Z',
    channel_allocations: [
      {
        channel_type: 'society',
        channel_id: 'soc-001',
        channel_name: 'Green Valley Society',
        quantity_kg: 500,
        price_per_kg: 30,
        revenue: 15000,
        priority: 1,
      },
      {
        channel_type: 'processing',
        channel_id: 'proc-001',
        channel_name: 'Fresh Foods Ltd',
        quantity_kg: 300,
        price_per_kg: 25,
        revenue: 7500,
        priority: 2,
      },
      {
        channel_type: 'mandi',
        channel_id: 'mandi-001',
        channel_name: 'City Mandi',
        quantity_kg: 200,
        price_per_kg: 20,
        revenue: 4000,
        priority: 3,
      },
    ],
    total_quantity_kg: 1000,
    blended_realization_per_kg: 26.5,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('should show loading state initially', () => {
    (global.fetch as any).mockImplementation(() => new Promise(() => {}));

    render(<AllocationFlowView allocationId="alloc-001" />);

    expect(screen.getByText('Loading allocation flow...')).toBeInTheDocument();
  });

  it('should display allocation flow after loading', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.queryByText('Loading allocation flow...')).not.toBeInTheDocument();
    });

    expect(screen.getByText('Allocation Flow')).toBeInTheDocument();
    expect(screen.getByText(/Distribution of tomato across channels/)).toBeInTheDocument();
  });

  it('should display error message on fetch failure', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Error loading allocation')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should display empty state when no allocation data', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        allocation_id: 'alloc-001',
        fpo_id: 'fpo-001',
        crop_type: 'tomato',
        allocation_date: '2026-03-08T00:00:00Z',
        channel_allocations: [],
        total_quantity_kg: 0,
        blended_realization_per_kg: 0,
      }),
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Allocation Flow')).toBeInTheDocument();
    });

    // With empty allocations, the table should still render but with no rows
    expect(screen.getByText('Channel Details')).toBeInTheDocument();
  });

  it('should display summary statistics', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Total Inventory')).toBeInTheDocument();
    });

    // Use getAllByText for values that appear multiple times
    const totalQuantities = screen.getAllByText('1,000');
    expect(totalQuantities.length).toBeGreaterThan(0);
    
    const societyQuantities = screen.getAllByText('500');
    expect(societyQuantities.length).toBeGreaterThan(0);
    
    const processingQuantities = screen.getAllByText('300');
    expect(processingQuantities.length).toBeGreaterThan(0);
    
    const mandiQuantities = screen.getAllByText('200');
    expect(mandiQuantities.length).toBeGreaterThan(0);
  });

  it('should display channel percentages', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('50.0% of total')).toBeInTheDocument(); // Society
    });

    expect(screen.getByText('30.0% of total')).toBeInTheDocument(); // Processing
    expect(screen.getByText('20.0% of total')).toBeInTheDocument(); // Mandi
  });

  it('should display channel details table', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Channel')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Quantity (kg)')).toBeInTheDocument();
    expect(screen.getByText('Percentage')).toBeInTheDocument();
    expect(screen.getByText('Price/kg')).toBeInTheDocument();
    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('Priority')).toBeInTheDocument();

    // Check channel names
    expect(screen.getByText('Green Valley Society')).toBeInTheDocument();
    expect(screen.getByText('Fresh Foods Ltd')).toBeInTheDocument();
    expect(screen.getByText('City Mandi')).toBeInTheDocument();
  });

  it('should display prices and revenues correctly', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    // Check prices
    expect(screen.getByText('₹30.00')).toBeInTheDocument();
    expect(screen.getByText('₹25.00')).toBeInTheDocument();
    expect(screen.getByText('₹20.00')).toBeInTheDocument();

    // Check revenues
    expect(screen.getByText('₹15,000')).toBeInTheDocument();
    expect(screen.getByText('₹7,500')).toBeInTheDocument();
    expect(screen.getByText('₹4,000')).toBeInTheDocument();
  });

  it('should display priority badges', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    const { container } = render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    // Check priority badges (1, 2, 3)
    const priorityBadges = container.querySelectorAll('td span.inline-flex.items-center.justify-center');
    expect(priorityBadges.length).toBeGreaterThanOrEqual(3);
  });

  it('should display blended realization in footer', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    expect(screen.getByText('₹26.50')).toBeInTheDocument(); // Blended realization
  });

  it('should display total revenue in footer', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    expect(screen.getByText('₹26,500')).toBeInTheDocument(); // Total revenue
  });

  it('should sort channels by priority in table', async () => {
    const unsortedAllocation = {
      ...mockAllocationData,
      channel_allocations: [
        mockAllocationData.channel_allocations[2], // Priority 3
        mockAllocationData.channel_allocations[0], // Priority 1
        mockAllocationData.channel_allocations[1], // Priority 2
      ],
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => unsortedAllocation,
    });

    const { container } = render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    // Check that rows are sorted by priority
    const rows = container.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(3);
    
    // First row should be priority 1 (Green Valley Society)
    expect(rows[0].textContent).toContain('Green Valley Society');
    
    // Second row should be priority 2 (Fresh Foods Ltd)
    expect(rows[1].textContent).toContain('Fresh Foods Ltd');
    
    // Third row should be priority 3 (City Mandi)
    expect(rows[2].textContent).toContain('City Mandi');
  });

  it('should render Sankey diagram container', async () => {
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockAllocationData,
    });

    const { container } = render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Flow Visualization')).toBeInTheDocument();
    });

    // Check for ResponsiveContainer (Recharts component)
    const responsiveContainer = container.querySelector('.recharts-responsive-container');
    expect(responsiveContainer).toBeInTheDocument();
  });

  it('should handle allocation with single channel', async () => {
    const singleChannelAllocation = {
      ...mockAllocationData,
      channel_allocations: [mockAllocationData.channel_allocations[0]],
      total_quantity_kg: 500,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => singleChannelAllocation,
    });

    render(<AllocationFlowView allocationId="alloc-001" />);

    await waitFor(() => {
      expect(screen.getByText('Channel Details')).toBeInTheDocument();
    });

    expect(screen.getByText('Green Valley Society')).toBeInTheDocument();
    expect(screen.queryByText('Fresh Foods Ltd')).not.toBeInTheDocument();
    expect(screen.queryByText('City Mandi')).not.toBeInTheDocument();
  });
});
