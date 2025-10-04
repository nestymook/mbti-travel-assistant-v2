"""
Unit tests for error service in the AgentCore Gateway MCP Tools service.

Tests the error service utilities for handling and formatting errors.
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status
from pydantic import ValidationError

from middleware.error_handler import (
    AuthenticationException,
    MCPServerException,
    RateLimitException,
)
from services.error_service import ErrorService, error_service


class TestErrorService:
    """Test cases for ErrorService class."""
    
    @pytest.fixture
    def service(self):
        """Create ErrorService instance for testing."""
        return ErrorService()
    
    def test_handle_validation_error(self, service):
        """Test handling of Pydantic validation errors."""
        
        # Create a mock ValidationError
        validation_error = MagicMock(spec=ValidationError)
        validation_error.errors.return_value = [
            {
                "loc": ("districts",),
                "msg": "field required",
                "type": "value_error.missing",
                "input": None,
            },
            {
                "loc": ("meal_types", 0),
                "msg": "invalid choice",
                "type": "value_error.enum",
                "input": "invalid_meal",
            },
        ]
        
        with patch.object(service, 'logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                service.handle_validation_error(validation_error, "restaurant search")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Validation failed for restaurant search" in exc_info.value.detail["message"]
        assert len(exc_info.value.detail["errors"]) == 2
        
        mock_logger.warning.assert_called_once()
    
    def test_handle_mcp_connection_error(self, service):
        """Test handling of MCP server connection errors."""
        original_error = ConnectionError("Connection refused")
        
        with patch.object(service, 'logger') as mock_logger:
            result = service.handle_mcp_connection_error(
                server_name="restaurant-search",
                server_endpoint="http://restaurant-search:8080",
                original_error=original_error,
                retry_attempt=2,
                max_retries=3,
            )
        
        assert isinstance(result, MCPServerException)
        assert result.server_name == "restaurant-search"
        assert result.server_endpoint == "http://restaurant-search:8080"
        assert result.retry_after == 4  # 2^2 = 4 seconds
        assert result.max_retries == 3
        assert result.current_attempt == 2
        assert "Connection refused" in str(result)
        
        mock_logger.error.assert_called_once()
    
    def test_handle_mcp_tool_error(self, service):
        """Test handling of MCP tool execution errors."""
        original_error = ValueError("Invalid parameters")
        
        with patch.object(service, 'logger') as mock_logger:
            result = service.handle_mcp_tool_error(
                server_name="restaurant-reasoning",
                tool_name="recommend_restaurants",
                original_error=original_error,
                parameters={"restaurants": [], "ranking_method": "invalid"},
            )
        
        assert isinstance(result, MCPServerException)
        assert result.server_name == "restaurant-reasoning"
        assert "recommend_restaurants" in str(result)
        assert "Invalid parameters" in str(result)
        assert result.retry_after == 10
        assert result.max_retries == 2
        
        mock_logger.error.assert_called_once()
    
    def test_handle_authentication_error_missing_token(self, service):
        """Test handling of missing authentication token."""
        
        with patch.object(service, 'logger') as mock_logger:
            result = service.handle_authentication_error(
                error_type="missing_token",
                discovery_url="https://example.com/.well-known/openid-configuration",
            )
        
        assert isinstance(result, AuthenticationException)
        assert "Authentication token is required" in str(result)
        assert result.auth_type == "JWT"
        assert "example.com" in result.discovery_url
        
        mock_logger.warning.assert_called_once()
    
    def test_handle_authentication_error_insufficient_scope(self, service):
        """Test handling of insufficient scope authentication error."""
        
        with patch.object(service, 'logger') as mock_logger:
            result = service.handle_authentication_error(
                error_type="insufficient_scope",
                details={"required_scopes": ["read:restaurants", "write:recommendations"]},
            )
        
        assert isinstance(result, AuthenticationException)
        assert "Insufficient permissions" in str(result)
        assert result.required_scopes == ["read:restaurants", "write:recommendations"]
        
        mock_logger.warning.assert_called_once()
    
    def test_handle_rate_limit_error(self, service):
        """Test handling of rate limit errors."""
        
        with patch.object(service, 'logger') as mock_logger:
            result = service.handle_rate_limit_error(
                limit=100,
                window=3600,
                current_usage=105,
                user_id="user-123",
            )
        
        assert isinstance(result, RateLimitException)
        assert result.limit == 100
        assert result.window == 3600
        assert result.retry_after == 3600
        assert result.current_usage == 105
        assert "105/100" in str(result)
        
        mock_logger.warning.assert_called_once()
    
    def test_handle_timeout_error(self, service):
        """Test handling of timeout errors."""
        
        with patch.object(service, 'logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                service.handle_timeout_error(
                    operation="restaurant_search",
                    timeout_seconds=30,
                    context={"query": "test", "districts": ["Central district"]},
                )
        
        assert exc_info.value.status_code == status.HTTP_408_REQUEST_TIMEOUT
        assert "restaurant_search" in exc_info.value.detail["message"]
        assert exc_info.value.detail["timeout_seconds"] == 30
        assert "retry_guidance" in exc_info.value.detail
        
        mock_logger.error.assert_called_once()
    
    def test_handle_service_unavailable_error(self, service):
        """Test handling of service unavailable errors."""
        
        with patch.object(service, 'logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                service.handle_service_unavailable_error(
                    service_name="restaurant-search-mcp",
                    reason="Server maintenance",
                    retry_after=300,
                )
        
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "restaurant-search-mcp" in exc_info.value.detail["message"]
        assert "Server maintenance" in exc_info.value.detail["message"]
        assert exc_info.value.detail["retry_after"] == 300
        assert exc_info.value.headers["Retry-After"] == "300"
        
        mock_logger.error.assert_called_once()
    
    def test_log_error_context(self, service):
        """Test logging error with context information."""
        error = ValueError("Test error")
        context = {
            "operation": "restaurant_search",
            "user_id": "user-123",
            "request_id": "req-456",
        }
        
        with patch.object(service, 'logger') as mock_logger:
            service.log_error_context(error, context, level="warning")
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "restaurant_search" in call_args[0][0]
        assert call_args[1]["extra"]["error_type"] == "ValueError"
        assert call_args[1]["extra"]["user_id"] == "user-123"
        assert call_args[1]["exc_info"] is True
    
    def test_create_error_summary(self, service):
        """Test creating error summary from multiple errors."""
        errors = [
            ValueError("Value error 1"),
            ValueError("Value error 2"),
            ConnectionError("Connection failed"),
            TimeoutError("Request timeout"),
        ]
        
        summary = service.create_error_summary(errors, "batch_operation")
        
        assert summary["operation"] == "batch_operation"
        assert summary["total_errors"] == 4
        assert summary["error_types"]["ValueError"] == 2
        assert summary["error_types"]["ConnectionError"] == 1
        assert summary["error_types"]["TimeoutError"] == 1
        assert len(summary["errors"]) == 4
        
        # Check individual error details
        assert summary["errors"][0]["type"] == "ValueError"
        assert summary["errors"][0]["message"] == "Value error 1"
    
    def test_should_retry_error(self, service):
        """Test retry decision logic for different error types."""
        
        # Test retryable errors
        assert service.should_retry_error(ConnectionError("Connection failed"), 1, 3) is True
        assert service.should_retry_error(TimeoutError("Timeout"), 2, 3) is True
        
        mcp_error = MCPServerException("Server error", "test", "http://test:8080")
        assert service.should_retry_error(mcp_error, 1, 3) is True
        
        # Test retryable HTTP exceptions
        http_503 = HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        assert service.should_retry_error(http_503, 1, 3) is True
        
        http_429 = HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        assert service.should_retry_error(http_429, 2, 3) is True
        
        # Test non-retryable errors
        assert service.should_retry_error(ValueError("Invalid value"), 1, 3) is False
        
        http_400 = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        assert service.should_retry_error(http_400, 1, 3) is False
        
        # Test max attempts exceeded
        assert service.should_retry_error(ConnectionError("Connection failed"), 3, 3) is False
        assert service.should_retry_error(ConnectionError("Connection failed"), 4, 3) is False
    
    def test_calculate_retry_delay(self, service):
        """Test retry delay calculation with different strategies."""
        
        # Test exponential backoff
        assert service.calculate_retry_delay(1, base_delay=1, exponential=True) == 1
        assert service.calculate_retry_delay(2, base_delay=1, exponential=True) == 2
        assert service.calculate_retry_delay(3, base_delay=1, exponential=True) == 4
        assert service.calculate_retry_delay(4, base_delay=1, exponential=True) == 8
        
        # Test linear backoff
        assert service.calculate_retry_delay(1, base_delay=5, exponential=False) == 5
        assert service.calculate_retry_delay(2, base_delay=5, exponential=False) == 10
        assert service.calculate_retry_delay(3, base_delay=5, exponential=False) == 15
        
        # Test max delay limit
        assert service.calculate_retry_delay(10, base_delay=1, max_delay=30, exponential=True) == 30
        assert service.calculate_retry_delay(5, base_delay=10, max_delay=25, exponential=False) == 25
    
    def test_error_service_singleton(self):
        """Test that error_service is properly instantiated."""
        assert isinstance(error_service, ErrorService)
        assert hasattr(error_service, 'logger')
        assert hasattr(error_service, 'handle_validation_error')


class TestErrorServiceIntegration:
    """Integration tests for ErrorService with other components."""
    
    def test_validation_error_to_http_exception_flow(self):
        """Test complete flow from validation error to HTTP exception."""
        
        # Create a real ValidationError
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            districts: list[str] = Field(..., min_items=1)
            meal_types: list[str] = Field(..., min_items=1)
        
        try:
            TestModel(districts=[], meal_types=["invalid"])
        except ValidationError as ve:
            with pytest.raises(HTTPException) as exc_info:
                error_service.handle_validation_error(ve, "test model")
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Validation failed for test model" in exc_info.value.detail["message"]
    
    def test_mcp_error_chain(self):
        """Test chaining of MCP errors through the service."""
        original_error = ConnectionError("Network unreachable")
        
        mcp_error = error_service.handle_mcp_connection_error(
            server_name="test-server",
            server_endpoint="http://test:8080",
            original_error=original_error,
            retry_attempt=1,
            max_retries=3,
        )
        
        # Verify the error can be used in retry logic
        assert error_service.should_retry_error(mcp_error, 1, 3) is True
        
        retry_delay = error_service.calculate_retry_delay(1)
        assert retry_delay == 1
    
    def test_authentication_error_with_context(self):
        """Test authentication error handling with full context."""
        auth_error = error_service.handle_authentication_error(
            error_type="expired_token",
            details={"token_exp": 1234567890, "current_time": 1234567950},
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/.well-known/openid-configuration",
        )
        
        assert isinstance(auth_error, AuthenticationException)
        assert "expired" in str(auth_error).lower()
        assert "cognito-idp" in auth_error.discovery_url
        assert auth_error.auth_type == "JWT"