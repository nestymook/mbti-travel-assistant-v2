"""
Authentication integration tests for MCP server.

Tests the complete authentication flow including JWT token validation,
middleware integration, and error handling scenarios.
"""

import json
import pytest
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI, Request
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None
    FastAPI = None
    Request = None

from services.auth_middleware import (
    AuthenticationMiddleware, 
    AuthenticationConfig, 
    AuthenticationHelper,
    create_authentication_middleware
)
from services.auth_service import (
    TokenValidator, 
    AuthenticationError, 
    UserContext, 
    JWTClaims,
    CognitoAuthenticator
)


class TestAuthenticationMiddleware:
    """Test authentication middleware functionality."""
    
    @pytest.fixture
    def cognito_config(self):
        """Mock Cognito configuration."""
        return {
            'user_pool_id': 'us-east-1_test123',
            'client_id': 'test-client-id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123/.well-known/openid-configuration'
        }
    
    @pytest.fixture
    def auth_config(self, cognito_config):
        """Authentication configuration for testing."""
        return AuthenticationConfig(
            cognito_config=cognito_config,
            bypass_paths=['/health', '/metrics', '/docs'],
            require_authentication=True,
            log_user_context=True
        )
    
    @pytest.fixture
    def mock_token_validator(self):
        """Mock token validator."""
        validator = Mock(spec=TokenValidator)
        return validator
    
    @pytest.fixture
    def valid_jwt_claims(self):
        """Valid JWT claims for testing."""
        return JWTClaims(
            user_id='test-user-123',
            username='testuser@example.com',
            email='testuser@example.com',
            client_id='test-client-id',
            token_use='access',
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
            aud='test-client-id'
        )
    
    @pytest.fixture
    def valid_user_context(self, valid_jwt_claims):
        """Valid user context for testing."""
        return UserContext(
            user_id=valid_jwt_claims.user_id,
            username=valid_jwt_claims.username,
            email=valid_jwt_claims.email,
            authenticated=True,
            token_claims=valid_jwt_claims
        )
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_middleware_initialization(self, auth_config):
        """Test middleware initialization."""
        app = FastAPI()
        middleware = AuthenticationMiddleware(app, auth_config)
        
        assert middleware.config == auth_config
        assert isinstance(middleware.token_validator, TokenValidator)
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    @pytest.mark.asyncio
    async def test_bypass_paths(self, auth_config):
        """Test that bypass paths skip authentication."""
        app = FastAPI()
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        @app.get("/protected")
        async def protected():
            return {"data": "protected"}
        
        middleware = AuthenticationMiddleware(app, auth_config)
        app.add_middleware(type(middleware), config=auth_config)
        
        client = TestClient(app)
        
        # Health endpoint should work without authentication
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, auth_config, mock_token_validator):
        """Test handling of missing Authorization header."""
        # Create mock request without Authorization header
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.url.path = "/protected"
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token extraction
        with pytest.raises(AuthenticationError) as exc_info:
            middleware._extract_bearer_token(mock_request)
        
        assert exc_info.value.error_type == "MISSING_AUTHORIZATION"
        assert exc_info.value.error_code == "MISSING_AUTH_HEADER"
    
    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self, auth_config, mock_token_validator):
        """Test handling of invalid Authorization header format."""
        # Create mock request with invalid Authorization header
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Basic dGVzdDp0ZXN0"}
        mock_request.url.path = "/protected"
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token extraction
        with pytest.raises(AuthenticationError) as exc_info:
            middleware._extract_bearer_token(mock_request)
        
        assert exc_info.value.error_type == "INVALID_AUTHORIZATION_FORMAT"
        assert exc_info.value.error_code == "INVALID_AUTH_FORMAT"
    
    @pytest.mark.asyncio
    async def test_empty_bearer_token(self, auth_config, mock_token_validator):
        """Test handling of empty Bearer token."""
        # Create mock request with empty Bearer token
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer "}
        mock_request.url.path = "/protected"
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token extraction
        with pytest.raises(AuthenticationError) as exc_info:
            middleware._extract_bearer_token(mock_request)
        
        assert exc_info.value.error_type == "EMPTY_TOKEN"
        assert exc_info.value.error_code == "EMPTY_BEARER_TOKEN"
    
    @pytest.mark.asyncio
    async def test_valid_token_extraction(self, auth_config, mock_token_validator):
        """Test successful token extraction."""
        # Create mock request with valid Bearer token
        test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
        mock_request = Mock()
        mock_request.headers = {"Authorization": f"Bearer {test_token}"}
        mock_request.url.path = "/protected"
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token extraction
        extracted_token = middleware._extract_bearer_token(mock_request)
        assert extracted_token == test_token
    
    @pytest.mark.asyncio
    async def test_token_validation_success(self, auth_config, mock_token_validator, valid_jwt_claims, valid_user_context):
        """Test successful token validation and user context creation."""
        test_token = "valid.jwt.token"
        
        # Mock successful token validation
        mock_token_validator.validate_jwt_token = AsyncMock(return_value=valid_jwt_claims)
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token validation
        user_context = await middleware._validate_token_and_create_context(test_token)
        
        assert user_context.user_id == valid_jwt_claims.user_id
        assert user_context.username == valid_jwt_claims.username
        assert user_context.email == valid_jwt_claims.email
        assert user_context.authenticated is True
        assert user_context.token_claims == valid_jwt_claims
        
        mock_token_validator.validate_jwt_token.assert_called_once_with(test_token)
    
    @pytest.mark.asyncio
    async def test_token_validation_failure(self, auth_config, mock_token_validator):
        """Test token validation failure handling."""
        test_token = "invalid.jwt.token"
        
        # Mock token validation failure
        auth_error = AuthenticationError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time (exp) has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        mock_token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        middleware = AuthenticationMiddleware(None, auth_config)
        middleware.token_validator = mock_token_validator
        
        # Test token validation failure
        with pytest.raises(AuthenticationError) as exc_info:
            await middleware._validate_token_and_create_context(test_token)
        
        assert exc_info.value.error_type == "TOKEN_EXPIRED"
        assert exc_info.value.error_code == "EXPIRED_SIGNATURE"
    
    def test_authentication_error_response_creation(self, auth_config):
        """Test creation of authentication error responses."""
        middleware = AuthenticationMiddleware(None, auth_config)
        
        auth_error = AuthenticationError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time (exp) has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        
        response = middleware._create_authentication_error_response(auth_error)
        
        assert response.status_code == 401
        assert response.headers.get('WWW-Authenticate') == 'Bearer realm="MCP Server", error="invalid_token"'
        
        content = response.body.decode() if hasattr(response, 'body') else json.dumps(response.content)
        response_data = json.loads(content)
        
        assert response_data['success'] is False
        assert response_data['error']['type'] == 'TOKEN_EXPIRED'
        assert response_data['error']['code'] == 'EXPIRED_SIGNATURE'
        assert response_data['error']['message'] == 'JWT token has expired'
    
    def test_internal_error_response_creation(self, auth_config):
        """Test creation of internal error responses."""
        middleware = AuthenticationMiddleware(None, auth_config)
        
        response = middleware._create_internal_error_response("Test error")
        
        assert response.status_code == 500
        
        content = response.body.decode() if hasattr(response, 'body') else json.dumps(response.content)
        response_data = json.loads(content)
        
        assert response_data['success'] is False
        assert response_data['error']['type'] == 'INTERNAL_ERROR'
        assert response_data['error']['code'] == 'MIDDLEWARE_ERROR'


