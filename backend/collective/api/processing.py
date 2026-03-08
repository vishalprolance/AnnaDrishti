"""
Processing partner management API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict
from pydantic import BaseModel, Field

from ..services.processing_service import ProcessingPartnerService


router = APIRouter(prefix="/api/processing-partners", tags=["processing-partners"])
processing_service = ProcessingPartnerService()


class ProcessingPartnerRegistrationInput(BaseModel):
    """Input model for processing partner registration"""
    partner_name: str = Field(..., description="Name of the processing partner")
    contact_details: Dict[str, str] = Field(..., description="Contact information (email, phone, etc.)")
    facility_location: str = Field(..., description="Location of processing facility")
    rates_by_crop: Dict[str, float] = Field(..., description="Pre-agreed rates per kg by crop type")
    capacity_by_crop: Dict[str, float] = Field(..., description="Daily/weekly capacity in kg by crop type")
    quality_requirements: Dict[str, str] = Field(default_factory=dict, description="Quality requirements by crop type")
    pickup_schedule: str = Field(..., description="Pickup schedule description")


class ProcessingPartnerUpdateInput(BaseModel):
    """Input model for processing partner updates"""
    partner_name: Optional[str] = None
    contact_details: Optional[Dict[str, str]] = None
    facility_location: Optional[str] = None
    rates_by_crop: Optional[Dict[str, float]] = None
    capacity_by_crop: Optional[Dict[str, float]] = None
    quality_requirements: Optional[Dict[str, str]] = None
    pickup_schedule: Optional[str] = None


@router.post("")
async def register_processing_partner(input_data: ProcessingPartnerRegistrationInput):
    """
    Register a new processing partner.
    
    This endpoint creates a new processing partner profile with pre-agreed rates,
    capacity constraints, and quality requirements.
    
    Args:
        input_data: Processing partner registration data
    
    Returns:
        Created processing partner profile with unique partner_id
    
    Raises:
        HTTPException 400: If validation fails (e.g., negative rates or capacities)
    """
    try:
        partner = processing_service.register_partner(
            partner_name=input_data.partner_name,
            contact_details=input_data.contact_details,
            facility_location=input_data.facility_location,
            rates_by_crop=input_data.rates_by_crop,
            capacity_by_crop=input_data.capacity_by_crop,
            quality_requirements=input_data.quality_requirements,
            pickup_schedule=input_data.pickup_schedule,
        )
        
        return partner.to_dict()
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{partner_id}")
async def get_processing_partner(partner_id: str):
    """
    Get processing partner profile by ID.
    
    Args:
        partner_id: Partner identifier
    
    Returns:
        Processing partner profile
    
    Raises:
        HTTPException 404: If partner not found
    """
    partner = processing_service.get_partner(partner_id)
    
    if partner is None:
        raise HTTPException(
            status_code=404,
            detail=f"Processing partner not found: {partner_id}"
        )
    
    return partner.to_dict()


@router.put("/{partner_id}")
async def update_processing_partner(partner_id: str, input_data: ProcessingPartnerUpdateInput):
    """
    Update processing partner profile.
    
    Args:
        partner_id: Partner identifier
        input_data: Fields to update
    
    Returns:
        Updated processing partner profile
    
    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If partner not found
    """
    try:
        # Convert to dict, excluding None values
        updates = input_data.model_dump(exclude_none=True)
        
        partner = processing_service.update_partner(partner_id, **updates)
        
        return partner.to_dict()
    
    except ValueError as e:
        # Check if it's a not found error
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{partner_id}")
async def delete_processing_partner(partner_id: str):
    """
    Delete processing partner profile.
    
    Args:
        partner_id: Partner identifier
    
    Returns:
        Success message
    
    Raises:
        HTTPException 404: If partner not found
    """
    try:
        processing_service.delete_partner(partner_id)
        
        return {
            "message": f"Processing partner {partner_id} deleted successfully"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
async def list_processing_partners(
    crop_type: Optional[str] = None,
):
    """
    List processing partners with optional filtering.
    
    Args:
        crop_type: Optional crop type filter (returns only partners that handle this crop)
    
    Returns:
        List of processing partner profiles
    """
    partners = processing_service.list_partners(crop_type=crop_type)
    
    return {
        "partners": [p.to_dict() for p in partners],
        "total": len(partners)
    }
