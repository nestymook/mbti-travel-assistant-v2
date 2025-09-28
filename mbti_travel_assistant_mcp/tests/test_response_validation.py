"""
Tests for Response Validation Service

Tests the response validation functionality including JSON schema validation,
size validation, and fallback response generation.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.response_validator import ResponseValidator, ValidationResult
from services.response_formatter import ResponseFormatter
from models.request_models import RecommendationRequest


class TestResponseValidator:
    """Test cases for ResponseValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ResponseValidator()
        self.sample_restaurant = {
            "id": "rest_001",
            "name": "Test Restaurant",
            "address": "123 Test St",
            "district": "Central district",
            "mealType": ["breakfast"],
            "sentiment": {
                "likes": 85,
                "dislikes": 10,
                "neutral": 5,
                "total": 100,
                "positivePercentage": 90.0,
                "likesPercentage": 85.0
            },
            "priceRange": "$$",
            "operatingHours": {
                "Monday": "07:00-11:30",
                "Tuesday": "07:00-11:30"
            },
            "locationCategory": "Shopping Mall"
        }
        
        self.sample_response = {
            "recommendation": self.sample_restaurant,
            "candidates": [self.sample_restaurant],
            "metadata": {
                "searchCriteria": {
                    "district": "Central district",
                    "mealTime": "breakfast",
                    "naturalLanguageQuery": None
                },
                "totalFound": 1,
                "timestamp": "2024-01-01T12:00:00Z",
                "processingTimeMs": 150.5,
                "correlationId": "test-123",
                "mcpCalls": ["search", "reasoning"],
                "cacheHit": False,
                "agentVersion": "1.0.0",
                "responseGenerated": "2024-01-01 12:00:00 UTC"
            }
        }
    
    def test_validate_valid_response(self):
        """Test validation of a valid response."""
        result = self.validator.validate_response(self.sample_response)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.size_bytes > 0
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields."""
        invalid_response = {"recommendation": None}
        
        result = self.validator.validate_response(invalid_response)
        
        assert not result.is_valid
        assert "Missing required field: candidates" in result.errors
        assert "Missing required field: metadata" in result.errors
    
    def test_validate_invalid_restaurant_structure(self):
        """Test validation with invalid restaurant structure."""
        invalid_response = self.sample_response.copy()
        invalid_response["recommendation"] = {
            "id": "",  # Empty ID should fail
            "name": "Test Restaurant"
            # Missing other required fields
        }
        
        result = self.validator.validate_response(invalid_response)
        
        assert not result.is_valid
        assert any("ID cannot be empty" in error for error in result.errors)
    
    def test_validate_too_many_candidates(self):
        """Test validation with too many candidates."""
        invalid_response = self.sample_response.copy()
        invalid_response["candidates"] = [self.sample_restaurant] * 25  # Exceeds limit of 19
        
        result = self.validator.validate_response(invalid_response)
        
        assert not result.is_valid
        assert any("Too many candidates" in error for error in result.errors)
    
    def test_validate_invalid_sentiment(self):
        """Test validation with invalid sentiment data."""
        invalid_restaurant = self.sample_restaurant.copy()
        invalid_restaurant["sentiment"] = {
            "likes": -5,  # Negative value should fail
            "dislikes": "invalid",  # Non-numeric should fail
            "neutral": 5,
            "total": 10  # Doesn't match calculated total
        }
        
        invalid_response = self.sample_response.copy()
        invalid_response["recommendation"] = invalid_restaurant
        
        result = self.validator.validate_response(invalid_response)
        
        assert not result.is_valid
        assert any("must be a non-negative integer" in error for error in result.errors)
    
    def test_validate_invalid_timestamp(self):
        """Test validation with invalid timestamp."""
        invalid_response = self.sample_response.copy()
        invalid_response["metadata"]["timestamp"] = "invalid-timestamp"
        
        result = self.validator.validate_response(invalid_response)
        
        assert not result.is_valid
        assert any("valid ISO 8601 datetime" in error for error in result.errors)
    
    def test_validate_business_rules(self):
        """Test business rule validation."""
        # Test case where recommendation is not in candidates
        invalid_response = self.sample_response.copy()
        invalid_response["recommendation"] = invalid_response["recommendation"].copy()
        invalid_response["recommendation"]["id"] = "different_id"
        
        result = self.validator.validate_response(invalid_response)
        
        
        # Should still be valid but have warnings
        assert result.is_valid
        assert any("not included in candidates" in warning for warning in result.warnings)
    
    def test_create_fallback_response(self):
        """Test fallback response creation."""
        fallback = self.validator.create_fallback_response(
            "Test error message",
            "test-correlation-id"
        )
        
        # Validate the fallback response structure
        result = self.validator.validate_response(fallback)
        
        assert result.is_valid
        assert fallback["recommendation"] is None
        assert fallback["candidates"] == []
        assert fallback["error"]["message"] == "Test error message"
        assert fallback["metadata"]["correlationId"] == "test-correlation-id"
    
    def test_sanitize_response_size_limit(self):
        """Test response sanitization for size limits."""
        # Create a response with many candidates
        large_response = self.sample_response.copy()
        large_response["candidates"] = [self.sample_restaurant] * 25
        
        sanitized = self.validator.sanitize_response(large_response)
        
        # Should be limited to 19 candidates
        assert len(sanitized["candidates"]) <= 19
        assert len(sanitized["candidates"]) < len(large_response["candidates"])
    
    def test_sanitize_response_preserves_valid_data(self):
        """Test that sanitization preserves valid data."""
        sanitized = self.validator.sanitize_response(self.sample_response)
        
        # Should be identical for valid response
        assert sanitized == self.sample_response
    
    @patch('services.response_validator.ResponseValidator.MAX_RESPONSE_SIZE', 100)
    def test_sanitize_oversized_response(self):
        """Test sanitization of oversized response."""
        # This response will be too large with the mocked size limit
        sanitized = self.validator.sanitize_response(self.sample_response)
        
        # Should have fewer or no candidates
        assert len(sanitized["candidates"]) <= len(self.sample_response["candidates"])


class TestResponseFormatterWithValidation:
    """Test ResponseFormatter integration with validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ResponseFormatter()
        self.request = RecommendationRequest(
            district="Central district",
            meal_time="breakfast"
        )
        self.start_time = datetime.utcnow()
    
    def test_format_response_with_validation(self):
        """Test response formatting with validation."""
        response_data = {
            "recommendation": {
                "id": "rest_001",
                "name": "Test Restaurant",
                "address": "123 Test St",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "price_range": "$$",
                "operating_hours": {"Monday": ["07:00", "11:30"]},
                "location_category": "Shopping Mall"
            },
            "candidates": [],
            "metadata": {"total_found": 1}
        }
        
        result = self.formatter.format_response(
            response_data,
            self.request,
            self.start_time,
            "test-correlation"
        )
        
        # Should be valid and properly formatted
        assert result is not None
        assert "recommendation" in result
        assert "candidates" in result
        assert "metadata" in result
        assert result["recommendation"]["id"] == "rest_001"
    
    def test_format_response_validation_failure(self):
        """Test response formatting when validation fails."""
        # Create invalid response data
        invalid_data = {
            "recommendation": {
                "id": "",  # Empty ID should cause validation failure
                "name": ""  # Empty name should cause validation failure
            },
            "candidates": [],
            "metadata": {}
        }
        
        result = self.formatter.format_response(
            invalid_data,
            self.request,
            self.start_time,
            "test-correlation"
        )
        
        # Should return response with None recommendation (filtered out)
        assert result is not None
        assert result["recommendation"] is None
        assert result["candidates"] == []
        # Should have warnings but still be valid since empty results are acceptable
    
    def test_format_response_with_oversized_candidates(self):
        """Test response formatting with too many candidates."""
        # Create response with many candidates
        many_candidates = []
        for i in range(25):  # Exceeds limit of 19
            many_candidates.append({
                "id": f"rest_{i:03d}",
                "name": f"Restaurant {i}",
                "address": f"{i} Test St",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "price_range": "$$",
                "operating_hours": {"Monday": ["07:00", "11:30"]},
                "location_category": "Shopping Mall"
            })
        
        response_data = {
            "recommendation": many_candidates[0],
            "candidates": many_candidates,
            "metadata": {"total_found": 25}
        }
        
        result = self.formatter.format_response(
            response_data,
            self.request,
            self.start_time,
            "test-correlation"
        )
        
        # Should be sanitized to 19 candidates
        assert len(result["candidates"]) <= 19
    
    def test_format_no_results_response(self):
        """Test formatting of no results response."""
        result = self.formatter.create_no_results_response(
            self.request,
            100.0,
            "test-correlation"
        )
        
        # Validate the no results response
        validator = ResponseValidator()
        validation_result = validator.validate_response(result)
        
        assert validation_result.is_valid
        assert result["error"]["errorType"] == "NO_RESULTS_FOUND"


if __name__ == "__main__":
    pytest.main([__file__])