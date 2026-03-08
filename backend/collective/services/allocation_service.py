"""
Allocation service for priority-based inventory allocation
"""

from typing import List, Optional, Tuple
from datetime import date
from decimal import Decimal
import uuid

from ..models import (
    Allocation,
    ChannelAllocation,
    ChannelType,
    AllocationStatus,
    FulfillmentStatus,
    Reservation,
    ReservationStatus,
)
from ..db import InventoryRepository, AllocationRepository
from ..validation import InventoryValidator, AllocationValidator
from ..audit import AuditLogger


class AllocationService:
    """
    Service for priority-based allocation of collective inventory.
    
    Implements the three-tier allocation strategy:
    - Priority 1: Society reservations (timestamp order)
    - Priority 2: Processing partners (rate order)
    - Priority 3: Mandi/buyers
    """
    
    def __init__(
        self,
        inventory_repository: Optional[InventoryRepository] = None,
        allocation_repository: Optional[AllocationRepository] = None,
        processing_partner_repository = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.inventory_repository = inventory_repository or InventoryRepository()
        self.allocation_repository = allocation_repository or AllocationRepository()
        self.audit_logger = audit_logger or AuditLogger()
        
        # Import here to avoid circular dependency
        from ..db.repositories import ProcessingPartnerRepository
        self.processing_partner_repository = processing_partner_repository or ProcessingPartnerRepository()
    
    def allocate_priority_1_societies(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
        available_quantity: Decimal,
        reservations: List[Reservation],
    ) -> Tuple[List[ChannelAllocation], Decimal, List[dict]]:
        """
        Allocate inventory to societies (Priority 1).
        
        Allocates to societies in timestamp order. If insufficient inventory,
        flags unfulfilled reservations.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date of allocation
            available_quantity: Available inventory quantity
            reservations: List of active reservations
        
        Returns:
            Tuple of:
            - List of ChannelAllocation objects for societies
            - Remaining available quantity after allocation
            - List of unfulfilled reservation warnings
        """
        channel_allocations = []
        remaining = available_quantity
        unfulfilled_warnings = []
        
        # Sort reservations by timestamp (earliest first)
        sorted_reservations = sorted(reservations, key=lambda r: r.reservation_timestamp)
        
        # Get society price (placeholder - in production, this would come from pricing service)
        society_price_per_kg = Decimal("50.0")  # ₹50/kg for societies
        
        for reservation in sorted_reservations:
            # Calculate how much we can allocate
            allocated_qty = min(reservation.reserved_quantity_kg, remaining)
            
            if allocated_qty > 0:
                # Create channel allocation
                revenue = allocated_qty * society_price_per_kg
                
                channel_allocation = ChannelAllocation(
                    channel_type=ChannelType.SOCIETY,
                    channel_id=reservation.society_id,
                    channel_name=f"Society-{reservation.society_id}",  # In production, get actual name
                    quantity_kg=allocated_qty,
                    price_per_kg=society_price_per_kg,
                    revenue=revenue,
                    priority=1,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )
                
                channel_allocations.append(channel_allocation)
                remaining -= allocated_qty
            
            # Check if reservation was fully fulfilled
            if allocated_qty < reservation.reserved_quantity_kg:
                unfulfilled_qty = reservation.reserved_quantity_kg - allocated_qty
                unfulfilled_warnings.append({
                    "reservation_id": reservation.reservation_id,
                    "society_id": reservation.society_id,
                    "crop_type": crop_type,
                    "requested_qty": reservation.reserved_quantity_kg,
                    "allocated_qty": allocated_qty,
                    "unfulfilled_qty": unfulfilled_qty,
                    "message": f"Insufficient inventory: requested {reservation.reserved_quantity_kg} kg, "
                               f"allocated {allocated_qty} kg, unfulfilled {unfulfilled_qty} kg",
                })
        
        return channel_allocations, remaining, unfulfilled_warnings
    
    def get_active_reservations(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
    ) -> List[Reservation]:
        """
        Query active reservations for allocation date.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date for allocation
        
        Returns:
            List of active reservations
        """
        # Get reservations from DynamoDB via repository
        all_reservations = self.inventory_repository.get_reservations_by_date(allocation_date)
        
        # Filter by crop type and status
        active_reservations = [
            r for r in all_reservations
            if r.crop_type == crop_type
            and r.status in [ReservationStatus.PREDICTED, ReservationStatus.CONFIRMED]
        ]
        
        return active_reservations
    
    def flag_unfulfilled_reservations(
        self,
        unfulfilled_warnings: List[dict],
    ) -> None:
        """
        Flag unfulfilled reservations for coordinator attention.
        
        In production, this would:
        - Log to CloudWatch
        - Send notifications to FPO coordinator
        - Update dashboard alerts
        
        Args:
            unfulfilled_warnings: List of unfulfilled reservation details
        """
        if not unfulfilled_warnings:
            return
        
        # Log warnings
        print("=" * 80)
        print("UNFULFILLED RESERVATIONS ALERT")
        print("=" * 80)
        
        for warning in unfulfilled_warnings:
            print(f"\nReservation ID: {warning['reservation_id']}")
            print(f"Society ID: {warning['society_id']}")
            print(f"Crop Type: {warning['crop_type']}")
            print(f"Requested: {warning['requested_qty']} kg")
            print(f"Allocated: {warning['allocated_qty']} kg")
            print(f"Unfulfilled: {warning['unfulfilled_qty']} kg")
            print(f"Message: {warning['message']}")
        
        print("=" * 80)
        
        # In production:
        # - Log to CloudWatch Logs
        # - Send SNS notification to coordinator
        # - Update DynamoDB alerts table
        # - Trigger dashboard alert
    def get_processing_partners_for_crop(
        self,
        fpo_id: str,
        crop_type: str,
    ) -> List:
        """
        Query processing partners that handle the specified crop type.

        Args:
            fpo_id: FPO identifier (for future filtering by FPO)
            crop_type: Crop type to filter by

        Returns:
            List of ProcessingPartner objects that have rates/capacity for the crop
        """
        # Get all partners from repository
        all_partners = self.processing_partner_repository.list_partners()

        # Filter partners that have rates and capacity for this crop type
        partners_for_crop = [
            partner for partner in all_partners
            if crop_type in partner.rates_by_crop and crop_type in partner.capacity_by_crop
        ]

        return partners_for_crop

    def allocate_priority_2_processing(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
        available_quantity: Decimal,
    ) -> Tuple[List[ChannelAllocation], Decimal]:
        """
        Allocate inventory to processing partners (Priority 2).

        Allocates to processing partners sorted by rate (highest first).
        Respects partner capacity constraints and quality requirements.

        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date of allocation
            available_quantity: Available inventory quantity after Priority 1

        Returns:
            Tuple of:
            - List of ChannelAllocation objects for processing partners
            - Remaining available quantity after allocation
        """
        channel_allocations = []
        remaining = available_quantity

        # Get processing partners for this crop type
        partners = self.get_processing_partners_for_crop(fpo_id, crop_type)

        # TODO: Filter partners by quality requirements (Requirement 4.5)
        # In production, this would check inventory quality grades against
        # partner.quality_requirements[crop_type] and only allocate to
        # partners whose quality requirements match available inventory

        # Sort partners by rate (highest first) to maximize value
        sorted_partners = sorted(
            partners,
            key=lambda p: p.get_rate(crop_type),
            reverse=True
        )

        # Allocate to each partner up to their capacity
        for partner in sorted_partners:
            if remaining <= 0:
                break

            # Get partner's capacity for this crop
            capacity = partner.get_capacity(crop_type)
            rate = partner.get_rate(crop_type)

            # Allocate up to capacity or remaining inventory, whichever is less
            allocated_qty = min(capacity, remaining)

            if allocated_qty > 0:
                revenue = allocated_qty * rate

                channel_allocation = ChannelAllocation(
                    channel_type=ChannelType.PROCESSING,
                    channel_id=partner.partner_id,
                    channel_name=partner.partner_name,
                    quantity_kg=allocated_qty,
                    price_per_kg=rate,
                    revenue=revenue,
                    priority=2,
                    fulfillment_status=FulfillmentStatus.PENDING,
                )

                channel_allocations.append(channel_allocation)
                remaining -= allocated_qty

        return channel_allocations, remaining
    
    def get_best_mandi_price(
        self,
        crop_type: str,
        allocation_date: date,
    ) -> dict:
        """
        Query best mandi price for the crop type.
        
        In production, this would:
        - Query real-time mandi prices from external API
        - Consider transportation costs
        - Factor in market trends
        
        Args:
            crop_type: Crop type
            allocation_date: Date of allocation
        
        Returns:
            Dictionary with mandi_id, mandi_name, and price_per_kg
        """
        # Placeholder implementation
        # In production, this would query actual mandi prices
        mandi_prices = {
            "tomato": Decimal("35.0"),
            "onion": Decimal("30.0"),
            "potato": Decimal("25.0"),
            "carrot": Decimal("40.0"),
            "cabbage": Decimal("28.0"),
        }
        
        price = mandi_prices.get(crop_type, Decimal("30.0"))
        
        return {
            "mandi_id": "MANDI001",
            "mandi_name": "APMC Market",
            "price_per_kg": price,
        }
    
    def allocate_priority_3_mandi(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
        available_quantity: Decimal,
    ) -> Tuple[List[ChannelAllocation], Decimal]:
        """
        Allocate inventory to mandi/buyers (Priority 3).
        
        Allocates all remaining inventory to the best available mandi.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date of allocation
            available_quantity: Available inventory quantity after Priority 1 and 2
        
        Returns:
            Tuple of:
            - List of ChannelAllocation objects for mandi (0 or 1 allocation)
            - Remaining available quantity after allocation (should be 0)
        """
        channel_allocations = []
        
        # If no inventory remaining, return empty
        if available_quantity <= 0:
            return channel_allocations, Decimal("0")
        
        # Get best mandi price
        best_mandi = self.get_best_mandi_price(crop_type, allocation_date)
        
        # Allocate all remaining inventory to mandi
        revenue = available_quantity * best_mandi["price_per_kg"]
        
        channel_allocation = ChannelAllocation(
            channel_type=ChannelType.MANDI,
            channel_id=best_mandi["mandi_id"],
            channel_name=best_mandi["mandi_name"],
            quantity_kg=available_quantity,
            price_per_kg=best_mandi["price_per_kg"],
            revenue=revenue,
            priority=3,
            fulfillment_status=FulfillmentStatus.PENDING,
        )
        
        channel_allocations.append(channel_allocation)
        
        return channel_allocations, Decimal("0")
    
    def allocate_inventory(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
        user_id: str = "system",
    ) -> Allocation:
        """
        Execute full allocation across all three priorities.
        
        Orchestrates the complete allocation process:
        1. Priority 1: Society reservations (timestamp order)
        2. Priority 2: Processing partners (rate order)
        3. Priority 3: Mandi/buyers
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date of allocation
            user_id: User performing the action
        
        Returns:
            Allocation object with all channel allocations
        
        Raises:
            ValueError: If inventory not found
        """
        # Get inventory
        inventory = self.inventory_repository.get_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        available = inventory.available_quantity_kg
        all_channel_allocations = []
        
        # Priority 1: Society reservations
        reservations = self.get_active_reservations(fpo_id, crop_type, allocation_date)
        
        society_allocations, remaining, unfulfilled_warnings = self.allocate_priority_1_societies(
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=allocation_date,
            available_quantity=available,
            reservations=reservations,
        )
        
        all_channel_allocations.extend(society_allocations)
        
        # Flag unfulfilled reservations
        if unfulfilled_warnings:
            self.flag_unfulfilled_reservations(unfulfilled_warnings)
        
        # Priority 2: Processing partners
        if remaining > 0:
            processing_allocations, remaining = self.allocate_priority_2_processing(
                fpo_id=fpo_id,
                crop_type=crop_type,
                allocation_date=allocation_date,
                available_quantity=remaining,
            )
            all_channel_allocations.extend(processing_allocations)
        
        # Priority 3: Mandi/buyers
        if remaining > 0:
            mandi_allocations, remaining = self.allocate_priority_3_mandi(
                fpo_id=fpo_id,
                crop_type=crop_type,
                allocation_date=allocation_date,
                available_quantity=remaining,
            )
            all_channel_allocations.extend(mandi_allocations)
        
        # Calculate totals
        total_quantity = sum(ca.quantity_kg for ca in all_channel_allocations)
        total_revenue = sum(ca.revenue for ca in all_channel_allocations)
        
        blended_realization = (
            total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
        )
        
        # Create allocation object
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=allocation_date,
            channel_allocations=all_channel_allocations,
            total_quantity_kg=total_quantity,
            blended_realization_per_kg=blended_realization,
            status=AllocationStatus.PENDING,
        )
        
        # Validate allocation before saving
        AllocationValidator.validate_no_over_allocation(allocation, available)
        AllocationValidator.validate_priority_ordering(allocation)
        AllocationValidator.validate_allocation_totals(allocation)
        InventoryValidator.validate_allocation_prices(allocation)
        
        # Update inventory
        inventory.allocated_quantity_kg += total_quantity
        inventory.available_quantity_kg = remaining
        
        # Validate inventory invariants after update
        InventoryValidator.validate_inventory_invariants(inventory)
        
        self.inventory_repository.save_inventory(inventory)
        
        # Save allocation to PostgreSQL
        self.allocation_repository.create_allocation(allocation)
        
        # Log audit event
        self.audit_logger.log_allocation_created(
            user_id=user_id,
            allocation_id=allocation.allocation_id,
            fpo_id=fpo_id,
            crop_type=crop_type,
            total_quantity_kg=total_quantity,
            blended_realization_per_kg=blended_realization,
            channel_allocations=all_channel_allocations,
        )
        
        return allocation
    
    def allocate_inventory_priority_1(
        self,
        fpo_id: str,
        crop_type: str,
        allocation_date: date,
    ) -> Allocation:
        """
        Execute Priority 1 allocation (societies only).
        
        This is a partial allocation that only handles Priority 1.
        Full allocation (Priority 1, 2, 3) will be implemented in task 8.8.
        
        Args:
            fpo_id: FPO identifier
            crop_type: Crop type
            allocation_date: Date of allocation
        
        Returns:
            Allocation object with Priority 1 allocations
        
        Raises:
            ValueError: If inventory not found
        """
        # Get inventory
        inventory = self.inventory_repository.get_inventory(fpo_id, crop_type)
        
        if inventory is None:
            raise ValueError(f"No inventory found for {fpo_id} - {crop_type}")
        
        available = inventory.available_quantity_kg
        
        # Get active reservations
        reservations = self.get_active_reservations(fpo_id, crop_type, allocation_date)
        
        # Allocate Priority 1: Societies
        channel_allocations, remaining, unfulfilled_warnings = self.allocate_priority_1_societies(
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=allocation_date,
            available_quantity=available,
            reservations=reservations,
        )
        
        # Flag unfulfilled reservations
        if unfulfilled_warnings:
            self.flag_unfulfilled_reservations(unfulfilled_warnings)
        
        # Calculate totals
        total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
        total_revenue = sum(ca.revenue for ca in channel_allocations)
        
        blended_realization = (
            total_revenue / total_quantity if total_quantity > 0 else Decimal("0")
        )
        
        # Create allocation object
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=allocation_date,
            channel_allocations=channel_allocations,
            total_quantity_kg=total_quantity,
            blended_realization_per_kg=blended_realization,
            status=AllocationStatus.PENDING,
        )
        
        # Update inventory
        inventory.allocated_quantity_kg += total_quantity
        inventory.available_quantity_kg = remaining
        self.inventory_repository.save_inventory(inventory)
        
        # Save allocation
        self.allocation_repository.create_allocation(allocation)
        
        return allocation
