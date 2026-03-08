"""
Unit tests for Priority 2: Processing partner allocation
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock

from collective.services.allocation_service import AllocationService
from collective.models import (
    ProcessingPartner,
    ChannelType,
    FulfillmentStatus,
)


class TestPriority2ProcessingAllocation:
    """Test Priority 2: Processing partner allocation logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mocked repositories
        mock_inventory_repo = Mock()
        mock_allocation_repo = Mock()
        mock_processing_partner_repo = Mock()
        
        # Create service with mocked repositories
        self.service = AllocationService(
            inventory_repository=mock_inventory_repo,
            allocation_repository=mock_allocation_repo,
            processing_partner_repository=mock_processing_partner_repo,
        )
        
        self.fpo_id = "FPO001"
        self.crop_type = "tomato"
        self.allocation_date = date(2024, 1, 15)
    
    def test_allocate_to_single_partner_within_capacity(self):
        """Test allocation to single partner within their capacity"""
        # Create mock partner
        partner = ProcessingPartner(
            partner_id="PP001",
            partner_name="Fresh Foods Processing",
            contact_details={"phone": "1234567890"},
            facility_location="Mumbai",
            rates_by_crop={"tomato": Decimal("45.0")},
            capacity_by_crop={"tomato": Decimal("500.0")},
            quality_requirements={"tomato": "Grade A"},
            pickup_schedule="Daily 8 AM",
            created_at=datetime.now(),
        )
        
        # Mock the repository
        self.service.processing_partner_repository.list_partners = lambda: [partner]
        
        # Allocate 300 kg (within capacity of 500 kg)
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("300.0"),
        )
        
        # Verify allocation
        assert len(allocations) == 1
        assert allocations[0].channel_type == ChannelType.PROCESSING
        assert allocations[0].channel_id == "PP001"
        assert allocations[0].channel_name == "Fresh Foods Processing"
        assert allocations[0].quantity_kg == Decimal("300.0")
        assert allocations[0].price_per_kg == Decimal("45.0")
        assert allocations[0].revenue == Decimal("13500.0")  # 300 * 45
        assert allocations[0].priority == 2
        assert allocations[0].fulfillment_status == FulfillmentStatus.PENDING
        assert remaining == Decimal("0.0")
    
    def test_allocate_exceeds_partner_capacity(self):
        """Test allocation when available quantity exceeds partner capacity"""
        partner = ProcessingPartner(
            partner_id="PP001",
            partner_name="Fresh Foods Processing",
            contact_details={"phone": "1234567890"},
            facility_location="Mumbai",
            rates_by_crop={"tomato": Decimal("45.0")},
            capacity_by_crop={"tomato": Decimal("200.0")},  # Capacity is 200 kg
            quality_requirements={"tomato": "Grade A"},
            pickup_schedule="Daily 8 AM",
            created_at=datetime.now(),
        )
        
        self.service.processing_partner_repository.list_partners = lambda: [partner]
        
        # Try to allocate 500 kg (exceeds capacity of 200 kg)
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("500.0"),
        )
        
        # Should only allocate up to capacity
        assert len(allocations) == 1
        assert allocations[0].quantity_kg == Decimal("200.0")
        assert remaining == Decimal("300.0")  # 500 - 200
    
    def test_allocate_to_multiple_partners_sorted_by_rate(self):
        """Test allocation to multiple partners sorted by rate (highest first)"""
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Low Rate Processor",
                contact_details={"phone": "1111111111"},
                facility_location="Pune",
                rates_by_crop={"tomato": Decimal("40.0")},  # Lower rate
                capacity_by_crop={"tomato": Decimal("300.0")},
                quality_requirements={"tomato": "Grade B"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
            ProcessingPartner(
                partner_id="PP002",
                partner_name="High Rate Processor",
                contact_details={"phone": "2222222222"},
                facility_location="Mumbai",
                rates_by_crop={"tomato": Decimal("50.0")},  # Higher rate
                capacity_by_crop={"tomato": Decimal("200.0")},
                quality_requirements={"tomato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
            ProcessingPartner(
                partner_id="PP003",
                partner_name="Medium Rate Processor",
                contact_details={"phone": "3333333333"},
                facility_location="Nashik",
                rates_by_crop={"tomato": Decimal("45.0")},  # Medium rate
                capacity_by_crop={"tomato": Decimal("250.0")},
                quality_requirements={"tomato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        self.service.processing_partner_repository.list_partners = lambda: partners
        
        # Allocate 600 kg across partners
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("600.0"),
        )
        
        # Should allocate in order: PP002 (50), PP003 (45), PP001 (40)
        assert len(allocations) == 3
        
        # First allocation: PP002 (highest rate)
        assert allocations[0].channel_id == "PP002"
        assert allocations[0].price_per_kg == Decimal("50.0")
        assert allocations[0].quantity_kg == Decimal("200.0")  # Full capacity
        
        # Second allocation: PP003 (medium rate)
        assert allocations[1].channel_id == "PP003"
        assert allocations[1].price_per_kg == Decimal("45.0")
        assert allocations[1].quantity_kg == Decimal("250.0")  # Full capacity
        
        # Third allocation: PP001 (lowest rate)
        assert allocations[2].channel_id == "PP001"
        assert allocations[2].price_per_kg == Decimal("40.0")
        assert allocations[2].quantity_kg == Decimal("150.0")  # Remaining 150 kg
        
        assert remaining == Decimal("0.0")
    
    def test_no_partners_available(self):
        """Test allocation when no processing partners are available"""
        self.service.processing_partner_repository.list_partners = lambda: []
        
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("500.0"),
        )
        
        # No allocations should be made
        assert len(allocations) == 0
        assert remaining == Decimal("500.0")
    
    def test_partners_without_crop_type_filtered_out(self):
        """Test that partners without rates/capacity for crop type are filtered out"""
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Tomato Processor",
                contact_details={"phone": "1111111111"},
                facility_location="Mumbai",
                rates_by_crop={"tomato": Decimal("45.0")},
                capacity_by_crop={"tomato": Decimal("300.0")},
                quality_requirements={"tomato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
            ProcessingPartner(
                partner_id="PP002",
                partner_name="Potato Processor",
                contact_details={"phone": "2222222222"},
                facility_location="Pune",
                rates_by_crop={"potato": Decimal("30.0")},  # Different crop
                capacity_by_crop={"potato": Decimal("500.0")},
                quality_requirements={"potato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        self.service.processing_partner_repository.list_partners = lambda: partners
        
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("400.0"),
        )
        
        # Only PP001 should be allocated (handles tomato)
        assert len(allocations) == 1
        assert allocations[0].channel_id == "PP001"
        assert allocations[0].quantity_kg == Decimal("300.0")
        assert remaining == Decimal("100.0")
    
    def test_zero_available_quantity(self):
        """Test allocation with zero available quantity"""
        partner = ProcessingPartner(
            partner_id="PP001",
            partner_name="Fresh Foods Processing",
            contact_details={"phone": "1234567890"},
            facility_location="Mumbai",
            rates_by_crop={"tomato": Decimal("45.0")},
            capacity_by_crop={"tomato": Decimal("500.0")},
            quality_requirements={"tomato": "Grade A"},
            pickup_schedule="Daily",
            created_at=datetime.now(),
        )
        
        self.service.processing_partner_repository.list_partners = lambda: [partner]
        
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("0.0"),
        )
        
        # No allocations should be made
        assert len(allocations) == 0
        assert remaining == Decimal("0.0")
    
    def test_partner_with_zero_capacity(self):
        """Test that partners with zero capacity are skipped"""
        partners = [
            ProcessingPartner(
                partner_id="PP001",
                partner_name="Zero Capacity Processor",
                contact_details={"phone": "1111111111"},
                facility_location="Mumbai",
                rates_by_crop={"tomato": Decimal("50.0")},
                capacity_by_crop={"tomato": Decimal("0.0")},  # Zero capacity
                quality_requirements={"tomato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
            ProcessingPartner(
                partner_id="PP002",
                partner_name="Normal Processor",
                contact_details={"phone": "2222222222"},
                facility_location="Pune",
                rates_by_crop={"tomato": Decimal("45.0")},
                capacity_by_crop={"tomato": Decimal("300.0")},
                quality_requirements={"tomato": "Grade A"},
                pickup_schedule="Daily",
                created_at=datetime.now(),
            ),
        ]
        
        self.service.processing_partner_repository.list_partners = lambda: partners
        
        allocations, remaining = self.service.allocate_priority_2_processing(
            fpo_id=self.fpo_id,
            crop_type=self.crop_type,
            allocation_date=self.allocation_date,
            available_quantity=Decimal("200.0"),
        )
        
        # Only PP002 should get allocation
        assert len(allocations) == 1
        assert allocations[0].channel_id == "PP002"
        assert allocations[0].quantity_kg == Decimal("200.0")
        assert remaining == Decimal("0.0")
