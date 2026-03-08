"""
Transaction management for database operations
"""

from typing import Optional, Callable, Any
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from botocore.exceptions import ClientError

from .repositories import DatabaseConfig


class TransactionError(Exception):
    """Raised when transaction fails"""
    pass


class ConcurrentUpdateError(Exception):
    """Raised when concurrent update conflict occurs"""
    pass


class PostgresTransactionManager:
    """
    Manages PostgreSQL transactions with proper isolation.
    
    Implements transaction isolation for allocation operations
    to prevent race conditions (Requirement 9.5).
    """
    
    def __init__(self, connection_pool: Optional[SimpleConnectionPool] = None):
        if connection_pool:
            self.pool = connection_pool
        else:
            config = DatabaseConfig.get_postgres_config()
            self.pool = SimpleConnectionPool(1, 10, **config)
    
    @contextmanager
    def transaction(self, isolation_level: str = "READ COMMITTED"):
        """
        Context manager for PostgreSQL transactions.
        
        Args:
            isolation_level: Transaction isolation level
                - "READ COMMITTED" (default)
                - "REPEATABLE READ"
                - "SERIALIZABLE"
        
        Yields:
            Database connection with active transaction
        
        Raises:
            TransactionError: If transaction fails
        
        Example:
            with transaction_manager.transaction() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO ...")
                    cur.execute("UPDATE ...")
                # Transaction commits automatically on success
                # Transaction rolls back automatically on exception
        """
        conn = self.pool.getconn()
        
        try:
            # Set isolation level
            conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
                if isolation_level == "READ COMMITTED"
                else psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ
                if isolation_level == "REPEATABLE READ"
                else psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
            )
            
            # Begin transaction
            yield conn
            
            # Commit on success
            conn.commit()
            
        except psycopg2.extensions.TransactionRollbackError as e:
            # Serialization failure - concurrent update conflict
            conn.rollback()
            raise ConcurrentUpdateError(
                f"Concurrent update conflict: {e}"
            ) from e
            
        except Exception as e:
            # Rollback on any error
            conn.rollback()
            raise TransactionError(
                f"Transaction failed: {e}"
            ) from e
            
        finally:
            # Return connection to pool
            self.pool.putconn(conn)
    
    def execute_in_transaction(
        self,
        func: Callable[[Any], Any],
        isolation_level: str = "READ COMMITTED",
        max_retries: int = 3,
    ) -> Any:
        """
        Execute a function within a transaction with retry logic.
        
        Args:
            func: Function that takes a connection and performs database operations
            isolation_level: Transaction isolation level
            max_retries: Maximum number of retries on concurrent update conflicts
        
        Returns:
            Result of the function
        
        Raises:
            TransactionError: If transaction fails after all retries
            ConcurrentUpdateError: If concurrent update conflict persists
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.transaction(isolation_level) as conn:
                    return func(conn)
                    
            except ConcurrentUpdateError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Retry on concurrent update conflict
                    continue
                else:
                    # Max retries exceeded
                    raise
                    
            except TransactionError:
                # Don't retry on other transaction errors
                raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error


class DynamoDBConditionalWriter:
    """
    Handles DynamoDB conditional writes to prevent concurrent update conflicts.
    
    Implements optimistic locking using version numbers or conditional expressions
    (Requirement 9.5).
    """
    
    @staticmethod
    def conditional_update_inventory(
        table,
        inventory_key: str,
        updates: dict,
        expected_version: Optional[int] = None,
    ) -> bool:
        """
        Update inventory with conditional write to prevent conflicts.
        
        Args:
            table: DynamoDB table resource
            inventory_key: Inventory key
            updates: Dictionary of updates to apply
            expected_version: Expected version number for optimistic locking
        
        Returns:
            True if update succeeded, False if condition failed
        
        Raises:
            Exception: If update fails for reasons other than condition
        """
        try:
            # Build update expression
            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}
            
            for key, value in updates.items():
                # Use attribute names to handle reserved keywords
                attr_name = f"#{key}"
                attr_value = f":{key}"
                
                update_expr_parts.append(f"{attr_name} = {attr_value}")
                expr_attr_names[attr_name] = key
                expr_attr_values[attr_value] = value
            
            # Add version increment
            if expected_version is not None:
                update_expr_parts.append("#version = :new_version")
                expr_attr_names["#version"] = "version"
                expr_attr_values[":new_version"] = expected_version + 1
                expr_attr_values[":expected_version"] = expected_version
            
            update_expression = "SET " + ", ".join(update_expr_parts)
            
            # Build condition expression
            if expected_version is not None:
                condition_expression = "#version = :expected_version"
            else:
                condition_expression = None
            
            # Execute conditional update
            kwargs = {
                "Key": {"inventory_key": inventory_key},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expr_attr_values,
                "ExpressionAttributeNames": expr_attr_names,
            }
            
            if condition_expression:
                kwargs["ConditionExpression"] = condition_expression
            
            table.update_item(**kwargs)
            
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Condition failed - concurrent update detected
                return False
            else:
                # Other error
                raise
    
    @staticmethod
    def conditional_reserve_inventory(
        table,
        inventory_key: str,
        reserve_quantity: Any,
        min_available: Any,
    ) -> bool:
        """
        Reserve inventory with conditional write to ensure sufficient availability.
        
        Args:
            table: DynamoDB table resource
            inventory_key: Inventory key
            reserve_quantity: Quantity to reserve
            min_available: Minimum available quantity required
        
        Returns:
            True if reservation succeeded, False if insufficient inventory
        
        Raises:
            Exception: If update fails for reasons other than condition
        """
        try:
            table.update_item(
                Key={"inventory_key": inventory_key},
                UpdateExpression="""
                    SET reserved_quantity_kg = reserved_quantity_kg + :reserve_qty,
                        available_quantity_kg = available_quantity_kg - :reserve_qty
                """,
                ConditionExpression="available_quantity_kg >= :min_available",
                ExpressionAttributeValues={
                    ":reserve_qty": reserve_quantity,
                    ":min_available": min_available,
                },
            )
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Insufficient inventory
                return False
            else:
                raise
    
    @staticmethod
    def conditional_allocate_inventory(
        table,
        inventory_key: str,
        allocate_quantity: Any,
        min_available: Any,
    ) -> bool:
        """
        Allocate inventory with conditional write to ensure sufficient availability.
        
        Args:
            table: DynamoDB table resource
            inventory_key: Inventory key
            allocate_quantity: Quantity to allocate
            min_available: Minimum available quantity required
        
        Returns:
            True if allocation succeeded, False if insufficient inventory
        
        Raises:
            Exception: If update fails for reasons other than condition
        """
        try:
            table.update_item(
                Key={"inventory_key": inventory_key},
                UpdateExpression="""
                    SET allocated_quantity_kg = allocated_quantity_kg + :alloc_qty,
                        available_quantity_kg = available_quantity_kg - :alloc_qty
                """,
                ConditionExpression="available_quantity_kg >= :min_available",
                ExpressionAttributeValues={
                    ":alloc_qty": allocate_quantity,
                    ":min_available": min_available,
                },
            )
            return True
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Insufficient inventory
                return False
            else:
                raise
