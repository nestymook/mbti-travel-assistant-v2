"""
Unit tests for authentication services.

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
    AuthenticationMiddleware,
    AuthenticationTokens,
    AuthenticationError,
    JWTClaims,
    UserContext,
    create_cognito_authenticator_from_config,
    create_token_validator_from_config,
    test_authentication_flow
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
    
    @patch('boto3.client')
    def test_authenticate_user_password_change_required(self, mock_boto_client):
        """Test authentication when password change is required."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock successful initiate_auth
        mock_client.initiate_auth.return_value = {
            'ChallengeName': 'PASSWORD_VERIFIER',
            'Session': 'test_session',
            'ChallengeParameters': {
                'SRP_B': 'test_srp_b_value',
                'SALT': 'test_salt_value',
                'SECRET_BLOCK': 'test_secret_block'
            }
        }
        
        # Mock NEW_PASSWORD_REQUIRED challenge
        mock_client.respond_to_auth_challenge.return_value = {
            'ChallengeName': 'NEW_PASSWORD_REQUIRED',
            'Session': 'test_session'
        }
        
        # Test password change required
        with pytest.raises(AuthenticationError) as exc_info:
            self.authenticator.authenticate_user('testuser', 'temppass')
        
        error = exc_info.value
        assert error.error_type == "PASSWORD_CHANGE_REQUIRED"
        assert error.error_code == "NEW_PASSWORD_REQUIRED"
    
    @patch('boto3.client')
    def test_refresh_token_success(self, mock_boto_client):
        """Test successful token refresh."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock refresh token response
        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'IdToken': 'new_id_token',
                'AccessToken': 'new_access_token',
                'ExpiresIn': 3600,
                'TokenType': 'Bearer'
            }
        }
        
        # Test token refresh
        tokens = self.authenticator.refresh_token('test_refresh_token')
        
        # Verify results
        assert tokens.id_token == 'new_id_token'
        assert tokens.access_token == 'new_access_token'
        assert tokens.refresh_token == 'test_refresh_token'  # Should remain same
        assert tokens.expires_in == 3600
    
    @patch('boto3.client')
    def test_refresh_token_invalid(self, mock_boto_client):
        """Test token refresh with invalid refresh token."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock invalid refresh token error
        error_response = {
            'Error': {
                'Code': 'NotAuthorizedException',
                'Message': 'Refresh Token has been revoked'
            }
        }
        mock_client.initiate_auth.side_effect = ClientError(error_response, 'InitiateAuth')
        
        # Test refresh failure
        with pytest.raises(AuthenticationError) as exc_info:
            self.authenticator.refresh_token('invalid_refresh_token')
        
        error = exc_info.value
        assert error.error_type == "TOKEN_REFRESH_FAILED"
        assert error.error_code == "NotAuthorizedException"
    
    @patch('boto3.client')
    def test_validate_user_session_success(self, mock_boto_client):
        """Test successful user session validation."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock get_user response
        mock_client.get_user.return_value = {
            'Username': 'testuser',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'email_verified', 'Value': 'true'}
            ]
        }
        
        # Create a test access token
        test_token = jwt.encode({
            'sub': 'user123',
            'username': 'testuser',
            'client_id': self.client_id,
            'token_use': 'access',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            'iat': int(datetime.now(timezone.utc).timestamp()),
            'iss': f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}',
            'aud': self.client_id
        }, 'secret', algorithm='HS256')
        
        # Test session validation
        user_context = self.authenticator.validate_user_session(test_token)
        
        # Verify results
        assert isinstance(user_context, UserContext)
        assert user_context.user_id == 'user123'
        assert user_context.username == 'testuser'
        assert user_context.email == 'test@example.com'
        assert user_context.authenticated is True
    
    @patch('boto3.client')
    def test_validate_user_session_invalid_token(self, mock_boto_client):
        """Test session validation with invalid access token."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock invalid token error
        error_response = {
            'Error': {
                'Code': 'NotAuthorizedException',
                'Message': 'Access Token has been revoked'
            }
        }
        mock_client.get_user.side_effect = ClientError(error_response, 'GetUser')
        
        # Test session validation failure
        with pytest.raises(AuthenticationError) as exc_info:
            self.authenticator.validate_user_session('invalid_token')
        
        error = exc_info.value
        assert error.error_type == "SESSION_VALIDATION_FAILED"
        assert error.error_code == "NotAuthorizedException"
    
    def test_generate_srp_a(self):
        """Test SRP 'a' value generation."""
        srp_a, big_a = self.authenticator._generate_srp_a()
        
        # Verify types and basic properties
        assert isinstance(srp_a, int)
        assert isinstance(big_a, str)
        assert srp_a > 0
        assert len(big_a) > 0
        assert big_a.isalnum()  # Should be hex string
    
    def test_calculate_password_claim(self):
        """Test SRP password claim calculation."""
        # Test with sample values
        username = "testuser"
        password = "testpass"
        srp_a = 12345
        srp_b = "ABCDEF123456"
        salt = "789ABC"
        secret_block = "secret123"
        
        claim = self.authenticator._calculate_password_claim(
            username, password, srp_a, srp_b, salt, secret_block
        )
        
        # Verify claim structure
        assert 'signature' in claim
        assert 'timestamp' in claim
        assert isinstance(claim['signature'], str)
        assert isinstance(claim['timestamp'], str)
        
        # Verify timestamp format
        datetime.strptime(claim['timestamp'], '%a %b %d %H:%M:%S UTC %Y')


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
    async def test_validate_jwt_token_invalid_audience(self):
        """Test token validation with invalid audience."""
        test_token = self.create_test_token()
        
        # Mock JWKS key retrieval
        with patch.object(self.validator, 'get_signing_key') as mock_get_key:
            mock_get_key.return_value = 'test_secret'
            
            # Mock get_unverified_header
            with patch('jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {'kid': 'test_kid'}
                
                # Mock JWT decode to raise InvalidAudienceError
                with patch('jwt.decode') as mock_decode:
                    mock_decode.side_effect = jwt.InvalidAudienceError("Invalid audience")
                    
                    # Test token validation failure
                    with pytest.raises(AuthenticationError) as exc_info:
                        await self.validator.validate_jwt_token(test_token)
                    
                    error = exc_info.value
                    assert error.error_type == "TOKEN_VALIDATION_ERROR"
                    assert error.error_code == "INVALID_AUDIENCE"
    
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
    async def test_get_jwks_keys_success(self, mock_get):
        """Test successful JWKS keys retrieval."""
        # Mock OIDC configuration response
        oidc_response = Mock()
        oidc_response.status_code = 200
        oidc_response.raise_for_status.return_value = None
        oidc_response.json.return_value = {
            'jwks_uri': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/jwks.json'
        }
        
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
        
        # Configure mock to return different responses for different URLs
        def mock_get_side_effect(url, **kwargs):
            if 'openid-configuration' in url:
                return oidc_response
            elif 'jwks.json' in url:
                return jwks_response
            else:
                raise ValueError(f"Unexpected URL: {url}")
        
        mock_get.side_effect = mock_get_side_effect
        
        # Mock RSAAlgorithm.from_jwk
        with patch('jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
            mock_from_jwk.return_value = 'mock_public_key'
            
            # Test JWKS retrieval
            keys = await self.jwks_manager.get_jwks_keys()
            
            # Verify results
            assert 'test_kid_1' in keys
            assert keys['test_kid_1'] == 'mock_public_key'
    
    @pytest.mark.asyncio
    @patch('requests.get')
    async def test_refresh_jwks_cache_network_error(self, mock_get):
        """Test JWKS cache refresh with network error."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        # Test cache refresh failure
        with pytest.raises(AuthenticationError) as exc_info:
            await self.jwks_manager.refresh_jwks_cache()
        
        error = exc_info.value
        assert error.error_type == "JWKS_PROCESSING_ERROR"
        assert error.error_code == "PROCESSING_ERROR"
    
    def test_get_signing_key_for_kid_success(self):
        """Test successful signing key retrieval."""
        # Set up cache with test key
        self.jwks_manager.jwks_keys = {'test_kid': 'test_public_key'}
        
        # Test key retrieval
        key = self.jwks_manager.get_signing_key_for_kid('test_kid')
        
        # Verify result
        assert key == 'test_public_key'
    
    def test_get_signing_key_for_kid_not_found(self):
        """Test signing key retrieval with missing key ID."""
        # Set up empty cache
        self.jwks_manager.jwks_keys = {}
        
        # Test key retrieval failure
        with pytest.raises(AuthenticationError) as exc_info:
            self.jwks_manager.get_signing_key_for_kid('missing_kid')
        
        error = exc_info.value
        assert error.error_type == "KEY_NOT_FOUND"
        assert error.error_code == "SIGNING_KEY_NOT_FOUND"
    
    def test_is_cache_expired_empty(self):
        """Test cache expiration check with empty cache."""
        # Test with empty cache
        assert self.jwks_manager.is_cache_expired() is True
    
    def test_is_cache_expired_valid(self):
        """Test cache expiration check with valid cache."""
        # Set up valid cache
        self.jwks_manager.jwks_keys = {'test_kid': 'test_key'}
        self.jwks_manager.cache_timestamp = datetime.now(timezone.utc).timestamp()
        
        # Test cache validity
        assert self.jwks_manager.is_cache_expired() is False
    
    def test_is_cache_expired_old(self):
        """Test cache expiration check with expired cache."""
        # Set up expired cache
        self.jwks_manager.jwks_keys = {'test_kid': 'test_key'}
        self.jwks_manager.cache_timestamp = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).timestamp()
        
        # Test cache expiration
        assert self.jwks_manager.is_cache_expired() is True


class TestAuthenticationMiddleware:
    """Test cases for AuthenticationMiddleware class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_validator = Mock(spec=TokenValidator)
        self.middleware = AuthenticationMiddleware(self.mock_validator)
    
    @pytest.mark.asyncio
    async def test_middleware_success(self):
        """Test successful authentication middleware processing."""
        # Mock request and response
        mock_request = Mock()
        mock_request.url.path = '/api/search'
        mock_request.headers = {'Authorization': 'Bearer test_token'}
        mock_request.state = Mock()
        
        mock_response = Mock()
        
        async def mock_call_next(request):
            return mock_response
        
        # Mock token validation
        test_claims = JWTClaims(
            user_id='user123',
            username='testuser',
            email='test@example.com',
            client_id='test_client',
            token_use='access',
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss='test_issuer',
            aud='test_audience'
        )
        self.mock_validator.validate_jwt_token.return_value = test_claims
        
        # Test middleware processing
        response = await self.middleware(mock_request, mock_call_next)
        
        # Verify results
        assert response == mock_response
        assert hasattr(mock_request.state, 'user_context')
        assert mock_request.state.user_context.user_id == 'user123'
        assert mock_request.state.user_context.authenticated is True
    
    @pytest.mark.asyncio
    async def test_middleware_health_check_bypass(self):
        """Test middleware bypass for health check endpoints."""
        # Mock health check request
        mock_request = Mock()
        mock_request.url.path = '/health'
        
        mock_response = Mock()
        
        async def mock_call_next(request):
            return mock_response
        
        # Test middleware processing (should bypass authentication)
        response = await self.middleware(mock_request, mock_call_next)
        
        # Verify results
        assert response == mock_response
        # Validator should not be called
        self.mock_validator.validate_jwt_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_middleware_missing_authorization(self):
        """Test middleware with missing Authorization header."""
        # Mock request without Authorization header
        mock_request = Mock()
        mock_request.url.path = '/api/search'
        mock_request.headers = {}
        
        async def mock_call_next(request):
            return Mock()
        
        # Test middleware processing
        response = await self.middleware(mock_request, mock_call_next)
        
        # Verify error response
        assert response.status_code == 401
        assert 'error' in response.body.decode()
    
    @pytest.mark.asyncio
    async def test_middleware_invalid_token_format(self):
        """Test middleware with invalid token format."""
        # Mock request with invalid Authorization header
        mock_request = Mock()
        mock_request.url.path = '/api/search'
        mock_request.headers = {'Authorization': 'Invalid token_format'}
        
        async def mock_call_next(request):
            return Mock()
        
        # Test middleware processing
        response = await self.middleware(mock_request, mock_call_next)
        
        # Verify error response
        assert response.status_code == 401
        assert 'error' in response.body.decode()
    
    def test_extract_bearer_token_success(self):
        """Test successful Bearer token extraction."""
        auth_header = 'Bearer test_token_value'
        
        token = self.middleware.extract_bearer_token(auth_header)
        
        assert token == 'test_token_value'
    
    def test_extract_bearer_token_invalid_format(self):
        """Test Bearer token extraction with invalid format."""
        auth_header = 'Basic dGVzdDp0ZXN0'
        
        token = self.middleware.extract_bearer_token(auth_header)
        
        assert token is None
    
    def test_extract_bearer_token_empty(self):
        """Test Bearer token extraction with empty token."""
        auth_header = 'Bearer '
        
        token = self.middleware.extract_bearer_token(auth_header)
        
        assert token is None
    
    def test_create_error_response(self):
        """Test error response creation."""
        response = self.middleware.create_error_response(
            "TEST_ERROR",
            "Test error message",
            "Test error details"
        )
        
        # Verify response structure
        assert response.status_code == 401
        response_data = json.loads(response.body.decode())
        assert response_data['error']['type'] == 'TEST_ERROR'
        assert response_data['error']['message'] == 'Test error message'
        assert response_data['error']['details'] == 'Test error details'


class TestConfigurationUtilities:
    """Test cases for configuration utility functions."""
    
    def test_create_cognito_authenticator_from_config_success(self, tmp_path):
        """Test successful CognitoAuthenticator creation from config."""
        # Create test config file
        config_data = {
            'user_pool': {'user_pool_id': 'us-east-1_testpool'},
            'app_client': {'client_id': 'test_client_id'},
            'region': 'us-east-1'
        }
        
        config_file = tmp_path / "test_cognito_config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Test authenticator creation
        authenticator = create_cognito_authenticator_from_config(str(config_file))
        
        # Verify results
        assert isinstance(authenticator, CognitoAuthenticator)
        assert authenticator.user_pool_id == 'us-east-1_testpool'
        assert authenticator.client_id == 'test_client_id'
        assert authenticator.region == 'us-east-1'
    
    def test_create_cognito_authenticator_from_config_missing_file(self):
        """Test CognitoAuthenticator creation with missing config file."""
        with pytest.raises(AuthenticationError) as exc_info:
            create_cognito_authenticator_from_config('nonexistent_config.json')
        
        error = exc_info.value
        assert error.error_type == "CONFIG_ERROR"
        assert error.error_code == "CONFIG_FILE_NOT_FOUND"
    
    def test_create_cognito_authenticator_from_config_missing_key(self, tmp_path):
        """Test CognitoAuthenticator creation with missing config key."""
        # Create incomplete config file
        config_data = {
            'user_pool': {'user_pool_id': 'us-east-1_testpool'},
            'region': 'us-east-1'
            # Missing app_client
        }
        
        config_file = tmp_path / "incomplete_config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Test authenticator creation failure
        with pytest.raises(AuthenticationError) as exc_info:
            create_cognito_authenticator_from_config(str(config_file))
        
        error = exc_info.value
        assert error.error_type == "CONFIG_ERROR"
        assert error.error_code == "MISSING_CONFIG_KEY"
    
    def test_create_token_validator_from_config_success(self, tmp_path):
        """Test successful TokenValidator creation from config."""
        # Create test config file
        config_data = {
            'user_pool': {'user_pool_id': 'us-east-1_testpool'},
            'app_client': {'client_id': 'test_client_id'},
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool/.well-known/openid-configuration'
        }
        
        config_file = tmp_path / "test_cognito_config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Test validator creation
        validator = create_token_validator_from_config(str(config_file))
        
        # Verify results
        assert isinstance(validator, TokenValidator)
        assert validator.user_pool_id == 'us-east-1_testpool'
        assert validator.client_id == 'test_client_id'
        assert validator.region == 'us-east-1'


class TestAuthenticationFlow:
    """Test cases for complete authentication flow."""
    
    @pytest.mark.asyncio
    @patch('services.auth_service.create_cognito_authenticator_from_config')
    @patch('services.auth_service.create_token_validator_from_config')
    async def test_authentication_flow_success(self, mock_create_validator, mock_create_authenticator):
        """Test successful complete authentication flow."""
        # Mock authenticator
        mock_authenticator = Mock()
        mock_tokens = AuthenticationTokens(
            id_token='test_id_token',
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            expires_in=3600
        )
        mock_authenticator.authenticate_user.return_value = mock_tokens
        
        mock_user_context = UserContext(
            user_id='user123',
            username='testuser',
            email='test@example.com',
            authenticated=True,
            token_claims=Mock()
        )
        mock_authenticator.validate_user_session.return_value = mock_user_context
        
        mock_create_authenticator.return_value = mock_authenticator
        
        # Mock validator
        mock_validator = Mock()
        mock_claims = JWTClaims(
            user_id='user123',
            username='testuser',
            email='test@example.com',
            client_id='test_client',
            token_use='access',
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss='test_issuer',
            aud='test_audience'
        )
        mock_validator.validate_jwt_token.return_value = mock_claims
        
        mock_create_validator.return_value = mock_validator
        
        # Test complete authentication flow
        results = await test_authentication_flow('testuser', 'testpass', 'test_config.json')
        
        # Verify results
        assert results['authentication'] is True
        assert results['token_validation'] is True
        assert results['user_context'] is not None
        assert len(results['errors']) == 0
        assert results['tokens']['has_access_token'] is True
        assert results['claims']['user_id'] == 'user123'
    
    @pytest.mark.asyncio
    @patch('services.auth_service.create_cognito_authenticator_from_config')
    async def test_authentication_flow_auth_failure(self, mock_create_authenticator):
        """Test authentication flow with authentication failure."""
        # Mock authenticator to raise error
        mock_authenticator = Mock()
        mock_authenticator.authenticate_user.side_effect = AuthenticationError(
            error_type="AUTHENTICATION_FAILED",
            error_code="NotAuthorizedException",
            message="Invalid credentials",
            details="Username or password incorrect",
            suggested_action="Verify credentials"
        )
        
        mock_create_authenticator.return_value = mock_authenticator
        
        # Test authentication flow failure
        results = await test_authentication_flow('testuser', 'wrongpass', 'test_config.json')
        
        # Verify results
        assert results['authentication'] is False
        assert results['token_validation'] is False
        assert len(results['errors']) > 0
        assert results['errors'][0]['type'] == 'AUTHENTICATION_FAILED'
        assert results['errors'][0]['code'] == 'NotAuthorizedException'


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])