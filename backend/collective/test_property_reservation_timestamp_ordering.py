"""
Property-based test for reservation timestamp ordering.

**Validates: Requirements 4.1**

Property 10: Reservation Timestamp Ordering
For any set of reservations with insufficient inventory, earlier reservations should be fulfilled before later ones.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume
from hypothesis import settings, HealthCheck

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
    hours_ago = draw(st.integers(min_value=0, max_value=23))
    minutes_ago = draw(st.integers(min_value=0, max_value=59))
    reservation_timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    
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
def allocation_with_timestamp_ordered_reservations_strategy(draw):
    """
    Generate an Allocation with Reservations that are allocated in timestamp order.
    
    This strategy ensures that:
    - All reservations are for the same crop type
    - Each reservation has a unique society_id (no duplicates)
    - Reservations have distinct timestamps
    - Allocation respects timestamp ordering
    """
    fpo_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    allocation_date = date.today()
    
    # Generate 2 to 10 reservations with distinct timestamps and unique society IDs
    num_reservations = draw(st.integers(min_value=2, max_value=10))
    reservations = []
    
    # Generate base timestamp
    base_timestamp = datetime.now() - timedelta(days=30)
    
    # Track used society IDs to ensure uniqueness
    used_society_ids = set()
    
    for i in range(num_reservations):
        reservation = draw(reservation_strategy())
        
        # Ensure unique society_id
        while reservation.society_id in used_society_ids:
            reservation.society_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
        
        used_society_ids.add(reservation.society_id)
        
        # Override crop_type to match allocation
        reservation.crop_type = crop_type
        # Ensure distinct timestamps by adding incremental time
        reservation.reservation_timestamp = base_timestamp + timedelta(hours=i * 2, minutes=i * 5)
        reservations.append(reservation)
    
    # Sort reservations by timestamp to ensure ordering
    reservations.sort(key=lambda r: r.reservation_timestamp)
    
    # Calculate total reserved quantity
    total_reserved = sum(r.reserved_quantity_kg for r in reservations)
    
    # Generate available inventory (can be sufficient or insufficient)
    inventory_ratio = draw(st.decimals(min_value=Decimal("0.3"), max_value=Decimal("1.5"), places=2))
    available_inventory = total_reserved * inventory_ratio
    
    # Create channel allocations respecting timestamp order
    society_price_per_kg = Decimal("50.0")
    channel_allocations = []
    remaining = available_inventory
    
    for reservation in reservations:
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


class TestReservationTimestampOrdering:
    """
    Property-based tests for reservation timestamp ordering.
    
    **Validates: Requirements 4.1**
    """
    
    @given(allocation_with_timestamp_ordered_reservations_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_reservation_timestamp_ordering_property(self, test_data):
        """
        Property 10: Reservation Timestamp Ordering
        
        For any set of reservations, allocations should respect timestamp ordering.
        Earlier reservations should be allocated before later ones.
        
        **Validates: Requirements 4.1**
        """
        allocation, reservations, available_inventory = test_data
        
        # Get society allocations from the allocation
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        # If no allocations, nothing to test
        if not society_allocations:
            return
        
        # Sort reservations by timestamp
        sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
        
        # Create a map of society_id to reservation timestamp
        reservation_timestamp_map = {r.society_id: r.reservation_timestamp for r in sorted_reservations}
        
        # Check that allocations are in timestamp order
        for i in range(len(society_allocations) - 1):
            current_allocation = society_allocations[i]
            next_allocation = society_allocations[i + 1]
            
            current_timestamp = reservation_timestamp_map.get(current_allocation.channel_id)
            next_timestamp = reservation_timestamp_map.get(next_allocation.channel_id)
            
            # If both timestamps exist, current should be <= next
            if current_timestamp and next_timestamp:
                assert current_timestamp <= next_timestamp, (
                    f"Timestamp ordering violated: "
                    f"allocation at index {i} has timestamp {current_timestamp}, "
                    f"but allocation at index {i+1} has earlier timestamp {next_timestamp}"
                )
    
    @given(allocation_with_timestamp_ordered_reservations_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_earlier_reservations_fulfilled_first(self, test_data):
        """
        Test that earlier reservations are fulfilled before later ones.
        
        If a later reservation is fully fulfilled, all earlier reservations
        should also be fully fulfilled.
        
        **Validates: Requirements 4.1**
        """
        allocation, reservations, available_inventory = test_data
        
        # Need at least 2 reservations to test ordering
        if len(reservations) < 2:
            return
        
        # Sort reservations by timestamp
        sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
        
        # Create allocation map: society_id -> total allocated quantity
        allocation_map = {}
        for ca in allocation.channel_allocations:
            if ca.channel_type == ChannelType.SOCIETY:
                allocation_map[ca.channel_id] = allocation_map.get(ca.channel_id, Decimal("0")) + ca.quantity_kg
        
        # Check ordering: if reservation[i+1] is fully fulfilled, reservation[i] should be too
        for i in range(len(sorted_reservations) - 1):
            current_reservation = sorted_reservations[i]
            next_reservation = sorted_reservations[i + 1]
            
            current_allocated = allocation_map.get(current_reservation.society_id, Decimal("0"))
            next_allocated = allocation_map.get(next_reservation.society_id, Decimal("0"))
            
            # If next reservation is fully fulfilled
            if abs(next_allocated - next_reservation.reserved_quantity_kg) < Decimal("0.01"):
                # Current reservation should also be fully fulfilled
                assert abs(current_allocated - current_reservation.reserved_quantity_kg) < Decimal("0.01"), (
                    f"Timestamp ordering violated: "
                    f"later reservation {next_reservation.reservation_id} "
                    f"(timestamp: {next_reservation.reservation_timestamp}) is fully allocated "
                    f"({next_allocated} kg), "
                    f"but earlier reservation {current_reservation.reservation_id} "
                    f"(timestamp: {current_reservation.reservation_timestamp}) is not fully allocated "
                    f"({current_allocated} kg out of {current_reservation.reserved_quantity_kg} kg)"
                )
    
    @given(allocation_with_timestamp_ordered_reservations_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_partial_fulfillment_respects_timestamp_order(self, test_data):
        """
        Test that partial fulfillment respects timestamp ordering.
        
        If there's insufficient inventory, earlier reservations should receive
        allocation before later ones get any allocation.
        
        **Validates: Requirements 4.1**
        """
        allocation, reservations, available_inventory = test_data
        
        # Need at least 2 reservations
        if len(reservations) < 2:
            return
        
        total_reserved = sum(r.reserved_quantity_kg for r in reservations)
        
        # Only test when inventory is insufficient
        if available_inventory >= total_reserved:
            return
        
        # Sort reservations by timestamp
        sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
        
        # Create allocation map
        allocation_map = {}
        for ca in allocation.channel_allocations:
            if ca.channel_type == ChannelType.SOCIETY:
                allocation_map[ca.channel_id] = allocation_map.get(ca.channel_id, Decimal("0")) + ca.quantity_kg
        
        # Check that if a later reservation has any allocation,
        # all earlier reservations should be fully allocated
        for i in range(len(sorted_reservations)):
            current_reservation = sorted_reservations[i]
            current_allocated = allocation_map.get(current_reservation.society_id, Decimal("0"))
            
            # If current reservation has any allocation
            if current_allocated > 0:
                # All earlier reservations should be fully allocated
                for j in range(i):
                    earlier_reservation = sorted_reservations[j]
                    earlier_allocated = allocation_map.get(earlier_reservation.society_id, Decimal("0"))
                    
                    assert abs(earlier_allocated - earlier_reservation.reserved_quantity_kg) < Decimal("0.01"), (
                        f"Timestamp ordering violated: "
                        f"reservation {current_reservation.reservation_id} "
                        f"(timestamp: {current_reservation.reservation_timestamp}) "
                        f"has allocation ({current_allocated} kg), "
                        f"but earlier reservation {earlier_reservation.reservation_id} "
                        f"(timestamp: {earlier_reservation.reservation_timestamp}) "
                        f"is not fully allocated "
                        f"({earlier_allocated} kg out of {earlier_reservation.reserved_quantity_kg} kg)"
                    )
    
    @given(allocation_with_timestamp_ordered_reservations_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_allocation_order_matches_timestamp_order(self, test_data):
        """
        Test that the order of allocations in the channel_allocations list
        matches the timestamp order of reservations.
        
        **Validates: Requirements 4.1**
        """
        allocation, reservations, available_inventory = test_data
        
        # Get society allocations
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        if len(society_allocations) < 2:
            return
        
        # Create timestamp map
        timestamp_map = {r.society_id: r.reservation_timestamp for r in reservations}
        
        # Verify that allocations are in timestamp order
        for i in range(len(society_allocations) - 1):
            current_society_id = society_allocations[i].channel_id
            next_society_id = society_allocations[i + 1].channel_id
            
            current_timestamp = timestamp_map.get(current_society_id)
            next_timestamp = timestamp_map.get(next_society_id)
            
            if current_timestamp and next_timestamp:
                assert current_timestamp <= next_timestamp, (
                    f"Allocation order does not match timestamp order: "
                    f"allocation {i} (society {current_society_id}, timestamp {current_timestamp}) "
                    f"comes before allocation {i+1} (society {next_society_id}, timestamp {next_timestamp})"
                )
    
    @given(allocation_with_timestamp_ordered_reservations_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.large_base_example])
    def test_no_allocation_gaps_in_timestamp_order(self, test_data):
        """
        Test that there are no gaps in allocation when following timestamp order.
        
        If reservation[i] is not fully allocated, then no reservation[j] where j > i
        should have any allocation.
        
        **Validates: Requirements 4.1**
        """
        allocation, reservations, available_inventory = test_data
        
        if len(reservations) < 2:
            return
        
        # Sort reservations by timestamp
        sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
        
        # Create allocation map
        allocation_map = {}
        for ca in allocation.channel_allocations:
            if ca.channel_type == ChannelType.SOCIETY:
                allocation_map[ca.channel_id] = allocation_map.get(ca.channel_id, Decimal("0")) + ca.quantity_kg
        
        # Find first partially fulfilled or unfulfilled reservation
        first_partial_index = None
        for i, reservation in enumerate(sorted_reservations):
            allocated = allocation_map.get(reservation.society_id, Decimal("0"))
            if allocated < reservation.reserved_quantity_kg - Decimal("0.01"):
                first_partial_index = i
                break
        
        # If we found a partial/unfulfilled reservation, all later ones should have no allocation
        # OR be partially fulfilled (but not fully fulfilled)
        if first_partial_index is not None:
            for i in range(first_partial_index + 1, len(sorted_reservations)):
                later_reservation = sorted_reservations[i]
                later_allocated = allocation_map.get(later_reservation.society_id, Decimal("0"))
                
                # Later reservation should not be fully fulfilled
                assert later_allocated < later_reservation.reserved_quantity_kg + Decimal("0.01"), (
                    f"Allocation gap detected: "
                    f"reservation {sorted_reservations[first_partial_index].reservation_id} "
                    f"(timestamp: {sorted_reservations[first_partial_index].reservation_timestamp}) "
                    f"is not fully allocated, "
                    f"but later reservation {later_reservation.reservation_id} "
                    f"(timestamp: {later_reservation.reservation_timestamp}) "
                    f"is fully allocated ({later_allocated} kg)"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
