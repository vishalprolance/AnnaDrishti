"""
Repository classes for database access
"""

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
import os
import json

from ..models import (
    CollectiveInventory,
    FarmerContribution,
    SocietyProfile,
    ProcessingPartner,
    Allocation,
    ChannelAllocation,
    Reservation,
)


class DatabaseConfig:
    """Database configuration"""
    
    @staticmethod
    def get_postgres_config() -> Dict[str, str]:
        """Get PostgreSQL configuration from environment"""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "anna_drishti"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
    
    @staticmethod
    def get_dynamodb_config() -> Dict[str, str]:
        """Get DynamoDB configuration from environment"""
        return {
            "region_name": os.getenv("AWS_REGION", "ap-south-1"),
            "endpoint_url": os.getenv("DYNAMODB_ENDPOINT"),  # For local testing
        }


class InventoryRepository:
    """Repository for collective inventory operations (DynamoDB)"""
    
    def __init__(self):
        config = DatabaseConfig.get_dynamodb_config()
        self.dynamodb = boto3.resource("dynamodb", **config)
        self.inventory_table = self.dynamodb.Table("collective_inventory")
        self.contributions_table = self.dynamodb.Table("farmer_contributions")
        self.reservations_table = self.dynamodb.Table("reservations")
    
    def _make_inventory_key(self, fpo_id: str, crop_type: str) -> str:
        """Create composite key for inventory"""
        return f"{fpo_id}#{crop_type}"
    
    def get_inventory(self, fpo_id: str, crop_type: str) -> Optional[CollectiveInventory]:
        """Get collective inventory for FPO and crop type"""
        try:
            response = self.inventory_table.get_item(
                Key={"inventory_key": self._make_inventory_key(fpo_id, crop_type)}
            )
            
            if "Item" not in response:
                return None
            
            item = response["Item"]
            return CollectiveInventory.from_dict(item)
        except Exception as e:
            print(f"Error getting inventory: {e}")
            raise
    
    def save_inventory(self, inventory: CollectiveInventory) -> None:
        """Save collective inventory"""
        try:
            item = inventory.to_dict()
            item["inventory_key"] = self._make_inventory_key(inventory.fpo_id, inventory.crop_type)
            item["fpo_id"] = inventory.fpo_id  # For GSI
            
            self.inventory_table.put_item(Item=item)
        except Exception as e:
            print(f"Error saving inventory: {e}")
            raise
    
    def add_contribution(self, contribution: FarmerContribution, fpo_id: str) -> None:
        """Add farmer contribution to inventory"""
        try:
            # Save contribution
            item = contribution.to_dict()
            item["fpo_id"] = fpo_id
            item["fpo_crop_key"] = f"{fpo_id}#{contribution.crop_type}"
            
            self.contributions_table.put_item(Item=item)
            
            # Update inventory atomically
            inventory_key = self._make_inventory_key(fpo_id, contribution.crop_type)
            
            self.inventory_table.update_item(
                Key={"inventory_key": inventory_key},
                UpdateExpression="""
                    SET total_quantity_kg = if_not_exists(total_quantity_kg, :zero) + :qty,
                        available_quantity_kg = if_not_exists(available_quantity_kg, :zero) + :qty,
                        last_updated = :timestamp,
                        fpo_id = :fpo_id,
                        crop_type = :crop_type
                """,
                ExpressionAttributeValues={
                    ":qty": Decimal(str(contribution.quantity_kg)),
                    ":zero": Decimal("0"),
                    ":timestamp": datetime.now().isoformat(),
                    ":fpo_id": fpo_id,
                    ":crop_type": contribution.crop_type,
                },
            )
        except Exception as e:
            print(f"Error adding contribution: {e}")
            raise
    
    def get_contributions_by_farmer(self, farmer_id: str) -> List[FarmerContribution]:
        """Get all contributions by a farmer"""
        try:
            response = self.contributions_table.query(
                IndexName="farmer_id-index",
                KeyConditionExpression="farmer_id = :farmer_id",
                ExpressionAttributeValues={":farmer_id": farmer_id},
            )
            
            return [FarmerContribution.from_dict(item) for item in response.get("Items", [])]
        except Exception as e:
            print(f"Error getting contributions: {e}")
            raise
    
    def create_reservation(self, reservation: Reservation) -> None:
        """Create inventory reservation"""
        try:
            item = reservation.to_dict()
            # Set TTL to 30 days from now
            item["ttl"] = int((datetime.now().timestamp() + 30 * 24 * 60 * 60))
            
            self.reservations_table.put_item(Item=item)
        except Exception as e:
            print(f"Error creating reservation: {e}")
            raise
    
    def get_reservations_by_date(self, delivery_date: date) -> List[Reservation]:
        """Get all reservations for a delivery date"""
        try:
            response = self.reservations_table.query(
                IndexName="delivery_date-index",
                KeyConditionExpression="delivery_date = :date",
                ExpressionAttributeValues={":date": delivery_date.isoformat()},
            )
            
            return [Reservation.from_dict(item) for item in response.get("Items", [])]
        except Exception as e:
            print(f"Error getting reservations: {e}")
            raise


