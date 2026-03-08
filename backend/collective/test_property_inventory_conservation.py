"""
Property-based test for inventory conservation.

**Validates: Requirements 1.1, 1.3**

Property 1: Inventory Conservation
For any collective inventory, the sum of available, reserved, and allocated quantities
must equal the total quantity.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from hypothesis import given, strategies as st, assume
from hypothesis import settings

from backend.collective.models import (
    CollectiveInventory,
    FarmerContribution,
)
from backend.collective.models.collective_inventory import QualityGrade


# Hypothesis strategies for generating test data
@st.composite
def farmer_contribution_strategy(draw):
    """Generate a valid FarmerContribution."""
    farmer_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    farmer_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122)))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    # Generate positive quantities between 0.1 and 1000 kg
    quantity_kg = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("1000"), places=2))
    quality_grade = draw(st.sampled_from([QualityGrade.A, QualityGrade.B, QualityGrade.C]))
    
    return FarmerContribution(
        contribution_id=draw(st.uuids()).hex,
        farmer_id=farmer_id,
        farmer_name=farmer_name,
        crop_type=crop_type,
        quantity_kg=quantity_kg,
        quality_grade=quality_grade,
        timestamp=datetime.now(),
        allocated=False,
    )


@st.composite
def collective_inventory_strategy(draw):
    """Generate a valid CollectiveInventory with multiple contributions."""
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    
    # Generate 1 to 20 contributions for the same crop type
    num_contributions = draw(st.integers(min_value=1, max_value=20))
    contributions = []
    
    for _ in range(num_contributions):
        contribution = draw(farmer_contribution_strategy())
        # Override crop_type to match inventory
        contribution.crop_type = crop_type
        contributions.append(contribution)
    
    # Calculate totals from contributions
    total_quantity = sum(c.quantity_kg for c in contributions)
    
    # Generate reserved and allocated quantities that don't exceed total
    reserved_quantity = draw(st.decimals(
        min_value=Decimal("0"),
        max_value=total_quantity,
        places=2
    ))
    
    remaining = total_quantity - reserved_quantity
    allocated_quantity = draw(st.decimals(
        min_value=Decimal("0"),
        max_value=remaining,
        places=2
    ))
    
    available_quantity = total_quantity - reserved_quantity - allocated_quantity
    
    return CollectiveInventory(
        fpo_id=fpo_id,
        crop_type=crop_type,
        total_quantity_kg=total_quantity,
        available_quantity_kg=available_quantity,
        reserved_quantity_kg=reserved_quantity,
        allocated_quantity_kg=allocated_quantity,
        contributions=contributions,
        last_updated=datetime.now(),
    )


class TestInventoryConservation:
    """
    Property-based tests for inventory conservation.
    
    **Validates: Requirements 1.1, 1.3**
    """
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_inventory_conservation_property(self, inventory: CollectiveInventory):
        """
        Property 1: Inventory Conservation
        
        For any collective inventory, the sum of available, reserved, and allocated
        quantities must equal the total quantity.
        
        **Validates: Requirements 1.1, 1.3**
        """
        # Calculate sum of available, reserved, and allocated
        sum_quantities = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        
        # Property: available + reserved + allocated = total
        assert abs(inventory.total_quantity_kg - sum_quantities) < Decimal("0.01"), (
            f"Inventory conservation violated: "
            f"total_quantity={inventory.total_quantity_kg}, "
            f"available+reserved+allocated={sum_quantities}, "
            f"available={inventory.available_quantity_kg}, "
            f"reserved={inventory.reserved_quantity_kg}, "
            f"allocated={inventory.allocated_quantity_kg}"
        )
    
    @given(
        st.lists(farmer_contribution_strategy(), min_size=1, max_size=30)
    )
    @settings(max_examples=100, deadline=None)
    def test_conservation_after_sequential_contributions(self, contributions: list):
        """
        Test that inventory conservation holds after adding contributions sequentially.
        
        **Validates: Requirements 1.1, 1.3**
        """
        # Ensure all contributions are for the same crop type
        crop_type = contributions[0].crop_type
        for c in contributions:
            c.crop_type = crop_type
        
        # Start with empty inventory
        inventory = CollectiveInventory(
            fpo_id="test_fpo",
            crop_type=crop_type,
            total_quantity_kg=Decimal("0"),
            available_quantity_kg=Decimal("0"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Add contributions one by one
        for contribution in contributions:
            inventory.add_contribution(contribution)
            
            # After each addition, verify conservation property holds
            sum_quantities = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            
            assert abs(inventory.total_quantity_kg - sum_quantities) < Decimal("0.01"), (
                f"Conservation violated after adding contribution: "
                f"total={inventory.total_quantity_kg}, sum={sum_quantities}"
            )
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_conservation_after_reservation(self, inventory: CollectiveInventory):
        """
        Test that inventory conservation holds after reserving quantities.
        
        Reserving should move quantity from available to reserved without
        changing the total.
        
        **Validates: Requirements 1.1, 1.3**
        """
        # Record initial state
        initial_total = inventory.total_quantity_kg
        initial_sum = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        
        # Verify initial conservation
        assert abs(initial_total - initial_sum) < Decimal("0.01")
        
        # Reserve some quantity (if available)
        if inventory.available_quantity_kg > 0:
            # Reserve up to half of available quantity
            reserve_amount = min(
                inventory.available_quantity_kg / 2,
                inventory.available_quantity_kg
            )
            
            inventory.reserve_quantity(reserve_amount)
            
            # After reservation, verify conservation still holds
            final_sum = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            
            assert abs(inventory.total_quantity_kg - final_sum) < Decimal("0.01"), (
                f"Conservation violated after reservation: "
                f"total={inventory.total_quantity_kg}, sum={final_sum}"
            )
            
            # Total should not change
            assert abs(inventory.total_quantity_kg - initial_total) < Decimal("0.01"), (
                f"Total quantity changed after reservation: "
                f"initial={initial_total}, final={inventory.total_quantity_kg}"
            )
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_conservation_after_allocation(self, inventory: CollectiveInventory):
        """
        Test that inventory conservation holds after allocating quantities.
        
        Allocating should move quantity from available to allocated without
        changing the total.
        
        **Validates: Requirements 1.1, 1.3**
        """
        # Record initial state
        initial_total = inventory.total_quantity_kg
        initial_sum = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        
        # Verify initial conservation
        assert abs(initial_total - initial_sum) < Decimal("0.01")
        
        # Allocate some quantity (if available)
        if inventory.available_quantity_kg > 0:
            # Allocate up to half of available quantity
            allocate_amount = min(
                inventory.available_quantity_kg / 2,
                inventory.available_quantity_kg
            )
            
            inventory.allocate_quantity(allocate_amount)
            
            # After allocation, verify conservation still holds
            final_sum = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            
            assert abs(inventory.total_quantity_kg - final_sum) < Decimal("0.01"), (
                f"Conservation violated after allocation: "
                f"total={inventory.total_quantity_kg}, sum={final_sum}"
            )
            
            # Total should not change
            assert abs(inventory.total_quantity_kg - initial_total) < Decimal("0.01"), (
                f"Total quantity changed after allocation: "
                f"initial={initial_total}, final={inventory.total_quantity_kg}"
            )
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_conservation_after_mixed_operations(self, inventory: CollectiveInventory):
        """
        Test that inventory conservation holds after mixed operations
        (reservations and allocations).
        
        **Validates: Requirements 1.1, 1.3**
        """
        initial_total = inventory.total_quantity_kg
        
        # Perform multiple operations
        operations_performed = 0
        
        # Try to reserve some quantity
        if inventory.available_quantity_kg > Decimal("1"):
            reserve_amount = inventory.available_quantity_kg / 3
            inventory.reserve_quantity(reserve_amount)
            operations_performed += 1
            
            # Verify conservation after reservation
            sum_after_reserve = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            assert abs(inventory.total_quantity_kg - sum_after_reserve) < Decimal("0.01")
        
        # Try to allocate some quantity
        if inventory.available_quantity_kg > Decimal("1"):
            allocate_amount = inventory.available_quantity_kg / 2
            inventory.allocate_quantity(allocate_amount)
            operations_performed += 1
            
            # Verify conservation after allocation
            sum_after_allocate = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            assert abs(inventory.total_quantity_kg - sum_after_allocate) < Decimal("0.01")
        
        # Final verification
        final_sum = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        
        assert abs(inventory.total_quantity_kg - final_sum) < Decimal("0.01"), (
            f"Conservation violated after {operations_performed} operations: "
            f"total={inventory.total_quantity_kg}, sum={final_sum}"
        )
        
        # Total should remain unchanged
        assert abs(inventory.total_quantity_kg - initial_total) < Decimal("0.01")
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.lists(
            st.decimals(min_value=Decimal("0.1"), max_value=Decimal("500"), places=2),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_conservation_building_from_scratch(self, fpo_id: str, crop_type: str, quantities: list):
        """
        Test inventory conservation when building inventory from scratch
        with contributions, reservations, and allocations.
        
        **Validates: Requirements 1.1, 1.3**
        """
        inventory = CollectiveInventory(
            fpo_id=fpo_id,
            crop_type=crop_type,
            total_quantity_kg=Decimal("0"),
            available_quantity_kg=Decimal("0"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Add contributions
        for i, quantity in enumerate(quantities):
            contribution = FarmerContribution(
                contribution_id=f"contrib_{i}",
                farmer_id=f"farmer_{i}",
                farmer_name=f"Farmer {i}",
                crop_type=crop_type,
                quantity_kg=quantity,
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            )
            
            inventory.add_contribution(contribution)
            
            # Verify conservation after each contribution
            sum_quantities = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            assert abs(inventory.total_quantity_kg - sum_quantities) < Decimal("0.01")
        
        # Reserve some quantity
        if inventory.available_quantity_kg > Decimal("2"):
            reserve_amount = inventory.available_quantity_kg / 4
            inventory.reserve_quantity(reserve_amount)
            
            sum_after_reserve = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            assert abs(inventory.total_quantity_kg - sum_after_reserve) < Decimal("0.01")
        
        # Allocate some quantity
        if inventory.available_quantity_kg > Decimal("2"):
            allocate_amount = inventory.available_quantity_kg / 4
            inventory.allocate_quantity(allocate_amount)
            
            sum_after_allocate = (
                inventory.available_quantity_kg +
                inventory.reserved_quantity_kg +
                inventory.allocated_quantity_kg
            )
            assert abs(inventory.total_quantity_kg - sum_after_allocate) < Decimal("0.01")
        
        # Final verification
        final_sum = (
            inventory.available_quantity_kg +
            inventory.reserved_quantity_kg +
            inventory.allocated_quantity_kg
        )
        assert abs(inventory.total_quantity_kg - final_sum) < Decimal("0.01")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
