"""
Property-based test for contribution aggregation.

**Validates: Requirements 1.1**

Property 2: Contribution Aggregation
For any collective inventory, the total quantity must equal the sum of all farmer contributions.
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


class TestContributionAggregation:
    """
    Property-based tests for contribution aggregation.
    
    **Validates: Requirements 1.1**
    """
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_contribution_aggregation_property(self, inventory: CollectiveInventory):
        """
        Property 2: Contribution Aggregation
        
        For any collective inventory, the total quantity must equal 
        the sum of all farmer contributions.
        
        **Validates: Requirements 1.1**
        """
        # Calculate sum of all contributions
        contribution_total = sum(c.quantity_kg for c in inventory.contributions)
        
        # Property: total_quantity must equal sum of contributions
        assert inventory.total_quantity_kg == contribution_total, (
            f"Contribution aggregation violated: "
            f"total_quantity={inventory.total_quantity_kg}, "
            f"sum(contributions)={contribution_total}"
        )
    
    @given(
        st.lists(farmer_contribution_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_sequential_contribution_addition(self, contributions: list):
        """
        Test that adding contributions sequentially maintains the aggregation property.
        
        **Validates: Requirements 1.1**
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
            
            # After each addition, verify the property holds
            contribution_total = sum(c.quantity_kg for c in inventory.contributions)
            assert inventory.total_quantity_kg == contribution_total, (
                f"Aggregation violated after adding contribution: "
                f"total={inventory.total_quantity_kg}, sum={contribution_total}"
            )
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_contribution_aggregation_with_reservations(self, inventory: CollectiveInventory):
        """
        Test that contribution aggregation holds even when inventory is reserved.
        
        Reservations should not affect the total quantity or contribution sum.
        
        **Validates: Requirements 1.1**
        """
        # Calculate contribution total before any operations
        contribution_total_before = sum(c.quantity_kg for c in inventory.contributions)
        total_before = inventory.total_quantity_kg
        
        # Verify initial property
        assert total_before == contribution_total_before
        
        # After reservations, the property should still hold
        contribution_total_after = sum(c.quantity_kg for c in inventory.contributions)
        assert inventory.total_quantity_kg == contribution_total_after, (
            f"Aggregation violated after reservations: "
            f"total={inventory.total_quantity_kg}, sum={contribution_total_after}"
        )
        
        # Total quantity should not change due to reservations
        assert inventory.total_quantity_kg == total_before
    
    @given(collective_inventory_strategy())
    @settings(max_examples=100, deadline=None)
    def test_contribution_aggregation_with_allocations(self, inventory: CollectiveInventory):
        """
        Test that contribution aggregation holds even when inventory is allocated.
        
        Allocations should not affect the total quantity or contribution sum.
        
        **Validates: Requirements 1.1**
        """
        # Calculate contribution total before any operations
        contribution_total_before = sum(c.quantity_kg for c in inventory.contributions)
        total_before = inventory.total_quantity_kg
        
        # Verify initial property
        assert total_before == contribution_total_before
        
        # After allocations, the property should still hold
        contribution_total_after = sum(c.quantity_kg for c in inventory.contributions)
        assert inventory.total_quantity_kg == contribution_total_after, (
            f"Aggregation violated after allocations: "
            f"total={inventory.total_quantity_kg}, sum={contribution_total_after}"
        )
        
        # Total quantity should not change due to allocations
        assert inventory.total_quantity_kg == total_before
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),  # farmer_id
                st.decimals(min_value=Decimal("0.1"), max_value=Decimal("500"), places=2),  # quantity
            ),
            min_size=1,
            max_size=30
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_contribution_aggregation_from_scratch(self, fpo_id: str, crop_type: str, farmer_data: list):
        """
        Test building inventory from scratch and verifying aggregation property.
        
        **Validates: Requirements 1.1**
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
        
        expected_total = Decimal("0")
        
        for farmer_id, quantity in farmer_data:
            contribution = FarmerContribution(
                contribution_id=f"contrib_{len(inventory.contributions)}",
                farmer_id=farmer_id,
                farmer_name=f"Farmer {farmer_id}",
                crop_type=crop_type,
                quantity_kg=quantity,
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            )
            
            inventory.add_contribution(contribution)
            expected_total += quantity
            
            # Verify property after each addition
            actual_total = sum(c.quantity_kg for c in inventory.contributions)
            assert inventory.total_quantity_kg == actual_total
            assert abs(inventory.total_quantity_kg - expected_total) < Decimal("0.01")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
