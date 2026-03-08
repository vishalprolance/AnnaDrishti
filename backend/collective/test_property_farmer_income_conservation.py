"""
Property test for farmer income conservation

**Property 7: Farmer Income Conservation**
**Validates: Requirements 6.2**

For any allocation, the sum of all farmer incomes must equal the total revenue from the allocation.
"""

import pytest
from hypothesis import given, strategies as st, assume
from decimal import Decimal
from datetime import datetime, date
import uuid

from collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    CollectiveInventory,
    FarmerContribution,
    QualityGrade,
)
from collective.services.realization_service import RealizationService


# Strategy for generating valid farmer contributions
@st.composite
def farmer_contribution_strategy(draw, crop_type="tomato"):
    """Generate a valid FarmerContribution"""
    farmer_id = f"FARMER{draw(st.integers(min_value=1, max_value=100)):03d}"
    quantity_kg = Decimal(str(draw(st.floats(min_value=1.0, max_value=500.0))))
    
    return FarmerContribution(
        contribution_id=str(uuid.uuid4()),
        farmer_id=farmer_id,
        farmer_name=f"Farmer {farmer_id}",
        crop_type=crop_type,
        quantity_kg=quantity_kg,
        quality_grade=draw(st.sampled_from([QualityGrade.A, QualityGrade.B, QualityGrade.C])),
        timestamp=datetime.now(),
        allocated=False,
    )


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
def inventory_and_allocation_strategy(draw):
    """
    Generate a CollectiveInventory and matching Allocation.
    
    The allocation's total quantity matches the sum of farmer contributions.
    """
    crop_type = "tomato"
    fpo_id = "FPO001"
    
    # Generate 2-10 farmer contributions
    num_farmers = draw(st.integers(min_value=2, max_value=10))
    contributions = [draw(farmer_contribution_strategy(crop_type=crop_type)) for _ in range(num_farmers)]
    
    # Calculate total from contributions
    total_contribution = sum(c.quantity_kg for c in contributions)
    
    # Assume total contribution is positive
    assume(total_contribution > 0)
    
    # Create inventory
    inventory = CollectiveInventory(
        fpo_id=fpo_id,
        crop_type=crop_type,
        total_quantity_kg=total_contribution,
        available_quantity_kg=Decimal("0"),  # All allocated
        reserved_quantity_kg=Decimal("0"),
        allocated_quantity_kg=total_contribution,
        contributions=contributions,
        last_updated=datetime.now(),
    )
    
    # Generate 1-3 channel allocations that sum to total_contribution
    num_channels = draw(st.integers(min_value=1, max_value=3))
    
    # Generate channel allocations with quantities that sum to total
    channel_allocations = []
    remaining = total_contribution
    
    for i in range(num_channels):
        if i == num_channels - 1:
            # Last channel gets remaining quantity
            quantity = remaining
        else:
            # Random portion of remaining
            max_qty = float(remaining * Decimal("0.8"))  # Leave some for other channels
            quantity = Decimal(str(draw(st.floats(min_value=0.1, max_value=max_qty))))
            remaining -= quantity
        
        # Generate price
        price_per_kg = Decimal(str(draw(st.floats(min_value=1.0, max_value=100.0))))
        revenue = quantity * price_per_kg
        
        # Assign channel type and priority
        if i == 0:
            channel_type = ChannelType.SOCIETY
            priority = 1
        elif i == 1:
            channel_type = ChannelType.PROCESSING
            priority = 2
        else:
            channel_type = ChannelType.MANDI
            priority = 3
        
        channel_allocation = ChannelAllocation(
            channel_type=channel_type,
            channel_id=f"{channel_type.value}_{i+1:03d}",
            channel_name=f"{channel_type.value.title()} {i+1}",
            quantity_kg=quantity,
            price_per_kg=price_per_kg,
            revenue=revenue,
            priority=priority,
        )
        channel_allocations.append(channel_allocation)
    
    # Calculate totals for allocation
    total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
    total_revenue = sum(ca.revenue for ca in channel_allocations)
    blended_realization = total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
    
    # Create allocation
    allocation = Allocation(
        allocation_id=str(uuid.uuid4()),
        fpo_id=fpo_id,
        crop_type=crop_type,
        allocation_date=date(2026, 3, 8),
        channel_allocations=channel_allocations,
        total_quantity_kg=total_quantity,
        blended_realization_per_kg=blended_realization,
        status=AllocationStatus.PENDING,
    )
    
    return inventory, allocation


@given(data=inventory_and_allocation_strategy())
def test_property_farmer_income_conservation(data):
    """
    Property: For any allocation, the sum of all farmer incomes must equal 
    the total revenue from the allocation.
    
    This property validates that income is conserved - no money is created
    or lost when distributing revenue to farmers.
    """
    inventory, allocation = data
    service = RealizationService()
    
    # Calculate total revenue from allocation
    total_revenue = sum(ca.revenue for ca in allocation.channel_allocations)
    
    # Calculate income for all farmers
    farmer_incomes = service.calculate_all_farmer_incomes(allocation, inventory)
    
    # Sum all farmer revenues
    sum_farmer_revenues = sum(Decimal(fi["total_revenue"]) for fi in farmer_incomes)
    
    # Verify conservation (within 0.01 tolerance for decimal precision)
    assert abs(sum_farmer_revenues - total_revenue) < Decimal("0.01"), (
        f"Income conservation violated: sum of farmer incomes={sum_farmer_revenues}, "
        f"total revenue={total_revenue}, difference={abs(sum_farmer_revenues - total_revenue)}"
    )


