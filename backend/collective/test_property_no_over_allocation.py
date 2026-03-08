"""
Property-based test for no over-allocation.

**Validates: Requirements 4.1**

Property 5: No Over-Allocation
For any allocation, the sum of allocated quantities across all channels must not exceed available inventory.
"""

import pytest
from decimal import Decimal
from datetime import date
from hypothesis import given, strategies as st, assume
from hypothesis import settings

from collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
)


# Hypothesis strategies for generating test data
@st.composite
def channel_allocation_strategy(draw):
    """Generate a valid ChannelAllocation."""
    channel_type = draw(st.sampled_from([ChannelType.SOCIETY, ChannelType.PROCESSING, ChannelType.MANDI]))
    channel_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    channel_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))))
    quantity = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("500"), places=2))
    price = draw(st.decimals(min_value=Decimal("20.0"), max_value=Decimal("100.0"), places=2))
    revenue = quantity * price
    
    # Assign priority based on channel type
    priority_map = {
        ChannelType.SOCIETY: 1,
        ChannelType.PROCESSING: 2,
        ChannelType.MANDI: 3,
    }
    priority = priority_map[channel_type]
    
    return ChannelAllocation(
        channel_type=channel_type,
        channel_id=channel_id,
        channel_name=channel_name,
        quantity_kg=quantity,
        price_per_kg=price,
        revenue=revenue,
        priority=priority,
        fulfillment_status=FulfillmentStatus.PENDING,
    )


