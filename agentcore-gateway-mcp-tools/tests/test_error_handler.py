"""
Unit tests for error handler middleware in the AgentCore Gateway MCP Tools service.

Tests the comprehensive error handling middleware and custom exceptions.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.responses import JSONResponse

from middleware.error_handler import (
    AuthenticationException,
    ErrorHandlerMiddleware,
    MCPServerException,
    RateLimitException,
    create_authentication_error,
    create_mcp_server_error,
    create_rate_limit_error,
)
from models.error_models import ErrorType


class TestCustomExceptions:
    """Test cases for custom exception classes."""
    
    def test_mcp_server_exception(self):
        """Test MCPServerException creation and attributes."""
        exc = MCPServerException(
            message="Connection failed",
            server_name="test-server",
            server_endpoint="http://test:8080",
            retry_after=30,
            max_retries=3,
            current_attempt=1,
            health_check_url="http://test:8080/health",
        )
        
        assert str(exc) == "Connection failed"
        assert exc.server_name == "test-server"
        assert exc.server_endpoint == "http://test:8080"
        assert exc.retry_after == 30
        assert exc.max_retries == 3
        assert exc.current_attempt == 1
        assert exc.health_check_url == "http://test:8080/health"
    
    def test_authentication_exception(self):
        """Test AuthenticationException creation and attributes."""
        exc = AuthenticationException(
            message="Token invalid",
            auth_type="JWT",
            discovery_url="https://example.com/.well-known/openid-configuration",
            required_scopes=["read", "write"],
            token_format="Bearer <token>",
            example_header="Authorization: Bearer token",
            help_url="https://docs.example.com",
        )
        
        assert str(exc) == "Token invalid"
        assert exc.auth_type == "JWT"
        assert "example.com" in exc.discovery_url
        assert exc.required_scopes == ["read", "write"]
        assert exc.token_format == "Bearer <token>"
        assert "Authorization: Bearer" in exc.example_header
        assert "docs.example.com" in exc.help_url
    
    def test_rate_limit_exception(self):
        """Test RateLimitException creation and attributes."""
        exc = RateLimitException(
            message="Rate limit exceeded",
            limit=100,
            window=3600,
            retry_after=1800,
            current_usage=105,
        )
        
        assert str(exc) == "Rate limit exceeded"
        assert exc.limit == 100
        assert exc.window == 3600
        assert exc.retry_after == 1800
        assert exc.current_usage == 105


class TestErrorHandlerMiddleware:
    """Test cases for ErrorHandlerMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create ErrorHandlerMiddleware instance for testing."""
        app = MagicMock()
        return ErrorHandlerMiddleware(app, include_trace_id=True, log_errors=True)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = "http://test.com/api/v1/restaurants/search"
        request.state = MagicMock()
        return request
    
    @pytest.mark.asyncio
    async def test_successful_request_passthrough(self, middleware, mock_request):
        """Test that successful requests pass through without modification."""
        mock_response = MagicMock()
        
        async def mock_call_next(request):
            return mock_response
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
        assert hasattr(mock_request.state, 'trace_id')
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, middleware, mock_request):
        """Test handling of RequestValidationError."""
        validation_error = RequestValidationError([
            {
                "loc": ("body", "districts"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": None,
            },
            {
                "loc": ("body", "meal_types"),
                "msg": "invalid choice",
                "type": "value_error.enum",
                "input": "invalid_meal",
            },
        ])
        
        async def mock_call_next(request):
            raise validation_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["type"] == "ValidationError"
        assert len(content["error"]["field_errors"]) == 2
        assert "body.districts" in content["error"]["invalid_fields"]
        assert "body.meal_types" in content["error"]["invalid_fields"]
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, middleware, mock_request):
        """Test handling of AuthenticationException."""
        auth_error = AuthenticationException(
            message="Token expired",
            auth_type="JWT",
            discovery_url="https://example.com/.well-known/openid-configuration",
            required_scopes=["read:restaurants"],
        )
        
        async def mock_call_next(request):
            raise auth_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["type"] == "AuthenticationError"
        assert content["error"]["auth_details"]["auth_type"] == "JWT"
        assert "example.com" in content["error"]["auth_details"]["discovery_url"]
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_server_error_handling(self, middleware, mock_request):
        """Test handling of MCPServerException."""
        mcp_error = MCPServerException(
            message="Server unavailable",
            server_name="restaurant-search",
            server_endpoint="http://restaurant-search:8080",
            retry_after=30,
            max_retries=3,
            current_attempt=1,
        )
        
        async def mock_call_next(request):
            raise mcp_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.headers.get("Retry-After") == "30"
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["type"] == "MCPServerError"
        assert content["error"]["server_details"]["server_name"] == "restaurant-search"
        assert content["error"]["server_details"]["retry_after"] == 30
        assert "retry" in content["error"]["retry_guidance"].lower()
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, middleware, mock_request):
        """Test handling of RateLimitException."""
        rate_limit_error = RateLimitException(
            message="Too many requests",
            limit=100,
            window=3600,
            retry_after=1800,
            current_usage=105,
        )
        
        async def mock_call_next(request):
            raise rate_limit_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.headers.get("Retry-After") == "1800"
        assert response.headers.get("X-RateLimit-Limit") == "100"
        assert response.headers.get("X-RateLimit-Window") == "3600"
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["type"] == "RateLimitError"
        assert content["error"]["rate_limit_details"]["limit"] == 100
        assert content["error"]["rate_limit_details"]["current_usage"] == 105
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_exception_handling(self, middleware, mock_request):
        """Test handling of FastAPI HTTPException."""
        http_error = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
            headers={"X-Custom-Header": "test"},
        )
        
        async def mock_call_next(request):
            raise http_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.headers.get("X-Custom-Header") == "test"
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["message"] == "Resource not found"
        assert content["error"]["code"] == "HTTP_404"
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_internal_error_handling(self, middleware, mock_request):
        """Test handling of unexpected internal errors."""
        internal_error = ValueError("Unexpected error")
        
        async def mock_call_next(request):
            raise internal_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        content = json.loads(response.body)
        assert content["success"] is False
        assert content["error"]["type"] == "InternalError"
        assert content["error"]["message"] == "An unexpected error occurred"
        assert content["error"]["details"]["exception_type"] == "ValueError"
        
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trace_id_generation(self, middleware, mock_request):
        """Test that trace IDs are generated and included in responses."""
        test_error = ValueError("Test error")
        
        async def mock_call_next(request):
            raise test_error
        
        with patch('middleware.error_handler.logger'):
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        content = json.loads(response.body)
        assert "request_id" in content
        assert content["request_id"] is not None
        assert content["error"]["trace_id"] is not None
        assert hasattr(mock_request.state, 'trace_id')
    
    @pytest.mark.asyncio
    async def test_no_trace_id_when_disabled(self, mock_request):
        """Test that trace IDs are not generated when disabled."""
        app = MagicMock()
        middleware = ErrorHandlerMiddleware(app, include_trace_id=False)
        
        test_error = ValueError("Test error")
        
        async def mock_call_next(request):
            raise test_error
        
        with patch('middleware.error_handler.logger'):
            response = await middleware.dispatch(mock_request, mock_call_next)
        
        content = json.loads(response.body)
        assert content["request_id"] is None
        assert content["error"]["trace_id"] is None
    
    @pytest.mark.asyncio
    async def test_logging_disabled(self, mock_request):
        """Test that logging can be disabled."""
        app = MagicMock()
        middleware = ErrorHandlerMiddleware(app, log_errors=False)
        
        test_error = ValueError("Test error")
        
        async def mock_call_next(request):
            raise test_error
        
        with patch('middleware.error_handler.logger') as mock_logger:
            await middleware.dispatch(mock_request, mock_call_next)
        
        mock_logger.error.assert_not_called()
    
    def test_generate_validation_suggestion(self, middleware):
        """Test validation suggestion generation."""
        
        # Test district-specific suggestion
        error = {"loc": ("body", "districts"), "type": "value_error.enum"}
        suggestion = middleware._generate_validation_suggestion("enum", error)
        assert "Hong Kong district" in suggestion
        
        # Test meal type-specific suggestion
        error = {"loc": ("body", "meal_types"), "type": "value_error.enum"}
        suggestion = middleware._generate_validation_suggestion("enum", error)
        assert "breakfast" in suggestion and "lunch" in suggestion
        
        # Test generic suggestion
        error = {"loc": ("body", "other_field"), "type": "missing"}
        suggestion = middleware._generate_validation_suggestion("missing", error)
        assert "required" in suggestion.lower()
    
    def test_generate_retry_guidance(self, middleware):
        """Test retry guidance generation for MCP errors."""
        
        # Test with all parameters
        exc = MCPServerException(
            message="Test error",
            server_name="test",
            server_endpoint="http://test:8080",
            retry_after=30,
            max_retries=3,
            current_attempt=1,
            health_check_url="http://test:8080/health",
        )
        
        guidance = middleware._generate_retry_guidance(exc)
        assert "30 seconds" in guidance
        assert "2 retry attempts remaining" in guidance
        assert "http://test:8080/health" in guidance
        
        # Test with no parameters
        exc = MCPServerException(
            message="Test error",
            server_name="test",
            server_endpoint="http://test:8080",
        )
        
        guidance = middleware._generate_retry_guidance(exc)
        assert "temporarily unavailable" in guidance.lower()
    
    def test_map_status_to_error_type(self, middleware):
        """Test HTTP status code to error type mapping."""
        
        assert middleware._map_status_to_error_type(400) == ErrorType.VALIDATION_ERROR
        assert middleware._map_status_to_error_type(401) == ErrorType.AUTHENTICATION_ERROR
        assert middleware._map_status_to_error_type(403) == ErrorType.AUTHORIZATION_ERROR
        assert middleware._map_status_to_error_type(408) == ErrorType.TIMEOUT_ERROR
        assert middleware._map_status_to_error_type(429) == ErrorType.RATE_LIMIT_ERROR
        assert middleware._map_status_to_error_type(503) == ErrorType.SERVICE_UNAVAILABLE
        assert middleware._map_status_to_error_type(999) == ErrorType.INTERNAL_ERROR


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_create_authentication_error(self):
        """Test create_authentication_error utility function."""
        error = create_authentication_error(
            message="Token invalid",
            discovery_url="https://example.com/.well-known/openid-configuration",
            required_scopes=["read", "write"],
        )
        
        assert isinstance(error, AuthenticationException)
        assert str(error) == "Token invalid"
        assert error.auth_type == "JWT"
        assert "example.com" in error.discovery_url
        assert error.required_scopes == ["read", "write"]
        assert "Bearer" in error.token_format
        assert "docs.aws.amazon.com" in error.help_url
    
    def test_create_mcp_server_error(self):
        """Test create_mcp_server_error utility function."""
        error = create_mcp_server_error(
            server_name="test-server",
            server_endpoint="http://test:8080",
            error_message="Connection failed",
            retry_after=60,
            max_retries=5,
            current_attempt=2,
        )
        
        assert isinstance(error, MCPServerException)
        assert str(error) == "Connection failed"
        assert error.server_name == "test-server"
        assert error.server_endpoint == "http://test:8080"
        assert error.retry_after == 60
        assert error.max_retries == 5
        assert error.current_attempt == 2
        assert error.health_check_url == "http://test:8080/health"
    
    def test_create_rate_limit_error(self):
        """Test create_rate_limit_error utility function."""
        error = create_rate_limit_error(
            limit=100,
            window=3600,
            retry_after=1800,
            current_usage=105,
        )
        
        assert isinstance(error, RateLimitException)
        assert "105/100" in str(error)
        assert error.limit == 100
        assert error.window == 3600
        assert error.retry_after == 1800
        assert error.current_usage == 105