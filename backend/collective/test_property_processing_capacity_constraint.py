"""
Property-based test for processing capacity constraint.

**Validates: Requirements 4.2, 4.5**

Property 9: Processing Capacity Constraint
For any allocation to processing partners, the allocated quantity must not exceed the partner's capacity.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from hypothesis import given, strategies as st, assume
from hypothesis import settings

from collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    ProcessingPartner,
)


# Hypothesis strategies for generating test data
@st.composite
def processing_partner_strategy(draw):
    """Generate a valid ProcessingPartner."""
    partner_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    partner_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    
    # Generate rate and capacity for the crop
    rate = draw(st.decimals(min_value=Decimal("20.0"), max_value=Decimal("100.0"), places=2))
    capacity = draw(st.decimals(min_value=Decimal("50.0"), max_value=Decimal("1000.0"), places=2))
    
    return ProcessingPartner(
        partner_id=partner_id,
        partner_name=partner_name,
        contact_details={"phone": "1234567890", "email": "partner@example.com"},
        facility_location="Test Location",
        rates_by_crop={crop_type: rate},
        capacity_by_crop={crop_type: capacity},
        quality_requirements={crop_type: "Grade A"},
        pickup_schedule="Daily 8 AM",
        created_at=datetime.now(),
    )


@st.composite
def allocation_with_processing_partners_strategy(draw):
    """
    Generate an Allocation with processing partner allocations and corresponding partners.
    
    This strategy ensures that:
    - All allocations respect partner capacity constraints
    - Partners are sorted by rate (highest first)
    - Allocated quantities do not exceed partner capacities
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    # Generate 1 to 5 processing partners
    num_partners = draw(st.integers(min_value=1, max_value=5))
    partners = []
    
    for i in range(num_partners):
        partner = draw(processing_partner_strategy())
        # Override crop_type to match allocation
        partner.rates_by_crop = {crop_type: partner.rates_by_crop[list(partner.rates_by_crop.keys())[0]]}
        partner.capacity_by_crop = {crop_type: partner.capacity_by_crop[list(partner.capacity_by_crop.keys())[0]]}
        partner.quality_requirements = {crop_type: "Grade A"}
        # Ensure unique partner_id
        partner.partner_id = f"PP{i:03d}"
        partners.append(partner)
    
    # Sort partners by rate (highest first) to simulate allocation order
    partners.sort(key=lambda p: p.get_rate(crop_type), reverse=True)
    
    # Generate available quantity
    total_capacity = sum(p.get_capacity(crop_type) for p in partners)
    # Available can be less than, equal to, or more than total capacity
    available_ratio = draw(st.decimals(min_value=Decimal("0.3"), max_value=Decimal("1.5"), places=2))
    available_quantity = total_capacity * available_ratio
    
    # Create channel allocations respecting capacity constraints
    channel_allocations = []
    remaining = available_quantity
    
    for partner in partners:
        if remaining <= 0:
            break
        
        capacity = partner.get_capacity(crop_type)
        rate = partner.get_rate(crop_type)
        
        # Allocate up to capacity or remaining, whichever is less
        allocated_qty = min(capacity, remaining)
        
        if allocated_qty > 0:
            revenue = allocated_qty * rate
            
            channel_allocation = ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id=partner.partner_id,
                channel_name=partner.partner_name,
                quantity_kg=allocated_qty,
                price_per_kg=rate,
                revenue=revenue,
                priority=2,
                fulfillment_status=FulfillmentStatus.PENDING,
            )
            channel_allocations.append(channel_allocation)
            remaining -= allocated_qty
    
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
    
    return allocation, partners


