"""
Unit tests for ProcessingPartnerService

Tests partner registration, updates, and management operations.
Validates Requirements 5.5 (registration validation, rate and capacity validation, partner updates)
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock

from collective.services import ProcessingPartnerService
from collective.models import ProcessingPartner


class TestPartnerRegistration:
    """Test partner registration validation (Requirement 5.5)"""
    
    def test_register_partner_with_valid_data(self):
        """Test registering a partner with valid data"""
        # Mock repository
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Register partner
        partner = service.register_partner(
            partner_name="Fresh Foods Processing",
            contact_details={
                "phone": "+91-9876543210",
                "email": "contact@freshfoods.com"
            },
            facility_location="Mumbai, Maharashtra",
            rates_by_crop={
                "tomato": 25.50,
                "potato": 18.00
            },
            capacity_by_crop={
                "tomato": 500,
                "potato": 1000
            },
            quality_requirements={
                "tomato": "Grade A or B",
                "potato": "Grade A"
            },
            pickup_schedule="Daily 6:00-8:00 AM"
        )
        
        # Verify partner was created
        assert partner.partner_name == "Fresh Foods Processing"
        assert partner.rates_by_crop["tomato"] == Decimal("25.50")
        assert partner.capacity_by_crop["potato"] == Decimal("1000")
        assert partner.partner_id.startswith("PP-")
        
        # Verify repository was called
        mock_repo.create_partner.assert_called_once()
    
    def test_register_partner_generates_unique_id(self):
        """Test that registration generates a unique partner ID"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner1 = service.register_partner(
            partner_name="Partner 1",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Location 1",
            rates_by_crop={"tomato": 20.00},
            capacity_by_crop={"tomato": 100},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        partner2 = service.register_partner(
            partner_name="Partner 2",
            contact_details={"phone": "+91-0987654321"},
            facility_location="Location 2",
            rates_by_crop={"potato": 15.00},
            capacity_by_crop={"potato": 200},
            quality_requirements={},
            pickup_schedule="Weekly"
        )
        
        # Verify IDs are different
        assert partner1.partner_id != partner2.partner_id
        assert partner1.partner_id.startswith("PP-")
        assert partner2.partner_id.startswith("PP-")
    
    def test_register_partner_converts_rates_to_decimal(self):
        """Test that rates are converted to Decimal for precision"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner = service.register_partner(
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": 25.50},  # Float input
            capacity_by_crop={"tomato": 500},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        # Verify conversion to Decimal
        assert isinstance(partner.rates_by_crop["tomato"], Decimal)
        assert partner.rates_by_crop["tomato"] == Decimal("25.50")
    
    def test_register_partner_converts_capacity_to_decimal(self):
        """Test that capacities are converted to Decimal for precision"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner = service.register_partner(
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"potato": 18.00},
            capacity_by_crop={"potato": 1000.5},  # Float input
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        # Verify conversion to Decimal
        assert isinstance(partner.capacity_by_crop["potato"], Decimal)
        assert partner.capacity_by_crop["potato"] == Decimal("1000.5")