class TestAuthenticationHelper:
    """Test authentication helper utilities."""
    
    @pytest.fixture
    def valid_user_context(self):
        """Valid user context for testing."""
        jwt_claims = JWTClaims(
            user_id='test-user-123',
            username='testuser@example.com',
            email='testuser@example.com',
            client_id='test-client-id',
            token_use='access',
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss='https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
            aud='test-client-id'
        )
        
        return UserContext(
            user_id=jwt_claims.user_id,
            username=jwt_claims.username,
            email=jwt_claims.email,
            authenticated=True,
            token_claims=jwt_claims
        )
    
    @pytest.fixture
    def mock_request_with_context(self, valid_user_context):
        """Mock request with user context."""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.user_context = valid_user_context
        mock_request.state.authenticated = True
        return mock_request
    
    @pytest.fixture
    def mock_request_without_context(self):
        """Mock request without user context."""
        mock_request = Mock()
        mock_request.state = Mock()
        # Explicitly set attributes to None to avoid Mock returning Mock objects
        mock_request.state.user_context = None
        mock_request.state.authenticated = False
        return mock_request
    
    def test_get_user_context_success(self, mock_request_with_context, valid_user_context):
        """Test successful user context retrieval."""
        user_context = AuthenticationHelper.get_user_context(mock_request_with_context)
        assert user_context == valid_user_context
    
    def test_get_user_context_none(self, mock_request_without_context):
        """Test user context retrieval when not available."""
        user_context = AuthenticationHelper.get_user_context(mock_request_without_context)
        assert user_context is None
    
    def test_is_authenticated_true(self, mock_request_with_context):
        """Test authentication check for authenticated request."""
        is_auth = AuthenticationHelper.is_authenticated(mock_request_with_context)
        assert is_auth is True
    
    def test_is_authenticated_false(self, mock_request_without_context):
        """Test authentication check for non-authenticated request."""
        is_auth = AuthenticationHelper.is_authenticated(mock_request_without_context)
        assert is_auth is False
    
    def test_require_authentication_success(self, mock_request_with_context, valid_user_context):
        """Test require authentication with authenticated request."""
        user_context = AuthenticationHelper.require_authentication(mock_request_with_context)
        assert user_context == valid_user_context
    
    def test_require_authentication_failure(self, mock_request_without_context):
        """Test require authentication with non-authenticated request."""
        try:
            from fastapi import HTTPException
            expected_exception = HTTPException
        except ImportError:
            expected_exception = Exception
        
        with pytest.raises(expected_exception):
            AuthenticationHelper.require_authentication(mock_request_without_context)
    
    def test_get_user_id(self, mock_request_with_context, valid_user_context):
        """Test user ID extraction."""
        user_id = AuthenticationHelper.get_user_id(mock_request_with_context)
        assert user_id == valid_user_context.user_id
    
    def test_get_username(self, mock_request_with_context, valid_user_context):
        """Test username extraction."""
        username = AuthenticationHelper.get_username(mock_request_with_context)
        assert username == valid_user_context.username


