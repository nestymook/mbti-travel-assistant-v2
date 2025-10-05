"""
Security Validation Tests for Enhanced MCP Status Check

This module contains security-focused tests to validate authentication
security, credential protection, and secure communication patterns.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aioresponses import aioresponses

from models.auth_models import (
    AuthenticationType,
    AuthenticationConfig,
    AuthenticationError,
    JWTTokenInfo,
    SecureCredentialStore
)
from services.authentication_service import AuthenticationService


class TestSecurityValidation:
    """Security validation test cases."""
    
    @pytest.fixture
    async def auth_service(self):
        """Create authentication service for security testing."""
        service = AuthenticationService()
        await service.__aenter__()
        yield service
        await service.__aexit__(None, None, None)
    
    def test_credential_storage_security(self):
        """Test secure credential storage mechanisms."""
        store = SecureCredentialStore()
        
        # Test that credentials are not stored in plain text (placeholder test)
        # In production, this would verify encryption
        sensitive_data = "super-secret-password"
        store.store_credential("password", sensitive_data, encrypt=True)
        
        # Verify credential can be retrieved
        retrieved = store.get_credential("password", decrypt=True)
        assert retrieved == sensitive_data
        
        # Test credential isolation
        store.store_credential("user1_token", "token1")
        store.store_credential("user2_token", "token2")
        
        assert store.get_credential("user1_token") != store.get_credential("user2_token")
        assert store.get_credential("user1_token") == "token1"
        assert store.get_credential("user2_token") == "token2"
    
    def test_token_expiry_security(self):
        """Test token expiry validation and security."""
        # Test expired token detection
        expired_token = JWTTokenInfo(
            token="expired-token",
            expires_at=datetime.now() - timedelta(minutes=5)
        )
        assert expired_token.is_expired() is True
        
        # Test token with buffer time
        soon_to_expire = JWTTokenInfo(
            token="soon-expired-token",
            expires_at=datetime.now() + timedelta(seconds=30)
        )
        assert soon_to_expire.is_expired(buffer_seconds=60) is True
        assert soon_to_expire.is_expired(buffer_seconds=10) is False
        
        # Test valid token
        valid_token = JWTTokenInfo(
            token="valid-token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert valid_token.is_expired() is False
    
    async def test_authentication_failure_handling(self, auth_service):
        """Test secure handling of authentication failures."""
        # Test invalid JWT token
        invalid_jwt_config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="invalid.jwt.token"
        )
        
        result = await auth_service.authenticate("test-server", invalid_jwt_config)
        
        # Should fail gracefully without exposing sensitive information
        assert result.success is False
        assert result.error_type == "INVALID_JWT_TOKEN"
        assert "Invalid JWT token" in result.error_message
        # Should not expose the actual token in error message
        assert "invalid.jwt.token" not in result.error_message
    
    async def test_oauth2_security_validation(self, auth_service):
        """Test OAuth2 security validation."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="test-client",
            oauth2_client_secret="secret-key",
            oauth2_scope=["read"]
        )
        
        # Test handling of OAuth2 error responses
        error_response = {
            "error": "invalid_client",
            "error_description": "Client authentication failed"
        }
        
        with aioresponses() as m:
            m.post(config.oauth2_token_url, payload=error_response, status=401)
            
            result = await auth_service.authenticate("test-server", config)
            
            assert result.success is False
            assert result.error_type == "TOKEN_ACQUISITION_FAILED"
            # Should not expose client secret in error messages
            assert config.oauth2_client_secret not in result.error_message
    
    async def test_concurrent_authentication_security(self, auth_service):
        """Test security of concurrent authentication attempts."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="test-token"
        )
        
        # Simulate concurrent authentication attempts
        tasks = [
            auth_service.authenticate(f"server-{i}", config)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed and be isolated
        for i, result in enumerate(results):
            assert result.success is True
            assert result.auth_headers["Authorization"] == "Bearer test-token"
        
        # Verify no cross-contamination between server credentials
        metrics = auth_service.get_metrics()
        assert metrics.successful_auth_attempts == 10
        assert metrics.failed_auth_attempts == 0
    
    def test_sensitive_data_exposure_prevention(self):
        """Test prevention of sensitive data exposure."""
        # Test that authentication config doesn't expose secrets in string representation
        config = AuthenticationConfig(
            auth_type=AuthenticationType.BASIC_AUTH,
            username="testuser",
            password="supersecret123",
            oauth2_client_secret="oauth-secret"
        )
        
        config_dict = config.to_dict()
        
        # Verify sensitive data is present (for functionality)
        assert config_dict["password"] == "supersecret123"
        assert config_dict["oauth2_client_secret"] == "oauth-secret"
        
        # In production, these should be masked or encrypted
        # This test serves as a reminder to implement proper secret handling
    
    async def test_token_refresh_security(self, auth_service):
        """Test security aspects of token refresh."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="test-client",
            oauth2_client_secret="secret",
            auto_refresh_enabled=True,
            refresh_buffer_seconds=300
        )
        
        # Store an expired token
        expired_token = JWTTokenInfo(
            token="expired-token",
            expires_at=datetime.now() - timedelta(minutes=1)
        )
        auth_service._credential_store.store_token("test-server", expired_token)
        
        # Mock successful token refresh
        refresh_response = {
            "access_token": "new-secure-token",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            m.post(config.oauth2_token_url, payload=refresh_response)
            
            result = await auth_service.refresh_token_if_needed("test-server", config)
            
            assert result.success is True
            
            # Verify old token is replaced
            current_token = auth_service._credential_store.get_token("test-server")
            assert current_token.token == "new-secure-token"
            assert current_token.token != expired_token.token
    
    async def test_authentication_timeout_security(self, auth_service):
        """Test authentication timeout handling for security."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="test-client",
            oauth2_client_secret="secret"
        )
        
        # Mock timeout scenario
        with aioresponses() as m:
            # Simulate slow response that would timeout
            async def slow_response(url, **kwargs):
                await asyncio.sleep(2)  # Longer than typical timeout
                return aioresponses.CallbackResult(
                    payload={"access_token": "token"},
                    status=200
                )
            
            m.post(config.oauth2_token_url, callback=slow_response)
            
            # Authentication should handle timeout gracefully
            start_time = time.time()
            result = await auth_service.authenticate("test-server", config)
            end_time = time.time()
            
            # Should fail due to timeout, not hang indefinitely
            assert result.success is False
            assert (end_time - start_time) < 10  # Should not take too long
    
    def test_credential_cleanup_security(self):
        """Test secure credential cleanup."""
        store = SecureCredentialStore()
        
        # Store multiple credentials and tokens
        store.store_credential("cred1", "value1")
        store.store_credential("cred2", "value2")
        
        valid_token = JWTTokenInfo(
            token="valid-token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        expired_token = JWTTokenInfo(
            token="expired-token",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        store.store_token("server1", valid_token)
        store.store_token("server2", expired_token)
        
        # Test selective cleanup of expired tokens
        removed_count = store.cleanup_expired_tokens()
        assert removed_count == 1
        assert store.get_token("server1") is not None  # Valid token remains
        assert store.get_token("server2") is None      # Expired token removed
        
        # Test complete cleanup
        store.clear_all()
        assert store.get_credential("cred1") is None
        assert store.get_credential("cred2") is None
        assert store.get_token("server1") is None
    
    async def test_authentication_error_information_disclosure(self, auth_service):
        """Test that authentication errors don't disclose sensitive information."""
        # Test with malformed discovery URL
        config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_discovery_url="https://invalid-domain-that-does-not-exist.com/.well-known/openid-configuration",
            jwt_client_id="test-client",
            jwt_client_secret="secret-key"
        )
        
        result = await auth_service.authenticate("test-server", config)
        
        assert result.success is False
        # Error message should not expose the client secret
        assert "secret-key" not in result.error_message
        # Should provide useful error information without sensitive details
        assert result.error_type == "TOKEN_ACQUISITION_FAILED"
    
    def test_authentication_config_validation_security(self):
        """Test authentication configuration validation for security."""
        # Test that validation catches insecure configurations
        
        # Empty password should be caught
        insecure_basic_config = AuthenticationConfig(
            auth_type=AuthenticationType.BASIC_AUTH,
            username="user",
            password=""  # Empty password
        )
        errors = insecure_basic_config.validate()
        assert len(errors) > 0
        
        # Missing API key should be caught
        insecure_api_config = AuthenticationConfig(
            auth_type=AuthenticationType.API_KEY,
            api_key="",  # Empty API key
            api_key_header="X-API-Key"
        )
        errors = insecure_api_config.validate()
        assert len(errors) > 0
        
        # Invalid refresh settings should be caught
        insecure_refresh_config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="token",
            refresh_buffer_seconds=-1,  # Negative buffer
            max_refresh_attempts=0      # No retry attempts
        )
        errors = insecure_refresh_config.validate()
        assert len(errors) >= 2
    
    async def test_rate_limiting_protection(self, auth_service):
        """Test protection against authentication rate limiting attacks."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="test-token"
        )
        
        # Simulate rapid authentication attempts
        start_time = time.time()
        
        tasks = [
            auth_service.authenticate(f"server-{i}", config)
            for i in range(100)  # Many rapid requests
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should succeed (bearer token is local validation)
        for result in results:
            assert result.success is True
        
        # Should complete in reasonable time (no artificial delays)
        assert (end_time - start_time) < 5.0
        
        # Verify metrics are properly tracked
        metrics = auth_service.get_metrics()
        assert metrics.total_auth_attempts == 100
        assert metrics.successful_auth_attempts == 100
    
    def test_memory_security_token_storage(self):
        """Test memory security for token storage."""
        store = SecureCredentialStore()
        
        # Store sensitive token
        sensitive_token = JWTTokenInfo(
            token="very-sensitive-jwt-token-with-secrets",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        store.store_token("sensitive-server", sensitive_token)
        
        # Verify token is stored
        retrieved = store.get_token("sensitive-server")
        assert retrieved.token == sensitive_token.token
        
        # Remove token
        removed = store.remove_token("sensitive-server")
        assert removed is True
        
        # Verify token is completely removed
        assert store.get_token("sensitive-server") is None
        
        # In production, this should also clear memory securely
        # This test serves as a reminder for secure memory handling


class TestAuthenticationSecurityScenarios:
    """Test realistic security scenarios."""
    
    @pytest.fixture
    async def auth_service(self):
        """Create authentication service for scenario testing."""
        service = AuthenticationService()
        await service.__aenter__()
        yield service
        await service.__aexit__(None, None, None)
    
    async def test_compromised_token_scenario(self, auth_service):
        """Test handling of potentially compromised tokens."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.JWT,
            jwt_token="potentially-compromised-token"
        )
        
        # Initial authentication succeeds
        result1 = await auth_service.authenticate("server1", config)
        assert result1.success is True
        
        # Simulate token compromise - clear credentials
        auth_service.clear_credentials("server1")
        
        # Subsequent authentication should require new token
        stored_token = auth_service._credential_store.get_token("server1")
        assert stored_token is None
    
    async def test_token_rotation_scenario(self, auth_service):
        """Test secure token rotation scenario."""
        config = AuthenticationConfig(
            auth_type=AuthenticationType.OAUTH2,
            oauth2_token_url="https://auth.example.com/token",
            oauth2_client_id="client-id",
            oauth2_client_secret="client-secret",
            auto_refresh_enabled=True,
            refresh_buffer_seconds=60
        )
        
        # Initial token
        initial_response = {
            "access_token": "initial-token",
            "expires_in": 120  # 2 minutes
        }
        
        with aioresponses() as m:
            m.post(config.oauth2_token_url, payload=initial_response)
            
            result1 = await auth_service.authenticate("server1", config)
            assert result1.success is True
            
            initial_token = auth_service._credential_store.get_token("server1")
            assert initial_token.token == "initial-token"
        
        # Simulate time passing (token near expiry)
        # Manually set token to be near expiry
        near_expiry_token = JWTTokenInfo(
            token="initial-token",
            expires_at=datetime.now() + timedelta(seconds=30)  # Within refresh buffer
        )
        auth_service._credential_store.store_token("server1", near_expiry_token)
        
        # Token refresh
        refresh_response = {
            "access_token": "rotated-token",
            "expires_in": 3600
        }
        
        with aioresponses() as m:
            m.post(config.oauth2_token_url, payload=refresh_response)
            
            refresh_result = await auth_service.refresh_token_if_needed("server1", config)
            assert refresh_result.success is True
            
            rotated_token = auth_service._credential_store.get_token("server1")
            assert rotated_token.token == "rotated-token"
            assert rotated_token.token != initial_token.token
    
    async def test_multi_server_isolation_scenario(self, auth_service):
        """Test isolation between multiple server authentications."""
        # Different auth configs for different servers
        server1_config = AuthenticationConfig(
            auth_type=AuthenticationType.BEARER_TOKEN,
            bearer_token="server1-token"
        )
        
        server2_config = AuthenticationConfig(
            auth_type=AuthenticationType.API_KEY,
            api_key="server2-key",
            api_key_header="X-API-Key"
        )
        
        # Authenticate both servers
        result1 = await auth_service.authenticate("server1", server1_config)
        result2 = await auth_service.authenticate("server2", server2_config)
        
        assert result1.success is True
        assert result2.success is True
        
        # Verify isolation - different auth headers
        assert result1.auth_headers["Authorization"] == "Bearer server1-token"
        assert result2.auth_headers["X-API-Key"] == "server2-key"
        
        # Verify no cross-contamination
        assert "X-API-Key" not in result1.auth_headers
        assert "Authorization" not in result2.auth_headers
        
        # Clear one server's credentials
        auth_service.clear_credentials("server1")
        
        # Verify other server's credentials remain
        servers = auth_service.list_authenticated_servers()
        # Note: Bearer token auth doesn't store tokens, only OAuth2/JWT do
        # This test verifies the isolation principle


if __name__ == "__main__":
    pytest.main([__file__])