"""
Unit tests for restaurant data validation service.

This module contains comprehensive tests for the RestaurantDataValidator class,
including validation of restaurant structures, sentiment data, and error reporting.
"""

import pytest
from typing import Dict, Any, List

from services.validation_service import RestaurantDataValidator
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType


class TestRestaurantDataValidator:
    """Test cases for RestaurantDataValidator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.validator = RestaurantDataValidator()
        self.strict_validator = RestaurantDataValidator(strict_mode=True)
        
        # Valid restaurant data for testing
        self.valid_restaurant = {
            "id": "rest_001",
            "name": "Test Restaurant",
            "address": "123 Test Street",
            "meal_type": ["Chinese", "Dim Sum"],
            "sentiment": {
                "likes": 85,
                "dislikes": 10,
                "neutral": 5
            },
            "location_category": "Restaurant",
            "district": "Central",
            "price_range": "$$",
            "operating_hours": {
                "Mon - Fri": ["07:00-11:30", "12:00-15:00", "18:00-22:30"],
                "Sat - Sun": ["07:00-11:30", "12:00-15:00", "18:00-22:30"],
                "Public Holiday": ["07:00-11:30", "12:00-15:00", "18:00-22:30"]
            },
            "metadata": {
                "dataQuality": "high",
                "version": "1.0"
            }
        }
        
        # Valid sentiment data for testing
        self.valid_sentiment = {
            "likes": 85,
            "dislikes": 10,
            "neutral": 5
        }
    
    def test_validate_valid_restaurant_structure(self):
        """Test validation of a valid restaurant structure."""
        result = self.validator.validate_restaurant_structure(self.valid_restaurant)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.valid_count == 1
        assert result.total_count == 1
    
    def test_validate_restaurant_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Test missing ID
        restaurant_no_id = self.valid_restaurant.copy()
        del restaurant_no_id["id"]
        
        result = self.validator.validate_restaurant_structure(restaurant_no_id)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
        assert result.valid_count == 0
        
        # Test missing name
        restaurant_no_name = self.valid_restaurant.copy()
        del restaurant_no_name["name"]
        
        result = self.validator.validate_restaurant_structure(restaurant_no_name)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
        
        # Test missing sentiment
        restaurant_no_sentiment = self.valid_restaurant.copy()
        del restaurant_no_sentiment["sentiment"]
        
        result = self.validator.validate_restaurant_structure(restaurant_no_sentiment)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
    
    def test_validate_restaurant_invalid_types(self):
        """Test validation with invalid field types."""
        # Test invalid ID type
        restaurant_invalid_id = self.valid_restaurant.copy()
        restaurant_invalid_id["id"] = 123  # Should be string
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_id)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        assert result.errors[0].expected_value == "str"
        assert result.errors[0].actual_value == "int"
        
        # Test invalid name type
        restaurant_invalid_name = self.valid_restaurant.copy()
        restaurant_invalid_name["name"] = ["Not", "A", "String"]  # Should be string
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_name)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        
        # Test invalid sentiment type
        restaurant_invalid_sentiment = self.valid_restaurant.copy()
        restaurant_invalid_sentiment["sentiment"] = "not a dict"  # Should be dict
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_sentiment)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
    
    def test_validate_restaurant_invalid_optional_fields(self):
        """Test validation with invalid optional field types."""
        # Test invalid meal_type type
        restaurant_invalid_meal_type = self.valid_restaurant.copy()
        restaurant_invalid_meal_type["meal_type"] = "Chinese"  # Should be list
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_meal_type)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "meal_type"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        
        # Test invalid operating_hours type
        restaurant_invalid_hours = self.valid_restaurant.copy()
        restaurant_invalid_hours["operating_hours"] = "9am-5pm"  # Should be dict
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_hours)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "operating_hours"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
    
    def test_validate_restaurant_not_dict(self):
        """Test validation when restaurant data is not a dictionary."""
        result = self.validator.validate_restaurant_structure("not a dict")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "root"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        assert result.errors[0].expected_value == "dict"
        assert result.errors[0].actual_value == "str"
    
    def test_validate_valid_sentiment_structure(self):
        """Test validation of valid sentiment structure."""
        result = self.validator.validate_sentiment_structure(self.valid_sentiment)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.valid_count == 1
        assert result.total_count == 1
    
    def test_validate_sentiment_missing_fields(self):
        """Test sentiment validation with missing required fields."""
        # Test missing likes
        sentiment_no_likes = self.valid_sentiment.copy()
        del sentiment_no_likes["likes"]
        
        result = self.validator.validate_sentiment_structure(sentiment_no_likes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.likes"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
        
        # Test missing dislikes
        sentiment_no_dislikes = self.valid_sentiment.copy()
        del sentiment_no_dislikes["dislikes"]
        
        result = self.validator.validate_sentiment_structure(sentiment_no_dislikes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.dislikes"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
        
        # Test missing neutral
        sentiment_no_neutral = self.valid_sentiment.copy()
        del sentiment_no_neutral["neutral"]
        
        result = self.validator.validate_sentiment_structure(sentiment_no_neutral)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.neutral"
        assert result.errors[0].error_type == ValidationErrorType.MISSING_FIELD
    
    def test_validate_sentiment_invalid_types(self):
        """Test sentiment validation with invalid field types."""
        # Test invalid likes type
        sentiment_invalid_likes = self.valid_sentiment.copy()
        sentiment_invalid_likes["likes"] = "85"  # Should be int
        
        result = self.validator.validate_sentiment_structure(sentiment_invalid_likes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.likes"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        assert result.errors[0].expected_value == "int"
        assert result.errors[0].actual_value == "str"
        
        # Test invalid dislikes type
        sentiment_invalid_dislikes = self.valid_sentiment.copy()
        sentiment_invalid_dislikes["dislikes"] = 10.5  # Should be int
        
        result = self.validator.validate_sentiment_structure(sentiment_invalid_dislikes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.dislikes"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
    
    def test_validate_sentiment_negative_values(self):
        """Test sentiment validation with negative values."""
        # Test negative likes
        sentiment_negative_likes = self.valid_sentiment.copy()
        sentiment_negative_likes["likes"] = -5
        
        result = self.validator.validate_sentiment_structure(sentiment_negative_likes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.likes"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_VALUE
        assert result.errors[0].expected_value == ">= 0"
        assert result.errors[0].actual_value == "-5"
        
        # Test negative dislikes
        sentiment_negative_dislikes = self.valid_sentiment.copy()
        sentiment_negative_dislikes["dislikes"] = -10
        
        result = self.validator.validate_sentiment_structure(sentiment_negative_dislikes)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment.dislikes"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_VALUE
    
    def test_validate_sentiment_zero_responses_warning(self):
        """Test sentiment validation with zero total responses (warning)."""
        sentiment_zero = {
            "likes": 0,
            "dislikes": 0,
            "neutral": 0
        }
        
        # Normal mode - should be warning only
        result = self.validator.validate_sentiment_structure(sentiment_zero)
        
        assert result.is_valid is True  # Still valid in normal mode
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "no sentiment responses" in result.warnings[0]
        
        # Strict mode - should be error
        result_strict = self.strict_validator.validate_sentiment_structure(sentiment_zero)
        
        assert result_strict.is_valid is False
        assert len(result_strict.errors) == 1
        assert result_strict.errors[0].error_type == ValidationErrorType.EMPTY_DATA
        assert len(result_strict.warnings) == 1
    
    def test_validate_sentiment_not_dict(self):
        """Test sentiment validation when sentiment is not a dictionary."""
        result = self.validator.validate_sentiment_structure("not a dict")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "sentiment"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        assert result.errors[0].expected_value == "dict"
        assert result.errors[0].actual_value == "str"
    
    def test_validate_restaurant_list_valid(self):
        """Test validation of a valid restaurant list."""
        restaurants = [self.valid_restaurant.copy(), self.valid_restaurant.copy()]
        restaurants[1]["id"] = "rest_002"
        restaurants[1]["name"] = "Second Restaurant"
        
        result = self.validator.validate_restaurant_list(restaurants)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.valid_count == 2
        assert result.total_count == 2
    
    def test_validate_restaurant_list_mixed_validity(self):
        """Test validation of restaurant list with mixed valid/invalid restaurants."""
        valid_restaurant = self.valid_restaurant.copy()
        invalid_restaurant = self.valid_restaurant.copy()
        del invalid_restaurant["id"]  # Make it invalid
        
        restaurants = [valid_restaurant, invalid_restaurant]
        
        result = self.validator.validate_restaurant_list(restaurants)
        
        assert result.is_valid is False  # Not all restaurants are valid
        assert len(result.errors) == 1
        assert result.valid_count == 1
        assert result.total_count == 2
        assert result.errors[0].restaurant_id == "index_1"
    
    def test_validate_restaurant_list_not_list(self):
        """Test validation when restaurants data is not a list."""
        result = self.validator.validate_restaurant_list("not a list")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "root"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
        assert result.errors[0].expected_value == "list"
        assert result.errors[0].actual_value == "str"
    
    def test_validate_restaurant_list_empty(self):
        """Test validation of empty restaurant list."""
        result = self.validator.validate_restaurant_list([])
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.EMPTY_DATA
        assert result.total_count == 0
    
    def test_sanitize_restaurant_data(self):
        """Test restaurant data sanitization."""
        dirty_restaurant = {
            "id": "  rest_001  ",  # Extra whitespace
            "name": "  Test   Restaurant  ",  # Extra whitespace
            "address": "123  Test   Street",  # Multiple spaces
            "meal_type": ["  Chinese  ", "", "Dim Sum", None],  # Mixed content
            "sentiment": {
                "likes": "85",  # String instead of int
                "dislikes": -5,  # Negative value
                "neutral": 10.5  # Float instead of int
            },
            "location_category": "  Restaurant  ",
            "district": "Central",
            "price_range": "$$"
        }
        
        sanitized = self.validator.sanitize_restaurant_data(dirty_restaurant)
        
        # Check string field sanitization
        assert sanitized["id"] == "rest_001"
        assert sanitized["name"] == "Test Restaurant"
        assert sanitized["address"] == "123 Test Street"
        assert sanitized["location_category"] == "Restaurant"
        
        # Check meal_type sanitization
        assert sanitized["meal_type"] == ["Chinese", "Dim Sum"]  # Empty and None removed
        
        # Check sentiment sanitization
        assert sanitized["sentiment"]["likes"] == 85  # Converted to int
        assert sanitized["sentiment"]["dislikes"] == 0  # Negative converted to 0
        assert sanitized["sentiment"]["neutral"] == 10  # Float converted to int
    
    def test_get_validation_errors(self):
        """Test getting validation errors for restaurant list."""
        valid_restaurant = self.valid_restaurant.copy()
        invalid_restaurant = self.valid_restaurant.copy()
        del invalid_restaurant["name"]  # Make it invalid
        
        restaurants = [valid_restaurant, invalid_restaurant]
        
        errors = self.validator.get_validation_errors(restaurants)
        
        assert len(errors) == 1
        assert errors[0].field == "name"
        assert errors[0].error_type == ValidationErrorType.MISSING_FIELD
    
    def test_validate_field_constraints(self):
        """Test validation of specific field constraints."""
        # Test empty ID
        restaurant_empty_id = self.valid_restaurant.copy()
        restaurant_empty_id["id"] = "   "  # Empty after strip
        
        result = self.validator.validate_restaurant_structure(restaurant_empty_id)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_VALUE
        assert "cannot be empty" in result.errors[0].message
        
        # Test empty name
        restaurant_empty_name = self.valid_restaurant.copy()
        restaurant_empty_name["name"] = ""
        
        result = self.validator.validate_restaurant_structure(restaurant_empty_name)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "name"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_VALUE
        
        # Test empty meal_type list (warning)
        restaurant_empty_meal_type = self.valid_restaurant.copy()
        restaurant_empty_meal_type["meal_type"] = []
        
        result = self.validator.validate_restaurant_structure(restaurant_empty_meal_type)
        
        assert result.is_valid is True  # Still valid, just warning
        assert len(result.warnings) == 1
        assert "empty meal_type list" in result.warnings[0]
        
        # Test non-string items in meal_type
        restaurant_invalid_meal_items = self.valid_restaurant.copy()
        restaurant_invalid_meal_items["meal_type"] = ["Chinese", 123, "Dim Sum"]
        
        result = self.validator.validate_restaurant_structure(restaurant_invalid_meal_items)
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "meal_type[1]"
        assert result.errors[0].error_type == ValidationErrorType.INVALID_TYPE
    
    def test_validation_result_methods(self):
        """Test ValidationResult helper methods."""
        # Create a validation result with errors and warnings
        restaurant_with_issues = self.valid_restaurant.copy()
        del restaurant_with_issues["name"]  # Missing field
        restaurant_with_issues["meal_type"] = []  # Empty list (warning)
        
        result = self.validator.validate_restaurant_structure(restaurant_with_issues)
        
        # Test helper methods
        assert result.has_errors() is True
        assert result.has_warnings() is True
        
        error_summary = result.error_summary()
        assert "missing_field" in error_summary
        assert error_summary["missing_field"] == 1
        
        # Test to_dict method
        result_dict = result.to_dict()
        assert "is_valid" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict
        assert "error_count" in result_dict
        assert "warning_count" in result_dict
        assert "error_summary" in result_dict
    
    def test_multiple_validation_errors(self):
        """Test validation with multiple errors in single restaurant."""
        invalid_restaurant = {
            "id": 123,  # Wrong type
            "name": "",  # Empty
            "sentiment": {
                "likes": -5,  # Negative
                "dislikes": "invalid",  # Wrong type
                # Missing neutral field
            }
        }
        
        result = self.validator.validate_restaurant_structure(invalid_restaurant)
        
        assert result.is_valid is False
        assert len(result.errors) >= 4  # Multiple errors
        
        # Check that we have different types of errors
        error_types = [error.error_type for error in result.errors]
        assert ValidationErrorType.INVALID_TYPE in error_types
        assert ValidationErrorType.INVALID_VALUE in error_types
        assert ValidationErrorType.MISSING_FIELD in error_types


if __name__ == "__main__":
    pytest.main([__file__])