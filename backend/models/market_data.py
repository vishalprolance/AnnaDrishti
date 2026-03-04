"""
Market data models.
"""

from dataclasses import dataclass
from typing import List, Literal


@dataclass
class MandiPrice:
    """
    Represents price data from a single mandi.
    """
    name: str
    price: float  # ₹/kg
    distance_km: float
    net_price: float  # price - transport cost
    arrivals_tonnes: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'price': self.price,
            'distance_km': self.distance_km,
            'net_price': self.net_price,
            'arrivals_tonnes': self.arrivals_tonnes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MandiPrice':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            price=float(data['price']),
            distance_km=float(data['distance_km']),
            net_price=float(data['net_price']),
            arrivals_tonnes=float(data['arrivals_tonnes']),
        )


@dataclass
class MarketScanResult:
    """
    Result of market scan across multiple mandis.
    """
    mandis: List[MandiPrice]
    recommended: str  # name of recommended mandi
    data_source: Literal['live', 'cached']
    timestamp: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'mandis': [m.to_dict() for m in self.mandis],
            'recommended': self.recommended,
            'data_source': self.data_source,
            'timestamp': self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MarketScanResult':
        """Create from dictionary."""
        return cls(
            mandis=[MandiPrice.from_dict(m) for m in data['mandis']],
            recommended=data['recommended'],
            data_source=data['data_source'],
            timestamp=data['timestamp'],
        )
    
    def get_best_mandi(self) -> MandiPrice:
        """Get mandi with highest net price."""
        return max(self.mandis, key=lambda m: m.net_price)
    
    def get_nearest_mandi(self) -> MandiPrice:
        """Get nearest mandi by distance."""
        return min(self.mandis, key=lambda m: m.distance_km)
