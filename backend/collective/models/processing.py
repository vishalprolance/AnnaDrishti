"""
Processing partner data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict


@dataclass
class ProcessingPartner:
    """
    Processing partner profile with rates and capacity.
    
    Attributes:
        partner_id: Unique identifier
        partner_name: Name of the processing partner
        contact_details: Contact information
        facility_location: Location of processing facility
        rates_by_crop: Rates per kg by crop type
        capacity_by_crop: Daily capacity in kg by crop type
        quality_requirements: Quality requirements by crop type
        pickup_schedule: Pickup schedule description
        created_at: When the profile was created
    """
    partner_id: str
    partner_name: str
    contact_details: Dict[str, str]
    facility_location: str
    rates_by_crop: Dict[str, Decimal]
    capacity_by_crop: Dict[str, Decimal]
    quality_requirements: Dict[str, str]
    pickup_schedule: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate processing partner data"""
        # Validate rates are positive
        for crop, rate in self.rates_by_crop.items():
            if rate <= 0:
                raise ValueError(f"Rate for {crop} must be positive: {rate}")
        
        # Validate capacities are non-negative
        for crop, capacity in self.capacity_by_crop.items():
            if capacity < 0:
                raise ValueError(f"Capacity for {crop} cannot be negative: {capacity}")
    
    def get_rate(self, crop_type: str) -> Decimal:
        """Get rate for a crop type"""
        return self.rates_by_crop.get(crop_type, Decimal("0"))
    
    def get_capacity(self, crop_type: str) -> Decimal:
        """Get capacity for a crop type"""
        return self.capacity_by_crop.get(crop_type, Decimal("0"))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "partner_id": self.partner_id,
            "partner_name": self.partner_name,
            "contact_details": self.contact_details,
            "facility_location": self.facility_location,
            "rates_by_crop": {k: str(v) for k, v in self.rates_by_crop.items()},
            "capacity_by_crop": {k: str(v) for k, v in self.capacity_by_crop.items()},
            "quality_requirements": self.quality_requirements,
            "pickup_schedule": self.pickup_schedule,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingPartner":
        """Create from dictionary"""
        return cls(
            partner_id=data["partner_id"],
            partner_name=data["partner_name"],
            contact_details=data["contact_details"],
            facility_location=data["facility_location"],
            rates_by_crop={k: Decimal(v) for k, v in data["rates_by_crop"].items()},
            capacity_by_crop={k: Decimal(v) for k, v in data["capacity_by_crop"].items()},
            quality_requirements=data["quality_requirements"],
            pickup_schedule=data["pickup_schedule"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
