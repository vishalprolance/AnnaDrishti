"""
Audit logging for tracking all inventory and allocation changes
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


class AuditEventType(Enum):
    """Types of audit events"""
    # Inventory events
    INVENTORY_CONTRIBUTION_ADDED = "inventory.contribution.added"
    INVENTORY_CONTRIBUTION_DELETED = "inventory.contribution.deleted"
    INVENTORY_RESERVED = "inventory.reserved"
    INVENTORY_ALLOCATED = "inventory.allocated"
    INVENTORY_UPDATED = "inventory.updated"
    
    # Allocation events
    ALLOCATION_CREATED = "allocation.created"
    ALLOCATION_UPDATED = "allocation.updated"
    ALLOCATION_EXECUTED = "allocation.executed"
    
    # Fulfillment events
    FULFILLMENT_STARTED = "fulfillment.started"
    FULFILLMENT_IN_TRANSIT = "fulfillment.in_transit"
    FULFILLMENT_DELIVERED = "fulfillment.delivered"
    FULFILLMENT_COMPLETED = "fulfillment.completed"
    
    # Society events
    SOCIETY_CREATED = "society.created"
    SOCIETY_UPDATED = "society.updated"
    SOCIETY_DELETED = "society.deleted"
    
    # Processing partner events
    PARTNER_CREATED = "partner.created"
    PARTNER_UPDATED = "partner.updated"
    PARTNER_DELETED = "partner.deleted"
    
    # Reservation events
    RESERVATION_CREATED = "reservation.created"
    RESERVATION_CONFIRMED = "reservation.confirmed"
    RESERVATION_CANCELLED = "reservation.cancelled"


@dataclass
class AuditEvent:
    """
    Audit event record.
    
    Captures all relevant information about a system event for audit trail.
    """
    event_type: AuditEventType
    timestamp: datetime
    user_id: str
    entity_type: str  # e.g., "inventory", "allocation", "society"
    entity_id: str
    action: str  # e.g., "create", "update", "delete"
    details: Dict[str, Any]
    fpo_id: Optional[str] = None
    crop_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["timestamp"] = self.timestamp.isoformat()
        
        # Convert Decimal to string for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj
        
        data["details"] = convert_decimals(data["details"])
        
        return data


class AuditLogger:
    """
    Audit logger for tracking all system changes.
    
    Implements audit logging requirements (Requirement 9.6):
    - Log all inventory changes with timestamp and user
    - Log all allocation decisions
    - Log all fulfillment updates
    - Store logs in CloudWatch (or local file for development)
    """
    
    def __init__(self, log_to_cloudwatch: bool = False):
        """
        Initialize audit logger.
        
        Args:
            log_to_cloudwatch: If True, send logs to CloudWatch.
                              If False, log to local file (for development).
        """
        import os
        
        # Auto-detect Lambda environment
        is_lambda = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
        self.log_to_cloudwatch = log_to_cloudwatch or is_lambda
        
        # Set up Python logger
        self.logger = logging.getLogger("collective.audit")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler for local logging (not in Lambda)
        if not self.log_to_cloudwatch:
            handler = logging.FileHandler("audit.log")
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            # In Lambda/CloudWatch, use StreamHandler (logs go to CloudWatch automatically)
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.
        
        Args:
            event: Audit event to log
        """
        event_dict = event.to_dict()
        log_message = json.dumps(event_dict, indent=2)
        
        self.logger.info(log_message)
    
    def log_inventory_contribution(
        self,
        user_id: str,
        fpo_id: str,
        crop_type: str,
        contribution_id: str,
        farmer_id: str,
        quantity_kg: Decimal,
        quality_grade: str,
    ) -> None:
        """Log farmer contribution added to inventory"""
        event = AuditEvent(
            event_type=AuditEventType.INVENTORY_CONTRIBUTION_ADDED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="inventory",
            entity_id=f"{fpo_id}#{crop_type}",
            action="contribution_added",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details={
                "contribution_id": contribution_id,
                "farmer_id": farmer_id,
                "quantity_kg": quantity_kg,
                "quality_grade": quality_grade,
            },
        )
        self.log_event(event)
    
    def log_inventory_contribution_deleted(
        self,
        user_id: str,
        fpo_id: str,
        crop_type: str,
        contribution_id: str,
        farmer_id: str,
        quantity_kg: Decimal,
    ) -> None:
        """Log farmer contribution deleted from inventory"""
        event = AuditEvent(
            event_type=AuditEventType.INVENTORY_CONTRIBUTION_DELETED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="inventory",
            entity_id=f"{fpo_id}#{crop_type}",
            action="contribution_deleted",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details={
                "contribution_id": contribution_id,
                "farmer_id": farmer_id,
                "quantity_kg": quantity_kg,
            },
        )
        self.log_event(event)
    
    def log_inventory_reserved(
        self,
        user_id: str,
        fpo_id: str,
        crop_type: str,
        quantity_kg: Decimal,
        reservation_id: str,
    ) -> None:
        """Log inventory reservation"""
        event = AuditEvent(
            event_type=AuditEventType.INVENTORY_RESERVED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="inventory",
            entity_id=f"{fpo_id}#{crop_type}",
            action="reserved",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details={
                "quantity_kg": quantity_kg,
                "reservation_id": reservation_id,
            },
        )
        self.log_event(event)
    
    def log_inventory_allocated(
        self,
        user_id: str,
        fpo_id: str,
        crop_type: str,
        quantity_kg: Decimal,
        allocation_id: str,
    ) -> None:
        """Log inventory allocation"""
        event = AuditEvent(
            event_type=AuditEventType.INVENTORY_ALLOCATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="inventory",
            entity_id=f"{fpo_id}#{crop_type}",
            action="allocated",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details={
                "quantity_kg": quantity_kg,
                "allocation_id": allocation_id,
            },
        )
        self.log_event(event)
    
    def log_allocation_created(
        self,
        user_id: str,
        allocation_id: str,
        fpo_id: str,
        crop_type: str,
        total_quantity_kg: Decimal,
        blended_realization_per_kg: Decimal,
        channel_allocations: list,
    ) -> None:
        """Log allocation creation"""
        event = AuditEvent(
            event_type=AuditEventType.ALLOCATION_CREATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="allocation",
            entity_id=allocation_id,
            action="created",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details={
                "total_quantity_kg": total_quantity_kg,
                "blended_realization_per_kg": blended_realization_per_kg,
                "channel_count": len(channel_allocations),
                "channels": [
                    {
                        "channel_type": ca.channel_type.value,
                        "channel_id": ca.channel_id,
                        "quantity_kg": ca.quantity_kg,
                        "price_per_kg": ca.price_per_kg,
                        "priority": ca.priority,
                    }
                    for ca in channel_allocations
                ],
            },
        )
        self.log_event(event)
    
    def log_allocation_updated(
        self,
        user_id: str,
        allocation_id: str,
        fpo_id: str,
        crop_type: str,
        changes: Dict[str, Any],
    ) -> None:
        """Log allocation update"""
        event = AuditEvent(
            event_type=AuditEventType.ALLOCATION_UPDATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="allocation",
            entity_id=allocation_id,
            action="updated",
            fpo_id=fpo_id,
            crop_type=crop_type,
            details=changes,
        )
        self.log_event(event)
    
    def log_fulfillment_update(
        self,
        user_id: str,
        allocation_id: str,
        channel_id: str,
        old_status: str,
        new_status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log fulfillment status update"""
        # Map status to event type
        event_type_map = {
            "pending": AuditEventType.FULFILLMENT_STARTED,
            "in_transit": AuditEventType.FULFILLMENT_IN_TRANSIT,
            "delivered": AuditEventType.FULFILLMENT_DELIVERED,
            "completed": AuditEventType.FULFILLMENT_COMPLETED,
        }
        
        # Default to FULFILLMENT_COMPLETED if status not in map
        event_type = event_type_map.get(
            new_status.lower(),
            AuditEventType.FULFILLMENT_COMPLETED
        )
        
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="fulfillment",
            entity_id=f"{allocation_id}#{channel_id}",
            action="status_updated",
            details={
                "allocation_id": allocation_id,
                "channel_id": channel_id,
                "old_status": old_status,
                "new_status": new_status,
                **(details or {}),
            },
        )
        self.log_event(event)
    
    def log_society_created(
        self,
        user_id: str,
        society_id: str,
        society_name: str,
        location: str,
    ) -> None:
        """Log society creation"""
        event = AuditEvent(
            event_type=AuditEventType.SOCIETY_CREATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="society",
            entity_id=society_id,
            action="created",
            details={
                "society_name": society_name,
                "location": location,
            },
        )
        self.log_event(event)
    
    def log_society_updated(
        self,
        user_id: str,
        society_id: str,
        changes: Dict[str, Any],
    ) -> None:
        """Log society update"""
        event = AuditEvent(
            event_type=AuditEventType.SOCIETY_UPDATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="society",
            entity_id=society_id,
            action="updated",
            details=changes,
        )
        self.log_event(event)
    
    def log_partner_created(
        self,
        user_id: str,
        partner_id: str,
        partner_name: str,
        facility_location: str,
    ) -> None:
        """Log processing partner creation"""
        event = AuditEvent(
            event_type=AuditEventType.PARTNER_CREATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="partner",
            entity_id=partner_id,
            action="created",
            details={
                "partner_name": partner_name,
                "facility_location": facility_location,
            },
        )
        self.log_event(event)
    
    def log_partner_updated(
        self,
        user_id: str,
        partner_id: str,
        changes: Dict[str, Any],
    ) -> None:
        """Log processing partner update"""
        event = AuditEvent(
            event_type=AuditEventType.PARTNER_UPDATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="partner",
            entity_id=partner_id,
            action="updated",
            details=changes,
        )
        self.log_event(event)
    
    def log_reservation_created(
        self,
        user_id: str,
        reservation_id: str,
        society_id: str,
        crop_type: str,
        quantity_kg: Decimal,
    ) -> None:
        """Log reservation creation"""
        event = AuditEvent(
            event_type=AuditEventType.RESERVATION_CREATED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="reservation",
            entity_id=reservation_id,
            action="created",
            crop_type=crop_type,
            details={
                "society_id": society_id,
                "quantity_kg": quantity_kg,
            },
        )
        self.log_event(event)
    
    def log_reservation_confirmed(
        self,
        user_id: str,
        reservation_id: str,
        society_id: str,
        crop_type: str,
        confirmed_quantity_kg: Decimal,
    ) -> None:
        """Log reservation confirmation"""
        event = AuditEvent(
            event_type=AuditEventType.RESERVATION_CONFIRMED,
            timestamp=datetime.now(),
            user_id=user_id,
            entity_type="reservation",
            entity_id=reservation_id,
            action="confirmed",
            crop_type=crop_type,
            details={
                "society_id": society_id,
                "confirmed_quantity_kg": confirmed_quantity_kg,
            },
        )
        self.log_event(event)
