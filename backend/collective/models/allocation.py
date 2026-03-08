"""
Allocation data models
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List
from enum import Enum


class ChannelType(str, Enum):
    """Type of sales channel"""
    SOCIETY = "society"
    PROCESSING = "processing"
    MANDI = "mandi"


class AllocationStatus(str, Enum):
    """Status of an allocation"""
    PENDING = "pending"
    EXECUTED = "executed"
    COMPLETED = "completed"


class FulfillmentStatus(str, Enum):
    """Status of fulfillment"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"


@dataclass
class ChannelAllocation:
    """
    Allocation to a specific channel.
    
    Attributes:
        channel_type: Type of channel (society, processing, mandi)
        channel_id: Unique identifier for the channel
        channel_name: Name of the channel
        quantity_kg: Allocated quantity in kg
        price_per_kg: Price per kg for this channel
        revenue: Total revenue (quantity * price)
        priority: Priority level (1, 2, or 3)
        fulfillment_status: Current fulfillment status
    """
    channel_type: ChannelType
    channel_id: str
    channel_name: str
    quantity_kg: Decimal
    price_per_kg: Decimal
    revenue: Decimal
    priority: int
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.PENDING
    
    def __post_init__(self):
        """Validate channel allocation"""
        if not isinstance(self.channel_type, ChannelType):
            self.channel_type = ChannelType(self.channel_type)
        
        if not isinstance(self.fulfillment_status, FulfillmentStatus):
            self.fulfillment_status = FulfillmentStatus(self.fulfillment_status)
        
        if self.quantity_kg < 0:
            raise ValueError(f"Quantity cannot be negative: {self.quantity_kg}")
        
        if self.price_per_kg < 0:
            raise ValueError(f"Price cannot be negative: {self.price_per_kg}")
        
        if self.priority not in [1, 2, 3]:
            raise ValueError(f"Priority must be 1, 2, or 3: {self.priority}")
        
        # Validate revenue calculation
        expected_revenue = self.quantity_kg * self.price_per_kg
        if abs(self.revenue - expected_revenue) > Decimal("0.01"):
            raise ValueError(
                f"Revenue mismatch: expected {expected_revenue}, got {self.revenue}"
            )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "channel_type": self.channel_type.value,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "quantity_kg": str(self.quantity_kg),
            "price_per_kg": str(self.price_per_kg),
            "revenue": str(self.revenue),
            "priority": self.priority,
            "fulfillment_status": self.fulfillment_status.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChannelAllocation":
        """Create from dictionary"""
        return cls(
            channel_type=ChannelType(data["channel_type"]),
            channel_id=data["channel_id"],
            channel_name=data["channel_name"],
            quantity_kg=Decimal(data["quantity_kg"]),
            price_per_kg=Decimal(data["price_per_kg"]),
            revenue=Decimal(data["revenue"]),
            priority=data["priority"],
            fulfillment_status=FulfillmentStatus(data.get("fulfillment_status", "pending")),
        )


@dataclass
class Allocation:
    """
    Complete allocation of inventory across channels.
    
    Invariants:
    - blended_realization_per_kg = sum(revenue) / sum(quantity)
    - Priorities are ordered: 1 before 2 before 3
    - total_quantity_kg = sum(channel allocations)
    
    Attributes:
        allocation_id: Unique identifier
        fpo_id: FPO this allocation is for
        crop_type: Crop type
        allocation_date: Date of allocation
        channel_allocations: List of channel allocations
        total_quantity_kg: Total quantity allocated
        blended_realization_per_kg: Blended realization rate
        status: Current status
    """
    allocation_id: str
    fpo_id: str
    crop_type: str
    allocation_date: date
    channel_allocations: List[ChannelAllocation]
    total_quantity_kg: Decimal
    blended_realization_per_kg: Decimal
    status: AllocationStatus = AllocationStatus.PENDING
    
    def __post_init__(self):
        """Validate allocation"""
        if not isinstance(self.status, AllocationStatus):
            self.status = AllocationStatus(self.status)
        
        self.validate_invariants()
    
    def validate_invariants(self):
        """Validate allocation invariants"""
        if not self.channel_allocations:
            return  # Empty allocation is valid
        
        # Validate total quantity
        calculated_total = sum(ca.quantity_kg for ca in self.channel_allocations)
        if abs(self.total_quantity_kg - calculated_total) > Decimal("0.01"):
            raise ValueError(
                f"Total quantity mismatch: expected {calculated_total}, got {self.total_quantity_kg}"
            )
        
        # Validate blended realization
        total_revenue = sum(ca.revenue for ca in self.channel_allocations)
        if self.total_quantity_kg > 0:
            expected_blended = total_revenue / self.total_quantity_kg
            if abs(self.blended_realization_per_kg - expected_blended) > Decimal("0.01"):
                raise ValueError(
                    f"Blended realization mismatch: expected {expected_blended}, "
                    f"got {self.blended_realization_per_kg}"
                )
        
        # Validate priority ordering
        priorities = [ca.priority for ca in self.channel_allocations]
        for i in range(len(priorities) - 1):
            if priorities[i] > priorities[i + 1]:
                raise ValueError(
                    f"Priority ordering violated: {priorities[i]} before {priorities[i + 1]}"
                )
    
    def get_channel_breakdown(self) -> dict:
        """Get breakdown by channel type"""
        breakdown = {
            ChannelType.SOCIETY: {"quantity": Decimal("0"), "revenue": Decimal("0")},
            ChannelType.PROCESSING: {"quantity": Decimal("0"), "revenue": Decimal("0")},
            ChannelType.MANDI: {"quantity": Decimal("0"), "revenue": Decimal("0")},
        }
        
        for ca in self.channel_allocations:
            breakdown[ca.channel_type]["quantity"] += ca.quantity_kg
            breakdown[ca.channel_type]["revenue"] += ca.revenue
        
        return {
            k.value: {
                "quantity_kg": str(v["quantity"]),
                "revenue": str(v["revenue"]),
                "rate_per_kg": str(v["revenue"] / v["quantity"]) if v["quantity"] > 0 else "0",
            }
            for k, v in breakdown.items()
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "allocation_id": self.allocation_id,
            "fpo_id": self.fpo_id,
            "crop_type": self.crop_type,
            "allocation_date": self.allocation_date.isoformat(),
            "channel_allocations": [ca.to_dict() for ca in self.channel_allocations],
            "total_quantity_kg": str(self.total_quantity_kg),
            "blended_realization_per_kg": str(self.blended_realization_per_kg),
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Allocation":
        """Create from dictionary"""
        return cls(
            allocation_id=data["allocation_id"],
            fpo_id=data["fpo_id"],
            crop_type=data["crop_type"],
            allocation_date=date.fromisoformat(data["allocation_date"]),
            channel_allocations=[
                ChannelAllocation.from_dict(ca) for ca in data["channel_allocations"]
            ],
            total_quantity_kg=Decimal(data["total_quantity_kg"]),
            blended_realization_per_kg=Decimal(data["blended_realization_per_kg"]),
            status=AllocationStatus(data.get("status", "pending")),
        )
