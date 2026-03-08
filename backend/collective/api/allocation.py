"""
Allocation API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict
from datetime import date

from ..services.allocation_service import AllocationService
from ..services.realization_service import RealizationService
from ..db import InventoryRepository, AllocationRepository
from ..error_handling import handle_integration_error, get_error_handler, log_to_cloudwatch


router = APIRouter(
    prefix="/api/allocations",
    tags=["allocations"],
)

# Initialize services
allocation_service = AllocationService()
realization_service = RealizationService()
inventory_repository = InventoryRepository()
allocation_repository = AllocationRepository()
error_handler = get_error_handler()


@router.get("/{allocation_id}/realization")
async def get_allocation_realization(allocation_id: str) -> Dict:
    """
    Get blended realization and farmer income details for an allocation.
    
    Returns:
    - Blended realization rate per kg
    - Channel-wise breakdown (quantity, revenue, rate)
    - Per-farmer income details
    - Comparison to best single-channel price
    
    **Validates: Requirements 6.3, 6.5**
    """
    try:
        # Get allocation from repository
        allocation = allocation_repository.get_allocation(allocation_id)
        
        if allocation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allocation {allocation_id} not found"
            )
        
        # Get inventory for farmer contributions
        inventory = inventory_repository.get_inventory(
            allocation.fpo_id,
            allocation.crop_type
        )
        
        if inventory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory not found for {allocation.fpo_id} - {allocation.crop_type}"
            )
        
        # Generate realization report
        report = realization_service.get_realization_report(allocation, inventory)
        
        return report
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating realization report: {str(e)}"
        )


@router.get("/{allocation_id}")
async def get_allocation(allocation_id: str) -> Dict:
    """
    Get allocation details by ID.
    
    Returns complete allocation information including channel allocations.
    """
    try:
        allocation = allocation_repository.get_allocation(allocation_id)
        
        if allocation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allocation {allocation_id} not found"
            )
        
        return allocation.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving allocation: {str(e)}"
        )


@router.post("")
async def create_allocation(
    fpo_id: str,
    crop_type: str,
    allocation_date: str,
) -> Dict:
    """
    Create a new allocation for the specified FPO and crop type.
    
    Executes the full three-tier allocation strategy:
    - Priority 1: Society reservations
    - Priority 2: Processing partners
    - Priority 3: Mandi/buyers
    
    Args:
        fpo_id: FPO identifier
        crop_type: Crop type
        allocation_date: Date for allocation (ISO format: YYYY-MM-DD)
    
    Returns:
        Created allocation with all channel allocations
    """
    try:
        # Parse date
        alloc_date = date.fromisoformat(allocation_date)
        
        # Execute allocation
        allocation = allocation_service.allocate_inventory(
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=alloc_date,
        )
        
        return allocation.to_dict()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating allocation: {str(e)}"
        )


@router.get("/{fpo_id}/history")
async def get_allocation_history(
    fpo_id: str,
    crop_type: str = None,
    limit: int = 10,
) -> Dict:
    """
    Get allocation history for an FPO.
    
    Args:
        fpo_id: FPO identifier
        crop_type: Optional crop type filter
        limit: Maximum number of allocations to return
    
    Returns:
        List of historical allocations
    """
    try:
        # Get allocations from repository
        allocations = allocation_repository.list_allocations(
            fpo_id=fpo_id,
            crop_type=crop_type,
            limit=limit,
        )
        
        return {
            "fpo_id": fpo_id,
            "crop_type": crop_type,
            "count": len(allocations),
            "allocations": [a.to_dict() for a in allocations],
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving allocation history: {str(e)}"
        )


@router.put("/{allocation_id}/fulfillment")
async def update_fulfillment_status(
    allocation_id: str,
    channel_id: str,
    fulfillment_status: str,
) -> Dict:
    """
    Update fulfillment status for a channel allocation.
    
    Args:
        allocation_id: Allocation identifier
        channel_id: Channel identifier
        fulfillment_status: New status (pending, in_transit, delivered, completed)
    
    Returns:
        Updated allocation
    """
    try:
        # Get allocation
        allocation = allocation_repository.get_allocation(allocation_id)
        
        if allocation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allocation {allocation_id} not found"
            )
        
        # Find and update channel allocation
        channel_found = False
        for ca in allocation.channel_allocations:
            if ca.channel_id == channel_id:
                from ..models import FulfillmentStatus
                ca.fulfillment_status = FulfillmentStatus(fulfillment_status)
                channel_found = True
                break
        
        if not channel_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found in allocation"
            )
        
        # Save updated allocation
        allocation_repository.update_allocation(allocation)
        
        return allocation.to_dict()
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating fulfillment status: {str(e)}"
        )


@router.get("/mandi")
@handle_integration_error(context="sell_agent_integration", fallback_value={"count": 0, "mandi_allocations": [], "error": "Service temporarily unavailable"})
async def get_mandi_allocations(
    fpo_id: str = None,
    crop_type: str = None,
    status: str = None,
    limit: int = 50,
) -> Dict:
    """
    Get mandi allocations for Sell Agent integration.
    
    This endpoint allows Sell Agent to query allocation data for mandi dispatch.
    Filters allocations to only return mandi channel allocations.
    
    Implements graceful degradation: returns empty list if service unavailable.
    
    Args:
        fpo_id: Optional FPO identifier filter
        crop_type: Optional crop type filter
        status: Optional fulfillment status filter (pending, in_transit, delivered, completed)
        limit: Maximum number of allocations to return (default: 50)
    
    Returns:
        List of mandi allocations with dispatch details
    
    **Validates: Requirements 10.1, 10.2, 10.5**
    """
    try:
        # Log integration request
        log_to_cloudwatch(
            log_group="/anna-drishti/collective/integrations",
            log_stream="sell-agent",
            message=f"Sell Agent querying mandi allocations: fpo_id={fpo_id}, crop_type={crop_type}",
            level="INFO"
        )
        
        # Get allocations from repository
        allocations = allocation_repository.list_allocations(
            fpo_id=fpo_id,
            crop_type=crop_type,
            limit=limit,
        )
        
        # Filter for mandi allocations only
        from ..models import ChannelType, FulfillmentStatus
        
        mandi_allocations = []
        for allocation in allocations:
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.MANDI:
                    # Apply status filter if provided
                    if status and ca.fulfillment_status.value != status:
                        continue
                    
                    mandi_allocations.append({
                        "allocation_id": allocation.allocation_id,
                        "fpo_id": allocation.fpo_id,
                        "crop_type": allocation.crop_type,
                        "allocation_date": allocation.allocation_date.isoformat(),
                        "mandi_id": ca.channel_id,
                        "mandi_name": ca.channel_name,
                        "quantity_kg": str(ca.quantity_kg),
                        "price_per_kg": str(ca.price_per_kg),
                        "revenue": str(ca.revenue),
                        "fulfillment_status": ca.fulfillment_status.value,
                        "priority": ca.priority,
                    })
        
        return {
            "count": len(mandi_allocations),
            "mandi_allocations": mandi_allocations,
            "filters": {
                "fpo_id": fpo_id,
                "crop_type": crop_type,
                "status": status,
            }
        }
        
    except Exception as e:
        # Log error for monitoring
        error_handler.log_error(
            error=e,
            context="sell_agent_integration",
            severity="ERROR",
            additional_info={
                "endpoint": "/api/allocations/mandi",
                "fpo_id": fpo_id,
                "crop_type": crop_type,
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving mandi allocations: {str(e)}"
        )


@router.get("/processing")
@handle_integration_error(context="process_agent_integration", fallback_value={"count": 0, "processing_allocations": [], "error": "Service temporarily unavailable"})
async def get_processing_allocations(
    fpo_id: str = None,
    crop_type: str = None,
    partner_id: str = None,
    status: str = None,
    limit: int = 50,
) -> Dict:
    """
    Get processing partner allocations for Process Agent integration.
    
    This endpoint allows Process Agent to query allocation data for processing
    partner coordination and pickup scheduling.
    
    Implements graceful degradation: returns empty list if service unavailable.
    
    Args:
        fpo_id: Optional FPO identifier filter
        crop_type: Optional crop type filter
        partner_id: Optional processing partner identifier filter
        status: Optional fulfillment status filter (pending, in_transit, delivered, completed)
        limit: Maximum number of allocations to return (default: 50)
    
    Returns:
        List of processing partner allocations with pickup details
    
    **Validates: Requirements 10.2, 10.5**
    """
    try:
        # Log integration request
        log_to_cloudwatch(
            log_group="/anna-drishti/collective/integrations",
            log_stream="process-agent",
            message=f"Process Agent querying processing allocations: fpo_id={fpo_id}, partner_id={partner_id}",
            level="INFO"
        )
        
        # Get allocations from repository
        allocations = allocation_repository.list_allocations(
            fpo_id=fpo_id,
            crop_type=crop_type,
            limit=limit,
        )
        
        # Filter for processing allocations only
        from ..models import ChannelType, FulfillmentStatus
        
        processing_allocations = []
        for allocation in allocations:
            for ca in allocation.channel_allocations:
                if ca.channel_type == ChannelType.PROCESSING:
                    # Apply partner_id filter if provided
                    if partner_id and ca.channel_id != partner_id:
                        continue
                    
                    # Apply status filter if provided
                    if status and ca.fulfillment_status.value != status:
                        continue
                    
                    processing_allocations.append({
                        "allocation_id": allocation.allocation_id,
                        "fpo_id": allocation.fpo_id,
                        "crop_type": allocation.crop_type,
                        "allocation_date": allocation.allocation_date.isoformat(),
                        "partner_id": ca.channel_id,
                        "partner_name": ca.channel_name,
                        "quantity_kg": str(ca.quantity_kg),
                        "price_per_kg": str(ca.price_per_kg),
                        "revenue": str(ca.revenue),
                        "fulfillment_status": ca.fulfillment_status.value,
                        "priority": ca.priority,
                    })
        
        return {
            "count": len(processing_allocations),
            "processing_allocations": processing_allocations,
            "filters": {
                "fpo_id": fpo_id,
                "crop_type": crop_type,
                "partner_id": partner_id,
                "status": status,
            }
        }
        
    except Exception as e:
        # Log error for monitoring
        error_handler.log_error(
            error=e,
            context="process_agent_integration",
            severity="ERROR",
            additional_info={
                "endpoint": "/api/allocations/processing",
                "fpo_id": fpo_id,
                "partner_id": partner_id,
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving processing allocations: {str(e)}"
        )
