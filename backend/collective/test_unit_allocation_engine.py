"""
Unit tests for the complete allocation engine (all three priorities).

**Validates: Requirements 4.7**
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
    FarmerContribution,
    QualityGrade,
    ProcessingPartner,
    AllocationStatus,
)
from collective.services import AllocationService


class TestAllocationEngine:
    """Test the complete allocation engine with all three priorities"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mocked repositories
        self.mock_inventory_repo = Mock()
        self.mock_allocation_repo = Mock()
        self.mock_processing_partner_repo = Mock()
        
        # Create service with mocked repositories
        self.service = AllocationService(
            inventory_repository=self.mock_inventory_repo,
            allocation_repository=self.mock_allocation_repo,
            processing_partner_repository=self.mock_processing_partner_repo,
        )
        
        self.fpo_id = "FPO001"
        self.crop_type = "tomato"
        self.allocation_date = date(2024, 1, 15)
    
    def test_allocate_with_sufficient_inventory_all_priorities(self):
        """
        Test allocation with sufficient inventory for all three priorities.
        
        Scenario:
        - 1000 kg available
        - 300 kg reserved by societies (Priority 1)
        - 400 kg capacity in processing partners (Priority 2)
        - Remaining 300 kg goes to mandi (Priority 3)
        """
        # Create inventory with contributions that match total quantity
        contributions = [
            FarmerContribution(
                contribution_id="contrib-1",
                farmer_id="farmer-1",
                farmer_name="Farmer One",
                crop_type=self.crop_type,
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
            FarmerContribution(
                contribution_id="contrib-2",
                farmer_id="farmer-2",
                farmer_name="Farmer Two",
                crop_type=self.crop_type,
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("1000"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # Create reservations (Priority 1)
        reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("150"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
            Reservation(
                reservation_id="res-2",
                society_id="soc-2",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("150"),
                reservation_timestamp=datetime(2024, 1, 1, 11, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
        ]
        
        # Create processing partners (Priority 2)
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="High Rate Processor",
                contact_details={"phone": "1234567890"},
                facility_location="Mumbai",
                rates_by_crop={self.crop_type: Decimal("45.0")},
                capacity_by_crop={self.crop_type: Decimal("250.0")},
                quality_requirements={self.crop_type: "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
            ProcessingPartner(
                partner_id="PP002",
                partner_name="Low Rate Processor",
                contact_details={"phone": "0987654321"},
                facility_location="Pune",
                rates_by_crop={self.crop_type: Decimal("40.0")},
                capacity_by_crop={self.crop_type: Decimal("150.0")},
                quality_requirements={self.crop_type: "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = partners
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Verify allocation structure
        assert allocation.fpo_id == self.fpo_id
        assert allocation.crop_type == self.crop_type
        assert allocation.status == AllocationStatus.PENDING
        
        # Verify channel allocations
        assert len(allocation.channel_allocations) == 5  # 2 societies + 2 processing + 1 mandi
        
        # Verify Priority 1: Societies (300 kg total)
        society_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.SOCIETY]
        assert len(society_allocations) == 2
        assert sum(ca.quantity_kg for ca in society_allocations) == Decimal("300")
        
        # Verify Priority 2: Processing (400 kg total)
        processing_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.PROCESSING]
        assert len(processing_allocations) == 2
        assert sum(ca.quantity_kg for ca in processing_allocations) == Decimal("400")
        
        # Verify Priority 3: Mandi (300 kg remaining)
        mandi_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.MANDI]
        assert len(mandi_allocations) == 1
        assert mandi_allocations[0].quantity_kg == Decimal("300")
        
        # Verify total allocation
        assert allocation.total_quantity_kg == Decimal("1000")
        
        # Verify inventory was updated
        assert self.mock_inventory_repo.save_inventory.called
        assert self.mock_allocation_repo.create_allocation.called
    
    def test_allocate_with_insufficient_inventory(self):
        """
        Test allocation with insufficient inventory.
        
        Scenario:
        - 200 kg available
        - 300 kg reserved by societies (Priority 1)
        - Societies get partial fulfillment, no inventory for Priority 2 or 3
        """
        # Create inventory with limited quantity and matching contributions
        contributions = [
            FarmerContribution(
                contribution_id="contrib-1",
                farmer_id="farmer-1",
                farmer_name="Farmer One",
                crop_type=self.crop_type,
                quantity_kg=Decimal("200"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("200"),
            available_quantity_kg=Decimal("200"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # Create reservations exceeding available inventory
        reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("150"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
            Reservation(
                reservation_id="res-2",
                society_id="soc-2",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("150"),
                reservation_timestamp=datetime(2024, 1, 1, 11, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
        ]
        
        # Create processing partners (won't be used due to insufficient inventory)
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Processor",
                contact_details={"phone": "1234567890"},
                facility_location="Mumbai",
                rates_by_crop={self.crop_type: Decimal("45.0")},
                capacity_by_crop={self.crop_type: Decimal("500.0")},
                quality_requirements={self.crop_type: "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = partners
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Verify only Priority 1 allocations exist
        assert len(allocation.channel_allocations) == 2
        
        # All allocations should be societies
        for ca in allocation.channel_allocations:
            assert ca.channel_type == ChannelType.SOCIETY
        
        # First society gets full allocation (150 kg)
        assert allocation.channel_allocations[0].quantity_kg == Decimal("150")
        
        # Second society gets partial allocation (50 kg)
        assert allocation.channel_allocations[1].quantity_kg == Decimal("50")
        
        # Total allocation equals available inventory
        assert allocation.total_quantity_kg == Decimal("200")
    
    def test_allocate_with_no_reservations(self):
        """
        Test allocation with no society reservations.
        
        Scenario:
        - 500 kg available
        - No reservations (Priority 1 skipped)
        - 300 kg to processing partners (Priority 2)
        - 200 kg to mandi (Priority 3)
        """
        # Create inventory with matching contributions
        contributions = [
            FarmerContribution(
                contribution_id="contrib-1",
                farmer_id="farmer-1",
                farmer_name="Farmer One",
                crop_type=self.crop_type,
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("500"),
            available_quantity_kg=Decimal("500"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # No reservations
        reservations = []
        
        # Create processing partners
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Processor",
                contact_details={"phone": "1234567890"},
                facility_location="Mumbai",
                rates_by_crop={self.crop_type: Decimal("45.0")},
                capacity_by_crop={self.crop_type: Decimal("300.0")},
                quality_requirements={self.crop_type: "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = partners
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Verify allocations
        assert len(allocation.channel_allocations) == 2  # 1 processing + 1 mandi
        
        # No society allocations
        society_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.SOCIETY]
        assert len(society_allocations) == 0
        
        # Processing allocation (300 kg)
        processing_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.PROCESSING]
        assert len(processing_allocations) == 1
        assert processing_allocations[0].quantity_kg == Decimal("300")
        
        # Mandi allocation (200 kg)
        mandi_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.MANDI]
        assert len(mandi_allocations) == 1
        assert mandi_allocations[0].quantity_kg == Decimal("200")
        
        # Total allocation
        assert allocation.total_quantity_kg == Decimal("500")
    
    def test_allocate_with_no_processing_partners(self):
        """
        Test allocation with no processing partners.
        
        Scenario:
        - 500 kg available
        - 200 kg to societies (Priority 1)
        - No processing partners (Priority 2 skipped)
        - 300 kg to mandi (Priority 3)
        """
        # Create inventory with matching contributions
        contributions = [
            FarmerContribution(
                contribution_id="contrib-1",
                farmer_id="farmer-1",
                farmer_name="Farmer One",
                crop_type=self.crop_type,
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("500"),
            available_quantity_kg=Decimal("500"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # Create reservations
        reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("200"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
        ]
        
        # No processing partners
        partners = []
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = partners
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Verify allocations
        assert len(allocation.channel_allocations) == 2  # 1 society + 1 mandi
        
        # Society allocation (200 kg)
        society_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.SOCIETY]
        assert len(society_allocations) == 1
        assert society_allocations[0].quantity_kg == Decimal("200")
        
        # No processing allocations
        processing_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.PROCESSING]
        assert len(processing_allocations) == 0
        
        # Mandi allocation (300 kg)
        mandi_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == ChannelType.MANDI]
        assert len(mandi_allocations) == 1
        assert mandi_allocations[0].quantity_kg == Decimal("300")
        
        # Total allocation
        assert allocation.total_quantity_kg == Decimal("500")
    
    def test_allocate_with_no_inventory(self):
        """
        Test allocation with no available inventory.
        """
        # Create inventory with zero available
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("0"),
            available_quantity_kg=Decimal("0"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Create reservations (won't be fulfilled)
        reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("100"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
        ]
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = []
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Verify no allocations
        assert len(allocation.channel_allocations) == 0
        assert allocation.total_quantity_kg == Decimal("0")
        assert allocation.blended_realization_per_kg == Decimal("0")
    
    def test_allocate_inventory_not_found(self):
        """
        Test allocation when inventory doesn't exist.
        """
        # Mock repository to return None
        self.mock_inventory_repo.get_inventory.return_value = None
        
        # Execute allocation and expect error
        with pytest.raises(ValueError, match="No inventory found"):
            self.service.allocate_inventory(
                fpo_id=self.fpo_id,
                crop_type=self.crop_type,
                allocation_date=self.allocation_date,
            )
    
    def test_blended_realization_calculation(self):
        """
        Test that blended realization is calculated correctly across all channels.
        
        Scenario:
        - 100 kg to societies at ₹50/kg = ₹5000
        - 100 kg to processing at ₹45/kg = ₹4500
        - 100 kg to mandi at ₹35/kg = ₹3500
        - Total: 300 kg, ₹13000
        - Blended realization: ₹13000 / 300 kg = ₹43.33/kg
        """
        # Create inventory with matching contributions
        contributions = [
            FarmerContribution(
                contribution_id="contrib-1",
                farmer_id="farmer-1",
                farmer_name="Farmer One",
                crop_type=self.crop_type,
                quantity_kg=Decimal("300"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            total_quantity_kg=Decimal("300"),
            available_quantity_kg=Decimal("300"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # Create reservations
        reservations = [
            Reservation(
                reservation_id="res-1",
                society_id="soc-1",
                crop_type=self.crop_type,
                reserved_quantity_kg=Decimal("100"),
                reservation_timestamp=datetime(2024, 1, 1, 10, 0, 0),
                delivery_date=self.allocation_date,
                status=ReservationStatus.CONFIRMED,
            ),
        ]
        
        # Create processing partners
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Processor",
                contact_details={"phone": "1234567890"},
                facility_location="Mumbai",
                rates_by_crop={self.crop_type: Decimal("45.0")},
                capacity_by_crop={self.crop_type: Decimal("100.0")},
                quality_requirements={self.crop_type: "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        # Mock repository methods
        self.mock_inventory_repo.get_inventory.return_value = inventory
        self.mock_inventory_repo.get_reservations_by_date.return_value = reservations
        self.mock_processing_partner_repo.list_partners.return_value = partners
        
        # Execute allocation
        allocation = self.service.allocate_inventory(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
        )
        
        # Calculate expected blended realization
        # Society: 100 kg * ₹50/kg = ₹5000
        # Processing: 100 kg * ₹45/kg = ₹4500
        # Mandi: 100 kg * ₹35/kg = ₹3500 (assuming mandi price is ₹35)
        # Total: ₹13000 / 300 kg = ₹43.33/kg
        
        expected_blended = Decimal("13000") / Decimal("300")
        
        # Verify blended realization (allow small rounding difference)
        assert abs(allocation.blended_realization_per_kg - expected_blended) < Decimal("0.50"), (
            f"Blended realization mismatch: expected ~{expected_blended}, "
            f"got {allocation.blended_realization_per_kg}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
