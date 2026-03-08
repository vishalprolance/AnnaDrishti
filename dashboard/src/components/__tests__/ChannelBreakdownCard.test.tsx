import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ChannelBreakdownCard from '../ChannelBreakdownCard';

describe('ChannelBreakdownCard', () => {
  const mockSocietyChannel = {
    channel_type: 'society',
    channel_id: 'SOC001',
    channel_name: 'Green Valley Society',
    quantity_kg: 500,
    price_per_kg: 50,
    revenue: 25000,
    priority: 1,
  };

  const mockProcessingChannel = {
    channel_type: 'processing',
    channel_id: 'PROC001',
    channel_name: 'Fresh Foods Ltd',
    quantity_kg: 300,
    price_per_kg: 40,
    revenue: 12000,
    priority: 2,
  };

  const mockMandiChannel = {
    channel_type: 'mandi',
    channel_id: 'MANDI001',
    channel_name: 'City Mandi',
    quantity_kg: 200,
    price_per_kg: 38,
    revenue: 7600,
    priority: 3,
  };

  const totalQuantity = 1000;
  const totalRevenue = 44600;

  it('should display channel name', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('Green Valley Society')).toBeInTheDocument();
  });

  it('should display channel type badge', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('society')).toBeInTheDocument();
  });

  it('should display priority', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('Priority 1')).toBeInTheDocument();
  });

  it('should display quantity with correct formatting', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('Quantity')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
    expect(screen.getByText('kg')).toBeInTheDocument();
  });

  it('should display quantity percentage', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    // 500/1000 = 50%
    expect(screen.getByText('50.0% of total')).toBeInTheDocument();
  });

  it('should display revenue with correct formatting', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('₹25,000.00')).toBeInTheDocument();
  });

  it('should display revenue percentage', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    // 25000/44600 = 56.1%
    expect(screen.getByText('56.1% of total')).toBeInTheDocument();
  });

  it('should display rate per kg', () => {
    render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    expect(screen.getByText('Rate per kg')).toBeInTheDocument();
    expect(screen.getByText('₹50.00')).toBeInTheDocument();
  });

  it('should apply correct color coding for society channel', () => {
    const { container } = render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('bg-blue-50');
    expect(card.className).toContain('border-blue-200');
  });

  it('should apply correct color coding for processing channel', () => {
    const { container } = render(
      <ChannelBreakdownCard
        channel={mockProcessingChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('bg-purple-50');
    expect(card.className).toContain('border-purple-200');
  });

  it('should apply correct color coding for mandi channel', () => {
    const { container } = render(
      <ChannelBreakdownCard
        channel={mockMandiChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('bg-orange-50');
    expect(card.className).toContain('border-orange-200');
  });

  it('should calculate percentages correctly for processing channel', () => {
    render(
      <ChannelBreakdownCard
        channel={mockProcessingChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    // 300/1000 = 30%
    expect(screen.getByText('30.0% of total')).toBeInTheDocument();
    // 12000/44600 = 26.9%
    expect(screen.getByText('26.9% of total')).toBeInTheDocument();
  });

  it('should calculate percentages correctly for mandi channel', () => {
    render(
      <ChannelBreakdownCard
        channel={mockMandiChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    // 200/1000 = 20%
    expect(screen.getByText('20.0% of total')).toBeInTheDocument();
    // 7600/44600 = 17.0%
    expect(screen.getByText('17.0% of total')).toBeInTheDocument();
  });

  it('should handle large numbers correctly', () => {
    const largeChannel = {
      ...mockSocietyChannel,
      quantity_kg: 10000,
      revenue: 500000,
    };

    render(
      <ChannelBreakdownCard
        channel={largeChannel}
        totalQuantity={20000}
        totalRevenue={1000000}
      />
    );

    expect(screen.getByText('10,000')).toBeInTheDocument();
    expect(screen.getByText('₹500,000.00')).toBeInTheDocument();
  });

  it('should handle decimal percentages correctly', () => {
    const channel = {
      ...mockSocietyChannel,
      quantity_kg: 333,
      revenue: 16650,
    };

    render(
      <ChannelBreakdownCard
        channel={channel}
        totalQuantity={1000}
        totalRevenue={50000}
      />
    );

    // 333/1000 = 33.3% and 16650/50000 = 33.3%
    // Both appear, so use getAllByText
    const percentageElements = screen.getAllByText('33.3% of total');
    expect(percentageElements).toHaveLength(2);
  });

  it('should display all three priorities correctly', () => {
    const { rerender } = render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );
    expect(screen.getByText('Priority 1')).toBeInTheDocument();

    rerender(
      <ChannelBreakdownCard
        channel={mockProcessingChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );
    expect(screen.getByText('Priority 2')).toBeInTheDocument();

    rerender(
      <ChannelBreakdownCard
        channel={mockMandiChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );
    expect(screen.getByText('Priority 3')).toBeInTheDocument();
  });

  it('should truncate long channel names', () => {
    const longNameChannel = {
      ...mockSocietyChannel,
      channel_name: 'Very Long Channel Name That Should Be Truncated For Display',
    };

    render(
      <ChannelBreakdownCard
        channel={longNameChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    const nameElement = screen.getByText('Very Long Channel Name That Should Be Truncated For Display');
    expect(nameElement.className).toContain('truncate');
  });

  it('should render visual percentage bar', () => {
    const { container } = render(
      <ChannelBreakdownCard
        channel={mockSocietyChannel}
        totalQuantity={totalQuantity}
        totalRevenue={totalRevenue}
      />
    );

    // Check for the percentage bar container
    const progressBar = container.querySelector('.bg-white.rounded-full.h-2');
    expect(progressBar).toBeInTheDocument();
  });
});
