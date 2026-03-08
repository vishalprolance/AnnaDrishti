"""
API tests for processing partner management endpoints
Tests Requirements 5.2, 5.3, 5.4
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI

# Mock the database connection before any imports
mock_pool = MagicMock()
with patch('collective.db.repositories.SimpleConnectionPool', return_value=mock_pool):
    from collective.api.processing import router
    from collective.models import ProcessingPartner
    from starlette.testclient import TestClient


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestGetProcessingPartner:
    """Test GET /api/processing-partners/{partner_id} endpoint (Requirement 5.2)"""
    
    @patch('collective.api.processing.processing_service')
    def test_get_existing_partner(self, mock_service):
        """Test retrieving an existing processing partner"""
        # Mock partner data
        mock_partner = ProcessingPartner(
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
        
        mock_service.get_partner.return_value = mock_partner
        
        # Make request
        response = client.get("/api/processing-partners/partner-001")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["partner_id"] == "partner-001"
        assert data["partner_name"] == "Fresh Foods Processing"
        assert data["rates_by_crop"]["tomato"] == "25.50"
        assert data["capacity_by_crop"]["potato"] == "1000"
        
        # Verify service was called correctly
        mock_service.get_partner.assert_called_once_with("partner-001")
    
    @patch('collective.api.processing.processing_service')
    def test_get_nonexistent_partner(self, mock_service):
        """Test retrieving a non-existent partner returns 404"""
        mock_service.get_partner.return_value = None
        
        # Make request
        response = client.get("/api/processing-partners/nonexistent-id")
        
        # Verify 404 response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('collective.api.processing.processing_service')
    def test_get_partner_with_all_fields(self, mock_service):
        """Test that all partner fields are returned correctly"""
        mock_partner = ProcessingPartner(
            partner_id="partner-002",
            partner_name="Complete Partner",
            contact_details={
                "phone": "+91-1234567890",
                "email": "test@example.com",
                "contact_person": "John Doe"
            },
            facility_location="Delhi",
            rates_by_crop={
                "tomato": Decimal("20.00"),
                "potato": Decimal("15.00"),
                "onion": Decimal("12.50")
            },
            capacity_by_crop={
                "tomato": Decimal("300"),
                "potato": Decimal("500"),
                "onion": Decimal("400")
            },
            quality_requirements={
                "tomato": "Grade A",
                "potato": "Grade A or B",
                "onion": "Grade B or better"
            },
            pickup_schedule="Twice weekly"
        )
        
        mock_service.get_partner.return_value = mock_partner
        
        response = client.get("/api/processing-partners/partner-002")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["rates_by_crop"]) == 3
        assert len(data["capacity_by_crop"]) == 3
        assert len(data["quality_requirements"]) == 3


class TestUpdateProcessingPartner:
    """Test PUT /api/processing-partners/{partner_id} endpoint (Requirement 5.3)"""
    
    @patch('collective.api.processing.processing_service')
    def test_update_partner_name(self, mock_service):
        """Test updating partner name"""
        updated_partner = ProcessingPartner(
            partner_id="partner-003",
            partner_name="Updated Partner Name",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Mumbai",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={"tomato": Decimal("500")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        # Make request
        response = client.put(
            "/api/processing-partners/partner-003",
            json={"partner_name": "Updated Partner Name"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["partner_name"] == "Updated Partner Name"
        
        # Verify service was called with correct parameters
        mock_service.update_partner.assert_called_once()
        call_args = mock_service.update_partner.call_args
        assert call_args[0][0] == "partner-003"
        assert call_args[1]["partner_name"] == "Updated Partner Name"
    
    @patch('collective.api.processing.processing_service')
    def test_update_rates_by_crop(self, mock_service):
        """Test updating rates by crop"""
        updated_partner = ProcessingPartner(
            partner_id="partner-004",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Delhi",
            rates_by_crop={
                "tomato": Decimal("30.00"),
                "potato": Decimal("20.00")
            },
            capacity_by_crop={"tomato": Decimal("500")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        response = client.put(
            "/api/processing-partners/partner-004",
            json={
                "rates_by_crop": {
                    "tomato": 30.00,
                    "potato": 20.00
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rates_by_crop"]["tomato"] == "30.00"
        assert data["rates_by_crop"]["potato"] == "20.00"
    
    @patch('collective.api.processing.processing_service')
    def test_update_capacity_by_crop(self, mock_service):
        """Test updating capacity by crop"""
        updated_partner = ProcessingPartner(
            partner_id="partner-005",
            partner_name="Test Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Bangalore",
            rates_by_crop={"tomato": Decimal("25.00")},
            capacity_by_crop={
                "tomato": Decimal("800"),
                "potato": Decimal("1200")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        response = client.put(
            "/api/processing-partners/partner-005",
            json={
                "capacity_by_crop": {
                    "tomato": 800,
                    "potato": 1200
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["capacity_by_crop"]["tomato"] == "800"
        assert data["capacity_by_crop"]["potato"] == "1200"
    
    @patch('collective.api.processing.processing_service')
    def test_update_multiple_fields(self, mock_service):
        """Test updating multiple fields at once"""
        updated_partner = ProcessingPartner(
            partner_id="partner-006",
            partner_name="Multi Update Partner",
            contact_details={
                "phone": "+91-9999999999",
                "email": "updated@example.com"
            },
            facility_location="Chennai",
            rates_by_crop={"tomato": Decimal("28.00")},
            capacity_by_crop={"tomato": Decimal("600")},
            quality_requirements={"tomato": "Grade A only"},
            pickup_schedule="Daily 7:00 AM"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        response = client.put(
            "/api/processing-partners/partner-006",
            json={
                "partner_name": "Multi Update Partner",
                "contact_details": {
                    "phone": "+91-9999999999",
                    "email": "updated@example.com"
                },
                "pickup_schedule": "Daily 7:00 AM"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["partner_name"] == "Multi Update Partner"
        assert data["contact_details"]["phone"] == "+91-9999999999"
        assert data["pickup_schedule"] == "Daily 7:00 AM"
    
    @patch('collective.api.processing.processing_service')
    def test_update_nonexistent_partner(self, mock_service):
        """Test updating a non-existent partner returns 404"""
        mock_service.update_partner.side_effect = ValueError("Processing partner not found: nonexistent-id")
        
        response = client.put(
            "/api/processing-partners/nonexistent-id",
            json={"partner_name": "New Name"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('collective.api.processing.processing_service')
    def test_update_with_invalid_rate(self, mock_service):
        """Test updating with invalid rate returns 400"""
        mock_service.update_partner.side_effect = ValueError("Rate for tomato must be positive")
        
        response = client.put(
            "/api/processing-partners/partner-007",
            json={
                "rates_by_crop": {
                    "tomato": -10.00
                }
            }
        )
        
        assert response.status_code == 400
        assert "positive" in response.json()["detail"].lower()
    
    @patch('collective.api.processing.processing_service')
    def test_update_with_invalid_capacity(self, mock_service):
        """Test updating with invalid capacity returns 400"""
        mock_service.update_partner.side_effect = ValueError("Capacity for potato cannot be negative")
        
        response = client.put(
            "/api/processing-partners/partner-008",
            json={
                "capacity_by_crop": {
                    "potato": -100
                }
            }
        )
        
        assert response.status_code == 400
        assert "negative" in response.json()["detail"].lower()
    
    @patch('collective.api.processing.processing_service')
    def test_update_with_empty_body(self, mock_service):
        """Test updating with empty body (no fields to update)"""
        existing_partner = ProcessingPartner(
            partner_id="partner-009",
            partner_name="Unchanged Partner",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Pune",
            rates_by_crop={"tomato": Decimal("22.00")},
            capacity_by_crop={"tomato": Decimal("400")},
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.update_partner.return_value = existing_partner
        
        response = client.put(
            "/api/processing-partners/partner-009",
            json={}
        )
        
        # Should succeed but not change anything
        assert response.status_code == 200
        data = response.json()
        assert data["partner_name"] == "Unchanged Partner"


class TestDeleteProcessingPartner:
    """Test DELETE /api/processing-partners/{partner_id} endpoint (Requirement 5.4)"""
    
    @patch('collective.api.processing.processing_service')
    def test_delete_existing_partner(self, mock_service):
        """Test deleting an existing processing partner"""
        mock_service.delete_partner.return_value = None
        
        # Make request
        response = client.delete("/api/processing-partners/partner-010")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
        assert "partner-010" in data["message"]
        
        # Verify service was called correctly
        mock_service.delete_partner.assert_called_once_with("partner-010")
    
    @patch('collective.api.processing.processing_service')
    def test_delete_nonexistent_partner(self, mock_service):
        """Test deleting a non-existent partner returns 404"""
        mock_service.delete_partner.side_effect = ValueError("Processing partner not found: nonexistent-id")
        
        response = client.delete("/api/processing-partners/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('collective.api.processing.processing_service')
    def test_delete_partner_idempotency(self, mock_service):
        """Test that deleting the same partner twice returns 404 on second attempt"""
        # First delete succeeds
        mock_service.delete_partner.return_value = None
        response1 = client.delete("/api/processing-partners/partner-011")
        assert response1.status_code == 200
        
        # Second delete fails (partner no longer exists)
        mock_service.delete_partner.side_effect = ValueError("Processing partner not found: partner-011")
        response2 = client.delete("/api/processing-partners/partner-011")
        assert response2.status_code == 404


class TestProcessingPartnerAPIRequirements:
    """Test that API endpoints meet requirements"""
    
    @patch('collective.api.processing.processing_service')
    def test_requirement_5_2_get_partner_terms(self, mock_service):
        """
        Requirement 5.2: WHEN setting partner terms, THE System SHALL store 
        pre-agreed rates by crop type
        
        Verify GET endpoint returns rates by crop type
        """
        mock_partner = ProcessingPartner(
            partner_id="req-partner-001",
            partner_name="Requirement Test",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={
                "tomato": Decimal("25.00"),
                "potato": Decimal("18.00")
            },
            capacity_by_crop={
                "tomato": Decimal("500"),
                "potato": Decimal("800")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.get_partner.return_value = mock_partner
        
        response = client.get("/api/processing-partners/req-partner-001")
        
        assert response.status_code == 200
        data = response.json()
        assert "rates_by_crop" in data
        assert "tomato" in data["rates_by_crop"]
        assert "potato" in data["rates_by_crop"]
    
    @patch('collective.api.processing.processing_service')
    def test_requirement_5_3_update_capacity_limits(self, mock_service):
        """
        Requirement 5.3: WHEN setting partner terms, THE System SHALL store 
        daily or weekly capacity limits by crop type
        
        Verify PUT endpoint can update capacity limits
        """
        updated_partner = ProcessingPartner(
            partner_id="req-partner-002",
            partner_name="Capacity Test",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("20.00")},
            capacity_by_crop={
                "tomato": Decimal("1000"),
                "potato": Decimal("1500")
            },
            quality_requirements={},
            pickup_schedule="Daily"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        response = client.put(
            "/api/processing-partners/req-partner-002",
            json={
                "capacity_by_crop": {
                    "tomato": 1000,
                    "potato": 1500
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "capacity_by_crop" in data
        assert data["capacity_by_crop"]["tomato"] == "1000"
        assert data["capacity_by_crop"]["potato"] == "1500"
    
    @patch('collective.api.processing.processing_service')
    def test_requirement_5_4_update_quality_requirements(self, mock_service):
        """
        Requirement 5.4: WHEN setting partner terms, THE System SHALL store 
        quality requirements and pickup schedule
        
        Verify PUT endpoint can update quality requirements and pickup schedule
        """
        updated_partner = ProcessingPartner(
            partner_id="req-partner-003",
            partner_name="Quality Test",
            contact_details={"phone": "+91-1234567890"},
            facility_location="Test Location",
            rates_by_crop={"tomato": Decimal("22.00")},
            capacity_by_crop={"tomato": Decimal("600")},
            quality_requirements={
                "tomato": "Grade A only",
                "potato": "Grade A or B"
            },
            pickup_schedule="Twice weekly - Monday and Thursday"
        )
        
        mock_service.update_partner.return_value = updated_partner
        
        response = client.put(
            "/api/processing-partners/req-partner-003",
            json={
                "quality_requirements": {
                    "tomato": "Grade A only",
                    "potato": "Grade A or B"
                },
                "pickup_schedule": "Twice weekly - Monday and Thursday"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quality_requirements" in data
        assert "pickup_schedule" in data
        assert data["quality_requirements"]["tomato"] == "Grade A only"
        assert data["pickup_schedule"] == "Twice weekly - Monday and Thursday"
