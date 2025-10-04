"""
Response models for AgentCore Gateway MCP Tools.

This module contains Pydantic models for structuring HTTP responses
from the AgentCore Gateway. These models ensure consistent response
formats and proper error handling structures.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status indicators."""
    SUCCESS = "success"
    ERROR = "error"


class ErrorType(str, Enum):
    """Types of errors that can occur."""
    VALIDATION_ERROR = "ValidationError"
    AUTHENTICATION_ERROR = "AuthenticationError"
    AUTHORIZATION_ERROR = "AuthorizationError"
    MCP_SERVER_ERROR = "MCPServerError"
    SERVICE_UNAVAILABLE = "ServiceUnavailable"
    RATE_LIMIT_ERROR = "RateLimitError"
    INTERNAL_ERROR = "InternalError"


class SentimentData(BaseModel):
    """Sentiment data model for responses."""
    
    likes: int = Field(..., description="Number of likes")
    dislikes: int = Field(..., description="Number of dislikes")
    neutral: int = Field(..., description="Number of neutral responses")
    total_responses: int = Field(..., description="Total number of responses")
    likes_percentage: float = Field(..., description="Percentage of likes")
    combined_positive_percentage: float = Field(..., description="Percentage of likes + neutral")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "likes": 85,
                "dislikes": 10,
                "neutral": 5,
                "total_responses": 100,
                "likes_percentage": 85.0,
                "combined_positive_percentage": 90.0
            }
        }


class OperatingHours(BaseModel):
    """Operating hours model for restaurants."""
    
    weekday_open: str = Field(..., description="Weekday opening time")
    weekday_close: str = Field(..., description="Weekday closing time")
    weekend_open: str = Field(..., description="Weekend opening time")
    weekend_close: str = Field(..., description="Weekend closing time")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "weekday_open": "09:00",
                "weekday_close": "22:00",
                "weekend_open": "10:00",
                "weekend_close": "23:00"
            }
        }


class RestaurantMetadata(BaseModel):
    """Metadata for restaurant records."""
    
    source: str = Field(..., description="Data source")
    last_updated: str = Field(..., description="Last update timestamp")
    data_quality_score: float = Field(..., description="Data quality score")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "source": "restaurant_api",
                "last_updated": "2025-01-03T10:30:00Z",
                "data_quality_score": 0.95
            }
        }


class RestaurantResponse(BaseModel):
    """Restaurant data model for responses."""
    
    id: str = Field(..., description="Unique restaurant identifier")
    name: str = Field(..., description="Restaurant name")
    address: str = Field(..., description="Restaurant address")
    meal_type: List[str] = Field(..., description="Supported meal types")
    sentiment: SentimentData = Field(..., description="Sentiment analysis data")
    location_category: str = Field(..., description="Location category")
    district: str = Field(..., description="Restaurant district")
    price_range: str = Field(..., description="Price range category")
    operating_hours: Optional[OperatingHours] = Field(None, description="Operating hours")
    metadata: Optional[RestaurantMetadata] = Field(None, description="Restaurant metadata")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "id": "rest_001",
                "name": "Great Restaurant",
                "address": "123 Main St, Central",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {
                    "likes": 85,
                    "dislikes": 10,
                    "neutral": 5,
                    "total_responses": 100,
                    "likes_percentage": 85.0,
                    "combined_positive_percentage": 90.0
                },
                "location_category": "Shopping Mall",
                "district": "Central district",
                "price_range": "$$"
            }
        }


class FileMetadata(BaseModel):
    """Metadata for restaurant data files."""
    
    file_name: str = Field(..., description="Source file name")
    total_restaurants: int = Field(..., description="Total restaurants in file")
    data_source: str = Field(..., description="Data source identifier")
    last_updated: str = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "file_name": "central_restaurants.json",
                "total_restaurants": 150,
                "data_source": "restaurant_api",
                "last_updated": "2025-01-03T10:30:00Z"
            }
        }


class SearchResultMetadata(BaseModel):
    """Metadata for search results."""
    
    total_results: int = Field(..., description="Total number of results found")
    search_criteria: Dict[str, Any] = Field(..., description="Search criteria used")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
    data_sources: List[str] = Field(..., description="Data sources queried")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "total_results": 25,
                "search_criteria": {"districts": ["Central district"]},
                "execution_time_ms": 150.5,
                "data_sources": ["s3_restaurant_data"]
            }
        }


