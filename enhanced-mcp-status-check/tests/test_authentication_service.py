"""
Tests for Authentication Service

This module contains comprehensive tests for the authentication service
including JWT authentication, token refresh, and security validation.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aioresponses import aioresponses

from models.auth_models import (
    AuthenticationType,
    AuthenticationConfig,
    AuthenticationResult,
    AuthenticationError,
    JWTTokenInfo,
    SecureCredentialStore,
    AuthenticationMetrics
)
from services.authentication_service import AuthenticationService


class TestAuthenticationService:
    """Test cases for AuthenticationService."""
    
    @pytest.fixture
    async def auth_service(self):
        """Create authentication service for testing."""
        service = AuthenticationService()
        await service.__aenter__()
        yield service
        await service.__aexit__(None, None, None)
    
    @pytest.fixture
    def jwt_config(self):
        """Create JWT authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        )
    
    @pytest.fixture
    def bearer_config(self):
        """Create bearer token authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="test-bearer-token"
        )
    
    @pytest.fixture
    def api_key_config(self):
        """Create API key authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.API_KEY,
            api_key="test-api-key",
            api_key_header="X-API-Key"
        )
    
    @pytest.fixture
    def basic_auth_config(self):
        """Create basic authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.BASIC_AUTH,
            username="testuser",
            password="testpass"
        )
    
    @pytest.fixture
    def oauth2_config(self):
        """Create OAuth2 authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="test-client-id",
            oauth2_client_secret="test-client-secret",
            oauth2_scope=["read", "write"]
        )
    
    @pytest.fixture
    def custom_headers_config(self):
        """Create custom headers authentication configuration."""
        return AuthenticationConfig(
            auth_type=AuthenticationType.CUSTOM_HEADER,
            custom_headers={"X-Custom-Auth": "custom-value", "X-Request-ID": "12345"}
        )
    
    async def test_no_authentication(self, auth_service):
        """Test authentication with no auth type."""
        config = AuthenticationConfig(auth_type=AuthenticationType.NONE)
        
        result = await auth_service.authenticate("test-server", config)
        
        assert result.success is True
        assert result.auth_headers == {}
        assert result.error_message is None
    
    async def test_jwt_authentication_with_token(self, auth_service, jwt_config):
        """Test JWT authentication with provided token."""
        result = await auth_service.authenticate("test-server", jwt_config)
        
        assert result.success is True
        assert "Authorization" in result.auth_headers
        assert result.auth_headers["Authorization"].startswith("Bearer ")
        assert result.token_info is not None
        assert result.token_info.token == jwt_config.jwt_token
    
    async def test_bearer_token_authentication(self, auth_service, bearer_config):
        """Test bearer token authentication."""
        result = await auth_service.authenticate("test-server", bearer_config)
        
        assert result.success is True
        assert result.auth_headers["Authorization"] == f"Bearer {bearer_config.bearer_token}"
    
    async def test_api_key_authentication(self, auth_service, api_key_config):
        """Test API key authentication."""
        result = await auth_service.authenticate("test-server", api_key_config)
        
        assert result.success is True
        assert result.auth_headers[api_key_config.api_key_header] == api_key_config.api_key
    
    async def test_basic_auth_authentication(self, auth_service, basic_auth_config):
        """Test basic authentication."""
        result = await auth_service.authenticate("test-server", basic_auth_config)
        
        assert result.success is True
        assert "Authorization" in result.auth_headers
        assert result.auth_headers["Authorization"].startswith("Basic ")
    
    async def test_custom_headers_authentication(self, auth_service, custom_headers_config):
        """Test custom headers authentication."""
        result = await auth_service.authenticate("test-server", custom_headers_config)
        
        assert result.success is True
        assert result.auth_headers == custom_headers_config.custom_headers
    
    async def test_oauth2_authentication_success(self, auth_service, oauth2_config):
        """Test successful OAuth2 authentication."""
        token_response = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            m.post(oauth2_config.oauth2_token_url, payload=token_response)
            
            result = await auth_service.authenticate("test-server", oauth2_config)
            
            assert result.success is True
            assert result.auth_headers["Authorization"] == "Bearer test-access-token"
            assert result.token_info is not None
            assert result.expires_at is not None
    
    async def test_oauth2_authentication_failure(self, auth_service, oauth2_config):
        """Test OAuth2 authentication failure."""
        error_response = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }
        
        with aioresponses() as m:
            m.post(oauth2_config.oauth2_token_url, payload=error_response, status=400)
            
            result = await auth_service.authenticate("test-server", oauth2_config)
            
            assert result.success is False
            assert "invalid_client" in result.error_message or "Invalid client" in result.error_message
    
    async def test_jwt_client_credentials_flow(self, auth_service):
        """Test JWT authentication using client credentials flow."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_discovery_url="https://auth.example.com/.well-known/openid-configuration",
            jwt_client_id="test-client-id",
            jwt_client_secret="test-client-secret",
            jwt_scope=["openid", "profile"]
        )
        
        discovery_response = {
            "token_endpoint": "https://auth.example.com/token",
            "issuer": "https://auth.example.com"
        }
        
        token_response = {
            "access_token": "test-jwt-token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            m.get(config.jwt_discovery_url, payload=discovery_response)
            m.post("https://auth.example.com/token", payload=token_response)
            
            result = await auth_service.authenticate("test-server", config)
            
            assert result.success is True
            assert result.auth_headers["Authorization"] == "Bearer test-jwt-token"
    
    async def test_token_refresh_when_expired(self, auth_service, oauth2_config):
        """Test automatic token refresh when token is expired."""
        # First authentication
        token_response = {
            "access_token": "initial-token",
            "expires_in": 1  # Very short expiry
        }
        
        with aioresponses() as m:
            m.post(oauth2_config.oauth2_token_url, payload=token_response)
            
            result1 = await auth_service.authenticate("test-server", oauth2_config)
            assert result1.success is True
        
        # Wait for token to expire
        await asyncio.sleep(2)
        
        # Second authentication should refresh token
        refresh_response = {
            "access_token": "refreshed-token",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            m.post(oauth2_config.oauth2_token_url, payload=refresh_response)
            
            result2 = await auth_service.refresh_token_if_needed("test-server", oauth2_config)
            assert result2.success is True
    
    async def test_authentication_error_handling(self, auth_service):
        """Test authentication error handling."""
        # Missing credentials
        config = AuthenticationConfig(auth_type=AuthenticationType.JWT)
        
        result = await auth_service.authenticate("test-server", config)
        
        assert result.success is False
        assert result.error_type == "MISSING_JWT_CREDENTIALS"
        assert "JWT authentication requires" in result.error_message
    
    async def test_unsupported_auth_type(self, auth_service):
        """Test handling of unsupported authentication type."""
        # Create config with invalid auth type (simulate future enum value)
        config = AuthenticationConfig()
        config.auth_type = "UNSUPPORTED_TYPE"  # Invalid enum value
        
        with pytest.raises(ValueError):
            await auth_service.authenticate("test-server", config)
    
    async def test_concurrent_token_refresh(self, auth_service, oauth2_config):
        """Test concurrent token refresh attempts."""
        # Set up expired token
        expired_token = JWTTokenInfo(
            token="expired-token",
            expires_at=datetime.now() - timedelta(minutes=1)
        )
        auth_service._credential_store.store_token("test-server", expired_token)
        
        refresh_response = {
            "access_token": "new-token",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            # Only one request should be made despite concurrent calls
            m.post(oauth2_config.oauth2_token_url, payload=refresh_response)
            
            # Make concurrent refresh requests
            tasks = [
                auth_service.refresh_token_if_needed("test-server", oauth2_config)
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert result.success is True
    
    def test_secure_credential_store(self):
        """Test secure credential storage functionality."""
        store = SecureCredentialStore()
        
        # Store and retrieve credential
        store.store_credential("test-key", "test-value")
        assert store.get_credential("test-key") == "test-value"
        
        # Store and retrieve token
        token_info = JWTTokenInfo(
            token="test-token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        store.store_token("test-server", token_info)
        retrieved_token = store.get_token("test-server")
        assert retrieved_token.token == "test-token"
        
        # Remove credential
        assert store.remove_credential("test-key") is True
        assert store.get_credential("test-key") is None
        
        # Cleanup expired tokens
        expired_token = JWTTokenInfo(
            token="expired-token",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        store.store_token("expired-server", expired_token)
        
        removed_count = store.cleanup_expired_tokens()
        assert removed_count == 1
        assert store.get_token("expired-server") is None
    
    def test_authentication_metrics(self):
        """Test authentication metrics tracking."""
        metrics = AuthenticationMetrics()
        
        # Record successful authentication
        metrics.record_auth_attempt(True)
        assert metrics.successful_auth_attempts == 1
        assert metrics.total_auth_attempts == 1
        
        # Record failed authentication
        metrics.record_auth_attempt(False, "INVALID_TOKEN")
        assert metrics.failed_auth_attempts == 1
        assert metrics.total_auth_attempts == 2
        assert metrics.auth_errors_by_type["INVALID_TOKEN"] == 1
        
        # Record token refresh
        metrics.record_token_refresh(True)
        assert metrics.successful_token_refreshes == 1
        
        # Check success rates
        assert metrics.get_auth_success_rate() == 50.0  # 1 success out of 2 attempts
        assert metrics.get_token_refresh_success_rate() == 100.0
    
    def test_jwt_token_info(self):
        """Test JWT token information handling."""
        expires_at = datetime.now() + timedelta(hours=1)
        token_info = JWTTokenInfo(
            token="test-token",
            expires_at=expires_at,
            issuer="https://auth.example.com",
            scopes=["read", "write"]
        )
        
        # Test expiry check
        assert token_info.is_expired() is False
        assert token_info.is_expired(buffer_seconds=3700) is True  # Within buffer
        
        # Test time until expiry
        time_until_expiry = token_info.time_until_expiry()
        assert time_until_expiry is not None
        assert time_until_expiry.total_seconds() > 0
        
        # Test serialization
        token_dict = token_info.to_dict()
        assert token_dict["token"] == "test-token"
        assert token_dict["issuer"] == "https://auth.example.com"
        
        # Test deserialization
        restored_token = JWTTokenInfo.from_dict(token_dict)
        assert restored_token.token == token_info.token
        assert restored_token.issuer == token_info.issuer
    
    def test_authentication_config_validation(self):
        """Test authentication configuration validation."""
        # Valid JWT config
        jwt_config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="valid-token"
        )
        assert len(jwt_config.validate()) == 0
        
        # Invalid JWT config (missing credentials)
        invalid_jwt_config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT
        )
        errors = invalid_jwt_config.validate()
        assert len(errors) > 0
        assert any("JWT authentication requires" in error for error in errors)
        
        # Valid API key config
        api_key_config = AuthenticationConfig(
            auth_type=AuthenticationType.API_KEY,
            api_key="test-key",
            api_key_header="X-API-Key"
        )
        assert len(api_key_config.validate()) == 0
        
        # Invalid refresh configuration
        invalid_refresh_config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="token",
            refresh_buffer_seconds=-1,
            max_refresh_attempts=0
        )
        errors = invalid_refresh_config.validate()
        assert len(errors) >= 2  # Both refresh settings are invalid
    
    async def test_authentication_service_cleanup(self, auth_service):
        """Test authentication service cleanup operations."""
        # Store some tokens
        token1 = JWTTokenInfo(token="token1", expires_at=datetime.now() + timedelta(hours=1))
        token2 = JWTTokenInfo(token="token2", expires_at=datetime.now() - timedelta(hours=1))  # Expired
        
        auth_service._credential_store.store_token("server1", token1)
        auth_service._credential_store.store_token("server2", token2)
        
        # Test listing servers
        servers = auth_service.list_authenticated_servers()
        assert "server1" in servers
        assert "server2" in servers
        
        # Test cleanup expired tokens
        removed_count = auth_service.cleanup_expired_tokens()
        assert removed_count == 1
        
        # Test clearing specific server credentials
        auth_service.clear_credentials("server1")
        servers_after_clear = auth_service.list_authenticated_servers()
        assert "server1" not in servers_after_clear
        
        # Test clearing all credentials
        auth_service._credential_store.store_token("server3", token1)
        auth_service.clear_credentials()
        assert len(auth_service.list_authenticated_servers()) == 0


class TestAuthenticationIntegration:
    """Integration tests for authentication with health check clients."""
    
    @pytest.fixture
    async def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return session
    
    async def test_mcp_client_with_authentication(self, mock_session):
        """Test MCP health check client with authentication."""
        from services.mcp_health_check_client import MCPHealthCheckClient
        from models.dual_health_models import EnhancedServerConfig
        
        # Create server config with authentication
        auth_config = AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="test-bearer-token"
        )
        
        server_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="https://test.example.com/mcp",
            rest_health_endpoint_url="https://test.example.com/health",
            auth_config=auth_config
        )
        
        # Mock successful MCP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"tools": [{"name": "test_tool", "description": "Test tool"}]}
        })
        mock_response.headers = {}
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Create client with authentication service
        auth_service = AuthenticationService(mock_session)
        client = MCPHealthCheckClient(mock_session, auth_service)
        
        # Perform health check
        result = await client.perform_mcp_health_check(server_config)
        
        # Verify authentication headers were used
        call_args = mock_session.post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-bearer-token"
        
        # Verify health check succeeded
        assert result.success is True
    
    async def test_rest_client_with_authentication(self, mock_session):
        """Test REST health check client with authentication."""
        from services.rest_health_check_client import RESTHealthCheckClient
        from models.dual_health_models import EnhancedServerConfig
        
        # Create server config with authentication
        auth_config = AuthenticationConfig(
            auth_type=AuthenticationType.API_KEY,
            api_key="test-api-key",
            api_key_header="X-API-Key"
        )
        
        server_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="https://test.example.com/mcp",
            rest_health_endpoint_url="https://test.example.com/health",
            auth_config=auth_config
        )
        
        # Mock successful REST response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps({"status": "healthy", "uptime": 12345})
        mock_response.headers = {}
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Create client with authentication service
        auth_service = AuthenticationService(mock_session)
        client = RESTHealthCheckClient(mock_session, auth_service)
        
        # Perform health check
        result = await client.perform_rest_health_check(server_config)
        
        # Verify authentication headers were used
        call_args = mock_session.get.call_args
        headers = call_args[1]["headers"]
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "test-api-key"
        
        # Verify health check succeeded
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__])