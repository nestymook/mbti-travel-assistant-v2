"""MBTI Travel Assistant request and response models.

This module contains dataclass models for HTTP request/response handling
specifically for the MBTI Travel Assistant, including MBTI personality validation,
complete itinerary responses, and comprehensive error handling.
Follows PEP8 style guidelines and supports BedrockAgentCore runtime patterns.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

from .itinerary_models import MainItinerary, CandidateLists
from .tourist_spot_models import TouristSpot
from .restaurant_models import Restaurant


@dataclass
class ItineraryRequest:
    """HTTP request payload for MBTI-based 3-day itinerary generation.
    
    Attributes:
        mbti_personality: 4-character MBTI personality code (required)
        user_context: User context from JWT token (optional)
        preferences: Additional user preferences (optional)
        start_date: Preferred start date for the itinerary (optional)
        special_requirements: Special requirements or constraints (optional)
    """
    mbti_personality: str
    user_context: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    special_requirements: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.preferences is None:
            self.preferences = {}
        if self.special_requirements is None:
            self.special_requirements = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItineraryRequest':
        """Create ItineraryRequest from dictionary data.
        
        Args:
            data: Dictionary containing request payload
            
        Returns:
            ItineraryRequest instance
        """
        return cls(
            mbti_personality=data.get('MBTI_personality', data.get('mbti_personality', '')),
            user_context=data.get('user_context'),
            preferences=data.get('preferences', {}),
            start_date=data.get('start_date'),
            special_requirements=data.get('special_requirements', [])
        )

    def validate(self) -> List[str]:
        """Validate MBTI itinerary request and return list of validation errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate MBTI personality (required)
        if not self.mbti_personality:
            errors.append("MBTI_personality is required")
        elif not isinstance(self.mbti_personality, str):
            errors.append("MBTI_personality must be a string")
        elif len(self.mbti_personality.strip()) != 4:
            errors.append("MBTI_personality must be a 4-character code")
        else:
            # Validate MBTI format
            valid_mbti_types = {
                'INTJ', 'INTP', 'ENTJ', 'ENTP',
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                'ISTP', 'ISFP', 'ESTP', 'ESFP'
            }
            
            mbti_upper = self.mbti_personality.upper().strip()
            if mbti_upper not in valid_mbti_types:
                errors.append(
                    f"Invalid MBTI personality type: '{self.mbti_personality}'. "
                    f"Valid types: {', '.join(sorted(valid_mbti_types))}"
                )
        
        # Validate start_date format if provided
        if self.start_date:
            if not isinstance(self.start_date, str):
                errors.append("start_date must be a string")
            else:
                try:
                    datetime.fromisoformat(self.start_date.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("start_date must be in ISO format (YYYY-MM-DD)")
        
        # Validate preferences structure
        if not isinstance(self.preferences, dict):
            errors.append("preferences must be a dictionary")
        
        # Validate special_requirements
        if not isinstance(self.special_requirements, list):
            errors.append("special_requirements must be a list")
        else:
            for i, requirement in enumerate(self.special_requirements):
                if not isinstance(requirement, str):
                    errors.append(f"special_requirements[{i}] must be a string")
                elif len(requirement.strip()) == 0:
                    errors.append(f"special_requirements[{i}] cannot be empty")
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of request
        """
        return {
            'MBTI_personality': self.mbti_personality,
            'user_context': self.user_context,
            'preferences': self.preferences,
            'start_date': self.start_date,
            'special_requirements': self.special_requirements
        }

    def get_normalized_mbti_personality(self) -> str:
        """Get normalized MBTI personality type.
        
        Returns:
            Uppercase, trimmed MBTI personality type
        """
        if self.mbti_personality:
            return self.mbti_personality.upper().strip()
        return ''


@dataclass
class ItineraryResponseMetadata:
    """Metadata about the MBTI itinerary generation response.
    
    Attributes:
        mbti_personality: MBTI personality type used for generation
        generation_timestamp: Response generation timestamp
        total_spots_found: Total number of tourist spots found
        total_restaurants_found: Total number of restaurants found
        processing_time_ms: Processing time in milliseconds
        knowledge_base_queries: Number of knowledge base queries made
        mcp_calls: List of MCP calls made during processing
        cache_hit: Whether response was served from cache
        validation_status: Status of itinerary validation
        generation_strategy: Strategy used for itinerary generation
    """
    mbti_personality: str
    generation_timestamp: str
    total_spots_found: int
    total_restaurants_found: int
    processing_time_ms: int
    knowledge_base_queries: int = 0
    mcp_calls: List[str] = None
    cache_hit: bool = False
    validation_status: str = "valid"
    generation_strategy: str = "standard"

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.mcp_calls is None:
            self.mcp_calls = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItineraryResponseMetadata':
        """Create ItineraryResponseMetadata from dictionary data.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            ItineraryResponseMetadata instance
        """
        return cls(
            mbti_personality=data.get('MBTI_personality', data.get('mbti_personality', '')),
            generation_timestamp=data.get('generation_timestamp', ''),
            total_spots_found=data.get('total_spots_found', 0),
            total_restaurants_found=data.get('total_restaurants_found', 0),
            processing_time_ms=data.get('processing_time_ms', 0),
            knowledge_base_queries=data.get('knowledge_base_queries', 0),
            mcp_calls=data.get('mcp_calls', []),
            cache_hit=data.get('cache_hit', False),
            validation_status=data.get('validation_status', 'valid'),
            generation_strategy=data.get('generation_strategy', 'standard')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            'MBTI_personality': self.mbti_personality,
            'generation_timestamp': self.generation_timestamp,
            'total_spots_found': self.total_spots_found,
            'total_restaurants_found': self.total_restaurants_found,
            'processing_time_ms': self.processing_time_ms,
            'knowledge_base_queries': self.knowledge_base_queries,
            'mcp_calls': self.mcp_calls,
            'cache_hit': self.cache_hit,
            'validation_status': self.validation_status,
            'generation_strategy': self.generation_strategy
        }


@dataclass
class ItineraryErrorInfo:
    """Error information structure for MBTI itinerary API responses.
    
    Attributes:
        error_type: Type/category of error
        message: Human-readable error message
        suggested_actions: List of suggested actions to resolve the error
        error_code: Specific error code for programmatic handling
        details: Additional error details
    """
    error_type: str
    message: str
    suggested_actions: List[str]
    error_code: str
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.details is None:
            self.details = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItineraryErrorInfo':
        """Create ItineraryErrorInfo from dictionary data.
        
        Args:
            data: Dictionary containing error information
            
        Returns:
            ItineraryErrorInfo instance
        """
        return cls(
            error_type=data.get('error_type', ''),
            message=data.get('message', ''),
            suggested_actions=data.get('suggested_actions', []),
            error_code=data.get('error_code', ''),
            details=data.get('details', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of error info
        """
        return {
            'error_type': self.error_type,
            'message': self.message,
            'suggested_actions': self.suggested_actions,
            'error_code': self.error_code,
            'details': self.details
        }

    @classmethod
    def validation_error(cls, message: str, details: Dict[str, Any] = None) -> 'ItineraryErrorInfo':
        """Create validation error for MBTI itinerary requests.
        
        Args:
            message: Validation error message
            details: Additional error details
            
        Returns:
            ItineraryErrorInfo instance for validation error
        """
        return cls(
            error_type='validation_error',
            message=message,
            suggested_actions=[
                'Check MBTI_personality parameter format (4-character code)',
                'Ensure required fields are provided',
                'Validate parameter formats and values'
            ],
            error_code='MBTI_VALIDATION_FAILED',
            details=details or {}
        )

    @classmethod
    def knowledge_base_error(cls, message: str, details: Dict[str, Any] = None) -> 'ItineraryErrorInfo':
        """Create knowledge base error.
        
        Args:
            message: Knowledge base error message
            details: Additional error details
            
        Returns:
            ItineraryErrorInfo instance for knowledge base error
        """
        return cls(
            error_type='knowledge_base_error',
            message=message,
            suggested_actions=[
                'Try again in a few moments',
                'Check knowledge base service status',
                'Contact support if problem persists'
            ],
            error_code='KNOWLEDGE_BASE_UNAVAILABLE',
            details=details or {}
        )

    @classmethod
    def itinerary_generation_error(cls, message: str, details: Dict[str, Any] = None) -> 'ItineraryErrorInfo':
        """Create itinerary generation error.
        
        Args:
            message: Itinerary generation error message
            details: Additional error details
            
        Returns:
            ItineraryErrorInfo instance for generation error
        """
        return cls(
            error_type='itinerary_generation_error',
            message=message,
            suggested_actions=[
                'Try with a different MBTI personality type',
                'Check if sufficient tourist spots are available',
                'Contact support if problem persists'
            ],
            error_code='ITINERARY_GENERATION_FAILED',
            details=details or {}
        )

    @classmethod
    def mcp_service_error(cls, service_name: str, message: str, details: Dict[str, Any] = None) -> 'ItineraryErrorInfo':
        """Create MCP service error for restaurant services.
        
        Args:
            service_name: Name of the MCP service that failed
            message: Error message
            details: Additional error details
            
        Returns:
            ItineraryErrorInfo instance for MCP service error
        """
        return cls(
            error_type='mcp_service_error',
            message=f"{service_name}: {message}",
            suggested_actions=[
                'Try again in a few moments',
                'Check restaurant service status',
                'Contact support if problem persists'
            ],
            error_code='MCP_SERVICE_UNAVAILABLE',
            details=details or {'service': service_name}
        )


@dataclass
class ItineraryResponse:
    """Complete response structure for MBTI-based 3-day itinerary generation.
    
    This matches the JSON response structure required by Requirements 6.1, 6.2, and 6.7.
    
    Attributes:
        main_itinerary: Complete 3-day itinerary with sessions and meals
        candidate_tourist_spots: Candidate tourist spots organized by day
        candidate_restaurants: Candidate restaurants organized by day and meal
        metadata: Response metadata with generation info and timing
        error: Error information if request failed (optional)
    """
    main_itinerary: Optional[MainItinerary] = None
    candidate_tourist_spots: Optional[Dict[str, List[TouristSpot]]] = None
    candidate_restaurants: Optional[Dict[str, Dict[str, List[Restaurant]]]] = None
    metadata: Optional[ItineraryResponseMetadata] = None
    error: Optional[ItineraryErrorInfo] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.candidate_tourist_spots is None:
            self.candidate_tourist_spots = {}
        if self.candidate_restaurants is None:
            self.candidate_restaurants = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItineraryResponse':
        """Create ItineraryResponse from dictionary data.
        
        Args:
            data: Dictionary containing response data
            
        Returns:
            ItineraryResponse instance
        """
        main_itinerary = None
        if data.get('main_itinerary'):
            main_itinerary = MainItinerary.from_dict(data['main_itinerary'])
        
        # Parse candidate tourist spots
        candidate_tourist_spots = {}
        if data.get('candidate_tourist_spots'):
            for day, spots_list in data['candidate_tourist_spots'].items():
                candidate_tourist_spots[day] = [
                    TouristSpot.from_dict(spot_data) for spot_data in spots_list
                ]
        
        # Parse candidate restaurants
        candidate_restaurants = {}
        if data.get('candidate_restaurants'):
            for day, meals_dict in data['candidate_restaurants'].items():
                candidate_restaurants[day] = {}
                for meal, restaurants_list in meals_dict.items():
                    candidate_restaurants[day][meal] = [
                        Restaurant.from_dict(restaurant_data) for restaurant_data in restaurants_list
                    ]
        
        metadata = None
        if data.get('metadata'):
            metadata = ItineraryResponseMetadata.from_dict(data['metadata'])
        
        error = None
        if data.get('error'):
            error = ItineraryErrorInfo.from_dict(data['error'])
        
        return cls(
            main_itinerary=main_itinerary,
            candidate_tourist_spots=candidate_tourist_spots,
            candidate_restaurants=candidate_restaurants,
            metadata=metadata,
            error=error
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation matching frontend requirements
        """
        result = {}
        
        if self.main_itinerary:
            result['main_itinerary'] = self.main_itinerary.to_dict()
        
        if self.candidate_tourist_spots:
            result['candidate_tourist_spots'] = {}
            for day, spots_list in self.candidate_tourist_spots.items():
                result['candidate_tourist_spots'][day] = [
                    spot.to_dict() for spot in spots_list
                ]
        
        if self.candidate_restaurants:
            result['candidate_restaurants'] = {}
            for day, meals_dict in self.candidate_restaurants.items():
                result['candidate_restaurants'][day] = {}
                for meal, restaurants_list in meals_dict.items():
                    result['candidate_restaurants'][day][meal] = [
                        restaurant.to_dict() for restaurant in restaurants_list
                    ]
        
        if self.metadata:
            result['metadata'] = self.metadata.to_dict()
        
        if self.error:
            result['error'] = self.error.to_dict()
        
        return result

    def to_json(self) -> str:
        """Convert to JSON string for HTTP response.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate_response_structure(self) -> List[str]:
        """Validate response structure against MBTI itinerary requirements.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check that we have either success data or error
        if not self.error and not self.main_itinerary:
            errors.append("Response must contain either main_itinerary or error")
        
        # If we have a main itinerary, validate structure
        if self.main_itinerary:
            if not isinstance(self.main_itinerary, MainItinerary):
                errors.append("main_itinerary must be a MainItinerary object")
            else:
                itinerary_errors = self.main_itinerary.validate()
                errors.extend([f"main_itinerary.{error}" for error in itinerary_errors])
                
                # Validate uniqueness constraints
                uniqueness_errors = self.main_itinerary.validate_uniqueness_constraints()
                errors.extend([f"main_itinerary.{error}" for error in uniqueness_errors])
        
        # Validate candidate tourist spots structure
        if self.candidate_tourist_spots:
            valid_days = ['day_1', 'day_2', 'day_3']
            for day, spots_list in self.candidate_tourist_spots.items():
                if day not in valid_days:
                    errors.append(f"candidate_tourist_spots invalid day key: '{day}'")
                
                if not isinstance(spots_list, list):
                    errors.append(f"candidate_tourist_spots['{day}'] must be a list")
                else:
                    for i, spot in enumerate(spots_list):
                        if not isinstance(spot, TouristSpot):
                            errors.append(f"candidate_tourist_spots['{day}'][{i}] must be a TouristSpot object")
        
        # Validate candidate restaurants structure
        if self.candidate_restaurants:
            valid_days = ['day_1', 'day_2', 'day_3']
            valid_meals = ['breakfast', 'lunch', 'dinner']
            
            for day, meals_dict in self.candidate_restaurants.items():
                if day not in valid_days:
                    errors.append(f"candidate_restaurants invalid day key: '{day}'")
                
                if not isinstance(meals_dict, dict):
                    errors.append(f"candidate_restaurants['{day}'] must be a dictionary")
                else:
                    for meal, restaurants_list in meals_dict.items():
                        if meal not in valid_meals:
                            errors.append(f"candidate_restaurants['{day}'] invalid meal key: '{meal}'")
                        
                        if not isinstance(restaurants_list, list):
                            errors.append(f"candidate_restaurants['{day}']['{meal}'] must be a list")
                        else:
                            for i, restaurant in enumerate(restaurants_list):
                                if not isinstance(restaurant, Restaurant):
                                    errors.append(
                                        f"candidate_restaurants['{day}']['{meal}'][{i}] "
                                        "must be a Restaurant object"
                                    )
        
        # Validate metadata if present
        if self.metadata and not isinstance(self.metadata, ItineraryResponseMetadata):
            errors.append("metadata must be an ItineraryResponseMetadata object")
        
        # Validate error if present
        if self.error and not isinstance(self.error, ItineraryErrorInfo):
            errors.append("error must be an ItineraryErrorInfo object")
        
        return errors

    @classmethod
    def success_response(
        cls,
        main_itinerary: MainItinerary,
        candidate_tourist_spots: Dict[str, List[TouristSpot]],
        candidate_restaurants: Dict[str, Dict[str, List[Restaurant]]],
        metadata: ItineraryResponseMetadata
    ) -> 'ItineraryResponse':
        """Create successful MBTI itinerary response.
        
        Args:
            main_itinerary: Complete 3-day itinerary
            candidate_tourist_spots: Candidate tourist spots by day
            candidate_restaurants: Candidate restaurants by day and meal
            metadata: Response metadata
            
        Returns:
            ItineraryResponse with success data
        """
        return cls(
            main_itinerary=main_itinerary,
            candidate_tourist_spots=candidate_tourist_spots,
            candidate_restaurants=candidate_restaurants,
            metadata=metadata,
            error=None
        )

    @classmethod
    def error_response(cls, error: ItineraryErrorInfo) -> 'ItineraryResponse':
        """Create error response for MBTI itinerary generation.
        
        Args:
            error: Error information
            
        Returns:
            ItineraryResponse with error data
        """
        return cls(
            main_itinerary=None,
            candidate_tourist_spots={},
            candidate_restaurants={},
            metadata=None,
            error=error
        )

    def is_successful(self) -> bool:
        """Check if response represents a successful itinerary generation.
        
        Returns:
            True if response contains main_itinerary and no error
        """
        return self.main_itinerary is not None and self.error is None

    def get_total_assignments_count(self) -> Dict[str, int]:
        """Get total count of assignments in the response.
        
        Returns:
            Dictionary with counts for tourist_spots and restaurants
        """
        tourist_spots_count = 0
        restaurants_count = 0
        
        if self.main_itinerary:
            tourist_spots_count = len(self.main_itinerary.get_all_tourist_spots())
            restaurants_count = len(self.main_itinerary.get_all_restaurants())
        
        return {
            'tourist_spots': tourist_spots_count,
            'restaurants': restaurants_count
        }


@dataclass
class AgentCoreItineraryRequest:
    """Request format for BedrockAgentCore runtime entrypoint for MBTI itineraries.
    
    This represents the payload structure that the @app.entrypoint
    decorator receives from HTTP requests for MBTI-based itinerary generation.
    
    Attributes:
        mbti_personality: 4-character MBTI personality code (required)
        user_context: User context from JWT authentication
        preferences: Additional user preferences
        start_date: Preferred start date for the itinerary
        special_requirements: Special requirements or constraints
    """
    mbti_personality: str
    user_context: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    special_requirements: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.preferences is None:
            self.preferences = {}
        if self.special_requirements is None:
            self.special_requirements = []

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'AgentCoreItineraryRequest':
        """Create AgentCoreItineraryRequest from entrypoint payload.
        
        Args:
            payload: Dictionary payload from AgentCore entrypoint
            
        Returns:
            AgentCoreItineraryRequest instance
        """
        return cls(
            mbti_personality=payload.get('MBTI_personality', payload.get('mbti_personality', '')),
            user_context=payload.get('user_context'),
            preferences=payload.get('preferences', {}),
            start_date=payload.get('start_date'),
            special_requirements=payload.get('special_requirements', [])
        )

    def to_itinerary_request(self) -> ItineraryRequest:
        """Convert to ItineraryRequest for processing.
        
        Returns:
            ItineraryRequest instance
        """
        return ItineraryRequest(
            mbti_personality=self.mbti_personality,
            user_context=self.user_context,
            preferences=self.preferences,
            start_date=self.start_date,
            special_requirements=self.special_requirements
        )

    def validate(self) -> List[str]:
        """Validate AgentCore itinerary request payload.
        
        Returns:
            List of validation errors
        """
        request = self.to_itinerary_request()
        return request.validate()