"""
Tests for the observability middleware.

This module tests the automatic request tracking, user context logging,
and security event recording functionality of the observability middleware.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from datetime import datetime, timezone

from middleware.observability_middleware import (
    ObservabilityMiddleware,
    add_mcp_server_call_tracking,
    add_mcp_server_error_tracking
)
from middleware.jwt_validator import UserContext
from services.observability_service import SecurityEventType


class TestObservabilityMiddleware:
    """Test cases for ObservabilityMiddleware."""
    
    @pytest.fixture
    def mock_observability_service(self):
        """Mock observability service."""
        service = Mock()
        service.log_request_start.return_value = 1234567890.0
        service.log_request_end.return_value = None
        service.log_security_event.return_value = None
        return service
    
    @pytest.fixture
    def app_with_middleware(self, mock_observability_service):
        """Create FastAPI app with observability middleware."""
        app = FastAPI()
        
        # Mock the get_observability_service function
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_observability_service):
            app.add_middleware(
                ObservabilityMiddleware,
                bypass_paths=["/health", "/docs"]
            )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/test-auth")
        async def test_auth_endpoint(request: Request):
            # Simulate authenticated user
            request.state.user_context = UserContext(
                user_id="test-user-123",
                username="testuser",
                email="test@example.com",
                token_claims={"sub": "test-user-123"},
                authenticated_at=datetime.now(timezone.utc)
            )
            return {"message": "authenticated"}
        
        @app.get("/test-error")
        async def test_error_endpoint():
            raise HTTPException(status_code=500, detail="Test error")
        
        @app.get("/test-auth-error")
        async def test_auth_error_endpoint():
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client."""
        return TestClient(app_with_middleware)
    
    def test_successful_request_tracking(self, client, mock_observability_service):
        """Test successful request tracking."""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Verify observability service was called
        mock_observability_service.log_request_start.assert_called_once()
        mock_observability_service.log_request_end.assert_called_once()
        
        # Check log_request_start call
        start_call = mock_observability_service.log_request_start.call_args
        assert start_call[1]["endpoint"] == "/test"
        assert start_call[1]["method"] == "GET"
        assert start_call[1]["user_context"] is None
        assert "request_id" in start_call[1]
        
        # Check log_request_end call
        end_call = mock_observability_service.log_request_end.call_args
        assert end_call[1]["endpoint"] == "/test"
        assert end_call[1]["method"] == "GET"
        assert end_call[1]["status_code"] == 200
        assert end_call[1]["user_context"] is None
        assert end_call[1]["mcp_server_calls"] == 0
        assert end_call[1]["mcp_server_duration_ms"] == 0.0
    
    def test_authenticated_request_tracking(self, client, mock_observability_service):
        """Test authenticated request tracking."""
        response = client.get("/test-auth")
        
        assert response.status_code == 200
        
        # Verify security event was logged for successful authentication
        mock_observability_service.log_security_event.assert_called_once()
        
        security_call = mock_observability_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.AUTH_SUCCESS
        assert security_call[1]["user_id"] == "test-user-123"
        assert security_call[1]["endpoint"] == "/test-auth"
        assert "username" in security_call[1]["details"]
    
    def test_bypass_path_no_auth_logging(self, client, mock_observability_service):
        """Test that bypass paths don't log authentication events."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        # Should still log request start/end but not security events
        mock_observability_service.log_request_start.assert_called_once()
        mock_observability_service.log_request_end.assert_called_once()
        mock_observability_service.log_security_event.assert_not_called()
    
    def test_error_request_tracking(self, client, mock_observability_service):
        """Test error request tracking."""
        response = client.get("/test-error")
        
        assert response.status_code == 500
        
        # Verify error was logged
        mock_observability_service.log_request_end.assert_called_once()
        
        end_call = mock_observability_service.log_request_end.call_args
        assert end_call[1]["status_code"] == 500
        assert "error" in end_call[1]
    
    def test_authentication_error_tracking(self, client, mock_observability_service):
        """Test authentication error tracking."""
        response = client.get("/test-auth-error")
        
        assert response.status_code == 401
        
        # Verify security event was logged for authentication failure
        mock_observability_service.log_security_event.assert_called_once()
        
        security_call = mock_observability_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.AUTH_FAILURE
        assert security_call[1]["endpoint"] == "/test-auth-error"
        assert "error" in security_call[1]["details"]
    
    def test_client_ip_extraction_forwarded_for(self, app_with_middleware, mock_observability_service):
        """Test client IP extraction from X-Forwarded-For header."""
        client = TestClient(app_with_middleware)
        
        response = client.get("/test", headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"})
        
        assert response.status_code == 200
        
        # Check that the first IP was extracted
        start_call = mock_observability_service.log_request_start.call_args
        assert start_call[1]["ip_address"] == "192.168.1.1"
    
    def test_client_ip_extraction_real_ip(self, app_with_middleware, mock_observability_service):
        """Test client IP extraction from X-Real-IP header."""
        client = TestClient(app_with_middleware)
        
        response = client.get("/test", headers={"X-Real-IP": "203.0.113.1"})
        
        assert response.status_code == 200
        
        # Check that the real IP was extracted
        start_call = mock_observability_service.log_request_start.call_args
        assert start_call[1]["ip_address"] == "203.0.113.1"
    
    def test_user_agent_extraction(self, app_with_middleware, mock_observability_service):
        """Test user agent extraction."""
        client = TestClient(app_with_middleware)
        
        response = client.get("/test", headers={"User-Agent": "TestClient/1.0"})
        
        assert response.status_code == 200
        
        # Check that user agent was extracted
        start_call = mock_observability_service.log_request_start.call_args
        assert start_call[1]["user_agent"] == "TestClient/1.0"
    
    def test_request_id_generation(self, client, mock_observability_service):
        """Test that unique request IDs are generated."""
        response1 = client.get("/test")
        response2 = client.get("/test")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Get request IDs from both calls
        calls = mock_observability_service.log_request_start.call_args_list
        request_id1 = calls[0][1]["request_id"]
        request_id2 = calls[1][1]["request_id"]
        
        # Should be different UUIDs
        assert request_id1 != request_id2
        assert len(request_id1) == 36  # UUID format
        assert len(request_id2) == 36


class TestMCPServerCallTracking:
    """Test MCP server call tracking functions."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.state = Mock()
        return request
    
    @pytest.fixture
    def mock_observability_service(self):
        """Mock observability service."""
        service = Mock()
        service.log_mcp_server_call.return_value = None
        return service
    
    def test_add_mcp_server_call_tracking_first_call(self, mock_request, mock_observability_service):
        """Test adding MCP server call tracking for first call."""
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_observability_service):
            add_mcp_server_call_tracking(
                request=mock_request,
                server_name="search-server",
                tool_name="search_restaurants",
                duration_ms=50.0
            )
        
        # Check that tracking was initialized
        assert mock_request.state.mcp_server_calls == 1
        assert mock_request.state.mcp_server_duration_ms == 50.0
        assert len(mock_request.state.mcp_server_details) == 1
        
        detail = mock_request.state.mcp_server_details[0]
        assert detail["server_name"] == "search-server"
        assert detail["tool_name"] == "search_restaurants"
        assert detail["duration_ms"] == 50.0
        
        # Check that observability service was called
        mock_observability_service.log_mcp_server_call.assert_called_once_with(
            server_name="search-server",
            tool_name="search_restaurants",
            duration_ms=50.0,
            success=True
        )
    
    def test_add_mcp_server_call_tracking_multiple_calls(self, mock_request, mock_observability_service):
        """Test adding multiple MCP server call tracking."""
        # Initialize with first call
        mock_request.state.mcp_server_calls = 1
        mock_request.state.mcp_server_duration_ms = 25.0
        mock_request.state.mcp_server_details = [{"server_name": "search-server", "tool_name": "search", "duration_ms": 25.0}]
        
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_observability_service):
            add_mcp_server_call_tracking(
                request=mock_request,
                server_name="reasoning-server",
                tool_name="analyze_sentiment",
                duration_ms=75.0
            )
        
        # Check that tracking was updated
        assert mock_request.state.mcp_server_calls == 2
        assert mock_request.state.mcp_server_duration_ms == 100.0
        assert len(mock_request.state.mcp_server_details) == 2
        
        # Check second detail
        detail = mock_request.state.mcp_server_details[1]
        assert detail["server_name"] == "reasoning-server"
        assert detail["tool_name"] == "analyze_sentiment"
        assert detail["duration_ms"] == 75.0
    
    def test_add_mcp_server_error_tracking(self, mock_request, mock_observability_service):
        """Test adding MCP server error tracking."""
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_observability_service):
            add_mcp_server_error_tracking(
                request=mock_request,
                server_name="search-server",
                tool_name="search_restaurants",
                duration_ms=100.0,
                error="Connection timeout"
            )
        
        # Check that tracking was initialized with error
        assert mock_request.state.mcp_server_calls == 1
        assert mock_request.state.mcp_server_duration_ms == 100.0
        assert len(mock_request.state.mcp_server_details) == 1
        
        detail = mock_request.state.mcp_server_details[0]
        assert detail["server_name"] == "search-server"
        assert detail["tool_name"] == "search_restaurants"
        assert detail["duration_ms"] == 100.0
        assert detail["error"] == "Connection timeout"
        
        # Check that observability service was called with error
        mock_observability_service.log_mcp_server_call.assert_called_once_with(
            server_name="search-server",
            tool_name="search_restaurants",
            duration_ms=100.0,
            success=False,
            error="Connection timeout"
        )


