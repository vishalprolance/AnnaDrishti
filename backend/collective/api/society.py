"""
Society management API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel

from ..services.society_service import SocietyService


router = APIRouter(prefix="/api/societies", tags=["societies"])
society_service = SocietyService()


class CropPreferenceInput(BaseModel):
    """Input model for crop preference"""
    crop_type: str
    typical_quantity_kg: float


class SocietyRegistrationInput(BaseModel):
    """Input model for society registration"""
    society_name: str
    location: str
    contact_details: Dict[str, str]
    delivery_address: str
    delivery_frequency: str
    preferred_day: str
    preferred_time_window: str
    crop_preferences: Optional[List[CropPreferenceInput]] = None


class SocietyUpdateInput(BaseModel):
    """Input model for society updates"""
    society_name: Optional[str] = None
    location: Optional[str] = None
    contact_details: Optional[Dict[str, str]] = None
    delivery_address: Optional[str] = None
    delivery_frequency: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_time_window: Optional[str] = None
    crop_preferences: Optional[List[CropPreferenceInput]] = None


@router.post("")
async def register_society(input_data: SocietyRegistrationInput):
    """
    Register a new society.
    
    Args:
        input_data: Society registration data
    
    Returns:
        Created society profile
    """
    try:
        # Convert crop preferences
        crop_prefs = None
        if input_data.crop_preferences:
            crop_prefs = [
                {
                    "crop_type": p.crop_type,
                    "typical_quantity_kg": p.typical_quantity_kg
                }
                for p in input_data.crop_preferences
            ]
        
        society = society_service.register_society(
            society_name=input_data.society_name,
            location=input_data.location,
            contact_details=input_data.contact_details,
            delivery_address=input_data.delivery_address,
            delivery_frequency=input_data.delivery_frequency,
            preferred_day=input_data.preferred_day,
            preferred_time_window=input_data.preferred_time_window,
            crop_preferences=crop_prefs,
        )
        
        return society.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{society_id}")
async def get_society(society_id: str):
    """
    Get society profile by ID.
    
    Args:
        society_id: Society identifier
    
    Returns:
        Society profile
    """
    society = society_service.get_society(society_id)
    
    if society is None:
        raise HTTPException(
            status_code=404,
            detail=f"Society not found: {society_id}"
        )
    
    return society.to_dict()


@router.put("/{society_id}")
async def update_society(society_id: str, input_data: SocietyUpdateInput):
    """
    Update society profile.
    
    Args:
        society_id: Society identifier
        input_data: Fields to update
    
    Returns:
        Updated society profile
    """
    try:
        # Convert to dict, excluding None values
        updates = input_data.dict(exclude_none=True)
        
        # Convert crop preferences if present
        if "crop_preferences" in updates and updates["crop_preferences"]:
            updates["crop_preferences"] = [
                {
                    "crop_type": p["crop_type"],
                    "typical_quantity_kg": p["typical_quantity_kg"]
                }
                for p in updates["crop_preferences"]
            ]
        
        society = society_service.update_society(society_id, **updates)
        
        return society.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{society_id}")
async def delete_society(society_id: str):
    """
    Delete society profile.
    
    Args:
        society_id: Society identifier
    
    Returns:
        Success message
    """
    try:
        society_service.delete_society(society_id)
        
        return {
            "message": f"Society {society_id} deleted successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
async def list_societies(
    fpo_id: Optional[str] = None,
    location: Optional[str] = None,
):
    """
    List societies with optional filtering.
    
    Args:
        fpo_id: Optional FPO ID filter
        location: Optional location filter
    
    Returns:
        List of society profiles
    """
    societies = society_service.list_societies(fpo_id=fpo_id, location=location)
    
    return {
        "societies": [s.to_dict() for s in societies],
        "total": len(societies)
    }
