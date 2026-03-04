"""
Farmer input data model.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class FarmerInput:
    """
    Represents farmer harvest input for demo.
    """
    farmer_name: str
    crop_type: Literal['tomato', 'onion', 'chili']
    plot_area: float  # acres
    estimated_quantity: float  # kg
    location: str  # e.g., "Sinnar, Nashik"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DynamoDB storage."""
        return {
            'farmer_name': self.farmer_name,
            'crop_type': self.crop_type,
            'plot_area': self.plot_area,
            'estimated_quantity': self.estimated_quantity,
            'location': self.location,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FarmerInput':
        """Create from dictionary."""
        return cls(
            farmer_name=data['farmer_name'],
            crop_type=data['crop_type'],
            plot_area=float(data['plot_area']),
            estimated_quantity=float(data['estimated_quantity']),
            location=data['location'],
        )
    
    @classmethod
    def get_default(cls) -> 'FarmerInput':
        """Get default demo input."""
        return cls(
            farmer_name="Ramesh Patil",
            crop_type="tomato",
            plot_area=2.1,
            estimated_quantity=2300.0,
            location="Sinnar, Nashik"
        )
