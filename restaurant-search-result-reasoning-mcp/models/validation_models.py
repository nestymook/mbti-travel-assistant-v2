"""
Validation and configuration data models for reasoning MCP server.

This module contains models for data validation results, error handling,
and configuration management for the restaurant reasoning system.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ValidationErrorType(Enum):
    """Types of validation errors that can occur."""
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    EMPTY_DATA = "empty_data"
    STRUCTURE_ERROR = "structure_error"


@dataclass
class ValidationError:
    """
    Individual validation error for a specific field or restaurant.
    
    Contains detailed information about validation failures
    for debugging and error reporting.
    """
    restaurant_id: str
    field: str
    error_type: ValidationErrorType
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation error to dictionary."""
        result = {
            "restaurant_id": self.restaurant_id,
            "field": self.field,
            "error_type": self.error_type.value,
            "message": self.message
        }
        
        if self.expected_value is not None:
            result["expected_value"] = self.expected_value
            
        if self.actual_value is not None:
            result["actual_value"] = self.actual_value
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationError":
        """Create ValidationError instance from dictionary."""
        return cls(
            restaurant_id=data["restaurant_id"],
            field=data["field"],
            error_type=ValidationErrorType(data["error_type"]),
            message=data["message"],
            expected_value=data.get("expected_value"),
            actual_value=data.get("actual_value")
        )


@dataclass
class ValidationResult:
    """
    Result of data validation with errors and warnings.
    
    Contains validation status and detailed error information
    for restaurant data validation.
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    valid_count: int = 0
    total_count: int = 0
    
    def add_error(self, error: ValidationError) -> None:
        """Add a validation error to the result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning to the result."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if validation result has any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation result has any warnings."""
        return len(self.warnings) > 0
    
    def error_summary(self) -> Dict[str, int]:
        """Get summary of error types and counts."""
        summary = {}
        for error in self.errors:
            error_type = error.error_type.value
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": self.warnings,
            "valid_count": self.valid_count,
            "total_count": self.total_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "error_summary": self.error_summary()
        }
    
    def to_json(self) -> str:
        """Convert validation result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        """Create ValidationResult instance from dictionary."""
        errors = [ValidationError.from_dict(e) for e in data.get("errors", [])]
        
        return cls(
            is_valid=data["is_valid"],
            errors=errors,
            warnings=data.get("warnings", []),
            valid_count=data.get("valid_count", 0),
            total_count=data.get("total_count", 0)
        )


@dataclass
class ReasoningConfig:
    """
    Configuration settings for restaurant reasoning operations.
    
    Contains default parameters and settings for sentiment analysis
    and recommendation algorithms.
    """
    default_ranking_method: str = "sentiment_likes"
    candidate_count: int = 20
    minimum_sentiment_responses: int = 1
    enable_random_seed: bool = False
    random_seed: Optional[int] = None
    max_restaurants_per_request: int = 1000
    enable_validation_warnings: bool = True
    strict_validation: bool = False
    
    def validate(self) -> ValidationResult:
        """Validate configuration settings."""
        result = ValidationResult(is_valid=True)
        
        # Validate ranking method
        valid_methods = ["sentiment_likes", "combined_sentiment"]
        if self.default_ranking_method not in valid_methods:
            error = ValidationError(
                restaurant_id="config",
                field="default_ranking_method",
                error_type=ValidationErrorType.INVALID_VALUE,
                message=f"Invalid ranking method: {self.default_ranking_method}",
                expected_value=f"One of: {valid_methods}",
                actual_value=self.default_ranking_method
            )
            result.add_error(error)
        
        # Validate candidate count
        if self.candidate_count <= 0:
            error = ValidationError(
                restaurant_id="config",
                field="candidate_count",
                error_type=ValidationErrorType.INVALID_VALUE,
                message="Candidate count must be positive",
                expected_value="> 0",
                actual_value=str(self.candidate_count)
            )
            result.add_error(error)
        
        # Validate minimum sentiment responses
        if self.minimum_sentiment_responses < 0:
            error = ValidationError(
                restaurant_id="config",
                field="minimum_sentiment_responses",
                error_type=ValidationErrorType.INVALID_VALUE,
                message="Minimum sentiment responses cannot be negative",
                expected_value=">= 0",
                actual_value=str(self.minimum_sentiment_responses)
            )
            result.add_error(error)
        
        # Validate max restaurants per request
        if self.max_restaurants_per_request <= 0:
            error = ValidationError(
                restaurant_id="config",
                field="max_restaurants_per_request",
                error_type=ValidationErrorType.INVALID_VALUE,
                message="Max restaurants per request must be positive",
                expected_value="> 0",
                actual_value=str(self.max_restaurants_per_request)
            )
            result.add_error(error)
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "default_ranking_method": self.default_ranking_method,
            "candidate_count": self.candidate_count,
            "minimum_sentiment_responses": self.minimum_sentiment_responses,
            "enable_random_seed": self.enable_random_seed,
            "random_seed": self.random_seed,
            "max_restaurants_per_request": self.max_restaurants_per_request,
            "enable_validation_warnings": self.enable_validation_warnings,
            "strict_validation": self.strict_validation
        }
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningConfig":
        """Create ReasoningConfig instance from dictionary."""
        return cls(
            default_ranking_method=data.get("default_ranking_method", "sentiment_likes"),
            candidate_count=data.get("candidate_count", 20),
            minimum_sentiment_responses=data.get("minimum_sentiment_responses", 1),
            enable_random_seed=data.get("enable_random_seed", False),
            random_seed=data.get("random_seed"),
            max_restaurants_per_request=data.get("max_restaurants_per_request", 1000),
            enable_validation_warnings=data.get("enable_validation_warnings", True),
            strict_validation=data.get("strict_validation", False)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "ReasoningConfig":
        """Create ReasoningConfig instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class MCPServerConfig:
    """
    Configuration settings for the MCP server.
    
    Contains server-specific settings for FastMCP server operation.
    """
    host: str = "0.0.0.0"
    port: int = 8080
    stateless_http: bool = True
    enable_cors: bool = True
    max_request_size: int = 10485760  # 10MB
    request_timeout: int = 30  # seconds
    enable_debug: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert MCP server config to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "stateless_http": self.stateless_http,
            "enable_cors": self.enable_cors,
            "max_request_size": self.max_request_size,
            "request_timeout": self.request_timeout,
            "enable_debug": self.enable_debug
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create MCPServerConfig instance from dictionary."""
        return cls(
            host=data.get("host", "0.0.0.0"),
            port=data.get("port", 8080),
            stateless_http=data.get("stateless_http", True),
            enable_cors=data.get("enable_cors", True),
            max_request_size=data.get("max_request_size", 10485760),
            request_timeout=data.get("request_timeout", 30),
            enable_debug=data.get("enable_debug", False)
        )