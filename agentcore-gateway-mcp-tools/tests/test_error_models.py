"""
Unit tests for error models in the AgentCore Gateway MCP Tools service.

Tests the Pydantic models used for structured error responses.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.error_models import (
    AuthenticationErrorDetail,
    AuthenticationErrorInfo,
    AuthenticationErrorResponse,
    ErrorInfo,
    ErrorResponse,
    ErrorType,
    MCPServerErrorDetail,
    MCPServerErrorInfo,
    MCPServerErrorResponse,
    RateLimitErrorDetail,
    RateLimitErrorInfo,
    RateLimitErrorResponse,
    ValidationErrorDetail,
    ValidationErrorInfo,
    ValidationErrorResponse,
)


class TestErrorModels:
    """Test cases for error model validation and serialization."""
    
    def test_error_type_enum(self):
        """Test ErrorType enum values."""
        assert ErrorType.VALIDATION_ERROR == "ValidationError"
        assert ErrorType.AUTHENTICATION_ERROR == "AuthenticationError"
        assert ErrorType.MCP_SERVER_ERROR == "MCPServerError"
        assert ErrorType.RATE_LIMIT_ERROR == "RateLimitError"
        assert ErrorType.INTERNAL_ERROR == "InternalError"
    
    def test_validation_error_detail(self):
        """Test ValidationErrorDetail model."""
        detail = ValidationErrorDetail(
            field="districts",
            message="Invalid district name",
            invalid_value="Invalid District",
            valid_values=["Central district", "Admiralty"],
            constraint="enum",
            suggestion="Please use a valid Hong Kong district name",
        )
        
        assert detail.field == "districts"
        assert detail.message == "Invalid district name"
        assert detail.invalid_value == "Invalid District"
        assert "Central district" in detail.valid_values
        assert detail.constraint == "enum"
        assert "valid Hong Kong district" in detail.suggestion
    
    def test_mcp_server_error_detail(self):
        """Test MCPServerErrorDetail model."""
        detail = MCPServerErrorDetail(
            server_name="restaurant-search",
            server_endpoint="http://restaurant-search:8080",
            error_message="Connection refused",
            retry_after=30,
            max_retries=3,
            current_attempt=1,
            health_check_url="http://restaurant-search:8080/health",
        )
        
        assert detail.server_name == "restaurant-search"
        assert detail.server_endpoint == "http://restaurant-search:8080"
        assert detail.error_message == "Connection refused"
        assert detail.retry_after == 30
        assert detail.max_retries == 3
        assert detail.current_attempt == 1
        assert detail.health_check_url == "http://restaurant-search:8080/health"
    
    def test_authentication_error_detail(self):
        """Test AuthenticationErrorDetail model."""
        detail = AuthenticationErrorDetail(
            auth_type="JWT",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/.well-known/openid-configuration",
            token_endpoint="https://cognito-idp.us-east-1.amazonaws.com/oauth2/token",
            required_scopes=["read:restaurants", "write:recommendations"],
            token_format="Bearer <JWT_TOKEN>",
            example_header="Authorization: Bearer eyJhbGciOiJSUzI1NiIs...",
        )
        
        assert detail.auth_type == "JWT"
        assert "cognito-idp" in detail.discovery_url
        assert "oauth2/token" in detail.token_endpoint
        assert "read:restaurants" in detail.required_scopes
        assert detail.token_format == "Bearer <JWT_TOKEN>"
        assert "Authorization: Bearer" in detail.example_header
    
    def test_rate_limit_error_detail(self):
        """Test RateLimitErrorDetail model."""
        detail = RateLimitErrorDetail(
            limit=100,
            window=3600,
            retry_after=1800,
            current_usage=105,
        )
        
        assert detail.limit == 100
        assert detail.window == 3600
        assert detail.retry_after == 1800
        assert detail.current_usage == 105
    
    def test_error_info_basic(self):
        """Test basic ErrorInfo model."""
        error_info = ErrorInfo(
            type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            code="VALIDATION_FAILED",
            trace_id="test-trace-123",
        )
        
        assert error_info.type == ErrorType.VALIDATION_ERROR
        assert error_info.message == "Validation failed"
        assert error_info.code == "VALIDATION_FAILED"
        assert error_info.trace_id == "test-trace-123"
    
    def test_error_response_basic(self):
        """Test basic ErrorResponse model."""
        error_info = ErrorInfo(
            type=ErrorType.INTERNAL_ERROR,
            message="Internal server error",
            code="INTERNAL_ERROR",
        )
        
        error_response = ErrorResponse(
            error=error_info,
            request_id="req-123",
        )
        
        assert error_response.success is False
        assert error_response.error.type == ErrorType.INTERNAL_ERROR
        assert error_response.request_id == "req-123"
        assert isinstance(error_response.timestamp, datetime)
    
    def test_validation_error_response(self):
        """Test ValidationErrorResponse model."""
        field_errors = [
            ValidationErrorDetail(
                field="districts",
                message="Invalid district",
                invalid_value="Bad District",
                suggestion="Use valid district names",
            ),
            ValidationErrorDetail(
                field="meal_types",
                message="Invalid meal type",
                invalid_value="snack",
                valid_values=["breakfast", "lunch", "dinner"],
                suggestion="Use breakfast, lunch, or dinner",
            ),
        ]
        
        error_info = ValidationErrorInfo(
            message="Request validation failed",
            code="VALIDATION_FAILED",
            field_errors=field_errors,
            invalid_fields=["districts", "meal_types"],
            trace_id="trace-456",
        )
        
        error_response = ValidationErrorResponse(
            error=error_info,
            request_id="req-456",
        )
        
        assert error_response.error.type == ErrorType.VALIDATION_ERROR
        assert len(error_response.error.field_errors) == 2
        assert "districts" in error_response.error.invalid_fields
        assert "meal_types" in error_response.error.invalid_fields
        assert error_response.error.trace_id == "trace-456"
    
    def test_mcp_server_error_response(self):
        """Test MCPServerErrorResponse model."""
        server_details = MCPServerErrorDetail(
            server_name="restaurant-reasoning",
            server_endpoint="http://restaurant-reasoning:8080",
            error_message="Service unavailable",
            retry_after=60,
            max_retries=3,
            current_attempt=2,
        )
        
        error_info = MCPServerErrorInfo(
            message="MCP server unavailable",
            code="MCP_SERVER_UNAVAILABLE",
            server_details=server_details,
            retry_guidance="Wait 60 seconds before retrying",
            trace_id="trace-789",
        )
        
        error_response = MCPServerErrorResponse(
            error=error_info,
            request_id="req-789",
        )
        
        assert error_response.error.type == ErrorType.MCP_SERVER_ERROR
        assert error_response.error.server_details.server_name == "restaurant-reasoning"
        assert error_response.error.server_details.retry_after == 60
        assert "60 seconds" in error_response.error.retry_guidance
    
    def test_authentication_error_response(self):
        """Test AuthenticationErrorResponse model."""
        auth_details = AuthenticationErrorDetail(
            auth_type="JWT",
            discovery_url="https://example.com/.well-known/openid-configuration",
            token_format="Bearer <JWT_TOKEN>",
            example_header="Authorization: Bearer token",
        )
        
        error_info = AuthenticationErrorInfo(
            message="Authentication required",
            code="AUTHENTICATION_REQUIRED",
            auth_details=auth_details,
            help_url="https://docs.example.com/auth",
            trace_id="trace-auth",
        )
        
        error_response = AuthenticationErrorResponse(
            error=error_info,
            request_id="req-auth",
        )
        
        assert error_response.error.type == ErrorType.AUTHENTICATION_ERROR
        assert error_response.error.auth_details.auth_type == "JWT"
        assert "docs.example.com" in error_response.error.help_url
    
    def test_rate_limit_error_response(self):
        """Test RateLimitErrorResponse model."""
        rate_limit_details = RateLimitErrorDetail(
            limit=50,
            window=300,
            retry_after=120,
            current_usage=55,
        )
        
        error_info = RateLimitErrorInfo(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            rate_limit_details=rate_limit_details,
            trace_id="trace-rate",
        )
        
        error_response = RateLimitErrorResponse(
            error=error_info,
            request_id="req-rate",
        )
        
        assert error_response.error.type == ErrorType.RATE_LIMIT_ERROR
        assert error_response.error.rate_limit_details.limit == 50
        assert error_response.error.rate_limit_details.current_usage == 55
    
    def test_error_response_serialization(self):
        """Test error response serialization to dict."""
        error_info = ErrorInfo(
            type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            code="TEST_ERROR",
        )
        
        error_response = ErrorResponse(
            error=error_info,
            request_id="test-req",
        )
        
        serialized = error_response.model_dump()
        
        assert serialized["success"] is False
        assert serialized["error"]["type"] == "ValidationError"
        assert serialized["error"]["message"] == "Test error"
        assert serialized["request_id"] == "test-req"
        assert "timestamp" in serialized
    
    def test_validation_error_detail_required_fields(self):
        """Test ValidationErrorDetail with only required fields."""
        detail = ValidationErrorDetail(
            field="test_field",
            message="Test message",
        )
        
        assert detail.field == "test_field"
        assert detail.message == "Test message"
        assert detail.invalid_value is None
        assert detail.valid_values is None
        assert detail.constraint is None
        assert detail.suggestion is None
    
    def test_mcp_server_error_detail_required_fields(self):
        """Test MCPServerErrorDetail with only required fields."""
        detail = MCPServerErrorDetail(
            server_name="test-server",
            server_endpoint="http://test:8080",
            error_message="Test error",
        )
        
        assert detail.server_name == "test-server"
        assert detail.server_endpoint == "http://test:8080"
        assert detail.error_message == "Test error"
        assert detail.retry_after is None
        assert detail.max_retries is None
        assert detail.current_attempt is None
        assert detail.health_check_url is None
    
    def test_error_info_with_details_dict(self):
        """Test ErrorInfo with details as dictionary."""
        error_info = ErrorInfo(
            type=ErrorType.INTERNAL_ERROR,
            message="Internal error",
            details={
                "exception_type": "ValueError",
                "exception_message": "Invalid value provided",
                "stack_trace": "Traceback...",
            },
        )
        
        assert error_info.details["exception_type"] == "ValueError"
        assert error_info.details["exception_message"] == "Invalid value provided"
        assert "stack_trace" in error_info.details
    
    def test_model_validation_errors(self):
        """Test that models properly validate required fields."""
        
        # Test ValidationErrorDetail missing required field
        with pytest.raises(ValidationError):
            ValidationErrorDetail(message="Missing field name")
        
        # Test MCPServerErrorDetail missing required fields
        with pytest.raises(ValidationError):
            MCPServerErrorDetail(server_name="test")
        
        # Test ErrorInfo missing required fields
        with pytest.raises(ValidationError):
            ErrorInfo(message="Missing type")
    
    def test_error_type_validation(self):
        """Test ErrorType enum validation in models."""
        
        # Valid error type
        error_info = ErrorInfo(
            type=ErrorType.AUTHENTICATION_ERROR,
            message="Auth error",
        )
        assert error_info.type == ErrorType.AUTHENTICATION_ERROR
        
        # Invalid error type should raise validation error
        with pytest.raises(ValidationError):
            ErrorInfo(
                type="InvalidErrorType",
                message="Invalid type",
            )