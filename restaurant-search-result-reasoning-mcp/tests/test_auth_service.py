"""
Unit tests for authentication services.
Adapted for restaurant reasoning MCP server.

Tests SRP authentication flow, JWT token validation, JWKS key management,
and error handling scenarios.
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import jwt
from botocore.exceptions import ClientError

from services.auth_service import (
    CognitoAuthenticator,
    TokenValidator,
    JWKSManager,
    AuthenticationTokens,
    AuthenticationError,
    JWTClaims,
    UserContext
)


class TestCognitoAuthenticator:
    """Test cases for CognitoAuthenticator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.user_pool_id = "us-east-1_testpool"
        self.client_id = "test_client_id"
        self.region = "us-east-1"
        
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.user_pool_id,
            client_id=self.client_id,
            region=self.region
        )
    
    @patch('boto3.client')
    def test_authenticate_user_success(self, mock_boto_client):
        """Test successful SRP authentication flow."""
        # Mock Cognito client responses
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock initiate_auth response
        mock_client.initiate_auth.return_value = {
            'ChallengeName': 'PASSWORD_VERIFIER',
            'Session': 'test_session',
            'ChallengeParameters': {
                'SRP_B': 'test_srp_b_value',
                'SALT': 'test_salt_value',
                'SECRET_BLOCK': 'test_secret_block'
            }
        }
        
        # Mock respond_to_auth_challenge response
        mock_client.respond_to_auth_challenge.return_value = {
            'AuthenticationResult': {
                'IdToken': 'test_id_token',
                'AccessToken': 'test_access_token',
                'RefreshToken': 'test_refresh_token',
                'ExpiresIn': 3600,
                'TokenType': 'Bearer'
            }
        }
        
        # Test authentication
        tokens = self.authenticator.authenticate_user('testuser', 'testpass')
        
        # Verify results
        assert isinstance(tokens, AuthenticationTokens)
        assert tokens.id_token == 'test_id_token'
        assert tokens.access_token == 'test_access_token'
        assert tokens.refresh_token == 'test_refresh_token'
        assert tokens.expires_in == 3600
        assert tokens.token_type == 'Bearer'
        
        # Verify Cognito client calls
        mock_client.initiate_auth.assert_called_once()
        mock_client.respond_to_auth_challenge.assert_called_once()
    
    @patch('boto3.client')
    def test_authenticate_user_invalid_credentials(self, mock_boto_client):
        """Test authentication with invalid credentials."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock Cognito error response
        error_response = {
            'Error': {
                'Code': 'NotAuthorizedException',
                'Message': 'Incorrect username or password.'
            }
        }
        mock_client.initiate_auth.side_effect = ClientError(error_response, 'InitiateAuth')
        
        # Test authentication failure
        with pytest.raises(AuthenticationError) as exc_info:
            self.authenticator.authenticate_user('testuser', 'wrongpass')
        
        error = exc_info.value
        assert error.error_type == "AUTHENTICATION_FAILED"
        assert error.error_code == "NotAuthorizedException"
        assert "Invalid username or password" in error.message
    
    @patch('boto3.client')
    def test_authenticate_user_user_not_found(self, mock_boto_client):
        """Test authentication with non-existent user."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock user not found error
        error_response = {
            'Error': {
                'Code': 'UserNotFoundException',
                'Message': 'User does not exist.'
            }
        }
        mock_client.initiate_auth.side_effect = ClientError(error_response, 'InitiateAuth')
        
        # Test authentication failure
        with pytest.raises(AuthenticationError) as exc_info:
            self.authenticator.authenticate_user('nonexistent', 'password')
        
        error = exc_info.value
        assert error.error_type == "USER_NOT_FOUND"
        assert error.error_code == "UserNotFoundException"


