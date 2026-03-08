"""
Unit tests for order generation and fulfillment tracking.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from collective.models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    DeliveryOrder,
    PickupOrder,
    DispatchOrder,
    OrderStatus,
    SocietyProfile,
    ProcessingPartner,
    DeliveryFrequency,
    CropPreference,
    CollectiveInventory,
)
from collective.services import OrderService


class TestOrderGeneration:
    """Test order generation for all channel types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mocked repositories
        self.mock_order_repo = Mock()
        self.mock_allocation_repo = Mock()
        self.mock_society_repo = Mock()
        self.mock_processing_repo = Mock()
        self.mock_inventory_repo = Mock()
        
        # Create service with mocked repositories
        self.service = OrderService(
            order_repo=self.mock_order_repo,
            allocation_repo=self.mock_allocation_repo,
            society_repo=self.mock_society_repo,
            processing_repo=self.mock_processing_repo,
            inventory_repo=self.mock_inventory_repo,
        )
        
        self.fpo_id = "FPO001"
        self.crop_type = "tomato"
        self.allocation_date = date(2024, 1, 15)
    
    def test_generate_delivery_orders(self):
        """
        Test delivery order generation for society allocations.
        
        Requirements: 7.1
        """
        # Create allocation with society channel allocations
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Green Valley Society",
                    quantity_kg=Decimal("150"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("7500"),
                    priority=1,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC002",
                    channel_name="Sunrise Apartments",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("5000"),
                    priority=1,
                ),
            ],
            total_quantity_kg=Decimal("250"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        # Create society profiles
        society1 = SocietyProfile(
            society_id="SOC001",
            society_name="Green Valley Society",
            location="Mumbai",
            contact_details={"phone": "1234567890"},
            delivery_address="123 Green Valley, Mumbai",
            delivery_frequency=DeliveryFrequency.TWICE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="8:00 AM - 10:00 AM",
            crop_preferences=[],
            created_at=datetime.now(),
        )
        
        society2 = SocietyProfile(
            society_id="SOC002",
            society_name="Sunrise Apartments",
            location="Pune",
            contact_details={"phone": "0987654321"},
            delivery_address="456 Sunrise Road, Pune",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Tuesday",
            preferred_time_window="9:00 AM - 11:00 AM",
            crop_preferences=[],
            created_at=datetime.now(),
        )
        
        # Mock repository methods
        self.mock_society_repo.get_society.side_effect = lambda sid: {
            "SOC001": society1,
            "SOC002": society2,
        }.get(sid)
        
        # Generate delivery orders
        orders = self.service.generate_delivery_orders(allocation)
        
        # Verify orders were created
        assert len(orders) == 2
        assert all(isinstance(order, DeliveryOrder) for order in orders)
        
        # Verify first order
        order1 = orders[0]
        assert order1.allocation_id == "ALLOC001"
        assert order1.society_id == "SOC001"
        assert order1.society_name == "Green Valley Society"
        assert order1.crop_type == self.crop_type
        assert order1.quantity_kg == Decimal("150")
        assert order1.delivery_address == "123 Green Valley, Mumbai"
        assert order1.delivery_date == self.allocation_date + timedelta(days=1)
        assert order1.delivery_time_window == "8:00 AM - 10:00 AM"
        assert order1.status == OrderStatus.PENDING
        
        # Verify second order
        order2 = orders[1]
        assert order2.society_id == "SOC002"
        assert order2.quantity_kg == Decimal("100")
        assert order2.delivery_time_window == "9:00 AM - 11:00 AM"
        
        # Verify repository calls
        assert self.mock_order_repo.create_delivery_order.call_count == 2
    
    def test_generate_delivery_orders_society_not_found(self):
        """
        Test delivery order generation when society doesn't exist.
        
        Requirements: 7.1
        """
        # Create allocation with society channel allocation
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC999",
                    channel_name="Non-existent Society",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("5000"),
                    priority=1,
                ),
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        # Mock repository to return None
        self.mock_society_repo.get_society.return_value = None
        
        # Expect error
        with pytest.raises(ValueError, match="Society not found"):
            self.service.generate_delivery_orders(allocation)
    
    def test_generate_pickup_orders(self):
        """
        Test pickup order generation for processing partner allocations.
        
        Requirements: 7.2
        """
        # Create allocation with processing channel allocations
        allocation = Allocation(
            allocation_id="ALLOC002",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PP001",
                    channel_name="Premium Processors",
                    quantity_kg=Decimal("200"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("9000"),
                    priority=2,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PP002",
                    channel_name="Standard Processors",
                    quantity_kg=Decimal("150"),
                    price_per_kg=Decimal("40"),
                    revenue=Decimal("6000"),
                    priority=2,
                ),
            ],
            total_quantity_kg=Decimal("350"),
            blended_realization_per_kg=Decimal("42.86"),
            status=AllocationStatus.PENDING,
        )
        
        # Create processing partners
        partner1 = ProcessingPartner(
            partner_id="PP001",
            partner_name="Premium Processors",
            contact_details={"phone": "1111111111"},
            facility_location="Mumbai Industrial Area",
            rates_by_crop={self.crop_type: Decimal("45")},
            capacity_by_crop={self.crop_type: Decimal("200")},
            quality_requirements={self.crop_type: "Grade A"},
            pickup_schedule="Daily 6:00 AM - 8:00 AM",
            created_at=datetime.now(),
        )
        
        partner2 = ProcessingPartner(
            partner_id="PP002",
            partner_name="Standard Processors",
            contact_details={"phone": "2222222222"},
            facility_location="Pune Industrial Zone",
            rates_by_crop={self.crop_type: Decimal("40")},
            capacity_by_crop={self.crop_type: Decimal("150")},
            quality_requirements={self.crop_type: "Grade B"},
            pickup_schedule="Weekdays 7:00 AM - 9:00 AM",
            created_at=datetime.now(),
        )
        
        # Mock repository methods
        self.mock_processing_repo.get_partner.side_effect = lambda pid: {
            "PP001": partner1,
            "PP002": partner2,
        }.get(pid)
        
        # Generate pickup orders
        orders = self.service.generate_pickup_orders(allocation)
        
        # Verify orders were created
        assert len(orders) == 2
        assert all(isinstance(order, PickupOrder) for order in orders)
        
        # Verify first order
        order1 = orders[0]
        assert order1.allocation_id == "ALLOC002"
        assert order1.partner_id == "PP001"
        assert order1.partner_name == "Premium Processors"
        assert order1.crop_type == self.crop_type
        assert order1.quantity_kg == Decimal("200")
        assert order1.pickup_location == "Mumbai Industrial Area"
        assert order1.pickup_date == self.allocation_date + timedelta(days=1)
        assert order1.pickup_schedule == "Daily 6:00 AM - 8:00 AM"
        assert order1.status == OrderStatus.PENDING
        
        # Verify second order
        order2 = orders[1]
        assert order2.partner_id == "PP002"
        assert order2.quantity_kg == Decimal("150")
        assert order2.pickup_schedule == "Weekdays 7:00 AM - 9:00 AM"
        
        # Verify repository calls
        assert self.mock_order_repo.create_pickup_order.call_count == 2
    
    def test_generate_pickup_orders_partner_not_found(self):
        """
        Test pickup order generation when partner doesn't exist.
        
        Requirements: 7.2
        """
        # Create allocation with processing channel allocation
        allocation = Allocation(
            allocation_id="ALLOC002",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PP999",
                    channel_name="Non-existent Partner",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("4500"),
                    priority=2,
                ),
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("45"),
            status=AllocationStatus.PENDING,
        )
        
        # Mock repository to return None
        self.mock_processing_repo.get_partner.return_value = None
        
        # Expect error
        with pytest.raises(ValueError, match="Processing partner not found"):
            self.service.generate_pickup_orders(allocation)
    
    def test_generate_dispatch_orders(self):
        """
        Test dispatch order generation for mandi allocations.
        
        Requirements: 7.3
        """
        # Create allocation with mandi channel allocation
        allocation = Allocation(
            allocation_id="ALLOC003",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.MANDI,
                    channel_id="MANDI001",
                    channel_name="Vashi APMC",
                    quantity_kg=Decimal("300"),
                    price_per_kg=Decimal("35"),
                    revenue=Decimal("10500"),
                    priority=3,
                ),
            ],
            total_quantity_kg=Decimal("300"),
            blended_realization_per_kg=Decimal("35"),
            status=AllocationStatus.PENDING,
        )
        
        # Generate dispatch orders
        orders = self.service.generate_dispatch_orders(allocation)
        
        # Verify orders were created
        assert len(orders) == 1
        assert isinstance(orders[0], DispatchOrder)
        
        # Verify order details
        order = orders[0]
        assert order.allocation_id == "ALLOC003"
        assert order.mandi_id == "MANDI001"
        assert order.mandi_name == "Vashi APMC"
        assert order.crop_type == self.crop_type
        assert order.quantity_kg == Decimal("300")
        assert order.destination == "Vashi APMC"
        assert order.dispatch_date == self.allocation_date + timedelta(days=1)
        assert order.transport_details == "Standard transport"
        assert order.status == OrderStatus.PENDING
        
        # Verify repository calls
        assert self.mock_order_repo.create_dispatch_order.call_count == 1
    
    def test_generate_all_order_types(self):
        """
        Test generating orders for allocation with all three channel types.
        
        Requirements: 7.1, 7.2, 7.3
        """
        # Create allocation with all channel types
        allocation = Allocation(
            allocation_id="ALLOC004",
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("5000"),
                    priority=1,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PP001",
                    channel_name="Processor 1",
                    quantity_kg=Decimal("200"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("9000"),
                    priority=2,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.MANDI,
                    channel_id="MANDI001",
                    channel_name="Mandi 1",
                    quantity_kg=Decimal("150"),
                    price_per_kg=Decimal("35"),
                    revenue=Decimal("5250"),
                    priority=3,
                ),
            ],
            total_quantity_kg=Decimal("450"),
            blended_realization_per_kg=Decimal("42.78"),
            status=AllocationStatus.PENDING,
        )
        
        # Mock society
        society = SocietyProfile(
            society_id="SOC001",
            society_name="Society 1",
            location="Mumbai",
            contact_details={},
            delivery_address="Address 1",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="8:00 AM - 10:00 AM",
            crop_preferences=[],
            created_at=datetime.now(),
        )
        
        # Mock partner
        partner = ProcessingPartner(
            partner_id="PP001",
            partner_name="Processor 1",
            contact_details={},
            facility_location="Location 1",
            rates_by_crop={self.crop_type: Decimal("45")},
            capacity_by_crop={self.crop_type: Decimal("200")},
            quality_requirements={},
            pickup_schedule="Daily",
            created_at=datetime.now(),
        )
        
        self.mock_society_repo.get_society.return_value = society
        self.mock_processing_repo.get_partner.return_value = partner
        
        # Generate all order types
        delivery_orders = self.service.generate_delivery_orders(allocation)
        pickup_orders = self.service.generate_pickup_orders(allocation)
        dispatch_orders = self.service.generate_dispatch_orders(allocation)
        
        # Verify counts
        assert len(delivery_orders) == 1
        assert len(pickup_orders) == 1
        assert len(dispatch_orders) == 1
        
        # Verify all orders reference the same allocation
        assert delivery_orders[0].allocation_id == "ALLOC004"
        assert pickup_orders[0].allocation_id == "ALLOC004"
        assert dispatch_orders[0].allocation_id == "ALLOC004"


