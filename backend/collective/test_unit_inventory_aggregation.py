"""
Unit tests for inventory aggregation

Tests contribution validation, concurrent updates, and error handling.
Validates Requirement 1.5: quantity validation and crop type recognition.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import uuid

from backend.collective.models import (
    CollectiveInventory,
    FarmerContribution,
    QualityGrade,
)
from backend.collective.services import InventoryService
from backend.collective.db import InventoryRepository


class TestContributionValidation:
    """Test contribution validation logic"""
    
    def test_positive_quantity_validation(self):
        """Test that positive quantities are accepted"""
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("100.5"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=False,
        )
        
        assert contribution.quantity_kg == Decimal("100.5")
    
    def test_negative_quantity_rejected(self):
        """Test that negative quantities are rejected"""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("-10"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            )
    
    def test_zero_quantity_rejected(self):
        """Test that zero quantities are rejected"""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("0"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            )
    
    def test_quality_grade_validation(self):
        """Test that quality grades are validated"""
        # Valid grades
        for grade in ["A", "B", "C"]:
            contribution = FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("100"),
                quality_grade=grade,
                timestamp=datetime.now(),
                allocated=False,
            )
            assert contribution.quality_grade.value == grade
    
    def test_invalid_quality_grade_rejected(self):
        """Test that invalid quality grades are rejected"""
        with pytest.raises(ValueError):
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("100"),
                quality_grade="D",  # Invalid grade
                timestamp=datetime.now(),
                allocated=False,
            )
    
    def test_crop_type_validation_in_inventory(self):
        """Test that crop type mismatch is detected when adding to inventory"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("0"),
            available_quantity_kg=Decimal("0"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="onion",  # Different crop type
            quantity_kg=Decimal("100"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=False,
        )
        
        with pytest.raises(ValueError, match="Crop type mismatch"):
            inventory.add_contribution(contribution)


class TestConcurrentUpdates:
    """Test concurrent update handling"""
    
    def test_atomic_contribution_addition(self):
        """Test that contributions are added atomically"""
        # Mock repository with atomic update
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.add_contribution = Mock()
        mock_repo.get_inventory = Mock(return_value=CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("100"),
            available_quantity_kg=Decimal("100"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        ))
        
        service = InventoryService(repository=mock_repo)
        
        # Add contribution
        contribution = service.aggregate_farmer_contribution(
            fpo_id="FPO001",
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade="A",
        )
        
        # Verify atomic update was called
        mock_repo.add_contribution.assert_called_once()
        assert contribution.quantity_kg == Decimal("50")
    
    def test_multiple_concurrent_contributions(self):
        """Test that multiple concurrent contributions maintain consistency"""
        # Create inventory with initial state
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("0"),
            available_quantity_kg=Decimal("0"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Simulate concurrent contributions
        contributions = [
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id=f"F{i:03d}",
                farmer_name=f"Farmer {i}",
                crop_type="tomato",
                quantity_kg=Decimal("10"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            )
            for i in range(10)
        ]
        
        # Add all contributions
        for contribution in contributions:
            inventory.add_contribution(contribution)
        
        # Verify total is correct
        assert inventory.total_quantity_kg == Decimal("100")
        assert inventory.available_quantity_kg == Decimal("100")
        assert len(inventory.contributions) == 10
        
        # Verify invariants hold
        inventory.validate_invariants()
    
    def test_concurrent_reserve_and_allocate(self):
        """Test that reserve and allocate operations maintain consistency"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("100"),
            available_quantity_kg=Decimal("100"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Reserve some quantity
        inventory.reserve_quantity(Decimal("30"))
        assert inventory.available_quantity_kg == Decimal("70")
        assert inventory.reserved_quantity_kg == Decimal("30")
        
        # Allocate some quantity
        inventory.allocate_quantity(Decimal("40"))
        assert inventory.available_quantity_kg == Decimal("30")
        assert inventory.allocated_quantity_kg == Decimal("40")
        
        # Verify invariants
        inventory.validate_invariants()
        assert inventory.total_quantity_kg == Decimal("100")


class TestErrorHandling:
    """Test error handling in inventory operations"""
    
    def test_insufficient_inventory_for_reservation(self):
        """Test error when trying to reserve more than available"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("50"),
            available_quantity_kg=Decimal("50"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        with pytest.raises(ValueError, match="Cannot reserve"):
            inventory.reserve_quantity(Decimal("100"))
    
    def test_insufficient_inventory_for_allocation(self):
        """Test error when trying to allocate more than available"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("50"),
            available_quantity_kg=Decimal("50"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        with pytest.raises(ValueError, match="Cannot allocate"):
            inventory.allocate_quantity(Decimal("100"))
    
    def test_service_handles_missing_inventory(self):
        """Test service handles missing inventory gracefully"""
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.get_inventory = Mock(return_value=None)
        
        service = InventoryService(repository=mock_repo)
        
        with pytest.raises(ValueError, match="No inventory found"):
            service.reserve_inventory("FPO001", "tomato", Decimal("10"))
    
    def test_service_handles_repository_errors(self):
        """Test service handles repository errors"""
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.add_contribution = Mock(side_effect=Exception("Database error"))
        
        service = InventoryService(repository=mock_repo)
        
        with pytest.raises(Exception, match="Database error"):
            service.aggregate_farmer_contribution(
                fpo_id="FPO001",
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("50"),
                quality_grade="A",
            )
    
    def test_inventory_conservation_violation_detected(self):
        """Test that inventory conservation violations are detected"""
        with pytest.raises(ValueError, match="Inventory conservation violated"):
            CollectiveInventory(
                fpo_id="FPO001",
                crop_type="tomato",
                total_quantity_kg=Decimal("100"),
                available_quantity_kg=Decimal("50"),
                reserved_quantity_kg=Decimal("30"),
                allocated_quantity_kg=Decimal("30"),  # 50+30+30 = 110 > 100
                contributions=[],
                last_updated=datetime.now(),
            )
    
    def test_negative_quantity_validation(self):
        """Test that negative quantities are rejected in inventory"""
        with pytest.raises(ValueError, match="cannot be negative"):
            CollectiveInventory(
                fpo_id="FPO001",
                crop_type="tomato",
                total_quantity_kg=Decimal("-10"),
                available_quantity_kg=Decimal("0"),
                reserved_quantity_kg=Decimal("0"),
                allocated_quantity_kg=Decimal("0"),
                contributions=[],
                last_updated=datetime.now(),
            )
    
    def test_contribution_aggregation_mismatch_detected(self):
        """Test that contribution aggregation mismatches are detected"""
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=False,
        )
        
        with pytest.raises(ValueError, match="Contribution aggregation violated"):
            CollectiveInventory(
                fpo_id="FPO001",
                crop_type="tomato",
                total_quantity_kg=Decimal("100"),  # Mismatch: should be 50
                available_quantity_kg=Decimal("100"),
                reserved_quantity_kg=Decimal("0"),
                allocated_quantity_kg=Decimal("0"),
                contributions=[contribution],
                last_updated=datetime.now(),
            )


class TestInventoryService:
    """Test InventoryService integration"""
    
    def test_get_or_create_inventory_creates_new(self):
        """Test that get_or_create creates new inventory when none exists"""
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.get_inventory = Mock(return_value=None)
        mock_repo.save_inventory = Mock()
        
        service = InventoryService(repository=mock_repo)
        inventory = service.get_or_create_inventory("FPO001", "tomato")
        
        assert inventory.fpo_id == "FPO001"
        assert inventory.crop_type == "tomato"
        assert inventory.total_quantity_kg == Decimal("0")
        mock_repo.save_inventory.assert_called_once()
    
    def test_get_or_create_inventory_returns_existing(self):
        """Test that get_or_create returns existing inventory"""
        existing_inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("100"),
            available_quantity_kg=Decimal("100"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.get_inventory = Mock(return_value=existing_inventory)
        
        service = InventoryService(repository=mock_repo)
        inventory = service.get_or_create_inventory("FPO001", "tomato")
        
        assert inventory.total_quantity_kg == Decimal("100")
    
    def test_get_inventory_breakdown_with_contributions(self):
        """Test inventory breakdown includes farmer contributions"""
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=False,
        )
        
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("50"),
            available_quantity_kg=Decimal("50"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[contribution],
            last_updated=datetime.now(),
        )
        
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.get_inventory = Mock(return_value=inventory)
        
        service = InventoryService(repository=mock_repo)
        breakdown = service.get_inventory_breakdown("FPO001", "tomato")
        
        assert breakdown["farmer_count"] == 1
        assert len(breakdown["contributions"]) == 1
        assert breakdown["contributions"][0]["farmer_id"] == "F001"
        assert breakdown["contributions"][0]["quantity_kg"] == "50"
    
    def test_get_inventory_breakdown_empty(self):
        """Test inventory breakdown when no inventory exists"""
        mock_repo = Mock(spec=InventoryRepository)
        mock_repo.get_inventory = Mock(return_value=None)
        
        service = InventoryService(repository=mock_repo)
        breakdown = service.get_inventory_breakdown("FPO001", "tomato")
        
        assert breakdown["farmer_count"] == 0
        assert breakdown["total_quantity_kg"] == "0"
        assert len(breakdown["contributions"]) == 0
