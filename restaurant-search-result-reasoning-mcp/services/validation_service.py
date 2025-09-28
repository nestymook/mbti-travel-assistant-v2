"""
Restaurant data validation service for reasoning MCP server.

This module provides comprehensive validation for restaurant data structures,
sentiment data, and error reporting functionality for the reasoning system.
"""

import re
from typing import List, Dict, Any, Optional, Union
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType
from models.restaurant_models import Restaurant, Sentiment


class RestaurantDataValidator:
    """
    Validator for restaurant data structures and sentiment information.
    
    Provides comprehensive validation for restaurant data including
    required fields, data types, and sentiment structure validation.
    """
    
    # Required fields for restaurant data
    REQUIRED_RESTAURANT_FIELDS = {
        "id": str,
        "name": str,
        "sentiment": dict
    }
    
    # Optional fields with expected types
    OPTIONAL_RESTAURANT_FIELDS = {
        "address": str,
        "meal_type": list,
        "location_category": str,
        "district": str,
        "price_range": str,
        "operating_hours": dict,
        "metadata": dict
    }
    
    # Required sentiment fields
    REQUIRED_SENTIMENT_FIELDS = {
        "likes": int,
        "dislikes": int,
        "neutral": int
    }
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
    
    def validate_restaurant_structure(self, restaurant: Dict[str, Any]) -> ValidationResult:
        """
        Validate restaurant data structure and required fields.
        
        Args:
            restaurant: Restaurant data dictionary to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True, total_count=1)
        
        # Check if restaurant is a dictionary first
        if not isinstance(restaurant, dict):
            error = ValidationError(
                restaurant_id="unknown",
                field="root",
                error_type=ValidationErrorType.INVALID_TYPE,
                message="Restaurant data must be a dictionary",
                expected_value="dict",
                actual_value=str(type(restaurant).__name__)
            )
            result.add_error(error)
            return result
        
        restaurant_id = restaurant.get("id", "unknown")
        

        
        # Validate required fields
        for field, expected_type in self.REQUIRED_RESTAURANT_FIELDS.items():
            if field not in restaurant:
                error = ValidationError(
                    restaurant_id=restaurant_id,
                    field=field,
                    error_type=ValidationErrorType.MISSING_FIELD,
                    message=f"Missing required field: {field}",
                    expected_value=f"field of type {expected_type.__name__}",
                    actual_value="missing"
                )
                result.add_error(error)
            elif not isinstance(restaurant[field], expected_type):
                error = ValidationError(
                    restaurant_id=restaurant_id,
                    field=field,
                    error_type=ValidationErrorType.INVALID_TYPE,
                    message=f"Invalid type for field {field}",
                    expected_value=expected_type.__name__,
                    actual_value=type(restaurant[field]).__name__
                )
                result.add_error(error)
        
        # Validate optional fields if present
        for field, expected_type in self.OPTIONAL_RESTAURANT_FIELDS.items():
            if field in restaurant and restaurant[field] is not None:
                if not isinstance(restaurant[field], expected_type):
                    error = ValidationError(
                        restaurant_id=restaurant_id,
                        field=field,
                        error_type=ValidationErrorType.INVALID_TYPE,
                        message=f"Invalid type for optional field {field}",
                        expected_value=expected_type.__name__,
                        actual_value=type(restaurant[field]).__name__
                    )
                    result.add_error(error)
        
        # Validate specific field constraints
        self._validate_field_constraints(restaurant, result)
        
        # Validate sentiment structure if present
        if "sentiment" in restaurant and isinstance(restaurant["sentiment"], dict):
            sentiment_result = self.validate_sentiment_structure(restaurant["sentiment"])
            # Merge sentiment validation errors
            for error in sentiment_result.errors:
                error.restaurant_id = restaurant_id  # Update restaurant ID
                result.add_error(error)
            
            # Merge sentiment warnings
            for warning in sentiment_result.warnings:
                result.add_warning(f"Sentiment validation: {warning}")
        
        # Update validation counts
        if result.has_errors():
            result.valid_count = 0
        else:
            result.valid_count = 1
        
        return result
    
    def validate_sentiment_structure(self, sentiment: Dict[str, Any]) -> ValidationResult:
        """
        Validate sentiment data structure and values.
        
        Args:
            sentiment: Sentiment data dictionary to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True, total_count=1)
        
        # Check if sentiment is a dictionary
        if not isinstance(sentiment, dict):
            error = ValidationError(
                restaurant_id="unknown",
                field="sentiment",
                error_type=ValidationErrorType.INVALID_TYPE,
                message="Sentiment data must be a dictionary",
                expected_value="dict",
                actual_value=str(type(sentiment).__name__)
            )
            result.add_error(error)
            return result
        
        # Validate required sentiment fields
        for field, expected_type in self.REQUIRED_SENTIMENT_FIELDS.items():
            if field not in sentiment:
                error = ValidationError(
                    restaurant_id="unknown",
                    field=f"sentiment.{field}",
                    error_type=ValidationErrorType.MISSING_FIELD,
                    message=f"Missing required sentiment field: {field}",
                    expected_value=f"field of type {expected_type.__name__}",
                    actual_value="missing"
                )
                result.add_error(error)
            elif not isinstance(sentiment[field], expected_type):
                error = ValidationError(
                    restaurant_id="unknown",
                    field=f"sentiment.{field}",
                    error_type=ValidationErrorType.INVALID_TYPE,
                    message=f"Invalid type for sentiment field {field}",
                    expected_value=expected_type.__name__,
                    actual_value=type(sentiment[field]).__name__
                )
                result.add_error(error)
            elif sentiment[field] < 0:
                error = ValidationError(
                    restaurant_id="unknown",
                    field=f"sentiment.{field}",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message=f"Sentiment {field} cannot be negative",
                    expected_value=">= 0",
                    actual_value=str(sentiment[field])
                )
                result.add_error(error)
        
        # Check for empty sentiment data (warning)
        if all(field in sentiment for field in self.REQUIRED_SENTIMENT_FIELDS.keys()):
            # Only calculate total if all fields are integers
            try:
                total_responses = sum(sentiment.get(field, 0) for field in self.REQUIRED_SENTIMENT_FIELDS.keys() 
                                    if isinstance(sentiment.get(field, 0), int))
                if total_responses == 0 and len([f for f in self.REQUIRED_SENTIMENT_FIELDS.keys() 
                                                if isinstance(sentiment.get(f), int)]) == len(self.REQUIRED_SENTIMENT_FIELDS):
                    warning = "Restaurant has no sentiment responses (all values are 0)"
                    result.add_warning(warning)
                    if self.strict_mode:
                        error = ValidationError(
                            restaurant_id="unknown",
                            field="sentiment",
                            error_type=ValidationErrorType.EMPTY_DATA,
                            message="Restaurant has no sentiment responses",
                            expected_value="> 0 total responses",
                            actual_value="0 total responses"
                        )
                        result.add_error(error)
            except (TypeError, ValueError):
                # Skip warning calculation if sentiment values are not valid integers
                pass
        
        # Update validation counts
        if result.has_errors():
            result.valid_count = 0
        else:
            result.valid_count = 1
        
        return result
    
    def validate_restaurant_list(self, restaurants: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate a list of restaurant data structures.
        
        Args:
            restaurants: List of restaurant dictionaries to validate
            
        Returns:
            ValidationResult with aggregated validation results
        """
        if not isinstance(restaurants, list):
            result = ValidationResult(is_valid=False, total_count=0)
            error = ValidationError(
                restaurant_id="list",
                field="root",
                error_type=ValidationErrorType.INVALID_TYPE,
                message="Restaurant data must be a list",
                expected_value="list",
                actual_value=str(type(restaurants).__name__)
            )
            result.add_error(error)
            return result
        
        if len(restaurants) == 0:
            result = ValidationResult(is_valid=False, total_count=0)
            error = ValidationError(
                restaurant_id="list",
                field="root",
                error_type=ValidationErrorType.EMPTY_DATA,
                message="Restaurant list cannot be empty",
                expected_value="non-empty list",
                actual_value="empty list"
            )
            result.add_error(error)
            return result
        
        # Aggregate validation results
        aggregate_result = ValidationResult(is_valid=True, total_count=len(restaurants))
        valid_count = 0
        
        for i, restaurant in enumerate(restaurants):
            restaurant_result = self.validate_restaurant_structure(restaurant)
            
            # Update restaurant ID in errors if not set
            for error in restaurant_result.errors:
                if error.restaurant_id == "unknown":
                    error.restaurant_id = f"index_{i}"
                aggregate_result.add_error(error)
            
            # Add warnings with index information
            for warning in restaurant_result.warnings:
                aggregate_result.add_warning(f"Restaurant {i}: {warning}")
            
            if not restaurant_result.has_errors():
                valid_count += 1
        
        aggregate_result.valid_count = valid_count
        aggregate_result.is_valid = (valid_count == len(restaurants))
        
        return aggregate_result
    
    def sanitize_restaurant_data(self, restaurant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize restaurant data by cleaning and normalizing values.
        
        Args:
            restaurant: Restaurant data dictionary to sanitize
            
        Returns:
            Sanitized restaurant data dictionary
        """
        sanitized = restaurant.copy()
        
        # Sanitize string fields
        string_fields = ["id", "name", "address", "location_category", "district", "price_range"]
        for field in string_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                # Strip whitespace and normalize
                sanitized[field] = sanitized[field].strip()
                # Remove extra whitespace
                sanitized[field] = re.sub(r'\s+', ' ', sanitized[field])
        
        # Sanitize meal_type list
        if "meal_type" in sanitized and isinstance(sanitized["meal_type"], list):
            sanitized_meal_types = []
            for meal_type in sanitized["meal_type"]:
                if isinstance(meal_type, str):
                    cleaned = meal_type.strip()
                    if cleaned:  # Only add non-empty strings
                        sanitized_meal_types.append(cleaned)
            sanitized["meal_type"] = sanitized_meal_types
        
        # Sanitize sentiment data
        if "sentiment" in sanitized and isinstance(sanitized["sentiment"], dict):
            sentiment = sanitized["sentiment"]
            for field in self.REQUIRED_SENTIMENT_FIELDS.keys():
                if field in sentiment:
                    # Ensure sentiment values are non-negative integers
                    try:
                        value = int(sentiment[field])
                        sentiment[field] = max(0, value)  # Ensure non-negative
                    except (ValueError, TypeError):
                        sentiment[field] = 0  # Default to 0 for invalid values
        
        return sanitized
    
    def get_validation_errors(self, restaurants: List[Dict[str, Any]]) -> List[ValidationError]:
        """
        Get all validation errors for a list of restaurants.
        
        Args:
            restaurants: List of restaurant dictionaries to validate
            
        Returns:
            List of ValidationError objects
        """
        result = self.validate_restaurant_list(restaurants)
        return result.errors
    
    def _validate_field_constraints(self, restaurant: Dict[str, Any], result: ValidationResult) -> None:
        """
        Validate specific field constraints and business rules.
        
        Args:
            restaurant: Restaurant data dictionary
            result: ValidationResult to add errors to
        """
        restaurant_id = restaurant.get("id", "unknown")
        
        # Validate ID format (should not be empty)
        if "id" in restaurant and isinstance(restaurant["id"], str):
            if not restaurant["id"].strip():
                error = ValidationError(
                    restaurant_id=restaurant_id,
                    field="id",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message="Restaurant ID cannot be empty",
                    expected_value="non-empty string",
                    actual_value="empty string"
                )
                result.add_error(error)
        
        # Validate name (should not be empty)
        if "name" in restaurant and isinstance(restaurant["name"], str):
            if not restaurant["name"].strip():
                error = ValidationError(
                    restaurant_id=restaurant_id,
                    field="name",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message="Restaurant name cannot be empty",
                    expected_value="non-empty string",
                    actual_value="empty string"
                )
                result.add_error(error)
        
        # Validate meal_type list (should not be empty if present)
        if "meal_type" in restaurant and isinstance(restaurant["meal_type"], list):
            if len(restaurant["meal_type"]) == 0:
                warning = "Restaurant has empty meal_type list"
                result.add_warning(warning)
            else:
                # Check for non-string items in meal_type
                for i, meal_type in enumerate(restaurant["meal_type"]):
                    if not isinstance(meal_type, str):
                        error = ValidationError(
                            restaurant_id=restaurant_id,
                            field=f"meal_type[{i}]",
                            error_type=ValidationErrorType.INVALID_TYPE,
                            message=f"Meal type at index {i} must be a string",
                            expected_value="string",
                            actual_value=type(meal_type).__name__
                        )
                        result.add_error(error)