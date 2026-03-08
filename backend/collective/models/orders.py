"""
Order data models for allocation execution and tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from enum import Enum


class OrderType(str, Enum):
    """Type of order"""
    DELIVERY = "delivery"
    PICKUP = "pickup"
    DISPATCH = "dispatch"


class OrderStatus(str, Enum):
    """Status of an order"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DeliveryOrder:
    """
    Delivery order for society allocation.
    
    Attributes:
        order_id: Unique identifier
        allocation_id: Reference to allocation
        society_id: Society receiving delivery
        society_name: Name of society
        crop_type: Crop type
        quantity_kg: Quantity to deliver
        delivery_address: Delivery address
        delivery_date: Scheduled delivery date
        delivery_time_window: Time window for delivery
        status: Current order status
        created_at: Order creation timestamp
        updated_at: Last update timestamp
    """
    order_id: str
    allocation_id: str
    society_id: str
    society_name: str
    crop_type: str
    quantity_kg: Decimal
    delivery_address: str
    delivery_date: date
    delivery_time_window: str
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate delivery order"""
        if not isinstance(self.status, OrderStatus):
            self.status = OrderStatus(self.status)
        
        if self.quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity_kg}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "order_id": self.order_id,
            "order_type": OrderType.DELIVERY.value,
            "allocation_id": self.allocation_id,
            "society_id": self.society_id,
            "society_name": self.society_name,
            "crop_type": self.crop_type,
            "quantity_kg": str(self.quantity_kg),
            "delivery_address": self.delivery_address,
            "delivery_date": self.delivery_date.isoformat(),
            "delivery_time_window": self.delivery_time_window,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeliveryOrder":
        """Create from dictionary"""
        return cls(
            order_id=data["order_id"],
            allocation_id=data["allocation_id"],
            society_id=data["society_id"],
            society_name=data["society_name"],
            crop_type=data["crop_type"],
            quantity_kg=Decimal(data["quantity_kg"]),
            delivery_address=data["delivery_address"],
            delivery_date=date.fromisoformat(data["delivery_date"]),
            delivery_time_window=data["delivery_time_window"],
            status=OrderStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            notes=data.get("notes"),
        )


@dataclass
class PickupOrder:
    """
    Pickup order for processing partner allocation.
    
    Attributes:
        order_id: Unique identifier
        allocation_id: Reference to allocation
        partner_id: Processing partner ID
        partner_name: Name of processing partner
        crop_type: Crop type
        quantity_kg: Quantity to pickup
        pickup_location: Pickup location
        pickup_date: Scheduled pickup date
        pickup_schedule: Pickup schedule details
        status: Current order status
        created_at: Order creation timestamp
        updated_at: Last update timestamp
    """
    order_id: str
    allocation_id: str
    partner_id: str
    partner_name: str
    crop_type: str
    quantity_kg: Decimal
    pickup_location: str
    pickup_date: date
    pickup_schedule: str
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate pickup order"""
        if not isinstance(self.status, OrderStatus):
            self.status = OrderStatus(self.status)
        
        if self.quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity_kg}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "order_id": self.order_id,
            "order_type": OrderType.PICKUP.value,
            "allocation_id": self.allocation_id,
            "partner_id": self.partner_id,
            "partner_name": self.partner_name,
            "crop_type": self.crop_type,
            "quantity_kg": str(self.quantity_kg),
            "pickup_location": self.pickup_location,
            "pickup_date": self.pickup_date.isoformat(),
            "pickup_schedule": self.pickup_schedule,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PickupOrder":
        """Create from dictionary"""
        return cls(
            order_id=data["order_id"],
            allocation_id=data["allocation_id"],
            partner_id=data["partner_id"],
            partner_name=data["partner_name"],
            crop_type=data["crop_type"],
            quantity_kg=Decimal(data["quantity_kg"]),
            pickup_location=data["pickup_location"],
            pickup_date=date.fromisoformat(data["pickup_date"]),
            pickup_schedule=data["pickup_schedule"],
            status=OrderStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            notes=data.get("notes"),
        )


@dataclass
class DispatchOrder:
    """
    Dispatch order for mandi allocation.
    
    Attributes:
        order_id: Unique identifier
        allocation_id: Reference to allocation
        mandi_id: Mandi destination ID
        mandi_name: Name of mandi
        crop_type: Crop type
        quantity_kg: Quantity to dispatch
        destination: Destination address
        dispatch_date: Scheduled dispatch date
        transport_details: Transport details
        status: Current order status
        created_at: Order creation timestamp
        updated_at: Last update timestamp
    """
    order_id: str
    allocation_id: str
    mandi_id: str
    mandi_name: str
    crop_type: str
    quantity_kg: Decimal
    destination: str
    dispatch_date: date
    transport_details: str
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate dispatch order"""
        if not isinstance(self.status, OrderStatus):
            self.status = OrderStatus(self.status)
        
        if self.quantity_kg <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity_kg}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "order_id": self.order_id,
            "order_type": OrderType.DISPATCH.value,
            "allocation_id": self.allocation_id,
            "mandi_id": self.mandi_id,
            "mandi_name": self.mandi_name,
            "crop_type": self.crop_type,
            "quantity_kg": str(self.quantity_kg),
            "destination": self.destination,
            "dispatch_date": self.dispatch_date.isoformat(),
            "transport_details": self.transport_details,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DispatchOrder":
        """Create from dictionary"""
        return cls(
            order_id=data["order_id"],
            allocation_id=data["allocation_id"],
            mandi_id=data["mandi_id"],
            mandi_name=data["mandi_name"],
            crop_type=data["crop_type"],
            quantity_kg=Decimal(data["quantity_kg"]),
            destination=data["destination"],
            dispatch_date=date.fromisoformat(data["dispatch_date"]),
            transport_details=data["transport_details"],
            status=OrderStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            notes=data.get("notes"),
        )
