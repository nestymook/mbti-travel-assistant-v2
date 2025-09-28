"""Restaurant data models for MCP server.

This module contains dataclass models for restaurant data structure,
including operating hours, sentiment, metadata, and complete restaurant records.
Follows PEP8 style guidelines and includes JSON serialization support.
"""

import json
import re
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

    def validate(self) -> List[str]:
        """Validate operating hours data structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate time format pattern (HH:MM - HH:MM)
        time_pattern = re.compile(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$')
        
        for day_type, hours_list in [
            ('Mon - Fri', self.mon_fri),
            ('Sat - Sun', self.sat_sun),
            ('Public Holiday', self.public_holiday)
        ]:
            if not isinstance(hours_list, list):
                errors.append(f"{day_type} must be a list")
                continue
            
            for i, time_range in enumerate(hours_list):
                if not isinstance(time_range, str):
                    errors.append(f"{day_type}[{i}] must be a string")
                    continue
                
                if not time_pattern.match(time_range.strip()):
                    errors.append(
                        f"{day_type}[{i}] invalid format: '{time_range}'. "
                        "Expected format: 'HH:MM - HH:MM'"
                    )
        
        return errors


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

    def validate(self) -> List[str]:
        """Validate sentiment data structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate that all sentiment values are non-negative integers
        for field_name, value in [
            ('likes', self.likes),
            ('dislikes', self.dislikes),
            ('neutral', self.neutral)
        ]:
            if not isinstance(value, int):
                errors.append(f"{field_name} must be an integer")
            elif value < 0:
                errors.append(f"{field_name} cannot be negative")
        
        # Validate that at least one sentiment value exists
        if self.likes == 0 and self.dislikes == 0 and self.neutral == 0:
            errors.append("At least one sentiment value must be greater than 0")
        
        return errors

    @property
    def total_responses(self) -> int:
        """Calculate total number of sentiment responses.
        
        Returns:
            Total count of all sentiment responses
        """
        return self.likes + self.dislikes + self.neutral

    @property
    def positive_percentage(self) -> float:
        """Calculate percentage of positive sentiment (likes + neutral).
        
        Returns:
            Percentage of positive sentiment (0.0 to 100.0)
        """
        if self.total_responses == 0:
            return 0.0
        return (self.likes + self.neutral) / self.total_responses * 100.0

    @property
    def likes_percentage(self) -> float:
        """Calculate percentage of likes only.
        
        Returns:
            Percentage of likes (0.0 to 100.0)
        """
        if self.total_responses == 0:
            return 0.0
        return self.likes / self.total_responses * 100.0


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

    def validate(self) -> List[str]:
        """Validate restaurant metadata structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate data_quality
        if not isinstance(self.data_quality, str):
            errors.append("data_quality must be a string")
        elif len(self.data_quality.strip()) == 0:
            errors.append("data_quality cannot be empty")
        
        # Validate version
        if not isinstance(self.version, str):
            errors.append("version must be a string")
        elif len(self.version.strip()) == 0:
            errors.append("version cannot be empty")
        
        # Validate quality_score
        if not isinstance(self.quality_score, int):
            errors.append("quality_score must be an integer")
        elif self.quality_score < 0 or self.quality_score > 100:
            errors.append("quality_score must be between 0 and 100")
        
        return errors


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

    def validate(self) -> List[str]:
        """Validate complete restaurant data structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_string_fields = [
            ('id', self.id),
            ('name', self.name),
            ('address', self.address),
            ('location_category', self.location_category),
            ('district', self.district),
            ('price_range', self.price_range)
        ]
        
        for field_name, value in required_string_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate ID format (should be alphanumeric with underscores/hyphens)
        if isinstance(self.id, str) and self.id:
            if not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
                errors.append(
                    "id must contain only alphanumeric characters, "
                    "underscores, and hyphens"
                )
        
        # Validate meal_type list
        if not isinstance(self.meal_type, list):
            errors.append("meal_type must be a list")
        elif len(self.meal_type) == 0:
            errors.append("meal_type cannot be empty")
        else:
            for i, meal in enumerate(self.meal_type):
                if not isinstance(meal, str):
                    errors.append(f"meal_type[{i}] must be a string")
                elif len(meal.strip()) == 0:
                    errors.append(f"meal_type[{i}] cannot be empty")
        
        # Validate price_range format
        valid_price_ranges = ['$', '$$', '$$$', '$$$$', 'Budget', 'Mid-range', 'Expensive']
        if isinstance(self.price_range, str) and self.price_range:
            if self.price_range not in valid_price_ranges:
                errors.append(
                    f"price_range must be one of: {', '.join(valid_price_ranges)}"
                )
        
        # Validate nested objects
        if not isinstance(self.sentiment, Sentiment):
            errors.append("sentiment must be a Sentiment object")
        else:
            sentiment_errors = self.sentiment.validate()
            errors.extend([f"sentiment.{error}" for error in sentiment_errors])
        
        if not isinstance(self.operating_hours, OperatingHours):
            errors.append("operating_hours must be an OperatingHours object")
        else:
            hours_errors = self.operating_hours.validate()
            errors.extend([f"operating_hours.{error}" for error in hours_errors])
        
        if not isinstance(self.metadata, RestaurantMetadata):
            errors.append("metadata must be a RestaurantMetadata object")
        else:
            metadata_errors = self.metadata.validate()
            errors.extend([f"metadata.{error}" for error in metadata_errors])
        
        return errors

    def is_valid(self) -> bool:
        """Check if restaurant data is valid.
        
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate()) == 0

    def validate_for_frontend(self) -> List[str]:
        """Validate restaurant data for frontend consumption.
        
        This checks additional requirements specific to frontend display.
        
        Returns:
            List of validation error messages
        """
        errors = self.validate()
        
        # Additional frontend-specific validations
        if isinstance(self.name, str) and len(self.name) > 100:
            errors.append("name too long for frontend display (max 100 characters)")
        
        if isinstance(self.address, str) and len(self.address) > 200:
            errors.append("address too long for frontend display (max 200 characters)")
        
        # Ensure sentiment data is meaningful for display
        if isinstance(self.sentiment, Sentiment):
            if self.sentiment.total_responses < 1:
                errors.append("sentiment data insufficient for frontend display")
        
        return errors


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

    def validate(self) -> List[str]:
        """Validate file metadata structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_string_fields = [
            ('timestamp', self.timestamp),
            ('version', self.version),
            ('district', self.district),
            ('location_category', self.location_category),
            ('sanitized_at', self.sanitized_at),
            ('sanitization_version', self.sanitization_version)
        ]
        
        for field_name, value in required_string_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate numeric fields
        if not isinstance(self.record_count, int):
            errors.append("record_count must be an integer")
        elif self.record_count < 0:
            errors.append("record_count cannot be negative")
        
        if not isinstance(self.file_size, int):
            errors.append("file_size must be an integer")
        elif self.file_size < 0:
            errors.append("file_size cannot be negative")
        
        return errors


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

    def validate(self) -> List[str]:
        """Validate complete restaurant data file structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate metadata
        if not isinstance(self.metadata, FileMetadata):
            errors.append("metadata must be a FileMetadata object")
        else:
            metadata_errors = self.metadata.validate()
            errors.extend([f"metadata.{error}" for error in metadata_errors])
        
        # Validate restaurants list
        if not isinstance(self.restaurants, list):
            errors.append("restaurants must be a list")
        else:
            # Validate each restaurant
            for i, restaurant in enumerate(self.restaurants):
                if not isinstance(restaurant, Restaurant):
                    errors.append(f"restaurants[{i}] must be a Restaurant object")
                else:
                    restaurant_errors = restaurant.validate()
                    errors.extend([
                        f"restaurants[{i}].{error}" for error in restaurant_errors
                    ])
            
            # Validate record count consistency
            if isinstance(self.metadata, FileMetadata):
                if self.metadata.record_count != len(self.restaurants):
                    errors.append(
                        f"metadata.record_count ({self.metadata.record_count}) "
                        f"does not match actual restaurant count ({len(self.restaurants)})"
                    )
        
        return errors

    def is_valid(self) -> bool:
        """Check if restaurant data file is valid.
        
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate()) == 0

    def get_restaurants_by_district(self, district: str) -> List[Restaurant]:
        """Get restaurants filtered by district.
        
        Args:
            district: District name to filter by
            
        Returns:
            List of restaurants in the specified district
        """
        return [
            restaurant for restaurant in self.restaurants
            if restaurant.district.lower() == district.lower()
        ]

    def get_restaurants_by_meal_type(self, meal_type: str) -> List[Restaurant]:
        """Get restaurants filtered by meal type.
        
        Args:
            meal_type: Meal type to filter by
            
        Returns:
            List of restaurants serving the specified meal type
        """
        return [
            restaurant for restaurant in self.restaurants
            if any(mt.lower() == meal_type.lower() for mt in restaurant.meal_type)
        ]

    def get_valid_restaurants(self) -> List[Restaurant]:
        """Get only valid restaurants from the file.
        
        Returns:
            List of restaurants that pass validation
        """
        return [
            restaurant for restaurant in self.restaurants
            if restaurant.is_valid()
        ]