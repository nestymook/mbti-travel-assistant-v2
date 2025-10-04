"""
Test configuration for AgentCore Gateway MCP Tools.

This module provides pytest fixtures and configuration for testing
the AgentCore Gateway application with proper mocking of authentication
and MCP client dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from main import app
from middleware.jwt_validator import UserContext


@pytest.fixture
def mock_user_context():
    """Mock authenticated user context."""
    return UserContext(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        token_claims={
            "sub": "test-user-123",
            "token_use": "access",
            "aud": "test-client-id",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST",
            "access_token": "test-access-token"
        },
        authenticated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client manager."""
    mock_client = AsyncMock()
    mock_client.call_mcp_tool = AsyncMock()
    mock_client.get_all_server_status = MagicMock(return_value={
        "restaurant-search": MagicMock(status=MagicMock(value="healthy")),
        "restaurant-reasoning": MagicMock(status=MagicMock(value="healthy"))
    })
    return mock_client


@pytest.fixture
def auth_headers():
    """Authentication headers for requests."""
    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def client_with_auth_bypass(mock_user_context, mock_mcp_client):
    """
    Create test client with authentication and MCP client mocked.
    
    This fixture automatically mocks the authentication middleware
    and MCP client manager for all tests that use it.
    """
    with patch("middleware.auth_middleware.get_current_user", return_value=mock_user_context), \
         patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
         patch("api.tool_metadata_endpoints.get_current_user", return_value=mock_user_context), \
         patch("services.mcp_client_manager.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("main.get_mcp_client_manager", return_value=mock_mcp_client):
        
        yield TestClient(app)


@pytest.fixture
def client():
    """Create basic test client without authentication mocking."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock application settings for testing."""
    with patch("config.settings.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.app.cors_origins = ["*"]
        mock_settings.app.cors_allow_credentials = True
        mock_settings.app.cors_allow_methods = ["*"]
        mock_settings.app.cors_allow_headers = ["*"]
        mock_settings.app.bypass_paths = ["/health", "/", "/docs", "/redoc", "/openapi.json"]
        mock_settings.auth.cognito_user_pool_id = "us-east-1_TEST"
        mock_settings.auth.cognito_client_id = "test-client-id"
        mock_settings.auth.cognito_region = "us-east-1"
        mock_settings.auth.discovery_url = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST/.well-known/openid-configuration"
        mock_settings.mcp.servers = {
            "restaurant-search": {
                "endpoint": "http://localhost:8001",
                "timeout": 30,
                "max_retries": 3
            },
            "restaurant-reasoning": {
                "endpoint": "http://localhost:8002",
                "timeout": 30,
                "max_retries": 3
            }
        }
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture(autouse=True)
def mock_startup_shutdown():
    """Mock FastAPI startup and shutdown events."""
    with patch("main.get_mcp_client_manager", return_value=AsyncMock()), \
         patch("main.shutdown_mcp_client_manager", return_value=AsyncMock()):
        yield


# Configure pytest to handle async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()