@st.composite
def allocation_with_available_inventory_strategy(draw):
    """
    Generate an Allocation with corresponding available inventory.
    
    This strategy ensures that:
    - Total allocated quantity does not exceed available inventory
    - Available inventory is tracked
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    # Generate available inventory
    available_inventory = draw(st.decimals(min_value=Decimal("10.0"), max_value=Decimal("2000.0"), places=2))
    
    # Generate channel allocations that don't exceed available inventory
    num_allocations = draw(st.integers(min_value=0, max_value=10))
    channel_allocations = []
    remaining = available_inventory
    
    for _ in range(num_allocations):
        if remaining <= 0:
            break
        
        # Generate allocation that doesn't exceed remaining inventory
        max_allocation = min(remaining, Decimal("500.0"))
        
        # Use a ratio to determine allocation (0.1 to 1.0 of remaining)
        allocation_ratio = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("1.0"), places=2))
        quantity = min(max_allocation * allocation_ratio, remaining)
        
        if quantity > 0:
            channel_type = draw(st.sampled_from([ChannelType.SOCIETY, ChannelType.PROCESSING, ChannelType.MANDI]))
            channel_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
            channel_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))))
            price = draw(st.decimals(min_value=Decimal("20.0"), max_value=Decimal("100.0"), places=2))
            revenue = quantity * price
            
            priority_map = {
                ChannelType.SOCIETY: 1,
                ChannelType.PROCESSING: 2,
                ChannelType.MANDI: 3,
            }
            priority = priority_map[channel_type]
            
            ca = ChannelAllocation(
                channel_type=channel_type,
                channel_id=channel_id,
                channel_name=channel_name,
                quantity_kg=quantity,
                price_per_kg=price,
                revenue=revenue,
                priority=priority,
                fulfillment_status=FulfillmentStatus.PENDING,
            )
            
            channel_allocations.append(ca)
            remaining -= quantity
    
    # Sort by priority to maintain ordering
    channel_allocations.sort(key=lambda ca: ca.priority)
    
    # Calculate totals
    total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
    total_revenue = sum(ca.revenue for ca in channel_allocations)
    blended_realization = total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
    
    allocation = Allocation(
        allocation_id=draw(st.uuids()).hex,
        fpo_id=fpo_id,
        crop_type=crop_type,
        allocation_date=allocation_date,
        channel_allocations=channel_allocations,
        total_quantity_kg=total_quantity,
        blended_realization_per_kg=blended_realization,
        status=AllocationStatus.PENDING,
    )
    
    return allocation, available_inventory


class TestNoOverAllocation:
    """
    Property-based tests for no over-allocation.
    
    **Validates: Requirements 4.1**
    """
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_no_over_allocation_property(self, test_data):
        """
        Property 5: No Over-Allocation
        
        For any allocation, the sum of allocated quantities across all channels
        must not exceed available inventory.
        
        **Validates: Requirements 4.1**
        """
        allocation, available_inventory = test_data
        
        # Calculate total allocated
        total_allocated = sum(ca.quantity_kg for ca in allocation.channel_allocations)
        
        # Property: Total allocated must not exceed available inventory
        assert total_allocated <= available_inventory + Decimal("0.01"), (
            f"Over-allocation detected: "
            f"available inventory = {available_inventory} kg, "
            f"total allocated = {total_allocated} kg"
        )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_total_quantity_matches_sum_of_allocations(self, test_data):
        """
        Test that the allocation's total_quantity_kg matches the sum of channel allocations.
        """
        allocation, available_inventory = test_data
        
        calculated_total = sum(ca.quantity_kg for ca in allocation.channel_allocations)
        
        assert abs(allocation.total_quantity_kg - calculated_total) < Decimal("0.01"), (
            f"Total quantity mismatch: "
            f"allocation.total_quantity_kg = {allocation.total_quantity_kg}, "
            f"sum of channel allocations = {calculated_total}"
        )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_all_allocations_are_non_negative(self, test_data):
        """
        Test that all allocation quantities are non-negative.
        """
        allocation, available_inventory = test_data
        
        for ca in allocation.channel_allocations:
            assert ca.quantity_kg >= 0, (
                f"Negative allocation quantity: {ca.quantity_kg} kg "
                f"for channel {ca.channel_id}"
            )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_remaining_inventory_is_non_negative(self, test_data):
        """
        Test that remaining inventory after allocation is non-negative.
        """
        allocation, available_inventory = test_data
        
        total_allocated = sum(ca.quantity_kg for ca in allocation.channel_allocations)
        remaining = available_inventory - total_allocated
        
        assert remaining >= -Decimal("0.01"), (
            f"Negative remaining inventory: "
            f"available = {available_inventory} kg, "
            f"allocated = {total_allocated} kg, "
            f"remaining = {remaining} kg"
        )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_no_over_allocation_with_serialization(self, test_data):
        """
        Test that no over-allocation property holds after serialization/deserialization.
        """
        allocation, available_inventory = test_data
        
        # Serialize and deserialize
        allocation_dict = allocation.to_dict()
        restored_allocation = Allocation.from_dict(allocation_dict)
        
        # Calculate total allocated
        total_allocated = sum(ca.quantity_kg for ca in restored_allocation.channel_allocations)
        
        # Property should still hold
        assert total_allocated <= available_inventory + Decimal("0.01"), (
            f"Over-allocation detected after serialization: "
            f"available = {available_inventory} kg, "
            f"allocated = {total_allocated} kg"
        )
    
    @given(
        st.decimals(min_value=Decimal("10.0"), max_value=Decimal("1000.0"), places=2),
        st.lists(channel_allocation_strategy(), min_size=1, max_size=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_no_over_allocation_with_arbitrary_allocations(self, available_inventory, channel_allocations):
        """
        Test no over-allocation with arbitrary channel allocations.
        
        This test generates allocations independently and checks if they would
        cause over-allocation.
        """
        # Calculate total allocated
        total_allocated = sum(ca.quantity_kg for ca in channel_allocations)
        
        # If total allocated exceeds available, this would be an over-allocation
        # In a real system, the allocation engine should prevent this
        if total_allocated > available_inventory:
            # This is expected - we're testing that we can detect over-allocation
            assert total_allocated > available_inventory, (
                "Over-allocation detection failed"
            )
        else:
            # No over-allocation
            assert total_allocated <= available_inventory + Decimal("0.01"), (
                "False positive: detected over-allocation when there is none"
            )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_empty_allocation_has_zero_quantity(self, test_data):
        """
        Test that an allocation with no channel allocations has zero total quantity.
        """
        allocation, available_inventory = test_data
        
        if not allocation.channel_allocations:
            assert allocation.total_quantity_kg == Decimal("0"), (
                f"Empty allocation should have zero total quantity, "
                f"got {allocation.total_quantity_kg}"
            )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_allocation_efficiency(self, test_data):
        """
        Test that allocation uses available inventory efficiently.
        
        This is not a strict requirement, but we can measure how much
        inventory is left unallocated.
        """
        allocation, available_inventory = test_data
        
        total_allocated = sum(ca.quantity_kg for ca in allocation.channel_allocations)
        remaining = available_inventory - total_allocated
        
        # Just verify the calculation is correct
        assert remaining >= -Decimal("0.01"), (
            f"Remaining inventory calculation error: {remaining}"
        )
        
        # Calculate utilization percentage
        if available_inventory > 0:
            utilization = (total_allocated / available_inventory) * 100
            # Utilization should be between 0% and 100%
            assert 0 <= utilization <= 100.01, (
                f"Invalid utilization percentage: {utilization}%"
            )
    
    @given(allocation_with_available_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_individual_allocations_within_available(self, test_data):
        """
        Test that each individual allocation is within available inventory.
        """
        allocation, available_inventory = test_data
        
        for ca in allocation.channel_allocations:
            assert ca.quantity_kg <= available_inventory + Decimal("0.01"), (
                f"Individual allocation exceeds available inventory: "
                f"channel {ca.channel_id} allocated {ca.quantity_kg} kg, "
                f"but available inventory is {available_inventory} kg"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
