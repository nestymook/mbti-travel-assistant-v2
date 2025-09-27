"""Restaurant data models for MCP server.

This module contains dataclass models for restaurant data structure,
including operating hours, sentiment, metadata, and complete restaurant records.
Follows PEP8 style guidelines and includes JSON serialization support.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class OperatingHours:
    """Operating hours for different day types.
    
    Attributes:
        mon_fri: List of time ranges for Monday-Friday (e.g., ["11:30 - 15:30"])
        sat_sun: List of time ranges for Saturday-Sunday
        public_holiday: List of time ranges for public holidays
    """
    mon_fri: List[str]
    sat_sun: List[str]
    public_holiday: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperatingHours':
        """Create OperatingHours from dictionary data.
        
        Args:
            data: Dictionary containing operating hours data
            
        Returns:
            OperatingHours instance
        """
        return cls(
            mon_fri=data.get('Mon - Fri', []),
            sat_sun=data.get('Sat - Sun', []),
            public_holiday=data.get('Public Holiday', [])
        )

    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'Mon - Fri': self.mon_fri,
            'Sat - Sun': self.sat_sun,
            'Public Holiday': self.public_holiday
        }


@dataclass
class Sentiment:
    """Sentiment analysis data for restaurant reviews.
    
    Attributes:
        likes: Number of positive reviews
        dislikes: Number of negative reviews
        neutral: Number of neutral reviews
    """
    likes: int
    dislikes: int
    neutral: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sentiment':
        """Create Sentiment from dictionary data.
        
        Args:
            data: Dictionary containing sentiment data
            
        Returns:
            Sentiment instance
        """
        return cls(
            likes=data.get('likes', 0),
            dislikes=data.get('dislikes', 0),
            neutral=data.get('neutral', 0)
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of sentiment data
        """
        return asdict(self)


@dataclass
class RestaurantMetadata:
    """Metadata for individual restaurant records.
    
    Attributes:
        data_quality: Quality assessment of the data
        version: Version of the restaurant data
        quality_score: Numeric quality score
    """
    data_quality: str
    version: str
    quality_score: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RestaurantMetadata':
        """Create RestaurantMetadata from dictionary data.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            RestaurantMetadata instance
        """
        return cls(
            data_quality=data.get('dataQuality', ''),
            version=data.get('version', ''),
            quality_score=data.get('qualityScore', 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'dataQuality': self.data_quality,
            'version': self.version,
            'qualityScore': self.quality_score
        }


@dataclass
class Restaurant:
    """Complete restaurant record with all associated data.
    
    Attributes:
        id: Unique restaurant identifier
        name: Restaurant name
        address: Full address
        meal_type: List of cuisine types/categories
        sentiment: Sentiment analysis data
        location_category: Category of location
        district: District name
        price_range: Price range indicator
        operating_hours: Operating hours for different day types
        metadata: Restaurant-specific metadata
    """
    id: str
    name: str
    address: str
    meal_type: List[str]
    sentiment: Sentiment
    location_category: str
    district: str
    price_range: str
    operating_hours: OperatingHours
    metadata: RestaurantMetadata

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Restaurant':
        """Create Restaurant from dictionary data.
        
        Args:
            data: Dictionary containing restaurant data
            
        Returns:
            Restaurant instance
        """
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            address=data.get('address', ''),
            meal_type=data.get('mealType', []),
            sentiment=Sentiment.from_dict(data.get('sentiment', {})),
            location_category=data.get('locationCategory', ''),
            district=data.get('district', ''),
            price_range=data.get('priceRange', ''),
            operating_hours=OperatingHours.from_dict(
                data.get('operatingHours', {})
            ),
            metadata=RestaurantMetadata.from_dict(data.get('metadata', {}))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'mealType': self.meal_type,
            'sentiment': self.sentiment.to_dict(),
            'locationCategory': self.location_category,
            'district': self.district,
            'priceRange': self.price_range,
            'operatingHours': self.operating_hours.to_dict(),
            'metadata': self.metadata.to_dict()
        }

    def to_json(self) -> str:
        """Convert restaurant to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class FileMetadata:
    """Metadata for restaurant data files.
    
    Attributes:
        timestamp: File creation/update timestamp
        version: File version
        district: District name for the file
        location_category: Location category
        record_count: Number of restaurant records in file
        file_size: File size in bytes
        sanitized_at: Timestamp when data was sanitized
        sanitization_version: Version of sanitization process
    """
    timestamp: str
    version: str
    district: str
    location_category: str
    record_count: int
    file_size: int
    sanitized_at: str
    sanitization_version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """Create FileMetadata from dictionary data.
        
        Args:
            data: Dictionary containing file metadata
            
        Returns:
            FileMetadata instance
        """
        return cls(
            timestamp=data.get('timestamp', ''),
            version=data.get('version', ''),
            district=data.get('district', ''),
            location_category=data.get('locationCategory', ''),
            record_count=data.get('recordCount', 0),
            file_size=data.get('fileSize', 0),
            sanitized_at=data.get('sanitizedAt', ''),
            sanitization_version=data.get('sanitizationVersion', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary with proper key names for JSON serialization
        """
        return {
            'timestamp': self.timestamp,
            'version': self.version,
            'district': self.district,
            'locationCategory': self.location_category,
            'recordCount': self.record_count,
            'fileSize': self.file_size,
            'sanitizedAt': self.sanitized_at,
            'sanitizationVersion': self.sanitization_version
        }


@dataclass
class RestaurantDataFile:
    """Complete restaurant data file structure.
    
    Attributes:
        metadata: File-level metadata
        restaurants: List of restaurant records
    """
    metadata: FileMetadata
    restaurants: List[Restaurant]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RestaurantDataFile':
        """Create RestaurantDataFile from dictionary data.
        
        Args:
            data: Dictionary containing complete file data
            
        Returns:
            RestaurantDataFile instance
        """
        return cls(
            metadata=FileMetadata.from_dict(data.get('metadata', {})),
            restaurants=[
                Restaurant.from_dict(restaurant_data)
                for restaurant_data in data.get('restaurants', [])
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching JSON structure.
        
        Returns:
            Dictionary representation of complete file data
        """
        return {
            'metadata': self.metadata.to_dict(),
            'restaurants': [restaurant.to_dict() for restaurant in self.restaurants]
        }

    def to_json(self) -> str:
        """Convert complete file data to JSON string.
        
        Returns:
            JSON string representation of file data
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'RestaurantDataFile':
        """Create RestaurantDataFile from JSON string.
        
        Args:
            json_str: JSON string containing file data
            
        Returns:
            RestaurantDataFile instance
            
        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        data = json.loads(json_str)
        return cls.from_dict(data)