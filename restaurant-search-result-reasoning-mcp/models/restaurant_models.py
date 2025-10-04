"""
Restaurant and sentiment data models for reasoning MCP server.

This module contains the core data models for restaurant sentiment analysis
and recommendation functionality, including JSON serialization support.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class OperatingHours:
    """Operating hours for different day types."""
    weekday_open: str
    weekday_close: str
    weekend_open: str
    weekend_close: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "weekday_open": self.weekday_open,
            "weekday_close": self.weekday_close,
            "weekend_open": self.weekend_open,
            "weekend_close": self.weekend_close
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperatingHours":
        """Create from dictionary."""
        return cls(
            weekday_open=data["weekday_open"],
            weekday_close=data["weekday_close"],
            weekend_open=data["weekend_open"],
            weekend_close=data["weekend_close"]
        )


@dataclass
class RestaurantMetadata:
    """Metadata for individual restaurant records."""
    source: str
    last_updated: str
    data_quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "last_updated": self.last_updated,
            "data_quality_score": self.data_quality_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestaurantMetadata":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            last_updated=data["last_updated"],
            data_quality_score=data["data_quality_score"]
        )


@dataclass
class FileMetadata:
    """Metadata for restaurant data files."""
    file_name: str
    total_restaurants: int
    data_source: str
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_name": self.file_name,
            "total_restaurants": self.total_restaurants,
            "data_source": self.data_source,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        """Create from dictionary."""
        return cls(
            file_name=data["file_name"],
            total_restaurants=data["total_restaurants"],
            data_source=data["data_source"],
            last_updated=data["last_updated"]
        )


@dataclass
class Sentiment:
    """
    Sentiment data model for restaurant customer feedback.
    
    Contains likes, dislikes, and neutral response counts with
    calculation methods for sentiment analysis.
    """
    likes: int
    dislikes: int
    neutral: int
    
    def total_responses(self) -> int:
        """Calculate total number of sentiment responses."""
        return self.likes + self.dislikes + self.neutral
    
    def likes_percentage(self) -> float:
        """
        Calculate percentage of likes out of total responses.
        
        Returns:
            Percentage of likes (0.0 to 100.0), or 0.0 if no responses.
        """
        total = self.total_responses()
        return (self.likes / total * 100) if total > 0 else 0.0
    
    def combined_positive_percentage(self) -> float:
        """
        Calculate combined likes + neutral percentage.
        
        Returns:
            Percentage of positive sentiment (likes + neutral) out of total.
        """
        total = self.total_responses()
        return ((self.likes + self.neutral) / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sentiment to dictionary for JSON serialization."""
        return {
            "likes": self.likes,
            "dislikes": self.dislikes,
            "neutral": self.neutral,
            "total_responses": self.total_responses(),
            "likes_percentage": self.likes_percentage(),
            "combined_positive_percentage": self.combined_positive_percentage()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sentiment":
        """Create Sentiment instance from dictionary."""
        return cls(
            likes=data["likes"],
            dislikes=data["dislikes"],
            neutral=data["neutral"]
        )


@dataclass
class Restaurant:
    """
    Restaurant data model with sentiment information.
    
    Contains all restaurant details including sentiment data
    for recommendation analysis.
    """
    id: str
    name: str
    address: str
    meal_type: List[str]
    sentiment: Sentiment
    location_category: str
    district: str
    price_range: str
    operating_hours: Optional[OperatingHours] = None
    metadata: Optional[RestaurantMetadata] = None
    
    def sentiment_score(self) -> float:
        """Calculate sentiment score for ranking (likes percentage)."""
        return self.sentiment.likes_percentage()
    
    def combined_sentiment_score(self) -> float:
        """Calculate combined sentiment score for ranking."""
        return self.sentiment.combined_positive_percentage()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert restaurant to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "meal_type": self.meal_type,
            "sentiment": self.sentiment.to_dict(),
            "location_category": self.location_category,
            "district": self.district,
            "price_range": self.price_range
        }
        
        if self.operating_hours is not None:
            result["operating_hours"] = self.operating_hours.to_dict()
            
        if self.metadata is not None:
            result["metadata"] = self.metadata.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Restaurant":
        """Create Restaurant instance from dictionary."""
        sentiment_data = data.get("sentiment", {})
        sentiment = Sentiment.from_dict(sentiment_data)
        
        # Handle operating hours
        operating_hours = None
        if "operating_hours" in data and data["operating_hours"]:
            operating_hours = OperatingHours.from_dict(data["operating_hours"])
        
        # Handle metadata
        metadata = None
        if "metadata" in data and data["metadata"]:
            metadata = RestaurantMetadata.from_dict(data["metadata"])
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            address=data.get("address", ""),
            meal_type=data.get("meal_type", data.get("mealType", [])),
            sentiment=sentiment,
            location_category=data.get("location_category", data.get("locationCategory", "")),
            district=data.get("district", ""),
            price_range=data.get("price_range", data.get("priceRange", "")),
            operating_hours=operating_hours,
            metadata=metadata
        )


@dataclass
class RecommendationResult:
    """
    Structured result for restaurant recommendations.
    
    Contains candidate list, single recommendation, and analysis metadata.
    """
    candidates: List[Restaurant]
    recommendation: Restaurant
    ranking_method: str
    analysis_summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation result to dictionary for JSON serialization."""
        return {
            "candidates": [restaurant.to_dict() for restaurant in self.candidates],
            "recommendation": self.recommendation.to_dict(),
            "ranking_method": self.ranking_method,
            "analysis_summary": self.analysis_summary,
            "candidate_count": len(self.candidates)
        }
    
    def to_json(self) -> str:
        """Convert recommendation result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationResult":
        """Create RecommendationResult instance from dictionary."""
        candidates = [Restaurant.from_dict(r) for r in data["candidates"]]
        recommendation = Restaurant.from_dict(data["recommendation"])
        
        return cls(
            candidates=candidates,
            recommendation=recommendation,
            ranking_method=data["ranking_method"],
            analysis_summary=data["analysis_summary"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "RecommendationResult":
        """Create RecommendationResult instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class SentimentAnalysis:
    """
    Aggregate sentiment analysis results for a set of restaurants.
    
    Provides statistical summary of sentiment data across restaurants.
    """
    restaurant_count: int
    average_likes: float
    average_dislikes: float
    average_neutral: float
    top_sentiment_score: float
    bottom_sentiment_score: float
    ranking_method: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sentiment analysis to dictionary."""
        return {
            "restaurant_count": self.restaurant_count,
            "average_likes": self.average_likes,
            "average_dislikes": self.average_dislikes,
            "average_neutral": self.average_neutral,
            "top_sentiment_score": self.top_sentiment_score,
            "bottom_sentiment_score": self.bottom_sentiment_score,
            "ranking_method": self.ranking_method
        }
    
    def to_json(self) -> str:
        """Convert sentiment analysis to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SentimentAnalysis":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class RestaurantDataFile:
    """Complete restaurant data file structure."""
    metadata: FileMetadata
    restaurants: List[Restaurant]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RestaurantDataFile':
        """Create RestaurantDataFile from dictionary data."""
        return cls(
            metadata=FileMetadata.from_dict(data.get('metadata', {})),
            restaurants=[
                Restaurant.from_dict(restaurant_data)
                for restaurant_data in data.get('restaurants', [])
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'metadata': self.metadata.to_dict(),
            'restaurants': [restaurant.to_dict() for restaurant in self.restaurants]
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'RestaurantDataFile':
        """Create RestaurantDataFile from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)