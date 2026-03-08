"""
Demand prediction and reservation API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

from ..services.demand_service import DemandService


router = APIRouter(prefix="/api/demand", tags=["demand"])
demand_service = DemandService()


class PredictDemandInput(BaseModel):
    """Input model for demand prediction"""
    society_id: str
    crop_type: str
    delivery_date: str  # ISO format date


class ReserveInventoryInput(BaseModel):
    """Input model for inventory reservation"""
    fpo_id: str
    society_id: str
    crop_type: str
    quantity_kg: float
    delivery_date: str  # ISO format date


@router.post("/predict")
async def predict_demand(input_data: PredictDemandInput):
    """
    Predict society demand based on historical patterns.
    
    Args:
        input_data: Prediction request data
    
    Returns:
        Demand prediction
    """
    try:
        delivery_date = date.fromisoformat(input_data.delivery_date)
        
        prediction = demand_service.predict_society_demand(
            society_id=input_data.society_id,
            crop_type=input_data.crop_type,
            delivery_date=delivery_date,
        )
        
        return prediction.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reserve")
async def reserve_inventory(input_data: ReserveInventoryInput):
    """
    Reserve inventory for society demand.
    
    Args:
        input_data: Reservation request data
    
    Returns:
        Created reservation
    """
    try:
        delivery_date = date.fromisoformat(input_data.delivery_date)
        
        reservation = demand_service.reserve_inventory(
            fpo_id=input_data.fpo_id,
            society_id=input_data.society_id,
            crop_type=input_data.crop_type,
            quantity_kg=Decimal(str(input_data.quantity_kg)),
            delivery_date=delivery_date,
        )
        
        return reservation.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/confirm/{reservation_id}")
async def confirm_reservation(reservation_id: str):
    """
    Confirm a predicted reservation.
    
    Args:
        reservation_id: Reservation identifier
    
    Returns:
        Updated reservation
    """
    try:
        reservation = demand_service.confirm_reservation(reservation_id)
        
        return reservation.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/reservations")
async def get_reservations(
    fpo_id: str,
    crop_type: str,
    allocation_date: str,
):
    """
    Get active reservations for allocation.
    
    Args:
        fpo_id: FPO identifier
        crop_type: Crop type
        allocation_date: Date for allocation (ISO format)
    
    Returns:
        List of active reservations
    """
    try:
        alloc_date = date.fromisoformat(allocation_date)
        
        reservations = demand_service.get_active_reservations(
            fpo_id=fpo_id,
            crop_type=crop_type,
            allocation_date=alloc_date,
        )
        
        return {
            "reservations": [r.to_dict() for r in reservations],
            "total": len(reservations)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
