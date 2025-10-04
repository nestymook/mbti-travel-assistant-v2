"""
Error models for the AgentCore Gateway MCP Tools service.

This module defines Pydantic models for structured error responses
with proper HTTP status code mapping and detailed error information.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_serializer


class ErrorType(str, Enum):
    """Enumeration of error types for categorization."""
    
    VALIDATION_ERROR = "ValidationError"
    AUTHENTICATION_ERROR = "AuthenticationError"
    AUTHORIZATION_ERROR = "AuthorizationError"
    MCP_SERVER_ERROR = "MCPServerError"
    RATE_LIMIT_ERROR = "RateLimitError"
    INTERNAL_ERROR = "InternalError"
    SERVICE_UNAVAILABLE = "ServiceUnavailableError"
    TIMEOUT_ERROR = "TimeoutError"


class ErrorDetail(BaseModel):
    """Detailed error information for specific fields or operations."""
    
    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    value: Optional[Any] = Field(None, description="Invalid value that caused the error")
    suggestion: Optional[str] = Field(None, description="Suggested correction")


class ValidationErrorDetail(BaseModel):
    """Validation-specific error details with field information."""
    
    field: str = Field(..., description="Field name with validation error")
    message: str = Field(..., description="Validation error message")
    invalid_value: Optional[Any] = Field(None, description="The invalid value provided")
    valid_values: Optional[List[Any]] = Field(None, description="List of valid values")
    constraint: Optional[str] = Field(None, description="Validation constraint that failed")
    suggestion: Optional[str] = Field(None, description="Suggested correction")


class MCPServerErrorDetail(BaseModel):
    """MCP server-specific error details with retry guidance."""
    
    server_name: str = Field(..., description="Name of the MCP server that failed")
    server_endpoint: str = Field(..., description="MCP server endpoint URL")
    error_message: str = Field(..., description="Error message from MCP server")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
    max_retries: Optional[int] = Field(None, description="Maximum retry attempts")
    current_attempt: Optional[int] = Field(None, description="Current retry attempt number")
    health_check_url: Optional[str] = Field(None, description="Health check endpoint")


class AuthenticationErrorDetail(BaseModel):
    """Authentication-specific error details with clear requirements."""
    
    auth_type: str = Field(..., description="Required authentication type (JWT, Bearer)")
    discovery_url: Optional[str] = Field(None, description="OIDC discovery URL")
    token_endpoint: Optional[str] = Field(None, description="Token endpoint URL")
    required_scopes: Optional[List[str]] = Field(None, description="Required OAuth scopes")
    token_format: Optional[str] = Field(None, description="Expected token format")
    example_header: Optional[str] = Field(None, description="Example Authorization header")


class RateLimitErrorDetail(BaseModel):
    """Rate limiting error details with retry information."""
    
    limit: int = Field(..., description="Rate limit threshold")
    window: int = Field(..., description="Rate limit window in seconds")
    retry_after: int = Field(..., description="Seconds until rate limit resets")
    current_usage: Optional[int] = Field(None, description="Current usage count")


class ErrorResponse(BaseModel):
    """Standard error response model for all API errors."""
    
    success: bool = Field(False, description="Always false for error responses")
    error: "ErrorInfo" = Field(..., description="Error information")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat() + "Z"


class ErrorInfo(BaseModel):
    """Core error information with type and details."""
    
    type: ErrorType = Field(..., description="Error type for categorization")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Union[
        ValidationErrorDetail,
        MCPServerErrorDetail,
        AuthenticationErrorDetail,
        RateLimitErrorDetail,
        Dict[str, Any]
    ]] = Field(None, description="Type-specific error details")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID")


class ValidationErrorResponse(ErrorResponse):
    """Specialized error response for validation errors."""
    
    error: "ValidationErrorInfo" = Field(..., description="Validation error information")


class ValidationErrorInfo(ErrorInfo):
    """Validation-specific error information."""
    
    type: ErrorType = Field(ErrorType.VALIDATION_ERROR, description="Always ValidationError")
    field_errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="List of field-specific validation errors"
    )
    invalid_fields: List[str] = Field(
        default_factory=list,
        description="List of field names with errors"
    )


class MCPServerErrorResponse(ErrorResponse):
    """Specialized error response for MCP server errors."""
    
    error: "MCPServerErrorInfo" = Field(..., description="MCP server error information")


class MCPServerErrorInfo(ErrorInfo):
    """MCP server-specific error information."""
    
    type: ErrorType = Field(ErrorType.MCP_SERVER_ERROR, description="Always MCPServerError")
    server_details: MCPServerErrorDetail = Field(..., description="MCP server error details")
    retry_guidance: Optional[str] = Field(None, description="Guidance for retry attempts")


class AuthenticationErrorResponse(ErrorResponse):
    """Specialized error response for authentication errors."""
    
    error: "AuthenticationErrorInfo" = Field(..., description="Authentication error information")


class AuthenticationErrorInfo(ErrorInfo):
    """Authentication-specific error information."""
    
    type: ErrorType = Field(ErrorType.AUTHENTICATION_ERROR, description="Always AuthenticationError")
    auth_details: AuthenticationErrorDetail = Field(..., description="Authentication requirements")
    help_url: Optional[str] = Field(None, description="URL for authentication help")


class RateLimitErrorResponse(ErrorResponse):
    """Specialized error response for rate limiting errors."""
    
    error: "RateLimitErrorInfo" = Field(..., description="Rate limit error information")


class RateLimitErrorInfo(ErrorInfo):
    """Rate limiting-specific error information."""
    
    type: ErrorType = Field(ErrorType.RATE_LIMIT_ERROR, description="Always RateLimitError")
    rate_limit_details: RateLimitErrorDetail = Field(..., description="Rate limit details")


# Update forward references
ErrorResponse.model_rebuild()
ValidationErrorResponse.model_rebuild()
MCPServerErrorResponse.model_rebuild()
AuthenticationErrorResponse.model_rebuild()
RateLimitErrorResponse.model_rebuild()