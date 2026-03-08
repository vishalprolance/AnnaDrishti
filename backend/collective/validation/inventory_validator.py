"""
Inventory validation and integrity checks
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from ..models import CollectiveInventory, FarmerContribution, Allocation


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class InventoryValidator:
    """
    Validates inventory operations and data integrity.
    
    Implements validation rules from Requirements 9.1, 9.2, 9.3:
    - Total allocated <= available inventory
    - All prices and quantities are non-negative
    - Prevent deletion of allocated contributions
    """
    
    @staticmethod
    def validate_inventory_allocation(
        inventory: CollectiveInventory,
        allocation_quantity: Decimal,
    ) -> None:
        """
        Validate that allocation does not exceed available inventory.
        
        Args:
            inventory: Collective inventory
            allocation_quantity: Quantity to allocate
        
        Raises:
            ValidationError: If allocation exceeds available inventory
        """
        if allocation_quantity < 0:
            raise ValidationError(
                f"Allocation quantity must be non-negative, got {allocation_quantity}"
            )
        
        if allocation_quantity > inventory.available_quantity_kg:
            raise ValidationError(
                f"Cannot allocate {allocation_quantity} kg: only "
                f"{inventory.available_quantity_kg} kg available "
                f"(total: {inventory.total_quantity_kg} kg, "
                f"reserved: {inventory.reserved_quantity_kg} kg, "
                f"allocated: {inventory.allocated_quantity_kg} kg)"
            )
    
    @staticmethod
    def validate_inventory_reservation(
        inventory: CollectiveInventory,
        reservation_quantity: Decimal,
    ) -> None:
        """
        Validate that reservation does not exceed available inventory.
        
        Args:
            inventory: Collective inventory
            reservation_quantity: Quantity to reserve
        
        Raises:
            ValidationError: If reservation exceeds available inventory
        """
        if reservation_quantity < 0:
            raise ValidationError(
                f"Reservation quantity must be non-negative, got {reservation_quantity}"
            )
        
        if reservation_quantity > inventory.available_quantity_kg:
            raise ValidationError(
                f"Cannot reserve {reservation_quantity} kg: only "
                f"{inventory.available_quantity_kg} kg available"
            )
    
    @staticmethod
    def validate_quantities_non_negative(
        inventory: CollectiveInventory,
    ) -> None:
        """
        Validate that all inventory quantities are non-negative.
        
        Args:
            inventory: Collective inventory
        
        Raises:
            ValidationError: If any quantity is negative
        """
        if inventory.total_quantity_kg < 0:
            raise ValidationError(
                f"Total quantity cannot be negative: {inventory.total_quantity_kg}"
            )
        
        if inventory.available_quantity_kg < 0:
            raise ValidationError(
                f"Available quantity cannot be negative: {inventory.available_quantity_kg}"
            )
        
        if inventory.reserved_quantity_kg < 0:
            raise ValidationError(
                f"Reserved quantity cannot be negative: {inventory.reserved_quantity_kg}"
            )
        
        if inventory.allocated_quantity_kg < 0:
            raise ValidationError(
                f"Allocated quantity cannot be negative: {inventory.allocated_quantity_kg}"
            )
    
    @staticmethod
    def validate_contribution_quantities(
        contributions: List[FarmerContribution],
    ) -> None:
        """
        Validate that all contribution quantities are non-negative.
        
        Args:
            contributions: List of farmer contributions
        
        Raises:
            ValidationError: If any contribution quantity is negative
        """
        for contribution in contributions:
            if contribution.quantity_kg < 0:
                raise ValidationError(
                    f"Contribution quantity cannot be negative: "
                    f"farmer {contribution.farmer_id} has {contribution.quantity_kg} kg"
                )
    
    @staticmethod
    def validate_allocation_prices(
        allocation: Allocation,
    ) -> None:
        """
        Validate that all prices in allocation are non-negative.
        
        Args:
            allocation: Allocation object
        
        Raises:
            ValidationError: If any price is negative
        """
        if allocation.blended_realization_per_kg < 0:
            raise ValidationError(
                f"Blended realization cannot be negative: "
                f"{allocation.blended_realization_per_kg}"
            )
        
        for channel_alloc in allocation.channel_allocations:
            if channel_alloc.price_per_kg < 0:
                raise ValidationError(
                    f"Price cannot be negative for channel {channel_alloc.channel_type}: "
                    f"{channel_alloc.price_per_kg}"
                )
            
            if channel_alloc.quantity_kg < 0:
                raise ValidationError(
                    f"Quantity cannot be negative for channel {channel_alloc.channel_type}: "
                    f"{channel_alloc.quantity_kg}"
                )
            
            if channel_alloc.revenue < 0:
                raise ValidationError(
                    f"Revenue cannot be negative for channel {channel_alloc.channel_type}: "
                    f"{channel_alloc.revenue}"
                )
    
    @staticmethod
    def validate_contribution_deletion(
        contribution: FarmerContribution,
    ) -> None:
        """
        Validate that contribution can be deleted (not allocated).
        
        Args:
            contribution: Farmer contribution
        
        Raises:
            ValidationError: If contribution is already allocated
        """
        if contribution.allocated:
            raise ValidationError(
                f"Cannot delete contribution {contribution.contribution_id}: "
                f"already allocated to a channel"
            )
    
    @staticmethod
    def validate_inventory_invariants(
        inventory: CollectiveInventory,
    ) -> None:
        """
        Validate all inventory invariants.
        
        Checks:
        - All quantities are non-negative
        - Total = available + reserved + allocated
        - Total = sum of contributions
        
        Args:
            inventory: Collective inventory
        
        Raises:
            ValidationError: If any invariant is violated
        """
        # Check non-negative quantities
        InventoryValidator.validate_quantities_non_negative(inventory)
        
        # Check contribution quantities
        InventoryValidator.validate_contribution_quantities(inventory.contributions)
        
        # Check inventory conservation
        expected_total = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        
        if inventory.total_quantity_kg != expected_total:
            raise ValidationError(
                f"Inventory conservation violated: "
                f"total ({inventory.total_quantity_kg}) != "
                f"available ({inventory.available_quantity_kg}) + "
                f"reserved ({inventory.reserved_quantity_kg}) + "
                f"allocated ({inventory.allocated_quantity_kg})"
            )
        
        # Check contribution aggregation
        contribution_total = sum(c.quantity_kg for c in inventory.contributions)
        if inventory.total_quantity_kg != contribution_total:
            raise ValidationError(
                f"Contribution aggregation violated: "
                f"total ({inventory.total_quantity_kg}) != "
                f"sum of contributions ({contribution_total})"
            )
