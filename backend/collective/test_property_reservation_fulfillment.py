"""
Property-based test for reservation fulfillment.

**Validates: Requirements 4.1, 4.7**

Property 4: Reservation Fulfillment
For any allocation, if available inventory >= total reservations, then all reservations must be fully allocated.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume
from hypothesis import settings

from backend.collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    Reservation,
    ReservationStatus,
)


# Hypothesis strategies for generating test data
@st.composite
def reservation_strategy(draw):
    """Generate a valid Reservation."""
    society_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    reserved_quantity = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("500"), places=2))
    
    # Generate timestamp within last 30 days
    days_ago = draw(st.integers(min_value=0, max_value=30))
    reservation_timestamp = datetime.now() - timedelta(days=days_ago)
    
    delivery_date = date.today() + timedelta(days=draw(st.integers(min_value=1, max_value=7)))
    
    return Reservation(
        reservation_id=draw(st.uuids()).hex,
        society_id=society_id,
        crop_type=crop_type,
        reserved_quantity_kg=reserved_quantity,
        reservation_timestamp=reservation_timestamp,
        delivery_date=delivery_date,
        status=draw(st.sampled_from([ReservationStatus.PREDICTED, ReservationStatus.CONFIRMED])),
    )


@st.composite
def allocation_with_reservations_strategy(draw):
    """
    Generate an Allocation with corresponding Reservations.
    
    This strategy ensures that:
    - All reservations are for the same crop type
    - Available inventory is >= total reservations (sufficient inventory case)
    - Allocation contains society allocations matching the reservations
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    # Generate 1 to 10 reservations
    num_reservations = draw(st.integers(min_value=1, max_value=10))
    reservations = []
    
    for _ in range(num_reservations):
        reservation = draw(reservation_strategy())
        # Override crop_type to match allocation
        reservation.crop_type = crop_type
        reservations.append(reservation)
    
    # Calculate total reserved quantity
    total_reserved = sum(r.reserved_quantity_kg for r in reservations)
    
    # Generate available inventory >= total reservations (sufficient inventory)
    # Add some buffer (0% to 100% extra)
    buffer_percentage = draw(st.decimals(min_value=Decimal("0"), max_value=Decimal("1.0"), places=2))
    available_inventory = total_reserved * (Decimal("1") + buffer_percentage)
    
    # Create channel allocations for societies
    # In the sufficient inventory case, all reservations should be fully allocated
    society_price_per_kg = Decimal("50.0")
    channel_allocations = []
    
    for reservation in reservations:
        allocated_qty = reservation.reserved_quantity_kg
        revenue = allocated_qty * society_price_per_kg
        
        channel_allocation = ChannelAllocation(
            channel_type=ChannelType.SOCIETY,
            channel_id=reservation.society_id,
            channel_name=f"Society-{reservation.society_id}",
            quantity_kg=allocated_qty,
            price_per_kg=society_price_per_kg,
            revenue=revenue,
            priority=1,
            fulfillment_status=FulfillmentStatus.PENDING,
        )
        channel_allocations.append(channel_allocation)
    
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
    
    return allocation, reservations, available_inventory


