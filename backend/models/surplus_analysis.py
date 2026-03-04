"""
Surplus analysis models.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ProcessorCapacity:
    """
    Represents a processor's capacity and rate.
    """
    name: str
    capacity_tonnes: float
    rate_per_kg: float  # ₹/kg
    location: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'capacity_tonnes': self.capacity_tonnes,
            'rate_per_kg': self.rate_per_kg,
            'location': self.location,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessorCapacity':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            capacity_tonnes=float(data['capacity_tonnes']),
            rate_per_kg=float(data['rate_per_kg']),
            location=data['location'],
        )


@dataclass
class SurplusAnalysis:
    """
    Result of surplus detection analysis.
    """
    total_volume_kg: float
    mandi_capacity_kg: float
    surplus_kg: float
    has_surplus: bool
    recommended_fresh_kg: float
    recommended_processing_kg: float
    processors: List[ProcessorCapacity]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'total_volume_kg': self.total_volume_kg,
            'mandi_capacity_kg': self.mandi_capacity_kg,
            'surplus_kg': self.surplus_kg,
            'has_surplus': self.has_surplus,
            'recommended_fresh_kg': self.recommended_fresh_kg,
            'recommended_processing_kg': self.recommended_processing_kg,
            'processors': [p.to_dict() for p in self.processors],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SurplusAnalysis':
        """Create from dictionary."""
        return cls(
            total_volume_kg=float(data['total_volume_kg']),
            mandi_capacity_kg=float(data['mandi_capacity_kg']),
            surplus_kg=float(data['surplus_kg']),
            has_surplus=bool(data['has_surplus']),
            recommended_fresh_kg=float(data['recommended_fresh_kg']),
            recommended_processing_kg=float(data['recommended_processing_kg']),
            processors=[ProcessorCapacity.from_dict(p) for p in data['processors']],
        )
