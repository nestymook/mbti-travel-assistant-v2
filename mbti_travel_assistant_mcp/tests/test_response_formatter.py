"""
Comprehensive Unit Tests for Response Formatter Service

Tests all aspects of response formatting including restaurant formatting,
metadata generation, error handling, and validation integration.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from services.response_formatter import ResponseFormatter, ErrorCode
from services.response_validator import ResponseValidator, ValidationResult
from models.request_models import RecommendationRequest


class TestResponseFormatter:
    """Comprehensive test cases for ResponseFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create response formatter instance."""
        return ResponseFormatter()
    
    @pytest.fixture
    def sample_request(self):
        """Create sample recommendation request."""
        return RecommendationRequest(
            district="Central district",
            meal_time="breakfast"
        )
    
    @pytest.fixture
    def sample_restaurant_data(self):
        """Create sample restaurant data."""
        return {
            "id": "rest_001",
            "name": "Test Restaurant",
            "address": "123 Test Street",
            "district": "Central district",
            "meal_type": ["breakfast", "lunch"],
            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
            "price_range": "$",
            "operating_hours": {"Monday": ["07:00", "11:30"], "Tuesday": ["07:00", "11:30"]},
            "location_category": "Shopping Mall",
            "cuisine_type": "Asian",
            "rating": 4.5,
            "image_url": "https://example.com/image.jpg"
        }
    
    @pytest.fixture
    def sample_response_data(self, sample_restaurant_data):
        """Create sample response data."""
        return {
            "recommendation": sample_restaurant_data,
            "candidates": [sample_restaurant_data],
            "metadata": {
                "total_found": 1,
                "mcp_calls": ["search", "reasoning"],
                "cache_hit": False,
                "agent_version": "1.0.0"
            }
        }
    
    def test_format_response_success(self, formatter, sample_response_data, sample_request):
        """Test successful response formatting."""
        start_time = datetime.utcnow()
        correlation_id = "test-123"
        
        with patch.object(formatter.validator, 'validate_response') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[], warnings=[])
            
            with patch.object(formatter.validator, 'sanitize_response') as mock_sanitize:
                mock_sanitize.return_value = sample_response_data
                
                result = formatter.format_response(
                    sample_response_data,
                    sample_request,
                    start_time,
                    correlation_id
                )
        
        assert result is not None
        assert "recommendation" in result
        assert "candidates" in result
        assert "metadata" in result
        assert result["recommendation"]["id"] == "rest_001"
        assert len(result["candidates"]) == 1
        assert result["metadata"]["correlationId"] == correlation_id
    
    def test_format_response_validation_failure(self, formatter, sample_response_data, sample_request):
        """Test response formatting when validation fails."""
        start_time = datetime.utcnow()
        correlation_id = "test-123"
        
        with patch.object(formatter.validator, 'validate_response') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                errors=["Invalid restaurant structure"],
                warnings=[]
            )
            
            with patch.object(formatter.validator, 'create_fallback_response') as mock_fallback:
                mock_fallback.return_value = {"error": "validation_failed"}
                
                result = formatter.format_response(
                    sample_response_data,
                    sample_request,
                    start_time,
                    correlation_id
                )
        
        assert result == {"error": "validation_failed"}
        mock_fallback.assert_called_once_with("Response validation failed", correlation_id)
    
    def test_format_response_with_error(self, formatter, sample_request):
        """Test formatting response that contains error information."""
        start_time = datetime.utcnow()
        correlation_id = "test-123"
        
        response_data = {
            "recommendation": None,
            "candidates": [],
            "metadata": {"total_found": 0},
            "error": {
                "error_type": "NO_RESULTS_FOUND",
                "message": "No restaurants found",
                "suggested_actions": ["Try different criteria"]
            }
        }
        
        with patch.object(formatter.validator, 'validate_response') as mock_validate:
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[], warnings=[])
            
            with patch.object(formatter.validator, 'sanitize_response') as mock_sanitize:
                mock_sanitize.return_value = response_data
                
                result = formatter.format_response(
                    response_data,
                    sample_request,
                    start_time,
                    correlation_id
                )
        
        assert "error" in result
        assert result["error"]["errorType"] == "NO_RESULTS_FOUND"
        assert result["error"]["message"] == "No restaurants found"
        assert "timestamp" in result["error"]
    
    def test_format_response_exception_handling(self, formatter, sample_request):
        """Test exception handling during response formatting."""
        start_time = datetime.utcnow()
        correlation_id = "test-123"
        
        # Create malformed response data that will cause an exception
        malformed_data = {"invalid": "structure"}
        
        result = formatter.format_response(
            malformed_data,
            sample_request,
            start_time,
            correlation_id
        )
        
        assert result is not None
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert "error" in result
        assert result["error"]["errorType"] == ErrorCode.FORMATTING_ERROR.value
    
    def test_format_candidates_success(self, formatter, sample_restaurant_data):
        """Test successful candidate formatting."""
        candidates = [sample_restaurant_data] * 5
        
        result = formatter._format_candidates(candidates)
        
        assert len(result) == 5
        assert all(candidate["id"] == "rest_001" for candidate in result)
    
    def test_format_candidates_limit_to_19(self, formatter, sample_restaurant_data):
        """Test candidate formatting limits to 19 restaurants."""
        candidates = [sample_restaurant_data] * 25  # More than 19
        
        result = formatter._format_candidates(candidates)
        
        assert len(result) <= 19
    
    def test_format_candidates_empty_list(self, formatter):
        """Test formatting empty candidates list."""
        result = formatter._format_candidates([])
        
        assert result == []
    
    def test_format_candidates_filters_invalid(self, formatter, sample_restaurant_data):
        """Test candidate formatting filters out invalid restaurants."""
        invalid_restaurant = sample_restaurant_data.copy()
        invalid_restaurant["id"] = ""  # Invalid empty ID
        
        candidates = [sample_restaurant_data, invalid_restaurant]
        
        result = formatter._format_candidates(candidates)
        
        # Should only include the valid restaurant
        assert len(result) == 1
        assert result[0]["id"] == "rest_001"
    
    def test_format_restaurant_success(self, formatter, sample_restaurant_data):
        """Test successful restaurant formatting."""
        result = formatter._format_restaurant(sample_restaurant_data)
        
        assert result is not None
        assert result["id"] == "rest_001"
        assert result["name"] == "Test Restaurant"
        assert result["address"] == "123 Test Street"
        assert result["district"] == "Central district"
        assert result["mealType"] == ["breakfast", "lunch"]
        assert result["priceRange"] == "$"
        assert result["locationCategory"] == "Shopping Mall"
        assert result["cuisineType"] == "Asian"
        assert result["rating"] == 4.5
        assert result["imageUrl"] == "https://example.com/image.jpg"
    
    def test_format_restaurant_missing_optional_fields(self, formatter):
        """Test restaurant formatting with only required fields."""
        minimal_data = {
            "id": "rest_002",
            "name": "Minimal Restaurant",
            "address": "456 Simple St",
            "district": "Test District",
            "meal_type": ["lunch"],
            "sentiment": {"likes": 50, "dislikes": 5, "neutral": 5},
            "price_range": "$$",
            "operating_hours": {"Monday": ["12:00", "14:00"]},
            "location_category": "Street Food"
        }
        
        result = formatter._format_restaurant(minimal_data)
        
        assert result is not None
        assert result["id"] == "rest_002"
        assert result["name"] == "Minimal Restaurant"
        assert "cuisineType" not in result
        assert "rating" not in result
        assert "imageUrl" not in result
    
    def test_format_restaurant_empty_id(self, formatter, sample_restaurant_data):
        """Test restaurant formatting with empty ID returns None."""
        sample_restaurant_data["id"] = ""
        
        result = formatter._format_restaurant(sample_restaurant_data)
        
        assert result is None
    
    def test_format_restaurant_empty_name(self, formatter, sample_restaurant_data):
        """Test restaurant formatting with empty name returns None."""
        sample_restaurant_data["name"] = ""
        
        result = formatter._format_restaurant(sample_restaurant_data)
        
        assert result is None
    
    def test_format_restaurant_none_input(self, formatter):
        """Test restaurant formatting with None input."""
        result = formatter._format_restaurant(None)
        
        assert result is None
    
    def test_format_restaurant_exception_handling(self, formatter):
        """Test restaurant formatting exception handling."""
        # Create data that will cause an exception
        malformed_data = {"id": 123}  # Non-string ID
        
        result = formatter._format_restaurant(malformed_data)
        
        assert result is None
    
    def test_format_operating_hours_list_format(self, formatter):
        """Test operating hours formatting from list format."""
        hours_data = {
            "Monday": ["07:00", "11:30"],
            "Tuesday": ["08:00", "12:00"]
        }
        
        result = formatter._format_operating_hours(hours_data)
        
        assert result["Monday"] == "07:00-11:30"
        assert result["Tuesday"] == "08:00-12:00"
    
    def test_format_operating_hours_string_format(self, formatter):
        """Test operating hours formatting from string format."""
        hours_data = {
            "Monday": "07:00-11:30",
            "Tuesday": "08:00-12:00"
        }
        
        result = formatter._format_operating_hours(hours_data)
        
        assert result["Monday"] == "07:00-11:30"
        assert result["Tuesday"] == "08:00-12:00"
    
    def test_format_operating_hours_invalid_format(self, formatter):
        """Test operating hours formatting with invalid format."""
        hours_data = {
            "Monday": ["07:00"],  # Missing end time
            "Tuesday": 123,  # Invalid type
            "Wednesday": None
        }
        
        result = formatter._format_operating_hours(hours_data)
        
        assert result["Monday"] == "Closed"
        assert result["Tuesday"] == "Closed"
        assert result["Wednesday"] == "Closed"
    
    def test_format_operating_hours_empty_input(self, formatter):
        """Test operating hours formatting with empty input."""
        result = formatter._format_operating_hours({})
        
        assert result == {}
    
    def test_format_sentiment_success(self, formatter):
        """Test successful sentiment formatting."""
        sentiment_data = {"likes": 85, "dislikes": 10, "neutral": 5}
        
        result = formatter._format_sentiment(sentiment_data)
        
        assert result["likes"] == 85
        assert result["dislikes"] == 10
        assert result["neutral"] == 5
        assert result["total"] == 100
        assert result["positivePercentage"] == 90.0
        assert result["likesPercentage"] == 85.0
    
    def test_format_sentiment_zero_total(self, formatter):
        """Test sentiment formatting with zero total."""
        sentiment_data = {"likes": 0, "dislikes": 0, "neutral": 0}
        
        result = formatter._format_sentiment(sentiment_data)
        
        assert result["total"] == 0
        assert result["positivePercentage"] == 0.0
        assert result["likesPercentage"] == 0.0
    
    def test_format_sentiment_negative_values(self, formatter):
        """Test sentiment formatting handles negative values."""
        sentiment_data = {"likes": -5, "dislikes": -2, "neutral": -1}
        
        result = formatter._format_sentiment(sentiment_data)
        
        # Should convert negative values to 0
        assert result["likes"] == 0
        assert result["dislikes"] == 0
        assert result["neutral"] == 0
        assert result["total"] == 0
    
    def test_format_sentiment_missing_fields(self, formatter):
        """Test sentiment formatting with missing fields."""
        sentiment_data = {"likes": 50}  # Missing dislikes and neutral
        
        result = formatter._format_sentiment(sentiment_data)
        
        assert result["likes"] == 50
        assert result["dislikes"] == 0
        assert result["neutral"] == 0
        assert result["total"] == 50
    
    def test_format_metadata_success(self, formatter, sample_request):
        """Test successful metadata formatting."""
        metadata = {
            "total_found": 5,
            "mcp_calls": ["search", "reasoning"],
            "cache_hit": True,
            "agent_version": "1.0.0",
            "performance_metrics": {"response_time": 150},
            "search_quality": {"relevance_score": 0.95}
        }
        
        result = formatter._format_metadata(
            metadata,
            sample_request,
            150.5,
            "test-123"
        )
        
        assert result["searchCriteria"]["district"] == "Central district"
        assert result["searchCriteria"]["mealTime"] == "breakfast"
        assert result["totalFound"] == 5
        assert result["processingTimeMs"] == 150.5
        assert result["correlationId"] == "test-123"
        assert result["mcpCalls"] == ["search", "reasoning"]
        assert result["cacheHit"] is True
        assert result["agentVersion"] == "1.0.0"
        assert "timestamp" in result
        assert "responseGenerated" in result
        assert result["performanceMetrics"] == {"response_time": 150}
        assert result["searchQuality"] == {"relevance_score": 0.95}
    
    def test_format_metadata_minimal(self, formatter, sample_request):
        """Test metadata formatting with minimal data."""
        metadata = {}
        
        result = formatter._format_metadata(
            metadata,
            sample_request,
            100.0,
            "test-456"
        )
        
        assert result["searchCriteria"]["district"] == "Central district"
        assert result["totalFound"] == 0
        assert result["processingTimeMs"] == 100.0
        assert result["correlationId"] == "test-456"
        assert result["mcpCalls"] == []
        assert result["cacheHit"] is False
        assert result["agentVersion"] == "1.0.0"
    
    def test_format_error_with_code_dict_input(self, formatter):
        """Test error formatting with dictionary input."""
        error_data = {
            "error_type": "VALIDATION_ERROR",
            "message": "Invalid input",
            "suggested_actions": ["Check input", "Try again"],
            "details": {"field": "district"}
        }
        
        result = formatter._format_error_with_code(error_data)
        
        assert result["errorType"] == "VALIDATION_ERROR"
        assert result["errorCode"] == "VALIDATION_ERROR"
        assert result["message"] == "Invalid input"
        assert result["suggestedActions"] == ["Check input", "Try again"]
        assert result["details"] == {"field": "district"}
        assert "timestamp" in result
    
    def test_format_error_with_code_unknown_type(self, formatter):
        """Test error formatting with unknown error type."""
        error_data = {
            "error_type": "UNKNOWN_ERROR_TYPE",
            "message": "Unknown error"
        }
        
        result = formatter._format_error_with_code(error_data)
        
        assert result["errorType"] == ErrorCode.INTERNAL_ERROR.value
        assert result["errorCode"] == ErrorCode.INTERNAL_ERROR.value
        assert result["message"] == "Unknown error"
    
    def test_format_error_with_code_string_input(self, formatter):
        """Test error formatting with string input."""
        error_data = "Simple error message"
        
        result = formatter._format_error_with_code(error_data)
        
        assert result["errorType"] == ErrorCode.INTERNAL_ERROR.value
        assert result["message"] == "Simple error message"
        assert result["suggestedActions"] == ["Try again", "Contact support if issue persists"]
    
    def test_create_error_response(self, formatter, sample_request):
        """Test creating standardized error response."""
        result = formatter._create_error_response(
            ErrorCode.TIMEOUT_ERROR,
            "Request timed out",
            ["Try again", "Use simpler query"],
            sample_request,
            200.0,
            "test-789"
        )
        
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert result["error"]["errorType"] == ErrorCode.TIMEOUT_ERROR.value
        assert result["error"]["message"] == "Request timed out"
        assert result["error"]["suggestedActions"] == ["Try again", "Use simpler query"]
        assert result["metadata"]["correlationId"] == "test-789"
        assert result["metadata"]["processingTimeMs"] == 200.0
    
    def test_create_no_results_response(self, formatter, sample_request):
        """Test creating no results response."""
        result = formatter.create_no_results_response(
            sample_request,
            100.0,
            "test-no-results"
        )
        
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert result["error"]["errorType"] == ErrorCode.NO_RESULTS_FOUND.value
        assert "No restaurants found for breakfast in Central district" in result["error"]["message"]
        assert "Try a different district" in result["error"]["suggestedActions"]
        assert result["metadata"]["correlationId"] == "test-no-results"
    
    def test_format_response_with_warnings(self, formatter, sample_response_data, sample_request):
        """Test response formatting with validation warnings."""
        start_time = datetime.utcnow()
        correlation_id = "test-warnings"
        
        with patch.object(formatter.validator, 'validate_response') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["Recommendation not in candidates"]
            )
            
            with patch.object(formatter.validator, 'sanitize_response') as mock_sanitize:
                mock_sanitize.return_value = sample_response_data
                
                result = formatter.format_response(
                    sample_response_data,
                    sample_request,
                    start_time,
                    correlation_id
                )
        
        # Should still return valid response despite warnings
        assert result is not None
        assert result["recommendation"]["id"] == "rest_001"
    
    def test_format_restaurant_alternative_field_names(self, formatter):
        """Test restaurant formatting with alternative field names."""
        restaurant_data = {
            "id": "rest_003",
            "name": "Alt Restaurant",
            "address": "789 Alt Street",
            "district": "Alt District",
            "mealType": ["dinner"],  # Alternative field name
            "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
            "priceRange": "$$$",  # Alternative field name
            "operatingHours": {"Monday": "18:00-22:00"},  # Alternative field name
            "locationCategory": "Fine Dining"  # Alternative field name
        }
        
        result = formatter._format_restaurant(restaurant_data)
        
        assert result is not None
        assert result["id"] == "rest_003"
        assert result["mealType"] == ["dinner"]
        assert result["priceRange"] == "$$$"
        assert result["operatingHours"]["Monday"] == "18:00-22:00"
        assert result["locationCategory"] == "Fine Dining"


if __name__ == "__main__":
    pytest.main([__file__])