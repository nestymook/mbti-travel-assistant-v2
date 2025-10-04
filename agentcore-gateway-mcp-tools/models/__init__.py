"""
Models package for AgentCore Gateway MCP Tools.

This package contains all Pydantic models for request/response validation,
tool metadata, and error handling in the AgentCore Gateway.
"""

# Request models
from .request_models import (
    MealType,
    RankingMethod,
    DistrictSearchRequest,
    MealTypeSearchRequest,
    CombinedSearchRequest,
    RestaurantData,
    RestaurantRecommendationRequest,
    SentimentAnalysisRequest
)

# Response models
from .response_models import (
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

# Tool metadata models
from .tool_metadata_models import (
    ParameterType,
    ToolCategory,
    MBTIPersonalityType,
    ParameterSchema,
    ResponseSchema,
    UseCaseScenario,
    MBTIIntegrationGuidance,
    ToolExample,
    ToolMetadata,
    ToolsMetadataResponse
)

# Validation models
from .validation_models import (
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

__all__ = [
    # Request models
    "MealType",
    "RankingMethod",
    "DistrictSearchRequest",
    "MealTypeSearchRequest",
    "CombinedSearchRequest",
    "RestaurantData",
    "RestaurantRecommendationRequest",
    "SentimentAnalysisRequest",
    
    # Response models
    "ResponseStatus",
    "ErrorType",
    "SentimentData",
    "OperatingHours",
    "RestaurantMetadata",
    "RestaurantResponse",
    "FileMetadata",
    "SearchResultMetadata",
    "RestaurantSearchResponse",
    "AnalysisSummary",
    "RecommendationResponse",
    "SentimentAnalysisResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthCheckResponse",
    "MetricsResponse",
    
    # Tool metadata models
    "ParameterType",
    "ToolCategory",
    "MBTIPersonalityType",
    "ParameterSchema",
    "ResponseSchema",
    "UseCaseScenario",
    "MBTIIntegrationGuidance",
    "ToolExample",
    "ToolMetadata",
    "ToolsMetadataResponse",
    
    # Validation models
    "ValidationSeverity",
    "ValidationErrorCode",
    "ValidationIssue",
    "ValidationResult",
    "DistrictValidationResult",
    "MealTypeValidationResult",
    "SentimentValidationResult",
    "RequestValidationError",
    "ValidationSummary",
    "FieldValidationRule",
    "ValidationRuleSet"
]