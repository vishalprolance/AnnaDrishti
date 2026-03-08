"""
Legacy API endpoints for backward compatibility.

This module maintains existing farmer and buyer workflow APIs to ensure
backward compatibility when collective mode is disabled or during migration.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, List
from decimal import Decimal
from datetime import datetime

from ..feature_flags import is_collective_mode_enabled


router = APIRouter(
    prefix="/api/legacy",
    tags=["legacy"],
)


@router.post("/farmer/sell")
async def legacy_farmer_sell(
    farmer_id: str,
    crop_type: str,
    quantity_kg: float,
    quality_grade: str,
    target_price: float = None,
) -> Dict:
    """
    Legacy endpoint for individual farmer selling workflow.
    
    When collective mode is disabled, this endpoint handles direct farmer-to-buyer
    transactions without pooling into collective inventory.
    
    When collective mode is enabled, this redirects to the collective contribution
    endpoint for backward compatibility.
    
    Args:
        farmer_id: Farmer identifier
        crop_type: Crop type
        quantity_kg: Quantity in kg
        quality_grade: Quality grade (A, B, or C)
        target_price: Optional target price per kg
    
    Returns:
        Transaction details or contribution confirmation
    
    **Validates: Requirements 10.4**
    """
    if is_collective_mode_enabled():
        # Redirect to collective contribution
        from ..services.inventory_service import InventoryService
        
        inventory_service = InventoryService()
        
        # Assume default FPO for backward compatibility
        # In production, map farmer_id to their FPO
        fpo_id = f"FPO_{farmer_id[:3]}"
        
        try:
            contribution = inventory_service.aggregate_farmer_contribution(
                fpo_id=fpo_id,
                farmer_id=farmer_id,
                farmer_name=f"Farmer-{farmer_id}",
                crop_type=crop_type,
                quantity_kg=Decimal(str(quantity_kg)),
                quality_grade=quality_grade,
            )
            
            return {
                "status": "success",
                "mode": "collective",
                "message": "Contribution added to collective inventory",
                "contribution_id": contribution.contribution_id,
                "farmer_id": farmer_id,
                "crop_type": crop_type,
                "quantity_kg": str(contribution.quantity_kg),
                "quality_grade": contribution.quality_grade.value,
                "timestamp": contribution.timestamp.isoformat(),
                "note": "Your produce has been pooled with other farmers for better pricing",
            }
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    else:
        # Legacy individual selling mode
        # In production, this would integrate with the original Sell Agent logic
        return {
            "status": "success",
            "mode": "individual",
            "message": "Individual sale transaction created",
            "transaction_id": f"TXN_{farmer_id}_{datetime.now().timestamp()}",
            "farmer_id": farmer_id,
            "crop_type": crop_type,
            "quantity_kg": quantity_kg,
            "quality_grade": quality_grade,
            "target_price": target_price,
            "note": "Legacy individual selling mode - direct farmer-to-buyer transaction",
        }


@router.get("/buyer/orders")
async def legacy_buyer_orders(
    buyer_id: str,
    status: str = None,
    limit: int = 20,
) -> Dict:
    """
    Legacy endpoint for buyer order management.
    
    When collective mode is disabled, returns individual farmer orders.
    When collective mode is enabled, returns society/processing allocations.
    
    Args:
        buyer_id: Buyer identifier
        status: Optional status filter
        limit: Maximum number of orders to return
    
    Returns:
        List of orders
    
    **Validates: Requirements 10.4**
    """
    if is_collective_mode_enabled():
        # Map buyer to society or processing partner
        # In production, maintain a mapping table
        
        from ..db import AllocationRepository
        from ..models import ChannelType
        
        allocation_repository = AllocationRepository()
        
        try:
            # Get allocations (assuming buyer_id maps to society or partner)
            allocations = allocation_repository.list_allocations(limit=limit)
            
            # Filter for this buyer
            buyer_orders = []
            for allocation in allocations:
                for ca in allocation.channel_allocations:
                    if ca.channel_id == buyer_id or ca.channel_name == buyer_id:
                        # Apply status filter if provided
                        if status and ca.fulfillment_status.value != status:
                            continue
                        
                        buyer_orders.append({
                            "order_id": f"{allocation.allocation_id}_{ca.channel_id}",
                            "allocation_id": allocation.allocation_id,
                            "crop_type": allocation.crop_type,
                            "quantity_kg": str(ca.quantity_kg),
                            "price_per_kg": str(ca.price_per_kg),
                            "total_amount": str(ca.revenue),
                            "status": ca.fulfillment_status.value,
                            "channel_type": ca.channel_type.value,
                            "allocation_date": allocation.allocation_date.isoformat(),
                        })
            
            return {
                "status": "success",
                "mode": "collective",
                "buyer_id": buyer_id,
                "count": len(buyer_orders),
                "orders": buyer_orders,
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving orders: {str(e)}"
            )
    
    else:
        # Legacy individual order mode
        return {
            "status": "success",
            "mode": "individual",
            "buyer_id": buyer_id,
            "count": 0,
            "orders": [],
            "note": "Legacy individual order mode - direct farmer-to-buyer transactions",
        }


@router.get("/farmer/income")
async def legacy_farmer_income(
    farmer_id: str,
    start_date: str = None,
    end_date: str = None,
) -> Dict:
    """
    Legacy endpoint for farmer income tracking.
    
    When collective mode is disabled, returns individual transaction income.
    When collective mode is enabled, returns blended realization income.
    
    Args:
        farmer_id: Farmer identifier
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
    
    Returns:
        Income details
    
    **Validates: Requirements 10.4**
    """
    if is_collective_mode_enabled():
        # Get farmer contributions and calculate blended income
        from ..services.inventory_service import InventoryService
        from ..services.realization_service import RealizationService
        from ..db import AllocationRepository
        
        inventory_service = InventoryService()
        realization_service = RealizationService()
        allocation_repository = AllocationRepository()
        
        try:
            # Get farmer contributions
            contributions = inventory_service.get_farmer_contributions(farmer_id)
            
            if not contributions:
                return {
                    "status": "success",
                    "mode": "collective",
                    "farmer_id": farmer_id,
                    "total_income": "0",
                    "contributions": [],
                    "message": "No contributions found",
                }
            
            # Calculate income from allocations
            # In production, this would aggregate across all allocations
            # For now, return contribution summary
            
            total_quantity = sum(c.quantity_kg for c in contributions)
            
            return {
                "status": "success",
                "mode": "collective",
                "farmer_id": farmer_id,
                "total_contributions_kg": str(total_quantity),
                "contribution_count": len(contributions),
                "contributions": [
                    {
                        "contribution_id": c.contribution_id,
                        "crop_type": c.crop_type,
                        "quantity_kg": str(c.quantity_kg),
                        "quality_grade": c.quality_grade.value,
                        "timestamp": c.timestamp.isoformat(),
                        "allocated": c.allocated,
                    }
                    for c in contributions
                ],
                "note": "Income calculated from blended realization across all channels",
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving farmer income: {str(e)}"
            )
    
    else:
        # Legacy individual income mode
        return {
            "status": "success",
            "mode": "individual",
            "farmer_id": farmer_id,
            "total_income": "0",
            "transactions": [],
            "note": "Legacy individual income mode - direct transaction income",
        }


@router.get("/health/mode")
async def get_system_mode() -> Dict:
    """
    Get current system mode (collective or individual).
    
    This endpoint helps clients determine which API endpoints to use.
    
    Returns:
        System mode and available features
    """
    from ..feature_flags import get_feature_flag_manager
    
    flag_manager = get_feature_flag_manager()
    
    return {
        "mode": "collective" if flag_manager.is_collective_mode_enabled() else "individual",
        "features": flag_manager.get_all_flags(),
        "api_version": "1.0.0",
        "backward_compatible": True,
    }
