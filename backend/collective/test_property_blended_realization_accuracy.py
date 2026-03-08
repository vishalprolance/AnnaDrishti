"""
Property test for blended realization accuracy

**Property 6: Blended Realization Accuracy**
**Validates: Requirements 6.1**

For any allocation, the blended realization must equal total revenue divided by total quantity.
"""

import pytest
from hypothesis import given, strategies as st
from decimal import Decimal
from datetime import date

from collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
)
from collective.services.realization_service import RealizationService


# Strategy for generating valid channel allocations
@st.composite
def channel_allocation_strategy(draw):
    """Generate a valid ChannelAllocation"""
    channel_types = [ChannelType.SOCIETY, ChannelType.PROCESSING, ChannelType.MANDI]
    channel_type = draw(st.sampled_from(channel_types))
    
    # Generate positive quantities and prices
    quantity_kg = Decimal(str(draw(st.floats(min_value=0.1, max_value=1000.0))))
    price_per_kg = Decimal(str(draw(st.floats(min_value=1.0, max_value=100.0))))
    
    # Calculate revenue
    revenue = quantity_kg * price_per_kg
    
    # Priority based on channel type
    priority_map = {
        ChannelType.SOCIETY: 1,
        ChannelType.PROCESSING: 2,
        ChannelType.MANDI: 3,
    }
    priority = priority_map[channel_type]
    
    return ChannelAllocation(
        channel_type=channel_type,
        channel_id=f"{channel_type.value}_001",
        channel_name=f"{channel_type.value.title()} Channel",
        quantity_kg=quantity_kg,
        price_per_kg=price_per_kg,
        revenue=revenue,
        priority=priority,
        fulfillment_status=FulfillmentStatus.PENDING,
    )


@st.composite
def allocation_strategy(draw):
    """Generate a valid Allocation with channel allocations"""
    # Generate 1-5 channel allocations
    num_allocations = draw(st.integers(min_value=1, max_value=5))
    channel_allocations = [draw(channel_allocation_strategy()) for _ in range(num_allocations)]
    
    # Sort by priority to maintain ordering
    channel_allocations.sort(key=lambda ca: ca.priority)
    
    # Calculate totals
    total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
    total_revenue = sum(ca.revenue for ca in channel_allocations)
    blended_realization = total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
    
    return Allocation(
        allocation_id="test_allocation_001",
        fpo_id="FPO001",
        crop_type="tomato",
        allocation_date=date(2026, 3, 8),
        channel_allocations=channel_allocations,
        total_quantity_kg=total_quantity,
        blended_realization_per_kg=blended_realization,
        status=AllocationStatus.PENDING,
    )


@given(allocation=allocation_strategy())
def test_property_blended_realization_accuracy(allocation: Allocation):
    """
    Property: For any allocation, the blended realization must equal 
    total revenue divided by total quantity.
    
    This property validates that the blended realization calculation is accurate
    and matches the mathematical definition.
    """
    service = RealizationService()
    
    # Calculate blended realization using service
    calculated_blended = service.calculate_blended_realization(allocation.channel_allocations)
    
    # Calculate expected blended realization manually
    total_revenue = sum(ca.revenue for ca in allocation.channel_allocations)
    total_quantity = sum(ca.quantity_kg for ca in allocation.channel_allocations)
    expected_blended = total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
    
    # Verify accuracy (within 0.01 tolerance for decimal precision)
    assert abs(calculated_blended - expected_blended) < Decimal("0.01"), (
        f"Blended realization mismatch: calculated={calculated_blended}, "
        f"expected={expected_blended}"
    )
    
    # Also verify that allocation's stored blended realization matches
    assert abs(allocation.blended_realization_per_kg - expected_blended) < Decimal("0.01"), (
        f"Allocation blended realization mismatch: stored={allocation.blended_realization_per_kg}, "
        f"expected={expected_blended}"
    )


@given(allocation=allocation_strategy())
def test_property_blended_realization_bounds(allocation: Allocation):
    """
    Property: Blended realization must be between the minimum and maximum 
    channel prices.
    
    This validates that the blended rate is a weighted average and falls
    within the range of individual channel prices.
    """
    service = RealizationService()
    
    # Calculate blended realization
    blended = service.calculate_blended_realization(allocation.channel_allocations)
    
    # Get min and max prices
    prices = [ca.price_per_kg for ca in allocation.channel_allocations]
    min_price = min(prices)
    max_price = max(prices)
    
    # Blended realization should be within bounds (with small tolerance for precision)
    tolerance = Decimal("0.01")
    assert min_price - tolerance <= blended <= max_price + tolerance, (
        f"Blended realization {blended} outside bounds [{min_price}, {max_price}]"
    )


def test_blended_realization_single_channel():
    """
    Test that blended realization equals channel price for single-channel allocation.
    """
    service = RealizationService()
    
    # Create single channel allocation
    channel_allocation = ChannelAllocation(
        channel_type=ChannelType.SOCIETY,
        channel_id="SOC001",
        channel_name="Society 1",
        quantity_kg=Decimal("100"),
        price_per_kg=Decimal("50"),
        revenue=Decimal("5000"),
        priority=1,
    )
    
    blended = service.calculate_blended_realization([channel_allocation])
    
    # For single channel, blended should equal channel price
    assert blended == Decimal("50")


def test_blended_realization_empty_allocation():
    """
    Test that empty allocation raises ValueError.
    """
    service = RealizationService()
    
    with pytest.raises(ValueError, match="Cannot calculate blended realization with no allocations"):
        service.calculate_blended_realization([])


def test_blended_realization_multiple_channels():
    """
    Test blended realization with multiple channels.
    """
    service = RealizationService()
    
    # Create multiple channel allocations
    allocations = [
        ChannelAllocation(
            channel_type=ChannelType.SOCIETY,
            channel_id="SOC001",
            channel_name="Society 1",
            quantity_kg=Decimal("100"),
            price_per_kg=Decimal("50"),
            revenue=Decimal("5000"),
            priority=1,
        ),
        ChannelAllocation(
            channel_type=ChannelType.PROCESSING,
            channel_id="PROC001",
            channel_name="Processor 1",
            quantity_kg=Decimal("50"),
            price_per_kg=Decimal("45"),
            revenue=Decimal("2250"),
            priority=2,
        ),
        ChannelAllocation(
            channel_type=ChannelType.MANDI,
            channel_id="MANDI001",
            channel_name="APMC Market",
            quantity_kg=Decimal("30"),
            price_per_kg=Decimal("30"),
            revenue=Decimal("900"),
            priority=3,
        ),
    ]
    
    blended = service.calculate_blended_realization(allocations)
    
    # Expected: (5000 + 2250 + 900) / (100 + 50 + 30) = 8150 / 180 = 45.28
    expected = Decimal("8150") / Decimal("180")
    
    assert abs(blended - expected) < Decimal("0.01")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
