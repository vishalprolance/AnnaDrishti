import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FarmerIncomeCard from '../FarmerIncomeCard';

describe('FarmerIncomeCard', () => {
  const mockFarmerIncome = {
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
  };

  it('should display farmer name and contribution', () => {
    render(<FarmerIncomeCard farmerIncome={mockFarmerIncome} />);

    expect(screen.getByText('FARMER001')).toBeInTheDocument();
    expect(screen.getByText('Contribution: 100 kg')).toBeInTheDocument();
  });

  it('should display total income and blended rate', () => {
    render(<FarmerIncomeCard farmerIncome={mockFarmerIncome} />);

    expect(screen.getByText('₹4,528.00')).toBeInTheDocument();
    expect(screen.getByText('Total Income')).toBeInTheDocument();
    expect(screen.getByText('@ ₹45.28/kg (blended)')).toBeInTheDocument();
  });

  it('should display channel breakdown', () => {
    render(<FarmerIncomeCard farmerIncome={mockFarmerIncome} />);

    expect(screen.getByText('Channel Breakdown')).toBeInTheDocument();
    
    // Check all channels are displayed
    expect(screen.getByText('society')).toBeInTheDocument();
    expect(screen.getByText('processing')).toBeInTheDocument();
    expect(screen.getByText('mandi')).toBeInTheDocument();

    // Check quantities
    expect(screen.getByText('55.6 kg')).toBeInTheDocument();
    expect(screen.getByText('27.8 kg')).toBeInTheDocument();
    expect(screen.getByText('16.7 kg')).toBeInTheDocument();

    // Check revenues
    expect(screen.getByText('₹2778.00')).toBeInTheDocument();
    expect(screen.getByText('₹1111.20')).toBeInTheDocument();
    expect(screen.getByText('₹638.80')).toBeInTheDocument();

    // Check rates
    expect(screen.getByText('@ ₹50.00/kg')).toBeInTheDocument();
    expect(screen.getByText('@ ₹40.00/kg')).toBeInTheDocument();
    expect(screen.getByText('@ ₹38.33/kg')).toBeInTheDocument();
  });

  it('should display improvement vs single channel (negative)', () => {
    render(<FarmerIncomeCard farmerIncome={mockFarmerIncome} />);

    expect(screen.getByText('vs Best Single Channel')).toBeInTheDocument();
    expect(screen.getByText(/₹-472.00/)).toBeInTheDocument();
    expect(screen.getByText(/\(-9.4%\)/)).toBeInTheDocument();
    expect(screen.getByText('Single channel would be better')).toBeInTheDocument();
  });

  it('should display positive improvement correctly', () => {
    const positiveImprovementFarmer = {
      ...mockFarmerIncome,
      vs_best_single_channel: {
        single_channel_revenue: '4000.00',
        improvement: '528.00',
        improvement_percentage: '13.20',
      },
    };

    render(<FarmerIncomeCard farmerIncome={positiveImprovementFarmer} />);

    expect(screen.getByText(/\+₹528.00/)).toBeInTheDocument();
    expect(screen.getByText(/\(\+13.2%\)/)).toBeInTheDocument();
    expect(screen.getByText('Better with collective selling')).toBeInTheDocument();
  });

  it('should display zero improvement correctly', () => {
    const zeroImprovementFarmer = {
      ...mockFarmerIncome,
      vs_best_single_channel: {
        single_channel_revenue: '4528.00',
        improvement: '0.00',
        improvement_percentage: '0.00',
      },
    };

    render(<FarmerIncomeCard farmerIncome={zeroImprovementFarmer} />);

    expect(screen.getByText(/₹0.00/)).toBeInTheDocument();
    expect(screen.getByText('Same as single channel')).toBeInTheDocument();
  });

  it('should apply correct color coding for channels', () => {
    const { container } = render(<FarmerIncomeCard farmerIncome={mockFarmerIncome} />);

    // Check that channel badges have appropriate styling
    const societyBadge = screen.getByText('society');
    expect(societyBadge.className).toContain('bg-blue-100');
    expect(societyBadge.className).toContain('text-blue-800');

    const processingBadge = screen.getByText('processing');
    expect(processingBadge.className).toContain('bg-purple-100');
    expect(processingBadge.className).toContain('text-purple-800');

    const mandiBadge = screen.getByText('mandi');
    expect(mandiBadge.className).toContain('bg-orange-100');
    expect(mandiBadge.className).toContain('text-orange-800');
  });

  it('should handle single channel breakdown', () => {
    const singleChannelFarmer = {
      ...mockFarmerIncome,
      channel_breakdown: [
        {
          channel: 'society',
          channel_name: 'Green Valley Society',
          quantity_kg: '100',
          revenue: '5000.00',
          rate_per_kg: '50',
        },
      ],
    };

    render(<FarmerIncomeCard farmerIncome={singleChannelFarmer} />);

    expect(screen.getByText('society')).toBeInTheDocument();
    expect(screen.getByText('100.0 kg')).toBeInTheDocument();
    expect(screen.getByText('₹5000.00')).toBeInTheDocument();
  });

  it('should format large numbers correctly', () => {
    const largeNumberFarmer = {
      ...mockFarmerIncome,
      contribution_kg: '10000',
      total_revenue: '452800.00',
      blended_rate_per_kg: '45.28',
    };

    render(<FarmerIncomeCard farmerIncome={largeNumberFarmer} />);

    expect(screen.getByText('Contribution: 10,000 kg')).toBeInTheDocument();
    expect(screen.getByText('₹452,800.00')).toBeInTheDocument();
  });
});
