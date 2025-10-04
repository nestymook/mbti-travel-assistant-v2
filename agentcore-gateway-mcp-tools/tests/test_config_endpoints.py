"""
Tests for configuration management API endpoints.

This module tests the REST API endpoints for configuration management including:
- Getting current configuration
- Reloading configuration
- Validating configuration
- Managing MCP server configurations
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from services.config_manager import EnvironmentConfig, MCPServerConfig
from middleware.jwt_validator import UserContext


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_user_context():
    """Mock user context for authentication."""
    return UserContext(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        token_claims={"sub": "test-user-123", "aud": "test-client"},
        authenticated_at=None
    )


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return EnvironmentConfig(
        name="development",
        log_level="INFO",
        debug=True,
        enable_hot_reload=True,
        mcp_servers={
            "search": MCPServerConfig(
                name="search",
                url="http://localhost:8080",
                timeout=30,
                max_retries=3,
                retry_delay=1.0,
                health_check_path="/health",
                enabled=True,
                tools=["search_restaurants_by_district"]
            ),
            "reasoning": MCPServerConfig(
                name="reasoning",
                url="http://localhost:8081",
                timeout=30,
                max_retries=3,
                retry_delay=1.0,
                health_check_path="/health",
                enabled=True,
                tools=["recommend_restaurants"]
            )
        }
    )


class TestConfigEndpoints:
    """Test configuration management endpoints."""
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_get_current_configuration_success(self, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test successful retrieval of current configuration."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_current_config.return_value = sample_config
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/current")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["environment"] == "development"
        assert data["data"]["debug"] is True
        assert "mcp_servers" in data["data"]
        assert len(data["data"]["mcp_servers"]) == 2
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_get_current_configuration_not_loaded(self, mock_get_manager, mock_get_user, client, mock_user_context):
        """Test getting configuration when not loaded."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_current_config.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/current")
        
        # Verify response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "Configuration not loaded" in data["detail"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    @patch('api.config_endpoints.get_config_validator')
    def test_reload_configuration_success(self, mock_get_validator, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test successful configuration reload."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.reload_configuration = AsyncMock()
        mock_manager.get_current_config.return_value = sample_config
        mock_get_manager.return_value = mock_manager
        
        mock_validator = Mock()
        mock_validator.validate_configuration = AsyncMock(return_value=(True, [], []))
        mock_get_validator.return_value = mock_validator
        
        # Make request
        response = client.post("/config/reload")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "Configuration reloaded successfully" in data["message"]
        assert data["data"]["environment"] == "development"
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    @patch('api.config_endpoints.get_config_validator')
    def test_reload_configuration_validation_failure(self, mock_get_validator, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test configuration reload with validation failure."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.reload_configuration = AsyncMock()
        mock_manager.get_current_config.return_value = sample_config
        mock_get_manager.return_value = mock_manager
        
        mock_validator = Mock()
        mock_validator.validate_configuration = AsyncMock(return_value=(False, ["Validation error"], []))
        mock_get_validator.return_value = mock_validator
        
        # Make request
        response = client.post("/config/reload")
        
        # Verify response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid configuration after reload" in data["detail"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    @patch('api.config_endpoints.get_config_validator')
    def test_validate_current_configuration_success(self, mock_get_validator, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test successful configuration validation."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_current_config.return_value = sample_config
        mock_get_manager.return_value = mock_manager
        
        mock_validator = Mock()
        mock_validator.validate_configuration = AsyncMock(return_value=(True, [], ["warning"]))
        mock_validator.validate_server_connectivity = AsyncMock(return_value=(True, None))
        mock_get_validator.return_value = mock_validator
        
        # Make request
        response = client.get("/config/validate")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert len(data["data"]["errors"]) == 0
        assert len(data["data"]["warnings"]) == 1
        assert "connectivity" in data["data"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.validate_all_environment_configs')
    def test_validate_all_configurations_success(self, mock_validate_all, mock_get_user, client, mock_user_context):
        """Test validation of all environment configurations."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_validate_all.return_value = {
            "development": (True, [], []),
            "staging": (True, [], ["warning"]),
            "production": (False, ["error"], []),
            "test": (True, [], [])
        }
        
        # Make request
        response = client.get("/config/validate/all")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["summary"]["total_environments"] == 4
        assert data["data"]["summary"]["valid_environments"] == 3
        assert data["data"]["summary"]["invalid_environments"] == 1
        
        assert "development" in data["data"]["results"]
        assert "staging" in data["data"]["results"]
        assert "production" in data["data"]["results"]
        assert "test" in data["data"]["results"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_get_mcp_servers_success(self, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test successful retrieval of MCP servers."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_all_mcp_servers.return_value = sample_config.mcp_servers
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/servers")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_servers"] == 2
        assert data["data"]["enabled_servers"] == 2
        assert "search" in data["data"]["servers"]
        assert "reasoning" in data["data"]["servers"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    @patch('api.config_endpoints.get_config_validator')
    def test_get_mcp_server_success(self, mock_get_validator, mock_get_manager, mock_get_user, client, mock_user_context, sample_config):
        """Test successful retrieval of specific MCP server."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_mcp_server_config.return_value = sample_config.mcp_servers["search"]
        mock_get_manager.return_value = mock_manager
        
        mock_validator = Mock()
        mock_validator.validate_server_connectivity = AsyncMock(return_value=(True, None))
        mock_get_validator.return_value = mock_validator
        
        # Make request
        response = client.get("/config/servers/search")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["name"] == "search"
        assert data["data"]["url"] == "http://localhost:8080"
        assert data["data"]["connectivity"]["reachable"] is True
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_get_mcp_server_not_found(self, mock_get_manager, mock_get_user, client, mock_user_context):
        """Test retrieval of non-existent MCP server."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_mcp_server_config.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/servers/nonexistent")
        
        # Verify response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "MCP server 'nonexistent' not found" in data["detail"]


class TestConfigEndpointsAuthentication:
    """Test authentication requirements for configuration endpoints."""
    
    def test_get_current_configuration_requires_auth(self, client):
        """Test that getting current configuration requires authentication."""
        response = client.get("/config/current")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_reload_configuration_requires_auth(self, client):
        """Test that reloading configuration requires authentication."""
        response = client.post("/config/reload")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_validate_configuration_requires_auth(self, client):
        """Test that validating configuration requires authentication."""
        response = client.get("/config/validate")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_mcp_servers_requires_auth(self, client):
        """Test that getting MCP servers requires authentication."""
        response = client.get("/config/servers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_mcp_server_requires_auth(self, client):
        """Test that getting specific MCP server requires authentication."""
        response = client.get("/config/servers/search")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestConfigEndpointsErrorHandling:
    """Test error handling in configuration endpoints."""
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_get_current_configuration_error(self, mock_get_manager, mock_get_user, client, mock_user_context):
        """Test error handling in get current configuration."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_current_config.side_effect = Exception("Test error")
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/current")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to get configuration" in data["detail"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_reload_configuration_error(self, mock_get_manager, mock_get_user, client, mock_user_context):
        """Test error handling in reload configuration."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.reload_configuration = AsyncMock(side_effect=Exception("Test error"))
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.post("/config/reload")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to reload configuration" in data["detail"]
    
    @patch('api.config_endpoints.get_current_user')
    @patch('api.config_endpoints.get_config_manager')
    def test_validate_configuration_error(self, mock_get_manager, mock_get_user, client, mock_user_context):
        """Test error handling in validate configuration."""
        # Setup mocks
        mock_get_user.return_value = mock_user_context
        mock_manager = Mock()
        mock_manager.get_current_config.side_effect = Exception("Test error")
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/config/validate")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to validate configuration" in data["detail"]


@pytest.mark.integration
class TestConfigEndpointsIntegration:
    """Integration tests for configuration endpoints."""
    
    @patch('api.config_endpoints.get_current_user')
    def test_full_configuration_workflow(self, mock_get_user, client, mock_user_context):
        """Test complete configuration management workflow."""
        # Setup authentication
        mock_get_user.return_value = mock_user_context
        
        # This would require actual configuration manager setup
        # For now, we'll test that the endpoints are accessible
        
        # Test getting current configuration
        response = client.get("/config/current")
        # May return 503 if no config loaded, which is expected
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        
        # Test getting MCP servers
        response = client.get("/config/servers")
        # May return error if no config loaded
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


if __name__ == "__main__":
    pytest.main([__file__])