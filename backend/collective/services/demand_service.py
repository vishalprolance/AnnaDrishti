"""
Demand prediction and reservation service
"""

from typing import Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import statistics

from ..models import DemandPrediction, Reservation, ReservationStatus
from ..db import SocietyRepository, InventoryRepository


class DemandService:
    """
    Service for demand prediction and inventory reservation.
    
    Implements the demand prediction algorithm using historical order data
    and manages inventory reservations for societies.
    """
    
    def __init__(
        self,
        society_repository: Optional[SocietyRepository] = None,
        inventory_repository: Optional[InventoryRepository] = None,
    ):
        self.society_repository = society_repository or SocietyRepository()
        self.inventory_repository = inventory_repository or InventoryRepository()
    
    def query_historical_orders(
        self,
        society_id: str,
        crop_type: str,
        lookback_days: int = 90,
    ) -> List[dict]:
        """
        Query historical orders for a society and crop type.
        
        Args:
            society_id: Society identifier
            crop_type: Crop type
            lookback_days: Number of days to look back (default: 90)
        
        Returns:
            List of historical orders with quantity and date
        """
        # Query from PostgreSQL order_history table
        # This is a placeholder - actual implementation would query the database
        
        # For now, return empty list
        # In production, this would execute:
        # SELECT order_id, quantity_kg, order_date
        # FROM order_history
        # WHERE society_id = %s AND crop_type = %s
        #   AND order_date >= CURRENT_DATE - INTERVAL '%s days'
        # ORDER BY order_date DESC
        
        return []
    
    def predict_society_demand(
        self,
        society_id: str,
        crop_type: str,
        delivery_date: date,
    ) -> DemandPrediction:
        """
        Predict society demand based on historical patterns.
        
        Uses exponential weighted moving average with recent orders weighted higher.
        
        Args:
            society_id: Society identifier
            crop_type: Crop type
            delivery_date: Expected delivery date
        
        Returns:
            DemandPrediction object
        """
        # Get historical orders
        historical_orders = self.query_historical_orders(society_id, crop_type, lookback_days=90)
        
        # If insufficient data, use society's typical quantity
        if len(historical_orders) < 3:
            society = self.society_repository.get_society(society_id)
            
            if society is None:
                raise ValueError(f"Society not found: {society_id}")
            
            typical_qty = society.get_typical_quantity(crop_type)
            
            if typical_qty is None:
                # No typical quantity, use default
                typical_qty = Decimal("10.0")
            
            return DemandPrediction(
                prediction_id=str(uuid.uuid4()),
                society_id=society_id,
                crop_type=crop_type,
                predicted_quantity_kg=typical_qty,
                confidence_score=0.5,
                prediction_date=datetime.now(),
                delivery_date=delivery_date,
                based_on_orders=0,
                status=ReservationStatus.PREDICTED,
            )
        
        # Exponential weighted moving average
        # Recent orders weighted higher: [0.5, 0.3, 0.2]
        weights = [0.5, 0.3, 0.2]
        recent_orders = historical_orders[-3:]
        
        predicted_qty = sum(
            Decimal(str(order["quantity_kg"])) * Decimal(str(weight))
            for order, weight in zip(recent_orders, weights)
        )
        
        # Calculate confidence based on consistency (inverse of coefficient of variation)
        quantities = [Decimal(str(o["quantity_kg"])) for o in recent_orders]
        mean_qty = sum(quantities) / len(quantities)
        
        if mean_qty > 0:
            # Calculate standard deviation
            variance = sum((q - mean_qty) ** 2 for q in quantities) / len(quantities)
            std_dev = variance ** Decimal("0.5")
            
            # Confidence: higher when std_dev is low relative to mean
            # confidence = 1 - (std_dev / mean_qty), bounded between 0.5 and 1.0
            cv = std_dev / mean_qty  # coefficient of variation
            confidence = max(0.5, min(1.0, 1.0 - float(cv)))
        else:
            confidence = 0.5
        
        return DemandPrediction(
            prediction_id=str(uuid.uuid4()),
            society_id=society_id,
            crop_type=crop_type,
            predicted_quantity_kg=predicted_qty,
            confidence_score=confidence,
            prediction_date=datetime.now(),
            delivery_date=delivery_date,
            based_on_orders=len(historical_orders),
            status=ReservationStatus.PREDICTED,
        )
    
    def reserve_inventory(
        self,
        fpo_id: str,
        society_id: str,
        crop_type: str,
        quantity_kg: Decimal,
        delivery_date: date,
    ) -> Reservation:
        """
        Reserve inventory for society demand.
        
        Args:
            fpo_id: FPO identifier
            society_id: Society identifier
            crop_type: Crop type
            quantity_kg: Quantity to reserve
            delivery_date: Expected delivery date
        
        Returns:
            Reservation object
        
        Raises:
            ValueError: If insufficient inventory available
        """
        # Check inventory availability
        inventory = self.inventory_repository.get_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        if quantity_kg > inventory.available_quantity_kg:
            raise ValueError(
                f"Cannot reserve {quantity_kg} kg, only {inventory.available_quantity_kg} kg available"
            )
        
        # Create reservation
        reservation = Reservation(
            reservation_id=str(uuid.uuid4()),
            society_id=society_id,
            crop_type=crop_type,
            reserved_quantity_kg=quantity_kg,
            reservation_timestamp=datetime.now(),
            delivery_date=delivery_date,
            status=ReservationStatus.PREDICTED,
        )
        
        # Update inventory (mark as reserved)
        inventory.reserve_quantity(quantity_kg)
        self.inventory_repository.save_inventory(inventory)
        
        # Save reservation to DynamoDB
        # This would be implemented in a ReservationRepository
        # For now, we'll just return the reservation object
        
        return reservation
    
    def confirm_reservation(
        self,
        reservation_id: str,
    ) -> Reservation:
        """
        Confirm a predicted reservation.
        
        Changes status from PREDICTED to CONFIRMED.
        
        Args:
            reservation_id: Reservation identifier
        
        Returns:
            Updated Reservation object
        
        Raises:
            ValueError: If reservation not found
        """
        # Get reservation from DynamoDB
        # This would be implemented with a ReservationRepository
        # For now, create a minimal implementation
        
        # In production:
        # 1. Get reservation from DynamoDB using reservation_id
        # 2. Validate status is PREDICTED
        # 3. Update status to CONFIRMED
        # 4. Save back to DynamoDB
        # 5. Return updated reservation
        
        # Placeholder: return a dummy reservation
        # This will be properly implemented when ReservationRepository is created
        return Reservation(
            reservation_id=reservation_id,
            society_id="placeholder",
            crop_type="placeholder",
            reserved_quantity_kg=Decimal("0"),
            reservation_timestamp=datetime.now(),
            delivery_date=date.today(),
            status=ReservationStatus.CONFIRMED,
        )
    
    def get_active_reservations(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
    ) -> List[Reservation]:
        """
        Get active reservations for allocation.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date for allocation
        
        Returns:
            List of active reservations sorted by timestamp
        """
        # This would query reservations from DynamoDB
        # For now, return empty list
        
        # In production:
        # Query reservations where:
        # - crop_type matches
        # - delivery_date = allocation_date
        # - status IN ('predicted', 'confirmed')
        # Sort by reservation_timestamp ASC
        
        return []
