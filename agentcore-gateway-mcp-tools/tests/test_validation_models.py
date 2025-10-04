"""
Unit tests for validation models.

This module contains comprehensive tests for validation models used
for error handling and validation feedback.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from typing import List, Dict, Any

from models.validation_models import (
    ValidationSeverity,
    ValidationErrorCode,
    ValidationIssue,
    ValidationResult,
    DistrictValidationResult,
    MealTypeValidationResult,
    SentimentValidationResult,
    RequestValidationError,
    ValidationSummary,
    FieldValidationRule,
    ValidationRuleSet
)


class TestValidationSeverityEnum:
    """Test ValidationSeverity enum."""
    
    def test_valid_severity_levels(self):
        """Test valid severity level values."""
        assert ValidationSeverity.ERROR == "error"
        assert ValidationSeverity.WARNING == "warning"
        assert ValidationSeverity.INFO == "info"


class TestValidationErrorCodeEnum:
    """Test ValidationErrorCode enum."""
    
    def test_valid_error_codes(self):
        """Test valid error code values."""
        assert ValidationErrorCode.REQUIRED_FIELD_MISSING == "REQUIRED_FIELD_MISSING"
        assert ValidationErrorCode.INVALID_FORMAT == "INVALID_FORMAT"
        assert ValidationErrorCode.INVALID_DISTRICT == "INVALID_DISTRICT"
        assert ValidationErrorCode.INVALID_MEAL_TYPE == "INVALID_MEAL_TYPE"
        assert ValidationErrorCode.DUPLICATE_VALUES == "DUPLICATE_VALUES"


class TestValidationIssue:
    """Test ValidationIssue model."""
    
    def test_valid_validation_issue(self):
        """Test valid validation issue."""
        issue = ValidationIssue(
            field="districts",
            code=ValidationErrorCode.INVALID_DISTRICT,
            message="District 'Invalid District' is not a valid Hong Kong district",
            severity=ValidationSeverity.ERROR,
            value="Invalid District",
            suggestion="Use valid districts like 'Central district', 'Admiralty'"
        )
        
        assert issue.field == "districts"
        assert issue.code == ValidationErrorCode.INVALID_DISTRICT
        assert "Invalid District" in issue.message
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.value == "Invalid District"
        assert "Central district" in issue.suggestion
    
    def test_minimal_validation_issue(self):
        """Test validation issue with only required fields."""
        issue = ValidationIssue(
            field="meal_types",
            code=ValidationErrorCode.EMPTY_LIST,
            message="Meal types list cannot be empty"
        )
        
        assert issue.field == "meal_types"
        assert issue.code == ValidationErrorCode.EMPTY_LIST
        assert issue.severity == ValidationSeverity.ERROR  # Default value
        assert issue.value is None
        assert issue.suggestion is None 
   
    def test_warning_severity_issue(self):
        """Test validation issue with warning severity."""
        issue = ValidationIssue(
            field="price_range",
            code=ValidationErrorCode.INVALID_FORMAT