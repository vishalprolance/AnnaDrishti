"""
Realization service for blended realization and farmer income calculations
"""

from typing import List, Dict, Optional
from decimal import Decimal

from ..models import Allocation, ChannelAllocation, CollectiveInventory


class RealizationService:
    """
    Service for calculating blended realization and farmer income.
    
    Implements:
    - Blended realization calculation across all channels
    - Per-farmer income calculation based on contribution share
    - Channel-wise breakdown
    - Comparison to best single-channel price
    """
    
    def calculate_blended_realization(
        self,
        channel_allocations: List[ChannelAllocation],
    ) -> Decimal:
        """
        Calculate blended realization rate across all channels.
        
        Formula: blended_realization = total_revenue / total_quantity
        
        Args:
            channel_allocations: List of channel allocations
        
        Returns:
            Blended realization rate per kg
        
        Raises:
            ValueError: If channel_allocations is empty
        """
        if not channel_allocations:
            raise ValueError("Cannot calculate blended realization with no allocations")
        
        # Calculate total revenue across all channels
        total_revenue = sum(ca.revenue for ca in channel_allocations)
        
        # Calculate total quantity across all channels
        total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
        
        # Compute blended realization
        if total_quantity == 0:
            return Decimal("0")
        
        blended_realization = total_revenue / total_quantity
        
        return blended_realization
    
    def get_channel_breakdown(
        self,
        channel_allocations: List[ChannelAllocation],
    ) -> Dict[str, Dict[str, str]]:
        """
        Get breakdown of allocation by channel type.
        
        Args:
            channel_allocations: List of channel allocations
        
        Returns:
            Dictionary with channel breakdown:
            {
                "society": {"quantity_kg": "100", "revenue": "5000", "rate_per_kg": "50"},
                "processing": {"quantity_kg": "50", "revenue": "2250", "rate_per_kg": "45"},
                "mandi": {"quantity_kg": "30", "revenue": "900", "rate_per_kg": "30"}
            }
        """
        from ..models import ChannelType
        
        breakdown = {
            ChannelType.SOCIETY.value: {
                "quantity_kg": Decimal("0"),
                "revenue": Decimal("0"),
            },
            ChannelType.PROCESSING.value: {
                "quantity_kg": Decimal("0"),
                "revenue": Decimal("0"),
            },
            ChannelType.MANDI.value: {
                "quantity_kg": Decimal("0"),
                "revenue": Decimal("0"),
            },
        }
        
        # Aggregate by channel type
        for ca in channel_allocations:
            channel_key = ca.channel_type.value
            breakdown[channel_key]["quantity_kg"] += ca.quantity_kg
            breakdown[channel_key]["revenue"] += ca.revenue
        
        # Calculate rate per kg for each channel
        result = {}
        for channel, data in breakdown.items():
            qty = data["quantity_kg"]
            rev = data["revenue"]
            rate = rev / qty if qty > 0 else Decimal("0")
            
            result[channel] = {
                "quantity_kg": str(qty),
                "revenue": str(rev),
                "rate_per_kg": str(rate),
            }
        
        return result
    
    def get_best_single_channel_price(
        self,
        channel_allocations: List[ChannelAllocation],
    ) -> Decimal:
        """
        Get the best (highest) price per kg from all channels.
        
        Args:
            channel_allocations: List of channel allocations
        
        Returns:
            Best single channel price per kg
        """
        if not channel_allocations:
            return Decimal("0")
        
        return max(ca.price_per_kg for ca in channel_allocations)
    
    def calculate_farmer_income(
        self,
        farmer_id: str,
        allocation: Allocation,
        inventory: CollectiveInventory,
    ) -> Dict:
        """
        Calculate individual farmer income from collective allocation.
        
        Formula: farmer_income = (farmer_contribution / total_quantity) * total_revenue
        
        Args:
            farmer_id: Farmer identifier
            allocation: Allocation object with channel allocations
            inventory: Collective inventory with farmer contributions
        
        Returns:
            Dictionary with farmer income details:
            {
                "farmer_id": str,
                "contribution_kg": Decimal,
                "blended_rate_per_kg": Decimal,
                "total_revenue": Decimal,
                "channel_breakdown": List[dict],
                "vs_best_single_channel": dict
            }
        
        Raises:
            ValueError: If farmer has no contribution or allocation is empty
        """
        # Get farmer's contribution
        farmer_contributions = [
            c for c in inventory.contributions
            if c.farmer_id == farmer_id
        ]
        
        if not farmer_contributions:
            raise ValueError(f"Farmer {farmer_id} has no contributions in inventory")
        
        farmer_contribution_kg = sum(c.quantity_kg for c in farmer_contributions)
        
        # Handle empty allocation
        if not allocation.channel_allocations:
            return {
                "farmer_id": farmer_id,
                "contribution_kg": str(farmer_contribution_kg),
                "blended_rate_per_kg": "0",
                "total_revenue": "0",
                "channel_breakdown": [],
                "vs_best_single_channel": {
                    "single_channel_revenue": "0",
                    "improvement": "0",
                    "improvement_percentage": "0",
                },
            }
        
        # Calculate farmer's share of total revenue
        total_quantity = allocation.total_quantity_kg
        total_revenue = sum(ca.revenue for ca in allocation.channel_allocations)
        
        if total_quantity == 0:
            raise ValueError("Allocation has zero total quantity")
        
        farmer_revenue = (farmer_contribution_kg / total_quantity) * total_revenue
        farmer_rate = farmer_revenue / farmer_contribution_kg if farmer_contribution_kg > 0 else Decimal("0")
        
        # Calculate channel breakdown for this farmer
        channel_breakdown = []
        for ca in allocation.channel_allocations:
            # Farmer's proportional quantity in this channel
            farmer_qty_in_channel = (farmer_contribution_kg / total_quantity) * ca.quantity_kg
            channel_revenue = farmer_qty_in_channel * ca.price_per_kg
            
            channel_breakdown.append({
                "channel": ca.channel_type.value,
                "channel_name": ca.channel_name,
                "quantity_kg": str(farmer_qty_in_channel),
                "revenue": str(channel_revenue),
                "rate_per_kg": str(ca.price_per_kg),
            })
        
        # Compare to best single-channel
        best_single_channel_price = self.get_best_single_channel_price(allocation.channel_allocations)
        single_channel_revenue = farmer_contribution_kg * best_single_channel_price
        improvement = farmer_revenue - single_channel_revenue
        improvement_percentage = (improvement / single_channel_revenue * 100) if single_channel_revenue > 0 else Decimal("0")
        
        return {
            "farmer_id": farmer_id,
            "contribution_kg": str(farmer_contribution_kg),
            "blended_rate_per_kg": str(farmer_rate),
            "total_revenue": str(farmer_revenue),
            "channel_breakdown": channel_breakdown,
            "vs_best_single_channel": {
                "single_channel_revenue": str(single_channel_revenue),
                "improvement": str(improvement),
                "improvement_percentage": str(improvement_percentage),
            },
        }
    
    def calculate_all_farmer_incomes(
        self,
        allocation: Allocation,
        inventory: CollectiveInventory,
    ) -> List[Dict]:
        """
        Calculate income for all farmers in the inventory.
        
        Args:
            allocation: Allocation object
            inventory: Collective inventory with farmer contributions
        
        Returns:
            List of farmer income dictionaries
        """
        # Get unique farmer IDs
        farmer_ids = list(set(c.farmer_id for c in inventory.contributions))
        
        # Calculate income for each farmer
        farmer_incomes = []
        for farmer_id in farmer_ids:
            try:
                income = self.calculate_farmer_income(farmer_id, allocation, inventory)
                farmer_incomes.append(income)
            except ValueError as e:
                # Skip farmers with no contributions (shouldn't happen)
                print(f"Warning: Could not calculate income for farmer {farmer_id}: {e}")
        
        return farmer_incomes
    
    def get_realization_report(
        self,
        allocation: Allocation,
        inventory: CollectiveInventory,
    ) -> Dict:
        """
        Generate complete realization report with blended realization and farmer incomes.
        
        Args:
            allocation: Allocation object
            inventory: Collective inventory
        
        Returns:
            Complete realization report dictionary
        """
        # Calculate blended realization
        if allocation.channel_allocations:
            blended_realization = self.calculate_blended_realization(allocation.channel_allocations)
        else:
            blended_realization = Decimal("0")
        
        # Get channel breakdown
        channel_breakdown = self.get_channel_breakdown(allocation.channel_allocations)
        
        # Calculate farmer incomes
        farmer_incomes = self.calculate_all_farmer_incomes(allocation, inventory)
        
        # Get best single channel price
        best_single_channel = self.get_best_single_channel_price(allocation.channel_allocations)
        
        return {
            "allocation_id": allocation.allocation_id,
            "fpo_id": allocation.fpo_id,
            "crop_type": allocation.crop_type,
            "allocation_date": allocation.allocation_date.isoformat(),
            "blended_realization_per_kg": str(blended_realization),
            "total_quantity_kg": str(allocation.total_quantity_kg),
            "total_revenue": str(sum(ca.revenue for ca in allocation.channel_allocations)),
            "channel_breakdown": channel_breakdown,
            "best_single_channel_price": str(best_single_channel),
            "farmer_incomes": farmer_incomes,
            "num_farmers": len(farmer_incomes),
        }
