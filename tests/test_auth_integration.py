"""
Integration tests for authentication services.

Tests basic functionality without requiring actual AWS Cognito resources.
"""

import pytest
import json
from unittest.mock import Mock, patch
from services.auth_service import (
    CognitoAuthenticator,
    TokenValidator,
    JWKSManager,
    AuthenticationMiddleware,
    AuthenticationError,
    create_cognito_authenticator_from_config,
    create_token_validator_from_config
)


class TestAuthenticationIntegration:
    """Integration tests for authentication components."""
    
    def test_cognito_authenticator_initialization(self):
        """Test CognitoAuthenticator can be initialized."""
        authenticator = CognitoAuthenticator(
            user_pool_id="us-east-1_testpool",
            client_id="test_client_id",
            region="us-east-1"
        )
        
        assert authenticator.user_pool_id == "us-east-1_testpool"
        assert authenticator.client_id == "test_client_id"
        assert authenticator.region == "us-east-1"
        assert authenticator.cognito_client is not None
    
    def test_token_validator_initialization(self):
        """Test TokenValidator can be initialized."""
        config = {
            'user_pool_id': 'us-east-1_testpool',
            'client_id': 'test_client_id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        }
        
        validator = TokenValidator(config)
        
        assert validator.user_pool_id == 'us-east-1_testpool'
        assert validator.client_id == 'test_client_id'
        assert validator.region == 'us-east-1'
        assert validator.discovery_url == config['discovery_url']
    
    def test_jwks_manager_initialization(self):
        """Test JWKSManager can be initialized."""
        discovery_url = 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        
        manager = JWKSManager(discovery_url)
        
        assert manager.discovery_url == discovery_url
        assert manager.cache_ttl == 3600
        assert manager.jwks_keys == {}
    
    def test_authentication_middleware_initialization(self):
        """Test AuthenticationMiddleware can be initialized."""
        mock_validator = Mock()
        
        middleware = AuthenticationMiddleware(mock_validator)
        
        assert middleware.token_validator == mock_validator
    
    def test_authentication_error_creation(self):
        """Test AuthenticationError can be created and raised."""
        error = AuthenticationError(
            error_type="TEST_ERROR",
            error_code="TEST_CODE",
            message="Test message",
            details="Test details",
            suggested_action="Test action"
        )
        
        assert error.error_type == "TEST_ERROR"
        assert error.error_code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.details == "Test details"
        assert error.suggested_action == "Test action"
        
        # Test that it can be raised and caught
        with pytest.raises(AuthenticationError) as exc_info:
            raise error
        
        caught_error = exc_info.value
        assert caught_error.error_type == "TEST_ERROR"
        assert caught_error.error_code == "TEST_CODE"
    
    def test_config_utilities_with_valid_config(self, tmp_path):
        """Test configuration utility functions with valid config."""
        # Create test config file
        config_data = {
            'user_pool': {'user_pool_id': 'us-east-1_testpool'},
            'app_client': {'client_id': 'test_client_id'},
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        }
        
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Test authenticator creation
        authenticator = create_cognito_authenticator_from_config(str(config_file))
        assert isinstance(authenticator, CognitoAuthenticator)
        assert authenticator.user_pool_id == 'us-east-1_testpool'
        
        # Test validator creation
        validator = create_token_validator_from_config(str(config_file))
        assert isinstance(validator, TokenValidator)
        assert validator.user_pool_id == 'us-east-1_testpool'
    
    def test_srp_utilities(self):
        """Test SRP utility functions work correctly."""
        authenticator = CognitoAuthenticator(
            user_pool_id="us-east-1_testpool",
            client_id="test_client_id",
            region="us-east-1"
        )
        
        # Test SRP 'a' generation
        srp_a, big_a = authenticator._generate_srp_a()
        assert isinstance(srp_a, int)
        assert isinstance(big_a, str)
        assert srp_a > 0
        assert len(big_a) > 0
        
        # Test password claim calculation
        claim = authenticator._calculate_password_claim(
            username="testuser",
            password="testpass",
            srp_a=srp_a,
            srp_b="ABCDEF123456",
            salt="789ABC",
            secret_block="secret123"
        )
        
        assert 'signature' in claim
        assert 'timestamp' in claim
        assert isinstance(claim['signature'], str)
        assert isinstance(claim['timestamp'], str)
    
    def test_bearer_token_extraction(self):
        """Test Bearer token extraction utility."""
        middleware = AuthenticationMiddleware(Mock())
        
        # Test valid Bearer token
        token = middleware.extract_bearer_token('Bearer test_token_123')
        assert token == 'test_token_123'
        
        # Test invalid format
        token = middleware.extract_bearer_token('Basic dGVzdA==')
        assert token is None
        
        # Test empty token
        token = middleware.extract_bearer_token('Bearer ')
        assert token is None
        
        # Test missing Bearer prefix
        token = middleware.extract_bearer_token('test_token_123')
        assert token is None
    
    def test_error_response_creation(self):
        """Test error response creation utility."""
        middleware = AuthenticationMiddleware(Mock())
        
        response = middleware.create_error_response(
            "TEST_ERROR",
            "Test error message",
            "Test error details"
        )
        
        assert response.status_code == 401
        
        # Parse response content
        response_data = json.loads(response.body.decode())
        assert response_data['error']['type'] == 'TEST_ERROR'
        assert response_data['error']['message'] == 'Test error message'
        assert response_data['error']['details'] == 'Test error details'
        assert 'timestamp' in response_data['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])