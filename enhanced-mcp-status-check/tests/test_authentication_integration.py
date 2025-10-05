"""
Authentication Integration Tests.

Comprehensive integration tests for authentication in both MCP and REST protocols.
Tests JWT authentication, token refresh, authentication failures, and security scenarios.

Requirements covered: 9.1, 9.2
"""

import pytest
import jwt
import time
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from models.dual_health_models import EnhancedServerConfig
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.authentication_service import AuthenticationService


class TestAuthenticationIntegration:
    """Integration tests for authentication in dual health checking."""

    @pytest.fixture
    async def enhanced_service(self):
        """Create enhanced health check service for testing."""
        service = EnhancedHealthCheckService()
        await service.initialize()
        return service

    @pytest.fixture
    def auth_service(self):
        """Create authentication service for testing."""
        return AuthenticationService()

    @pytest.fixture
    def jwt_server_config(self):
        """Create server configuration with JWT authentication."""
        return EnhancedServerConfig(
            server_name="jwt-auth-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=True,
            jwt_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJpYXQiOjE2NDA5OTUyMDAsImV4cCI6MTY0MDk5ODgwMH0.test-signature",
            auth_headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJpYXQiOjE2NDA5OTUyMDAsImV4cCI6MTY0MDk5ODgwMH0.test-signature",
                "X-API-Key": "api-key-123"
            }
        )

    @pytest.fixture
    def bearer_token_config(self):
        """Create server configuration with Bearer token authentication."""
        return EnhancedServerConfig(
            server_name="bearer-auth-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=True,
            auth_headers={
                "Authorization": "Bearer access-token-12345",
                "X-Client-ID": "client-123"
            }
        )

    async def test_jwt_authentication_mcp_success(self, enhanced_service, jwt_server_config, auth_service):
        """
        Test successful JWT authentication for MCP requests.
        
        Requirements: 9.1
        """
        with patch.object(auth_service, 'validate_jwt_token', return_value=True), \
             patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful MCP response
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            # Configure successful REST response
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify JWT token was included in MCP request
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "headers" in call_kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"].startswith("Bearer ")
            
            # Verify authentication succeeded
            assert result.mcp_success is True
            assert result.rest_success is True

    async def test_jwt_authentication_rest_success(self, enhanced_service, jwt_server_config, auth_service):
        """
        Test successful JWT authentication for REST requests.
        
        Requirements: 9.2
        """
        with patch.object(auth_service, 'validate_jwt_token', return_value=True), \
             patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify JWT token was included in REST request
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert "headers" in call_kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert "X-API-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["X-API-Key"] == "api-key-123"
            
            # Verify authentication succeeded
            assert result.rest_success is True

    async def test_bearer_token_authentication_integration(self, enhanced_service, bearer_token_config):
        """
        Test Bearer token authentication for both MCP and REST.
        
        Requirements: 9.1, 9.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(bearer_token_config)

            # Verify Bearer token was included in both requests
            mock_post.assert_called_once()
            mcp_headers = mock_post.call_args[1]["headers"]
            assert mcp_headers["Authorization"] == "Bearer access-token-12345"
            assert mcp_headers["X-Client-ID"] == "client-123"
            
            mock_get.assert_called_once()
            rest_headers = mock_get.call_args[1]["headers"]
            assert rest_headers["Authorization"] == "Bearer access-token-12345"
            assert rest_headers["X-Client-ID"] == "client-123"

    async def test_jwt_token_validation_failure(self, enhanced_service, jwt_server_config, auth_service):
        """
        Test JWT token validation failure handling.
        
        Requirements: 9.1, 9.2
        """
        with patch.object(auth_service, 'validate_jwt_token', return_value=False), \
             patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure authentication failure responses
            mock_post.return_value.__aenter__.return_value.status = 401
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "error": "Invalid JWT token"
            }
            
            mock_get.return_value.__aenter__.return_value.status = 401
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "error": "Authentication failed"
            }

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify authentication failures are handled
            assert result.mcp_success is False
            assert result.rest_success is False
            assert "401" in str(result.mcp_error_message) or "invalid" in str(result.mcp_error_message).lower()
            assert "401" in str(result.rest_error_message) or "authentication" in str(result.rest_error_message).lower()

    async def test_jwt_token_expiration_and_refresh(self, enhanced_service, jwt_server_config, auth_service):
        """
        Test JWT token expiration detection and automatic refresh.
        
        Requirements: 9.1, 9.2
        """
        # Create an expired JWT token
        expired_payload = {
            "sub": "test-user",
            "iat": int(time.time()) - 7200,  # Issued 2 hours ago
            "exp": int(time.time()) - 3600   # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        # Create a fresh JWT token
        fresh_payload = {
            "sub": "test-user",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600  # Expires in 1 hour
        }
        fresh_token = jwt.encode(fresh_payload, "secret", algorithm="HS256")

        jwt_server_config.jwt_token = expired_token
        jwt_server_config.auth_headers["Authorization"] = f"Bearer {expired_token}"

        with patch.object(auth_service, 'is_jwt_token_expired', return_value=True), \
             patch.object(auth_service, 'refresh_jwt_token', return_value=fresh_token), \
             patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses after token refresh
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify token refresh was called
            auth_service.refresh_jwt_token.assert_called_once()
            
            # Verify requests used refreshed token
            mock_post.assert_called_once()
            mcp_headers = mock_post.call_args[1]["headers"]
            assert fresh_token in mcp_headers["Authorization"]
            
            mock_get.assert_called_once()
            rest_headers = mock_get.call_args[1]["headers"]
            assert fresh_token in rest_headers["Authorization"]

    async def test_authentication_failure_mcp_success_rest(self, enhanced_service, jwt_server_config):
        """
        Test scenario where MCP authentication fails but REST succeeds.
        
        Requirements: 9.1, 9.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP authentication failure
            mock_post.return_value.__aenter__.return_value.status = 401
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "error": "JWT token validation failed"
            }
            
            # Configure REST authentication success
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify mixed authentication results
            assert result.mcp_success is False
            assert result.rest_success is True
            assert result.overall_success is False
            assert "jwt" in str(result.mcp_error_message).lower() or "401" in str(result.mcp_error_message)

    async def test_authentication_failure_rest_success_mcp(self, enhanced_service, jwt_server_config):
        """
        Test scenario where REST authentication fails but MCP succeeds.
        
        Requirements: 9.1, 9.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP authentication success
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            # Configure REST authentication failure
            mock_get.return_value.__aenter__.return_value.status = 403
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "error": "API key invalid or expired"
            }

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify mixed authentication results
            assert result.mcp_success is True
            assert result.rest_success is False
            assert result.overall_success is False
            assert "api key" in str(result.rest_error_message).lower() or "403" in str(result.rest_error_message)

    async def test_multiple_authentication_headers_integration(self, enhanced_service):
        """
        Test integration with multiple authentication headers.
        
        Requirements: 9.1, 9.2
        """
        multi_auth_config = EnhancedServerConfig(
            server_name="multi-auth-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=True,
            auth_headers={
                "Authorization": "Bearer jwt-token-123",
                "X-API-Key": "api-key-456",
                "X-Client-ID": "client-789",
                "X-Request-ID": "req-abc123",
                "User-Agent": "HealthChecker/1.0"
            }
        )

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(multi_auth_config)

            # Verify all authentication headers were included
            mock_post.assert_called_once()
            mcp_headers = mock_post.call_args[1]["headers"]
            assert mcp_headers["Authorization"] == "Bearer jwt-token-123"
            assert mcp_headers["X-API-Key"] == "api-key-456"
            assert mcp_headers["X-Client-ID"] == "client-789"
            assert mcp_headers["X-Request-ID"] == "req-abc123"
            assert mcp_headers["User-Agent"] == "HealthChecker/1.0"
            
            mock_get.assert_called_once()
            rest_headers = mock_get.call_args[1]["headers"]
            assert rest_headers["Authorization"] == "Bearer jwt-token-123"
            assert rest_headers["X-API-Key"] == "api-key-456"

    async def test_authentication_retry_after_token_refresh(self, enhanced_service, jwt_server_config, auth_service):
        """
        Test authentication retry after token refresh failure and recovery.
        
        Requirements: 9.1, 9.2
        """
        call_count = {'mcp': 0, 'rest': 0}
        
        def mock_post_side_effect(*args, **kwargs):
            call_count['mcp'] += 1
            if call_count['mcp'] == 1:
                # First call fails with expired token
                mock_response = AsyncMock()
                mock_response.status = 401
                mock_response.json.return_value = {"error": "Token expired"}
                return mock_response
            else:
                # Second call succeeds with refreshed token
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

        def mock_get_side_effect(*args, **kwargs):
            call_count['rest'] += 1
            if call_count['rest'] == 1:
                # First call fails with expired token
                mock_response = AsyncMock()
                mock_response.status = 401
                mock_response.json.return_value = {"error": "Token expired"}
                return mock_response
            else:
                # Second call succeeds with refreshed token
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

        with patch.object(auth_service, 'refresh_jwt_token', return_value="new-jwt-token"), \
             patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify retry logic worked
            assert call_count['mcp'] == 2
            assert call_count['rest'] == 2
            assert result.mcp_success is True
            assert result.rest_success is True
            auth_service.refresh_jwt_token.assert_called()

    async def test_authentication_security_headers_validation(self, enhanced_service, jwt_server_config):
        """
        Test validation of security-related authentication headers.
        
        Requirements: 9.1, 9.2
        """
        # Add security headers to configuration
        jwt_server_config.auth_headers.update({
            "X-Forwarded-For": "192.168.1.100",
            "X-Real-IP": "192.168.1.100",
            "X-Forwarded-Proto": "https",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY"
        })

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(jwt_server_config)

            # Verify security headers were included
            mock_post.assert_called_once()
            mcp_headers = mock_post.call_args[1]["headers"]
            assert mcp_headers["X-Forwarded-Proto"] == "https"
            assert mcp_headers["X-Content-Type-Options"] == "nosniff"
            assert mcp_headers["X-Frame-Options"] == "DENY"

    async def test_authentication_concurrent_requests_token_sharing(self, enhanced_service, jwt_server_config):
        """
        Test authentication with concurrent requests sharing the same token.
        
        Requirements: 9.1, 9.2
        """
        # Create multiple server configurations with same token
        server_configs = []
        for i in range(3):
            config = EnhancedServerConfig(
                server_name=f"concurrent-server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                jwt_token=jwt_server_config.jwt_token,
                auth_headers=jwt_server_config.auth_headers.copy()
            )
            server_configs.append(config)

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            # Execute concurrent health checks
            results = await enhanced_service.check_multiple_servers_dual(server_configs)

            # Verify all requests succeeded with shared authentication
            assert len(results) == 3
            for result in results:
                assert result.mcp_success is True
                assert result.rest_success is True

            # Verify authentication headers were used in all requests
            assert mock_post.call_count == 3
            assert mock_get.call_count == 3

    async def test_authentication_error_categorization(self, enhanced_service, jwt_server_config):
        """
        Test categorization of different authentication error types.
        
        Requirements: 9.1, 9.2
        """
        auth_error_scenarios = [
            (401, "Unauthorized", "Invalid credentials"),
            (403, "Forbidden", "Insufficient permissions"),
            (429, "Too Many Requests", "Rate limit exceeded"),
            (498, "Invalid Token", "Token format invalid"),
            (499, "Token Required", "Missing authentication token")
        ]

        for status_code, error_type, error_message in auth_error_scenarios:
            with patch('aiohttp.ClientSession.post') as mock_post, \
                 patch('aiohttp.ClientSession.get') as mock_get:
                
                # Configure authentication error responses
                mock_post.return_value.__aenter__.return_value.status = status_code
                mock_post.return_value.__aenter__.return_value.json.return_value = {
                    "error": f"{error_type}: {error_message}"
                }
                
                mock_get.return_value.__aenter__.return_value.status = status_code
                mock_get.return_value.__aenter__.return_value.json.return_value = {
                    "error": f"{error_type}: {error_message}"
                }

                result = await enhanced_service.perform_dual_health_check(jwt_server_config)

                # Verify error categorization
                assert result.mcp_success is False
                assert result.rest_success is False
                assert str(status_code) in str(result.mcp_error_message) or error_type.lower() in str(result.mcp_error_message).lower()
                assert str(status_code) in str(result.rest_error_message) or error_type.lower() in str(result.rest_error_message).lower()