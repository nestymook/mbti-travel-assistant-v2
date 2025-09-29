"""Tourist spot data models for MBTI Travel Assistant.

This module contains dataclass models for tourist spot data structure,
including operating hours, operating days validation, district and area matching,
and MBTI personality alignment. Follows PEP8 style guidelines and includes
JSON serialization support.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, time
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class SessionType(Enum):
    """Session types for tourist spot assignments."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


@dataclass
class TouristSpotOperatingHours:
    """Operating hours for tourist spots with session validation.
    
    Attributes:
        monday: Operating hours for Monday (e.g., "09:00-18:00")
        tuesday: Operating hours for Tuesday
        wednesday: Operating hours for Wednesday
        thursday: Operating hours for Thursday
        friday: Operating hours for Friday
        saturday: Operating hours for Saturday
        sunday: Operating hours for Sunday
        public_holiday: Operating hours for public holidays
        notes: Additional notes about operating hours
    """
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None
    public_holiday: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TouristSpotOperatingHours':
        """Create TouristSpotOperatingHours from dictionary data.
        
        Args:
            data: Dictionary containing operating hours data
            
        Returns:
            TouristSpotOperatingHours instance
        """
        return cls(
            monday=data.get('monday'),
            tuesday=data.get('tuesday'),
            wednesday=data.get('wednesday'),
            thursday=data.get('thursday'),
            friday=data.get('friday'),
            saturday=data.get('saturday'),
            sunday=data.get('sunday'),
            public_holiday=data.get('public_holiday'),
            notes=data.get('notes')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of operating hours
        """
        return {
            'monday': self.monday,
            'tuesday': self.tuesday,
            'wednesday': self.wednesday,
            'thursday': self.thursday,
            'friday': self.friday,
            'saturday': self.saturday,
            'sunday': self.sunday,
            'public_holiday': self.public_holiday,
            'notes': self.notes
        }

    def validate(self) -> List[str]:
        """Validate operating hours format and consistency.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Time format pattern (HH:MM-HH:MM or "Closed" or "24 hours")
        time_pattern = re.compile(r'^\d{2}:\d{2}-\d{2}:\d{2}$')
        special_values = {'closed', '24 hours', 'by appointment', 'varies'}
        
        days = [
            ('monday', self.monday),
            ('tuesday', self.tuesday),
            ('wednesday', self.wednesday),
            ('thursday', self.thursday),
            ('friday', self.friday),
            ('saturday', self.saturday),
            ('sunday', self.sunday),
            ('public_holiday', self.public_holiday)
        ]
        
        for day_name, hours in days:
            if hours is not None:
                if not isinstance(hours, str):
                    errors.append(f"{day_name} must be a string")
                    continue
                
                hours_clean = hours.strip().lower()
                if hours_clean not in special_values and not time_pattern.match(hours.strip()):
                    errors.append(
                        f"{day_name} invalid format: '{hours}'. "
                        "Expected format: 'HH:MM-HH:MM', 'Closed', '24 hours', etc."
                    )
        
        return errors

    def is_open_during_session(self, session_type: SessionType, day_of_week: str = 'monday') -> bool:
        """Check if tourist spot is open during specific session time.
        
        Args:
            session_type: Morning, afternoon, or night session
            day_of_week: Day of the week to check (default: monday)
            
        Returns:
            True if open during session, False otherwise
        """
        # Session time ranges
        session_times = {
            SessionType.MORNING: (time(7, 0), time(11, 59)),
            SessionType.AFTERNOON: (time(12, 0), time(17, 59)),
            SessionType.NIGHT: (time(18, 0), time(23, 59))
        }
        
        session_start, session_end = session_times[session_type]
        
        # Get operating hours for the day
        day_hours = getattr(self, day_of_week.lower(), None)
        
        # If no operating hours specified, assume always open
        if not day_hours:
            return True
        
        day_hours_clean = day_hours.strip().lower()
        
        # Handle special cases
        if day_hours_clean == 'closed':
            return False
        elif day_hours_clean in ['24 hours', 'always open']:
            return True
        elif day_hours_clean in ['by appointment', 'varies']:
            return True  # Assume available for planning purposes
        
        # Parse time range (HH:MM-HH:MM)
        time_pattern = re.compile(r'^(\d{2}):(\d{2})-(\d{2}):(\d{2})$')
        match = time_pattern.match(day_hours.strip())
        
        if not match:
            return True  # If format unclear, assume available
        
        open_hour, open_min, close_hour, close_min = map(int, match.groups())
        open_time = time(open_hour, open_min)
        close_time = time(close_hour, close_min)
        
        # Check if session overlaps with operating hours
        return not (session_end < open_time or session_start > close_time)

    def get_available_sessions(self, day_of_week: str = 'monday') -> List[SessionType]:
        """Get list of sessions when tourist spot is available.
        
        Args:
            day_of_week: Day of the week to check
            
        Returns:
            List of available session types
        """
        available_sessions = []
        
        for session_type in SessionType:
            if self.is_open_during_session(session_type, day_of_week):
                available_sessions.append(session_type)
        
        return available_sessions


@dataclass
class TouristSpot:
    """Complete tourist spot record with MBTI matching capability.
    
    Attributes:
        id: Unique tourist spot identifier
        name: Tourist spot name
        address: Full address
        district: District name (for matching logic)
        area: Area name (fallback for district matching)
        location_category: Category of location (e.g., "Museum", "Park")
        description: Description of the tourist spot
        operating_hours: Operating hours for different days
        operating_days: List of operating days
        mbti_match: Boolean indicating if spot matches MBTI personality
        mbti_personality_types: List of MBTI types this spot matches
        keywords: Keywords for search and matching
        rating: Average rating (1-5 scale)
        visitor_count: Estimated visitor count
        accessibility: Accessibility information
        entrance_fee: Entrance fee information
        contact_info: Contact information
        website: Website URL
        image_urls: List of image URLs
        metadata: Additional metadata
    """
    id: str
    name: str
    address: str
    district: str
    area: str
    location_category: str
    description: str
    operating_hours: TouristSpotOperatingHours
    operating_days: List[str]
    mbti_match: bool = False
    mbti_personality_types: List[str] = None
    keywords: List[str] = None
    rating: Optional[float] = None
    visitor_count: Optional[int] = None
    accessibility: Optional[str] = None
    entrance_fee: Optional[str] = None
    contact_info: Optional[str] = None
    website: Optional[str] = None
    image_urls: List[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.mbti_personality_types is None:
            self.mbti_personality_types = []
        if self.keywords is None:
            self.keywords = []
        if self.image_urls is None:
            self.image_urls = []
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TouristSpot':
        """Create TouristSpot from dictionary data.
        
        Args:
            data: Dictionary containing tourist spot data
            
        Returns:
            TouristSpot instance
        """
        operating_hours_data = data.get('operating_hours', {})
        if isinstance(operating_hours_data, dict):
            operating_hours = TouristSpotOperatingHours.from_dict(operating_hours_data)
        else:
            operating_hours = TouristSpotOperatingHours()
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            address=data.get('address', ''),
            district=data.get('district', ''),
            area=data.get('area', ''),
            location_category=data.get('location_category', ''),
            description=data.get('description', ''),
            operating_hours=operating_hours,
            operating_days=data.get('operating_days', []),
            mbti_match=data.get('mbti_match', False),
            mbti_personality_types=data.get('mbti_personality_types', []),
            keywords=data.get('keywords', []),
            rating=data.get('rating'),
            visitor_count=data.get('visitor_count'),
            accessibility=data.get('accessibility'),
            entrance_fee=data.get('entrance_fee'),
            contact_info=data.get('contact_info'),
            website=data.get('website'),
            image_urls=data.get('image_urls', []),
            metadata=data.get('metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of tourist spot
        """
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'district': self.district,
            'area': self.area,
            'location_category': self.location_category,
            'description': self.description,
            'operating_hours': self.operating_hours.to_dict(),
            'operating_days': self.operating_days,
            'mbti_match': self.mbti_match,
            'mbti_personality_types': self.mbti_personality_types,
            'keywords': self.keywords,
            'rating': self.rating,
            'visitor_count': self.visitor_count,
            'accessibility': self.accessibility,
            'entrance_fee': self.entrance_fee,
            'contact_info': self.contact_info,
            'website': self.website,
            'image_urls': self.image_urls,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Convert tourist spot to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate(self) -> List[str]:
        """Validate tourist spot data structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_string_fields = [
            ('id', self.id),
            ('name', self.name),
            ('address', self.address),
            ('district', self.district),
            ('area', self.area),
            ('location_category', self.location_category),
            ('description', self.description)
        ]
        
        for field_name, value in required_string_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate ID format
        if isinstance(self.id, str) and self.id:
            if not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
                errors.append(
                    "id must contain only alphanumeric characters, "
                    "underscores, and hyphens"
                )
        
        # Validate operating_days list
        if not isinstance(self.operating_days, list):
            errors.append("operating_days must be a list")
        else:
            valid_days = {
                'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday', 'daily', 'weekdays', 'weekends'
            }
            for i, day in enumerate(self.operating_days):
                if not isinstance(day, str):
                    errors.append(f"operating_days[{i}] must be a string")
                elif day.lower() not in valid_days:
                    errors.append(
                        f"operating_days[{i}] invalid day: '{day}'. "
                        f"Valid values: {', '.join(sorted(valid_days))}"
                    )
        
        # Validate MBTI personality types
        if not isinstance(self.mbti_personality_types, list):
            errors.append("mbti_personality_types must be a list")
        else:
            valid_mbti_types = {
                'INTJ', 'INTP', 'ENTJ', 'ENTP',
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                'ISTP', 'ISFP', 'ESTP', 'ESFP'
            }
            for i, mbti_type in enumerate(self.mbti_personality_types):
                if not isinstance(mbti_type, str):
                    errors.append(f"mbti_personality_types[{i}] must be a string")
                elif mbti_type.upper() not in valid_mbti_types:
                    errors.append(
                        f"mbti_personality_types[{i}] invalid MBTI type: '{mbti_type}'"
                    )
        
        # Validate keywords list
        if not isinstance(self.keywords, list):
            errors.append("keywords must be a list")
        else:
            for i, keyword in enumerate(self.keywords):
                if not isinstance(keyword, str):
                    errors.append(f"keywords[{i}] must be a string")
                elif len(keyword.strip()) == 0:
                    errors.append(f"keywords[{i}] cannot be empty")
        
        # Validate rating
        if self.rating is not None:
            if not isinstance(self.rating, (int, float)):
                errors.append("rating must be a number")
            elif self.rating < 1.0 or self.rating > 5.0:
                errors.append("rating must be between 1.0 and 5.0")
        
        # Validate visitor_count
        if self.visitor_count is not None:
            if not isinstance(self.visitor_count, int):
                errors.append("visitor_count must be an integer")
            elif self.visitor_count < 0:
                errors.append("visitor_count cannot be negative")
        
        # Validate image_urls list
        if not isinstance(self.image_urls, list):
            errors.append("image_urls must be a list")
        else:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE
            )
            for i, url in enumerate(self.image_urls):
                if not isinstance(url, str):
                    errors.append(f"image_urls[{i}] must be a string")
                elif url and not url_pattern.match(url):
                    errors.append(f"image_urls[{i}] invalid URL format: '{url}'")
        
        # Validate operating hours
        if not isinstance(self.operating_hours, TouristSpotOperatingHours):
            errors.append("operating_hours must be a TouristSpotOperatingHours object")
        else:
            hours_errors = self.operating_hours.validate()
            errors.extend([f"operating_hours.{error}" for error in hours_errors])
        
        # Validate metadata
        if not isinstance(self.metadata, dict):
            errors.append("metadata must be a dictionary")
        
        return errors

    def is_valid(self) -> bool:
        """Check if tourist spot data is valid.
        
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate()) == 0

    def matches_mbti_personality(self, mbti_personality: str) -> bool:
        """Check if tourist spot matches specific MBTI personality.
        
        Args:
            mbti_personality: 4-character MBTI code (e.g., "INFJ")
            
        Returns:
            True if spot matches the personality type
        """
        if not mbti_personality or not isinstance(mbti_personality, str):
            return False
        
        mbti_upper = mbti_personality.upper().strip()
        return mbti_upper in [mbti.upper() for mbti in self.mbti_personality_types]

    def matches_district(self, target_district: str) -> bool:
        """Check if tourist spot is in the target district.
        
        Args:
            target_district: District name to match
            
        Returns:
            True if district matches
        """
        if not target_district or not isinstance(target_district, str):
            return False
        
        return self.district.lower().strip() == target_district.lower().strip()

    def matches_area(self, target_area: str) -> bool:
        """Check if tourist spot is in the target area.
        
        Args:
            target_area: Area name to match
            
        Returns:
            True if area matches
        """
        if not target_area or not isinstance(target_area, str):
            return False
        
        return self.area.lower().strip() == target_area.lower().strip()

    def is_available_for_session(self, session_type: SessionType, day_of_week: str = 'monday') -> bool:
        """Check if tourist spot is available for specific session.
        
        Args:
            session_type: Morning, afternoon, or night session
            day_of_week: Day of the week to check
            
        Returns:
            True if available for the session
        """
        # Check operating days
        day_lower = day_of_week.lower()
        operating_days_lower = [day.lower() for day in self.operating_days]
        
        if operating_days_lower:
            day_available = (
                day_lower in operating_days_lower or
                'daily' in operating_days_lower or
                ('weekdays' in operating_days_lower and day_lower in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']) or
                ('weekends' in operating_days_lower and day_lower in ['saturday', 'sunday'])
            )
            
            if not day_available:
                return False
        
        # Check operating hours for the session
        return self.operating_hours.is_open_during_session(session_type, day_of_week)

    def get_district_area_priority_score(self, target_district: str, target_area: str) -> int:
        """Get priority score for district/area matching.
        
        Args:
            target_district: Target district for matching
            target_area: Target area for matching
            
        Returns:
            Priority score (higher is better):
            - 3: Same district
            - 2: Same area
            - 1: Different district and area
        """
        if self.matches_district(target_district):
            return 3
        elif self.matches_area(target_area):
            return 2
        else:
            return 1

    def set_mbti_match_status(self, mbti_personality: str) -> None:
        """Set MBTI match status based on personality type.
        
        Args:
            mbti_personality: 4-character MBTI code to check against
        """
        self.mbti_match = self.matches_mbti_personality(mbti_personality)

    def add_mbti_personality_type(self, mbti_type: str) -> None:
        """Add MBTI personality type to the list.
        
        Args:
            mbti_type: 4-character MBTI code to add
        """
        if mbti_type and isinstance(mbti_type, str):
            mbti_upper = mbti_type.upper().strip()
            if mbti_upper not in [mbti.upper() for mbti in self.mbti_personality_types]:
                self.mbti_personality_types.append(mbti_upper)

    def remove_mbti_personality_type(self, mbti_type: str) -> None:
        """Remove MBTI personality type from the list.
        
        Args:
            mbti_type: 4-character MBTI code to remove
        """
        if mbti_type and isinstance(mbti_type, str):
            mbti_upper = mbti_type.upper().strip()
            self.mbti_personality_types = [
                mbti for mbti in self.mbti_personality_types
                if mbti.upper() != mbti_upper
            ]