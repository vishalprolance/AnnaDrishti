"""
Unit tests for society management

Tests registration validation, profile updates, and delivery frequency validation.
Validates Requirement 2.5: delivery frequency validation.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import uuid

from backend.collective.models import (
    SocietyProfile,
    CropPreference,
    DeliveryFrequency,
)
from backend.collective.services import SocietyService
from backend.collective.db import SocietyRepository


class TestSocietyRegistrationValidation:
    """Test society registration validation logic"""
    
    def test_valid_society_registration(self):
        """Test that valid society registration is accepted"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        society = service.register_society(
            society_name="Green Valley Apartments",
            location="Bangalore",
            contact_details={"phone": "9876543210", "email": "admin@greenvalley.com"},
            delivery_address="Green Valley, Whitefield, Bangalore",
            delivery_frequency="once_weekly",
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
            crop_preferences=[
                {"crop_type": "tomato", "typical_quantity_kg": 50},
                {"crop_type": "onion", "typical_quantity_kg": 30},
            ],
        )
        
        assert society.society_name == "Green Valley Apartments"
        assert society.location == "Bangalore"
        assert society.delivery_frequency == DeliveryFrequency.ONCE_WEEKLY
        assert len(society.crop_preferences) == 2
        assert society.crop_preferences[0].crop_type == "tomato"
        assert society.crop_preferences[0].typical_quantity_kg == Decimal("50")
        mock_repo.create_society.assert_called_once()
    
    def test_registration_generates_unique_id(self):
        """Test that registration generates a unique society ID"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        society1 = service.register_society(
            society_name="Society 1",
            location="Location 1",
            contact_details={"phone": "1234567890"},
            delivery_address="Address 1",
            delivery_frequency="once_weekly",
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        society2 = service.register_society(
            society_name="Society 2",
            location="Location 2",
            contact_details={"phone": "0987654321"},
            delivery_address="Address 2",
            delivery_frequency="twice_weekly",
            preferred_day="Tuesday",
            preferred_time_window="10:00-12:00",
        )
        
        assert society1.society_id != society2.society_id
        assert len(society1.society_id) > 0
        assert len(society2.society_id) > 0
    
    def test_registration_without_crop_preferences(self):
        """Test that registration works without crop preferences"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        society = service.register_society(
            society_name="Simple Society",
            location="Mumbai",
            contact_details={"phone": "1111111111"},
            delivery_address="Simple Address",
            delivery_frequency="weekend_only",
            preferred_day="Saturday",
            preferred_time_window="8:00-10:00",
        )
        
        assert society.crop_preferences == []
        mock_repo.create_society.assert_called_once()
    
    def test_registration_with_empty_crop_preferences(self):
        """Test that registration works with empty crop preferences list"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        society = service.register_society(
            society_name="Empty Prefs Society",
            location="Delhi",
            contact_details={"phone": "2222222222"},
            delivery_address="Delhi Address",
            delivery_frequency="once_weekly",
            preferred_day="Wednesday",
            preferred_time_window="14:00-16:00",
            crop_preferences=[],
        )
        
        assert society.crop_preferences == []


class TestDeliveryFrequencyValidation:
    """Test delivery frequency validation"""
    
    def test_valid_delivery_frequencies(self):
        """Test that all valid delivery frequencies are accepted"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        valid_frequencies = ["once_weekly", "twice_weekly", "weekend_only"]
        
        for freq in valid_frequencies:
            society = service.register_society(
                society_name=f"Society {freq}",
                location="Test Location",
                contact_details={"phone": "9999999999"},
                delivery_address="Test Address",
                delivery_frequency=freq,
                preferred_day="Monday",
                preferred_time_window="9:00-11:00",
            )
            
            assert society.delivery_frequency.value == freq
    
    def test_invalid_delivery_frequency_rejected(self):
        """Test that invalid delivery frequency is rejected"""
        mock_repo = Mock(spec=SocietyRepository)
        service = SocietyService(repository=mock_repo)
        
        with pytest.raises(ValueError):
            service.register_society(
                society_name="Invalid Freq Society",
                location="Test Location",
                contact_details={"phone": "9999999999"},
                delivery_address="Test Address",
                delivery_frequency="daily",  # Invalid frequency
                preferred_day="Monday",
                preferred_time_window="9:00-11:00",
            )
    
    def test_delivery_frequency_enum_validation(self):
        """Test that DeliveryFrequency enum validates correctly"""
        # Valid values
        assert DeliveryFrequency.ONCE_WEEKLY.value == "once_weekly"
        assert DeliveryFrequency.TWICE_WEEKLY.value == "twice_weekly"
        assert DeliveryFrequency.WEEKEND_ONLY.value == "weekend_only"
        
        # Invalid value
        with pytest.raises(ValueError):
            DeliveryFrequency("invalid_frequency")
    
    def test_society_profile_validates_delivery_frequency(self):
        """Test that SocietyProfile validates delivery frequency on creation"""
        # Valid frequency as string
        society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Test Location",
            contact_details={"phone": "9999999999"},
            delivery_address="Test Address",
            delivery_frequency="once_weekly",
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        assert society.delivery_frequency == DeliveryFrequency.ONCE_WEEKLY
        
        # Valid frequency as enum
        society2 = SocietyProfile(
            society_id="S002",
            society_name="Test Society 2",
            location="Test Location",
            contact_details={"phone": "8888888888"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.TWICE_WEEKLY,
            preferred_day="Tuesday",
            preferred_time_window="10:00-12:00",
        )
        
        assert society2.delivery_frequency == DeliveryFrequency.TWICE_WEEKLY
        
        # Invalid frequency
        with pytest.raises(ValueError):
            SocietyProfile(
                society_id="S003",
                society_name="Invalid Society",
                location="Test Location",
                contact_details={"phone": "7777777777"},
                delivery_address="Test Address",
                delivery_frequency="monthly",  # Invalid
                preferred_day="Monday",
                preferred_time_window="9:00-11:00",
            )


class TestSocietyProfileUpdates:
    """Test society profile update operations"""
    
    def test_update_society_name(self):
        """Test updating society name"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Old Name",
            location="Bangalore",
            contact_details={"phone": "9876543210"},
            delivery_address="Old Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        updated_society = service.update_society(
            society_id="S001",
            society_name="New Name",
        )
        
        assert updated_society.society_name == "New Name"
        assert updated_society.location == "Bangalore"  # Unchanged
        mock_repo.update_society.assert_called_once()
    
    def test_update_delivery_frequency(self):
        """Test updating delivery frequency"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Mumbai",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        updated_society = service.update_society(
            society_id="S001",
            delivery_frequency="twice_weekly",
        )
        
        assert updated_society.delivery_frequency == DeliveryFrequency.TWICE_WEEKLY
        mock_repo.update_society.assert_called_once()
    
    def test_update_invalid_delivery_frequency_rejected(self):
        """Test that updating to invalid delivery frequency is rejected"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Delhi",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        service = SocietyService(repository=mock_repo)
        
        with pytest.raises(ValueError):
            service.update_society(
                society_id="S001",
                delivery_frequency="daily",  # Invalid
            )
    
    def test_update_contact_details(self):
        """Test updating contact details"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Pune",
            contact_details={"phone": "1111111111", "email": "old@test.com"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        new_contact = {"phone": "2222222222", "email": "new@test.com"}
        updated_society = service.update_society(
            society_id="S001",
            contact_details=new_contact,
        )
        
        assert updated_society.contact_details == new_contact
        mock_repo.update_society.assert_called_once()
    
    def test_update_crop_preferences(self):
        """Test updating crop preferences"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Chennai",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
            crop_preferences=[
                CropPreference(crop_type="tomato", typical_quantity_kg=Decimal("50")),
            ],
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        new_prefs = [
            {"crop_type": "onion", "typical_quantity_kg": 30},
            {"crop_type": "potato", "typical_quantity_kg": 40},
        ]
        
        updated_society = service.update_society(
            society_id="S001",
            crop_preferences=new_prefs,
        )
        
        assert len(updated_society.crop_preferences) == 2
        assert updated_society.crop_preferences[0].crop_type == "onion"
        assert updated_society.crop_preferences[1].crop_type == "potato"
        mock_repo.update_society.assert_called_once()
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields at once"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Old Name",
            location="Old Location",
            contact_details={"phone": "1111111111"},
            delivery_address="Old Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        updated_society = service.update_society(
            society_id="S001",
            society_name="New Name",
            location="New Location",
            delivery_frequency="weekend_only",
            preferred_day="Saturday",
        )
        
        assert updated_society.society_name == "New Name"
        assert updated_society.location == "New Location"
        assert updated_society.delivery_frequency == DeliveryFrequency.WEEKEND_ONLY
        assert updated_society.preferred_day == "Saturday"
        assert updated_society.preferred_time_window == "9:00-11:00"  # Unchanged
        mock_repo.update_society.assert_called_once()
    
    def test_update_nonexistent_society_raises_error(self):
        """Test that updating nonexistent society raises error"""
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = None
        service = SocietyService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Society not found"):
            service.update_society(
                society_id="NONEXISTENT",
                society_name="New Name",
            )
    
    def test_update_preferred_day_and_time(self):
        """Test updating preferred delivery day and time window"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Hyderabad",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.TWICE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.update_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        updated_society = service.update_society(
            society_id="S001",
            preferred_day="Friday",
            preferred_time_window="14:00-16:00",
        )
        
        assert updated_society.preferred_day == "Friday"
        assert updated_society.preferred_time_window == "14:00-16:00"
        mock_repo.update_society.assert_called_once()


class TestSocietyProfileModel:
    """Test SocietyProfile model methods"""
    
    def test_get_typical_quantity_existing_crop(self):
        """Test getting typical quantity for existing crop preference"""
        society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Bangalore",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
            crop_preferences=[
                CropPreference(crop_type="tomato", typical_quantity_kg=Decimal("50")),
                CropPreference(crop_type="onion", typical_quantity_kg=Decimal("30")),
            ],
        )
        
        qty = society.get_typical_quantity("tomato")
        assert qty == Decimal("50")
        
        qty = society.get_typical_quantity("onion")
        assert qty == Decimal("30")
    
    def test_get_typical_quantity_nonexistent_crop(self):
        """Test getting typical quantity for nonexistent crop returns None"""
        society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Mumbai",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
            crop_preferences=[
                CropPreference(crop_type="tomato", typical_quantity_kg=Decimal("50")),
            ],
        )
        
        qty = society.get_typical_quantity("potato")
        assert qty is None
    
    def test_society_to_dict_and_from_dict(self):
        """Test serialization and deserialization of society profile"""
        original = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Delhi",
            contact_details={"phone": "9876543210", "email": "test@test.com"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.TWICE_WEEKLY,
            preferred_day="Wednesday",
            preferred_time_window="10:00-12:00",
            crop_preferences=[
                CropPreference(crop_type="tomato", typical_quantity_kg=Decimal("50")),
                CropPreference(crop_type="onion", typical_quantity_kg=Decimal("30")),
            ],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )
        
        # Convert to dict
        data = original.to_dict()
        
        assert data["society_id"] == "S001"
        assert data["society_name"] == "Test Society"
        assert data["delivery_frequency"] == "twice_weekly"
        assert len(data["crop_preferences"]) == 2
        
        # Convert back from dict
        restored = SocietyProfile.from_dict(data)
        
        assert restored.society_id == original.society_id
        assert restored.society_name == original.society_name
        assert restored.delivery_frequency == original.delivery_frequency
        assert len(restored.crop_preferences) == len(original.crop_preferences)
        assert restored.crop_preferences[0].crop_type == "tomato"
        assert restored.crop_preferences[0].typical_quantity_kg == Decimal("50")


