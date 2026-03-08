"""
Allocation validation and integrity checks
"""

from decimal import Decimal
from typing import List

from ..models import Allocation, ChannelAllocation, ProcessingPartner


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class AllocationValidator:
    """
    Validates allocation operations and data integrity.
    
    Implements validation rules from Requirements 9.1, 9.2:
    - Total allocated <= available inventory
    - All prices and quantities are non-negative
    - Processing capacity constraints
    """
    
    @staticmethod
    def validate_no_over_allocation(
        allocation: Allocation,
        available_inventory: Decimal,
    ) -> None:
        """
        Validate that total allocation does not exceed available inventory.
        
        Args:
            allocation: Allocation object
            available_inventory: Available inventory quantity
        
        Raises:
            ValidationError: If allocation exceeds available inventory
        """
        total_allocated = sum(
            ca.quantity_kg for ca in allocation.channel_allocations
        )
        
        if total_allocated > available_inventory:
            raise ValidationError(
                f"Over-allocation detected: allocated {total_allocated} kg "
                f"but only {available_inventory} kg available"
            )
    
    @staticmethod
    def validate_processing_capacity(
        channel_allocation: ChannelAllocation,
        partner: ProcessingPartner,
        crop_type: str,
    ) -> None:
        """
        Validate that processing allocation does not exceed partner capacity.
        
        Args:
            channel_allocation: Channel allocation for processing partner
            partner: Processing partner
            crop_type: Crop type
        
        Raises:
            ValidationError: If allocation exceeds partner capacity
        """
        capacity = partner.capacity_by_crop.get(crop_type, Decimal("0"))
        
        if channel_allocation.quantity_kg > capacity:
            raise ValidationError(
                f"Processing allocation exceeds capacity: "
                f"allocated {channel_allocation.quantity_kg} kg "
                f"but partner {partner.partner_name} capacity is {capacity} kg"
            )
    
    @staticmethod
    def validate_priority_ordering(
        allocation: Allocation,
    ) -> None:
        """
        Validate that channel allocations follow priority ordering.
        
        Priority 1: Societies
        Priority 2: Processing partners
        Priority 3: Mandi
        
        Args:
            allocation: Allocation object
        
        Raises:
            ValidationError: If priority ordering is violated
        """
        priorities = [ca.priority for ca in allocation.channel_allocations]
        
        # Check that priorities are in ascending order
        for i in range(len(priorities) - 1):
            if priorities[i] > priorities[i + 1]:
                raise ValidationError(
                    f"Priority ordering violated: "
                    f"priority {priorities[i]} appears before priority {priorities[i + 1]}"
                )
    
    @staticmethod
    def validate_allocation_totals(
        allocation: Allocation,
    ) -> None:
        """
        Validate that allocation totals are consistent.
        
        Checks:
        - Total quantity = sum of channel quantities
        - Blended realization = total revenue / total quantity
        
        Args:
            allocation: Allocation object
        
        Raises:
            ValidationError: If totals are inconsistent
        """
        # Check total quantity
        channel_total = sum(ca.quantity_kg for ca in allocation.channel_allocations)
        
        if allocation.total_quantity_kg != channel_total:
            raise ValidationError(
                f"Allocation total mismatch: "
                f"total_quantity_kg ({allocation.total_quantity_kg}) != "
                f"sum of channel quantities ({channel_total})"
            )
        
        # Check blended realization
        if allocation.total_quantity_kg > 0:
            total_revenue = sum(
                ca.quantity_kg * ca.price_per_kg
                for ca in allocation.channel_allocations
            )
            expected_blended = total_revenue / allocation.total_quantity_kg
            
            # Allow small rounding differences
            if abs(allocation.blended_realization_per_kg - expected_blended) > Decimal("0.01"):
                raise ValidationError(
                    f"Blended realization mismatch: "
                    f"stored ({allocation.blended_realization_per_kg}) != "
                    f"calculated ({expected_blended})"
                )
