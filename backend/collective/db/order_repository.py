"""
Repository for order operations (PostgreSQL)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import List, Optional, Dict
from datetime import datetime
import os

from ..models import DeliveryOrder, PickupOrder, DispatchOrder, OrderStatus


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


class OrderRepository:
    """Repository for order operations (PostgreSQL)"""
    
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
    
    def create_delivery_order(self, order: DeliveryOrder) -> None:
        """Create a new delivery order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO delivery_orders (
                        order_id, allocation_id, society_id, society_name,
                        crop_type, quantity_kg, delivery_address, delivery_date,
                        delivery_time_window, status, created_at, updated_at, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order.order_id,
                        order.allocation_id,
                        order.society_id,
                        order.society_name,
                        order.crop_type,
                        order.quantity_kg,
                        order.delivery_address,
                        order.delivery_date,
                        order.delivery_time_window,
                        order.status.value,
                        order.created_at,
                        order.updated_at,
                        order.notes,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating delivery order: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_delivery_order(self, order_id: str) -> Optional[DeliveryOrder]:
        """Get delivery order by ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM delivery_orders WHERE order_id = %s",
                    (order_id,),
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return DeliveryOrder.from_dict(dict(row))
        finally:
            self._return_connection(conn)
    
    def list_delivery_orders(
        self,
        allocation_id: Optional[str] = None,
        society_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[DeliveryOrder]:
        """List delivery orders with optional filters"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM delivery_orders WHERE 1=1"
                params = []
                
                if allocation_id:
                    query += " AND allocation_id = %s"
                    params.append(allocation_id)
                
                if society_id:
                    query += " AND society_id = %s"
                    params.append(society_id)
                
                if status:
                    query += " AND status = %s"
                    params.append(status.value)
                
                query += " ORDER BY delivery_date, created_at"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [DeliveryOrder.from_dict(dict(row)) for row in rows]
        finally:
            self._return_connection(conn)
    
    def update_delivery_order(self, order: DeliveryOrder) -> None:
        """Update delivery order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                order.updated_at = datetime.now()
                cur.execute(
                    """
                    UPDATE delivery_orders
                    SET status = %s,
                        updated_at = %s,
                        notes = %s
                    WHERE order_id = %s
                    """,
                    (
                        order.status.value,
                        order.updated_at,
                        order.notes,
                        order.order_id,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating delivery order: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def create_pickup_order(self, order: PickupOrder) -> None:
        """Create a new pickup order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pickup_orders (
                        order_id, allocation_id, partner_id, partner_name,
                        crop_type, quantity_kg, pickup_location, pickup_date,
                        pickup_schedule, status, created_at, updated_at, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order.order_id,
                        order.allocation_id,
                        order.partner_id,
                        order.partner_name,
                        order.crop_type,
                        order.quantity_kg,
                        order.pickup_location,
                        order.pickup_date,
                        order.pickup_schedule,
                        order.status.value,
                        order.created_at,
                        order.updated_at,
                        order.notes,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating pickup order: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_pickup_order(self, order_id: str) -> Optional[PickupOrder]:
        """Get pickup order by ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM pickup_orders WHERE order_id = %s",
                    (order_id,),
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return PickupOrder.from_dict(dict(row))
        finally:
            self._return_connection(conn)
    
    def list_pickup_orders(
        self,
        allocation_id: Optional[str] = None,
        partner_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[PickupOrder]:
        """List pickup orders with optional filters"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM pickup_orders WHERE 1=1"
                params = []
                
                if allocation_id:
                    query += " AND allocation_id = %s"
                    params.append(allocation_id)
                
                if partner_id:
                    query += " AND partner_id = %s"
                    params.append(partner_id)
                
                if status:
                    query += " AND status = %s"
                    params.append(status.value)
                
                query += " ORDER BY pickup_date, created_at"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [PickupOrder.from_dict(dict(row)) for row in rows]
        finally:
            self._return_connection(conn)
    
    def update_pickup_order(self, order: PickupOrder) -> None:
        """Update pickup order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                order.updated_at = datetime.now()
                cur.execute(
                    """
                    UPDATE pickup_orders
                    SET status = %s,
                        updated_at = %s,
                        notes = %s
                    WHERE order_id = %s
                    """,
                    (
                        order.status.value,
                        order.updated_at,
                        order.notes,
                        order.order_id,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating pickup order: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def create_dispatch_order(self, order: DispatchOrder) -> None:
        """Create a new dispatch order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dispatch_orders (
                        order_id, allocation_id, mandi_id, mandi_name,
                        crop_type, quantity_kg, destination, dispatch_date,
                        transport_details, status, created_at, updated_at, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        order.order_id,
                        order.allocation_id,
                        order.mandi_id,
                        order.mandi_name,
                        order.crop_type,
                        order.quantity_kg,
                        order.destination,
                        order.dispatch_date,
                        order.transport_details,
                        order.status.value,
                        order.created_at,
                        order.updated_at,
                        order.notes,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating dispatch order: {e}")
            raise
        finally:
            self._return_connection(conn)
    
    def get_dispatch_order(self, order_id: str) -> Optional[DispatchOrder]:
        """Get dispatch order by ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM dispatch_orders WHERE order_id = %s",
                    (order_id,),
                )
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return DispatchOrder.from_dict(dict(row))
        finally:
            self._return_connection(conn)
    
    def list_dispatch_orders(
        self,
        allocation_id: Optional[str] = None,
        mandi_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[DispatchOrder]:
        """List dispatch orders with optional filters"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = "SELECT * FROM dispatch_orders WHERE 1=1"
                params = []
                
                if allocation_id:
                    query += " AND allocation_id = %s"
                    params.append(allocation_id)
                
                if mandi_id:
                    query += " AND mandi_id = %s"
                    params.append(mandi_id)
                
                if status:
                    query += " AND status = %s"
                    params.append(status.value)
                
                query += " ORDER BY dispatch_date, created_at"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [DispatchOrder.from_dict(dict(row)) for row in rows]
        finally:
            self._return_connection(conn)
    
    def update_dispatch_order(self, order: DispatchOrder) -> None:
        """Update dispatch order"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                order.updated_at = datetime.now()
                cur.execute(
                    """
                    UPDATE dispatch_orders
                    SET status = %s,
                        updated_at = %s,
                        notes = %s
                    WHERE order_id = %s
                    """,
                    (
                        order.status.value,
                        order.updated_at,
                        order.notes,
                        order.order_id,
                    ),
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating dispatch order: {e}")
            raise
        finally:
            self._return_connection(conn)
