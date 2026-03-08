"""
Order execution service for allocation tracking
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional
from decimal import Decimal

from ..models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    DeliveryOrder,
    PickupOrder,
    DispatchOrder,
    OrderStatus,
    FulfillmentStatus,
)
from ..db.order_repository import OrderRepository
from ..db.repositories import AllocationRepository, SocietyRepository, ProcessingPartnerRepository, InventoryRepository


class OrderService:
    """Service for order generation and fulfillment tracking"""
    
    def __init__(
        self,
        order_repo: Optional[OrderRepository] = None,
        allocation_repo: Optional[AllocationRepository] = None,
        society_repo: Optional[SocietyRepository] = None,
        processing_repo: Optional[ProcessingPartnerRepository] = None,
        inventory_repo: Optional[InventoryRepository] = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.allocation_repo = allocation_repo or AllocationRepository()
        self.society_repo = society_repo or SocietyRepository()
        self.processing_repo = processing_repo or ProcessingPartnerRepository()
        self.inventory_repo = inventory_repo or InventoryRepository()
    
    def generate_delivery_orders(self, allocation: Allocation) -> List[DeliveryOrder]:
        """
        Generate delivery orders for society allocations.
        
        Args:
            allocation: Allocation with channel allocations
        
        Returns:
            List of delivery orders created
        
        Requirements: 7.1
        """
        delivery_orders = []
        
        # Filter society allocations
        society_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.SOCIETY
        ]
        
        for ca in society_allocations:
            # Get society details
            society = self.society_repo.get_society(ca.channel_id)
            if not society:
                raise ValueError(f"Society not found: {ca.channel_id}")
            
            # Create delivery order
            order = DeliveryOrder(
                order_id=f"DEL-{uuid.uuid4().hex[:12].upper()}",
                allocation_id=allocation.allocation_id,
                society_id=society.society_id,
                society_name=society.society_name,
                crop_type=allocation.crop_type,
                quantity_kg=ca.quantity_kg,
                delivery_address=society.delivery_address,
                delivery_date=allocation.allocation_date + timedelta(days=1),  # Next day delivery
                delivery_time_window=society.preferred_time_window,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
            # Save to database
            self.order_repo.create_delivery_order(order)
            delivery_orders.append(order)
        
        return delivery_orders
    
    def generate_pickup_orders(self, allocation: Allocation) -> List[PickupOrder]:
        """
        Generate pickup orders for processing partner allocations.
        
        Args:
            allocation: Allocation with channel allocations
        
        Returns:
            List of pickup orders created
        
        Requirements: 7.2
        """
        pickup_orders = []
        
        # Filter processing allocations
        processing_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        for ca in processing_allocations:
            # Get partner details
            partner = self.processing_repo.get_partner(ca.channel_id)
            if not partner:
                raise ValueError(f"Processing partner not found: {ca.channel_id}")
            
            # Create pickup order
            order = PickupOrder(
                order_id=f"PKP-{uuid.uuid4().hex[:12].upper()}",
                allocation_id=allocation.allocation_id,
                partner_id=partner.partner_id,
                partner_name=partner.partner_name,
                crop_type=allocation.crop_type,
                quantity_kg=ca.quantity_kg,
                pickup_location=partner.facility_location,
                pickup_date=allocation.allocation_date + timedelta(days=1),  # Next day pickup
                pickup_schedule=partner.pickup_schedule,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
            # Save to database
            self.order_repo.create_pickup_order(order)
            pickup_orders.append(order)
        
        return pickup_orders
    
    def generate_dispatch_orders(self, allocation: Allocation) -> List[DispatchOrder]:
        """
        Generate dispatch orders for mandi allocations.
        
        Args:
            allocation: Allocation with channel allocations
        
        Returns:
            List of dispatch orders created
        
        Requirements: 7.3
        """
        dispatch_orders = []
        
        # Filter mandi allocations
        mandi_allocations = [
            ca for ca in allocation.channel_allocations
            if ca.channel_type == ChannelType.MANDI
        ]
        
        for ca in mandi_allocations:
            # Create dispatch order
            order = DispatchOrder(
                order_id=f"DSP-{uuid.uuid4().hex[:12].upper()}",
                allocation_id=allocation.allocation_id,
                mandi_id=ca.channel_id,
                mandi_name=ca.channel_name,
                crop_type=allocation.crop_type,
                quantity_kg=ca.quantity_kg,
                destination=ca.channel_name,  # Mandi name as destination
                dispatch_date=allocation.allocation_date + timedelta(days=1),  # Next day dispatch
                transport_details="Standard transport",  # Default transport
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
            # Save to database
            self.order_repo.create_dispatch_order(order)
            dispatch_orders.append(order)
        
        return dispatch_orders
    
    def update_fulfillment_status(
        self,
        order_id: str,
        order_type: str,
        new_status: OrderStatus,
    ) -> None:
        """
        Update fulfillment status for an order.
        
        Tracks status transitions: pending → in_transit → delivered → completed
        Updates inventory on fulfillment and prevents double-allocation.
        
        Args:
            order_id: Order ID
            order_type: Type of order (delivery, pickup, dispatch)
            new_status: New status to set
        
        Requirements: 7.4, 7.5, 7.6
        """
        # Validate status transition
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
            OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: [],
        }
        
        # Get order based on type
        if order_type == "delivery":
            order = self.order_repo.get_delivery_order(order_id)
        elif order_type == "pickup":
            order = self.order_repo.get_pickup_order(order_id)
        elif order_type == "dispatch":
            order = self.order_repo.get_dispatch_order(order_id)
        else:
            raise ValueError(f"Invalid order type: {order_type}")
        
        if not order:
            raise ValueError(f"Order not found: {order_id}")
        
        # Validate transition
        if new_status not in valid_transitions.get(order.status, []):
            raise ValueError(
                f"Invalid status transition: {order.status.value} → {new_status.value}"
            )
        
        # Update order status
        old_status = order.status
        order.status = new_status
        
        if order_type == "delivery":
            self.order_repo.update_delivery_order(order)
        elif order_type == "pickup":
            self.order_repo.update_pickup_order(order)
        elif order_type == "dispatch":
            self.order_repo.update_dispatch_order(order)
        
        # Update allocation fulfillment status when order is completed
        if new_status == OrderStatus.COMPLETED:
            self._update_allocation_fulfillment(order)
    
    def _update_allocation_fulfillment(self, order) -> None:
        """
        Update allocation fulfillment status when order is completed.
        
        Updates inventory to reflect dispatched quantity and prevents double-allocation.
        """
        # Get allocation
        allocation = self.allocation_repo.get_allocation(order.allocation_id)
        if not allocation:
            raise ValueError(f"Allocation not found: {order.allocation_id}")
        
        # Find matching channel allocation
        channel_id = None
        if hasattr(order, 'society_id'):
            channel_id = order.society_id
        elif hasattr(order, 'partner_id'):
            channel_id = order.partner_id
        elif hasattr(order, 'mandi_id'):
            channel_id = order.mandi_id
        
        for ca in allocation.channel_allocations:
            if ca.channel_id == channel_id:
                # Update fulfillment status
                ca.fulfillment_status = FulfillmentStatus.COMPLETED
                break
        
        # Check if all channel allocations are completed
        all_completed = all(
            ca.fulfillment_status == FulfillmentStatus.COMPLETED
            for ca in allocation.channel_allocations
        )
        
        # Update allocation status if all completed
        if all_completed:
            from ..models.allocation import AllocationStatus
            allocation.status = AllocationStatus.COMPLETED
        
        # Save updated allocation
        self.allocation_repo.update_allocation(allocation)
        
        # Update inventory to mark quantity as dispatched
        # This prevents double-allocation by reducing allocated_quantity
        inventory = self.inventory_repo.get_inventory(allocation.fpo_id, allocation.crop_type)
        if inventory:
            # Reduce allocated quantity as it's now fulfilled
            inventory.allocated_quantity_kg -= order.quantity_kg
            self.inventory_repo.save_inventory(inventory)
