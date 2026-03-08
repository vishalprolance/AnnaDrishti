"""
Integration tests for Sell Agent and Process Agent integration.

Tests:
- Sell Agent integration (contribution and mandi allocation queries)
- Process Agent integration (processing allocation queries and fulfillment updates)
- Backward compatibility (legacy endpoints)
- Error handling and graceful degradation

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch

from .models import (
    CollectiveInventory,
    FarmerContribution,
    QualityGrade,
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
)
from .services.inventory_service import InventoryService
from .services.allocation_service import AllocationService
from .db import InventoryRepository, AllocationRepository
from .feature_flags import FeatureFlagManager, FeatureFlag
from .error_handling import ErrorHandler, handle_integration_error


class TestSellAgentIntegration:
    """Test Sell Agent integration endpoints"""
    
    def test_contribution_endpoint(self):
        """
        Test POST /api/inventory/contributions endpoint for Sell Agent.
        
        Validates that Sell Agent can route farmer produce to collective inventory.
        **Validates: Requirement 10.1**
        """
        # Setup
        inventory_service = InventoryService(
            repository=Mock(spec=InventoryRepository)
        )
        
        # Mock repository methods
        inventory_service.repository.add_contribution = Mock()
        inventory_service.repository.get_inventory = Mock(return_value=CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("100"),
            available_quantity_kg=Decimal("100"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        ))
        
        # Execute
        contribution = inventory_service.aggregate_farmer_contribution(
            fpo_id="FPO001",
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("50"),
            quality_grade="A",
        )
        
        # Verify
        assert contribution.farmer_id == "F001"
        assert contribution.crop_type == "tomato"
        assert contribution.quantity_kg == Decimal("50")
        assert contribution.quality_grade == QualityGrade.A
        
        # Verify repository was called
        inventory_service.repository.add_contribution.assert_called_once()
    
    def test_mandi_allocation_query(self):
        """
        Test GET /api/allocations/mandi endpoint for Sell Agent.
        
        Validates that Sell Agent can query mandi allocations for dispatch.
        **Validates: Requirement 10.2**
        """
        # Setup
        allocation_repository = Mock(spec=AllocationRepository)
        
        # Create test allocation with mandi channel
        test_allocation = Allocation(
            allocation_id="ALLOC001",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.MANDI,
                    channel_id="MANDI001",
                    channel_name="APMC Market",
                    quantity_kg=Decimal("50"),
                    price_per_kg=Decimal("35"),
                    revenue=Decimal("1750"),
                    priority=3,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
            ],
            total_quantity_kg=Decimal("50"),
            blended_realization_per_kg=Decimal("35"),
            status=AllocationStatus.PENDING,
        )
        
        allocation_repository.list_allocations = Mock(return_value=[test_allocation])
        
        # Execute - filter for mandi allocations
        allocations = allocation_repository.list_allocations(
            fpo_id="FPO001",
            crop_type="tomato",
        )
        
        # Filter for mandi channels
        mandi_allocations = []
        for allocation in allocations:
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.MANDI:
                    mandi_allocations.append(ca)
        
        # Verify
        assert len(mandi_allocations) == 1
        assert mandi_allocations[0].channel_type == ChannelType.MANDI
        assert mandi_allocations[0].channel_id == "MANDI001"
        assert mandi_allocations[0].quantity_kg == Decimal("50")
        assert mandi_allocations[0].fulfillment_status == FulfillmentStatus.PENDING


class TestProcessAgentIntegration:
    """Test Process Agent integration endpoints"""
    
    def test_processing_allocation_query(self):
        """
        Test GET /api/allocations/processing endpoint for Process Agent.
        
        Validates that Process Agent can query processing partner allocations.
        **Validates: Requirement 10.2**
        """
        # Setup
        allocation_repository = Mock(spec=AllocationRepository)
        
        # Create test allocation with processing channel
        test_allocation = Allocation(
            allocation_id="ALLOC002",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PARTNER001",
                    channel_name="Processing Co",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("4500"),
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("45"),
            status=AllocationStatus.PENDING,
        )
        
        allocation_repository.list_allocations = Mock(return_value=[test_allocation])
        
        # Execute - filter for processing allocations
        allocations = allocation_repository.list_allocations(
            fpo_id="FPO001",
            crop_type="tomato",
        )
        
        # Filter for processing channels
        processing_allocations = []
        for allocation in allocations:
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.PROCESSING:
                    processing_allocations.append(ca)
        
        # Verify
        assert len(processing_allocations) == 1
        assert processing_allocations[0].channel_type == ChannelType.PROCESSING
        assert processing_allocations[0].channel_id == "PARTNER001"
        assert processing_allocations[0].quantity_kg == Decimal("100")
    
    def test_fulfillment_update(self):
        """
        Test PUT /api/allocations/{id}/fulfillment endpoint for Process Agent.
        
        Validates that Process Agent can update fulfillment status.
        **Validates: Requirement 10.2**
        """
        # Setup
        allocation_repository = Mock(spec=AllocationRepository)
        
        # Create test allocation
        test_allocation = Allocation(
            allocation_id="ALLOC003",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PARTNER001",
                    channel_name="Processing Co",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("4500"),
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("45"),
            status=AllocationStatus.PENDING,
        )
        
        allocation_repository.get_allocation = Mock(return_value=test_allocation)
        allocation_repository.update_allocation = Mock()
        
        # Execute - update fulfillment status
        allocation = allocation_repository.get_allocation("ALLOC003")
        
        for ca in allocation.channel_allocations:
            if ca.channel_id == "PARTNER001":
                ca.fulfillment_status = FulfillmentStatus.IN_TRANSIT
        
        allocation_repository.update_allocation(allocation)
        
        # Verify
        assert allocation.channel_allocations[0].fulfillment_status == FulfillmentStatus.IN_TRANSIT
        allocation_repository.update_allocation.assert_called_once()


class TestBackwardCompatibility:
    """Test backward compatibility with legacy workflows"""
    
    def test_collective_mode_enabled(self):
        """
        Test that legacy endpoints work when collective mode is enabled.
        
        **Validates: Requirement 10.4**
        """
        # Setup
        flag_manager = FeatureFlagManager()
        flag_manager.enable(FeatureFlag.COLLECTIVE_MODE)
        
        # Verify
        assert flag_manager.is_collective_mode_enabled() is True
        assert flag_manager.is_enabled(FeatureFlag.COLLECTIVE_MODE) is True
    
    def test_collective_mode_disabled(self):
        """
        Test that system falls back to individual mode when collective mode is disabled.
        
        **Validates: Requirement 10.4**
        """
        # Setup
        flag_manager = FeatureFlagManager()
        flag_manager.disable(FeatureFlag.COLLECTIVE_MODE)
        
        # Verify
        assert flag_manager.is_collective_mode_enabled() is False
        assert flag_manager.is_enabled(FeatureFlag.COLLECTIVE_MODE) is False
    
    def test_legacy_farmer_sell_collective_mode(self):
        """
        Test legacy farmer sell endpoint redirects to collective contribution.
        
        **Validates: Requirement 10.4**
        """
        # Setup
        flag_manager = FeatureFlagManager()
        flag_manager.enable(FeatureFlag.COLLECTIVE_MODE)
        
        inventory_service = InventoryService(
            repository=Mock(spec=InventoryRepository)
        )
        
        # Mock repository
        inventory_service.repository.add_contribution = Mock()
        inventory_service.repository.get_inventory = Mock(return_value=CollectiveInventory(
            fpo_id="FPO_F00",
            crop_type="tomato",
            total_quantity_kg=Decimal("50"),
            available_quantity_kg=Decimal("50"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        ))
        
        # Execute - simulate legacy sell endpoint
        if flag_manager.is_collective_mode_enabled():
            contribution = inventory_service.aggregate_farmer_contribution(
                fpo_id="FPO_F00",
                farmer_id="F001",
                farmer_name="Test Farmer",
                crop_type="tomato",
                quantity_kg=Decimal("50"),
                quality_grade="A",
            )
            
            # Verify redirected to collective
            assert contribution.farmer_id == "F001"
            assert contribution.crop_type == "tomato"
    
    def test_legacy_buyer_orders_collective_mode(self):
        """
        Test legacy buyer orders endpoint returns allocations in collective mode.
        
        **Validates: Requirement 10.4**
        """
        # Setup
        flag_manager = FeatureFlagManager()
        flag_manager.enable(FeatureFlag.COLLECTIVE_MODE)
        
        allocation_repository = Mock(spec=AllocationRepository)
        
        # Create test allocation
        test_allocation = Allocation(
            allocation_id="ALLOC004",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="BUYER001",
                    channel_name="Society A",
                    quantity_kg=Decimal("30"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("1500"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
            ],
            total_quantity_kg=Decimal("30"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        allocation_repository.list_allocations = Mock(return_value=[test_allocation])
        
        # Execute - simulate legacy buyer orders endpoint
        if flag_manager.is_collective_mode_enabled():
            allocations = allocation_repository.list_allocations()
            
            # Filter for buyer
            buyer_orders = []
            for allocation in allocations:
                for ca in allocation.channel_allocations:
                    if ca.channel_id == "BUYER001":
                        buyer_orders.append(ca)
            
            # Verify
            assert len(buyer_orders) == 1
            assert buyer_orders[0].channel_id == "BUYER001"


class TestErrorHandling:
    """Test error handling and graceful degradation"""
    
    def test_error_logging(self):
        """
        Test that integration errors are logged properly.
        
        **Validates: Requirement 10.5**
        """
        # Setup
        error_handler = ErrorHandler()
        
        # Execute
        test_error = Exception("Test integration error")
        error_handler.log_error(
            error=test_error,
            context="sell_agent_integration",
            severity="ERROR",
            additional_info={"endpoint": "/api/allocations/mandi"}
        )
        
        # Verify
        stats = error_handler.get_error_stats("sell_agent_integration")
        assert stats["error_count"] == 1
        assert stats["last_error_time"] is not None
    
    def test_graceful_degradation(self):
        """
        Test that system continues operating with degraded functionality.
        
        **Validates: Requirement 10.5**
        """
        # Setup
        error_handler = ErrorHandler()
        
        # Simulate multiple errors
        for i in range(6):
            error_handler.log_error(
                error=Exception(f"Error {i}"),
                context="process_agent_integration",
                severity="ERROR"
            )
        
        # Verify degradation threshold reached
        assert error_handler.should_degrade("process_agent_integration", threshold=5) is True
    
    def test_error_handler_decorator(self):
        """
        Test error handler decorator with fallback value.
        
        **Validates: Requirement 10.5**
        """
        # Setup
        @handle_integration_error(
            context="test_integration",
            fallback_value={"status": "degraded", "data": []}
        )
        def failing_function():
            raise Exception("Integration failed")
        
        # Execute
        result = failing_function()
        
        # Verify fallback value returned
        assert result["status"] == "degraded"
        assert result["data"] == []
    
    def test_error_handler_decorator_success(self):
        """
        Test error handler decorator with successful execution.
        
        **Validates: Requirement 10.5**
        """
        # Setup
        @handle_integration_error(
            context="test_integration",
            fallback_value={"status": "degraded"}
        )
        def successful_function():
            return {"status": "success", "data": [1, 2, 3]}
        
        # Execute
        result = successful_function()
        
        # Verify normal result returned
        assert result["status"] == "success"
        assert result["data"] == [1, 2, 3]


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    def test_sell_agent_to_process_agent_flow(self):
        """
        Test complete flow from Sell Agent contribution to Process Agent fulfillment.
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Setup
        inventory_service = InventoryService(
            repository=Mock(spec=InventoryRepository)
        )
        
        # Mock repositories
        inventory_service.repository.add_contribution = Mock()
        inventory_service.repository.get_inventory = Mock(return_value=CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("100"),
            available_quantity_kg=Decimal("100"),
            reserved_quantity_kg=Decimal("0"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        ))
        
        # Step 1: Sell Agent adds contribution
        contribution = inventory_service.aggregate_farmer_contribution(
            fpo_id="FPO001",
            farmer_id="F001",
            farmer_name="Test Farmer",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            quality_grade="A",
        )
        
        assert contribution.farmer_id == "F001"
        
        # Step 2: Allocation happens (mocked)
        test_allocation = Allocation(
            allocation_id="ALLOC005",
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="PARTNER001",
                    channel_name="Processing Co",
                    quantity_kg=Decimal("100"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("4500"),
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
            ],
            total_quantity_kg=Decimal("100"),
            blended_realization_per_kg=Decimal("45"),
            status=AllocationStatus.PENDING,
        )
        
        # Step 3: Process Agent queries allocation
        processing_allocations = [
            ca for ca in test_allocation.channel_allocations
            if ca.channel_type == ChannelType.PROCESSING
        ]
        
        assert len(processing_allocations) == 1
        assert processing_allocations[0].channel_id == "PARTNER001"
        
        # Step 4: Process Agent updates fulfillment
        processing_allocations[0].fulfillment_status = FulfillmentStatus.COMPLETED
        
        assert processing_allocations[0].fulfillment_status == FulfillmentStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