class TestTokenValidator:
    """Test cases for TokenValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cognito_config = {
            'user_pool_id': 'us-east-1_testpool',
            'client_id': 'test_client_id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        }
        
        self.validator = TokenValidator(self.cognito_config)
    
    def create_test_token(self, claims: dict = None, algorithm: str = 'RS256') -> str:
        """Create a test JWT token."""
        default_claims = {
            'sub': 'user123',
            'username': 'testuser',
            'email': 'test@example.com',
            'client_id': self.cognito_config['client_id'],
            'token_use': 'access',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            'iat': int(datetime.now(timezone.utc).timestamp()),
            'iss': f"https://cognito-idp.{self.cognito_config['region']}.amazonaws.com/{self.cognito_config['user_pool_id']}",
            'aud': self.cognito_config['client_id']
        }
        
        if claims:
            default_claims.update(claims)
        
        # For testing, use HS256 with a secret key
        if algorithm == 'HS256':
            return jwt.encode(default_claims, 'test_secret', algorithm='HS256')
        else:
            # For RS256, we'll mock the validation process
            return jwt.encode(default_claims, 'test_secret', algorithm='HS256')
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_success(self):
        """Test successful JWT token validation."""
        # Create test token
        test_token = self.create_test_token()
        
        # Mock JWKS key retrieval
        with patch.object(self.validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'test_secret'
            
            # Mock JWT decode to return expected claims
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'sub': 'user123',
                    'username': 'testuser',
                    'email': 'test@example.com',
                    'client_id': self.cognito_config['client_id'],
                    'token_use': 'access',
                    'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                    'iat': int(datetime.now(timezone.utc).timestamp()),
                    'iss': f"https://cognito-idp.{self.cognito_config['region']}.amazonaws.com/{self.cognito_config['user_pool_id']}",
                    'aud': self.cognito_config['client_id']
                }
                
                # Mock get_unverified_header
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'test_kid'}
                    
                    # Test token validation
                    claims = await self.validator.validate_jwt_token(test_token)
                    
                    # Verify results
                    assert isinstance(claims, JWTClaims)
                    assert claims.user_id == 'user123'
                    assert claims.username == 'testuser'
                    assert claims.email == 'test@example.com'
                    assert claims.token_use == 'access'
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_missing_kid(self):
        """Test token validation with missing key ID."""
        test_token = self.create_test_token()
        
        # Mock get_unverified_header to return header without kid
        with patch('jwt.get_unverified_header') as mock_header:
            mock_header.return_value = {}  # No 'kid' field
            
            # Test token validation failure
            with pytest.raises(AuthenticationError) as exc_info:
                await self.validator.validate_jwt_token(test_token)
            
            error = exc_info.value
            assert error.error_type == "TOKEN_VALIDATION_ERROR"
            assert error.error_code == "MISSING_KEY_ID"
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_expired(self):
        """Test token validation with expired token."""
        # Create expired token
        expired_claims = {
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        test_token = self.create_test_token(expired_claims)
        
        # Mock JWKS key retrieval
        with patch.object(self.validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'test_secret'
            
            # Mock get_unverified_header
            with patch('jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {'kid': 'test_kid'}
                
                # Mock JWT decode to raise ExpiredSignatureError
                with patch('jwt.decode') as mock_decode:
                    mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
                    
                    # Test token validation failure
                    with pytest.raises(AuthenticationError) as exc_info:
                        await self.validator.validate_jwt_token(test_token)
                    
                    error = exc_info.value
                    assert error.error_type == "TOKEN_EXPIRED"
                    assert error.error_code == "EXPIRED_SIGNATURE"
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_invalid_signature(self):
        """Test token validation with invalid signature."""
        test_token = self.create_test_token()
        
        # Mock JWKS key retrieval
        with patch.object(self.validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'wrong_secret'
            
            # Mock get_unverified_header
            with patch('jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {'kid': 'test_kid'}
                
                # Mock JWT decode to raise InvalidSignatureError
                with patch('jwt.decode') as mock_decode:
                    mock_decode.side_effect = jwt.InvalidSignatureError("Signature verification failed")
                    
                    # Test token validation failure
                    with pytest.raises(AuthenticationError) as exc_info:
                        await self.validator.validate_jwt_token(test_token)
                    
                    error = exc_info.value
                    assert error.error_type == "TOKEN_VALIDATION_ERROR"
                    assert error.error_code == "INVALID_SIGNATURE"
    
    def test_extract_claims(self):
        """Test JWT claims extraction without verification."""
        test_claims = {
            'sub': 'user123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        test_token = self.create_test_token(test_claims, algorithm='HS256')
        
        # Test claims extraction
        extracted_claims = self.validator.extract_claims(test_token)
        
        # Verify results
        assert extracted_claims['sub'] == 'user123'
        assert extracted_claims['username'] == 'testuser'
        assert extracted_claims['email'] == 'test@example.com'
    
    def test_is_token_expired_true(self):
        """Test expired token detection."""
        # Create expired token
        expired_claims = {
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        expired_token = self.create_test_token(expired_claims, algorithm='HS256')
        
        # Test expiration check
        assert self.validator.is_token_expired(expired_token) is True
    
    def test_is_token_expired_false(self):
        """Test valid token expiration check."""
        # Create valid token
        valid_claims = {
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        valid_token = self.create_test_token(valid_claims, algorithm='HS256')
        
        # Test expiration check
        assert self.validator.is_token_expired(valid_token) is False
    
    def test_is_token_expired_malformed(self):
        """Test expiration check with malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        
        # Test expiration check (should return True for malformed tokens)
        assert self.validator.is_token_expired(malformed_token) is True


