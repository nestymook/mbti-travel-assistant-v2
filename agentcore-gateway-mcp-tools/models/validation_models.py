"""
Validation models for AgentCore Gateway MCP Tools.

This module contains Pydantic models for validation results and error handling.
These models provide structured validation feedback and error reporting.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationErrorCode(str, Enum):
    """Standardized validation error codes."""
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"
    INVALID_ENUM_VALUE = "INVALID_ENUM_VALUE"
    DUPLICATE_VALUES = "DUPLICATE_VALUES"
    EMPTY_LIST = "EMPTY_LIST"
    INVALID_DISTRICT = "INVALID_DISTRICT"
    INVALID_MEAL_TYPE = "INVALID_MEAL_TYPE"
    INVALID_SENTIMENT_DATA = "INVALID_SENTIMENT_DATA"
    INVALID_RESTAURANT_ID = "INVALID_RESTAURANT_ID"
    INVALID_RANKING_METHOD = "INVALID_RANKING_METHOD"


class ValidationIssue(BaseModel):
    """Individual validation issue."""
    
    field: str = Field(..., description="Field that has the validation issue")
    code: ValidationErrorCode = Field(..., description="Standardized error code")
    message: str = Field(..., description="Human-readable error message")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR, description="Issue severity")
    value: Optional[Any] = Field(None, description="Invalid value that caused the issue")
    suggestion: Optional[str] = Field(None, description="Suggested correction")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "field": "districts",
                "code": "INVALID_DISTRICT",
                "message": "District 'Invalid District' is not a valid Hong Kong district",
                "severity": "error",
                "value": "Invalid District",
                "suggestion": "Use valid districts like 'Central district', 'Admiralty', or 'Causeway Bay'"
            }
        }


class ValidationResult(BaseModel):
    """Result of validation operation."""
    
    is_valid: bool = Field(..., description="Whether validation passed")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="List of warnings")
    field_count: int = Field(..., description="Number of fields validated")
    error_count: int = Field(..., description="Number of validation errors")
    warning_count: int = Field(..., description="Number of validation warnings")
    
    @validator('error_count', always=True)
    def calculate_error_count(cls, v, values):
        """Calculate error count from issues."""
        issues = values.get('issues', [])
        return len([issue for issue in issues if issue.severity == ValidationSeverity.ERROR])
    
    @validator('warning_count', always=True)
    def calculate_warning_count(cls, v, values):
        """Calculate warning count from issues."""
        issues = values.get('issues', [])
        warnings = values.get('warnings', [])
        return len([issue for issue in issues if issue.severity == ValidationSeverity.WARNING]) + len(warnings)
    
    @validator('is_valid', always=True)
    def determine_validity(cls, v, values):
        """Determine if validation is valid based on error count."""
        error_count = values.get('error_count', 0)
        return error_count == 0
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "is_valid": False,
                "issues": [
                    {
                        "field": "districts",
                        "code": "INVALID_DISTRICT",
                        "message": "Invalid district name provided",
                        "severity": "error",
                        "value": "Invalid District"
                    }
                ],
                "warnings": [],
                "field_count": 2,
                "error_count": 1,
                "warning_count": 0
            }
        }


class DistrictValidationResult(BaseModel):
    """Validation result specific to district validation."""
    
    valid_districts: List[str] = Field(..., description="List of valid districts")
    invalid_districts: List[str] = Field(..., description="List of invalid districts")
    available_districts: List[str] = Field(..., description="List of all available districts")
    suggestions: Dict[str, List[str]] = Field(default_factory=dict, description="Suggestions for invalid districts")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "valid_districts": ["Central district", "Admiralty"],
                "invalid_districts": ["Invalid District"],
                "available_districts": ["Central district", "Admiralty", "Causeway Bay"],
                "suggestions": {
                    "Invalid District": ["Central district", "Admiralty"]
                }
            }
        }


class MealTypeValidationResult(BaseModel):
    """Validation result specific to meal type validation."""
    
    valid_meal_types: List[str] = Field(..., description="List of valid meal types")
    invalid_meal_types: List[str] = Field(..., description="List of invalid meal types")
    available_meal_types: List[str] = Field(default=["breakfast", "lunch", "dinner"], description="List of all available meal types")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "valid_meal_types": ["breakfast", "lunch"],
                "invalid_meal_types": ["brunch"],
                "available_meal_types": ["breakfast", "lunch", "dinner"]
            }
        }


class SentimentValidationResult(BaseModel):
    """Validation result specific to sentiment data validation."""
    
    valid_restaurants: List[str] = Field(..., description="List of restaurant IDs with valid sentiment")
    invalid_restaurants: List[str] = Field(..., description="List of restaurant IDs with invalid sentiment")
    missing_fields: Dict[str, List[str]] = Field(default_factory=dict, description="Missing sentiment fields by restaurant")
    invalid_values: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Invalid sentiment values by restaurant")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "valid_restaurants": ["rest_001", "rest_002"],
                "invalid_restaurants": ["rest_003"],
                "missing_fields": {
                    "rest_003": ["likes", "neutral"]
                },
                "invalid_values": {
                    "rest_003": {"dislikes": -5}
                }
            }
        }


class RequestValidationError(BaseModel):
    """Detailed validation error for requests."""
    
    request_type: str = Field(..., description="Type of request being validated")
    validation_result: ValidationResult = Field(..., description="Validation result details")
    district_validation: Optional[DistrictValidationResult] = Field(None, description="District-specific validation")
    meal_type_validation: Optional[MealTypeValidationResult] = Field(None, description="Meal type-specific validation")
    sentiment_validation: Optional[SentimentValidationResult] = Field(None, description="Sentiment-specific validation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "request_type": "DistrictSearchRequest",
                "validation_result": {
                    "is_valid": False,
                    "issues": [
                        {
                            "field": "districts",
                            "code": "INVALID_DISTRICT",
                            "message": "Invalid district name provided",
                            "severity": "error"
                        }
                    ],
                    "field_count": 1,
                    "error_count": 1,
                    "warning_count": 0
                },
                "district_validation": {
                    "valid_districts": ["Central district"],
                    "invalid_districts": ["Invalid District"],
                    "available_districts": ["Central district", "Admiralty"]
                },
                "timestamp": "2025-01-03T10:30:00Z"
            }
        }


class ValidationSummary(BaseModel):
    """Summary of validation operations."""
    
    total_validations: int = Field(..., description="Total number of validations performed")
    successful_validations: int = Field(..., description="Number of successful validations")
    failed_validations: int = Field(..., description="Number of failed validations")
    common_errors: List[Dict[str, Any]] = Field(..., description="Most common validation errors")
    success_rate: float = Field(..., description="Validation success rate percentage")
    
    @validator('success_rate', always=True)
    def calculate_success_rate(cls, v, values):
        """Calculate success rate from validation counts."""
        total = values.get('total_validations', 0)
        successful = values.get('successful_validations', 0)
        return (successful / total * 100) if total > 0 else 0.0
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "total_validations": 100,
                "successful_validations": 85,
                "failed_validations": 15,
                "common_errors": [
                    {
                        "code": "INVALID_DISTRICT",
                        "count": 8,
                        "percentage": 53.3
                    }
                ],
                "success_rate": 85.0
            }
        }


class FieldValidationRule(BaseModel):
    """Validation rule for a specific field."""
    
    field_name: str = Field(..., description="Name of the field")
    required: bool = Field(default=False, description="Whether field is required")
    data_type: str = Field(..., description="Expected data type")
    min_length: Optional[int] = Field(None, description="Minimum length for strings/arrays")
    max_length: Optional[int] = Field(None, description="Maximum length for strings/arrays")
    pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    allowed_values: Optional[List[str]] = Field(None, description="List of allowed values")
    custom_validator: Optional[str] = Field(None, description="Custom validator function name")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "field_name": "districts",
                "required": True,
                "data_type": "array",
                "min_length": 1,
                "max_length": 20,
                "custom_validator": "validate_hong_kong_districts"
            }
        }


class ValidationRuleSet(BaseModel):
    """Set of validation rules for a request type."""
    
    request_type: str = Field(..., description="Type of request these rules apply to")
    rules: List[FieldValidationRule] = Field(..., description="List of field validation rules")
    description: str = Field(..., description="Description of the validation rule set")
    version: str = Field(..., description="Version of the rule set")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "request_type": "DistrictSearchRequest",
                "rules": [
                    {
                        "field_name": "districts",
                        "required": True,
                        "data_type": "array",
                        "min_length": 1,
                        "max_length": 20
                    }
                ],
                "description": "Validation rules for district search requests",
                "version": "1.0.0"
            }
        }