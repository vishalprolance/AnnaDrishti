"""
Society management service
"""

from typing import Optional, List, Dict
from datetime import datetime
import uuid

from ..models import SocietyProfile, CropPreference, DeliveryFrequency
from ..db import SocietyRepository


class SocietyService:
    """
    Service for society profile management.
    
    Handles society registration, profile updates, and queries.
    """
    
    def __init__(self, repository: Optional[SocietyRepository] = None):
        self.repository = repository or SocietyRepository()
    
    def register_society(
        self,
        society_name: str,
        location: str,
        contact_details: Dict[str, str],
        delivery_address: str,
        delivery_frequency: str,
        preferred_day: str,
        preferred_time_window: str,
        crop_preferences: Optional[List[Dict[str, any]]] = None,
    ) -> SocietyProfile:
        """
        Register a new society.
        
        Args:
            society_name: Name of the society
            location: Location/address
            contact_details: Contact information
            delivery_address: Delivery address
            delivery_frequency: Delivery frequency (once_weekly, twice_weekly, weekend_only)
            preferred_day: Preferred delivery day
            preferred_time_window: Preferred time window
            crop_preferences: Optional list of crop preferences
        
        Returns:
            Created SocietyProfile
        
        Raises:
            ValueError: If validation fails
        """
        # Generate unique ID
        society_id = str(uuid.uuid4())
        
        # Parse crop preferences
        prefs = []
        if crop_preferences:
            from decimal import Decimal
            prefs = [
                CropPreference(
                    crop_type=p["crop_type"],
                    typical_quantity_kg=Decimal(str(p["typical_quantity_kg"]))
                )
                for p in crop_preferences
            ]
        
        # Create society profile
        society = SocietyProfile(
            society_id=society_id,
            society_name=society_name,
            location=location,
            contact_details=contact_details,
            delivery_address=delivery_address,
            delivery_frequency=DeliveryFrequency(delivery_frequency),
            preferred_day=preferred_day,
            preferred_time_window=preferred_time_window,
            crop_preferences=prefs,
            created_at=datetime.now(),
        )
        
        # Save to database
        self.repository.create_society(society)
        
        return society
    
    def get_society(self, society_id: str) -> Optional[SocietyProfile]:
        """
        Get society profile by ID.
        
        Args:
            society_id: Society identifier
        
        Returns:
            SocietyProfile or None if not found
        """
        return self.repository.get_society(society_id)
    
    def update_society(
        self,
        society_id: str,
        **updates
    ) -> SocietyProfile:
        """
        Update society profile.
        
        Args:
            society_id: Society identifier
            **updates: Fields to update
        
        Returns:
            Updated SocietyProfile
        
        Raises:
            ValueError: If society not found or validation fails
        """
        society = self.repository.get_society(society_id)
        
        if society is None:
            raise ValueError(f"Society not found: {society_id}")
        
        # Update fields
        if "society_name" in updates:
            society.society_name = updates["society_name"]
        
        if "location" in updates:
            society.location = updates["location"]
        
        if "contact_details" in updates:
            society.contact_details = updates["contact_details"]
        
        if "delivery_address" in updates:
            society.delivery_address = updates["delivery_address"]
        
        if "delivery_frequency" in updates:
            society.delivery_frequency = DeliveryFrequency(updates["delivery_frequency"])
        
        if "preferred_day" in updates:
            society.preferred_day = updates["preferred_day"]
        
        if "preferred_time_window" in updates:
            society.preferred_time_window = updates["preferred_time_window"]
        
        if "crop_preferences" in updates:
            from decimal import Decimal
            society.crop_preferences = [
                CropPreference(
                    crop_type=p["crop_type"],
                    typical_quantity_kg=Decimal(str(p["typical_quantity_kg"]))
                )
                for p in updates["crop_preferences"]
            ]
        
        # Save to database
        self.repository.update_society(society)
        
        return society
    
    def delete_society(self, society_id: str) -> None:
        """
        Delete society profile.
        
        Args:
            society_id: Society identifier
        
        Raises:
            ValueError: If society not found
        """
        society = self.repository.get_society(society_id)
        
        if society is None:
            raise ValueError(f"Society not found: {society_id}")
        
        self.repository.delete_society(society_id)
    
    def list_societies(
        self,
        fpo_id: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[SocietyProfile]:
        """
        List societies with optional filtering.
        
        Args:
            fpo_id: Optional FPO ID filter
            location: Optional location filter
        
        Returns:
            List of SocietyProfile objects
        """
        # For now, return all societies
        # In production, implement filtering in repository
        return self.repository.list_societies()
