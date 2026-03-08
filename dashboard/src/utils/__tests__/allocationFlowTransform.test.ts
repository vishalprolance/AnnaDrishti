import { describe, it, expect } from 'vitest';
import {
  transformToSankeyFormat,
  transformToDetailedSankeyFormat,
  calculateChannelPercentages,
  getChannelColor,
  type AllocationData,
} from '../allocationFlowTransform';

describe('allocationFlowTransform', () => {
  const mockAllocation: AllocationData = {
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

  describe('transformToSankeyFormat', () => {
    it('should create nodes for inventory and each channel type', () => {
      const result = transformToSankeyFormat(mockAllocation);

      expect(result.nodes).toHaveLength(4); // Inventory + 3 channel types
      expect(result.nodes[0].name).toBe('Collective Inventory');
      expect(result.nodes[1].name).toBe('Societies');
      expect(result.nodes[2].name).toBe('Processing Partners');
      expect(result.nodes[3].name).toBe('Mandi/Buyers');
    });

    it('should create links from inventory to each channel', () => {
      const result = transformToSankeyFormat(mockAllocation);

      expect(result.links).toHaveLength(3); // One link per channel type
      
      // Check society link
      expect(result.links[0].source).toBe(0);
      expect(result.links[0].target).toBe(1);
      expect(result.links[0].value).toBe(500);

      // Check processing link
      expect(result.links[1].source).toBe(0);
      expect(result.links[1].target).toBe(2);
      expect(result.links[1].value).toBe(300);

      // Check mandi link
      expect(result.links[2].source).toBe(0);
      expect(result.links[2].target).toBe(3);
      expect(result.links[2].value).toBe(200);
    });

    it('should assign correct colors to nodes', () => {
      const result = transformToSankeyFormat(mockAllocation);

      expect(result.nodes[0].color).toBe('#3b82f6'); // inventory - blue
      expect(result.nodes[1].color).toBe('#10b981'); // society - green
      expect(result.nodes[2].color).toBe('#8b5cf6'); // processing - purple
      expect(result.nodes[3].color).toBe('#f59e0b'); // mandi - amber
    });

    it('should handle empty allocations', () => {
      const emptyAllocation: AllocationData = {
        ...mockAllocation,
        channel_allocations: [],
        total_quantity_kg: 0,
      };

      const result = transformToSankeyFormat(emptyAllocation);

      expect(result.nodes).toHaveLength(1); // Only inventory node
      expect(result.links).toHaveLength(0);
    });

    it('should group multiple allocations of same channel type', () => {
      const multiAllocation: AllocationData = {
        ...mockAllocation,
        channel_allocations: [
          {
            channel_type: 'society',
            channel_id: 'soc-001',
            channel_name: 'Society A',
            quantity_kg: 300,
            price_per_kg: 30,
            revenue: 9000,
            priority: 1,
          },
          {
            channel_type: 'society',
            channel_id: 'soc-002',
            channel_name: 'Society B',
            quantity_kg: 200,
            price_per_kg: 30,
            revenue: 6000,
            priority: 1,
          },
        ],
        total_quantity_kg: 500,
      };

      const result = transformToSankeyFormat(multiAllocation);

      expect(result.nodes).toHaveLength(2); // Inventory + Societies (grouped)
      expect(result.links).toHaveLength(1);
      expect(result.links[0].value).toBe(500); // Combined quantity
    });
  });

  describe('transformToDetailedSankeyFormat', () => {
    it('should create individual nodes for multiple allocations of same type', () => {
      const multiAllocation: AllocationData = {
        ...mockAllocation,
        channel_allocations: [
          {
            channel_type: 'society',
            channel_id: 'soc-001',
            channel_name: 'Society A',
            quantity_kg: 300,
            price_per_kg: 30,
            revenue: 9000,
            priority: 1,
          },
          {
            channel_type: 'society',
            channel_id: 'soc-002',
            channel_name: 'Society B',
            quantity_kg: 200,
            price_per_kg: 30,
            revenue: 6000,
            priority: 1,
          },
        ],
        total_quantity_kg: 500,
      };

      const result = transformToDetailedSankeyFormat(multiAllocation);

      // Inventory + Societies + Society A + Society B
      expect(result.nodes.length).toBeGreaterThanOrEqual(4);
      expect(result.nodes.some(n => n.name === 'Society A')).toBe(true);
      expect(result.nodes.some(n => n.name === 'Society B')).toBe(true);
    });

    it('should not create individual nodes for single allocation per type', () => {
      const result = transformToDetailedSankeyFormat(mockAllocation);

      // Should only have Inventory + 3 channel types (no individual channels)
      expect(result.nodes).toHaveLength(4);
    });
  });

  describe('calculateChannelPercentages', () => {
    it('should calculate correct percentages for each channel', () => {
      const percentages = calculateChannelPercentages(mockAllocation);

      expect(percentages.society).toBe(50); // 500/1000
      expect(percentages.processing).toBe(30); // 300/1000
      expect(percentages.mandi).toBe(20); // 200/1000
    });

    it('should sum to 100%', () => {
      const percentages = calculateChannelPercentages(mockAllocation);
      const total = Object.values(percentages).reduce((sum, p) => sum + p, 0);

      expect(total).toBeCloseTo(100, 1);
    });

    it('should handle single channel allocation', () => {
      const singleChannelAllocation: AllocationData = {
        ...mockAllocation,
        channel_allocations: [
          {
            channel_type: 'society',
            channel_id: 'soc-001',
            channel_name: 'Green Valley Society',
            quantity_kg: 1000,
            price_per_kg: 30,
            revenue: 30000,
            priority: 1,
          },
        ],
        total_quantity_kg: 1000,
      };

      const percentages = calculateChannelPercentages(singleChannelAllocation);

      expect(percentages.society).toBe(100);
      expect(Object.keys(percentages)).toHaveLength(1);
    });
  });

  describe('getChannelColor', () => {
    it('should return correct colors for known channel types', () => {
      expect(getChannelColor('society')).toBe('#10b981');
      expect(getChannelColor('processing')).toBe('#8b5cf6');
      expect(getChannelColor('mandi')).toBe('#f59e0b');
      expect(getChannelColor('inventory')).toBe('#3b82f6');
    });

    it('should return default color for unknown channel types', () => {
      expect(getChannelColor('unknown')).toBe('#6b7280');
      expect(getChannelColor('custom')).toBe('#6b7280');
    });
  });
});