class RestaurantSearchResponse(BaseModel):
    """Response model for restaurant search operations."""
    
    success: bool = Field(True, description="Indicates if the request was successful")
    restaurants: List[RestaurantResponse] = Field(..., description="List of matching restaurants")
    metadata: SearchResultMetadata = Field(..., description="Search result metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "success": True,
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Great Restaurant",
                        "address": "123 Main St, Central",
                        "meal_type": ["lunch", "dinner"],
                        "sentiment": {
                            "likes": 85,
                            "dislikes": 10,
                            "neutral": 5,
                            "total_responses": 100,
                            "likes_percentage": 85.0,
                            "combined_positive_percentage": 90.0
                        },
                        "location_category": "Shopping Mall",
                        "district": "Central district",
                        "price_range": "$$"
                    }
                ],
                "metadata": {
                    "total_results": 1,
                    "search_criteria": {"districts": ["Central district"]},
                    "execution_time_ms": 150.5,
                    "data_sources": ["s3_restaurant_data"]
                },
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class AnalysisSummary(BaseModel):
    """Summary statistics for sentiment analysis."""
    
    restaurant_count: int = Field(..., description="Number of restaurants analyzed")
    average_likes: float = Field(..., description="Average likes across all restaurants")
    average_dislikes: float = Field(..., description="Average dislikes across all restaurants")
    average_neutral: float = Field(..., description="Average neutral responses across all restaurants")
    top_sentiment_score: float = Field(..., description="Highest sentiment score found")
    bottom_sentiment_score: float = Field(..., description="Lowest sentiment score found")
    ranking_method: str = Field(..., description="Ranking method used for analysis")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "restaurant_count": 10,
                "average_likes": 75.5,
                "average_dislikes": 15.2,
                "average_neutral": 9.3,
                "top_sentiment_score": 95.0,
                "bottom_sentiment_score": 45.0,
                "ranking_method": "sentiment_likes"
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for restaurant recommendation operations."""
    
    success: bool = Field(True, description="Indicates if the request was successful")
    recommendation: RestaurantResponse = Field(..., description="Top recommended restaurant")
    candidates: List[RestaurantResponse] = Field(..., description="List of candidate restaurants (top 20)")
    ranking_method: str = Field(..., description="Ranking method used")
    analysis_summary: AnalysisSummary = Field(..., description="Statistical analysis summary")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "success": True,
                "recommendation": {
                    "id": "rest_001",
                    "name": "Top Restaurant",
                    "address": "123 Main St, Central",
                    "meal_type": ["lunch", "dinner"],
                    "sentiment": {
                        "likes": 95,
                        "dislikes": 3,
                        "neutral": 2,
                        "total_responses": 100,
                        "likes_percentage": 95.0,
                        "combined_positive_percentage": 97.0
                    },
                    "location_category": "Shopping Mall",
                    "district": "Central district",
                    "price_range": "$$"
                },
                "candidates": [],
                "ranking_method": "sentiment_likes",
                "analysis_summary": {
                    "restaurant_count": 10,
                    "average_likes": 75.5,
                    "average_dislikes": 15.2,
                    "average_neutral": 9.3,
                    "top_sentiment_score": 95.0,
                    "bottom_sentiment_score": 45.0,
                    "ranking_method": "sentiment_likes"
                },
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis operations."""
    
    success: bool = Field(True, description="Indicates if the request was successful")
    sentiment_analysis: AnalysisSummary = Field(..., description="Sentiment analysis results")
    restaurant_count: int = Field(..., description="Number of restaurants analyzed")
    ranking_method: str = Field(..., description="Ranking method used for analysis")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "success": True,
                "sentiment_analysis": {
                    "restaurant_count": 10,
                    "average_likes": 75.5,
                    "average_dislikes": 15.2,
                    "average_neutral": 9.3,
                    "top_sentiment_score": 95.0,
                    "bottom_sentiment_score": 45.0,
                    "ranking_method": "sentiment_likes"
                },
                "restaurant_count": 10,
                "ranking_method": "sentiment_likes",
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "field": "districts",
                "message": "Invalid district name provided",
                "code": "INVALID_DISTRICT"
            }
        }


class SuccessResponse(BaseModel):
    """Response model for successful operations."""
    
    success: bool = Field(True, description="Always true for success responses")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {
                    "operation": "config_update",
                    "affected_items": 1
                },
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error conditions."""
    
    success: bool = Field(False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    @validator('error')
    def validate_error_structure(cls, v):
        """Validate error structure contains required fields."""
        required_fields = {'type', 'message'}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Error must contain fields: {required_fields}")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "type": "ValidationError",
                    "message": "Invalid district names provided",
                    "details": {
                        "invalid_districts": ["Invalid District"],
                        "available_districts": ["Central district", "Admiralty"]
                    }
                },
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Service version")
    mcp_servers: Dict[str, str] = Field(..., description="MCP server health status")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-03T10:30:00Z",
                "version": "1.0.0",
                "mcp_servers": {
                    "restaurant-search": "healthy",
                    "restaurant-reasoning": "healthy"
                }
            }
        }


class MetricsResponse(BaseModel):
    """Response model for metrics endpoints."""
    
    request_count: int = Field(..., description="Total request count")
    error_count: int = Field(..., description="Total error count")
    average_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "request_count": 1250,
                "error_count": 15,
                "average_response_time_ms": 245.5,
                "uptime_seconds": 86400,
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }