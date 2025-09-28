"""Request and response models for MBTI Travel Assistant MCP.

This module contains dataclass models for HTTP request/response handling,
including payload validation, response formatting, and error handling.
Follows PEP8 style guidelines and supports BedrockAgentCore runtime patterns.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

from .restaurant_models import Restaurant, Sentiment


@dataclass
class RecommendationRequest:
    """HTTP request payload for restaurant recommendations.
    
    Attributes:
        district: District name for restaurant search (optional)
        meal_time: Meal time filter (breakfast, lunch, dinner) (optional)
        natural_language_query: Natural language query (optional)
        user_context: User context from JWT token (optional)
    """
    district: Optional[str] = None
    meal_time: Optional[str] = None
    natural_language_query: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecommendationRequest':
        """Create RecommendationRequest from dictionary data.
        
        Args:
            data: Dictionary containing request payload
            
        Returns:
            RecommendationRequest instance
        """
        return cls(
            district=data.get('district'),
            meal_time=data.get('meal_time'),
            natural_language_query=data.get('natural_language_query'),
            user_context=data.get('user_context')
        )

    def validate(self) -> List[str]:
        """Validate request and return list of validation errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # At least one search parameter must be provided
        if not self.district and not self.natural_language_query:
            errors.append(
                "Either district or natural_language_query must be provided"
            )
        
        # Validate meal_time if provided
        if self.meal_time:
            valid_meal_times = ['breakfast', 'lunch', 'dinner']
            if self.meal_time.lower() not in valid_meal_times:
                errors.append(
                    f"meal_time must be one of: {', '.join(valid_meal_times)}"
                )
        
        # Validate district format if provided
        if self.district:
            if len(self.district.strip()) == 0:
                errors.append("district cannot be empty")
            elif len(self.district) > 100:
                errors.append("district name too long (max 100 characters)")
        
        # Validate natural language query if provided
        if self.natural_language_query:
            if len(self.natural_language_query.strip()) == 0:
                errors.append("natural_language_query cannot be empty")
            elif len(self.natural_language_query) > 500:
                errors.append(
                    "natural_language_query too long (max 500 characters)"
                )
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of request
        """
        return {
            'district': self.district,
            'meal_time': self.meal_time,
            'natural_language_query': self.natural_language_query,
            'user_context': self.user_context
        }


@dataclass
class ResponseMetadata:
    """Metadata about the recommendation response.
    
    Attributes:
        search_criteria: Dictionary of search parameters used
        total_found: Total number of restaurants found
        timestamp: Response generation timestamp
        processing_time_ms: Processing time in milliseconds
        cache_hit: Whether response was served from cache
        mcp_calls: List of MCP calls made during processing
    """
    search_criteria: Dict[str, str]
    total_found: int
    timestamp: datetime
    processing_time_ms: int
    cache_hit: bool
    mcp_calls: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseMetadata':
        """Create ResponseMetadata from dictionary data.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            ResponseMetadata instance
        """
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_str or datetime.utcnow()
        
        return cls(
            search_criteria=data.get('search_criteria', {}),
            total_found=data.get('total_found', 0),
            timestamp=timestamp,
            processing_time_ms=data.get('processing_time_ms', 0),
            cache_hit=data.get('cache_hit', False),
            mcp_calls=data.get('mcp_calls', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            'search_criteria': self.search_criteria,
            'total_found': self.total_found,
            'timestamp': self.timestamp.isoformat(),
            'processing_time_ms': self.processing_time_ms,
            'cache_hit': self.cache_hit,
            'mcp_calls': self.mcp_calls
        }


@dataclass
class ErrorInfo:
    """Error information structure for API responses.
    
    Attributes:
        error_type: Type/category of error
        message: Human-readable error message
        suggested_actions: List of suggested actions to resolve the error
        error_code: Specific error code for programmatic handling
    """
    error_type: str
    message: str
    suggested_actions: List[str]
    error_code: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorInfo':
        """Create ErrorInfo from dictionary data.
        
        Args:
            data: Dictionary containing error information
            
        Returns:
            ErrorInfo instance
        """
        return cls(
            error_type=data.get('error_type', ''),
            message=data.get('message', ''),
            suggested_actions=data.get('suggested_actions', []),
            error_code=data.get('error_code', '')
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
            'error_code': self.error_code
        }

    @classmethod
    def validation_error(cls, message: str) -> 'ErrorInfo':
        """Create validation error.
        
        Args:
            message: Validation error message
            
        Returns:
            ErrorInfo instance for validation error
        """
        return cls(
            error_type='validation_error',
            message=message,
            suggested_actions=[
                'Check request parameters',
                'Ensure required fields are provided',
                'Validate parameter formats'
            ],
            error_code='VALIDATION_FAILED'
        )

    @classmethod
    def authentication_error(cls, message: str) -> 'ErrorInfo':
        """Create authentication error.
        
        Args:
            message: Authentication error message
            
        Returns:
            ErrorInfo instance for authentication error
        """
        return cls(
            error_type='authentication_error',
            message=message,
            suggested_actions=[
                'Check JWT token validity',
                'Ensure proper Authorization header',
                'Verify token has not expired'
            ],
            error_code='AUTH_FAILED'
        )

    @classmethod
    def mcp_service_error(cls, service_name: str, message: str) -> 'ErrorInfo':
        """Create MCP service error.
        
        Args:
            service_name: Name of the MCP service that failed
            message: Error message
            
        Returns:
            ErrorInfo instance for MCP service error
        """
        return cls(
            error_type='mcp_service_error',
            message=f"{service_name}: {message}",
            suggested_actions=[
                'Try again in a few moments',
                'Check service status',
                'Contact support if problem persists'
            ],
            error_code='MCP_SERVICE_UNAVAILABLE'
        )


@dataclass
class RecommendationResponse:
    """Final response structure for frontend applications.
    
    This matches the JSON response structure required by Requirement 4.
    
    Attributes:
        recommendation: Single recommended restaurant (exactly 1)
        candidates: List of candidate restaurants (exactly 19 or fewer)
        metadata: Response metadata with search info and timing
        error: Error information if request failed (optional)
    """
    recommendation: Optional[Restaurant] = None
    candidates: List[Restaurant] = None
    metadata: Optional[ResponseMetadata] = None
    error: Optional[ErrorInfo] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.candidates is None:
            self.candidates = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecommendationResponse':
        """Create RecommendationResponse from dictionary data.
        
        Args:
            data: Dictionary containing response data
            
        Returns:
            RecommendationResponse instance
        """
        recommendation = None
        if data.get('recommendation'):
            recommendation = Restaurant.from_dict(data['recommendation'])
        
        candidates = []
        if data.get('candidates'):
            candidates = [
                Restaurant.from_dict(candidate_data)
                for candidate_data in data['candidates']
            ]
        
        metadata = None
        if data.get('metadata'):
            metadata = ResponseMetadata.from_dict(data['metadata'])
        
        error = None
        if data.get('error'):
            error = ErrorInfo.from_dict(data['error'])
        
        return cls(
            recommendation=recommendation,
            candidates=candidates,
            metadata=metadata,
            error=error
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation matching frontend requirements
        """
        result = {}
        
        if self.recommendation:
            result['recommendation'] = self.recommendation.to_dict()
        
        if self.candidates:
            result['candidates'] = [
                candidate.to_dict() for candidate in self.candidates
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
        """Validate response structure against requirements.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check that we have either success data or error
        if not self.error and not self.recommendation:
            errors.append("Response must contain either recommendation or error")
        
        # If we have a recommendation, validate structure
        if self.recommendation:
            if not isinstance(self.recommendation, Restaurant):
                errors.append("recommendation must be a Restaurant object")
        
        # Validate candidates list
        if self.candidates:
            if len(self.candidates) > 19:
                errors.append("candidates list cannot exceed 19 restaurants")
            
            for i, candidate in enumerate(self.candidates):
                if not isinstance(candidate, Restaurant):
                    errors.append(f"candidates[{i}] must be a Restaurant object")
        
        # Validate metadata if present
        if self.metadata and not isinstance(self.metadata, ResponseMetadata):
            errors.append("metadata must be a ResponseMetadata object")
        
        # Validate error if present
        if self.error and not isinstance(self.error, ErrorInfo):
            errors.append("error must be an ErrorInfo object")
        
        return errors

    @classmethod
    def success_response(
        cls,
        recommendation: Restaurant,
        candidates: List[Restaurant],
        metadata: ResponseMetadata
    ) -> 'RecommendationResponse':
        """Create successful recommendation response.
        
        Args:
            recommendation: Single recommended restaurant
            candidates: List of candidate restaurants (max 19)
            metadata: Response metadata
            
        Returns:
            RecommendationResponse with success data
        """
        # Ensure candidates list doesn't exceed 19 items
        if len(candidates) > 19:
            candidates = candidates[:19]
        
        return cls(
            recommendation=recommendation,
            candidates=candidates,
            metadata=metadata,
            error=None
        )

    @classmethod
    def error_response(cls, error: ErrorInfo) -> 'RecommendationResponse':
        """Create error response.
        
        Args:
            error: Error information
            
        Returns:
            RecommendationResponse with error data
        """
        return cls(
            recommendation=None,
            candidates=[],
            metadata=None,
            error=error
        )


@dataclass
class AgentCoreRequest:
    """Request format for BedrockAgentCore runtime entrypoint.
    
    This represents the payload structure that the @app.entrypoint
    decorator receives from HTTP requests.
    
    Attributes:
        district: District name for search
        meal_time: Meal time filter
        natural_language_query: Natural language query (optional)
        user_context: User context from JWT authentication
    """
    district: Optional[str] = None
    meal_time: Optional[str] = None
    natural_language_query: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'AgentCoreRequest':
        """Create AgentCoreRequest from entrypoint payload.
        
        Args:
            payload: Dictionary payload from AgentCore entrypoint
            
        Returns:
            AgentCoreRequest instance
        """
        return cls(
            district=payload.get('district'),
            meal_time=payload.get('meal_time'),
            natural_language_query=payload.get('natural_language_query'),
            user_context=payload.get('user_context')
        )

    def to_recommendation_request(self) -> RecommendationRequest:
        """Convert to RecommendationRequest for processing.
        
        Returns:
            RecommendationRequest instance
        """
        return RecommendationRequest(
            district=self.district,
            meal_time=self.meal_time,
            natural_language_query=self.natural_language_query,
            user_context=self.user_context
        )

    def validate(self) -> List[str]:
        """Validate AgentCore request payload.
        
        Returns:
            List of validation errors
        """
        request = self.to_recommendation_request()
        return request.validate()