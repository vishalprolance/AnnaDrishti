"""
Unit tests for realization calculation

Tests:
- Blended realization with multiple channels
- Farmer income with multiple farmers
- Channel breakdown accuracy
- Comparison to single-channel

**Validates: Requirements 6.6**
"""

import pytest
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


@pytest.fixture
def realization_service():
    """Create realization service"""
    return RealizationService()


@pytest.fixture
def sample_channel_allocations():
    """Create sample channel allocations"""
    return [
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


@pytest.fixture
def sample_allocation(sample_channel_allocations):
    """Create sample allocation"""
    total_quantity = sum(ca.quantity_kg for ca in sample_channel_allocations)
    total_revenue = sum(ca.revenue for ca in sample_channel_allocations)
    blended = total_revenue / total_quantity
    
    return Allocation(
        allocation_id="ALLOC001",
        fpo_id="FPO001",
        crop_type="tomato",
        allocation_date=date(2026, 3, 8),
        channel_allocations=sample_channel_allocations,
        total_quantity_kg=total_quantity,
        blended_realization_per_kg=blended,
        status=AllocationStatus.PENDING,
    )


@pytest.fixture
def sample_inventory():
    """Create sample inventory with multiple farmers"""
    contributions = [
        FarmerContribution(
            contribution_id="CONT001",
            farmer_id="FARMER001",
            farmer_name="Farmer 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
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
        FarmerContribution(
            contribution_id="CONT003",
            farmer_id="FARMER003",
            farmer_name="Farmer 3",
            crop_type="tomato",
            quantity_kg=Decimal("30"),
            quality_grade=QualityGrade.B,
            timestamp=datetime.now(),
        ),
    ]
    
    total = sum(c.quantity_kg for c in contributions)
    
    return CollectiveInventory(
        fpo_id="FPO001",
        crop_type="tomato",
        total_quantity_kg=total,
        available_quantity_kg=Decimal("0"),
        reserved_quantity_kg=Decimal("0"),
        allocated_quantity_kg=total,
        contributions=contributions,
    )


def test_blended_realization_multiple_channels(realization_service, sample_channel_allocations):
    """
    Test blended realization calculation with multiple channels.
    
    Expected: (5000 + 2250 + 900) / (100 + 50 + 30) = 8150 / 180 = 45.277...
    """
    blended = realization_service.calculate_blended_realization(sample_channel_allocations)
    
    expected = Decimal("8150") / Decimal("180")
    
    assert abs(blended - expected) < Decimal("0.01")
    
    # Verify it's approximately 45.28
    assert abs(blended - Decimal("45.28")) < Decimal("0.01")


def test_channel_breakdown_accuracy(realization_service, sample_channel_allocations):
    """
    Test channel breakdown calculation accuracy.
    """
    breakdown = realization_service.get_channel_breakdown(sample_channel_allocations)
    
    # Verify society channel
    assert Decimal(breakdown["society"]["quantity_kg"]) == Decimal("100")
    assert Decimal(breakdown["society"]["revenue"]) == Decimal("5000")
    assert Decimal(breakdown["society"]["rate_per_kg"]) == Decimal("50")
    
    # Verify processing channel
    assert Decimal(breakdown["processing"]["quantity_kg"]) == Decimal("50")
    assert Decimal(breakdown["processing"]["revenue"]) == Decimal("2250")
    assert Decimal(breakdown["processing"]["rate_per_kg"]) == Decimal("45")
    
    # Verify mandi channel
    assert Decimal(breakdown["mandi"]["quantity_kg"]) == Decimal("30")
    assert Decimal(breakdown["mandi"]["revenue"]) == Decimal("900")
    assert Decimal(breakdown["mandi"]["rate_per_kg"]) == Decimal("30")


def test_channel_breakdown_empty_channels(realization_service, sample_channel_allocations):
    """
    Test that channels with no allocations show zero values.
    """
    # Use only society allocation
    society_only = [sample_channel_allocations[0]]
    
    breakdown = realization_service.get_channel_breakdown(society_only)
    
    # Society should have values
    assert Decimal(breakdown["society"]["quantity_kg"]) == Decimal("100")
    
    # Processing and mandi should be zero
    assert Decimal(breakdown["processing"]["quantity_kg"]) == Decimal("0")
    assert Decimal(breakdown["processing"]["revenue"]) == Decimal("0")
    assert Decimal(breakdown["mandi"]["quantity_kg"]) == Decimal("0")
    assert Decimal(breakdown["mandi"]["revenue"]) == Decimal("0")


def test_best_single_channel_price(realization_service, sample_channel_allocations):
    """
    Test getting the best single channel price.
    """
    best_price = realization_service.get_best_single_channel_price(sample_channel_allocations)
    
    # Best price should be society at 50/kg
    assert best_price == Decimal("50")


def test_farmer_income_multiple_farmers(realization_service, sample_allocation, sample_inventory):
    """
    Test farmer income calculation with multiple farmers.
    
    Total revenue: 8150
    Total quantity: 180
    
    Farmer 1: 100 kg (55.56% of total)
    Farmer 2: 50 kg (27.78% of total)
    Farmer 3: 30 kg (16.67% of total)
    """
    # Calculate income for Farmer 1
    income1 = realization_service.calculate_farmer_income("FARMER001", sample_allocation, sample_inventory)
    
    # Farmer 1 contributed 100 kg out of 180 total
    # Expected revenue: (100/180) * 8150 = 4527.78
    expected_revenue1 = (Decimal("100") / Decimal("180")) * Decimal("8150")
    
    assert abs(Decimal(income1["total_revenue"]) - expected_revenue1) < Decimal("0.01")
    assert Decimal(income1["contribution_kg"]) == Decimal("100")
    
    # Calculate income for Farmer 2
    income2 = realization_service.calculate_farmer_income("FARMER002", sample_allocation, sample_inventory)
    
    # Farmer 2 contributed 50 kg out of 180 total
    # Expected revenue: (50/180) * 8150 = 2263.89
    expected_revenue2 = (Decimal("50") / Decimal("180")) * Decimal("8150")
    
    assert abs(Decimal(income2["total_revenue"]) - expected_revenue2) < Decimal("0.01")
    assert Decimal(income2["contribution_kg"]) == Decimal("50")
    
    # Calculate income for Farmer 3
    income3 = realization_service.calculate_farmer_income("FARMER003", sample_allocation, sample_inventory)
    
    # Farmer 3 contributed 30 kg out of 180 total
    # Expected revenue: (30/180) * 8150 = 1358.33
    expected_revenue3 = (Decimal("30") / Decimal("180")) * Decimal("8150")
    
    assert abs(Decimal(income3["total_revenue"]) - expected_revenue3) < Decimal("0.01")
    assert Decimal(income3["contribution_kg"]) == Decimal("30")


def test_farmer_income_channel_breakdown(realization_service, sample_allocation, sample_inventory):
    """
    Test that farmer income includes accurate channel breakdown.
    """
    income = realization_service.calculate_farmer_income("FARMER001", sample_allocation, sample_inventory)
    
    # Verify channel breakdown exists
    assert "channel_breakdown" in income
    assert len(income["channel_breakdown"]) == 3
    
    # Verify each channel has required fields
    for channel in income["channel_breakdown"]:
        assert "channel" in channel
        assert "channel_name" in channel
        assert "quantity_kg" in channel
        assert "revenue" in channel
        assert "rate_per_kg" in channel
    
    # Verify total from breakdown matches total revenue
    total_from_breakdown = sum(Decimal(ch["revenue"]) for ch in income["channel_breakdown"])
    assert abs(total_from_breakdown - Decimal(income["total_revenue"])) < Decimal("0.01")


def test_farmer_income_vs_single_channel(realization_service, sample_allocation, sample_inventory):
    """
    Test comparison to best single-channel price.
    
    Best single channel is society at 50/kg.
    Blended realization is 45.28/kg.
    
    For Farmer 1 (100 kg):
    - Blended: 100 * 45.28 = 4528
    - Single: 100 * 50 = 5000
    - Improvement: 4528 - 5000 = -472 (negative because blended is lower)
    """
    income = realization_service.calculate_farmer_income("FARMER001", sample_allocation, sample_inventory)
    
    # Verify comparison fields exist
    assert "vs_best_single_channel" in income
    comparison = income["vs_best_single_channel"]
    
    assert "single_channel_revenue" in comparison
    assert "improvement" in comparison
    assert "improvement_percentage" in comparison
    
    # For this case, single channel (50/kg) is better than blended (45.28/kg)
    # So improvement should be negative
    improvement = Decimal(comparison["improvement"])
    assert improvement < 0
    
    # Single channel revenue should be 100 * 50 = 5000
    single_revenue = Decimal(comparison["single_channel_revenue"])
    assert single_revenue == Decimal("5000")


def test_calculate_all_farmer_incomes(realization_service, sample_allocation, sample_inventory):
    """
    Test calculating income for all farmers.
    """
    all_incomes = realization_service.calculate_all_farmer_incomes(sample_allocation, sample_inventory)
    
    # Should have 3 farmers
    assert len(all_incomes) == 3
    
    # Verify all farmer IDs are present
    farmer_ids = {income["farmer_id"] for income in all_incomes}
    assert farmer_ids == {"FARMER001", "FARMER002", "FARMER003"}
    
    # Verify total revenue conservation
    total_revenue = sum(Decimal(income["total_revenue"]) for income in all_incomes)
    expected_total = Decimal("8150")
    
    assert abs(total_revenue - expected_total) < Decimal("0.01")


def test_get_realization_report(realization_service, sample_allocation, sample_inventory):
    """
    Test generating complete realization report.
    """
    report = realization_service.get_realization_report(sample_allocation, sample_inventory)
    
    # Verify report structure
    assert "allocation_id" in report
    assert "fpo_id" in report
    assert "crop_type" in report
    assert "allocation_date" in report
    assert "blended_realization_per_kg" in report
    assert "total_quantity_kg" in report
    assert "total_revenue" in report
    assert "channel_breakdown" in report
    assert "best_single_channel_price" in report
    assert "farmer_incomes" in report
    assert "num_farmers" in report
    
    # Verify values
    assert report["allocation_id"] == "ALLOC001"
    assert report["fpo_id"] == "FPO001"
    assert report["crop_type"] == "tomato"
    assert Decimal(report["total_quantity_kg"]) == Decimal("180")
    assert Decimal(report["total_revenue"]) == Decimal("8150")
    assert report["num_farmers"] == 3
    
    # Verify blended realization
    expected_blended = Decimal("8150") / Decimal("180")
    assert abs(Decimal(report["blended_realization_per_kg"]) - expected_blended) < Decimal("0.01")


def test_farmer_income_no_contribution_error(realization_service, sample_allocation, sample_inventory):
    """
    Test that calculating income for non-existent farmer raises error.
    """
    with pytest.raises(ValueError, match="has no contributions"):
        realization_service.calculate_farmer_income("FARMER999", sample_allocation, sample_inventory)


def test_blended_realization_empty_allocation_error(realization_service):
    """
    Test that empty allocation raises error.
    """
    with pytest.raises(ValueError, match="Cannot calculate blended realization with no allocations"):
        realization_service.calculate_blended_realization([])


def test_farmer_income_empty_allocation(realization_service, sample_inventory):
    """
    Test farmer income calculation with empty allocation.
    """
    # Create empty allocation
    empty_allocation = Allocation(
        allocation_id="ALLOC_EMPTY",
        fpo_id="FPO001",
        crop_type="tomato",
        allocation_date=date(2026, 3, 8),
        channel_allocations=[],
        total_quantity_kg=Decimal("0"),
        blended_realization_per_kg=Decimal("0"),
    )
    
    income = realization_service.calculate_farmer_income("FARMER001", empty_allocation, sample_inventory)
    
    # Should return zero values
    assert Decimal(income["total_revenue"]) == Decimal("0")
    assert Decimal(income["blended_rate_per_kg"]) == Decimal("0")
    assert len(income["channel_breakdown"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