class TestObservabilityMiddlewareErrorHandling:
    """Test error handling in observability middleware."""
    
    @pytest.fixture
    def app_with_various_errors(self):
        """Create FastAPI app with various error types."""
        app = FastAPI()
        
        # Mock observability service
        mock_service = Mock()
        mock_service.log_request_start.return_value = 1234567890.0
        mock_service.log_request_end.return_value = None
        mock_service.log_security_event.return_value = None
        
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_service):
            app.add_middleware(ObservabilityMiddleware)
        
        @app.get("/token-expired")
        async def token_expired_endpoint():
            raise Exception("Token has expired and refresh failed")
        
        @app.get("/token-invalid")
        async def token_invalid_endpoint():
            raise Exception("Token is invalid")
        
        @app.get("/forbidden")
        async def forbidden_endpoint():
            raise Exception("Access forbidden")
        
        @app.get("/rate-limit")
        async def rate_limit_endpoint():
            raise Exception("Rate limit exceeded")
        
        return app
    
    def test_token_expired_error_handling(self, app_with_various_errors):
        """Test token expired error handling."""
        client = TestClient(app_with_various_errors)
        
        with patch('middleware.observability_middleware.get_observability_service') as mock_get_service:
            mock_service = Mock()
            mock_service.log_request_start.return_value = 1234567890.0
            mock_service.log_request_end.return_value = None
            mock_service.log_security_event.return_value = None
            mock_get_service.return_value = mock_service
            
            response = client.get("/token-expired")
        
        assert response.status_code == 401
        
        # Check that token expired security event was logged
        mock_service.log_security_event.assert_called_once()
        security_call = mock_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.TOKEN_EXPIRED
    
    def test_token_invalid_error_handling(self, app_with_various_errors):
        """Test token invalid error handling."""
        client = TestClient(app_with_various_errors)
        
        with patch('middleware.observability_middleware.get_observability_service') as mock_get_service:
            mock_service = Mock()
            mock_service.log_request_start.return_value = 1234567890.0
            mock_service.log_request_end.return_value = None
            mock_service.log_security_event.return_value = None
            mock_get_service.return_value = mock_service
            
            response = client.get("/token-invalid")
        
        assert response.status_code == 401
        
        # Check that token invalid security event was logged
        mock_service.log_security_event.assert_called_once()
        security_call = mock_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.TOKEN_INVALID
    
    def test_forbidden_error_handling(self, app_with_various_errors):
        """Test forbidden error handling."""
        client = TestClient(app_with_various_errors)
        
        with patch('middleware.observability_middleware.get_observability_service') as mock_get_service:
            mock_service = Mock()
            mock_service.log_request_start.return_value = 1234567890.0
            mock_service.log_request_end.return_value = None
            mock_service.log_security_event.return_value = None
            mock_get_service.return_value = mock_service
            
            response = client.get("/forbidden")
        
        assert response.status_code == 403
        
        # Check that unauthorized access security event was logged
        mock_service.log_security_event.assert_called_once()
        security_call = mock_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.UNAUTHORIZED_ACCESS
    
    def test_rate_limit_error_handling(self, app_with_various_errors):
        """Test rate limit error handling."""
        client = TestClient(app_with_various_errors)
        
        with patch('middleware.observability_middleware.get_observability_service') as mock_get_service:
            mock_service = Mock()
            mock_service.log_request_start.return_value = 1234567890.0
            mock_service.log_request_end.return_value = None
            mock_service.log_security_event.return_value = None
            mock_get_service.return_value = mock_service
            
            response = client.get("/rate-limit")
        
        assert response.status_code == 429
        
        # Check that rate limit exceeded security event was logged
        mock_service.log_security_event.assert_called_once()
        security_call = mock_service.log_security_event.call_args
        assert security_call[1]["event_type"] == SecurityEventType.RATE_LIMIT_EXCEEDED