@given(data=inventory_and_allocation_strategy())
def test_property_farmer_income_proportional(data):
    """
    Property: Each farmer's income should be proportional to their contribution.
    
    If farmer A contributes twice as much as farmer B, farmer A should earn
    twice as much revenue (assuming same allocation).
    """
    inventory, allocation = data
    service = RealizationService()
    
    # Calculate income for all farmers
    farmer_incomes = service.calculate_all_farmer_incomes(allocation, inventory)
    
    # Verify proportionality
    for income in farmer_incomes:
        farmer_contribution = Decimal(income["contribution_kg"])
        farmer_revenue = Decimal(income["total_revenue"])
        
        # Calculate expected revenue based on proportion
        total_quantity = allocation.total_quantity_kg
        total_revenue = sum(ca.revenue for ca in allocation.channel_allocations)
        
        expected_revenue = (farmer_contribution / total_quantity) * total_revenue
        
        # Verify (within 0.01 tolerance)
        assert abs(farmer_revenue - expected_revenue) < Decimal("0.01"), (
            f"Farmer {income['farmer_id']} income not proportional: "
            f"got {farmer_revenue}, expected {expected_revenue}"
        )


def test_farmer_income_single_farmer():
    """
    Test that a single farmer gets all revenue.
    """
    service = RealizationService()
    
    # Create inventory with single farmer
    contribution = FarmerContribution(
        contribution_id="CONT001",
        farmer_id="FARMER001",
        farmer_name="Farmer 1",
        crop_type="tomato",
        quantity_kg=Decimal("100"),
        quality_grade=QualityGrade.A,
        timestamp=datetime.now(),
    )
    
    inventory = CollectiveInventory(
        fpo_id="FPO001",
        crop_type="tomato",
        total_quantity_kg=Decimal("100"),
        available_quantity_kg=Decimal("0"),
        reserved_quantity_kg=Decimal("0"),
        allocated_quantity_kg=Decimal("100"),
        contributions=[contribution],
    )
    
    # Create allocation
    channel_allocation = ChannelAllocation(
        channel_type=ChannelType.SOCIETY,
        channel_id="SOC001",
        channel_name="Society 1",
        quantity_kg=Decimal("100"),
        price_per_kg=Decimal("50"),
        revenue=Decimal("5000"),
        priority=1,
    )
    
    allocation = Allocation(
        allocation_id="ALLOC001",
        fpo_id="FPO001",
        crop_type="tomato",
        allocation_date=date(2026, 3, 8),
        channel_allocations=[channel_allocation],
        total_quantity_kg=Decimal("100"),
        blended_realization_per_kg=Decimal("50"),
    )
    
    # Calculate farmer income
    income = service.calculate_farmer_income("FARMER001", allocation, inventory)
    
    # Farmer should get all revenue
    assert Decimal(income["total_revenue"]) == Decimal("5000")
    assert Decimal(income["blended_rate_per_kg"]) == Decimal("50")


def test_farmer_income_equal_split():
    """
    Test that two farmers with equal contributions get equal revenue.
    """
    service = RealizationService()
    
    # Create inventory with two farmers
    contributions = [
        FarmerContribution(
            contribution_id="CONT001",
            farmer_id="FARMER001",
            farmer_name="Farmer 1",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
        ),
        FarmerContribution(
            contribution_id="CONT002",
            farmer_id="FARMER002",
            farmer_name="Farmer 2",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
        ),
    ]
    
    inventory = CollectiveInventory(
        fpo_id="FPO001",
        crop_type="tomato",
        total_quantity_kg=Decimal("100"),
        available_quantity_kg=Decimal("0"),
        reserved_quantity_kg=Decimal("0"),
        allocated_quantity_kg=Decimal("100"),
        contributions=contributions,
    )
    
    # Create allocation
    channel_allocation = ChannelAllocation(
        channel_type=ChannelType.SOCIETY,
        channel_id="SOC001",
        channel_name="Society 1",
        quantity_kg=Decimal("100"),
        price_per_kg=Decimal("50"),
        revenue=Decimal("5000"),
        priority=1,
    )
    
    allocation = Allocation(
        allocation_id="ALLOC001",
        fpo_id="FPO001",
        crop_type="tomato",
        allocation_date=date(2026, 3, 8),
        channel_allocations=[channel_allocation],
        total_quantity_kg=Decimal("100"),
        blended_realization_per_kg=Decimal("50"),
    )
    
    # Calculate farmer incomes
    income1 = service.calculate_farmer_income("FARMER001", allocation, inventory)
    income2 = service.calculate_farmer_income("FARMER002", allocation, inventory)
    
    # Both farmers should get equal revenue
    assert Decimal(income1["total_revenue"]) == Decimal("2500")
    assert Decimal(income2["total_revenue"]) == Decimal("2500")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