class TestFulfillmentTracking:
    """Test fulfillment status tracking"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_order_repo = Mock()
        self.mock_allocation_repo = Mock()
        self.mock_inventory_repo = Mock()
        self.mock_society_repo = Mock()
        self.mock_processing_repo = Mock()
        
        self.service = OrderService(
            order_repo=self.mock_order_repo,
            allocation_repo=self.mock_allocation_repo,
            inventory_repo=self.mock_inventory_repo,
            society_repo=self.mock_society_repo,
            processing_repo=self.mock_processing_repo,
        )
    
    def test_update_fulfillment_status_valid_transition(self):
        """
        Test valid status transitions.
        
        Requirements: 7.4
        """
        # Create delivery order
        order = DeliveryOrder(
            order_id="DEL001",
            allocation_id="ALLOC001",
            society_id="SOC001",
            society_name="Society 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            delivery_address="Address 1",
            delivery_date=date(2024, 1, 16),
            delivery_time_window="8:00 AM - 10:00 AM",
            status=OrderStatus.PENDING,
        )
        
        self.mock_order_repo.get_delivery_order.return_value = order
        
        # Test pending → in_transit
        self.service.update_fulfillment_status("DEL001", "delivery", OrderStatus.IN_TRANSIT)
        assert self.mock_order_repo.update_delivery_order.called
    
    def test_update_fulfillment_status_invalid_transition(self):
        """
        Test invalid status transitions are rejected.
        
        Requirements: 7.4
        """
        # Create order in DELIVERED status
        order = DeliveryOrder(
            order_id="DEL001",
            allocation_id="ALLOC001",
            society_id="SOC001",
            society_name="Society 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            delivery_address="Address 1",
            delivery_date=date(2024, 1, 16),
            delivery_time_window="8:00 AM - 10:00 AM",
            status=OrderStatus.DELIVERED,
        )
        
        self.mock_order_repo.get_delivery_order.return_value = order
        
        # Try invalid transition: delivered → in_transit
        with pytest.raises(ValueError, match="Invalid status transition"):
            self.service.update_fulfillment_status("DEL001", "delivery", OrderStatus.IN_TRANSIT)
    
    def test_update_fulfillment_status_order_not_found(self):
        """
        Test error when order doesn't exist.
        
        Requirements: 7.4
        """
        self.mock_order_repo.get_delivery_order.return_value = None
        
        with pytest.raises(ValueError, match="Order not found"):
            self.service.update_fulfillment_status("DEL999", "delivery", OrderStatus.IN_TRANSIT)
    
    def test_update_fulfillment_status_completed_updates_allocation(self):
        """
        Test that completing an order updates allocation fulfillment.
        
        Requirements: 7.5, 7.6
        """
        # Create order
        order = DeliveryOrder(
            order_id="DEL001",
            allocation_id="ALLOC001",
            society_id="SOC001",
            society_name="Society 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            delivery_address="Address 1",
            delivery_date=date(2024, 1, 16),
            delivery_time_window="8:00 AM - 10:00 AM",
            status=OrderStatus.DELIVERED,
        )
        
        # Create allocation
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("5000"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.EXECUTED,
        )
        
        # Create inventory
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("900"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("100"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        self.mock_order_repo.get_delivery_order.return_value = order
        self.mock_allocation_repo.get_allocation.return_value = allocation
        self.mock_inventory_repo.get_inventory.return_value = inventory
        
        # Complete the order
        self.service.update_fulfillment_status("DEL001", "delivery", OrderStatus.COMPLETED)
        
        # Verify allocation was updated
        assert self.mock_allocation_repo.update_allocation.called
        updated_allocation = self.mock_allocation_repo.update_allocation.call_args[0][0]
        assert updated_allocation.channel_allocations[0].fulfillment_status == FulfillmentStatus.COMPLETED
        
        # Verify inventory was updated (allocated quantity reduced)
        assert self.mock_inventory_repo.save_inventory.called
        updated_inventory = self.mock_inventory_repo.save_inventory.call_args[0][0]
        assert updated_inventory.allocated_quantity_kg == Decimal("0")
    
    def test_status_transition_sequence(self):
        """
        Test complete status transition sequence: pending → in_transit → delivered → completed.
        
        Requirements: 7.4
        """
        # Create order
        order = PickupOrder(
            order_id="PKP001",
            allocation_id="ALLOC001",
            partner_id="PP001",
            partner_name="Partner 1",
            crop_type="tomato",
            quantity_kg=Decimal("200"),
            pickup_location="Location 1",
            pickup_date=date(2024, 1, 16),
            pickup_schedule="Daily",
            status=OrderStatus.PENDING,
        )
        
        self.mock_order_repo.get_pickup_order.return_value = order
        
        # Transition 1: pending → in_transit
        self.service.update_fulfillment_status("PKP001", "pickup", OrderStatus.IN_TRANSIT)
        order.status = OrderStatus.IN_TRANSIT
        
        # Transition 2: in_transit → delivered
        self.service.update_fulfillment_status("PKP001", "pickup", OrderStatus.DELIVERED)
        order.status = OrderStatus.DELIVERED
        
        # Transition 3: delivered → completed
        allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date(2024, 1, 15),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PP001",
                    channel_name="Partner 1",
                    quantity_kg=Decimal("200"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("9000"),
                    priority=2,
                ),
            ],
            total_quantity_kg=Decimal("200"),
            blended_realization_per_kg=Decimal("45"),
        )
        
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("200"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        self.mock_allocation_repo.get_allocation.return_value = allocation
        self.mock_inventory_repo.get_inventory.return_value = inventory
        
        self.service.update_fulfillment_status("PKP001", "pickup", OrderStatus.COMPLETED)
        
        # Verify all transitions succeeded
        assert self.mock_order_repo.update_pickup_order.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
