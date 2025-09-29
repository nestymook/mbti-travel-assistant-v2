"""Models package for MBTI Travel Assistant MCP.

This package contains all data models for the MBTI Travel Assistant,
including tourist spot models, itinerary models, restaurant data models,
request/response models, and validation.
"""

from .restaurant_models import (
    OperatingHours,
    Sentiment,
    RestaurantMetadata,
    Restaurant,
    FileMetadata,
    RestaurantDataFile
)

from .request_models import (
    RecommendationRequest,
    ResponseMetadata,
    ErrorInfo,
    RecommendationResponse,
    AgentCoreRequest
)

from .auth_models import (
    CognitoConfig,
    JWTClaims,
    UserContext,
    AuthenticationError
)

from .tourist_spot_models import (
    SessionType,
    TouristSpotOperatingHours,
    TouristSpot
)

from .itinerary_models import (
    SessionAssignment,
    MealAssignment,
    DayItinerary,
    MainItinerary,
    CandidateLists
)

from .mbti_request_response_models import (
    ItineraryRequest,
    ItineraryResponseMetadata,
    ItineraryErrorInfo,
    ItineraryResponse,
    AgentCoreItineraryRequest
)

__all__ = [
    # Restaurant models
    'OperatingHours',
    'Sentiment',
    'RestaurantMetadata',
    'Restaurant',
    'FileMetadata',
    'RestaurantDataFile',
    
    # Request/Response models
    'RecommendationRequest',
    'ResponseMetadata',
    'ErrorInfo',
    'RecommendationResponse',
    'AgentCoreRequest',
    
    # Authentication models
    'CognitoConfig',
    'JWTClaims',
    'UserContext',
    'AuthenticationError',
    
    # Tourist spot models
    'SessionType',
    'TouristSpotOperatingHours',
    'TouristSpot',
    
    # Itinerary models
    'SessionAssignment',
    'MealAssignment',
    'DayItinerary',
    'MainItinerary',
    'CandidateLists',
    
    # MBTI Request/Response models
    'ItineraryRequest',
    'ItineraryResponseMetadata',
    'ItineraryErrorInfo',
    'ItineraryResponse',
    'AgentCoreItineraryRequest'
]