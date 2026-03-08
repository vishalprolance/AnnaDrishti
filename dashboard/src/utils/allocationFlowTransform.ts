/**
 * Utility functions for transforming allocation data to Sankey diagram format
 */

export interface ChannelAllocation {
  channel_type: string;
  channel_id: string;
  channel_name: string;
  quantity_kg: number;
  price_per_kg: number;
  revenue: number;
  priority: number;
}

export interface AllocationData {
  allocation_id: string;
  fpo_id: string;
  crop_type: string;
  allocation_date: string;
  channel_allocations: ChannelAllocation[];
  total_quantity_kg: number;
  blended_realization_per_kg: number;
}

export interface SankeyNode {
  name: string;
  color: string;
}

export interface SankeyLink {
  source: number;
  target: number;
  value: number;
  color: string;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// Color mapping for channel types
const CHANNEL_COLORS = {
  society: '#10b981', // green-500
  processing: '#8b5cf6', // purple-500
  mandi: '#f59e0b', // amber-500
  inventory: '#3b82f6', // blue-500
};

/**
 * Transform allocation data to Sankey diagram format
 * Creates a flow from "Collective Inventory" to each channel
 */
export function transformToSankeyFormat(allocation: AllocationData): SankeyData {
  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];

  // Add source node (Collective Inventory)
  nodes.push({
    name: 'Collective Inventory',
    color: CHANNEL_COLORS.inventory,
  });

  // Group allocations by channel type
  const channelGroups = groupByChannelType(allocation.channel_allocations);

  // Add nodes and links for each channel type
  Object.entries(channelGroups).forEach(([channelType, allocations]) => {
    const totalQuantity = allocations.reduce((sum, a) => sum + a.quantity_kg, 0);
    
    // Add channel type node
    const channelNodeIndex = nodes.length;
    nodes.push({
      name: formatChannelName(channelType),
      color: CHANNEL_COLORS[channelType as keyof typeof CHANNEL_COLORS] || '#6b7280',
    });

    // Add link from inventory to channel
    links.push({
      source: 0, // Collective Inventory
      target: channelNodeIndex,
      value: totalQuantity,
      color: CHANNEL_COLORS[channelType as keyof typeof CHANNEL_COLORS] || '#6b7280',
    });
  });

  return { nodes, links };
}

/**
 * Transform allocation data with individual channel details
 * Creates a flow from "Collective Inventory" → Channel Type → Individual Channels
 */
export function transformToDetailedSankeyFormat(allocation: AllocationData): SankeyData {
  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];

  // Add source node (Collective Inventory)
  nodes.push({
    name: 'Collective Inventory',
    color: CHANNEL_COLORS.inventory,
  });

  // Group allocations by channel type
  const channelGroups = groupByChannelType(allocation.channel_allocations);

  // Add nodes and links for each channel type and individual channels
  Object.entries(channelGroups).forEach(([channelType, allocations]) => {
    const channelColor = CHANNEL_COLORS[channelType as keyof typeof CHANNEL_COLORS] || '#6b7280';
    
    // Add channel type node
    const channelTypeNodeIndex = nodes.length;
    nodes.push({
      name: formatChannelName(channelType),
      color: channelColor,
    });

    // Calculate total for this channel type
    const totalQuantity = allocations.reduce((sum, a) => sum + a.quantity_kg, 0);

    // Add link from inventory to channel type
    links.push({
      source: 0, // Collective Inventory
      target: channelTypeNodeIndex,
      value: totalQuantity,
      color: channelColor,
    });

    // Add individual channel nodes and links (if more than one allocation per type)
    if (allocations.length > 1) {
      allocations.forEach((alloc) => {
        const individualNodeIndex = nodes.length;
        nodes.push({
          name: alloc.channel_name || `${channelType}-${alloc.channel_id}`,
          color: channelColor,
        });

        links.push({
          source: channelTypeNodeIndex,
          target: individualNodeIndex,
          value: alloc.quantity_kg,
          color: channelColor,
        });
      });
    }
  });

  return { nodes, links };
}

/**
 * Group channel allocations by channel type
 */
function groupByChannelType(allocations: ChannelAllocation[]): Record<string, ChannelAllocation[]> {
  return allocations.reduce((groups, allocation) => {
    const type = allocation.channel_type;
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(allocation);
    return groups;
  }, {} as Record<string, ChannelAllocation[]>);
}

/**
 * Format channel type name for display
 */
function formatChannelName(channelType: string): string {
  const names: Record<string, string> = {
    society: 'Societies',
    processing: 'Processing Partners',
    mandi: 'Mandi/Buyers',
  };
  return names[channelType] || channelType.charAt(0).toUpperCase() + channelType.slice(1);
}

/**
 * Calculate percentage of total for each channel
 */
export function calculateChannelPercentages(allocation: AllocationData): Record<string, number> {
  const total = allocation.total_quantity_kg;
  const channelGroups = groupByChannelType(allocation.channel_allocations);

  const percentages: Record<string, number> = {};
  Object.entries(channelGroups).forEach(([channelType, allocations]) => {
    const channelTotal = allocations.reduce((sum, a) => sum + a.quantity_kg, 0);
    percentages[channelType] = (channelTotal / total) * 100;
  });

  return percentages;
}

/**
 * Get color for channel type
 */
export function getChannelColor(channelType: string): string {
  return CHANNEL_COLORS[channelType as keyof typeof CHANNEL_COLORS] || '#6b7280';
}
