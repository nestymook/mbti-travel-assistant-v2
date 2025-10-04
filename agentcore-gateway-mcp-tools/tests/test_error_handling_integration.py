"""
Integration tests for the complete error handling system in the AgentCore Gateway MCP Tools service.

Tests the end-to-end error handling flow from request to response.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError

from middleware.error_handler import (
    AuthenticationException,
    ErrorHandlerMiddleware,
    MCPServerException,
    RateLimitException,
)
from models.error_models import ErrorType
from services.error_service import error_service


class ValidationTestRequest(BaseModel):
    """Test request model for validation testing."""
    districts: list[str] = Field(..., min_length=1, description="List of districts")
    meal_types: list[str] = Field(..., min_length=1, description="List of meal types")


class TestErrorHandlingIntegration:
    """Integration tests for complete error handling system."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with error handling middleware."""
        app = FastAPI(title="Test API")
        
        # Add error handling middleware
        app.add_middleware(ErrorHandlerMiddleware, include_trace_id=True, log_errors=True)
        
        # Add custom exception handlers to ensure our middleware handles validation errors
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request, exc):
            # Re-raise to let middleware handle it
            raise exc
        
        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request, exc):
            # Re-raise to let middleware handle it
            raise exc
        
        @app.post("/test/validation")
        async def test_validation(request: ValidationTestRequest):
            return {"message": "success", "data": request.model_dump()}
        
        @app.post("/test/authentication")
        async def test_authentication():
            raise AuthenticationException(
                message="Token expired",
                auth_type="JWT",
                discovery_url="https://example.com/.well-known/openid-configuration",
                required_scopes=["read:test"],
            )
        
        @app.post("/test/mcp-server")
        async def test_mcp_server():
            raise MCPServerException(
                message="Server unavailable",
                server_name="test-server",
                server_endpoint="http://test:8080",
                retry_after=30,
                max_retries=3,
                current_attempt=1,
            )
        
        @app.post("/test/rate-limit")
        async def test_rate_limit():
            raise RateLimitException(
                message="Too many requests",
                limit=100,
                window=3600,
                retry_after=1800,
                current_usage=105,
            )
        
        @app.post("/test/http-exception")
        async def test_http_exception():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
                headers={"X-Custom-Header": "test-value"},
            )
        
        @app.post("/test/internal-error")
        async def test_internal_error():
            raise ValueError("Unexpected internal error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_successful_request(self, client):
        """Test that successful requests work normally."""
        response = client.post(
            "/test/validation",
            json={
                "districts": ["Central district"],
                "meal_types": ["lunch"],
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "success"
        assert data["data"]["districts"] == ["Central district"]
        assert data["data"]["meal_types"] == ["lunch"]
    
    def test_validation_error_response(self, client):
        """Test validation error handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post(
                "/test/validation",
                json={
                    "districts": [],  # Empty list should fail min_items validation
                    "meal_types": ["invalid_meal"],  # This will pass basic validation
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert "error" in data
        assert "request_id" in data
        assert "timestamp" in data
        
        # Check error details
        error = data["error"]
        assert error["type"] == "ValidationError"
        assert "validation failed" in error["message"].lower()
        assert "field_errors" in error
        assert "invalid_fields" in error
        
        # Check field errors
        field_errors = error["field_errors"]
        assert len(field_errors) > 0
        
        # Find the districts error
        districts_error = next((e for e in field_errors if e["field"] == "districts"), None)
        assert districts_error is not None
        assert "min_items" in districts_error["constraint"] or "ensure this value has at least" in districts_error["message"]
    
    def test_authentication_error_response(self, client):
        """Test authentication error handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/authentication")
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert "JWT" in response.headers["WWW-Authenticate"]
        
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"]["type"] == "AuthenticationError"
        assert "token expired" in data["error"]["message"].lower()
        
        # Check authentication details
        auth_details = data["error"]["auth_details"]
        assert auth_details["auth_type"] == "JWT"
        assert "example.com" in auth_details["discovery_url"]
        assert auth_details["required_scopes"] == ["read:test"]
    
    def test_mcp_server_error_response(self, client):
        """Test MCP server error handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/mcp-server")
        
        assert response.status_code == 503
        assert response.headers.get("Retry-After") == "30"
        
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"]["type"] == "MCPServerError"
        assert "unavailable" in data["error"]["message"].lower()
        
        # Check server details
        server_details = data["error"]["server_details"]
        assert server_details["server_name"] == "test-server"
        assert server_details["server_endpoint"] == "http://test:8080"
        assert server_details["retry_after"] == 30
        assert server_details["max_retries"] == 3
        assert server_details["current_attempt"] == 1
        
        # Check retry guidance
        assert "retry_guidance" in data["error"]
        assert "30 seconds" in data["error"]["retry_guidance"]
    
    def test_rate_limit_error_response(self, client):
        """Test rate limit error handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/rate-limit")
        
        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "1800"
        assert response.headers.get("X-RateLimit-Limit") == "100"
        assert response.headers.get("X-RateLimit-Window") == "3600"
        
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"]["type"] == "RateLimitError"
        assert "too many requests" in data["error"]["message"].lower()
        
        # Check rate limit details
        rate_details = data["error"]["rate_limit_details"]
        assert rate_details["limit"] == 100
        assert rate_details["window"] == 3600
        assert rate_details["retry_after"] == 1800
        assert rate_details["current_usage"] == 105
    
    def test_http_exception_response(self, client):
        """Test HTTP exception handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/http-exception")
        
        assert response.status_code == 404
        assert response.headers.get("X-Custom-Header") == "test-value"
        
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"]["message"] == "Resource not found"
        assert data["error"]["code"] == "HTTP_404"
    
    def test_internal_error_response(self, client):
        """Test internal error handling and response format."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/internal-error")
        
        assert response.status_code == 500
        
        data = response.json()
        
        # Check response structure
        assert data["success"] is False
        assert data["error"]["type"] == "InternalError"
        assert data["error"]["message"] == "An unexpected error occurred"
        
        # Check error details
        details = data["error"]["details"]
        assert details["exception_type"] == "ValueError"
        assert details["exception_message"] == "Unexpected internal error"
    
    def test_trace_id_consistency(self, client):
        """Test that trace IDs are consistent across error responses."""
        with patch('middleware.error_handler.logger'):
            response = client.post("/test/internal-error")
        
        data = response.json()
        
        # Both request_id and trace_id should be present and equal
        assert data["request_id"] is not None
        assert data["error"]["trace_id"] is not None
        assert data["request_id"] == data["error"]["trace_id"]
    
    def test_multiple_validation_errors(self, client):
        """Test handling of multiple validation errors in a single request."""
        with patch('middleware.error_handler.logger'):
            response = client.post(
                "/test/validation",
                json={
                    "districts": [],  # Empty list
                    "meal_types": [],  # Empty list
                }
            )
        
        assert response.status_code == 400
        data = response.json()
        
        # Should have errors for both fields
        field_errors = data["error"]["field_errors"]
        invalid_fields = data["error"]["invalid_fields"]
        
        assert len(field_errors) >= 2
        assert "districts" in invalid_fields
        assert "meal_types" in invalid_fields
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests."""
        with patch('middleware.error_handler.logger'):
            response = client.post(
                "/test/validation",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 422  # FastAPI's default for JSON decode errors
    
    def test_missing_content_type(self, client):
        """Test handling of requests with missing content type."""
        with patch('middleware.error_handler.logger'):
            response = client.post(
                "/test/validation",
                data='{"districts": ["Central district"], "meal_types": ["lunch"]}'
            )
        
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 422]
    
    def test_error_logging(self, client):
        """Test that errors are properly logged."""
        with patch('middleware.error_handler.logger') as mock_logger:
            client.post("/test/internal-error")
        
        # Verify that error was logged
        mock_logger.error.assert_called_once()
        
        # Check log call arguments
        call_args = mock_logger.error.call_args
        assert "Error processing request" in call_args[0][0]
        assert call_args[1]["exc_info"] is True
        assert "trace_id" in call_args[1]["extra"]
        assert "method" in call_args[1]["extra"]
        assert "url" in call_args[1]["extra"]


class TestErrorServiceIntegrationWithMiddleware:
    """Test integration between ErrorService and ErrorHandlerMiddleware."""
    
    def test_error_service_with_middleware_flow(self):
        """Test complete flow from ErrorService to middleware response."""
        
        # Create a validation error using ErrorService
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            districts: list[str] = Field(..., min_items=1)
        
        try:
            TestModel(districts=[])
        except ValidationError as ve:
            # This should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                error_service.handle_validation_error(ve, "test")
            
            # Verify the HTTPException would be handled correctly by middleware
            http_exc = exc_info.value
            assert http_exc.status_code == 400
            assert "Validation failed" in http_exc.detail["message"]
    
    def test_mcp_error_service_integration(self):
        """Test MCP error handling integration."""
        
        # Create MCP connection error
        original_error = ConnectionError("Network unreachable")
        mcp_error = error_service.handle_mcp_connection_error(
            server_name="test-server",
            server_endpoint="http://test:8080",
            original_error=original_error,
            retry_attempt=1,
            max_retries=3,
        )
        
        # Verify the error has correct attributes for middleware handling
        assert isinstance(mcp_error, MCPServerException)
        assert mcp_error.server_name == "test-server"
        assert mcp_error.retry_after is not None
        assert mcp_error.max_retries == 3
    
    def test_authentication_error_service_integration(self):
        """Test authentication error handling integration."""
        
        # Create authentication error
        auth_error = error_service.handle_authentication_error(
            error_type="invalid_token",
            discovery_url="https://example.com/.well-known/openid-configuration",
        )
        
        # Verify the error has correct attributes for middleware handling
        assert isinstance(auth_error, AuthenticationException)
        assert auth_error.auth_type == "JWT"
        assert "example.com" in auth_error.discovery_url
        assert auth_error.help_url is not None


class TestErrorHandlingEdgeCases:
    """Test edge cases and corner scenarios in error handling."""
    
    @pytest.fixture
    def minimal_app(self):
        """Create minimal FastAPI app for edge case testing."""
        app = FastAPI()
        app.add_middleware(ErrorHandlerMiddleware, include_trace_id=False, log_errors=False)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        return app
    
    def test_no_trace_id_configuration(self, minimal_app):
        """Test error handling with trace ID disabled."""
        client = TestClient(minimal_app)
        
        # Add an endpoint that raises an error
        @minimal_app.post("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        response = client.post("/error")
        data = response.json()
        
        # Trace ID should be None when disabled
        assert data["request_id"] is None
        assert data["error"]["trace_id"] is None
    
    def test_error_with_none_values(self):
        """Test error models with None values."""
        from models.error_models import ValidationErrorDetail
        
        # Should handle None values gracefully
        detail = ValidationErrorDetail(
            field="test_field",
            message="Test message",
            invalid_value=None,
            valid_values=None,
            constraint=None,
            suggestion=None,
        )
        
        assert detail.field == "test_field"
        assert detail.message == "Test message"
        assert detail.invalid_value is None
    
    def test_retry_logic_edge_cases(self):
        """Test retry logic with edge cases."""
        
        # Test with attempt equal to max attempts
        assert error_service.should_retry_error(ConnectionError("test"), 3, 3) is False
        
        # Test with attempt greater than max attempts
        assert error_service.should_retry_error(ConnectionError("test"), 5, 3) is False
        
        # Test with zero max attempts
        assert error_service.should_retry_error(ConnectionError("test"), 1, 0) is False
    
    def test_retry_delay_edge_cases(self):
        """Test retry delay calculation edge cases."""
        
        # Test with zero base delay
        assert error_service.calculate_retry_delay(1, base_delay=0) == 0
        
        # Test with very high attempt number
        delay = error_service.calculate_retry_delay(20, base_delay=1, max_delay=60)
        assert delay == 60  # Should be capped at max_delay
        
        # Test with negative attempt (should handle gracefully)
        delay = error_service.calculate_retry_delay(0, base_delay=5)
        assert delay >= 0