"""
Inventory API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from ..services.inventory_service import InventoryService
from ..models import FarmerContribution


router = APIRouter(prefix="/api/inventory", tags=["inventory"])
inventory_service = InventoryService()


@router.get("/{fpo_id}/{crop_type}")
async def get_inventory(
    fpo_id: str,
    crop_type: str,
    start_date: Optional[str] = Query(None, description="Filter contributions from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter contributions until this date (ISO format)"),
):
    """
    Get collective inventory for FPO and crop type.
    
    Returns aggregate totals and per-farmer breakdowns.
    Optionally filter by date range.
    
    Args:
        fpo_id: FPO identifier
        crop_type: Crop type
        start_date: Optional start date for filtering (ISO format)
        end_date: Optional end date for filtering (ISO format)
    
    Returns:
        Inventory breakdown with farmer contributions
    """
    inventory = inventory_service.get_collective_inventory(fpo_id, crop_type)
    
    if inventory is None:
        raise HTTPException(
            status_code=404,
            detail=f"No inventory found for FPO {fpo_id} and crop {crop_type}"
        )
    
    # Get breakdown
    breakdown = inventory_service.get_inventory_breakdown(fpo_id, crop_type)
    
    # Apply date filtering if provided
    if start_date or end_date:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        filtered_contributions = []
        for contrib in breakdown["contributions"]:
            contrib_dt = datetime.fromisoformat(contrib["timestamp"])
            
            if start_dt and contrib_dt < start_dt:
                continue
            if end_dt and contrib_dt > end_dt:
                continue
            
            filtered_contributions.append(contrib)
        
        # Recalculate totals for filtered contributions
        if filtered_contributions:
            filtered_total = sum(Decimal(c["quantity_kg"]) for c in filtered_contributions)
            breakdown["contributions"] = filtered_contributions
            breakdown["farmer_count"] = len(filtered_contributions)
            breakdown["filtered_total_kg"] = str(filtered_total)
            breakdown["filtered"] = True
        else:
            breakdown["contributions"] = []
            breakdown["farmer_count"] = 0
            breakdown["filtered_total_kg"] = "0"
            breakdown["filtered"] = True
    
    return breakdown


@router.get("/{fpo_id}/summary")
async def get_inventory_summary(fpo_id: str):
    """
    Get inventory summary across all crop types for an FPO.
    
    Args:
        fpo_id: FPO identifier
    
    Returns:
        Summary of inventory by crop type
    """
    summary = inventory_service.get_inventory_summary(fpo_id)
    
    return {
        "fpo_id": fpo_id,
        "crop_types": summary,
        "total_crop_types": len(summary)
    }


@router.post("/contributions")
async def add_contribution(
    fpo_id: str,
    farmer_id: str,
    farmer_name: str,
    crop_type: str,
    quantity_kg: float,
    quality_grade: str,
):
    """
    Add farmer contribution to collective inventory.
    
    Args:
        fpo_id: FPO identifier
        farmer_id: Farmer identifier
        farmer_name: Farmer name
        crop_type: Crop type
        quantity_kg: Quantity in kg
        quality_grade: Quality grade (A, B, or C)
    
    Returns:
        Created contribution
    """
    try:
        contribution = inventory_service.aggregate_farmer_contribution(
            fpo_id=fpo_id,
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            crop_type=crop_type,
            quantity_kg=Decimal(str(quantity_kg)),
            quality_grade=quality_grade,
        )
        
        return {
            "contribution_id": contribution.contribution_id,
            "farmer_id": contribution.farmer_id,
            "farmer_name": contribution.farmer_name,
            "crop_type": contribution.crop_type,
            "quantity_kg": str(contribution.quantity_kg),
            "quality_grade": contribution.quality_grade.value,
            "timestamp": contribution.timestamp.isoformat(),
            "allocated": contribution.allocated,
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/farmers/{farmer_id}/contributions")
async def get_farmer_contributions(farmer_id: str):
    """
    Get all contributions by a farmer.
    
    Args:
        farmer_id: Farmer identifier
    
    Returns:
        List of farmer contributions
    """
    contributions = inventory_service.get_farmer_contributions(farmer_id)
    
    return {
        "farmer_id": farmer_id,
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
        "total_contributions": len(contributions),
    }
