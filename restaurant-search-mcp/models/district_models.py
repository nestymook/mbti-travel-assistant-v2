"""District configuration models for MCP server.

This module contains dataclass models for district configuration structure,
including district, region, and master configuration data.
Follows PEP8 style guidelines and includes JSON serialization support.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class RateLimit:
    """Rate limiting configuration for district crawling.
    
    Attributes:
        requests_per_minute: Maximum requests per minute
        burst_limit: Burst request limit
        backoff_multiplier: Backoff multiplier for retries
        max_retries: Maximum number of retries
    """
    requests_per_minute: int
    burst_limit: int
    backoff_multiplier: int
    max_retries: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RateLimit':
        """Create RateLimit from dictionary data.
        
        Args:
            data: Dictionary containing rate limit data
            
        Returns:
            RateLimit instance
        """
        return cls(
            requests_per_minute=data.get('requestsPerMinute', 20),
            burst_limit=data.get('burstLimit', 2),
            backoff_multiplier=data.get('backoffMultiplier', 2),
            max_retries=data.get('maxRetries', 3)
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'requestsPerMinute': self.requests_per_minute,
            'burstLimit': self.burst_limit,
            'backoffMultiplier': self.backoff_multiplier,
            'maxRetries': self.max_retries
        }


@dataclass
class CrawlingHours:
    """Crawling hours configuration for district.
    
    Attributes:
        start: Start time for crawling (e.g., "09:00")
        end: End time for crawling (e.g., "23:00")
        timezone: Timezone for crawling hours
    """
    start: str
    end: str
    timezone: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlingHours':
        """Create CrawlingHours from dictionary data.
        
        Args:
            data: Dictionary containing crawling hours data
            
        Returns:
            CrawlingHours instance
        """
        return cls(
            start=data.get('start', '09:00'),
            end=data.get('end', '23:00'),
            timezone=data.get('timezone', 'Asia/Hong_Kong')
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of crawling hours
        """
        return asdict(self)


@dataclass
class Checkpoints:
    """Checkpoint configuration for district crawling.
    
    Attributes:
        enabled: Whether checkpoints are enabled
        interval_pages: Pages between checkpoints
        save_progress_every: Save progress frequency
    """
    enabled: bool
    interval_pages: int
    save_progress_every: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoints':
        """Create Checkpoints from dictionary data.
        
        Args:
            data: Dictionary containing checkpoint data
            
        Returns:
            Checkpoints instance
        """
        return cls(
            enabled=data.get('enabled', True),
            interval_pages=data.get('intervalPages', 10),
            save_progress_every=data.get('saveProgressEvery', 5)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'enabled': self.enabled,
            'intervalPages': self.interval_pages,
            'saveProgressEvery': self.save_progress_every
        }


