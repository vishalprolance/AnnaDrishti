"""
Processing partner management service
"""

from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
import uuid

from ..models import ProcessingPartner
from ..db import ProcessingPartnerRepository


class ProcessingPartnerService:
    """
    Service for processing partner management.
    
    Handles partner registration, profile updates, and queries.
    """
    
    def __init__(self, repository: Optional[ProcessingPartnerRepository] = None):
        self.repository = repository or ProcessingPartnerRepository()
    
    def register_partner(
        self,
        partner_name: str,
        contact_details: Dict[str, str],
        facility_location: str,
        rates_by_crop: Dict[str, float],
        capacity_by_crop: Dict[str, float],
        quality_requirements: Dict[str, str],
        pickup_schedule: str,
    ) -> ProcessingPartner:
        """
        Register a new processing partner.
        
        Args:
            partner_name: Name of the processing partner
            contact_details: Contact information
            facility_location: Location of processing facility
            rates_by_crop: Pre-agreed rates per kg by crop type
            capacity_by_crop: Daily/weekly capacity in kg by crop type
            quality_requirements: Quality requirements by crop type
            pickup_schedule: Pickup schedule description
        
        Returns:
            Created ProcessingPartner
        
        Raises:
            ValueError: If validation fails
        """
        # Generate unique ID
        partner_id = f"PP-{str(uuid.uuid4())[:8].upper()}"
        
        # Convert rates and capacities to Decimal
        rates = {k: Decimal(str(v)) for k, v in rates_by_crop.items()}
        capacities = {k: Decimal(str(v)) for k, v in capacity_by_crop.items()}
        
        # Create partner profile
        partner = ProcessingPartner(
            partner_id=partner_id,
            partner_name=partner_name,
            contact_details=contact_details,
            facility_location=facility_location,
            rates_by_crop=rates,
            capacity_by_crop=capacities,
            quality_requirements=quality_requirements,
            pickup_schedule=pickup_schedule,
            created_at=datetime.now(),
        )
        
        # Save to database
        self.repository.create_partner(partner)
        
        return partner
    
    def get_partner(self, partner_id: str) -> Optional[ProcessingPartner]:
        """
        Get processing partner by ID.
        
        Args:
            partner_id: Partner identifier
        
        Returns:
            ProcessingPartner or None if not found
        """
        return self.repository.get_partner(partner_id)
    
    def update_partner(
        self,
        partner_id: str,
        **updates
    ) -> ProcessingPartner:
        """
        Update processing partner profile.
        
        Args:
            partner_id: Partner identifier
            **updates: Fields to update
        
        Returns:
            Updated ProcessingPartner
        
        Raises:
            ValueError: If partner not found or validation fails
        """
        partner = self.repository.get_partner(partner_id)
        
        if partner is None:
            raise ValueError(f"Processing partner not found: {partner_id}")
        
        # Update fields
        if "partner_name" in updates:
            partner.partner_name = updates["partner_name"]
        
        if "contact_details" in updates:
            partner.contact_details = updates["contact_details"]
        
        if "facility_location" in updates:
            partner.facility_location = updates["facility_location"]
        
        if "rates_by_crop" in updates:
            partner.rates_by_crop = {
                k: Decimal(str(v)) for k, v in updates["rates_by_crop"].items()
            }
        
        if "capacity_by_crop" in updates:
            partner.capacity_by_crop = {
                k: Decimal(str(v)) for k, v in updates["capacity_by_crop"].items()
            }
        
        if "quality_requirements" in updates:
            partner.quality_requirements = updates["quality_requirements"]
        
        if "pickup_schedule" in updates:
            partner.pickup_schedule = updates["pickup_schedule"]
        
        # Validate updated partner
        partner.__post_init__()
        
        # Save to database
        self.repository.update_partner(partner)
        
        return partner
    
    def delete_partner(self, partner_id: str) -> None:
        """
        Delete processing partner profile.
        
        Args:
            partner_id: Partner identifier
        
        Raises:
            ValueError: If partner not found
        """
        partner = self.repository.get_partner(partner_id)
        
        if partner is None:
            raise ValueError(f"Processing partner not found: {partner_id}")
        
        self.repository.delete_partner(partner_id)
    
    def list_partners(
        self,
        crop_type: Optional[str] = None,
    ) -> List[ProcessingPartner]:
        """
        List processing partners with optional filtering.
        
        Args:
            crop_type: Optional crop type filter
        
        Returns:
            List of ProcessingPartner objects
        """
        partners = self.repository.list_partners()
        
        # Filter by crop type if specified
        if crop_type:
            partners = [
                p for p in partners
                if crop_type in p.rates_by_crop
            ]
        
        return partners
