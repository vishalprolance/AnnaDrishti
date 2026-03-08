"""
Unit tests for Priority 1: Society allocation
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from collective.models import (
    Reservation,
    ReservationStatus,
    ChannelType,
    CollectiveInventory,
)
from collective.services import AllocationService


class TestPriority1SocietyAllocation:
    """Test Priority 1: Society allocation logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mocked repositories
        mock_inventory_repo = Mock()
        mock_allocation_repo = Mock()
        mock_processing_partner_repo = Mock()
        
        # Create service with mocked repositories
        self.allocation_service = AllocationService(
            inventory_repository=mock_inventory_repo,
            allocation_repository=mock_allocation_repo,
            processing_partner_repository=mock_processing_partner_repo,
        )
    
    def test_allocate_single_society_sufficient_inventory(self):
        """Test allocation to single society with sufficient inventory"""
        # Create reservation
        reservation = Reservation(
            reservation_id="res-1",
            society_id="soc-1",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("100"),
            reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        # Allocate
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("200"),
            reservations=[reservation],
        )
        
        # Verify allocation
        assert len(channel_allocations) == 1
        assert channel_allocations[0].channel_type == ChannelType.SOCIETY
        assert channel_allocations[0].channel_id == "soc-1"
        assert channel_allocations[0].quantity_kg == Decimal("100")
        assert channel_allocations[0].priority == 1
        
        # Verify remaining inventory
        assert remaining == Decimal("100")
        
        # Verify no warnings
        assert len(warnings) == 0
    
    def test_allocate_single_society_insufficient_inventory(self):
        """Test allocation to single society with insufficient inventory"""
        # Create reservation
        reservation = Reservation(
            reservation_id="res-1",
            society_id="soc-1",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("100"),
            reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        # Allocate with insufficient inventory
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("60"),
            reservations=[reservation],
        )
        
        # Verify partial allocation
        assert len(channel_allocations) == 1
        assert channel_allocations[0].quantity_kg == Decimal("60")
        
        # Verify no remaining inventory
        assert remaining == Decimal("0")
        
        # Verify unfulfilled warning
        assert len(warnings) == 1
        assert warnings[0]["reservation_id"] == "res-1"
        assert warnings[0]["allocated_qty"] == Decimal("60")
        assert warnings[0]["unfulfilled_qty"] == Decimal("40")
    
    def test_allocate_multiple_societies_timestamp_order(self):
        """Test allocation to multiple societies in timestamp order"""
        # Create reservations with different timestamps
        res1 = Reservation(
            reservation_id="res-1",
            society_id="soc-1",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),  # Earlier
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        res2 = Reservation(
            reservation_id="res-2",
            society_id="soc-2",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 12, 0, 0),  # Later
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        res3 = Reservation(
            reservation_id="res-3",
            society_id="soc-3",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 9, 0, 0),  # Earliest
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        # Allocate with reservations in random order
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("150"),
            reservations=[res1, res2, res3],  # Not in timestamp order
        )
        
        # Verify all allocated
        assert len(channel_allocations) == 3
        
        # Verify timestamp order: res3 (9:00), res1 (10:00), res2 (12:00)
        assert channel_allocations[0].channel_id == "soc-3"
        assert channel_allocations[1].channel_id == "soc-1"
        assert channel_allocations[2].channel_id == "soc-2"
        
        # Verify quantities
        assert channel_allocations[0].quantity_kg == Decimal("50")
        assert channel_allocations[1].quantity_kg == Decimal("50")
        assert channel_allocations[2].quantity_kg == Decimal("50")
        
        # Verify no remaining inventory
        assert remaining == Decimal("0")
        
        # Verify no warnings
        assert len(warnings) == 0
    
    def test_allocate_multiple_societies_partial_fulfillment(self):
        """Test allocation to multiple societies with partial fulfillment"""
        # Create reservations
        res1 = Reservation(
            reservation_id="res-1",
            society_id="soc-1",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 9, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        res2 = Reservation(
            reservation_id="res-2",
            society_id="soc-2",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        res3 = Reservation(
            reservation_id="res-3",
            society_id="soc-3",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("50"),
            reservation_timestamp=datetime(2024, 1, 1, 11, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        # Allocate with insufficient inventory (only 120 kg available)
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("120"),
            reservations=[res1, res2, res3],
        )
        
        # Verify allocations
        assert len(channel_allocations) == 3
        
        # First two societies get full allocation
        assert channel_allocations[0].channel_id == "soc-1"
        assert channel_allocations[0].quantity_kg == Decimal("50")
        
        assert channel_allocations[1].channel_id == "soc-2"
        assert channel_allocations[1].quantity_kg == Decimal("50")
        
        # Third society gets partial allocation
        assert channel_allocations[2].channel_id == "soc-3"
        assert channel_allocations[2].quantity_kg == Decimal("20")
        
        # Verify no remaining inventory
        assert remaining == Decimal("0")
        
        # Verify one unfulfilled warning for third society
        assert len(warnings) == 1
        assert warnings[0]["reservation_id"] == "res-3"
        assert warnings[0]["allocated_qty"] == Decimal("20")
        assert warnings[0]["unfulfilled_qty"] == Decimal("30")
    
    def test_allocate_no_reservations(self):
        """Test allocation with no reservations"""
        # Allocate with no reservations
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("100"),
            reservations=[],
        )
        
        # Verify no allocations
        assert len(channel_allocations) == 0
        
        # Verify all inventory remains
        assert remaining == Decimal("100")
        
        # Verify no warnings
        assert len(warnings) == 0
    
    def test_allocate_zero_inventory(self):
        """Test allocation with zero inventory"""
        # Create reservation
        reservation = Reservation(
            reservation_id="res-1",
            society_id="soc-1",
            crop_type="tomato",
            reserved_quantity_kg=Decimal("100"),
            reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
            delivery_date=date(2024, 1, 5),
            status=ReservationStatus.CONFIRMED,
        )
        
        # Allocate with zero inventory
        channel_allocations, remaining, warnings = self.allocation_service.allocate_priority_1_societies(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
            available_quantity=Decimal("0"),
            reservations=[reservation],
        )
        
        # Verify no allocation created (zero quantity means no allocation)
        assert len(channel_allocations) == 0
        
        # Verify no remaining inventory
        assert remaining == Decimal("0")
        
        # Verify unfulfilled warning
        assert len(warnings) == 1
        assert warnings[0]["allocated_qty"] == Decimal("0")
        assert warnings[0]["unfulfilled_qty"] == Decimal("100")
    
    def test_get_active_reservations_filters_by_crop_and_status(self):
        """Test that get_active_reservations filters correctly"""
        # Mock repository to return mixed reservations
        mock_reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type="tomato",
                reserved_quantity_kg=Decimal("50"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=date(2024, 1, 5),
                status=ReservationStatus.CONFIRMED,
            ),
            Reservation(
                reservation_id="res-2",
                society_id="soc-2",
                crop_type="potato",  # Different crop
                reserved_quantity_kg=Decimal("50"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=date(2024, 1, 5),
                status=ReservationStatus.CONFIRMED,
            ),
            Reservation(
                reservation_id="res-3",
                society_id="soc-3",
                crop_type="tomato",
                reserved_quantity_kg=Decimal("50"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=date(2024, 1, 5),
                status=ReservationStatus.FULFILLED,  # Already fulfilled
            ),
            Reservation(
                reservation_id="res-4",
                society_id="soc-4",
                crop_type="tomato",
                reserved_quantity_kg=Decimal("50"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=date(2024, 1, 5),
                status=ReservationStatus.PREDICTED,  # Should be included
            ),
        ]
        
        self.allocation_service.inventory_repository.get_reservations_by_date.return_value = mock_reservations
        
        # Get active reservations for tomato
        active = self.allocation_service.get_active_reservations(
            fpo_id="fpo-1",
            crop_type="tomato",
            allocation_date=date(2024, 1, 5),
        )
        
        # Should only include res-1 and res-4 (tomato + active status)
        assert len(active) == 2
        assert active[0].reservation_id == "res-1"
        assert active[1].reservation_id == "res-4"
    
    def test_flag_unfulfilled_reservations_logs_warnings(self, capsys):
        """Test that unfulfilled reservations are flagged"""
        warnings = [
            {
                "reservation_id": "res-1",
                "society_id": "soc-1",
                "crop_type": "tomato",
                "requested_qty": Decimal("100"),
                "allocated_qty": Decimal("60"),
                "unfulfilled_qty": Decimal("40"),
                "message": "Insufficient inventory",
            }
        ]
        
        # Flag warnings
        self.allocation_service.flag_unfulfilled_reservations(warnings)
        
        # Verify output
        captured = capsys.readouterr()
        assert "UNFULFILLED RESERVATIONS ALERT" in captured.out
        assert "res-1" in captured.out
        assert "soc-1" in captured.out
        assert "40" in captured.out
    
    def test_flag_unfulfilled_reservations_empty_list(self, capsys):
        """Test that empty warnings list produces no output"""
        # Flag empty warnings
        self.allocation_service.flag_unfulfilled_reservations([])
        
        # Verify no output
        captured = capsys.readouterr()
        assert captured.out == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
