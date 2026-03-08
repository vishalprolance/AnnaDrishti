"""
Feature flags for backward compatibility and gradual rollout.

This module provides feature flag management to enable/disable collective
selling mode while maintaining backward compatibility with existing workflows.
"""

import os
from typing import Dict, Optional
from enum import Enum


class FeatureFlag(Enum):
    """Available feature flags"""
    COLLECTIVE_MODE = "collective_mode"
    DEMAND_PREDICTION = "demand_prediction"
    PROCESSING_ALLOCATION = "processing_allocation"
    MANDI_ALLOCATION = "mandi_allocation"
    BLENDED_REALIZATION = "blended_realization"


class FeatureFlagManager:
    """
    Manages feature flags for the collective selling system.
    
    Feature flags can be controlled via:
    1. Environment variables (highest priority)
    2. Configuration file
    3. Default values (lowest priority)
    
    This enables gradual rollout and A/B testing of collective features.
    """
    
    def __init__(self):
        """Initialize feature flag manager with default values"""
        self._flags: Dict[str, bool] = {
            FeatureFlag.COLLECTIVE_MODE.value: self._get_env_flag(
                "COLLECTIVE_MODE_ENABLED",
                default=True
            ),
            FeatureFlag.DEMAND_PREDICTION.value: self._get_env_flag(
                "DEMAND_PREDICTION_ENABLED",
                default=True
            ),
            FeatureFlag.PROCESSING_ALLOCATION.value: self._get_env_flag(
                "PROCESSING_ALLOCATION_ENABLED",
                default=True
            ),
            FeatureFlag.MANDI_ALLOCATION.value: self._get_env_flag(
                "MANDI_ALLOCATION_ENABLED",
                default=True
            ),
            FeatureFlag.BLENDED_REALIZATION.value: self._get_env_flag(
                "BLENDED_REALIZATION_ENABLED",
                default=True
            ),
        }
    
    def _get_env_flag(self, env_var: str, default: bool = False) -> bool:
        """
        Get feature flag value from environment variable.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set
        
        Returns:
            Boolean flag value
        """
        value = os.getenv(env_var)
        
        if value is None:
            return default
        
        # Parse boolean from string
        return value.lower() in ("true", "1", "yes", "on", "enabled")
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag: Feature flag to check
        
        Returns:
            True if enabled, False otherwise
        """
        return self._flags.get(flag.value, False)
    
    def enable(self, flag: FeatureFlag) -> None:
        """
        Enable a feature flag.
        
        Args:
            flag: Feature flag to enable
        """
        self._flags[flag.value] = True
    
    def disable(self, flag: FeatureFlag) -> None:
        """
        Disable a feature flag.
        
        Args:
            flag: Feature flag to disable
        """
        self._flags[flag.value] = False
    
    def get_all_flags(self) -> Dict[str, bool]:
        """
        Get all feature flags and their current values.
        
        Returns:
            Dictionary of flag names to boolean values
        """
        return self._flags.copy()
    
    def is_collective_mode_enabled(self) -> bool:
        """
        Check if collective selling mode is enabled.
        
        When disabled, the system operates in legacy individual farmer mode.
        
        Returns:
            True if collective mode is enabled
        """
        return self.is_enabled(FeatureFlag.COLLECTIVE_MODE)


# Global feature flag manager instance
_feature_flag_manager: Optional[FeatureFlagManager] = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """
    Get the global feature flag manager instance.
    
    Returns:
        FeatureFlagManager singleton instance
    """
    global _feature_flag_manager
    
    if _feature_flag_manager is None:
        _feature_flag_manager = FeatureFlagManager()
    
    return _feature_flag_manager


def is_collective_mode_enabled() -> bool:
    """
    Convenience function to check if collective mode is enabled.
    
    Returns:
        True if collective mode is enabled
    """
    return get_feature_flag_manager().is_collective_mode_enabled()