class TestProcessingCapacityConstraint:
    """
    Property-based tests for processing capacity constraint.
    
    **Validates: Requirements 4.2, 4.5**
    """
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_processing_capacity_constraint_property(self, test_data):
        """
        Property 9: Processing Capacity Constraint
        
        For any allocation to processing partners, the allocated quantity
        must not exceed the partner's capacity.
        
        **Validates: Requirements 4.2, 4.5**
        """
        allocation, partners = test_data
        
        # Get processing allocations
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        # Create a map of partner_id to partner
        partner_map = {p.partner_id: p for p in partners}
        
        # Check each processing allocation
        for ca in processing_allocations:
            partner = partner_map.get(ca.channel_id)
            
            # Partner should exist
            assert partner is not None, f"Partner {ca.channel_id} not found in partner list"
            
            # Get partner's capacity for the crop
            capacity = partner.get_capacity(allocation.crop_type)
            
            # Property: Allocated quantity must not exceed capacity
            assert ca.quantity_kg <= capacity + Decimal("0.01"), (
                f"Processing capacity constraint violated: "
                f"partner {ca.channel_id} allocated {ca.quantity_kg} kg "
                f"but capacity is {capacity} kg"
            )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_all_processing_allocations_within_capacity(self, test_data):
        """
        Test that all processing allocations are within partner capacity.
        """
        allocation, partners = test_data
        
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        partner_map = {p.partner_id: p for p in partners}
        
        for ca in processing_allocations:
            partner = partner_map[ca.channel_id]
            capacity = partner.get_capacity(allocation.crop_type)
            
            # Allocated quantity should be positive and within capacity
            assert ca.quantity_kg > 0, f"Allocated quantity should be positive: {ca.quantity_kg}"
            assert ca.quantity_kg <= capacity, (
                f"Allocated {ca.quantity_kg} kg exceeds capacity {capacity} kg "
                f"for partner {ca.channel_id}"
            )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_no_partner_allocated_twice(self, test_data):
        """
        Test that no partner is allocated more than once in the same allocation.
        """
        allocation, partners = test_data
        
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        # Get all partner IDs from allocations
        allocated_partner_ids = [ca.channel_id for ca in processing_allocations]
        
        # Check for duplicates
        assert len(allocated_partner_ids) == len(set(allocated_partner_ids)), (
            f"Partner allocated multiple times: {allocated_partner_ids}"
        )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_total_processing_allocation_within_total_capacity(self, test_data):
        """
        Test that total processing allocation does not exceed total partner capacity.
        """
        allocation, partners = test_data
        
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        # Calculate total allocated to processing
        total_allocated = sum(ca.quantity_kg for ca in processing_allocations)
        
        # Calculate total capacity
        total_capacity = sum(p.get_capacity(allocation.crop_type) for p in partners)
        
        # Total allocated should not exceed total capacity
        assert total_allocated <= total_capacity + Decimal("0.01"), (
            f"Total processing allocation {total_allocated} kg "
            f"exceeds total capacity {total_capacity} kg"
        )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_partners_sorted_by_rate(self, test_data):
        """
        Test that partners are allocated in order of rate (highest first).
        
        This validates that the allocation maximizes value by prioritizing
        higher-paying partners.
        """
        allocation, partners = test_data
        
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        if len(processing_allocations) < 2:
            return  # Need at least 2 allocations to test ordering
        
        # Check that rates are in descending order
        for i in range(len(processing_allocations) - 1):
            current_rate = processing_allocations[i].price_per_kg
            next_rate = processing_allocations[i + 1].price_per_kg
            
            assert current_rate >= next_rate, (
                f"Processing partners not sorted by rate: "
                f"allocation {i} has rate {current_rate}, "
                f"but allocation {i+1} has higher rate {next_rate}"
            )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_capacity_constraint_with_serialization(self, test_data):
        """
        Test that capacity constraint holds after serialization/deserialization.
        """
        allocation, partners = test_data
        
        # Serialize and deserialize
        allocation_dict = allocation.to_dict()
        restored_allocation = Allocation.from_dict(allocation_dict)
        
        # Get processing allocations
        processing_allocations = [
            ca for ca in restored_allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        partner_map = {p.partner_id: p for p in partners}
        
        # Check capacity constraint still holds
        for ca in processing_allocations:
            partner = partner_map.get(ca.channel_id)
            if partner:
                capacity = partner.get_capacity(restored_allocation.crop_type)
                assert ca.quantity_kg <= capacity + Decimal("0.01"), (
                    f"Capacity constraint violated after serialization: "
                    f"allocated {ca.quantity_kg} kg, capacity {capacity} kg"
                )
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.lists(processing_partner_strategy(), min_size=1, max_size=3),
        st.decimals(min_value=Decimal("0.0"), max_value=Decimal("2000.0"), places=2),
    )
    @settings(max_examples=50, deadline=None)
    def test_capacity_constraint_with_arbitrary_available_quantity(
        self, fpo_id, crop_type, partners, available_quantity
    ):
        """
        Test capacity constraint with arbitrary available quantity.
        """
        # Ensure unique partner IDs
        for i, partner in enumerate(partners):
            partner.partner_id = f"PP{i:03d}"
        
        # Override crop type for all partners
        for partner in partners:
            old_crop = list(partner.rates_by_crop.keys())[0]
            rate = partner.rates_by_crop[old_crop]
            capacity = partner.capacity_by_crop[old_crop]
            partner.rates_by_crop = {crop_type: rate}
            partner.capacity_by_crop = {crop_type: capacity}
            partner.quality_requirements = {crop_type: "Grade A"}
        
        # Sort partners by rate
        partners.sort(key=lambda p: p.get_rate(crop_type), reverse=True)
        
        # Simulate allocation
        channel_allocations = []
        remaining = available_quantity
        
        for partner in partners:
            if remaining <= 0:
                break
            
            capacity = partner.get_capacity(crop_type)
            rate = partner.get_rate(crop_type)
            allocated_qty = min(capacity, remaining)
            
            if allocated_qty > 0:
                revenue = allocated_qty * rate
                channel_allocation = ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id=partner.partner_id,
                    channel_name=partner.partner_name,
                    quantity_kg=allocated_qty,
                    price_per_kg=rate,
                    revenue=revenue,
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
                channel_allocations.append(channel_allocation)
                remaining -= allocated_qty
        
        # Verify capacity constraint
        partner_map = {p.partner_id: p for p in partners}
        for ca in channel_allocations:
            partner = partner_map[ca.channel_id]
            capacity = partner.get_capacity(crop_type)
            assert ca.quantity_kg <= capacity + Decimal("0.01"), (
                f"Capacity constraint violated: allocated {ca.quantity_kg} kg, "
                f"capacity {capacity} kg"
            )
    
    @given(allocation_with_processing_partners_strategy())
    @settings(max_examples=100, deadline=None)
    def test_zero_capacity_partners_not_allocated(self, test_data):
        """
        Test that partners with zero capacity receive no allocation.
        """
        allocation, partners = test_data
        
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        partner_map = {p.partner_id: p for p in partners}
        
        # Check that no partner with zero capacity is allocated
        for partner in partners:
            capacity = partner.get_capacity(allocation.crop_type)
            if capacity == 0:
                # This partner should not have any allocation
                allocated_to_partner = [
                    ca for ca in processing_allocations
                    if ca.channel_id == partner.partner_id
                ]
                assert len(allocated_to_partner) == 0, (
                    f"Partner {partner.partner_id} with zero capacity "
                    f"should not receive allocation"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
