"""
Unit tests for response models.

This module contains comprehensive tests for all response models including
validation rules, field constraints, and serialization.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from typing import List, Dict, Any

from models.response_models import (
    ResponseStatus,
    ErrorType,
    SentimentData,
    OperatingHours,
    RestaurantMetadata,
    RestaurantResponse,
    FileMetadata,
    SearchResultMetadata,
    RestaurantSearchResponse,
    AnalysisSummary,
    RecommendationResponse,
    SentimentAnalysisResponse,
    ErrorDetail,
    ErrorResponse,
    HealthCheckResponse,
    MetricsResponse
)


class TestResponseStatusEnum:
    """Test ResponseStatus enum."""
    
    def test_valid_response_statuses(self):
        """Test valid response status values."""
        assert ResponseStatus.SUCCESS == "success"
        assert ResponseStatus.ERROR == "error"


class TestErrorTypeEnum:
    """Test ErrorType enum."""
    
    def test_valid_error_types(self):
        """Test valid error type values."""
        assert ErrorType.VALIDATION_ERROR == "ValidationError"
        assert ErrorType.AUTHENTICATION_ERROR == "AuthenticationError"
        assert ErrorType.AUTHORIZATION_ERROR == "AuthorizationError"
        assert ErrorType.MCP_SERVER_ERROR == "MCPServerError"
        assert ErrorType.SERVICE_UNAVAILABLE == "ServiceUnavailable"
        assert ErrorType.RATE_LIMIT_ERROR == "RateLimitError"
        assert ErrorType.INTERNAL_ERROR == "InternalError"


class TestSentimentData:
    """Test SentimentData model."""
    
    def test_valid_sentiment_data(self):
        """Test valid sentiment data."""
        sentiment = SentimentData(
            likes=85,
            dislikes=10,
            neutral=5,
            total_responses=100,
            likes_percentage=85.0,
            combined_positive_percentage=90.0
        )
        
        assert sentiment.likes == 85
        assert sentiment.dislikes == 10
        assert sentiment.neutral == 5
        assert sentiment.total_responses == 100
        assert sentiment.likes_percentage == 85.0
        assert sentiment.combined_positive_percentage == 90.0
    
    def test_zero_values(self):
        """Test sentiment data with zero values."""
        sentiment = SentimentData(
            likes=0,
            dislikes=0,
            neutral=0,
            total_responses=0,
            likes_percentage=0.0,
            combined_positive_percentage=0.0
        )
        
        assert sentiment.likes == 0
        assert sentiment.total_responses == 0
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentData(likes=85, dislikes=10)  # Missing required fields
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        missing_fields = [error["loc"][0] for error in errors if error["type"] == "missing"]
        assert "neutral" in missing_fields


class TestOperatingHours:
    """Test OperatingHours model."""
    
    def test_valid_operating_hours(self):
        """Test valid operating hours."""
        hours = OperatingHours(
            weekday_open="09:00",
            weekday_close="22:00",
            weekend_open="10:00",
            weekend_close="23:00"
        )
        
        assert hours.weekday_open == "09:00"
        assert hours.weekday_close == "22:00"
        assert hours.weekend_open == "10:00"
        assert hours.weekend_close == "23:00"
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            OperatingHours(weekday_open="09:00")  # Missing other required fields
        
        errors = exc_info.value.errors()
        assert len(errors) >= 3  # Missing 3 fields


class TestRestaurantMetadata:
    """Test RestaurantMetadata model."""
    
    def test_valid_restaurant_metadata(self):
        """Test valid restaurant metadata."""
        metadata = RestaurantMetadata(
            source="restaurant_api",
            last_updated="2025-01-03T10:30:00Z",
            data_quality_score=0.95
        )
        
        assert metadata.source == "restaurant_api"
        assert metadata.last_updated == "2025-01-03T10:30:00Z"
        assert metadata.data_quality_score == 0.95
    
    def test_quality_score_boundaries(self):
        """Test data quality score boundaries."""
        # Test minimum score
        metadata = RestaurantMetadata(
            source="test",
            last_updated="2025-01-03T10:30:00Z",
            data_quality_score=0.0
        )
        assert metadata.data_quality_score == 0.0
        
        # Test maximum score
        metadata = RestaurantMetadata(
            source="test",
            last_updated="2025-01-03T10:30:00Z",
            data_quality_score=1.0
        )
        assert metadata.data_quality_score == 1.0


class TestRestaurantResponse:
    """Test RestaurantResponse model."""
    
    def test_valid_restaurant_response(self):
        """Test valid restaurant response."""
        sentiment = SentimentData(
            likes=85,
            dislikes=10,
            neutral=5,
            total_responses=100,
            likes_percentage=85.0,
            combined_positive_percentage=90.0
        )
        
        restaurant = RestaurantResponse(
            id="rest_001",
            name="Great Restaurant",
            address="123 Main St, Central",
            meal_type=["lunch", "dinner"],
            sentiment=sentiment,
            location_category="Shopping Mall",
            district="Central district",
            price_range="$$"
        )
        
        assert restaurant.id == "rest_001"
        assert restaurant.name == "Great Restaurant"
        assert restaurant.sentiment.likes == 85
        assert len(restaurant.meal_type) == 2
    
    def test_restaurant_with_optional_fields(self):
        """Test restaurant response with optional fields."""
        sentiment = SentimentData(
            likes=85,
            dislikes=10,
            neutral=5,
            total_responses=100,
            likes_percentage=85.0,
            combined_positive_percentage=90.0
        )
        
        hours = OperatingHours(
            weekday_open="09:00",
            weekday_close="22:00",
            weekend_open="10:00",
            weekend_close="23:00"
        )
        
        metadata = RestaurantMetadata(
            source="restaurant_api",
            last_updated="2025-01-03T10:30:00Z",
            data_quality_score=0.95
        )
        
        restaurant = RestaurantResponse(
            id="rest_001",
            name="Great Restaurant",
            address="123 Main St, Central",
            meal_type=["lunch", "dinner"],
            sentiment=sentiment,
            location_category="Shopping Mall",
            district="Central district",
            price_range="$$",
            operating_hours=hours,
            metadata=metadata
        )
        
        assert restaurant.operating_hours is not None
        assert restaurant.metadata is not None
        assert restaurant.operating_hours.weekday_open == "09:00"
        assert restaurant.metadata.data_quality_score == 0.95
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantResponse(id="rest_001", name="Restaurant")  # Missing many required fields
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        missing_fields = [error["loc"][0] for error in errors if error["type"] == "missing"]
        assert "sentiment" in missing_fields


class TestSearchResultMetadata:
    """Test SearchResultMetadata model."""
    
    def test_valid_search_metadata(self):
        """Test valid search result metadata."""
        metadata = SearchResultMetadata(
            total_results=25,
            search_criteria={"districts": ["Central district"]},
            execution_time_ms=150.5,
            data_sources=["s3_restaurant_data"]
        )
        
        assert metadata.total_results == 25
        assert metadata.search_criteria["districts"] == ["Central district"]
        assert metadata.execution_time_ms == 150.5
        assert len(metadata.data_sources) == 1
    
    def test_empty_search_criteria(self):
        """Test metadata with empty search criteria."""
        metadata = SearchResultMetadata(
            total_results=0,
            search_criteria={},
            execution_time_ms=50.0,
            data_sources=[]
        )
        
        assert metadata.total_results == 0
        assert metadata.search_criteria == {}
        assert len(metadata.data_sources) == 0


class TestRestaurantSearchResponse:
    """Test RestaurantSearchResponse model."""
    
    def test_valid_search_response(self):
        """Test valid restaurant search response."""
        sentiment = SentimentData(
            likes=85,
            dislikes=10,
            neutral=5,
            total_responses=100,
            likes_percentage=85.0,
            combined_positive_percentage=90.0
        )
        
        restaurant = RestaurantResponse(
            id="rest_001",
            name="Great Restaurant",
            address="123 Main St, Central",
            meal_type=["lunch", "dinner"],
            sentiment=sentiment,
            location_category="Shopping Mall",
            district="Central district",
            price_range="$$"
        )
        
        metadata = SearchResultMetadata(
            total_results=1,
            search_criteria={"districts": ["Central district"]},
            execution_time_ms=150.5,
            data_sources=["s3_restaurant_data"]
        )
        
        response = RestaurantSearchResponse(
            restaurants=[restaurant],
            metadata=metadata
        )
        
        assert response.success is True
        assert len(response.restaurants) == 1
        assert response.restaurants[0].id == "rest_001"
        assert response.metadata.total_results == 1
        assert isinstance(response.timestamp, datetime)
    
    def test_empty_search_response(self):
        """Test search response with no results."""
        metadata = SearchResultMetadata(
            total_results=0,
            search_criteria={"districts": ["Nonexistent District"]},
            execution_time_ms=75.0,
            data_sources=["s3_restaurant_data"]
        )
        
        response = RestaurantSearchResponse(
            restaurants=[],
            metadata=metadata
        )
        
        assert response.success is True
        assert len(response.restaurants) == 0
        assert response.metadata.total_results == 0


class TestAnalysisSummary:
    """Test AnalysisSummary model."""
    
    def test_valid_analysis_summary(self):
        """Test valid analysis summary."""
        summary = AnalysisSummary(
            restaurant_count=10,
            average_likes=75.5,
            average_dislikes=15.2,
            average_neutral=9.3,
            top_sentiment_score=95.0,
            bottom_sentiment_score=45.0,
            ranking_method="sentiment_likes"
        )
        
        assert summary.restaurant_count == 10
        assert summary.average_likes == 75.5
        assert summary.top_sentiment_score == 95.0
        assert summary.ranking_method == "sentiment_likes"
    
    def test_zero_restaurant_count(self):
        """Test analysis summary with zero restaurants."""
        summary = AnalysisSummary(
            restaurant_count=0,
            average_likes=0.0,
            average_dislikes=0.0,
            average_neutral=0.0,
            top_sentiment_score=0.0,
            bottom_sentiment_score=0.0,
            ranking_method="sentiment_likes"
        )
        
        assert summary.restaurant_count == 0
        assert summary.average_likes == 0.0


class TestRecommendationResponse:
    """Test RecommendationResponse model."""
    
    def test_valid_recommendation_response(self):
        """Test valid recommendation response."""
        sentiment = SentimentData(
            likes=95,
            dislikes=3,
            neutral=2,
            total_responses=100,
            likes_percentage=95.0,
            combined_positive_percentage=97.0
        )
        
        restaurant = RestaurantResponse(
            id="rest_001",
            name="Top Restaurant",
            address="123 Main St, Central",
            meal_type=["lunch", "dinner"],
            sentiment=sentiment,
            location_category="Shopping Mall",
            district="Central district",
            price_range="$$"
        )
        
        summary = AnalysisSummary(
            restaurant_count=10,
            average_likes=75.5,
            average_dislikes=15.2,
            average_neutral=9.3,
            top_sentiment_score=95.0,
            bottom_sentiment_score=45.0,
            ranking_method="sentiment_likes"
        )
        
        response = RecommendationResponse(
            recommendation=restaurant,
            candidates=[restaurant],
            ranking_method="sentiment_likes",
            analysis_summary=summary
        )
        
        assert response.success is True
        assert response.recommendation.id == "rest_001"
        assert len(response.candidates) == 1
        assert response.ranking_method == "sentiment_likes"
        assert isinstance(response.timestamp, datetime)


class TestSentimentAnalysisResponse:
    """Test SentimentAnalysisResponse model."""
    
    def test_valid_sentiment_analysis_response(self):
        """Test valid sentiment analysis response."""
        summary = AnalysisSummary(
            restaurant_count=10,
            average_likes=75.5,
            average_dislikes=15.2,
            average_neutral=9.3,
            top_sentiment_score=95.0,
            bottom_sentiment_score=45.0,
            ranking_method="sentiment_likes"
        )
        
        response = SentimentAnalysisResponse(
            sentiment_analysis=summary,
            restaurant_count=10,
            ranking_method="sentiment_likes"
        )
        
        assert response.success is True
        assert response.sentiment_analysis.restaurant_count == 10
        assert response.restaurant_count == 10
        assert response.ranking_method == "sentiment_likes"
        assert isinstance(response.timestamp, datetime)


class TestErrorResponse:
    """Test ErrorResponse model."""
    
    def test_valid_error_response(self):
        """Test valid error response."""
        error_data = {
            "type": "ValidationError",
            "message": "Invalid district names provided",
            "details": {
                "invalid_districts": ["Invalid District"],
                "available_districts": ["Central district", "Admiralty"]
            }
        }
        
        response = ErrorResponse(error=error_data)
        
        assert response.success is False
        assert response.error["type"] == "ValidationError"
        assert response.error["message"] == "Invalid district names provided"
        assert isinstance(response.timestamp, datetime)
    
    def test_minimal_error_response(self):
        """Test error response with minimal required fields."""
        error_data = {
            "type": "InternalError",
            "message": "Something went wrong"
        }
        
        response = ErrorResponse(error=error_data)
        
        assert response.success is False
        assert response.error["type"] == "InternalError"
        assert response.error["message"] == "Something went wrong"
    
    def test_invalid_error_structure(self):
        """Test validation error for invalid error structure."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(error={"message": "Missing type field"})  # Missing 'type'
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Error must contain fields" in str(error) for error in errors)
    
    def test_empty_error_dict(self):
        """Test validation error for empty error dictionary."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(error={})
        
        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestHealthCheckResponse:
    """Test HealthCheckResponse model."""
    
    def test_valid_health_check_response(self):
        """Test valid health check response."""
        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            mcp_servers={
                "restaurant-search": "healthy",
                "restaurant-reasoning": "healthy"
            }
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert len(response.mcp_servers) == 2
        assert isinstance(response.timestamp, datetime)
    
    def test_unhealthy_status(self):
        """Test health check response with unhealthy status."""
        response = HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            mcp_servers={
                "restaurant-search": "healthy",
                "restaurant-reasoning": "unhealthy"
            }
        )
        
        assert response.status == "unhealthy"
        assert response.mcp_servers["restaurant-reasoning"] == "unhealthy"


class TestMetricsResponse:
    """Test MetricsResponse model."""
    
    def test_valid_metrics_response(self):
        """Test valid metrics response."""
        response = MetricsResponse(
            request_count=1250,
            error_count=15,
            average_response_time_ms=245.5,
            uptime_seconds=86400
        )
        
        assert response.request_count == 1250
        assert response.error_count == 15
        assert response.average_response_time_ms == 245.5
        assert response.uptime_seconds == 86400
        assert isinstance(response.timestamp, datetime)
    
    def test_zero_metrics(self):
        """Test metrics response with zero values."""
        response = MetricsResponse(
            request_count=0,
            error_count=0,
            average_response_time_ms=0.0,
            uptime_seconds=0
        )
        
        assert response.request_count == 0
        assert response.error_count == 0
        assert response.average_response_time_ms == 0.0
        assert response.uptime_seconds == 0


# Integration tests for model serialization
class TestResponseModelSerialization:
    """Test response model serialization and deserialization."""
    
    def test_restaurant_search_response_serialization(self):
        """Test RestaurantSearchResponse serialization."""
        sentiment = SentimentData(
            likes=85,
            dislikes=10,
            neutral=5,
            total_responses=100,
            likes_percentage=85.0,
            combined_positive_percentage=90.0
        )
        
        restaurant = RestaurantResponse(
            id="rest_001",
            name="Great Restaurant",
            address="123 Main St, Central",
            meal_type=["lunch", "dinner"],
            sentiment=sentiment,
            location_category="Shopping Mall",
            district="Central district",
            price_range="$$"
        )
        
        metadata = SearchResultMetadata(
            total_results=1,
            search_criteria={"districts": ["Central district"]},
            execution_time_ms=150.5,
            data_sources=["s3_restaurant_data"]
        )
        
        response = RestaurantSearchResponse(
            restaurants=[restaurant],
            metadata=metadata
        )
        
        # Test dict conversion
        response_dict = response.dict()
        assert response_dict["success"] is True
        assert len(response_dict["restaurants"]) == 1
        assert response_dict["restaurants"][0]["id"] == "rest_001"
        
        # Test JSON conversion
        response_json = response.json()
        assert "rest_001" in response_json
        assert "Great Restaurant" in response_json
        assert "success" in response_json
    
    def test_error_response_serialization(self):
        """Test ErrorResponse serialization."""
        error_data = {
            "type": "ValidationError",
            "message": "Invalid district names provided"
        }
        
        response = ErrorResponse(error=error_data)
        
        # Test dict conversion
        response_dict = response.dict()
        assert response_dict["success"] is False
        assert response_dict["error"]["type"] == "ValidationError"
        
        # Test JSON conversion
        response_json = response.json()
        assert "ValidationError" in response_json
        assert "success" in response_json
    
    def test_datetime_serialization(self):
        """Test datetime serialization in responses."""
        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            mcp_servers={}
        )
        
        # Test JSON conversion includes properly formatted timestamp
        response_json = response.json()
        assert "timestamp" in response_json
        assert "Z" in response_json  # ISO format with Z suffix