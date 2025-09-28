"""Models package for MBTI Travel Assistant MCP.

This package contains all data models for the MBTI Travel Assistant,
including restaurant data models, request/response models, and validation.
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
    'AuthenticationError'
]