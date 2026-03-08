import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import InventoryCard from '../InventoryCard';

describe('InventoryCard', () => {
  const mockInventory = {
    fpo_id: 'fpo-001',
    crop_type: 'tomato',
    total_quantity_kg: '1000',
    available_quantity_kg: '600',
    reserved_quantity_kg: '200',
    allocated_quantity_kg: '200',
    farmer_count: 5,
    last_updated: new Date().toISOString(),
  };

  it('should display crop type and total quantity', () => {
    const onClick = vi.fn();
    render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('tomato')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('kg')).toBeInTheDocument();
  });

  it('should display quantity breakdown', () => {
    const onClick = vi.fn();
    render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('Available:')).toBeInTheDocument();
    expect(screen.getByText('600 kg')).toBeInTheDocument();
    expect(screen.getByText('Reserved:')).toBeInTheDocument();
    expect(screen.getByText('200 kg')).toBeInTheDocument();
    expect(screen.getByText('Allocated:')).toBeInTheDocument();
  });

  it('should show healthy status when available > 50%', () => {
    const onClick = vi.fn();
    render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('should show moderate status when available between 20-50%', () => {
    const onClick = vi.fn();
    const moderateInventory = {
      ...mockInventory,
      available_quantity_kg: '300',
      reserved_quantity_kg: '400',
      allocated_quantity_kg: '300',
    };

    render(
      <InventoryCard
        cropType="tomato"
        inventory={moderateInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('Moderate')).toBeInTheDocument();
  });

  it('should show low status when available < 20%', () => {
    const onClick = vi.fn();
    const lowInventory = {
      ...mockInventory,
      available_quantity_kg: '100',
      reserved_quantity_kg: '400',
      allocated_quantity_kg: '500',
    };

    render(
      <InventoryCard
        cropType="tomato"
        inventory={lowInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('should display farmer count', () => {
    const onClick = vi.fn();
    render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText('5 farmers')).toBeInTheDocument();
  });

  it('should display last updated timestamp', () => {
    const onClick = vi.fn();
    render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    expect(screen.getByText(/Updated/)).toBeInTheDocument();
  });

  it('should call onClick when clicked', () => {
    const onClick = vi.fn();
    const { container } = render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );

    const card = container.firstChild as HTMLElement;
    card.click();

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('should apply selected styling when isSelected is true', () => {
    const onClick = vi.fn();
    const { container } = render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={true}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('ring-2');
    expect(card.className).toContain('ring-green-500');
  });

  it('should use color coding based on inventory level', () => {
    const onClick = vi.fn();
    
    // Healthy inventory (>50% available)
    const { container: healthyContainer } = render(
      <InventoryCard
        cropType="tomato"
        inventory={mockInventory}
        onClick={onClick}
        isSelected={false}
      />
    );
    expect(healthyContainer.firstChild?.className).toContain('bg-green-100');

    // Moderate inventory (20-50% available)
    const moderateInventory = {
      ...mockInventory,
      available_quantity_kg: '300',
      reserved_quantity_kg: '400',
      allocated_quantity_kg: '300',
    };
    const { container: moderateContainer } = render(
      <InventoryCard
        cropType="tomato"
        inventory={moderateInventory}
        onClick={onClick}
        isSelected={false}
      />
    );
    expect(moderateContainer.firstChild?.className).toContain('bg-yellow-100');

    // Low inventory (<20% available)
    const lowInventory = {
      ...mockInventory,
      available_quantity_kg: '100',
      reserved_quantity_kg: '400',
      allocated_quantity_kg: '500',
    };
    const { container: lowContainer } = render(
      <InventoryCard
        cropType="tomato"
        inventory={lowInventory}
        onClick={onClick}
        isSelected={false}
      />
    );
    expect(lowContainer.firstChild?.className).toContain('bg-red-100');
  });
});
