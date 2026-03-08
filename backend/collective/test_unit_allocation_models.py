"""
Unit tests for Allocation and ChannelAllocation data models
"""

import pytest
from decimal import Decimal
from datetime import date

from backend.collective.models.allocation import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
)


class TestChannelAllocation:
    """Test ChannelAllocation data model"""
    
    def test_create_valid_channel_allocation(self):
        """Test creating a valid channel allocation"""
        ca = ChannelAllocation(
            channel_type=ChannelType.SOCIETY,
            channel_id="SOC001",
            channel_name="Green Valley Society",
            quantity_kg=Decimal("100"),
            price_per_kg=Decimal("50"),
            revenue=Decimal("5000"),
            priority=1,
        )
        
        assert ca.channel_type == ChannelType.SOCIETY
        assert ca.channel_id == "SOC001"
        assert ca.quantity_kg == Decimal("100")
        assert ca.price_per_kg == Decimal("50")
        assert ca.revenue == Decimal("5000")
        assert ca.priority == 1
        assert ca.fulfillment_status == FulfillmentStatus.PENDING
    
    def test_validate_priority_values(self):
        """Test that priority must be 1, 2, or 3"""
        # Valid priorities
        for priority in [1, 2, 3]:
            ca = ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Test Society",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=priority,
            )
            assert ca.priority == priority
        
        # Invalid priorities
        for invalid_priority in [0, 4, -1, 10]:
            with pytest.raises(ValueError, match="Priority must be 1, 2, or 3"):
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Test Society",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("5000"),
                    priority=invalid_priority,
                )
    
    def test_validate_negative_quantity(self):
        """Test that quantity cannot be negative"""
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Test Society",
                quantity_kg=Decimal("-100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("-5000"),
                priority=1,
            )
    
    def test_validate_negative_price(self):
        """Test that price cannot be negative"""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Test Society",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("-50"),
                revenue=Decimal("-5000"),
                priority=1,
            )
    
    def test_validate_revenue_calculation(self):
        """Test that revenue must match quantity * price"""
        # Valid revenue
        ca = ChannelAllocation(
            channel_type=ChannelType.SOCIETY,
            channel_id="SOC001",
            channel_name="Test Society",
            quantity_kg=Decimal("100"),
            price_per_kg=Decimal("50"),
            revenue=Decimal("5000"),
            priority=1,
        )
        assert ca.revenue == Decimal("5000")
        
        # Invalid revenue
        with pytest.raises(ValueError, match="Revenue mismatch"):
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Test Society",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("4000"),  # Should be 5000
                priority=1,
            )
    
    def test_channel_allocation_to_dict(self):
        """Test converting channel allocation to dictionary"""
        ca = ChannelAllocation(
            channel_type=ChannelType.PROCESSING,
            channel_id="PROC001",
            channel_name="ABC Processing",
            quantity_kg=Decimal("200"),
            price_per_kg=Decimal("45"),
            revenue=Decimal("9000"),
            priority=2,
            fulfillment_status=FulfillmentStatus.IN_TRANSIT,
        )
        
        data = ca.to_dict()
        
        assert data["channel_type"] == "processing"
        assert data["channel_id"] == "PROC001"
        assert data["quantity_kg"] == "200"
        assert data["price_per_kg"] == "45"
        assert data["revenue"] == "9000"
        assert data["priority"] == 2
        assert data["fulfillment_status"] == "in_transit"
    
    def test_channel_allocation_from_dict(self):
        """Test creating channel allocation from dictionary"""
        data = {
            "channel_type": "mandi",
            "channel_id": "MAN001",
            "channel_name": "City Mandi",
            "quantity_kg": "150",
            "price_per_kg": "40",
            "revenue": "6000",
            "priority": 3,
            "fulfillment_status": "delivered",
        }
        
        ca = ChannelAllocation.from_dict(data)
        
        assert ca.channel_type == ChannelType.MANDI
        assert ca.channel_id == "MAN001"
        assert ca.quantity_kg == Decimal("150")
        assert ca.price_per_kg == Decimal("40")
        assert ca.revenue == Decimal("6000")
        assert ca.priority == 3
        assert ca.fulfillment_status == FulfillmentStatus.DELIVERED


