"""
Request models for AgentCore Gateway MCP Tools.

This module contains Pydantic models for validating incoming HTTP requests
to the AgentCore Gateway. These models ensure proper validation of parameters
for restaurant search and reasoning operations.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class MealType(str, Enum):
    """Valid meal types for restaurant search."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class RankingMethod(str, Enum):
    """Valid ranking methods for restaurant recommendations."""
    SENTIMENT_LIKES = "sentiment_likes"
    COMBINED_SENTIMENT = "combined_sentiment"


class DistrictSearchRequest(BaseModel):
    """Request model for district-based restaurant search."""
    
    districts: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of Hong Kong districts to search. Must contain at least 1 district.",
        json_schema_extra={"example": ["Central district", "Admiralty", "Causeway Bay"]}
    )
    
    @field_validator('districts')
    @classmethod
    def validate_districts(cls, v):
        """Validate district names are not empty and properly formatted."""
        if not v:
            raise ValueError("Districts list cannot be empty")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_districts = []
        for district in v:
            if district and district.strip():
                district_clean = district.strip()
                if district_clean not in seen:
                    seen.add(district_clean)
                    unique_districts.append(district_clean)
        
        if not unique_districts:
            raise ValueError("At least one valid district name is required")
        
        return unique_districts
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "districts": ["Central district", "Admiralty"]
            }
        }
    }


class MealTypeSearchRequest(BaseModel):
    """Request model for meal type-based restaurant search."""
    
    meal_types: List[MealType] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="List of meal types to search for. Valid values: breakfast, lunch, dinner",
        json_schema_extra={"example": ["breakfast", "lunch"]}
    )
    
    @field_validator('meal_types')
    @classmethod
    def validate_meal_types(cls, v):
        """Validate meal types and remove duplicates."""
        if not v:
            raise ValueError("Meal types list cannot be empty")
        
        # Remove duplicates while preserving order
        unique_meal_types = []
        seen = set()
        for meal_type in v:
            if meal_type not in seen:
                seen.add(meal_type)
                unique_meal_types.append(meal_type)
        
        return unique_meal_types
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "meal_types": ["breakfast", "lunch"]
            }
        }
    }


class CombinedSearchRequest(BaseModel):
    """Request model for combined district and meal type search."""
    
    districts: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Optional list of Hong Kong districts to filter by",
        json_schema_extra={"example": ["Central district", "Admiralty"]}
    )
    
    meal_types: Optional[List[MealType]] = Field(
        None,
        min_length=1,
        max_length=3,
        description="Optional list of meal types to filter by. Valid values: breakfast, lunch, dinner",
        json_schema_extra={"example": ["breakfast", "lunch"]}
    )
    
    @field_validator('districts')
    @classmethod
    def validate_districts(cls, v):
        """Validate district names if provided."""
        if v is None:
            return v
        
        if not v:
            raise ValueError("Districts list cannot be empty if provided")
        
        # Remove duplicates and empty values
        seen = set()
        unique_districts = []
        for district in v:
            if district and district.strip():
                district_clean = district.strip()
                if district_clean not in seen:
                    seen.add(district_clean)
                    unique_districts.append(district_clean)
        
        if not unique_districts:
            raise ValueError("At least one valid district name is required if districts are provided")
        
        return unique_districts
    
    @field_validator('meal_types')
    @classmethod
    def validate_meal_types(cls, v):
        """Validate meal types if provided."""
        if v is None:
            return v
        
        if not v:
            raise ValueError("Meal types list cannot be empty if provided")
        
        # Remove duplicates
        unique_meal_types = []
        seen = set()
        for meal_type in v:
            if meal_type not in seen:
                seen.add(meal_type)
                unique_meal_types.append(meal_type)
        
        return unique_meal_types
    
    @model_validator(mode='after')
    def validate_at_least_one_filter(self):
        """Ensure at least one filter is provided."""
        if not self.districts and not self.meal_types:
            raise ValueError("At least one of 'districts' or 'meal_types' must be provided")
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "districts": ["Central district"],
                "meal_types": ["lunch", "dinner"]
            }
        }
    }


class RestaurantData(BaseModel):
    """Model for individual restaurant data in recommendation requests."""
    
    id: str = Field(..., description="Unique restaurant identifier")
    name: str = Field(..., description="Restaurant name")
    sentiment: Dict[str, int] = Field(
        ...,
        description="Sentiment data with likes, dislikes, and neutral counts"
    )
    address: Optional[str] = Field(None, description="Restaurant address")
    district: Optional[str] = Field(None, description="Restaurant district")
    meal_type: Optional[List[str]] = Field(None, description="Supported meal types")
    price_range: Optional[str] = Field(None, description="Price range category")
    location_category: Optional[str] = Field(None, description="Location category")
    
    @field_validator('sentiment')
    @classmethod
    def validate_sentiment(cls, v):
        """Validate sentiment data structure."""
        required_fields = {'likes', 'dislikes', 'neutral'}
        
        if not isinstance(v, dict):
            raise ValueError("Sentiment must be a dictionary")
        
        missing_fields = required_fields - set(v.keys())
        if missing_fields:
            raise ValueError(f"Sentiment missing required fields: {missing_fields}")
        
        # Validate all values are non-negative integers
        for field, value in v.items():
            if field in required_fields:
                if not isinstance(value, int) or value < 0:
                    raise ValueError(f"Sentiment field '{field}' must be a non-negative integer")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "rest_001",
                "name": "Great Restaurant",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "address": "123 Main St",
                "district": "Central district"
            }
        }
    }


class RestaurantRecommendationRequest(BaseModel):
    """Request model for restaurant recommendation analysis."""
    
    restaurants: List[RestaurantData] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of restaurant data with sentiment information for analysis"
    )
    
    ranking_method: RankingMethod = Field(
        default=RankingMethod.SENTIMENT_LIKES,
        description="Method to use for ranking restaurants. 'sentiment_likes' ranks by likes count, 'combined_sentiment' ranks by likes + neutral percentage"
    )
    
    @field_validator('restaurants')
    @classmethod
    def validate_restaurants(cls, v):
        """Validate restaurant data list."""
        if not v:
            raise ValueError("Restaurants list cannot be empty")
        
        # Check for duplicate IDs
        ids = [restaurant.id for restaurant in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Restaurant IDs must be unique")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Great Restaurant",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                        "address": "123 Main St",
                        "district": "Central district"
                    }
                ],
                "ranking_method": "sentiment_likes"
            }
        }
    }


class SentimentAnalysisRequest(BaseModel):
    """Request model for restaurant sentiment analysis."""
    
    restaurants: List[RestaurantData] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of restaurant data for sentiment analysis"
    )
    
    @field_validator('restaurants')
    @classmethod
    def validate_restaurants(cls, v):
        """Validate restaurant data list."""
        if not v:
            raise ValueError("Restaurants list cannot be empty")
        
        # Check for duplicate IDs
        ids = [restaurant.id for restaurant in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Restaurant IDs must be unique")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Restaurant A",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    },
                    {
                        "id": "rest_002",
                        "name": "Restaurant B",
                        "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10}
                    }
                ]
            }
        }
    }