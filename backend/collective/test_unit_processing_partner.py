"""
Unit tests for ProcessingPartner data model
"""

import pytest
from decimal import Decimal
from datetime import datetime
from backend.collective.models import ProcessingPartner


class TestProcessingPartnerValidation:
    """Test validation rules for ProcessingPartner"""
    
    def test_create_valid_partner(self):
        """Test creating a valid processing partner"""
        partner = ProcessingPartner(
            partner_id="partner-001",
            partner_name="Fresh Foods Processing",
            contact_details={
                "phone": "+91-9876543210",
                "email": "contact@freshfoods.com"
            },
            facility_location="Mumbai, Maharashtra",
            rates_by_crop={
                "tomato": Decimal("25.50"),
                "potato": Decimal("18.00")
            },
            capacity_by_crop={
                "tomato": Decimal("500"),
                "potato": Decimal("1000")
            },
            quality_requirements={
                "tomato": "Grade A or B",
                "potato": "Grade A"
            },
            pickup_schedule="Daily 6:00-8:00 AM"
        )
        
        assert partner.partner_id == "partner-001"
        assert partner.partner_name == "Fresh Foods Processing"
        assert partner.rates_by_crop["tomato"] == Decimal("25.50")
        assert partner.capacity_by_crop["potato"] == Decimal("1000")
    
    def test_validate_positive_rates(self):
        """Test that rates must be positive (Requirement 5.5)"""
        with pytest.raises(ValueError, match="Rate for tomato must be positive"):
            ProcessingPartner(
                partner_id="partner-002",
                partner_name="Bad Rates Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Delhi",
                rates_by_crop={
                    "tomato": Decimal("-10.00")  # Negative rate
                },
                capacity_by_crop={
                    "tomato": Decimal("100")
                },
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_validate_zero_rate_not_allowed(self):
        """Test that zero rates are not allowed (Requirement 5.5)"""
        with pytest.raises(ValueError, match="Rate for potato must be positive"):
            ProcessingPartner(
                partner_id="partner-003",
                partner_name="Zero Rate Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Bangalore",
                rates_by_crop={
                    "potato": Decimal("0")  # Zero rate
                },
                capacity_by_crop={
                    "potato": Decimal("100")
                },
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_validate_non_negative_capacity(self):
        """Test that capacity limits must be non-negative (Requirement 5.5)"""
        with pytest.raises(ValueError, match="Capacity for tomato cannot be negative"):
            ProcessingPartner(
                partner_id="partner-004",
                partner_name="Negative Capacity Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Chennai",
                rates_by_crop={
                    "tomato": Decimal("20.00")
                },
                capacity_by_crop={
                    "tomato": Decimal("-50")  # Negative capacity
                },
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_zero_capacity_allowed(self):
        """Test that zero capacity is allowed (non-negative includes zero)"""
        partner = ProcessingPartner(
            partner_id="partner-005",
            partner_name="Zero Capacity Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Pune",
            rates_by_crop={
                "onion": Decimal("15.00")
            },
            capacity_by_crop={
                "onion": Decimal("0")  # Zero capacity is valid
            },
            quality_requirements={},
            pickup_schedule="Weekly"
        )
        
        assert partner.capacity_by_crop["onion"] == Decimal("0")


class TestProcessingPartnerMethods:
    """Test methods of ProcessingPartner"""
    
    def test_get_rate_existing_crop(self):
        """Test getting rate for an existing crop"""
        partner = ProcessingPartner(
            partner_id="partner-006",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Hyderabad",
            rates_by_crop={
                "tomato": Decimal("22.00"),
                "potato": Decimal("16.00")
            },
            capacity_by_crop={
                "tomato": Decimal("300"),
                "potato": Decimal("500")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        assert partner.get_rate("tomato") == Decimal("22.00")
        assert partner.get_rate("potato") == Decimal("16.00")
    
    def test_get_rate_non_existing_crop(self):
        """Test getting rate for a non-existing crop returns zero"""
        partner = ProcessingPartner(
            partner_id="partner-007",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Kolkata",
            rates_by_crop={
                "tomato": Decimal("22.00")
            },
            capacity_by_crop={
                "tomato": Decimal("300")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        assert partner.get_rate("carrot") == Decimal("0")
    
    def test_get_capacity_existing_crop(self):
        """Test getting capacity for an existing crop"""
        partner = ProcessingPartner(
            partner_id="partner-008",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Ahmedabad",
            rates_by_crop={
                "tomato": Decimal("20.00")
            },
            capacity_by_crop={
                "tomato": Decimal("400")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        assert partner.get_capacity("tomato") == Decimal("400")
    
    def test_get_capacity_non_existing_crop(self):
        """Test getting capacity for a non-existing crop returns zero"""
        partner = ProcessingPartner(
            partner_id="partner-009",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Jaipur",
            rates_by_crop={
                "tomato": Decimal("20.00")
            },
            capacity_by_crop={
                "tomato": Decimal("400")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        assert partner.get_capacity("onion") == Decimal("0")


class TestProcessingPartnerSerialization:
    """Test serialization and deserialization"""
    
    def test_to_dict(self):
        """Test converting partner to dictionary"""
        created_at = datetime(2024, 1, 15, 10, 30, 0)
        partner = ProcessingPartner(
            partner_id="partner-010",
            partner_name="Serialization Test",
            contact_details={
                "phone": "+91-9876543210",
                "email": "test@example.com"
            },
            facility_location="Surat",
            rates_by_crop={
                "tomato": Decimal("23.50")
            },
            capacity_by_crop={
                "tomato": Decimal("600")
            },
            quality_requirements={
                "tomato": "Grade A"
            },
            pickup_schedule="Daily 7:00 AM",
            created_at=created_at
        )
        
        data = partner.to_dict()
        
        assert data["partner_id"] == "partner-010"
        assert data["partner_name"] == "Serialization Test"
        assert data["rates_by_crop"]["tomato"] == "23.50"
        assert data["capacity_by_crop"]["tomato"] == "600"
        assert data["created_at"] == created_at.isoformat()
    
    def test_from_dict(self):
        """Test creating partner from dictionary"""
        data = {
            "partner_id": "partner-011",
            "partner_name": "Deserialization Test",
            "contact_details": {
                "phone": "+91-9876543210"
            },
            "facility_location": "Lucknow",
            "rates_by_crop": {
                "potato": "19.00"
            },
            "capacity_by_crop": {
                "potato": "800"
            },
            "quality_requirements": {
                "potato": "Grade B or better"
            },
            "pickup_schedule": "Twice weekly",
            "created_at": "2024-01-15T10:30:00"
        }
        
        partner = ProcessingPartner.from_dict(data)
        
        assert partner.partner_id == "partner-011"
        assert partner.partner_name == "Deserialization Test"
        assert partner.rates_by_crop["potato"] == Decimal("19.00")
        assert partner.capacity_by_crop["potato"] == Decimal("800")
        assert partner.created_at == datetime(2024, 1, 15, 10, 30, 0)
    
    def test_round_trip_serialization(self):
        """Test that serialization and deserialization are inverses"""
        original = ProcessingPartner(
            partner_id="partner-012",
            partner_name="Round Trip Test",
            contact_details={
                "phone": "+91-1234567890",
                "email": "roundtrip@example.com"
            },
            facility_location="Indore",
            rates_by_crop={
                "tomato": Decimal("21.75"),
                "potato": Decimal("17.25")
            },
            capacity_by_crop={
                "tomato": Decimal("450"),
                "potato": Decimal("750")
            },
            quality_requirements={
                "tomato": "Grade A",
                "potato": "Grade A or B"
            },
            pickup_schedule="Daily 6:00-8:00 AM"
        )
        
        # Serialize and deserialize
        data = original.to_dict()
        restored = ProcessingPartner.from_dict(data)
        
        # Verify all fields match
        assert restored.partner_id == original.partner_id
        assert restored.partner_name == original.partner_name
        assert restored.contact_details == original.contact_details
        assert restored.facility_location == original.facility_location
        assert restored.rates_by_crop == original.rates_by_crop
        assert restored.capacity_by_crop == original.capacity_by_crop
        assert restored.quality_requirements == original.quality_requirements
        assert restored.pickup_schedule == original.pickup_schedule
        assert restored.created_at == original.created_at


class TestProcessingPartnerRequirements:
    """Test that all requirements are met"""
    
    def test_requirement_5_1_capture_partner_details(self):
        """
        Requirement 5.1: WHEN a processing partner is registered, 
        THE System SHALL capture partner name, contact details, 
        and processing facility location
        """
        partner = ProcessingPartner(
            partner_id="partner-013",
            partner_name="Requirement Test Partner",
            contact_details={
                "phone": "+91-9876543210",
                "email": "req@test.com",
                "contact_person": "John Doe"
            },
            facility_location="123 Industrial Area, Mumbai",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("500")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        # Verify all required fields are captured
        assert partner.partner_name == "Requirement Test Partner"
        assert "phone" in partner.contact_details
        assert "email" in partner.contact_details
        assert partner.facility_location == "123 Industrial Area, Mumbai"
    
    def test_requirement_5_5_validate_positive_rates(self):
        """
        Requirement 5.5: THE System SHALL validate that rates are positive
        """
        # Valid positive rate
        partner = ProcessingPartner(
            partner_id="partner-014",
            partner_name="Valid Rate Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Delhi",
            rates_by_crop={"tomato": Decimal("25.00")},
            capacity_by_crop={"tomato": Decimal("100")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        assert partner.rates_by_crop["tomato"] > 0
        
        # Invalid negative rate should raise error
        with pytest.raises(ValueError):
            ProcessingPartner(
                partner_id="partner-015",
                partner_name="Invalid Rate Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Delhi",
                rates_by_crop={"tomato": Decimal("-5.00")},
                capacity_by_crop={"tomato": Decimal("100")},
                quality_requirements={},
                pickup_schedule="Daily"
            )
    
    def test_requirement_5_5_validate_non_negative_capacity(self):
        """
        Requirement 5.5: THE System SHALL validate that capacity limits 
        are non-negative
        """
        # Valid non-negative capacity (including zero)
        partner = ProcessingPartner(
            partner_id="partner-016",
            partner_name="Valid Capacity Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Bangalore",
            rates_by_crop={"potato": Decimal("18.00")},
            capacity_by_crop={"potato": Decimal("0")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        assert partner.capacity_by_crop["potato"] >= 0
        
        # Invalid negative capacity should raise error
        with pytest.raises(ValueError):
            ProcessingPartner(
                partner_id="partner-017",
                partner_name="Invalid Capacity Partner",
                contact_details={"phone": "+91-1234567890"},
                facility_location="Bangalore",
                rates_by_crop={"potato": Decimal("18.00")},
                capacity_by_crop={"potato": Decimal("-100")},
                quality_requirements={},
                pickup_schedule="Daily"
            )