class TestSocietyDeletion:
    """Test society deletion operations"""
    
    def test_delete_existing_society(self):
        """Test deleting an existing society"""
        existing_society = SocietyProfile(
            society_id="S001",
            society_name="Test Society",
            location="Bangalore",
            contact_details={"phone": "9876543210"},
            delivery_address="Test Address",
            delivery_frequency=DeliveryFrequency.ONCE_WEEKLY,
            preferred_day="Monday",
            preferred_time_window="9:00-11:00",
        )
        
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = existing_society
        mock_repo.delete_society = Mock()  # Add mock method
        service = SocietyService(repository=mock_repo)
        
        service.delete_society("S001")
        
        mock_repo.delete_society.assert_called_once_with("S001")
    
    def test_delete_nonexistent_society_raises_error(self):
        """Test that deleting nonexistent society raises error"""
        mock_repo = Mock(spec=SocietyRepository)
        mock_repo.get_society.return_value = None
        service = SocietyService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="Society not found"):
            service.delete_society("NONEXISTENT")


class TestCropPreferenceModel:
    """Test CropPreference model"""
    
    def test_crop_preference_creation(self):
        """Test creating crop preference"""
        pref = CropPreference(
            crop_type="tomato",
            typical_quantity_kg=Decimal("50.5"),
        )
        
        assert pref.crop_type == "tomato"
        assert pref.typical_quantity_kg == Decimal("50.5")
    
    def test_crop_preference_to_dict_and_from_dict(self):
        """Test serialization and deserialization of crop preference"""
        original = CropPreference(
            crop_type="onion",
            typical_quantity_kg=Decimal("30.25"),
        )
        
        data = original.to_dict()
        
        assert data["crop_type"] == "onion"
        assert data["typical_quantity_kg"] == "30.25"
        
        restored = CropPreference.from_dict(data)
        
        assert restored.crop_type == original.crop_type
        assert restored.typical_quantity_kg == original.typical_quantity_kg
