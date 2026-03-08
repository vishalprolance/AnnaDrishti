"""
Society and demand prediction data models
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional
from enum import Enum


class DeliveryFrequency(str, Enum):
    """Delivery frequency options for societies"""
    ONCE_WEEKLY = "once_weekly"
    TWICE_WEEKLY = "twice_weekly"
    WEEKEND_ONLY = "weekend_only"


class ReservationStatus(str, Enum):
    """Status of a reservation"""
    PREDICTED = "predicted"
    CONFIRMED = "confirmed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


@dataclass
class CropPreference:
    """Crop preference for a society"""
    crop_type: str
    typical_quantity_kg: Decimal
    
    def to_dict(self) -> dict:
        return {
            "crop_type": self.crop_type,
            "typical_quantity_kg": str(self.typical_quantity_kg),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CropPreference":
        return cls(
            crop_type=data["crop_type"],
            typical_quantity_kg=Decimal(data["typical_quantity_kg"]),
        )


@dataclass
class SocietyProfile:
    """
    Profile for a residential society that orders produce.
    
    Attributes:
        society_id: Unique identifier
        society_name: Name of the society
        location: Location/address
        contact_details: Contact information (phone, email, etc.)
        delivery_address: Delivery address
        delivery_frequency: How often they want deliveries
        preferred_day: Preferred delivery day (e.g., "Monday")
        preferred_time_window: Preferred time window (e.g., "9:00-11:00")
        crop_preferences: List of crop preferences with typical quantities
        created_at: When the profile was created
    """
    society_id: str
    society_name: str
    location: str
    contact_details: Dict[str, str]
    delivery_address: str
    delivery_frequency: DeliveryFrequency
    preferred_day: str
    preferred_time_window: str
    crop_preferences: List[CropPreference] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate society profile"""
        if not isinstance(self.delivery_frequency, DeliveryFrequency):
            self.delivery_frequency = DeliveryFrequency(self.delivery_frequency)
    
    def get_typical_quantity(self, crop_type: str) -> Optional[Decimal]:
        """Get typical quantity for a crop type"""
        for pref in self.crop_preferences:
            if pref.crop_type == crop_type:
                return pref.typical_quantity_kg
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "society_id": self.society_id,
            "society_name": self.society_name,
            "location": self.location,
            "contact_details": self.contact_details,
            "delivery_address": self.delivery_address,
            "delivery_frequency": self.delivery_frequency.value,
            "preferred_day": self.preferred_day,
            "preferred_time_window": self.preferred_time_window,
            "crop_preferences": [p.to_dict() for p in self.crop_preferences],
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SocietyProfile":
        """Create from dictionary"""
        return cls(
            society_id=data["society_id"],
            society_name=data["society_name"],
            location=data["location"],
            contact_details=data["contact_details"],
            delivery_address=data["delivery_address"],
            delivery_frequency=DeliveryFrequency(data["delivery_frequency"]),
            preferred_day=data["preferred_day"],
            preferred_time_window=data["preferred_time_window"],
            crop_preferences=[
                CropPreference.from_dict(p) for p in data.get("crop_preferences", [])
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class DemandPrediction:
    """
    Predicted demand for a society and crop type.
    
    Attributes:
        prediction_id: Unique identifier
        society_id: Society this prediction is for
        crop_type: Crop type
        predicted_quantity_kg: Predicted quantity in kg
        confidence_score: Confidence score (0.0 to 1.0)
        prediction_date: When the prediction was made
        delivery_date: Expected delivery date
        based_on_orders: Number of historical orders used
        status: Current status of the prediction
    """
    prediction_id: str
    society_id: str
    crop_type: str
    predicted_quantity_kg: Decimal
    confidence_score: float
    prediction_date: datetime
    delivery_date: date
    based_on_orders: int
    status: ReservationStatus = ReservationStatus.PREDICTED
    
    def __post_init__(self):
        """Validate prediction"""
        if self.predicted_quantity_kg < 0:
            raise ValueError(f"Predicted quantity cannot be negative: {self.predicted_quantity_kg}")
        
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"Confidence score must be between 0 and 1: {self.confidence_score}")
        
        if not isinstance(self.status, ReservationStatus):
            self.status = ReservationStatus(self.status)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "prediction_id": self.prediction_id,
            "society_id": self.society_id,
            "crop_type": self.crop_type,
            "predicted_quantity_kg": str(self.predicted_quantity_kg),
            "confidence_score": self.confidence_score,
            "prediction_date": self.prediction_date.isoformat(),
            "delivery_date": self.delivery_date.isoformat(),
            "based_on_orders": self.based_on_orders,
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DemandPrediction":
        """Create from dictionary"""
        return cls(
            prediction_id=data["prediction_id"],
            society_id=data["society_id"],
            crop_type=data["crop_type"],
            predicted_quantity_kg=Decimal(data["predicted_quantity_kg"]),
            confidence_score=data["confidence_score"],
            prediction_date=datetime.fromisoformat(data["prediction_date"]),
            delivery_date=date.fromisoformat(data["delivery_date"]),
            based_on_orders=data["based_on_orders"],
            status=ReservationStatus(data.get("status", "predicted")),
        )


@dataclass
class Reservation:
    """
    Reservation of inventory for society demand.
    
    Attributes:
        reservation_id: Unique identifier
        society_id: Society this reservation is for
        crop_type: Crop type
        reserved_quantity_kg: Reserved quantity in kg
        reservation_timestamp: When the reservation was made
        delivery_date: Expected delivery date
        status: Current status
    """
    reservation_id: str
    society_id: str
    crop_type: str
    reserved_quantity_kg: Decimal
    reservation_timestamp: datetime
    delivery_date: date
    status: ReservationStatus = ReservationStatus.PREDICTED
    
    def __post_init__(self):
        """Validate reservation"""
        if self.reserved_quantity_kg < 0:
            raise ValueError(f"Reserved quantity cannot be negative: {self.reserved_quantity_kg}")
        
        if not isinstance(self.status, ReservationStatus):
            self.status = ReservationStatus(self.status)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "reservation_id": self.reservation_id,
            "society_id": self.society_id,
            "crop_type": self.crop_type,
            "reserved_quantity_kg": str(self.reserved_quantity_kg),
            "reservation_timestamp": self.reservation_timestamp.isoformat(),
            "delivery_date": self.delivery_date.isoformat(),
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Reservation":
        """Create from dictionary"""
        return cls(
            reservation_id=data["reservation_id"],
            society_id=data["society_id"],
            crop_type=data["crop_type"],
            reserved_quantity_kg=Decimal(data["reserved_quantity_kg"]),
            reservation_timestamp=datetime.fromisoformat(data["reservation_timestamp"]),
            delivery_date=date.fromisoformat(data["delivery_date"]),
            status=ReservationStatus(data.get("status", "predicted")),
        )