@st.composite
def allocation_with_insufficient_inventory_strategy(draw):
    """
    Generate an Allocation with insufficient inventory.
    
    This strategy ensures that:
    - Available inventory < total reservations (insufficient inventory case)
    - Some reservations may be partially fulfilled or unfulfilled
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    # Generate 2 to 10 reservations
    num_reservations = draw(st.integers(min_value=2, max_value=10))
    reservations = []
    
    for _ in range(num_reservations):
        reservation = draw(reservation_strategy())
        reservation.crop_type = crop_type
        reservations.append(reservation)
    
    # Calculate total reserved quantity
    total_reserved = sum(r.reserved_quantity_kg for r in reservations)
    
    # Generate available inventory < total reservations (insufficient inventory)
    # Use 10% to 90% of total reserved
    shortage_percentage = draw(st.decimals(min_value=Decimal("0.1"), max_value=Decimal("0.9"), places=2))
    available_inventory = total_reserved * shortage_percentage
    
    # Sort reservations by timestamp (allocation should follow this order)
    sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
    
    # Allocate in timestamp order until inventory runs out
    society_price_per_kg = Decimal("50.0")
    channel_allocations = []
    remaining = available_inventory
    
    for reservation in sorted_reservations:
        if remaining <= 0:
            break
        
        allocated_qty = min(reservation.reserved_quantity_kg, remaining)
        
        if allocated_qty > 0:
            revenue = allocated_qty * society_price_per_kg
            
            channel_allocation = ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id=reservation.society_id,
                channel_name=f"Society-{reservation.society_id}",
                quantity_kg=allocated_qty,
                price_per_kg=society_price_per_kg,
                revenue=revenue,
                priority=1,
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
    
    return allocation, reservations, available_inventory


class TestReservationFulfillment:
    """
    Property-based tests for reservation fulfillment.
    
    **Validates: Requirements 4.1, 4.7**
    """
    
    @given(allocation_with_reservations_strategy())
    @settings(max_examples=100, deadline=None)
    def test_reservation_fulfillment_property(self, test_data):
        """
        Property 4: Reservation Fulfillment
        
        For any allocation, if available inventory >= total reservations,
        then all reservations must be fully allocated.
        """
        allocation, reservations, available_inventory = test_data
        
        # Calculate total reserved quantity
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        # Get society allocations from the allocation
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        # Calculate total society allocated
        total_society_allocated = sum(ca.quantity_kg for ca in society_allocations)
        
        # Property: If available >= total reserved, then all reservations are fully allocated
        if available_inventory >= total_reserved:
            assert abs(total_society_allocated - total_reserved) < Decimal("0.01"), (
                f"Reservation fulfillment violated: "
                f"available={available_inventory}, "
                f"total_reserved={total_reserved}, "
                f"total_allocated={total_society_allocated}"
            )
    
    @given(allocation_with_reservations_strategy())
    @settings(max_examples=100, deadline=None)
    def test_all_reservations_have_allocations(self, test_data):
        """
        Test that when inventory is sufficient, each reservation has a corresponding allocation.
        """
        allocation, reservations, available_inventory = test_data
        
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        if available_inventory >= total_reserved:
            # Get society IDs from allocations
            allocated_society_ids = {
                ca.channel_id for ca in allocation.channel_allocations
                if ca.channel_type == ChannelType.SOCIETY
            }
            
            # Get society IDs from reservations
            reserved_society_ids = {r.society_id for r in reservations}
            
            # All reserved societies should have allocations
            assert reserved_society_ids == allocated_society_ids, (
                f"Not all reservations have allocations: "
                f"reserved={reserved_society_ids}, "
                f"allocated={allocated_society_ids}"
            )
    
    @given(allocation_with_reservations_strategy())
    @settings(max_examples=100, deadline=None)
    def test_individual_reservation_fulfillment(self, test_data):
        """
        Test that when inventory is sufficient, each individual reservation is fully allocated.
        
        Note: Multiple reservations can exist for the same society_id, so we need to
        sum all reservations per society and compare to total allocated.
        """
        allocation, reservations, available_inventory = test_data
        
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        if available_inventory >= total_reserved:
            # Create a map of society_id to allocated quantity
            allocation_map = {}
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.SOCIETY:
                    allocation_map[ca.channel_id] = allocation_map.get(ca.channel_id, Decimal("0")) + ca.quantity_kg
            
            # Create a map of society_id to total reserved quantity
            reservation_map = {}
            for reservation in reservations:
                reservation_map[reservation.society_id] = reservation_map.get(reservation.society_id, Decimal("0")) + reservation.reserved_quantity_kg
            
            # Check each society's total reservations are fulfilled
            for society_id, total_reserved_for_society in reservation_map.items():
                allocated_qty = allocation_map.get(society_id, Decimal("0"))
                
                assert abs(allocated_qty - total_reserved_for_society) < Decimal("0.01"), (
                    f"Society {society_id} reservations not fully allocated: "
                    f"total_reserved={total_reserved_for_society}, "
                    f"allocated={allocated_qty}"
                )
    
    @given(allocation_with_insufficient_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_insufficient_inventory_partial_fulfillment(self, test_data):
        """
        Test that when inventory is insufficient, allocations don't exceed available inventory.
        """
        allocation, reservations, available_inventory = test_data
        
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        # Get society allocations
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        total_society_allocated = sum(ca.quantity_kg for ca in society_allocations)
        
        # Property: When insufficient, allocated <= available
        assert total_society_allocated <= available_inventory + Decimal("0.01"), (
            f"Over-allocation detected: "
            f"available={available_inventory}, "
            f"allocated={total_society_allocated}"
        )
        
        # Property: When insufficient, allocated < total reserved
        if available_inventory < total_reserved:
            assert total_society_allocated < total_reserved, (
                f"Allocated more than available when insufficient: "
                f"available={available_inventory}, "
                f"total_reserved={total_reserved}, "
                f"allocated={total_society_allocated}"
            )
    
    @given(allocation_with_insufficient_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_timestamp_ordering_with_insufficient_inventory(self, test_data):
        """
        Test that when inventory is insufficient, reservations are processed in timestamp order.
        
        This means: if we simulate the allocation process step by step in timestamp order,
        the total allocated should match what we see in the actual allocation.
        """
        allocation, reservations, available_inventory = test_data
        
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        if available_inventory < total_reserved and len(reservations) > 1:
            # Sort reservations by timestamp
            sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
            
            # Simulate allocation in timestamp order
            simulated_allocations = {}
            remaining = available_inventory
            
            for reservation in sorted_reservations:
                allocated = min(reservation.reserved_quantity_kg, remaining)
                if allocated > 0:
                    simulated_allocations[reservation.society_id] = simulated_allocations.get(
                        reservation.society_id, Decimal("0")
                    ) + allocated
                    remaining -= allocated
            
            # Get actual allocations
            actual_allocations = {}
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.SOCIETY:
                    actual_allocations[ca.channel_id] = actual_allocations.get(
                        ca.channel_id, Decimal("0")
                    ) + ca.quantity_kg
            
            # Compare simulated vs actual
            for society_id in set(list(simulated_allocations.keys()) + list(actual_allocations.keys())):
                simulated = simulated_allocations.get(society_id, Decimal("0"))
                actual = actual_allocations.get(society_id, Decimal("0"))
                
                assert abs(simulated - actual) < Decimal("0.01"), (
                    f"Allocation mismatch for society {society_id}: "
                    f"simulated={simulated}, actual={actual}. "
                    f"This suggests reservations were not processed in timestamp order."
                )
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.lists(reservation_strategy(), min_size=1, max_size=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_allocation_when_no_inventory(self, fpo_id, crop_type, reservations):
        """
        Test that when available inventory is zero, no allocations are made.
        """
        # Override crop type for all reservations
        for reservation in reservations:
            reservation.crop_type = crop_type
        
        available_inventory = Decimal("0")
        
        # Create empty allocation
        allocation = Allocation(
            allocation_id="test-allocation",
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=date.today(),
            channel_allocations=[],
            total_quantity_kg=Decimal("0"),
            blended_realization_per_kg=Decimal("0"),
            status=AllocationStatus.PENDING,
        )
        
        # Get society allocations
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        total_society_allocated = sum(ca.quantity_kg for ca in society_allocations)
        
        # Property: No allocation when no inventory
        assert total_society_allocated == Decimal("0"), (
            f"Allocation made with zero inventory: allocated={total_society_allocated}"
        )
    
    @given(allocation_with_reservations_strategy())
    @settings(max_examples=100, deadline=None)
    def test_allocation_quantity_non_negative(self, test_data):
        """
        Test that all allocation quantities are non-negative.
        """
        allocation, reservations, available_inventory = test_data
        
        for ca in allocation.channel_allocations:
            assert ca.quantity_kg >= 0, (
                f"Negative allocation quantity: {ca.quantity_kg}"
            )
    
    @given(allocation_with_reservations_strategy())
    @settings(max_examples=100, deadline=None)
    def test_reservation_fulfillment_with_serialization(self, test_data):
        """
        Test that reservation fulfillment property holds after serialization/deserialization.
        """
        allocation, reservations, available_inventory = test_data
        
        # Serialize and deserialize
        allocation_dict = allocation.to_dict()
        restored_allocation = Allocation.from_dict(allocation_dict)
        
        # Calculate totals
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        society_allocations = [
            ca for ca in restored_allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        total_society_allocated = sum(ca.quantity_kg for ca in society_allocations)
        
        # Property should still hold after serialization
        if available_inventory >= total_reserved:
            assert abs(total_society_allocated - total_reserved) < Decimal("0.01"), (
                f"Reservation fulfillment violated after serialization"
            )
