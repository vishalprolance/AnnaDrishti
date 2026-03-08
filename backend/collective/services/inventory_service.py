"""
Inventory aggregation service
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict
import uuid

from ..models import CollectiveInventory, FarmerContribution, QualityGrade
from ..db import InventoryRepository
from ..validation import InventoryValidator
from ..audit import AuditLogger


class InventoryService:
    """
    Service for collective inventory management.
    
    Implements the inventory aggregation algorithm with atomic updates
    and invariant validation.
    """
    
    def __init__(self, repository: Optional[InventoryRepository] = None, audit_logger: Optional[AuditLogger] = None):
        self.repository = repository or InventoryRepository()
        self.audit_logger = audit_logger or AuditLogger()
    
    def aggregate_farmer_contribution(
        self,
        fpo_id: str,
        farmer_id: str,
        farmer_name: str,
        crop_type: str,
        quantity_kg: Decimal,
        quality_grade: str,
        user_id: str = "system",
    ) -> FarmerContribution:
        """
        Aggregate farmer contribution into collective inventory.
        
        This implements the core aggregation algorithm:
        1. Create contribution record
        2. Add to DynamoDB (atomic update)
        3. Validate invariants
        4. Log audit event
        
        Args:
            fpo_id: FPO identifier
            farmer_id: Farmer identifier
            farmer_name: Farmer name
            crop_type: Crop type
            quantity_kg: Quantity in kg
            quality_grade: Quality grade (A, B, or C)
            user_id: User performing the action
        
        Returns:
            FarmerContribution object
        
        Raises:
            ValueError: If validation fails
        """
        # Create contribution
        contribution = FarmerContribution(
            contribution_id=str(uuid.uuid4()),
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            crop_type=crop_type,
            quantity_kg=quantity_kg,
            quality_grade=QualityGrade(quality_grade),
            timestamp=datetime.now(),
            allocated=False,
        )
        
        # Add to inventory (atomic DynamoDB update)
        self.repository.add_contribution(contribution, fpo_id)
        
        # Verify invariants by fetching updated inventory
        inventory = self.repository.get_inventory(fpo_id, crop_type)
        if inventory:
            inventory.validate_invariants()
        
        # Log audit event
        self.audit_logger.log_inventory_contribution(
            user_id=user_id,
            fpo_id=fpo_id,
            crop_type=crop_type,
            contribution_id=contribution.contribution_id,
            farmer_id=farmer_id,
            quantity_kg=quantity_kg,
            quality_grade=quality_grade,
        )
        
        return contribution
    
    def get_collective_inventory(
        self,
        fpo_id: str,
        crop_type: str,
    ) -> Optional[CollectiveInventory]:
        """
        Get collective inventory for FPO and crop type.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
        
        Returns:
            CollectiveInventory or None if not found
        """
        return self.repository.get_inventory(fpo_id, crop_type)
    
    def get_or_create_inventory(
        self,
        fpo_id: str,
        crop_type: str,
    ) -> CollectiveInventory:
        """
        Get existing inventory or create new empty inventory.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
        
        Returns:
            CollectiveInventory
        """
        inventory = self.repository.get_inventory(fpo_id, crop_type)
        
        if inventory is None:
            # Create new empty inventory
            inventory = CollectiveInventory(
                fpo_id=fpo_id,
                crop_type=crop_type,
                total_quantity_kg=Decimal("0"),
                available_quantity_kg=Decimal("0"),
                reserved_quantity_kg=Decimal("0"),
                allocated_quantity_kg=Decimal("0"),
                contributions=[],
                last_updated=datetime.now(),
            )
            self.repository.save_inventory(inventory)
        
        return inventory
    
    def get_farmer_contributions(
        self,
        farmer_id: str,
    ) -> List[FarmerContribution]:
        """
        Get all contributions by a farmer.
        
        Args:
            farmer_id: Farmer identifier
        
        Returns:
            List of FarmerContribution objects
        """
        return self.repository.get_contributions_by_farmer(farmer_id)
    
    def get_inventory_summary(
        self,
        fpo_id: str,
    ) -> Dict[str, Dict[str, any]]:
        """
        Get inventory summary across all crop types for an FPO.
        
        Args:
            fpo_id: FPO identifier
        
        Returns:
            Dictionary with crop types as keys and inventory details as values
        """
        # Note: This would require a scan or maintaining a separate index
        # For now, we'll return a placeholder
        # In production, consider maintaining a summary table
        return {}
    
    def reserve_inventory(
        self,
        fpo_id: str,
        crop_type: str,
        quantity: Decimal,
    ) -> None:
        """
        Reserve inventory for society demand.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            quantity: Quantity to reserve
        
        Raises:
            ValueError: If insufficient inventory available
        """
        inventory = self.get_collective_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        # Validate reservation
        InventoryValidator.validate_inventory_reservation(inventory, quantity)
        
        # Update inventory
        inventory.reserve_quantity(quantity)
        
        # Validate invariants after update
        InventoryValidator.validate_inventory_invariants(inventory)
        
        self.repository.save_inventory(inventory)
    
    def allocate_inventory(
        self,
        fpo_id: str,
        crop_type: str,
        quantity: Decimal,
    ) -> None:
        """
        Allocate inventory to a channel.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            quantity: Quantity to allocate
        
        Raises:
            ValueError: If insufficient inventory available
        """
        inventory = self.get_collective_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        # Validate allocation
        InventoryValidator.validate_inventory_allocation(inventory, quantity)
        
        # Update inventory
        inventory.allocate_quantity(quantity)
        
        # Validate invariants after update
        InventoryValidator.validate_inventory_invariants(inventory)
        
        self.repository.save_inventory(inventory)
    
    def get_inventory_breakdown(
        self,
        fpo_id: str,
        crop_type: str,
    ) -> Dict[str, any]:
        """
        Get detailed inventory breakdown including per-farmer contributions.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
        
        Returns:
            Dictionary with inventory details and farmer breakdown
        """
        inventory = self.get_collective_inventory(fpo_id, crop_type)
        
        if inventory is None:
            return {
                "fpo_id": fpo_id,
                "crop_type": crop_type,
                "total_quantity_kg": "0",
                "available_quantity_kg": "0",
                "reserved_quantity_kg": "0",
                "allocated_quantity_kg": "0",
                "farmer_count": 0,
                "contributions": [],
            }
        
        return {
            "fpo_id": inventory.fpo_id,
            "crop_type": inventory.crop_type,
            "total_quantity_kg": str(inventory.total_quantity_kg),
            "available_quantity_kg": str(inventory.available_quantity_kg),
            "reserved_quantity_kg": str(inventory.reserved_quantity_kg),
            "allocated_quantity_kg": str(inventory.allocated_quantity_kg),
            "farmer_count": len(inventory.contributions),
            "contributions": [
                {
                    "farmer_id": c.farmer_id,
                    "farmer_name": c.farmer_name,
                    "quantity_kg": str(c.quantity_kg),
                    "quality_grade": c.quality_grade.value,
                    "timestamp": c.timestamp.isoformat(),
                    "allocated": c.allocated,
                }
                for c in inventory.contributions
            ],
            "last_updated": inventory.last_updated.isoformat(),
        }
    
    def delete_contribution(
        self,
        contribution_id: str,
        fpo_id: str,
        crop_type: str,
        user_id: str = "system",
    ) -> None:
        """
        Delete a farmer contribution from inventory.
        
        Validates that the contribution has not been allocated before deletion.
        
        Args:
            contribution_id: Contribution identifier
            fpo_id: FPO identifier
            crop_type: Crop type
            user_id: User performing the action
        
        Raises:
            ValueError: If contribution not found or already allocated
        """
        inventory = self.get_collective_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        # Find contribution
        contribution = None
        for c in inventory.contributions:
            if c.contribution_id == contribution_id:
                contribution = c
                break
        
        if contribution is None:
            raise ValueError(f"Contribution {contribution_id} not found")
        
        # Validate deletion
        InventoryValidator.validate_contribution_deletion(contribution)
        
        # Remove contribution
        inventory.contributions.remove(contribution)
        inventory.total_quantity_kg -= contribution.quantity_kg
        inventory.available_quantity_kg -= contribution.quantity_kg
        
        # Validate invariants after update
        InventoryValidator.validate_inventory_invariants(inventory)
        
        self.repository.save_inventory(inventory)
        
        # Log audit event
        self.audit_logger.log_inventory_contribution_deleted(
            user_id=user_id,
            fpo_id=fpo_id,
            crop_type=crop_type,
            contribution_id=contribution_id,
            farmer_id=contribution.farmer_id,
            quantity_kg=contribution.quantity_kg,
        )
