import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DeliveryCard from '../DeliveryCard';

describe('DeliveryCard', () => {
  const mockDelivery = {
    reservation_id: 'r1',
    society_id: 's1',
    society_name: 'Green Valley Apartments',
    crop_type: 'tomato',
    reserved_quantity_kg: '100',
    delivery_date: '2024-01-05',
    delivery_time_window: '9:00-11:00',
    status: 'predicted',
  };

  it('should display society name', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    expect(screen.getByText('Green Valley Apartments')).toBeInTheDocument();
  });

  it('should display crop type with capitalization', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    expect(screen.getByText('Tomato')).toBeInTheDocument();
  });

  it('should display quantity with formatting', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('kg')).toBeInTheDocument();
  });

  it('should display delivery date', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    // Date should be formatted
    expect(screen.getByText(/Jan 5, 2024/)).toBeInTheDocument();
  });

  it('should display time window', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    expect(screen.getByText('9:00-11:00')).toBeInTheDocument();
  });

  it('should display predicted status with correct styling', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    const statusBadge = screen.getByText('Predicted');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge.className).toContain('bg-yellow-100');
  });

  it('should display confirmed status with correct styling', () => {
    const confirmedDelivery = { ...mockDelivery, status: 'confirmed' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={confirmedDelivery} onConfirm={onConfirm} />);
    
    const statusBadge = screen.getByText('Confirmed');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge.className).toContain('bg-blue-100');
  });

  it('should display fulfilled status with correct styling', () => {
    const fulfilledDelivery = { ...mockDelivery, status: 'fulfilled' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={fulfilledDelivery} onConfirm={onConfirm} />);
    
    const statusBadge = screen.getByText('Fulfilled');
    expect(statusBadge).toBeInTheDocument();
    expect(statusBadge.className).toContain('bg-green-100');
  });

  it('should show confirm button for predicted status', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    const confirmButton = screen.getByText('Confirm Order');
    expect(confirmButton).toBeInTheDocument();
  });

  it('should call onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    const confirmButton = screen.getByText('Confirm Order');
    fireEvent.click(confirmButton);
    
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('should show edit button for predicted status', () => {
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={mockDelivery} onConfirm={onConfirm} />);
    
    const editButton = screen.getByText('Edit');
    expect(editButton).toBeInTheDocument();
  });

  it('should not show confirm button for confirmed status', () => {
    const confirmedDelivery = { ...mockDelivery, status: 'confirmed' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={confirmedDelivery} onConfirm={onConfirm} />);
    
    expect(screen.queryByText('Confirm Order')).not.toBeInTheDocument();
  });

  it('should show view details button for confirmed status', () => {
    const confirmedDelivery = { ...mockDelivery, status: 'confirmed' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={confirmedDelivery} onConfirm={onConfirm} />);
    
    const viewDetailsButton = screen.getByText('View Details');
    expect(viewDetailsButton).toBeInTheDocument();
  });

  it('should not show action buttons for fulfilled status', () => {
    const fulfilledDelivery = { ...mockDelivery, status: 'fulfilled' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={fulfilledDelivery} onConfirm={onConfirm} />);
    
    expect(screen.queryByText('Confirm Order')).not.toBeInTheDocument();
    expect(screen.queryByText('View Details')).not.toBeInTheDocument();
  });

  it('should format large quantities with commas', () => {
    const largeQuantityDelivery = { ...mockDelivery, reserved_quantity_kg: '1500' };
    const onConfirm = vi.fn();
    render(<DeliveryCard delivery={largeQuantityDelivery} onConfirm={onConfirm} />);
    
    expect(screen.getByText('1,500')).toBeInTheDocument();
  });
});
