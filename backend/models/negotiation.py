"""
Negotiation models.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class NegotiationMessage:
    """
    Represents a single message in negotiation.
    """
    sender: Literal['agent', 'buyer']
    message: str
    price_mentioned: float | None
    timestamp: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'sender': self.sender,
            'message': self.message,
            'price_mentioned': self.price_mentioned,
            'timestamp': self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NegotiationMessage':
        """Create from dictionary."""
        return cls(
            sender=data['sender'],
            message=data['message'],
            price_mentioned=float(data['price_mentioned']) if data.get('price_mentioned') else None,
            timestamp=data['timestamp'],
        )


@dataclass
class NegotiationResult:
    """
    Final result of negotiation.
    """
    agreed_price: float
    buyer_name: str
    message_count: int
    duration_seconds: float
    success: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'agreed_price': self.agreed_price,
            'buyer_name': self.buyer_name,
            'message_count': self.message_count,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NegotiationResult':
        """Create from dictionary."""
        return cls(
            agreed_price=float(data['agreed_price']),
            buyer_name=data['buyer_name'],
            message_count=int(data['message_count']),
            duration_seconds=float(data['duration_seconds']),
            success=bool(data['success']),
        )