class TestAllocation:
    """Test Allocation data model"""
    
    def test_create_valid_allocation(self):
        """Test creating a valid allocation"""
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="PROC001",
                channel_name="ABC Processing",
                quantity_kg=Decimal("200"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("9000"),
                priority=2,
            ),
        ]
        
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations,
            total_quantity_kg=Decimal("300"),
            blended_realization_per_kg=Decimal("46.67"),
        )
        
        assert allocation.allocation_id == "ALLOC001"
        assert allocation.fpo_id == "FPO001"
        assert allocation.crop_type == "tomato"
        assert len(allocation.channel_allocations) == 2
        assert allocation.total_quantity_kg == Decimal("300")
        assert allocation.status == AllocationStatus.PENDING
    
    def test_validate_total_quantity(self):
        """Test that total quantity must match sum of channel allocations"""
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
        ]
        
        # Valid total
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations,
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("50"),
        )
        assert allocation.total_quantity_kg == Decimal("100")
        
        # Invalid total
        with pytest.raises(ValueError, match="Total quantity mismatch"):
            Allocation(
                allocation_id="ALLOC001",
                fpo_id="FPO001",
                crop_type="tomato",
                allocation_date=date(2024, 1, 15),
                channel_allocations=channel_allocations,
                total_quantity_kg=Decimal("200"),  # Should be 100
                blended_realization_per_kg=Decimal("50"),
            )
    
    def test_validate_blended_realization(self):
        """Test that blended realization must match total revenue / total quantity"""
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="PROC001",
                channel_name="ABC Processing",
                quantity_kg=Decimal("200"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("9000"),
                priority=2,
            ),
        ]
        
        # Valid blended realization: (5000 + 9000) / (100 + 200) = 46.67
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations,
            total_quantity_kg=Decimal("300"),
            blended_realization_per_kg=Decimal("46.67"),
        )
        assert allocation.blended_realization_per_kg == Decimal("46.67")
        
        # Invalid blended realization
        with pytest.raises(ValueError, match="Blended realization mismatch"):
            Allocation(
                allocation_id="ALLOC001",
                fpo_id="FPO001",
                crop_type="tomato",
                allocation_date=date(2024, 1, 15),
                channel_allocations=channel_allocations,
                total_quantity_kg=Decimal("300"),
                blended_realization_per_kg=Decimal("50"),  # Should be 46.67
            )
    
    def test_validate_priority_ordering(self):
        """Test that priorities must be in ascending order"""
        # Valid ordering: 1, 2, 3
        channel_allocations_valid = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="PROC001",
                channel_name="ABC Processing",
                quantity_kg=Decimal("200"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("9000"),
                priority=2,
            ),
            ChannelAllocation(
                channel_type=ChannelType.MANDI,
                channel_id="MAN001",
                channel_name="City Mandi",
                quantity_kg=Decimal("150"),
                price_per_kg=Decimal("40"),
                revenue=Decimal("6000"),
                priority=3,
            ),
        ]
        
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations_valid,
            total_quantity_kg=Decimal("450"),
            blended_realization_per_kg=Decimal("44.44"),
        )
        assert len(allocation.channel_allocations) == 3
        
        # Invalid ordering: 2, 1, 3
        channel_allocations_invalid = [
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="PROC001",
                channel_name="ABC Processing",
                quantity_kg=Decimal("200"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("9000"),
                priority=2,
            ),
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
        ]
        
        with pytest.raises(ValueError, match="Priority ordering violated"):
            Allocation(
                allocation_id="ALLOC001",
                fpo_id="FPO001",
                crop_type="tomato",
                allocation_date=date(2024, 1, 15),
                channel_allocations=channel_allocations_invalid,
                total_quantity_kg=Decimal("300"),
                blended_realization_per_kg=Decimal("46.67"),
            )
    
    def test_empty_allocation(self):
        """Test that empty allocation is valid"""
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=[],
            total_quantity_kg=Decimal("0"),
            blended_realization_per_kg=Decimal("0"),
        )
        
        assert len(allocation.channel_allocations) == 0
        assert allocation.total_quantity_kg == Decimal("0")
    
    def test_get_channel_breakdown(self):
        """Test getting channel breakdown"""
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC002",
                channel_name="Blue Hills",
                quantity_kg=Decimal("50"),
                price_per_kg=Decimal("52"),
                revenue=Decimal("2600"),
                priority=1,
            ),
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="PROC001",
                channel_name="ABC Processing",
                quantity_kg=Decimal("200"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("9000"),
                priority=2,
            ),
        ]
        
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations,
            total_quantity_kg=Decimal("350"),
            blended_realization_per_kg=Decimal("47.43"),
        )
        
        breakdown = allocation.get_channel_breakdown()
        
        # Society: 100 + 50 = 150 kg, 5000 + 2600 = 7600 revenue
        assert breakdown["society"]["quantity_kg"] == "150"
        assert breakdown["society"]["revenue"] == "7600"
        
        # Processing: 200 kg, 9000 revenue
        assert breakdown["processing"]["quantity_kg"] == "200"
        assert breakdown["processing"]["revenue"] == "9000"
        
        # Mandi: 0 kg, 0 revenue
        assert breakdown["mandi"]["quantity_kg"] == "0"
        assert breakdown["mandi"]["revenue"] == "0"
    
    def test_allocation_to_dict(self):
        """Test converting allocation to dictionary"""
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Green Valley",
                quantity_kg=Decimal("100"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("5000"),
                priority=1,
            ),
        ]
        
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=channel_allocations,
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.EXECUTED,
        )
        
        data = allocation.to_dict()
        
        assert data["allocation_id"] == "ALLOC001"
        assert data["fpo_id"] == "FPO001"
        assert data["crop_type"] == "tomato"
        assert data["allocation_date"] == "2024-01-15"
        assert len(data["channel_allocations"]) == 1
        assert data["total_quantity_kg"] == "100"
        assert data["blended_realization_per_kg"] == "50"
        assert data["status"] == "executed"
    
    def test_allocation_from_dict(self):
        """Test creating allocation from dictionary"""
        data = {
            "allocation_id": "ALLOC001",
            "fpo_id": "FPO001",
            "crop_type": "tomato",
            "allocation_date": "2024-01-15",
            "channel_allocations": [
                {
                    "channel_type": "society",
                    "channel_id": "SOC001",
                    "channel_name": "Green Valley",
                    "quantity_kg": "100",
                    "price_per_kg": "50",
                    "revenue": "5000",
                    "priority": 1,
                    "fulfillment_status": "pending",
                }
            ],
            "total_quantity_kg": "100",
            "blended_realization_per_kg": "50",
            "status": "completed",
        }
        
        allocation = Allocation.from_dict(data)
        
        assert allocation.allocation_id == "ALLOC001"
        assert allocation.fpo_id == "FPO001"
        assert allocation.crop_type == "tomato"
        assert allocation.allocation_date == date(2024, 1, 15)
        assert len(allocation.channel_allocations) == 1
        assert allocation.total_quantity_kg == Decimal("100")
        assert allocation.blended_realization_per_kg == Decimal("50")
        assert allocation.status == AllocationStatus.COMPLETED