class SocietyRepository:
    """Repository for society operations (PostgreSQL)"""
    
    def __init__(self, connection_pool: Optional[SimpleConnectionPool] = None):
        if connection_pool:
            self.pool = connection_pool
        else:
            config = DatabaseConfig.get_postgres_config()
            self.pool = SimpleConnectionPool(1, 10, **config)
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def create_society(self, society: SocietyProfile) -> None:
        """Create a new society"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO societies (
                        society_id, society_name, location, contact_details,
                        delivery_address, delivery_frequency, preferred_day,
                        preferred_time_window, crop_preferences, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        society.society_id,
                        society.society_name,
                        society.location,
                        json.dumps(society.contact_details),
                        society.delivery_address,
                        society.delivery_frequency.value,
                        society.preferred_day,
                        society.preferred_time_window,
                        json.dumps([p.to_dict() for p in society.crop_preferences]),
                        society.created_at,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating society: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_society(self, society_id: str) -> Optional[SocietyProfile]:
        """Get society by ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM societies WHERE society_id = %s",
                    (society_id,),
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return SocietyProfile.from_dict(dict(row))
        finally:
            self._return_connection(conn)
    
    def list_societies(self) -> List[SocietyProfile]:
        """List all societies"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM societies ORDER BY society_name")
                rows = cur.fetchall()
                
                return [SocietyProfile.from_dict(dict(row)) for row in rows]
        finally:
            self._return_connection(conn)


class ProcessingPartnerRepository:
    """Repository for processing partner operations (PostgreSQL)"""
    
    def __init__(self, connection_pool: Optional[SimpleConnectionPool] = None):
        if connection_pool:
            self.pool = connection_pool
        else:
            config = DatabaseConfig.get_postgres_config()
            self.pool = SimpleConnectionPool(1, 10, **config)
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def create_partner(self, partner: ProcessingPartner) -> None:
        """Create a new processing partner"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO processing_partners (
                        partner_id, partner_name, contact_details, facility_location,
                        rates_by_crop, capacity_by_crop, quality_requirements,
                        pickup_schedule, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        partner.partner_id,
                        partner.partner_name,
                        json.dumps(partner.contact_details),
                        partner.facility_location,
                        json.dumps(partner.to_dict()["rates_by_crop"]),
                        json.dumps(partner.to_dict()["capacity_by_crop"]),
                        json.dumps(partner.quality_requirements),
                        partner.pickup_schedule,
                        partner.created_at,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating partner: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_partner(self, partner_id: str) -> Optional[ProcessingPartner]:
        """Get processing partner by ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM processing_partners WHERE partner_id = %s",
                    (partner_id,),
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return ProcessingPartner.from_dict(dict(row))
        finally:
            self._return_connection(conn)
    
    def list_partners(self) -> List[ProcessingPartner]:
        """List all processing partners"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM processing_partners ORDER BY partner_name")
                rows = cur.fetchall()
                
                return [ProcessingPartner.from_dict(dict(row)) for row in rows]
        finally:
            self._return_connection(conn)
    
    def update_partner(self, partner: ProcessingPartner) -> None:
        """Update an existing processing partner"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE processing_partners
                    SET partner_name = %s,
                        contact_details = %s,
                        facility_location = %s,
                        rates_by_crop = %s,
                        capacity_by_crop = %s,
                        quality_requirements = %s,
                        pickup_schedule = %s
                    WHERE partner_id = %s
                    """,
                    (
                        partner.partner_name,
                        json.dumps(partner.contact_details),
                        partner.facility_location,
                        json.dumps(partner.to_dict()["rates_by_crop"]),
                        json.dumps(partner.to_dict()["capacity_by_crop"]),
                        json.dumps(partner.quality_requirements),
                        partner.pickup_schedule,
                        partner.partner_id,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating partner: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def delete_partner(self, partner_id: str) -> None:
        """Delete a processing partner"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM processing_partners WHERE partner_id = %s",
                    (partner_id,),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error deleting partner: {e}")
            raise
        finally:
            self._return_connection(conn)


class AllocationRepository:
    """Repository for allocation operations (PostgreSQL)"""
    
    def __init__(self, connection_pool: Optional[SimpleConnectionPool] = None):
        if connection_pool:
            self.pool = connection_pool
        else:
            config = DatabaseConfig.get_postgres_config()
            self.pool = SimpleConnectionPool(1, 10, **config)
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def create_allocation(self, allocation: Allocation) -> None:
        """Create a new allocation with channel allocations"""
        conn = self._get_connection()
        try:
            # Use transaction to ensure atomicity
            with conn:
                with conn.cursor() as cur:
                    # Insert allocation
                    cur.execute(
                        """
                        INSERT INTO allocations (
                            allocation_id, fpo_id, crop_type, allocation_date,
                            total_quantity_kg, blended_realization_per_kg, status, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            allocation.allocation_id,
                            allocation.fpo_id,
                            allocation.crop_type,
                            allocation.allocation_date,
                            allocation.total_quantity_kg,
                            allocation.blended_realization_per_kg,
                            allocation.status.value,
                            datetime.now(),
                        ),
                    )
                    
                    # Insert channel allocations
                    for ca in allocation.channel_allocations:
                        cur.execute(
                            """
                            INSERT INTO channel_allocations (
                                allocation_id, channel_type, channel_id, channel_name,
                                quantity_kg, price_per_kg, revenue, priority,
                                fulfillment_status, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                allocation.allocation_id,
                                ca.channel_type.value,
                                ca.channel_id,
                                ca.channel_name,
                                ca.quantity_kg,
                                ca.price_per_kg,
                                ca.revenue,
                                ca.priority,
                                ca.fulfillment_status.value,
                                datetime.now(),
                            ),
                        )
                # Transaction commits automatically on context exit
        except Exception as e:
            # Transaction rolls back automatically on exception
            print(f"Error creating allocation: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_allocation(self, allocation_id: str) -> Optional[Allocation]:
        """Get allocation by ID with channel allocations"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get allocation
                cur.execute(
                    "SELECT * FROM allocations WHERE allocation_id = %s",
                    (allocation_id,),
                )
                alloc_row = cur.fetchone()
                
                if not alloc_row:
                    return None
                
                # Get channel allocations
                cur.execute(
                    """
                    SELECT * FROM channel_allocations 
                    WHERE allocation_id = %s 
                    ORDER BY priority
                    """,
                    (allocation_id,),
                )
                channel_rows = cur.fetchall()
                
                # Build allocation object
                alloc_dict = dict(alloc_row)
                alloc_dict["channel_allocations"] = [dict(row) for row in channel_rows]
                
                return Allocation.from_dict(alloc_dict)
        finally:
            self._return_connection(conn)


    def list_allocations(
        self,
        fpo_id: str,
        crop_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Allocation]:
        """List allocations for an FPO with optional crop type filter"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build query
                if crop_type:
                    query = """
                        SELECT * FROM allocations
                        WHERE fpo_id = %s AND crop_type = %s
                        ORDER BY allocation_date DESC
                        LIMIT %s
                    """
                    params = (fpo_id, crop_type, limit)
                else:
                    query = """
                        SELECT * FROM allocations
                        WHERE fpo_id = %s
                        ORDER BY allocation_date DESC
                        LIMIT %s
                    """
                    params = (fpo_id, limit)

                cur.execute(query, params)
                alloc_rows = cur.fetchall()

                # Get allocations with channel allocations
                allocations = []
                for alloc_row in alloc_rows:
                    allocation_id = alloc_row["allocation_id"]

                    # Get channel allocations
                    cur.execute(
                        """
                        SELECT * FROM channel_allocations
                        WHERE allocation_id = %s
                        ORDER BY priority
                        """,
                        (allocation_id,),
                    )
                    channel_rows = cur.fetchall()

                    # Build allocation object
                    alloc_dict = dict(alloc_row)
                    alloc_dict["channel_allocations"] = [dict(row) for row in channel_rows]

                    allocations.append(Allocation.from_dict(alloc_dict))

                return allocations
        finally:
            self._return_connection(conn)

    def update_allocation(self, allocation: Allocation) -> None:
        """Update an existing allocation"""
        conn = self._get_connection()
        try:
            # Use transaction to ensure atomicity
            with conn:
                with conn.cursor() as cur:
                    # Update allocation
                    cur.execute(
                        """
                        UPDATE allocations
                        SET status = %s,
                            blended_realization_per_kg = %s,
                            total_quantity_kg = %s
                        WHERE allocation_id = %s
                        """,
                        (
                            allocation.status.value,
                            allocation.blended_realization_per_kg,
                            allocation.total_quantity_kg,
                            allocation.allocation_id,
                        ),
                    )

                    # Update channel allocations
                    for ca in allocation.channel_allocations:
                        cur.execute(
                            """
                            UPDATE channel_allocations
                            SET fulfillment_status = %s,
                                quantity_kg = %s,
                                price_per_kg = %s,
                                revenue = %s
                            WHERE allocation_id = %s AND channel_id = %s
                            """,
                            (
                                ca.fulfillment_status.value,
                                ca.quantity_kg,
                                ca.price_per_kg,
                                ca.revenue,
                                allocation.allocation_id,
                                ca.channel_id,
                            ),
                        )
                # Transaction commits automatically on context exit
        except Exception as e:
            # Transaction rolls back automatically on exception
            print(f"Error updating allocation: {e}")
            raise
        finally:
            self._return_connection(conn)