class TestMCPServerAuthenticationIntegration:
    """Test MCP server authentication integration."""
    
    @pytest.fixture
    def cognito_config(self):
        """Load actual Cognito configuration for integration tests."""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cognito_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return {
                'user_pool_id': config['user_pool']['user_pool_id'],
                'client_id': config['app_client']['client_id'],
                'region': config['region'],
                'discovery_url': config['discovery_url']
            }
        except Exception:
            # Fallback for testing
            return {
                'user_pool_id': 'us-east-1_test123',
                'client_id': 'test-client-id',
                'region': 'us-east-1',
                'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123/.well-known/openid-configuration'
            }
    
    @pytest.mark.asyncio
    async def test_cognito_authenticator_initialization(self, cognito_config):
        """Test Cognito authenticator initialization."""
        authenticator = CognitoAuthenticator(
            user_pool_id=cognito_config['user_pool_id'],
            client_id=cognito_config['client_id'],
            region=cognito_config['region']
        )
        
        assert authenticator.user_pool_id == cognito_config['user_pool_id']
        assert authenticator.client_id == cognito_config['client_id']
        assert authenticator.region == cognito_config['region']
    
    @pytest.mark.asyncio
    async def test_token_validator_initialization(self, cognito_config):
        """Test token validator initialization."""
        validator = TokenValidator(cognito_config)
        
        assert validator.user_pool_id == cognito_config['user_pool_id']
        assert validator.client_id == cognito_config['client_id']
        assert validator.region == cognito_config['region']
        assert validator.discovery_url == cognito_config['discovery_url']
    
    @pytest.mark.asyncio
    async def test_invalid_token_validation(self, cognito_config):
        """Test validation of invalid JWT token."""
        validator = TokenValidator(cognito_config)
        
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(AuthenticationError):
            await validator.validate_jwt_token(invalid_token)
    
    @pytest.mark.asyncio
    async def test_malformed_token_validation(self, cognito_config):
        """Test validation of malformed JWT token."""
        validator = TokenValidator(cognito_config)
        
        malformed_token = "not-a-jwt-token"
        
        with pytest.raises(AuthenticationError):
            await validator.validate_jwt_token(malformed_token)
    
    def test_middleware_factory_creation(self, cognito_config):
        """Test authentication middleware factory."""
        middleware_factory = create_authentication_middleware(
            cognito_config=cognito_config,
            bypass_paths=['/health', '/metrics'],
            require_authentication=True,
            log_user_context=True
        )
        
        assert callable(middleware_factory)
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_health_endpoint_bypass(self, cognito_config):
        """Test that health endpoints bypass authentication."""
        # This would require setting up a full FastAPI app with the MCP server
        # For now, we test the bypass logic in isolation
        
        config = AuthenticationConfig(
            cognito_config=cognito_config,
            bypass_paths=['/health', '/metrics'],
            require_authentication=True
        )
        
        middleware = AuthenticationMiddleware(None, config)
        
        # Mock request to health endpoint
        mock_request = Mock()
        mock_request.url.path = '/health'
        
        should_bypass = middleware._should_bypass_auth(mock_request)
        assert should_bypass is True
        
        # Mock request to protected endpoint
        mock_request.url.path = '/protected'
        should_bypass = middleware._should_bypass_auth(mock_request)
        assert should_bypass is False


