"""
Unit tests for authentication middleware and JWT validation.

Tests cover JWT token validation, authentication bypass functionality,
user context extraction, and error handling scenarios.
"""

import pytest
import jwt
import json
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from middleware.auth_middleware import AuthenticationMiddleware, get_current_user
from middleware.jwt_validator import JWTValidator, UserContext, JWTValidationError


class TestJWTValidator:
    """Test cases for JWT token validation."""
    
    @pytest.fixture
    def jwt_validator(self):
        """Create JWT validator instance for testing."""
        return JWTValidator()
    
    @pytest.fixture
    def mock_jwks(self):
        """Mock JWKS response."""
        return {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-n-value",
                    "e": "AQAB"
                }
            ]
        }
    
    @pytest.fixture
    def mock_discovery_doc(self):
        """Mock OpenID Connect discovery document."""
        return {
            "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "jwks_uri": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json",
            "authorization_endpoint": "https://test.auth.us-east-1.amazoncognito.com/oauth2/authorize",
            "token_endpoint": "https://test.auth.us-east-1.amazoncognito.com/oauth2/token"
        }
    
    @pytest.fixture
    def valid_token_payload(self):
        """Valid JWT token payload."""
        return {
            "sub": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "token_use": "access",
            "aud": "1ofgeckef3po4i3us4j1m4chvd",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nbf": int(datetime.now(timezone.utc).timestamp())
        }
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_success(self, mock_get, jwt_validator, mock_discovery_doc):
        """Test successful retrieval of discovery document."""
        mock_response = Mock()
        mock_response.json.return_value = mock_discovery_doc
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = jwt_validator._get_discovery_document()
        
        assert result == mock_discovery_doc
        mock_get.assert_called_once_with(
            jwt_validator.cognito_config.discovery_url,
            timeout=10
        )
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_failure(self, mock_get, jwt_validator):
        """Test failure to retrieve discovery document."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve discovery document"):
            jwt_validator._get_discovery_document()
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_jwks_success(self, mock_get, jwt_validator, mock_discovery_doc, mock_jwks):
        """Test successful retrieval of JWKS."""
        # Mock discovery document request
        mock_discovery_response = Mock()
        mock_discovery_response.json.return_value = mock_discovery_doc
        mock_discovery_response.raise_for_status.return_value = None
        
        # Mock JWKS request
        mock_jwks_response = Mock()
        mock_jwks_response.json.return_value = mock_jwks
        mock_jwks_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_discovery_response, mock_jwks_response]
        
        result = jwt_validator._get_jwks()
        
        assert result == mock_jwks
        assert mock_get.call_count == 2
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_jwks_failure(self, mock_get, jwt_validator, mock_discovery_doc):
        """Test failure to retrieve JWKS."""
        # Mock discovery document request
        mock_discovery_response = Mock()
        mock_discovery_response.json.return_value = mock_discovery_doc
        mock_discovery_response.raise_for_status.return_value = None
        
        # Mock JWKS request failure
        mock_get.side_effect = [mock_discovery_response, Exception("JWKS error")]
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve JWKS"):
            jwt_validator._get_jwks()
    
    def test_extract_user_context_success(self, jwt_validator, valid_token_payload):
        """Test successful user context extraction."""
        user_context = jwt_validator._extract_user_context(valid_token_payload)
        
        assert user_context.user_id == "test-user-id"
        assert user_context.username == "testuser"
        assert user_context.email == "test@example.com"
        assert user_context.token_claims == valid_token_payload
        assert isinstance(user_context.authenticated_at, datetime)
    
    def test_extract_user_context_missing_sub(self, jwt_validator):
        """Test user context extraction with missing sub claim."""
        payload = {"username": "testuser", "token_use": "access"}
        
        with pytest.raises(JWTValidationError, match="Token missing required 'sub' claim"):
            jwt_validator._extract_user_context(payload)
    
    def test_extract_user_context_fallback_username(self, jwt_validator):
        """Test user context extraction with fallback username."""
        payload = {"sub": "test-user-id", "token_use": "access"}
        
        user_context = jwt_validator._extract_user_context(payload)
        
        assert user_context.user_id == "test-user-id"
        assert user_context.username == "test-user-id"  # Fallback to user_id
        assert user_context.email is None
    
    def test_is_token_expired_true(self, jwt_validator):
        """Test token expiration check for expired token."""
        expired_payload = {
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        assert jwt_validator.is_token_expired(expired_token) is True
    
    def test_is_token_expired_false(self, jwt_validator):
        """Test token expiration check for valid token."""
        valid_payload = {
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        valid_token = jwt.encode(valid_payload, "secret", algorithm="HS256")
        
        assert jwt_validator.is_token_expired(valid_token) is False
    
    def test_is_token_expired_invalid_token(self, jwt_validator):
        """Test token expiration check for invalid token."""
        assert jwt_validator.is_token_expired("invalid-token") is True


class TestAuthenticationMiddleware:
    """Test cases for authentication middleware."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_endpoint():
            return {"message": "protected"}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client with authentication middleware."""
        middleware = AuthenticationMiddleware(
            app,
            bypass_paths=["/health", "/docs", "/"]
        )
        app.add_middleware(AuthenticationMiddleware, bypass_paths=["/health", "/docs", "/"])
        return TestClient(app)
    
    def test_bypass_paths_exact_match(self):
        """Test bypass path matching for exact paths."""
        middleware = AuthenticationMiddleware(None, bypass_paths=["/health", "/docs"])
        
        assert middleware._should_bypass_auth("/health") is True
        assert middleware._should_bypass_auth("/docs") is True
        assert middleware._should_bypass_auth("/protected") is False
    
    def test_bypass_paths_root_match(self):
        """Test bypass path matching for root path."""
        middleware = AuthenticationMiddleware(None, bypass_paths=["/"])
        
        assert middleware._should_bypass_auth("/") is True
        assert middleware._should_bypass_auth("") is True
        assert middleware._should_bypass_auth("/health") is False
    
    def test_bypass_paths_prefix_match(self):
        """Test bypass path matching for prefix patterns."""
        middleware = AuthenticationMiddleware(None, bypass_paths=["/docs/*"])
        
        assert middleware._should_bypass_auth("/docs/") is True
        assert middleware._should_bypass_auth("/docs/swagger") is True
        assert middleware._should_bypass_auth("/docs/redoc") is True
        assert middleware._should_bypass_auth("/api/docs") is False
    
    def test_bypass_paths_normalization(self):
        """Test path normalization in bypass checking."""
        middleware = AuthenticationMiddleware(None, bypass_paths=["/health"])
        
        assert middleware._should_bypass_auth("/health/") is True
        assert middleware._should_bypass_auth("/health") is True
    
    @patch('middleware.auth_middleware.jwt_validator.validate_token')
    def test_successful_authentication(self, mock_validate, client):
        """Test successful request authentication."""
        mock_user_context = UserContext(
            user_id="test-user",
            username="testuser",
            email="test@example.com"
        )
        mock_validate.return_value = mock_user_context
        
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == 200
        mock_validate.assert_called_once_with("valid-token")
    
    def test_missing_authorization_header(self, client):
        """Test request without authorization header."""
        response = client.get("/protected")
        
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["error"]["message"]
    
    def test_invalid_authorization_format(self, client):
        """Test request with invalid authorization header format."""
        response = client.get(
            "/protected",
            headers={"Authorization": "Invalid format"}
        )
        
        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["error"]["message"]
    
    def test_empty_token(self, client):
        """Test request with empty token."""
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer "}
        )
        
        assert response.status_code == 401
        assert "JWT token is required" in response.json()["error"]["message"]
    
    @patch('middleware.auth_middleware.jwt_validator.validate_token')
    def test_invalid_token(self, mock_validate, client):
        """Test request with invalid JWT token."""
        mock_validate.side_effect = JWTValidationError("Invalid token")
        
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        assert "Invalid JWT token" in response.json()["error"]["message"]
    
    def test_bypass_path_no_auth_required(self, client):
        """Test that bypass paths don't require authentication."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestGetCurrentUser:
    """Test cases for get_current_user dependency."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.state = Mock()
        return request
    
    def test_get_current_user_from_state(self, mock_request):
        """Test getting user from request state."""
        user_context = UserContext(
            user_id="test-user",
            username="testuser"
        )
        mock_request.state.user = user_context
        
        result = asyncio.run(get_current_user(mock_request, None))
        
        assert result == user_context
    
    @patch('middleware.auth_middleware.get_settings')
    def test_get_current_user_bypass_path(self, mock_get_settings, mock_request):
        """Test getting user for bypass path."""
        mock_request.url.path = "/health"
        mock_request.state.user = None
        
        mock_settings = Mock()
        mock_settings.app.bypass_paths = ["/health"]
        mock_get_settings.return_value = mock_settings
        
        result = asyncio.run(get_current_user(mock_request, None))
        
        assert result.user_id == "anonymous"
        assert result.username == "anonymous"
    
    @patch('middleware.auth_middleware.jwt_validator.validate_token')
    def test_get_current_user_with_credentials(self, mock_validate, mock_request):
        """Test getting user with valid credentials."""
        mock_request.state.user = None
        
        user_context = UserContext(
            user_id="test-user",
            username="testuser"
        )
        mock_validate.return_value = user_context
        
        credentials = Mock()
        credentials.credentials = "valid-token"
        
        result = asyncio.run(get_current_user(mock_request, credentials))
        
        assert result == user_context
        assert mock_request.state.user == user_context
        mock_validate.assert_called_once_with("valid-token")
    
    def test_get_current_user_no_credentials(self, mock_request):
        """Test getting user without credentials for protected path."""
        mock_request.state.user = None
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(mock_request, None))
        
        assert exc_info.value.status_code == 401
        assert "Authorization header required" in exc_info.value.detail
    
    @patch('middleware.auth_middleware.jwt_validator.validate_token')
    def test_get_current_user_invalid_token(self, mock_validate, mock_request):
        """Test getting user with invalid token."""
        mock_request.state.user = None
        mock_validate.side_effect = JWTValidationError("Invalid token")
        
        credentials = Mock()
        credentials.credentials = "invalid-token"
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(mock_request, credentials))
        
        assert exc_info.value.status_code == 401
        assert "Invalid JWT token" in exc_info.value.detail


class TestUserContext:
    """Test cases for UserContext dataclass."""
    
    def test_user_context_creation(self):
        """Test UserContext creation with all fields."""
        token_claims = {"sub": "test", "username": "testuser"}
        auth_time = datetime.now(timezone.utc)
        
        user_context = UserContext(
            user_id="test-user",
            username="testuser",
            email="test@example.com",
            token_claims=token_claims,
            authenticated_at=auth_time
        )
        
        assert user_context.user_id == "test-user"
        assert user_context.username == "testuser"
        assert user_context.email == "test@example.com"
        assert user_context.token_claims == token_claims
        assert user_context.authenticated_at == auth_time
    
    def test_user_context_defaults(self):
        """Test UserContext creation with default values."""
        user_context = UserContext(
            user_id="test-user",
            username="testuser"
        )
        
        assert user_context.user_id == "test-user"
        assert user_context.username == "testuser"
        assert user_context.email is None
        assert user_context.token_claims == {}
        assert isinstance(user_context.authenticated_at, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])