class TestJWKSManager:
    """Test cases for JWKSManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.discovery_url = 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        self.jwks_manager = JWKSManager(self.discovery_url, cache_ttl=3600)
    
    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_get_key_success(self, mock_get):
        """Test successful JWKS key retrieval."""
        # Mock JWKS response
        jwks_response = Mock()
        jwks_response.status_code = 200
        jwks_response.raise_for_status.return_value = None
        jwks_response.json.return_value = {
            'keys': [
                {
                    'kid': 'test_kid_1',
                    'kty': 'RSA',
                    'use': 'sig',
                    'n': 'test_n_value',
                    'e': 'AQAB'
                }
            ]
        }
        
        mock_get.return_value = jwks_response
        
        # Mock RSAAlgorithm.from_jwk
        with patch('jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
            mock_from_jwk.return_value = 'mock_public_key'
            
            # Test key retrieval
            key = await self.jwks_manager.get_key('test_kid_1')
            
            # Verify result
            assert key == 'mock_public_key'
    
    @pytest.mark.asyncio
    async def test_get_key_not_found(self):
        """Test key retrieval with missing key ID."""
        # Set up empty cache
        self.jwks_manager.keys_cache = {}
        
        # Mock _refresh_cache to not add the requested key
        with patch.object(self.jwks_manager, '_refresh_cache') as mock_refresh:
            mock_refresh.return_value = None
            
            # Test key retrieval failure
            with pytest.raises(AuthenticationError) as exc_info:
                await self.jwks_manager.get_key('missing_kid')
            
            error = exc_info.value
            assert error.error_type == "KEY_NOT_FOUND"
            assert error.error_code == "SIGNING_KEY_NOT_FOUND"


class TestAuthenticationIntegration:
    """Integration tests for authentication services in reasoning server context."""
    
    def setup_method(self):
        """Set up test fixtures for reasoning server."""
        self.cognito_config = {
            'user_pool_id': 'us-east-1_reasoning_pool',
            'client_id': 'reasoning_client_id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_reasoning_pool/.well-known/openid-configuration'
        }
    
    @patch('boto3.client')
    def test_reasoning_server_authentication_flow(self, mock_boto_client):
        """Test complete authentication flow for reasoning server."""
        # Mock Cognito client
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock successful authentication
        mock_client.initiate_auth.return_value = {
            'ChallengeName': 'PASSWORD_VERIFIER',
            'Session': 'reasoning_session',
            'ChallengeParameters': {
                'SRP_B': 'reasoning_srp_b',
                'SALT': 'reasoning_salt',
                'SECRET_BLOCK': 'reasoning_secret'
            }
        }
        
        mock_client.respond_to_auth_challenge.return_value = {
            'AuthenticationResult': {
                'IdToken': 'reasoning_id_token',
                'AccessToken': 'reasoning_access_token',
                'RefreshToken': 'reasoning_refresh_token',
                'ExpiresIn': 3600,
                'TokenType': 'Bearer'
            }
        }
        
        # Test authentication for reasoning server
        authenticator = CognitoAuthenticator(
            user_pool_id=self.cognito_config['user_pool_id'],
            client_id=self.cognito_config['client_id'],
            region=self.cognito_config['region']
        )
        
        tokens = authenticator.authenticate_user('reasoning_user', 'reasoning_pass')
        
        # Verify reasoning server specific tokens
        assert tokens.id_token == 'reasoning_id_token'
        assert tokens.access_token == 'reasoning_access_token'
        assert tokens.refresh_token == 'reasoning_refresh_token'
    
    @pytest.mark.asyncio
    async def test_reasoning_server_jwt_validation(self):
        """Test JWT validation for reasoning server tokens."""
        validator = TokenValidator(self.cognito_config)
        
        # Create reasoning server specific test token
        test_token = jwt.encode({
            'sub': 'reasoning_user_123',
            'username': 'reasoning_user',
            'email': 'reasoning@example.com',
            'client_id': self.cognito_config['client_id'],
            'token_use': 'access',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            'iat': int(datetime.now(timezone.utc).timestamp()),
            'iss': f"https://cognito-idp.{self.cognito_config['region']}.amazonaws.com/{self.cognito_config['user_pool_id']}",
            'aud': self.cognito_config['client_id']
        }, 'test_secret', algorithm='HS256')
        
        # Mock validation components
        with patch.object(validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'test_secret'
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'sub': 'reasoning_user_123',
                    'username': 'reasoning_user',
                    'email': 'reasoning@example.com',
                    'client_id': self.cognito_config['client_id'],
                    'token_use': 'access',
                    'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                    'iat': int(datetime.now(timezone.utc).timestamp()),
                    'iss': f"https://cognito-idp.{self.cognito_config['region']}.amazonaws.com/{self.cognito_config['user_pool_id']}",
                    'aud': self.cognito_config['client_id']
                }
                
                with patch('jwt.get_unverified_header') as mock_header:
                    mock_header.return_value = {'kid': 'reasoning_kid'}
                    
                    # Test token validation for reasoning server
                    claims = await validator.validate_jwt_token(test_token)
                    
                    # Verify reasoning server specific claims
                    assert claims.user_id == 'reasoning_user_123'
                    assert claims.username == 'reasoning_user'
                    assert claims.email == 'reasoning@example.com'
                    assert claims.token_use == 'access'


class TestReasoningServerErrorHandling:
    """Test error handling scenarios specific to reasoning server."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cognito_config = {
            'user_pool_id': 'us-east-1_reasoning_pool',
            'client_id': 'reasoning_client_id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_reasoning_pool/.well-known/openid-configuration'
        }
    
    @pytest.mark.asyncio
    async def test_reasoning_server_expired_token_handling(self):
        """Test handling of expired tokens in reasoning server context."""
        validator = TokenValidator(self.cognito_config)
        
        # Create expired token
        expired_token = jwt.encode({
            'sub': 'reasoning_user_123',
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            'client_id': self.cognito_config['client_id'],
            'token_use': 'access'
        }, 'test_secret', algorithm='HS256')
        
        # Mock components for expired token test
        with patch.object(validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'test_secret'
            
            with patch('jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {'kid': 'reasoning_kid'}
                
                with patch('jwt.decode') as mock_decode:
                    mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
                    
                    # Test expired token handling
                    with pytest.raises(AuthenticationError) as exc_info:
                        await validator.validate_jwt_token(expired_token)
                    
                    error = exc_info.value
                    assert error.error_type == "TOKEN_EXPIRED"
                    assert error.error_code == "EXPIRED_SIGNATURE"
                    assert "JWT token has expired" in error.message
    
    @pytest.mark.asyncio
    async def test_reasoning_server_invalid_signature_handling(self):
        """Test handling of invalid signatures in reasoning server context."""
        validator = TokenValidator(self.cognito_config)
        
        # Create test token
        test_token = jwt.encode({
            'sub': 'reasoning_user_123',
            'client_id': self.cognito_config['client_id'],
            'token_use': 'access'
        }, 'test_secret', algorithm='HS256')
        
        # Mock components for invalid signature test
        with patch.object(validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'wrong_secret'
            
            with patch('jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {'kid': 'reasoning_kid'}
                
                with patch('jwt.decode') as mock_decode:
                    mock_decode.side_effect = jwt.InvalidSignatureError("Signature verification failed")
                    
                    # Test invalid signature handling
                    with pytest.raises(AuthenticationError) as exc_info:
                        await validator.validate_jwt_token(test_token)
                    
                    error = exc_info.value
                    assert error.error_type == "TOKEN_VALIDATION_ERROR"
                    assert error.error_code == "INVALID_SIGNATURE"
                    assert "JWT token signature verification failed" in error.message


# Configuration tests would go here if utility functions were available
# The reasoning server auth_service doesn't include the utility functions
# create_cognito_authenticator_from_config and create_token_validator_from_config


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])