class TestRateValidation:
    """Test rate validation (Requirement 5.5)"""
    
    def test_register_partner_rejects_negative_rates(self):
        """Test that negative rates are rejected"""
        mock_repo = Mock()
        service = ProcessingPartnerService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Rate for tomato must be positive"):
            service.register_partner(
                partner_name="Bad Rates Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Test Location",
                rates_by_crop={"tomato": -10.00},  # Negative rate
                capacity_by_crop={"tomato": 100},
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_register_partner_rejects_zero_rates(self):
        """Test that zero rates are rejected"""
        mock_repo = Mock()
        service = ProcessingPartnerService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Rate for potato must be positive"):
            service.register_partner(
                partner_name="Zero Rate Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Test Location",
                rates_by_crop={"potato": 0},  # Zero rate
                capacity_by_crop={"potato": 100},
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_register_partner_accepts_positive_rates(self):
        """Test that positive rates are accepted"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner = service.register_partner(
            partner_name="Valid Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={
                "tomato": 25.00,
                "potato": 18.50,
                "onion": 12.75
            },
            capacity_by_crop={
                "tomato": 100,
                "potato": 200,
                "onion": 150
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        # Verify all rates are positive
        assert all(rate > 0 for rate in partner.rates_by_crop.values())


class TestCapacityValidation:
    """Test capacity validation (Requirement 5.5)"""
    
    def test_register_partner_rejects_negative_capacity(self):
        """Test that negative capacity is rejected"""
        mock_repo = Mock()
        service = ProcessingPartnerService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Capacity for tomato cannot be negative"):
            service.register_partner(
                partner_name="Negative Capacity Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Test Location",
                rates_by_crop={"tomato": 20.00},
                capacity_by_crop={"tomato": -50},  # Negative capacity
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_register_partner_accepts_zero_capacity(self):
        """Test that zero capacity is accepted (non-negative includes zero)"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner = service.register_partner(
            partner_name="Zero Capacity Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"onion": 15.00},
            capacity_by_crop={"onion": 0},  # Zero capacity is valid
            quality_requirements={},
            pickup_schedule="Weekly"
        )
        
        assert partner.capacity_by_crop["onion"] == Decimal("0")
    
    def test_register_partner_accepts_positive_capacity(self):
        """Test that positive capacity is accepted"""
        mock_repo = Mock()
        mock_repo.create_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        partner = service.register_partner(
            partner_name="Valid Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": 20.00},
            capacity_by_crop={"tomato": 500},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        assert partner.capacity_by_crop["tomato"] == Decimal("500")
        assert partner.capacity_by_crop["tomato"] >= 0


class TestPartnerUpdates:
    """Test partner update operations (Requirement 5.5)"""
    
    def test_update_partner_name(self):
        """Test updating partner name"""
        # Create existing partner
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST001",
            partner_name="Original Name",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Original Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update partner name
        updated = service.update_partner(
            partner_id="PP-TEST001",
            partner_name="Updated Name"
        )
        
        assert updated.partner_name == "Updated Name"
        mock_repo.update_partner.assert_called_once()
    
    def test_update_contact_details(self):
        """Test updating contact details"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST002",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update contact details
        updated = service.update_partner(
            partner_id="PP-TEST002",
            contact_details={
                "phone": "+91-9876543210",
                "email": "new@example.com"
            }
        )
        
        assert updated.contact_details["phone"] == "+91-9876543210"
        assert updated.contact_details["email"] == "new@example.com"
    
    def test_update_rates_by_crop(self):
        """Test updating rates by crop"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST003",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update rates
        updated = service.update_partner(
            partner_id="PP-TEST003",
            rates_by_crop={
                "tomato": 25.00,
                "potato": 18.00
            }
        )
        
        assert updated.rates_by_crop["tomato"] == Decimal("25.00")
        assert updated.rates_by_crop["potato"] == Decimal("18.00")
    
    def test_update_capacity_by_crop(self):
        """Test updating capacity by crop"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST004",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update capacity
        updated = service.update_partner(
            partner_id="PP-TEST004",
            capacity_by_crop={
                "tomato": 500,
                "potato": 1000
            }
        )
        
        assert updated.capacity_by_crop["tomato"] == Decimal("500")
        assert updated.capacity_by_crop["potato"] == Decimal("1000")
    
    def test_update_validates_positive_rates(self):
        """Test that update validates rates are positive"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST005",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Try to update with negative rate
        with pytest.raises(ValueError, match="Rate for potato must be positive"):
            service.update_partner(
                partner_id="PP-TEST005",
                rates_by_crop={"potato": -10.00}
            )
    
    def test_update_validates_non_negative_capacity(self):
        """Test that update validates capacity is non-negative"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST006",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Try to update with negative capacity
        with pytest.raises(ValueError, match="Capacity for potato cannot be negative"):
            service.update_partner(
                partner_id="PP-TEST006",
                capacity_by_crop={"potato": -50}
            )
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST007",
            partner_name="Original Name",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Original Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update multiple fields
        updated = service.update_partner(
            partner_id="PP-TEST007",
            partner_name="Updated Name",
            facility_location="Updated Location",
            rates_by_crop={"tomato": 25.00, "potato": 18.00},
            capacity_by_crop={"tomato": 500, "potato": 1000}
        )
        
        assert updated.partner_name == "Updated Name"
        assert updated.facility_location == "Updated Location"
        assert updated.rates_by_crop["tomato"] == Decimal("25.00")
        assert updated.capacity_by_crop["potato"] == Decimal("1000")
    
    def test_update_nonexistent_partner_raises_error(self):
        """Test that updating a nonexistent partner raises an error"""
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=None)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Processing partner not found: PP-NONEXISTENT"):
            service.update_partner(
                partner_id="PP-NONEXISTENT",
                partner_name="New Name"
            )
    
    def test_update_quality_requirements(self):
        """Test updating quality requirements"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST008",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={"tomato": "Grade A"},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update quality requirements
        updated = service.update_partner(
            partner_id="PP-TEST008",
            quality_requirements={
                "tomato": "Grade A or B",
                "potato": "Grade A"
            }
        )
        
        assert updated.quality_requirements["tomato"] == "Grade A or B"
        assert updated.quality_requirements["potato"] == "Grade A"
    
    def test_update_pickup_schedule(self):
        """Test updating pickup schedule"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST009",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.update_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Update pickup schedule
        updated = service.update_partner(
            partner_id="PP-TEST009",
            pickup_schedule="Twice weekly: Mon & Thu 6:00-8:00 AM"
        )
        
        assert updated.pickup_schedule == "Twice weekly: Mon & Thu 6:00-8:00 AM"


class TestPartnerDeletion:
    """Test partner deletion operations"""
    
    def test_delete_existing_partner(self):
        """Test deleting an existing partner"""
        existing_partner = ProcessingPartner(
            partner_id="PP-TEST010",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=existing_partner)
        mock_repo.delete_partner = Mock()
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Delete partner
        service.delete_partner("PP-TEST010")
        
        mock_repo.delete_partner.assert_called_once_with("PP-TEST010")
    
    def test_delete_nonexistent_partner_raises_error(self):
        """Test that deleting a nonexistent partner raises an error"""
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=None)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Processing partner not found: PP-NONEXISTENT"):
            service.delete_partner("PP-NONEXISTENT")


class TestPartnerQueries:
    """Test partner query operations"""
    
    def test_get_partner_by_id(self):
        """Test retrieving a partner by ID"""
        partner = ProcessingPartner(
            partner_id="PP-TEST011",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=partner)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # Get partner
        result = service.get_partner("PP-TEST011")
        
        assert result.partner_id == "PP-TEST011"
        assert result.partner_name == "Test Partner"
        mock_repo.get_partner.assert_called_once_with("PP-TEST011")
    
    def test_get_nonexistent_partner_returns_none(self):
        """Test that getting a nonexistent partner returns None"""
        mock_repo = Mock()
        mock_repo.get_partner = Mock(return_value=None)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        result = service.get_partner("PP-NONEXISTENT")
        
        assert result is None
    
    def test_list_all_partners(self):
        """Test listing all partners"""
        partners = [
            ProcessingPartner(
                partner_id="PP-TEST012",
                partner_name="Partner 1",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Location 1",
                rates_by_crop={"tomato": Decimal("20.00")},
                capacity_by_crop={"tomato": Decimal("100")},
                quality_requirements={},
                pickup_schedule="Daily"
            ),
            ProcessingPartner(
                partner_id="PP-TEST013",
                partner_name="Partner 2",
                contact_details={"phone": "+91-0987654321"},
                facility_location="Location 2",
                rates_by_crop={"potato": Decimal("15.00")},
                capacity_by_crop={"potato": Decimal("200")},
                quality_requirements={},
                pickup_schedule="Weekly"
            )
        ]
        
        mock_repo = Mock()
        mock_repo.list_partners = Mock(return_value=partners)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # List all partners
        result = service.list_partners()
        
        assert len(result) == 2
        assert result[0].partner_id == "PP-TEST012"
        assert result[1].partner_id == "PP-TEST013"
    
    def test_list_partners_filtered_by_crop(self):
        """Test listing partners filtered by crop type"""
        partners = [
            ProcessingPartner(
                partner_id="PP-TEST014",
                partner_name="Tomato Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Location 1",
                rates_by_crop={"tomato": Decimal("20.00")},
                capacity_by_crop={"tomato": Decimal("100")},
                quality_requirements={},
                pickup_schedule="Daily"
            ),
            ProcessingPartner(
                partner_id="PP-TEST015",
                partner_name="Potato Partner",
                contact_details={"phone": "+91-0987654321"},
                facility_location="Location 2",
                rates_by_crop={"potato": Decimal("15.00")},
                capacity_by_crop={"potato": Decimal("200")},
                quality_requirements={},
                pickup_schedule="Weekly"
            ),
            ProcessingPartner(
                partner_id="PP-TEST016",
                partner_name="Multi Crop Partner",
                contact_details={"phone": "+91-5555555555"},
                facility_location="Location 3",
                rates_by_crop={
                    "tomato": Decimal("22.00"),
                    "potato": Decimal("16.00")
                },
                capacity_by_crop={
                    "tomato": Decimal("150"),
                    "potato": Decimal("250")
                },
                quality_requirements={},
                pickup_schedule="Daily"
            )
        ]
        
        mock_repo = Mock()
        mock_repo.list_partners = Mock(return_value=partners)
        
        service = ProcessingPartnerService(repository=mock_repo)
        
        # List partners that handle tomato
        result = service.list_partners(crop_type="tomato")
        
        assert len(result) == 2
        assert all("tomato" in p.rates_by_crop for p in result)