@dataclass
class DistrictConfig:
    """Configuration for a single district.
    
    Attributes:
        name: District name
        priority: Priority level for crawling
        max_pages: Maximum pages to crawl
        rate_limit: Rate limiting configuration
        crawling_hours: Crawling hours configuration
        checkpoints: Checkpoint configuration
        openrice_urls: List of OpenRice URLs for the district
        district_id: Unique district identifier
    """
    name: str
    priority: int
    max_pages: int
    rate_limit: RateLimit
    crawling_hours: CrawlingHours
    checkpoints: Checkpoints
    openrice_urls: List[str]
    district_id: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistrictConfig':
        """Create DistrictConfig from dictionary data.
        
        Args:
            data: Dictionary containing district configuration data
            
        Returns:
            DistrictConfig instance
        """
        return cls(
            name=data.get('name', ''),
            priority=data.get('priority', 1),
            max_pages=data.get('maxPages', 50),
            rate_limit=RateLimit.from_dict(data.get('rateLimit', {})),
            crawling_hours=CrawlingHours.from_dict(data.get('crawlingHours', {})),
            checkpoints=Checkpoints.from_dict(data.get('checkpoints', {})),
            openrice_urls=data.get('openriceUrls', []),
            district_id=data.get('districtId', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'name': self.name,
            'priority': self.priority,
            'maxPages': self.max_pages,
            'rateLimit': self.rate_limit.to_dict(),
            'crawlingHours': self.crawling_hours.to_dict(),
            'checkpoints': self.checkpoints.to_dict(),
            'openriceUrls': self.openrice_urls,
            'districtId': self.district_id
        }

    def validate_district_name(self) -> bool:
        """Validate that district name is not empty.
        
        Returns:
            True if district name is valid, False otherwise
        """
        return bool(self.name and self.name.strip())

    def get_s3_path_key(self, region_name: str) -> str:
        """Generate S3 path key for this district.
        
        Args:
            region_name: Name of the region (e.g., "hong-kong-island")
            
        Returns:
            S3 path key for district data file
        """
        # Convert region name to lowercase and replace spaces with hyphens
        region_key = region_name.lower().replace(' ', '-')
        # Convert district name to lowercase and replace spaces with hyphens
        district_key = self.name.lower().replace(' ', '-')
        return f"{region_key}/{district_key}.json"


@dataclass
class RegionConfig:
    """Configuration for a region containing multiple districts.
    
    Attributes:
        name: Region name
        category: Region category
        priority: Priority level for the region
        districts: List of district configurations
    """
    name: str
    category: str
    priority: int
    districts: List[DistrictConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionConfig':
        """Create RegionConfig from dictionary data.
        
        Args:
            data: Dictionary containing region configuration data
            
        Returns:
            RegionConfig instance
        """
        return cls(
            name=data.get('name', ''),
            category=data.get('category', ''),
            priority=data.get('priority', 1),
            districts=[
                DistrictConfig.from_dict(district_data)
                for district_data in data.get('districts', [])
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of region configuration
        """
        return {
            'name': self.name,
            'category': self.category,
            'priority': self.priority,
            'districts': [district.to_dict() for district in self.districts]
        }

    def get_district_names(self) -> List[str]:
        """Get list of all district names in this region.
        
        Returns:
            List of district names
        """
        return [district.name for district in self.districts]

    def find_district_by_name(self, district_name: str) -> Optional[DistrictConfig]:
        """Find district configuration by name.
        
        Args:
            district_name: Name of the district to find
            
        Returns:
            DistrictConfig if found, None otherwise
        """
        for district in self.districts:
            if district.name.lower() == district_name.lower():
                return district
        return None

    def validate_districts(self) -> List[str]:
        """Validate all districts in the region.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        district_names = set()
        
        for district in self.districts:
            if not district.validate_district_name():
                errors.append(f"Invalid district name: '{district.name}'")
            
            if district.name in district_names:
                errors.append(f"Duplicate district name: '{district.name}'")
            district_names.add(district.name)
            
        return errors


@dataclass
class GlobalRateLimit:
    """Global rate limiting configuration.
    
    Attributes:
        max_concurrent_districts: Maximum concurrent districts
        global_requests_per_minute: Global requests per minute limit
        cooldown_between_districts: Cooldown time between districts
    """
    max_concurrent_districts: int
    global_requests_per_minute: int
    cooldown_between_districts: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalRateLimit':
        """Create GlobalRateLimit from dictionary data.
        
        Args:
            data: Dictionary containing global rate limit data
            
        Returns:
            GlobalRateLimit instance
        """
        return cls(
            max_concurrent_districts=data.get('maxConcurrentDistricts', 3),
            global_requests_per_minute=data.get('globalRequestsPerMinute', 100),
            cooldown_between_districts=data.get('cooldownBetweenDistricts', 300)
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'maxConcurrentDistricts': self.max_concurrent_districts,
            'globalRequestsPerMinute': self.global_requests_per_minute,
            'cooldownBetweenDistricts': self.cooldown_between_districts
        }


@dataclass
class CrawlingStrategy:
    """Crawling strategy configuration.
    
    Attributes:
        priority_based: Whether to use priority-based crawling
        respect_crawling_hours: Whether to respect crawling hours
        enable_checkpoints: Whether to enable checkpoints
        global_rate_limit: Global rate limiting configuration
    """
    priority_based: bool
    respect_crawling_hours: bool
    enable_checkpoints: bool
    global_rate_limit: GlobalRateLimit

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlingStrategy':
        """Create CrawlingStrategy from dictionary data.
        
        Args:
            data: Dictionary containing crawling strategy data
            
        Returns:
            CrawlingStrategy instance
        """
        return cls(
            priority_based=data.get('priorityBased', True),
            respect_crawling_hours=data.get('respectCrawlingHours', True),
            enable_checkpoints=data.get('enableCheckpoints', True),
            global_rate_limit=GlobalRateLimit.from_dict(
                data.get('globalRateLimit', {})
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'priorityBased': self.priority_based,
            'respectCrawlingHours': self.respect_crawling_hours,
            'enableCheckpoints': self.enable_checkpoints,
            'globalRateLimit': self.global_rate_limit.to_dict()
        }


@dataclass
class RegionReference:
    """Reference to a region configuration file.
    
    Attributes:
        config_file: Name of the configuration file
        enabled: Whether the region is enabled
        scheduling_weight: Weight for scheduling priority
    """
    config_file: str
    enabled: bool
    scheduling_weight: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionReference':
        """Create RegionReference from dictionary data.
        
        Args:
            data: Dictionary containing region reference data
            
        Returns:
            RegionReference instance
        """
        return cls(
            config_file=data.get('configFile', ''),
            enabled=data.get('enabled', True),
            scheduling_weight=data.get('schedulingWeight', 10)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'configFile': self.config_file,
            'enabled': self.enabled,
            'schedulingWeight': self.scheduling_weight
        }


@dataclass
class MasterConfig:
    """Master configuration containing all regions and global settings.
    
    Attributes:
        version: Configuration version
        last_updated: Last update timestamp
        crawling_strategy: Crawling strategy configuration
        regions: List of region references
    """
    version: str
    last_updated: str
    crawling_strategy: CrawlingStrategy
    regions: List[RegionReference]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasterConfig':
        """Create MasterConfig from dictionary data.
        
        Args:
            data: Dictionary containing master configuration data
            
        Returns:
            MasterConfig instance
        """
        return cls(
            version=data.get('version', '1.0.0'),
            last_updated=data.get('lastUpdated', ''),
            crawling_strategy=CrawlingStrategy.from_dict(
                data.get('crawlingStrategy', {})
            ),
            regions=[
                RegionReference.from_dict(region_data)
                for region_data in data.get('regions', [])
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'version': self.version,
            'lastUpdated': self.last_updated,
            'crawlingStrategy': self.crawling_strategy.to_dict(),
            'regions': [region.to_dict() for region in self.regions]
        }

    def to_json(self) -> str:
        """Convert master configuration to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'MasterConfig':
        """Create MasterConfig from JSON string.
        
        Args:
            json_str: JSON string containing master configuration
            
        Returns:
            MasterConfig instance
            
        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_enabled_regions(self) -> List[RegionReference]:
        """Get list of enabled regions.
        
        Returns:
            List of enabled region references
        """
        return [region for region in self.regions if region.enabled]

    def validate_configuration(self) -> List[str]:
        """Validate the master configuration.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        
        if not self.version:
            errors.append("Version is required")
            
        if not self.last_updated:
            errors.append("Last updated timestamp is required")
            
        config_files = set()
        for region in self.regions:
            if not region.config_file:
                errors.append("Region config file is required")
            elif region.config_file in config_files:
                errors.append(f"Duplicate config file: {region.config_file}")
            else:
                config_files.add(region.config_file)
                
        return errors


# Utility functions for working with district configurations

def load_master_config_from_file(file_path: str) -> MasterConfig:
    """Load master configuration from JSON file.
    
    Args:
        file_path: Path to the master configuration file
        
    Returns:
        MasterConfig instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return MasterConfig.from_json(f.read())


def load_region_config_from_file(file_path: str) -> RegionConfig:
    """Load region configuration from JSON file.
    
    Args:
        file_path: Path to the region configuration file
        
    Returns:
        RegionConfig instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return RegionConfig.from_dict(data)


def get_all_district_names_from_regions(regions: List[RegionConfig]) -> Dict[str, str]:
    """Get mapping of district names to region names.
    
    Args:
        regions: List of region configurations
        
    Returns:
        Dictionary mapping district names to region names
    """
    district_to_region = {}
    for region in regions:
        for district in region.districts:
            district_to_region[district.name] = region.name
    return district_to_region


def validate_district_name_across_regions(
    district_name: str, 
    regions: List[RegionConfig]
) -> bool:
    """Validate if a district name exists across all regions.
    
    Args:
        district_name: Name of the district to validate
        regions: List of region configurations
        
    Returns:
        True if district exists, False otherwise
    """
    for region in regions:
        if region.find_district_by_name(district_name):
            return True
    return False