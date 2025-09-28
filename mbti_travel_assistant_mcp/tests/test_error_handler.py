"""
Comprehensive Unit Tests for Error Handler Service

Tests all aspects of error handling including error classification,
specific error type handling, and structured error response generation.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from services.error_handler import ErrorHandler, SystemErrorType
from services.mcp_client_manager import (
    MCPConnectionError, 
    MCPToolCallError, 
    MCPCircuitBreakerOpenError
)
from models.auth_models import AuthenticationError
from services.auth_service import AuthenticationError as AuthError


class TestErrorHandler:
    """Comprehensive test cases for ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        return ErrorHandler()
    
    @pytest.fixture
    def error_handler_with_debug(self):
        """Create error handler with debug info enabled."""
        handler = ErrorHandler()
        handler.include_debug_info = True
        return handler
    
    def test_init_default_config(self, error_handler):
        """Test error handler initialization with default config."""
        assert error_handler.include_debug_info is False
        assert error_handler.max_error_message_length == 500
    
    def test_classify_error_mcp_circuit_breaker(self, error_handler):
        """Test classification of MCP circuit breaker errors."""
        error = MCPCircuitBreakerOpenError("Circuit breaker open")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.MCP_CIRCUIT_BREAKER_ERROR
    
    def test_classify_error_mcp_connection(self, error_handler):
        """Test classification of MCP connection errors."""
        error = MCPConnectionError("Connection failed")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.MCP_CONNECTION_ERROR
    
    def test_classify_error_mcp_tool_call(self, error_handler):
        """Test classification of MCP tool call errors."""
        error = MCPToolCallError("Tool call failed")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.MCP_TOOL_ERROR
    
    def test_classify_error_authentication(self, error_handler):
        """Test classification of authentication errors."""
        auth_error = AuthenticationError.invalid_token("Invalid token")
        
        result = error_handler._classify_error(auth_error)
        
        assert result == SystemErrorType.AUTHENTICATION_ERROR
    
    def test_classify_error_authentication_by_message(self, error_handler):
        """Test classification of authentication errors by message content."""
        error = Exception("Authentication failed")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.AUTHENTICATION_ERROR
    
    def test_classify_error_authorization_by_message(self, error_handler):
        """Test classification of authorization errors by message content."""
        error = Exception("Authorization failed - forbidden")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.AUTHORIZATION_ERROR
    
    def test_classify_error_validation(self, error_handler):
        """Test classification of validation errors."""
        error = ValueError("Invalid input value")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.VALIDATION_ERROR
    
    def test_classify_error_timeout(self, error_handler):
        """Test classification of timeout errors."""
        error = TimeoutError("Request timeout")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.TIMEOUT_ERROR
    
    def test_classify_error_connection(self, error_handler):
        """Test classification of connection errors."""
        error = ConnectionError("Network connection failed")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.MCP_CONNECTION_ERROR
    
    def test_classify_error_parsing(self, error_handler):
        """Test classification of parsing errors."""
        error = Exception("JSON parse error")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.PARSING_ERROR
    
    def test_classify_error_rate_limit(self, error_handler):
        """Test classification of rate limit errors."""
        error = Exception("Rate limit exceeded - 429")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.RATE_LIMIT_ERROR
    
    def test_classify_error_configuration(self, error_handler):
        """Test classification of configuration errors."""
        error = Exception("Configuration setting invalid")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.CONFIGURATION_ERROR
    
    def test_classify_error_generic(self, error_handler):
        """Test classification of generic errors."""
        error = Exception("Unknown error occurred")
        
        result = error_handler._classify_error(error)
        
        assert result == SystemErrorType.INTERNAL_ERROR
    
    def test_get_log_level_for_error_warning_types(self, error_handler):
        """Test log level assignment for warning-level errors."""
        warning_types = [
            SystemErrorType.VALIDATION_ERROR,
            SystemErrorType.AUTHENTICATION_ERROR,
            SystemErrorType.AUTHORIZATION_ERROR,
            SystemErrorType.RATE_LIMIT_ERROR,
            SystemErrorType.MCP_CIRCUIT_BREAKER_ERROR
        ]
        
        for error_type in warning_types:
            level = error_handler._get_log_level_for_error(error_type)
            assert level == logging.WARNING
    
    def test_get_log_level_for_error_error_types(self, error_handler):
        """Test log level assignment for error-level errors."""
        error_types = [
            SystemErrorType.MCP_CONNECTION_ERROR,
            SystemErrorType.MCP_TOOL_ERROR,
            SystemErrorType.PARSING_ERROR,
            SystemErrorType.TIMEOUT_ERROR,
            SystemErrorType.INTERNAL_ERROR,
            SystemErrorType.CONFIGURATION_ERROR
        ]
        
        for error_type in error_types:
            level = error_handler._get_log_level_for_error(error_type)
            assert level == logging.ERROR
    
    def test_create_base_error_response(self, error_handler):
        """Test creating base error response structure."""
        result = error_handler._create_base_error_response(
            error_type="test_error",
            message="Test error message",
            suggested_actions=["Action 1", "Action 2"],
            correlation_id="test-123",
            additional_info={"extra": "info"}
        )
        
        assert result["recommendation"] is None
        assert result["candidates"] == []
        assert result["error"]["error_type"] == "test_error"
        assert result["error"]["message"] == "Test error message"
        assert result["error"]["suggested_actions"] == ["Action 1", "Action 2"]
        assert result["error"]["extra"] == "info"
        assert result["metadata"]["correlation_id"] == "test-123"
        assert result["metadata"]["error_handled"] is True
    
    def test_create_base_error_response_long_message(self, error_handler):
        """Test base error response with message truncation."""
        long_message = "A" * 600  # Exceeds max length
        
        result = error_handler._create_base_error_response(
            error_type="test_error",
            message=long_message,
            suggested_actions=["Try again"]
        )
        
        assert len(result["error"]["message"]) <= 500
        assert result["error"]["message"].endswith("...")
    
    def test_handle_validation_error_district(self, error_handler):
        """Test handling validation error with district-specific guidance."""
        error = ValueError("Invalid district name provided")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "validation_error"
        assert "Request validation failed" in result["error"]["message"]
        assert any("valid district name" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_validation_error_meal_time(self, error_handler):
        """Test handling validation error with meal_time-specific guidance."""
        error = ValueError("Invalid meal_time parameter")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "validation_error"
        assert any("meal_time" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_validation_error_generic(self, error_handler):
        """Test handling generic validation error."""
        error = ValueError("Generic validation error")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "validation_error"
        assert any("required parameters" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_error_expired(self, error_handler):
        """Test handling expired authentication token error."""
        error = AuthError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time has passed",
            suggested_action="Refresh token"
        )
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "expired" in result["error"]["message"].lower()
        assert any("new authentication token" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 0
    
    def test_handle_authentication_error_invalid(self, error_handler):
        """Test handling invalid authentication token error."""
        error = AuthError(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_TOKEN",
            message="Invalid JWT token",
            details="Token format is invalid",
            suggested_action="Provide valid token"
        )
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication failed" in result["error"]["message"]
        assert any("authentication credentials" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_error_generic(self, error_handler):
        """Test handling generic authentication error."""
        error = Exception("Authentication required")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication required" in result["error"]["message"]
        assert any("valid authentication token" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authorization_error(self, error_handler):
        """Test handling authorization error."""
        error = Exception("Access forbidden")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "authorization_error"
        assert "Access denied" in result["error"]["message"]
        assert any("permission" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 0
    
    def test_handle_mcp_connection_error(self, error_handler):
        """Test handling MCP connection error."""
        error = MCPConnectionError("Connection failed")
        error.server_name = "restaurant-search"
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "connection_error"
        assert "restaurant-search" in result["error"]["message"]
        assert any("Try again" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 30
        assert result["error"]["service_status"] == "degraded"
    
    def test_handle_mcp_connection_error_generic(self, error_handler):
        """Test handling generic MCP connection error."""
        error = ConnectionError("Network error")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "connection_error"
        assert "restaurant services" in result["error"]["message"]
    
    def test_handle_mcp_tool_error(self, error_handler):
        """Test handling MCP tool call error."""
        error = MCPToolCallError("Tool execution failed")
        error.tool_name = "search_restaurants"
        error.server_name = "restaurant-search"
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "service_error"
        assert "search_restaurants" in result["error"]["message"]
        assert "restaurant-search" in result["error"]["message"]
        assert any("different search criteria" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 10
    
    def test_handle_mcp_tool_error_generic(self, error_handler):
        """Test handling generic MCP tool error."""
        error = Exception("Tool call failed")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "service_error"
        assert "Restaurant service error" in result["error"]["message"]
    
    def test_handle_mcp_circuit_breaker_error(self, error_handler):
        """Test handling MCP circuit breaker error."""
        error = MCPCircuitBreakerOpenError("Circuit breaker open")
        error.server_name = "restaurant-reasoning"
        error.recovery_time = datetime.now()
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "service_unavailable"
        assert "restaurant-reasoning" in result["error"]["message"]
        assert "temporarily unavailable" in result["error"]["message"]
        assert any("Try again" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["service_status"] == "unavailable"
    
    def test_handle_mcp_circuit_breaker_error_generic(self, error_handler):
        """Test handling generic circuit breaker error."""
        error = Exception("Service unavailable")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "service_unavailable"
        assert result["error"]["retry_after"] == 60
    
    def test_handle_parsing_error(self, error_handler):
        """Test handling parsing error."""
        error = Exception("JSON decode error")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "parsing_error"
        assert "Error processing restaurant data" in result["error"]["message"]
        assert any("simpler request" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 5
    
    def test_handle_timeout_error(self, error_handler):
        """Test handling timeout error."""
        error = TimeoutError("Request timeout")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "timeout_error"
        assert "Request timed out" in result["error"]["message"]
        assert any("simpler search" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 15
        assert result["error"]["timeout_duration"] == "30s"
    
    def test_handle_rate_limit_error(self, error_handler):
        """Test handling rate limit error."""
        error = Exception("Rate limit exceeded")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "rate_limit_error"
        assert "Too many requests" in result["error"]["message"]
        assert any("Wait before" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 60
    
    def test_handle_configuration_error(self, error_handler):
        """Test handling configuration error."""
        error = Exception("Invalid configuration setting")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "configuration_error"
        assert "Service configuration error" in result["error"]["message"]
        assert any("Contact support" in action for action in result["error"]["suggested_actions"])
        assert result["error"]["retry_after"] == 300
    
    def test_handle_generic_error_memory(self, error_handler):
        """Test handling generic memory error."""
        error = Exception("Out of memory error")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "internal_error"
        assert "System temporarily overloaded" in result["error"]["message"]
    
    def test_handle_generic_error_disk(self, error_handler):
        """Test handling generic disk error."""
        error = Exception("Disk space full")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "internal_error"
        assert "System storage temporarily unavailable" in result["error"]["message"]
    
    def test_handle_generic_error_network(self, error_handler):
        """Test handling generic network error."""
        error = Exception("Network connectivity issue")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "internal_error"
        assert "Network connectivity issue" in result["error"]["message"]
    
    def test_handle_generic_error_unknown(self, error_handler):
        """Test handling unknown generic error."""
        error = Exception("Unknown error")
        
        result = error_handler.handle_error(error, "test-123")
        
        assert result["error"]["error_type"] == "internal_error"
        assert "An unexpected error occurred" in result["error"]["message"]
        assert any("correlation ID: test-123" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_error_with_debug_info(self, error_handler_with_debug):
        """Test error handling with debug info enabled."""
        error = ValueError("Test validation error")
        request_context = {"path": "/api/test", "method": "POST"}
        
        result = error_handler_with_debug.handle_error(
            error, 
            "test-123", 
            request_context
        )
        
        assert result["error"]["request_context"] == request_context
    
    def test_handle_error_without_debug_info(self, error_handler):
        """Test error handling with debug info disabled."""
        error = ValueError("Test validation error")
        request_context = {"path": "/api/test", "method": "POST"}
        
        result = error_handler.handle_error(
            error, 
            "test-123", 
            request_context
        )
        
        assert result["error"]["request_context"] is None
    
    def test_handle_malformed_payload_error(self, error_handler):
        """Test handling malformed payload error."""
        payload = {"invalid": "structure"}
        validation_errors = [
            "Missing required field: district",
            "Invalid meal_time format",
            "JSON structure invalid"
        ]
        
        result = error_handler.handle_malformed_payload_error(
            payload,
            validation_errors,
            "test-123"
        )
        
        assert result["error"]["error_type"] == "validation_error"
        assert "Request payload is malformed" in result["error"]["message"]
        assert result["error"]["validation_errors"] == validation_errors
        assert any("valid district name" in action for action in result["error"]["suggested_actions"])
        assert any("valid meal_time" in action for action in result["error"]["suggested_actions"])
        assert any("valid JSON format" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_failure_expired_token(self, error_handler):
        """Test handling authentication failure with expired token."""
        result = error_handler.handle_authentication_failure(
            "Token expired at 2024-01-01",
            "test-123"
        )
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication token has expired" in result["error"]["message"]
        assert any("new authentication token" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_failure_invalid_token(self, error_handler):
        """Test handling authentication failure with invalid token."""
        result = error_handler.handle_authentication_failure(
            "Token invalid format",
            "test-123"
        )
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication token is invalid" in result["error"]["message"]
        assert any("token format" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_failure_missing_token(self, error_handler):
        """Test handling authentication failure with missing token."""
        result = error_handler.handle_authentication_failure(
            "Missing authorization header",
            "test-123"
        )
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication token is missing" in result["error"]["message"]
        assert any("Authorization header" in action for action in result["error"]["suggested_actions"])
    
    def test_handle_authentication_failure_generic(self, error_handler):
        """Test handling generic authentication failure."""
        result = error_handler.handle_authentication_failure(
            "Unknown auth failure",
            "test-123"
        )
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "Authentication failed: Unknown auth failure" in result["error"]["message"]
    
    def test_handle_authentication_failure_with_headers(self, error_handler_with_debug):
        """Test authentication failure handling with request headers."""
        headers = {"Authorization": "Bearer token123", "User-Agent": "Test"}
        
        result = error_handler_with_debug.handle_authentication_failure(
            "Invalid token",
            "test-123",
            headers
        )
        
        assert result["error"]["has_auth_header"] is True
    
    def test_handle_error_logging(self, error_handler, caplog):
        """Test that errors are logged appropriately."""
        error = ValueError("Test validation error")
        
        with caplog.at_level(logging.WARNING):
            error_handler.handle_error(error, "test-123")
        
        assert "Handling validation_error" in caplog.text
        assert "test-123" in caplog.text
    
    def test_handle_error_with_request_context(self, error_handler):
        """Test error handling with request context."""
        error = Exception("Test error")
        context = {
            "path": "/api/restaurants",
            "method": "POST",
            "user_id": "user123"
        }
        
        result = error_handler.handle_error(error, "test-123", context)
        
        assert result["metadata"]["correlation_id"] == "test-123"
        assert result["error"]["error_type"] == "internal_error"


if __name__ == "__main__":
    pytest.main([__file__])