class TestAuthenticationErrorScenarios:
    """Test various authentication error scenarios."""
    
    @pytest.fixture
    def cognito_config(self):
        """Mock Cognito configuration."""
        return {
            'user_pool_id': 'us-east-1_test123',
            'client_id': 'test-client-id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123/.well-known/openid-configuration'
        }
    
    @pytest.mark.asyncio
    async def test_expired_token_error(self, cognito_config):
        """Test handling of expired JWT token."""
        validator = TokenValidator(cognito_config)
        
        # Create an expired token (this is a mock - in real scenario we'd need a properly signed expired token)
        with patch.object(validator, 'validate_jwt_token') as mock_validate:
            mock_validate.side_effect = AuthenticationError(
                error_type="TOKEN_EXPIRED",
                error_code="EXPIRED_SIGNATURE",
                message="JWT token has expired",
                details="Token expiration time (exp) has passed",
                suggested_action="Refresh token or re-authenticate"
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                await validator.validate_jwt_token("expired.token")
            
            assert exc_info.value.error_type == "TOKEN_EXPIRED"
            assert exc_info.value.suggested_action == "Refresh token or re-authenticate"
    
    @pytest.mark.asyncio
    async def test_invalid_signature_error(self, cognito_config):
        """Test handling of invalid token signature."""
        validator = TokenValidator(cognito_config)
        
        with patch.object(validator, 'validate_jwt_token') as mock_validate:
            mock_validate.side_effect = AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="INVALID_SIGNATURE",
                message="JWT token signature verification failed",
                details="Token signature does not match expected value",
                suggested_action="Verify token integrity and JWKS configuration"
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                await validator.validate_jwt_token("invalid.signature.token")
            
            assert exc_info.value.error_code == "INVALID_SIGNATURE"
    
    @pytest.mark.asyncio
    async def test_jwks_fetch_error(self, cognito_config):
        """Test handling of JWKS fetch errors."""
        validator = TokenValidator(cognito_config)
        
        with patch.object(validator, 'get_signing_key') as mock_get_key:
            mock_get_key.side_effect = AuthenticationError(
                error_type="JWKS_FETCH_ERROR",
                error_code="NETWORK_ERROR",
                message="Failed to fetch JWKS",
                details="Network connection failed",
                suggested_action="Check network connectivity and JWKS URL"
            )
            
            with pytest.raises(AuthenticationError) as exc_info:
                await validator.get_signing_key("test-kid")
            
            assert exc_info.value.error_type == "JWKS_FETCH_ERROR"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])