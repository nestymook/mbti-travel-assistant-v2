"""
Unit tests for JWT Authentication Handler.

Tests JWT token validation, user context extraction, and security monitoring
for the MBTI Travel Assistant MCP authentication system.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import jwt
import boto3
from moto import mock_cognitoidp

from services.jwt_auth_handler import (
    JWTAuthHandler, JWTAuthHandlerFactory, TokenValidationResult, AuthenticationContext
)
from models.auth_models import CognitoConfig, JWTClaims, UserContext, AuthenticationError
from services.auth_service import AuthenticationError as AuthError


class TestJWTAuthHandler:
    """Test cases for JWT Authentication Handler."""
    
    @pytest.fixture
    def cognito_config(self):
        """Create test Cognito configuration."""
        return CognitoConfig(
            user_pool_id="us-east-1_test123",
            client_id="test-client-id",
            region="us-east-1",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123/.well-known/openid-configuration",
            jwks_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123/.well-known/jwks.json",
            issuer_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123"
        )
    
    @pytest.fixture
    def jwt_claims(self):
        """Create test JWT claims."""
        return JWTClaims(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            client_id="test-client-id",
            token_use="access",
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123",
            aud="test-client-id"
        )
    
    @pytest.fixture
    def auth_context(self):
        """Create test authentication context."""
        return AuthenticationContext(
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
            request_path="/api/test",
            request_method="POST",
            timestamp=datetime.now(timezone.utc),
            request_id="test-request-123"
        )
    
    @pytest.fixture
    def jwt_auth_handler(self, cognito_config):
        """Create JWT auth handler with test configuration."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                handler = JWTAuthHandler(cognito_config)
                return handler
    
    def test_init_with_valid_config(self, cognito_config):
        """Test JWT auth handler initialization with valid config."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                handler = JWTAuthHandler(cognito_config)
                
                assert handler.cognito_config == cognito_config
                assert handler.token_validator is not None
                assert handler.error_handler is not None
                assert handler.security_monitor is not None
    
    def test_init_with_invalid_config(self):
        """Test JWT auth handler initialization with invalid config."""
        invalid_config = CognitoConfig(
            user_pool_id="",  # Invalid empty user pool ID
            client_id="test-client",
            region="us-east-1",
            discovery_url="invalid-url",
            jwks_url="invalid-url",
            issuer_url="invalid-url"
        )
        
        with pytest.raises(ValueError, match="Invalid Cognito configuration"):
            JWTAuthHandler(invalid_config)
    
    def test_extract_bearer_token_valid(self, jwt_auth_handler):
        """Test extracting valid Bearer token from header."""
        auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        
        token = jwt_auth_handler.extract_token_from_header(auth_header)
        
        assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    
    def test_extract_bearer_token_missing_header(self, jwt_auth_handler):
        """Test extracting token from missing header."""
        with pytest.raises(AuthenticationError) as exc_info:
            jwt_auth_handler.extract_token_from_header("")
        
        assert exc_info.value.error_code == "MISSING_TOKEN"
    
    def test_extract_bearer_token_invalid_format(self, jwt_auth_handler):
        """Test extracting token from invalid header format."""
        with pytest.raises(AuthenticationError) as exc_info:
            jwt_auth_handler.extract_token_from_header("Basic dGVzdDp0ZXN0")
        
        assert exc_info.value.error_code == "INVALID_TOKEN"
    
    def test_extract_bearer_token_empty_token(self, jwt_auth_handler):
        """Test extracting empty token from header."""
        with pytest.raises(AuthenticationError) as exc_info:
            jwt_auth_handler.extract_token_from_header("Bearer ")
        
        assert exc_info.value.error_code == "INVALID_TOKEN"
    
    @pytest.mark.asyncio
    async def test_validate_request_token_success(self, jwt_auth_handler, jwt_claims, auth_context):
        """Test successful token validation."""
        auth_header = "Bearer valid.jwt.token"
        
        # Mock token validator
        jwt_auth_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
        
        result = await jwt_auth_handler.validate_request_token(auth_header, auth_context)
        
        assert result.is_valid is True
        assert result.user_context is not None
        assert result.user_context.user_id == jwt_claims.user_id
        assert result.user_context.username == jwt_claims.username
        assert result.user_context.authenticated is True
        assert result.validation_time_ms is not None
        assert result.validation_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_validate_request_token_expired(self, jwt_auth_handler, auth_context):
        """Test token validation with expired token."""
        auth_header = "Bearer expired.jwt.token"
        
        # Mock token validator to raise expired token error
        auth_error = AuthError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        jwt_auth_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        result = await jwt_auth_handler.validate_request_token(auth_header, auth_context)
        
        assert result.is_valid is False
        assert result.error is not None
        assert result.error.error_code == "EXPIRED_SIGNATURE"
        assert result.validation_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_validate_request_token_invalid_signature(self, jwt_auth_handler, auth_context):
        """Test token validation with invalid signature."""
        auth_header = "Bearer invalid.signature.token"
        
        # Mock token validator to raise invalid signature error
        auth_error = AuthError(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_SIGNATURE",
            message="JWT token signature verification failed",
            details="Token signature does not match",
            suggested_action="Verify token integrity"
        )
        jwt_auth_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        result = await jwt_auth_handler.validate_request_token(auth_header, auth_context)
        
        assert result.is_valid is False
        assert result.error is not None
        assert result.error.error_code == "INVALID_SIGNATURE"
    
    @pytest.mark.asyncio
    async def test_validate_token_claims_success(self, jwt_auth_handler, jwt_claims):
        """Test successful token claims validation."""
        token = "valid.jwt.token"
        
        jwt_auth_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
        
        result = await jwt_auth_handler.validate_token_claims(token)
        
        assert result == jwt_claims
    
    @pytest.mark.asyncio
    async def test_validate_token_claims_failure(self, jwt_auth_handler):
        """Test token claims validation failure."""
        token = "invalid.jwt.token"
        
        auth_error = AuthError(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_TOKEN",
            message="Invalid JWT token",
            details="Token format is invalid",
            suggested_action="Provide valid JWT token"
        )
        jwt_auth_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        with pytest.raises(AuthenticationError) as exc_info:
            await jwt_auth_handler.validate_token_claims(token)
        
        assert exc_info.value.error_code == "INVALID_TOKEN"
    
    def test_get_user_context_from_token_success(self, jwt_auth_handler):
        """Test extracting user context from valid token."""
        # Create a test JWT token (without signature verification)
        payload = {
            'sub': 'test-user-123',
            'username': 'testuser',
            'email': 'test@example.com',
            'client_id': 'test-client-id',
            'token_use': 'access',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            'iat': int(datetime.now(timezone.utc).timestamp()),
            'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
            'aud': 'test-client-id'
        }
        
        # Mock jwt.decode to return our payload
        with patch('jwt.decode', return_value=payload):
            user_context = jwt_auth_handler.get_user_context_from_token("test.jwt.token")
            
            assert user_context.user_id == "test-user-123"
            assert user_context.username == "testuser"
            assert user_context.email == "test@example.com"
            assert user_context.authenticated is True
    
    def test_get_user_context_from_token_invalid(self, jwt_auth_handler):
        """Test extracting user context from invalid token."""
        with patch('jwt.decode', side_effect=jwt.DecodeError("Invalid token")):
            with pytest.raises(AuthenticationError) as exc_info:
                jwt_auth_handler.get_user_context_from_token("invalid.token")
            
            assert exc_info.value.error_code == "INVALID_TOKEN"
    
    def test_is_token_expired_true(self, jwt_auth_handler):
        """Test checking expired token."""
        # Create expired token payload
        expired_payload = {
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        
        with patch('jwt.decode', return_value=expired_payload):
            result = jwt_auth_handler.is_token_expired("expired.token")
            
            assert result is True
    
    def test_is_token_expired_false(self, jwt_auth_handler):
        """Test checking valid (non-expired) token."""
        # Create valid token payload
        valid_payload = {
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        
        with patch('jwt.decode', return_value=valid_payload):
            result = jwt_auth_handler.is_token_expired("valid.token")
            
            assert result is False
    
    def test_is_token_expired_invalid_token(self, jwt_auth_handler):
        """Test checking expiration of invalid token."""
        with patch('jwt.decode', side_effect=jwt.DecodeError("Invalid token")):
            result = jwt_auth_handler.is_token_expired("invalid.token")
            
            assert result is True  # Assume expired if can't decode
    
    @mock_cognitoidp
    def test_get_cognito_user_info_success(self, jwt_auth_handler):
        """Test getting Cognito user info with valid token."""
        # Setup mock Cognito client
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        jwt_auth_handler.cognito_client = cognito_client
        
        # Mock the get_user response
        mock_response = {
            'Username': 'testuser',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'cognito:user_status', 'Value': 'CONFIRMED'}
            ],
            'UserMFASettingList': [],
            'PreferredMfaSetting': None
        }
        
        with patch.object(cognito_client, 'get_user', return_value=mock_response):
            user_info = jwt_auth_handler.get_cognito_user_info("valid.access.token")
            
            assert user_info['username'] == 'testuser'
            assert user_info['user_attributes']['email'] == 'test@example.com'
            assert user_info['user_attributes']['cognito:user_status'] == 'CONFIRMED'
    
    @mock_cognitoidp
    def test_get_cognito_user_info_failure(self, jwt_auth_handler):
        """Test getting Cognito user info with invalid token."""
        # Setup mock Cognito client
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        jwt_auth_handler.cognito_client = cognito_client
        
        # Mock ClientError
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Invalid token'}},
            'GetUser'
        )
        
        with patch.object(cognito_client, 'get_user', side_effect=error):
            with pytest.raises(AuthenticationError) as exc_info:
                jwt_auth_handler.get_cognito_user_info("invalid.token")
            
            assert exc_info.value.error_code == "COGNITO_ERROR"
    
    def test_create_authentication_context(self, jwt_auth_handler):
        """Test creating authentication context."""
        context = jwt_auth_handler.create_authentication_context(
            client_ip="192.168.1.100",
            user_agent="Test Browser",
            request_path="/api/test",
            request_method="POST",
            request_id="test-123"
        )
        
        assert context.client_ip == "192.168.1.100"
        assert context.user_agent == "Test Browser"
        assert context.request_path == "/api/test"
        assert context.request_method == "POST"
        assert context.request_id == "test-123"
        assert isinstance(context.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_refresh_jwks_cache_success(self, jwt_auth_handler):
        """Test successful JWKS cache refresh."""
        jwt_auth_handler.token_validator._refresh_jwks_cache = AsyncMock()
        
        await jwt_auth_handler.refresh_jwks_cache()
        
        jwt_auth_handler.token_validator._refresh_jwks_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_jwks_cache_failure(self, jwt_auth_handler):
        """Test JWKS cache refresh failure."""
        jwt_auth_handler.token_validator._refresh_jwks_cache = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await jwt_auth_handler.refresh_jwks_cache()
        
        assert exc_info.value.error_code == "COGNITO_ERROR"


class TestJWTAuthHandlerFactory:
    """Test cases for JWT Auth Handler Factory."""
    
    def test_create_default_handler(self):
        """Test creating handler with default configuration."""
        with patch('services.jwt_auth_handler.settings') as mock_settings:
            mock_settings.authentication.cognito_user_pool_id = "us-east-1_test123"
            mock_settings.authentication.cognito_region = "us-east-1"
            mock_settings.authentication.jwt_audience = "test-client"
            
            with patch('services.jwt_auth_handler.get_security_monitor'):
                with patch('services.jwt_auth_handler.boto3.client'):
                    handler = JWTAuthHandlerFactory.create_default_handler()
                    
                    assert isinstance(handler, JWTAuthHandler)
                    assert handler.cognito_config.user_pool_id == "us-east-1_test123"
    
    def test_create_handler_with_config(self):
        """Test creating handler with specific config."""
        config = CognitoConfig(
            user_pool_id="us-east-1_custom123",
            client_id="custom-client-id",
            region="us-east-1",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_custom123/.well-known/openid-configuration",
            jwks_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_custom123/.well-known/jwks.json",
            issuer_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_custom123"
        )
        
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                handler = JWTAuthHandlerFactory.create_handler_with_config(config)
                
                assert isinstance(handler, JWTAuthHandler)
                assert handler.cognito_config == config
    
    def test_create_handler_from_dict(self):
        """Test creating handler from configuration dictionary."""
        config_dict = {
            'user_pool_id': 'us-east-1_dict123',
            'client_id': 'dict-client-id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_dict123/.well-known/openid-configuration',
            'jwks_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_dict123/.well-known/jwks.json',
            'issuer_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_dict123'
        }
        
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                handler = JWTAuthHandlerFactory.create_handler_from_dict(config_dict)
                
                assert isinstance(handler, JWTAuthHandler)
                assert handler.cognito_config.user_pool_id == 'us-east-1_dict123'
                assert handler.cognito_config.client_id == 'dict-client-id'


class TestTokenValidationResult:
    """Test cases for TokenValidationResult dataclass."""
    
    def test_successful_validation_result(self, jwt_claims):
        """Test creating successful validation result."""
        user_context = UserContext(
            user_id=jwt_claims.user_id,
            username=jwt_claims.username,
            email=jwt_claims.email,
            authenticated=True,
            token_claims=jwt_claims
        )
        
        result = TokenValidationResult(
            is_valid=True,
            user_context=user_context,
            claims=jwt_claims,
            validation_time_ms=150
        )
        
        assert result.is_valid is True
        assert result.user_context == user_context
        assert result.claims == jwt_claims
        assert result.validation_time_ms == 150
        assert result.error is None
    
    def test_failed_validation_result(self):
        """Test creating failed validation result."""
        error = AuthenticationError.invalid_token("Invalid JWT token")
        
        result = TokenValidationResult(
            is_valid=False,
            error=error,
            validation_time_ms=75
        )
        
        assert result.is_valid is False
        assert result.error == error
        assert result.validation_time_ms == 75
        assert result.user_context is None
        assert result.claims is None


class TestAuthenticationContext:
    """Test cases for AuthenticationContext dataclass."""
    
    def test_create_authentication_context(self):
        """Test creating authentication context."""
        timestamp = datetime.now(timezone.utc)
        
        context = AuthenticationContext(
            client_ip="10.0.1.100",
            user_agent="Mozilla/5.0 (Test)",
            request_path="/api/restaurants",
            request_method="GET",
            timestamp=timestamp,
            request_id="req-123"
        )
        
        assert context.client_ip == "10.0.1.100"
        assert context.user_agent == "Mozilla/5.0 (Test)"
        assert context.request_path == "/api/restaurants"
        assert context.request_method == "GET"
        assert context.timestamp == timestamp
        assert context.request_id == "req-123"
    
    def test_create_context_without_request_id(self):
        """Test creating context without request ID."""
        context = AuthenticationContext(
            client_ip="192.168.1.1",
            user_agent="Test Agent",
            request_path="/health",
            request_method="GET",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert context.request_id is None
        assert context.client_ip == "192.168.1.1"


if __name__ == "__main__":
    pytest.main([__file__])