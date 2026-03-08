"""
Collective Inventory data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum


class QualityGrade(str, Enum):
    """Quality grade for farmer contributions"""
    A = "A"
    B = "B"
    C = "C"


@dataclass
class FarmerContribution:
    """
    Represents an individual farmer's contribution to collective inventory.
    
    Attributes:
        contribution_id: Unique identifier for this contribution
        farmer_id: Unique identifier for the farmer
        farmer_name: Name of the farmer
        crop_type: Type of crop (e.g., "tomato", "onion")
        quantity_kg: Quantity in kilograms
        quality_grade: Quality grade (A, B, or C)
        timestamp: When the contribution was made
        allocated: Whether this contribution has been allocated
    """
    contribution_id: str
    farmer_id: str
    farmer_name: str
    crop_type: str
    quantity_kg: Decimal
    quality_grade: QualityGrade
    timestamp: datetime
    allocated: bool = False
    
    def __post_init__(self):
        """Validate contribution data"""
        if self.quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity_kg}")
        
        if not isinstance(self.quality_grade, QualityGrade):
            self.quality_grade = QualityGrade(self.quality_grade)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "contribution_id": self.contribution_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "crop_type": self.crop_type,
            "quantity_kg": str(self.quantity_kg),
            "quality_grade": self.quality_grade.value,
            "timestamp": self.timestamp.isoformat(),
            "allocated": self.allocated,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FarmerContribution":
        """Create from dictionary"""
        return cls(
            contribution_id=data["contribution_id"],
            farmer_id=data["farmer_id"],
            farmer_name=data["farmer_name"],
            crop_type=data["crop_type"],
            quantity_kg=Decimal(data["quantity_kg"]),
            quality_grade=QualityGrade(data["quality_grade"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            allocated=data.get("allocated", False),
        )


@dataclass
class CollectiveInventory:
    """
    Represents the collective inventory pool for an FPO and crop type.
    
    Invariants:
    - total_quantity_kg = sum(all contributions)
    - available_quantity_kg = total_quantity_kg - reserved_quantity_kg - allocated_quantity_kg
    - available_quantity_kg >= 0
    
    Attributes:
        fpo_id: Unique identifier for the FPO
        crop_type: Type of crop
        total_quantity_kg: Total quantity from all contributions
        available_quantity_kg: Quantity available for allocation
        reserved_quantity_kg: Quantity reserved for society demand
        allocated_quantity_kg: Quantity already allocated
        contributions: List of farmer contributions
        last_updated: Last update timestamp
    """
    fpo_id: str
    crop_type: str
    total_quantity_kg: Decimal
    available_quantity_kg: Decimal
    reserved_quantity_kg: Decimal
    allocated_quantity_kg: Decimal
    contributions: List[FarmerContribution] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate inventory invariants"""
        self.validate_invariants()
    
    def validate_invariants(self):
        """Validate inventory conservation invariants"""
        # Check that quantities are non-negative
        if self.total_quantity_kg < 0:
            raise ValueError(f"Total quantity cannot be negative: {self.total_quantity_kg}")
        if self.available_quantity_kg < 0:
            raise ValueError(f"Available quantity cannot be negative: {self.available_quantity_kg}")
        if self.reserved_quantity_kg < 0:
            raise ValueError(f"Reserved quantity cannot be negative: {self.reserved_quantity_kg}")
        if self.allocated_quantity_kg < 0:
            raise ValueError(f"Allocated quantity cannot be negative: {self.allocated_quantity_kg}")
        
        # Check inventory conservation
        expected_total = self.available_quantity_kg + self.reserved_quantity_kg + self.allocated_quantity_kg
        if abs(self.total_quantity_kg - expected_total) > Decimal("0.01"):
            raise ValueError(
                f"Inventory conservation violated: total={self.total_quantity_kg}, "
                f"available+reserved+allocated={expected_total}"
            )
        
        # Check contribution aggregation
        if self.contributions:
            contribution_total = sum(c.quantity_kg for c in self.contributions)
            if abs(self.total_quantity_kg - contribution_total) > Decimal("0.01"):
                raise ValueError(
                    f"Contribution aggregation violated: total={self.total_quantity_kg}, "
                    f"sum(contributions)={contribution_total}"
                )
    
    def add_contribution(self, contribution: FarmerContribution):
        """Add a farmer contribution to the inventory"""
        if contribution.crop_type != self.crop_type:
            raise ValueError(
                f"Crop type mismatch: inventory={self.crop_type}, "
                f"contribution={contribution.crop_type}"
            )
        
        self.contributions.append(contribution)
        self.total_quantity_kg += contribution.quantity_kg
        self.available_quantity_kg += contribution.quantity_kg
        self.last_updated = datetime.now()
        
        self.validate_invariants()
    
    def reserve_quantity(self, quantity: Decimal):
        """Reserve quantity for society demand"""
        if quantity > self.available_quantity_kg:
            raise ValueError(
                f"Cannot reserve {quantity} kg, only {self.available_quantity_kg} kg available"
            )
        
        self.available_quantity_kg -= quantity
        self.reserved_quantity_kg += quantity
        self.last_updated = datetime.now()
        
        self.validate_invariants()
    
    def allocate_quantity(self, quantity: Decimal):
        """Allocate quantity to a channel"""
        if quantity > self.available_quantity_kg:
            raise ValueError(
                f"Cannot allocate {quantity} kg, only {self.available_quantity_kg} kg available"
            )
        
        self.available_quantity_kg -= quantity
        self.allocated_quantity_kg += quantity
        self.last_updated = datetime.now()
        
        self.validate_invariants()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "fpo_id": self.fpo_id,
            "crop_type": self.crop_type,
            "total_quantity_kg": str(self.total_quantity_kg),
            "available_quantity_kg": str(self.available_quantity_kg),
            "reserved_quantity_kg": str(self.reserved_quantity_kg),
            "allocated_quantity_kg": str(self.allocated_quantity_kg),
            "contributions": [c.to_dict() for c in self.contributions],
            "last_updated": self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CollectiveInventory":
        """Create from dictionary"""
        return cls(
            fpo_id=data["fpo_id"],
            crop_type=data["crop_type"],
            total_quantity_kg=Decimal(data["total_quantity_kg"]),
            available_quantity_kg=Decimal(data["available_quantity_kg"]),
            reserved_quantity_kg=Decimal(data["reserved_quantity_kg"]),
            allocated_quantity_kg=Decimal(data["allocated_quantity_kg"]),
            contributions=[
                FarmerContribution.from_dict(c) for c in data.get("contributions", [])
            ],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )
