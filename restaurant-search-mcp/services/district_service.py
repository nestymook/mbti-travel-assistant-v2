"""District service for configuration management.

This module provides the DistrictService class for loading and managing
district configuration data from local JSON files. It handles district
validation, region mapping, and file path generation for restaurant data.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from models.district_models import (
    MasterConfig,
    RegionConfig,
    DistrictConfig,
    load_master_config_from_file,
    load_region_config_from_file,
    get_all_district_names_from_regions,
    validate_district_name_across_regions
)


class DistrictConfigurationError(Exception):
    """Exception raised for district configuration errors."""
    pass


class DistrictService:
    """Service for managing district configuration and validation.
    
    This service loads district configuration from local JSON files and provides
    methods for district validation, region mapping, and file path generation.
    """
    
    def __init__(self, config_base_path: str = "config"):
        """Initialize the district service.
        
        Args:
            config_base_path: Base path to configuration directory
        """
        self.config_base_path = Path(config_base_path)
        self.districts_path = self.config_base_path / "districts"
        self.restaurants_path = self.config_base_path / "restaurants"
        
        self._master_config: Optional[MasterConfig] = None
        self._region_configs: Dict[str, RegionConfig] = {}
        self._district_to_region_map: Dict[str, str] = {}
        self._loaded = False
    
    def load_district_config(self) -> None:
        """Load district configuration from local files.
        
        Loads master configuration and all region configuration files.
        Creates district-to-region mapping for fast lookups.
        
        Raises:
            DistrictConfigurationError: If configuration files are missing or invalid
        """
        try:
            # Load master configuration
            master_config_path = self.districts_path / "master-config.json"
            if not master_config_path.exists():
                raise DistrictConfigurationError(
                    f"Master configuration file not found: {master_config_path}"
                )
            
            self._master_config = load_master_config_from_file(str(master_config_path))
            
            # Validate master configuration
            validation_errors = self._master_config.validate_configuration()
            if validation_errors:
                raise DistrictConfigurationError(
                    f"Master configuration validation failed: {', '.join(validation_errors)}"
                )
            
            # Load region configurations
            self._region_configs = {}
            enabled_regions = self._master_config.get_enabled_regions()
            
            for region_ref in enabled_regions:
                region_config_path = self.districts_path / region_ref.config_file
                if not region_config_path.exists():
                    raise DistrictConfigurationError(
                        f"Region configuration file not found: {region_config_path}"
                    )
                
                region_config = load_region_config_from_file(str(region_config_path))
                
                # Validate region configuration (but allow duplicate names for now)
                validation_errors = region_config.validate_districts()
                # Filter out duplicate name errors since the actual config has duplicates
                filtered_errors = [
                    error for error in validation_errors 
                    if not error.startswith("Duplicate district name:")
                ]
                if filtered_errors:
                    raise DistrictConfigurationError(
                        f"Region '{region_config.name}' validation failed: "
                        f"{', '.join(filtered_errors)}"
                    )
                
                self._region_configs[region_config.name] = region_config
            
            # Create district-to-region mapping (handle duplicates by using first occurrence)
            self._district_to_region_map = {}
            for region_name, region_config in self._region_configs.items():
                for district in region_config.districts:
                    # Only add if not already present (first occurrence wins)
                    if district.name not in self._district_to_region_map:
                        self._district_to_region_map[district.name] = region_name
            
            self._loaded = True
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            raise DistrictConfigurationError(f"Failed to load district configuration: {e}")
    
    def _ensure_loaded(self) -> None:
        """Ensure configuration is loaded before operations.
        
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        if not self._loaded:
            raise DistrictConfigurationError(
                "District configuration not loaded. Call load_district_config() first."
            )
    
    def get_all_districts(self) -> Dict[str, List[str]]:
        """Get all districts organized by region.
        
        Returns:
            Dictionary mapping region names to lists of district names
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        result = {}
        for region_name, region_config in self._region_configs.items():
            result[region_name] = region_config.get_district_names()
        
        return result
    
    def get_all_district_names(self) -> List[str]:
        """Get flat list of all district names.
        
        Returns:
            List of all district names across all regions
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        return list(self._district_to_region_map.keys())
    
    def validate_district(self, district_name: str) -> bool:
        """Validate if a district name exists in configuration.
        
        Args:
            district_name: Name of the district to validate
            
        Returns:
            True if district exists, False otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        return district_name in self._district_to_region_map
    
    def validate_districts(self, district_names: List[str]) -> Tuple[List[str], List[str]]:
        """Validate multiple district names.
        
        Args:
            district_names: List of district names to validate
            
        Returns:
            Tuple of (valid_districts, invalid_districts)
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        valid_districts = []
        invalid_districts = []
        
        for district_name in district_names:
            if self.validate_district(district_name):
                valid_districts.append(district_name)
            else:
                invalid_districts.append(district_name)
        
        return valid_districts, invalid_districts
    
    def get_region_for_district(self, district_name: str) -> Optional[str]:
        """Get the region name for a given district.
        
        Args:
            district_name: Name of the district
            
        Returns:
            Region name if district exists, None otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        return self._district_to_region_map.get(district_name)
    
    def get_district_config(self, district_name: str) -> Optional[DistrictConfig]:
        """Get the full configuration for a district.
        
        If there are duplicate district names, returns the first match found.
        
        Args:
            district_name: Name of the district
            
        Returns:
            DistrictConfig if found, None otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        # Search through all regions to find the district (first match wins)
        for region_config in self._region_configs.values():
            district_config = region_config.find_district_by_name(district_name)
            if district_config:
                return district_config
        
        return None
    
    def get_local_file_path_for_district(self, district_name: str) -> Optional[str]:
        """Get local file path for district restaurant data.
        
        Generates path in format: config/restaurants/{region}/{district}.json
        
        Args:
            district_name: Name of the district
            
        Returns:
            Local file path if district exists, None otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        region_name = self.get_region_for_district(district_name)
        if not region_name:
            return None
        
        # Convert region name to lowercase and replace spaces with hyphens
        region_key = region_name.lower().replace(' ', '-')
        # Convert district name to lowercase and replace spaces with hyphens  
        district_key = district_name.lower().replace(' ', '-')
        
        file_path = self.restaurants_path / region_key / f"{district_key}.json"
        return str(file_path)
    
    def get_s3_path_for_district(self, district_name: str) -> Optional[str]:
        """Get S3 path for district restaurant data.
        
        Generates path in format: {region}/{district}.json
        
        Args:
            district_name: Name of the district
            
        Returns:
            S3 path if district exists, None otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        region_name = self.get_region_for_district(district_name)
        if not region_name:
            return None
        
        district_config = self.get_district_config(district_name)
        if not district_config:
            return None
        
        return district_config.get_s3_path_key(region_name)
    
    def check_local_file_exists(self, district_name: str) -> bool:
        """Check if local restaurant data file exists for district.
        
        Args:
            district_name: Name of the district
            
        Returns:
            True if local file exists, False otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        file_path = self.get_local_file_path_for_district(district_name)
        if not file_path:
            return False
        
        return Path(file_path).exists()
    
    def get_districts_by_region(self, region_name: str) -> List[str]:
        """Get all districts in a specific region.
        
        Args:
            region_name: Name of the region
            
        Returns:
            List of district names in the region
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        region_config = self._region_configs.get(region_name)
        if not region_config:
            return []
        
        return region_config.get_district_names()
    
    def get_region_names(self) -> List[str]:
        """Get list of all region names.
        
        Returns:
            List of region names
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        return list(self._region_configs.keys())
    
    def get_master_config(self) -> Optional[MasterConfig]:
        """Get the master configuration.
        
        Returns:
            MasterConfig if loaded, None otherwise
        """
        return self._master_config
    
    def get_region_config(self, region_name: str) -> Optional[RegionConfig]:
        """Get configuration for a specific region.
        
        Args:
            region_name: Name of the region
            
        Returns:
            RegionConfig if found, None otherwise
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        return self._region_configs.get(region_name)
    
    def reload_configuration(self) -> None:
        """Reload all configuration from files.
        
        Useful for picking up configuration changes without restarting.
        
        Raises:
            DistrictConfigurationError: If configuration files are missing or invalid
        """
        self._loaded = False
        self._master_config = None
        self._region_configs = {}
        self._district_to_region_map = {}
        
        self.load_district_config()
    
    def get_configuration_summary(self) -> Dict[str, any]:
        """Get summary of loaded configuration.
        
        Returns:
            Dictionary containing configuration summary
            
        Raises:
            DistrictConfigurationError: If configuration is not loaded
        """
        self._ensure_loaded()
        
        total_districts = len(self._district_to_region_map)
        regions_summary = {}
        
        for region_name, region_config in self._region_configs.items():
            regions_summary[region_name] = {
                'district_count': len(region_config.districts),
                'districts': region_config.get_district_names()
            }
        
        return {
            'master_config_version': self._master_config.version if self._master_config else None,
            'total_regions': len(self._region_configs),
            'total_districts': total_districts,
            'regions': regions_summary,
            'loaded': self._loaded
        }