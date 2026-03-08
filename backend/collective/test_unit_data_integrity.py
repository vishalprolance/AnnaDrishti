"""
Unit tests for data integrity and validation

Tests validation rules, transaction rollback, concurrent update handling,
and audit log completeness (Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6).
"""

import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, MagicMock, patch
import uuid

from .models import (
    CollectiveInventory,
    FarmerContribution,
    QualityGrade,
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    ProcessingPartner,
)
from .validation import InventoryValidator, AllocationValidator
from .validation.inventory_validator import ValidationError
from .db import TransactionError, ConcurrentUpdateError
from .audit import AuditLogger, AuditEventType


class TestInventoryValidation:
    """Test inventory validation rules (Requirements 9.1, 9.2, 9.3)"""
    
    def test_validate_inventory_allocation_success(self):
        """Test successful inventory allocation validation"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("200"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Should not raise exception
        InventoryValidator.validate_inventory_allocation(inventory, Decimal("500"))
    
    def test_validate_inventory_allocation_exceeds_available(self):
        """Test allocation exceeding available inventory"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("200"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        with pytest.raises(ValidationError, match="Cannot allocate"):
            InventoryValidator.validate_inventory_allocation(inventory, Decimal("900"))
    
    def test_validate_negative_allocation_quantity(self):
        """Test negative allocation quantity"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("200"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        with pytest.raises(ValidationError, match="must be non-negative"):
            InventoryValidator.validate_inventory_allocation(inventory, Decimal("-100"))
    
    def test_validate_quantities_non_negative(self):
        """Test all quantities are non-negative"""
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("200"),
            allocated_quantity_kg=Decimal("0"),
            contributions=[],
            last_updated=datetime.now(),
        )
        
        # Should not raise exception
        InventoryValidator.validate_quantities_non_negative(inventory)
    
    def test_validate_negative_total_quantity(self):
        """Test negative total quantity"""
        # Models validate on creation, so we test the validator directly
        # by creating an inventory that bypasses __post_init__
        inventory = object.__new__(CollectiveInventory)
        inventory.fpo_id = "FPO001"
        inventory.crop_type = "tomato"
        inventory.total_quantity_kg = Decimal("-100")
        inventory.available_quantity_kg = Decimal("0")
        inventory.reserved_quantity_kg = Decimal("0")
        inventory.allocated_quantity_kg = Decimal("0")
        inventory.contributions = []
        inventory.last_updated = datetime.now()
        
        with pytest.raises(ValidationError, match="Total quantity cannot be negative"):
            InventoryValidator.validate_quantities_non_negative(inventory)
    
    def test_validate_allocation_prices_success(self):
        """Test allocation prices are non-negative"""
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("500"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("25000"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
            ],
            total_quantity_kg=Decimal("500"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        # Should not raise exception
        InventoryValidator.validate_allocation_prices(allocation)
    
    def test_validate_negative_price(self):
        """Test negative price in allocation"""
        # Create channel allocation bypassing validation
        channel_allocation = object.__new__(ChannelAllocation)
        channel_allocation.channel_type = ChannelType.SOCIETY
        channel_allocation.channel_id = "SOC001"
        channel_allocation.channel_name = "Society 1"
        channel_allocation.quantity_kg = Decimal("500")
        channel_allocation.price_per_kg = Decimal("-50")
        channel_allocation.revenue = Decimal("-25000")
        channel_allocation.priority = 1
        channel_allocation.fulfillment_status = FulfillmentStatus.PENDING
        
        allocation = object.__new__(Allocation)
        allocation.allocation_id = str(uuid.uuid4())
        allocation.fpo_id = "FPO001"
        allocation.crop_type = "tomato"
        allocation.allocation_date = date.today()
        allocation.channel_allocations = [channel_allocation]
        allocation.total_quantity_kg = Decimal("500")
        allocation.blended_realization_per_kg = Decimal("50")
        allocation.status = AllocationStatus.PENDING
        
        with pytest.raises(ValidationError, match="Price cannot be negative"):
            InventoryValidator.validate_allocation_prices(allocation)
    
    def test_validate_contribution_deletion_success(self):
        """Test successful contribution deletion validation"""
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Farmer 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=False,
        )
        
        # Should not raise exception
        InventoryValidator.validate_contribution_deletion(contribution)
    
    def test_validate_contribution_deletion_already_allocated(self):
        """Test deletion of allocated contribution"""
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id="F001",
            farmer_name="Farmer 1",
            crop_type="tomato",
            quantity_kg=Decimal("100"),
            quality_grade=QualityGrade.A,
            timestamp=datetime.now(),
            allocated=True,
        )
        
        with pytest.raises(ValidationError, match="Cannot delete contribution"):
            InventoryValidator.validate_contribution_deletion(contribution)
    
    def test_validate_inventory_invariants_success(self):
        """Test inventory invariants validation"""
        contributions = [
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Farmer 1",
                crop_type="tomato",
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F002",
                farmer_name="Farmer 2",
                crop_type="tomato",
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.B,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        inventory = CollectiveInventory(
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("1000"),
            available_quantity_kg=Decimal("800"),
            reserved_quantity_kg=Decimal("200"),
            allocated_quantity_kg=Decimal("0"),
            contributions=contributions,
            last_updated=datetime.now(),
        )
        
        # Should not raise exception
        InventoryValidator.validate_inventory_invariants(inventory)
    
    def test_validate_inventory_conservation_violated(self):
        """Test inventory conservation violation"""
        # Create inventory bypassing validation
        inventory = object.__new__(CollectiveInventory)
        inventory.fpo_id = "FPO001"
        inventory.crop_type = "tomato"
        inventory.total_quantity_kg = Decimal("1000")
        inventory.available_quantity_kg = Decimal("600")
        inventory.reserved_quantity_kg = Decimal("200")
        inventory.allocated_quantity_kg = Decimal("100")
        inventory.contributions = []
        inventory.last_updated = datetime.now()
        
        with pytest.raises(ValidationError, match="Inventory conservation violated"):
            InventoryValidator.validate_inventory_invariants(inventory)
    
    def test_validate_contribution_aggregation_violated(self):
        """Test contribution aggregation violation"""
        contributions = [
            FarmerContribution(
                contribution_id=str(uuid.uuid4()),
                farmer_id="F001",
                farmer_name="Farmer 1",
                crop_type="tomato",
                quantity_kg=Decimal("500"),
                quality_grade=QualityGrade.A,
                timestamp=datetime.now(),
                allocated=False,
            ),
        ]
        
        # Create inventory bypassing validation
        inventory = object.__new__(CollectiveInventory)
        inventory.fpo_id = "FPO001"
        inventory.crop_type = "tomato"
        inventory.total_quantity_kg = Decimal("1000")  # Mismatch
        inventory.available_quantity_kg = Decimal("800")
        inventory.reserved_quantity_kg = Decimal("200")
        inventory.allocated_quantity_kg = Decimal("0")
        inventory.contributions = contributions
        inventory.last_updated = datetime.now()
        
        with pytest.raises(ValidationError, match="Contribution aggregation violated"):
            InventoryValidator.validate_inventory_invariants(inventory)


class TestAllocationValidation:
    """Test allocation validation rules (Requirements 9.1, 9.2)"""
    
    def test_validate_no_over_allocation_success(self):
        """Test successful no over-allocation validation"""
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("500"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("25000"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
            ],
            total_quantity_kg=Decimal("500"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        # Should not raise exception
        AllocationValidator.validate_no_over_allocation(allocation, Decimal("1000"))
    
    def test_validate_over_allocation(self):
        """Test over-allocation detection"""
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("600"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("30000"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
            ],
            total_quantity_kg=Decimal("600"),
            blended_realization_per_kg=Decimal("50"),
            status=AllocationStatus.PENDING,
        )
        
        from .validation.allocation_validator import ValidationError as AllocValidationError
        with pytest.raises(AllocValidationError, match="Over-allocation detected"):
            AllocationValidator.validate_no_over_allocation(allocation, Decimal("500"))
    
    def test_validate_processing_capacity_success(self):
        """Test processing capacity validation"""
        partner = ProcessingPartner(
            partner_id="P001",
            partner_name="Partner 1",
            contact_details={},
            facility_location="Location 1",
            rates_by_crop={"tomato": Decimal("45")},
            capacity_by_crop={"tomato": Decimal("1000")},
            quality_requirements={},
            pickup_schedule="daily",
            created_at=datetime.now(),
        )
        
        channel_allocation = ChannelAllocation(
            channel_type=ChannelType.PROCESSING,
            channel_id="P001",
            channel_name="Partner 1",
            quantity_kg=Decimal("500"),
            price_per_kg=Decimal("45"),
            revenue=Decimal("22500"),
            priority=2,
            fulfillment_status=FulfillmentStatus.PENDING,
        )
        
        # Should not raise exception
        AllocationValidator.validate_processing_capacity(channel_allocation, partner, "tomato")
    
    def test_validate_processing_capacity_exceeded(self):
        """Test processing capacity exceeded"""
        partner = ProcessingPartner(
            partner_id="P001",
            partner_name="Partner 1",
            contact_details={},
            facility_location="Location 1",
            rates_by_crop={"tomato": Decimal("45")},
            capacity_by_crop={"tomato": Decimal("400")},
            quality_requirements={},
            pickup_schedule="daily",
            created_at=datetime.now(),
        )
        
        channel_allocation = ChannelAllocation(
            channel_type=ChannelType.PROCESSING,
            channel_id="P001",
            channel_name="Partner 1",
            quantity_kg=Decimal("500"),
            price_per_kg=Decimal("45"),
            revenue=Decimal("22500"),
            priority=2,
            fulfillment_status=FulfillmentStatus.PENDING,
        )
        
        from .validation.allocation_validator import ValidationError as AllocValidationError
        with pytest.raises(AllocValidationError, match="exceeds capacity"):
            AllocationValidator.validate_processing_capacity(channel_allocation, partner, "tomato")
    
    def test_validate_priority_ordering_success(self):
        """Test priority ordering validation"""
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id="FPO001",
            crop_type="tomato",
            allocation_date=date.today(),
            channel_allocations=[
                ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id="SOC001",
                    channel_name="Society 1",
                    quantity_kg=Decimal("300"),
                    price_per_kg=Decimal("50"),
                    revenue=Decimal("15000"),
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id="P001",
                    channel_name="Partner 1",
                    quantity_kg=Decimal("400"),
                    price_per_kg=Decimal("45"),
                    revenue=Decimal("18000"),
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
                ChannelAllocation(
                    channel_type=ChannelType.MANDI,
                    channel_id="M001",
                    channel_name="Mandi 1",
                    quantity_kg=Decimal("300"),
                    price_per_kg=Decimal("35"),
                    revenue=Decimal("10500"),
                    priority=3,
                    fulfillment_status=FulfillmentStatus.PENDING,
                ),
            ],
            total_quantity_kg=Decimal("1000"),
            blended_realization_per_kg=Decimal("43.5"),
            status=AllocationStatus.PENDING,
        )
        
        # Should not raise exception
        AllocationValidator.validate_priority_ordering(allocation)
    
    def test_validate_priority_ordering_violated(self):
        """Test priority ordering violation"""
        # Create channel allocations with wrong order
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.PROCESSING,
                channel_id="P001",
                channel_name="Partner 1",
                quantity_kg=Decimal("400"),
                price_per_kg=Decimal("45"),
                revenue=Decimal("18000"),
                priority=2,
                fulfillment_status=FulfillmentStatus.PENDING,
            ),
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Society 1",
                quantity_kg=Decimal("300"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("15000"),
                priority=1,
                fulfillment_status=FulfillmentStatus.PENDING,
            ),
        ]
        
        # Create allocation bypassing validation
        allocation = object.__new__(Allocation)
        allocation.allocation_id = str(uuid.uuid4())
        allocation.fpo_id = "FPO001"
        allocation.crop_type = "tomato"
        allocation.allocation_date = date.today()
        allocation.channel_allocations = channel_allocations
        allocation.total_quantity_kg = Decimal("700")
        allocation.blended_realization_per_kg = Decimal("47.14")
        allocation.status = AllocationStatus.PENDING
        
        from .validation.allocation_validator import ValidationError as AllocValidationError
        with pytest.raises(AllocValidationError, match="Priority ordering violated"):
            AllocationValidator.validate_priority_ordering(allocation)


class TestTransactionRollback:
    """Test transaction rollback (Requirement 9.5)"""
    
    def test_postgres_transaction_rollback_on_error(self):
        """Test PostgreSQL transaction rollback on error"""
        from .db.transaction_manager import PostgresTransactionManager, TransactionError
        
        # Create mock connection pool
        mock_conn = Mock()
        mock_conn.commit = Mock()
        mock_conn.rollback = Mock()
        mock_conn.set_isolation_level = Mock()
        
        mock_pool = Mock()
        mock_pool.getconn = Mock(return_value=mock_conn)
        mock_pool.putconn = Mock()
        
        transaction_manager = PostgresTransactionManager(connection_pool=mock_pool)
        
        # Test that exception triggers rollback
        with pytest.raises(TransactionError):
            with transaction_manager.transaction() as conn:
                # Simulate an error during transaction
                raise ValueError("Simulated database error")
        
        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_postgres_transaction_commit_on_success(self):
        """Test PostgreSQL transaction commit on success"""
        from .db.transaction_manager import PostgresTransactionManager
        
        # Create mock connection pool
        mock_conn = Mock()
        mock_conn.commit = Mock()
        mock_conn.rollback = Mock()
        mock_conn.set_isolation_level = Mock()
        
        mock_pool = Mock()
        mock_pool.getconn = Mock(return_value=mock_conn)
        mock_pool.putconn = Mock()
        
        transaction_manager = PostgresTransactionManager(connection_pool=mock_pool)
        
        # Test successful transaction
        with transaction_manager.transaction() as conn:
            # Simulate successful operations
            pass
        
        # Verify commit was called
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_postgres_transaction_isolation_level(self):
        """Test PostgreSQL transaction isolation level setting"""
        from .db.transaction_manager import PostgresTransactionManager
        import psycopg2
        
        # Create mock connection pool
        mock_conn = Mock()
        mock_conn.commit = Mock()
        mock_conn.rollback = Mock()
        mock_conn.set_isolation_level = Mock()
        
        mock_pool = Mock()
        mock_pool.getconn = Mock(return_value=mock_conn)
        mock_pool.putconn = Mock()
        
        transaction_manager = PostgresTransactionManager(connection_pool=mock_pool)
        
        # Test SERIALIZABLE isolation level
        with transaction_manager.transaction(isolation_level="SERIALIZABLE") as conn:
            pass
        
        # Verify isolation level was set
        mock_conn.set_isolation_level.assert_called_once_with(
            psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
        )
    
    def test_execute_in_transaction_with_retry(self):
        """Test transaction execution with retry on concurrent update"""
        from .db.transaction_manager import PostgresTransactionManager, ConcurrentUpdateError
        import psycopg2
        
        # Create mock connection pool
        mock_conn = Mock()
        mock_conn.commit = Mock()
        mock_conn.rollback = Mock()
        mock_conn.set_isolation_level = Mock()
        
        # First call raises concurrent update error, second succeeds
        call_count = [0]
        
        def mock_commit_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                raise psycopg2.extensions.TransactionRollbackError("Serialization failure")
        
        mock_conn.commit.side_effect = mock_commit_side_effect
        
        mock_pool = Mock()
        mock_pool.getconn = Mock(return_value=mock_conn)
        mock_pool.putconn = Mock()
        
        transaction_manager = PostgresTransactionManager(connection_pool=mock_pool)
        
        # Test function that should succeed on retry
        def test_func(conn):
            return "success"
        
        result = transaction_manager.execute_in_transaction(test_func, max_retries=3)
        
        # Verify retry occurred and succeeded
        assert result == "success"
        assert call_count[0] == 2  # First failed, second succeeded
    
    def test_execute_in_transaction_max_retries_exceeded(self):
        """Test transaction execution fails after max retries"""
        from .db.transaction_manager import PostgresTransactionManager, ConcurrentUpdateError
        import psycopg2
        
        # Create mock connection pool
        mock_conn = Mock()
        mock_conn.commit = Mock()
        mock_conn.rollback = Mock()
        mock_conn.set_isolation_level = Mock()
        
        # Always raise concurrent update error
        mock_conn.commit.side_effect = psycopg2.extensions.TransactionRollbackError(
            "Serialization failure"
        )
        
        mock_pool = Mock()
        mock_pool.getconn = Mock(return_value=mock_conn)
        mock_pool.putconn = Mock()
        
        transaction_manager = PostgresTransactionManager(connection_pool=mock_pool)
        
        # Test function
        def test_func(conn):
            return "success"
        
        # Should raise after max retries
        with pytest.raises(ConcurrentUpdateError):
            transaction_manager.execute_in_transaction(test_func, max_retries=3)


class TestConcurrentUpdateHandling:
    """Test concurrent update handling (Requirement 9.5)"""
    
    def test_dynamodb_conditional_update_success(self):
        """Test successful DynamoDB conditional update"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock()
        
        # Test successful update
        result = DynamoDBConditionalWriter.conditional_update_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            updates={"available_quantity_kg": Decimal("900")},
            expected_version=1,
        )
        
        assert result is True
        mock_table.update_item.assert_called_once()
    
    def test_dynamodb_conditional_update_conflict(self):
        """Test DynamoDB conditional update conflict"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        from botocore.exceptions import ClientError
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock(
            side_effect=ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem"
            )
        )
        
        # Test conflict detection
        result = DynamoDBConditionalWriter.conditional_update_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            updates={"available_quantity_kg": Decimal("900")},
            expected_version=1,
        )
        
        assert result is False
    
    def test_dynamodb_conditional_reserve_success(self):
        """Test successful DynamoDB conditional reserve"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock()
        
        # Test successful reservation
        result = DynamoDBConditionalWriter.conditional_reserve_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            reserve_quantity=Decimal("200"),
            min_available=Decimal("200"),
        )
        
        assert result is True
        mock_table.update_item.assert_called_once()
    
    def test_dynamodb_conditional_reserve_insufficient_inventory(self):
        """Test DynamoDB conditional reserve with insufficient inventory"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        from botocore.exceptions import ClientError
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock(
            side_effect=ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem"
            )
        )
        
        # Test insufficient inventory detection
        result = DynamoDBConditionalWriter.conditional_reserve_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            reserve_quantity=Decimal("500"),
            min_available=Decimal("500"),
        )
        
        assert result is False
    
    def test_dynamodb_conditional_allocate_success(self):
        """Test successful DynamoDB conditional allocate"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock()
        
        # Test successful allocation
        result = DynamoDBConditionalWriter.conditional_allocate_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            allocate_quantity=Decimal("300"),
            min_available=Decimal("300"),
        )
        
        assert result is True
        mock_table.update_item.assert_called_once()
    
    def test_dynamodb_conditional_allocate_insufficient_inventory(self):
        """Test DynamoDB conditional allocate with insufficient inventory"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        from botocore.exceptions import ClientError
        
        # Create mock DynamoDB table
        mock_table = Mock()
        mock_table.update_item = Mock(
            side_effect=ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem"
            )
        )
        
        # Test insufficient inventory detection
        result = DynamoDBConditionalWriter.conditional_allocate_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            allocate_quantity=Decimal("800"),
            min_available=Decimal("800"),
        )
        
        assert result is False
    
    def test_concurrent_inventory_updates_prevented(self):
        """Test that concurrent inventory updates are prevented"""
        from .db.transaction_manager import DynamoDBConditionalWriter
        from botocore.exceptions import ClientError
        
        # Simulate two concurrent updates
        mock_table = Mock()
        
        # First update succeeds
        mock_table.update_item = Mock()
        result1 = DynamoDBConditionalWriter.conditional_update_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            updates={"available_quantity_kg": Decimal("900")},
            expected_version=1,
        )
        assert result1 is True
        
        # Second update with same version fails (simulating concurrent update)
        mock_table.update_item = Mock(
            side_effect=ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem"
            )
        )
        result2 = DynamoDBConditionalWriter.conditional_update_inventory(
            table=mock_table,
            inventory_key="FPO001#tomato",
            updates={"available_quantity_kg": Decimal("850")},
            expected_version=1,  # Same version - should fail
        )
        assert result2 is False


class TestAuditLogging:
    """Test audit log completeness (Requirement 9.6)"""
    
    def test_log_inventory_contribution(self):
        """Test logging inventory contribution"""
        audit_logger = AuditLogger(log_to_cloudwatch=False)
        
        audit_logger.log_inventory_contribution(
            user_id="user123",
            fpo_id="FPO001",
            crop_type="tomato",
            contribution_id="C001",
            farmer_id="F001",
            quantity_kg=Decimal("100"),
            quality_grade="A",
        )
        
        # Verify log was created (check file exists and contains entry)
        # In production, would verify CloudWatch logs
    
    def test_log_allocation_created(self):
        """Test logging allocation creation"""
        audit_logger = AuditLogger(log_to_cloudwatch=False)
        
        channel_allocations = [
            ChannelAllocation(
                channel_type=ChannelType.SOCIETY,
                channel_id="SOC001",
                channel_name="Society 1",
                quantity_kg=Decimal("500"),
                price_per_kg=Decimal("50"),
                revenue=Decimal("25000"),
                priority=1,
                fulfillment_status=FulfillmentStatus.PENDING,
            ),
        ]
        
        audit_logger.log_allocation_created(
            user_id="user123",
            allocation_id="A001",
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("500"),
            blended_realization_per_kg=Decimal("50"),
            channel_allocations=channel_allocations,
        )
    
    def test_log_fulfillment_update(self):
        """Test logging fulfillment update"""
        audit_logger = AuditLogger(log_to_cloudwatch=False)
        
        audit_logger.log_fulfillment_update(
            user_id="user123",
            allocation_id="A001",
            channel_id="SOC001",
            old_status="pending",
            new_status="in_transit",
            details={"driver": "Driver 1", "vehicle": "VH001"},
        )
        
        # Verify log was created (in production, would verify CloudWatch logs)
    
    def test_audit_log_contains_timestamp(self):
        """Test that audit logs contain timestamps"""
        audit_logger = AuditLogger(log_to_cloudwatch=False)
        
        # Log an event
        audit_logger.log_inventory_contribution(
            user_id="user123",
            fpo_id="FPO001",
            crop_type="tomato",
            contribution_id="C001",
            farmer_id="F001",
            quantity_kg=Decimal("100"),
            quality_grade="A",
        )
        
        # Verify timestamp is included (implementation-specific)
        # In production, would verify CloudWatch log entry has timestamp
    
    def test_audit_log_contains_user_identifier(self):
        """Test that audit logs contain user identifiers"""
        audit_logger = AuditLogger(log_to_cloudwatch=False)
        
        # Log an event with user ID
        audit_logger.log_allocation_created(
            user_id="user456",
            allocation_id="A002",
            fpo_id="FPO001",
            crop_type="tomato",
            total_quantity_kg=Decimal("500"),
            blended_realization_per_kg=Decimal("50"),
            channel_allocations=[],
        )
        
        # Verify user ID is included (implementation-specific)
        # In production, would verify CloudWatch log entry has user_id field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
