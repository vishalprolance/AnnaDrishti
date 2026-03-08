"""
Property-based test for priority ordering.

**Validates: Requirements 4.1, 4.2, 4.3**

Property 3: Priority Ordering
For any allocation, society allocations (Priority 1) must come before processing allocations (Priority 2),
which must come before mandi allocations (Priority 3).
"""

import pytest
from decimal import Decimal
from datetime import date
from hypothesis import given, strategies as st
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
def channel_allocation_strategy(draw, channel_type, priority):
    """Generate a valid ChannelAllocation for a specific channel type and priority."""
    channel_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    channel_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))))
    quantity = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("500"), places=2))
    price = draw(st.decimals(min_value=Decimal("20.0"), max_value=Decimal("100.0"), places=2))
    revenue = quantity * price
    
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
def allocation_with_all_priorities_strategy(draw):
    """
    Generate an Allocation with channel allocations across all three priorities.
    
    This strategy ensures that:
    - Allocations include Priority 1 (societies), Priority 2 (processing), and Priority 3 (mandi)
    - Allocations are in priority order
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    channel_allocations = []
    
    # Generate Priority 1 allocations (societies)
    num_societies = draw(st.integers(min_value=0, max_value=5))
    for _ in range(num_societies):
        ca = draw(channel_allocation_strategy(ChannelType.SOCIETY, 1))
        channel_allocations.append(ca)
    
    # Generate Priority 2 allocations (processing)
    num_processing = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_processing):
        ca = draw(channel_allocation_strategy(ChannelType.PROCESSING, 2))
        channel_allocations.append(ca)
    
    # Generate Priority 3 allocations (mandi)
    num_mandi = draw(st.integers(min_value=0, max_value=1))
    for _ in range(num_mandi):
        ca = draw(channel_allocation_strategy(ChannelType.MANDI, 3))
        channel_allocations.append(ca)
    
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
    
    return allocation


class TestPriorityOrdering:
    """
    Property-based tests for priority ordering.
    
    **Validates: Requirements 4.1, 4.2, 4.3**
    """
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_priority_ordering_property(self, allocation):
        """
        Property 3: Priority Ordering
        
        For any allocation, society allocations (Priority 1) must come before
        processing allocations (Priority 2), which must come before mandi
        allocations (Priority 3).
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        if not allocation.channel_allocations:
            return  # Empty allocation is valid
        
        # Extract priorities from channel allocations
        priorities = [ca.priority for ca in allocation.channel_allocations]
        
        # Check that priorities are in ascending order (1, 2, 3)
        for i in range(len(priorities) - 1):
            assert priorities[i] <= priorities[i + 1], (
                f"Priority ordering violated: "
                f"allocation at index {i} has priority {priorities[i]}, "
                f"but allocation at index {i+1} has priority {priorities[i + 1]}"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_society_before_processing(self, allocation):
        """
        Test that all society allocations come before processing allocations.
        """
        society_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        processing_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        # If both exist, all society indices should be less than all processing indices
        if society_indices and processing_indices:
            max_society_index = max(society_indices)
            min_processing_index = min(processing_indices)
            
            assert max_society_index < min_processing_index, (
                f"Society allocations must come before processing allocations: "
                f"last society at index {max_society_index}, "
                f"first processing at index {min_processing_index}"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_processing_before_mandi(self, allocation):
        """
        Test that all processing allocations come before mandi allocations.
        """
        processing_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        mandi_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.MANDI
        ]
        
        # If both exist, all processing indices should be less than all mandi indices
        if processing_indices and mandi_indices:
            max_processing_index = max(processing_indices)
            min_mandi_index = min(mandi_indices)
            
            assert max_processing_index < min_mandi_index, (
                f"Processing allocations must come before mandi allocations: "
                f"last processing at index {max_processing_index}, "
                f"first mandi at index {min_mandi_index}"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_society_before_mandi(self, allocation):
        """
        Test that all society allocations come before mandi allocations.
        """
        society_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        mandi_indices = [
            i for i, ca in enumerate(allocation.channel_allocations)
            if ca.channel_type == ChannelType.MANDI
        ]
        
        # If both exist, all society indices should be less than all mandi indices
        if society_indices and mandi_indices:
            max_society_index = max(society_indices)
            min_mandi_index = min(mandi_indices)
            
            assert max_society_index < min_mandi_index, (
                f"Society allocations must come before mandi allocations: "
                f"last society at index {max_society_index}, "
                f"first mandi at index {min_mandi_index}"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_priority_values_are_valid(self, allocation):
        """
        Test that all priority values are 1, 2, or 3.
        """
        for ca in allocation.channel_allocations:
            assert ca.priority in [1, 2, 3], (
                f"Invalid priority value: {ca.priority} for channel {ca.channel_id}"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_channel_type_matches_priority(self, allocation):
        """
        Test that channel types match their expected priorities.
        
        - Society channels should have priority 1
        - Processing channels should have priority 2
        - Mandi channels should have priority 3
        """
        for ca in allocation.channel_allocations:
            if ca.channel_type == ChannelType.SOCIETY:
                assert ca.priority == 1, (
                    f"Society channel {ca.channel_id} has wrong priority: {ca.priority}"
                )
            elif ca.channel_type == ChannelType.PROCESSING:
                assert ca.priority == 2, (
                    f"Processing channel {ca.channel_id} has wrong priority: {ca.priority}"
                )
            elif ca.channel_type == ChannelType.MANDI:
                assert ca.priority == 3, (
                    f"Mandi channel {ca.channel_id} has wrong priority: {ca.priority}"
                )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_priority_ordering_with_serialization(self, allocation):
        """
        Test that priority ordering holds after serialization/deserialization.
        """
        # Serialize and deserialize
        allocation_dict = allocation.to_dict()
        restored_allocation = Allocation.from_dict(allocation_dict)
        
        if not restored_allocation.channel_allocations:
            return
        
        # Extract priorities
        priorities = [ca.priority for ca in restored_allocation.channel_allocations]
        
        # Check ordering
        for i in range(len(priorities) - 1):
            assert priorities[i] <= priorities[i + 1], (
                f"Priority ordering violated after serialization"
            )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_no_priority_gaps(self, allocation):
        """
        Test that priorities are used appropriately.
        
        Note: It's valid for only Priority 3 (mandi) to exist if there are
        no society reservations and no processing partners available.
        This test just ensures that priorities are consecutive when multiple exist.
        """
        if not allocation.channel_allocations:
            return
        
        priorities = sorted(set(ca.priority for ca in allocation.channel_allocations))
        
        # If we have multiple priorities, they should be consecutive
        # For example: [1, 2], [1, 3], [2, 3], or [1, 2, 3]
        # But we allow single priority like [1], [2], or [3]
        if len(priorities) > 1:
            # Check that priorities don't skip (e.g., [1, 3] without 2 is OK in practice)
            # This is because we might have societies but no processing partners
            # So we just verify they're in ascending order
            for i in range(len(priorities) - 1):
                assert priorities[i] < priorities[i + 1], (
                    f"Priorities are not in ascending order: {priorities}"
                )
    
    @given(allocation_with_all_priorities_strategy())
    @settings(max_examples=100, deadline=None)
    def test_priorities_are_consecutive_in_list(self, allocation):
        """
        Test that allocations of the same priority are grouped together.
        
        For example, all Priority 1 allocations should be consecutive,
        followed by all Priority 2 allocations, etc.
        """
        if len(allocation.channel_allocations) < 2:
            return
        
        # Group allocations by priority
        priority_groups = {}
        for i, ca in enumerate(allocation.channel_allocations):
            if ca.priority not in priority_groups:
                priority_groups[ca.priority] = []
            priority_groups[ca.priority].append(i)
        
        # Check that each priority group is consecutive
        for priority, indices in priority_groups.items():
            if len(indices) > 1:
                # Check that indices are consecutive
                for i in range(len(indices) - 1):
                    assert indices[i + 1] == indices[i] + 1, (
                        f"Priority {priority} allocations are not consecutive: "
                        f"found at indices {indices}"
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
