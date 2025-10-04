"""
Unit tests for JWT validation functionality.

Tests JWT token validation, signature verification, claim extraction,
and token expiration handling.
"""

import pytest
import jwt
import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from middleware.jwt_validator import (
    JWTValidator,
    UserContext,
    JWTValidationError,
    CognitoConfig
)


class TestJWTValidatorCore:
    """Core JWT validation functionality tests."""
    
    @pytest.fixture
    def cognito_config(self):
        """Create Cognito configuration for testing."""
        return CognitoConfig(
            user_pool_id="us-east-1_KePRX24Bn",
            client_id="1ofgeckef3po4i3us4j1m4chvd",
            region="us-east-1",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
        )
    
    @pytest.fixture
    def jwt_validator(self, cognito_config):
        """Create JWT validator instance."""
        return JWTValidator(cognito_config)
    
    @pytest.fixture
    def valid_jwt_payload(self):
        """Valid JWT payload for testing."""
        return {
            "sub": "test-user-id-12345",
            "username": "testuser",
            "email": "testuser@example.com",
            "token_use": "access",
            "aud": "1ofgeckef3po4i3us4j1m4chvd",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nbf": int(datetime.now(timezone.utc).timestamp()),
            "auth_time": int(datetime.now(timezone.utc).timestamp()),
            "scope": "openid email profile"
        }
    
    @pytest.fixture
    def mock_jwks_response(self):
        """Mock JWKS response from Cognito."""
        return {
            "keys": [
                {
                    "kid": "test-key-id-1",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-modulus-value-here",
                    "e": "AQAB"
                },
                {
                    "kid": "test-key-id-2", 
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "another-modulus-value",
                    "e": "AQAB"
                }
            ]
        }
    
    @pytest.fixture
    def mock_discovery_document(self):
        """Mock OpenID Connect discovery document."""
        return {
            "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "jwks_uri": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json",
            "authorization_endpoint": "https://test-domain.auth.us-east-1.amazoncognito.com/oauth2/authorize",
            "token_endpoint": "https://test-domain.auth.us-east-1.amazoncognito.com/oauth2/token",
            "userinfo_endpoint": "https://test-domain.auth.us-east-1.amazoncognito.com/oauth2/userInfo",
            "response_types_supported": ["code", "token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "email", "profile"]
        }
    
    def test_cognito_config_initialization(self, cognito_config):
        """Test CognitoConfig initialization."""
        assert cognito_config.user_pool_id == "us-east-1_KePRX24Bn"
        assert cognito_config.client_id == "1ofgeckef3po4i3us4j1m4chvd"
        assert cognito_config.region == "us-east-1"
        assert "cognito-idp.us-east-1.amazonaws.com" in cognito_config.discovery_url
    
    def test_jwt_validator_initialization(self, jwt_validator, cognito_config):
        """Test JWTValidator initialization."""
        assert jwt_validator.cognito_config == cognito_config
        assert jwt_validator._jwks_cache is None
        assert jwt_validator._discovery_cache is None
        assert jwt_validator._cache_expiry == 0
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_success(self, mock_get, jwt_validator, mock_discovery_document):
        """Test successful discovery document retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_discovery_document
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = jwt_validator._get_discovery_document()
        
        assert result == mock_discovery_document
        mock_get.assert_called_once_with(
            jwt_validator.cognito_config.discovery_url,
            timeout=10
        )
        
        # Verify caching
        assert jwt_validator._discovery_cache == mock_discovery_document
        assert jwt_validator._cache_expiry > time.time()
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_cached(self, mock_get, jwt_validator, mock_discovery_document):
        """Test discovery document retrieval from cache."""
        # Set up cache
        jwt_validator._discovery_cache = mock_discovery_document
        jwt_validator._cache_expiry = time.time() + 3600  # 1 hour from now
        
        result = jwt_validator._get_discovery_document()
        
        assert result == mock_discovery_document
        mock_get.assert_not_called()  # Should not make HTTP request
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_cache_expired(self, mock_get, jwt_validator, mock_discovery_document):
        """Test discovery document retrieval when cache is expired."""
        # Set up expired cache
        jwt_validator._discovery_cache = {"old": "data"}
        jwt_validator._cache_expiry = time.time() - 1  # 1 second ago
        
        mock_response = Mock()
        mock_response.json.return_value = mock_discovery_document
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = jwt_validator._get_discovery_document()
        
        assert result == mock_discovery_document
        mock_get.assert_called_once()
        assert jwt_validator._discovery_cache == mock_discovery_document
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_discovery_document_network_error(self, mock_get, jwt_validator):
        """Test discovery document retrieval network error."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve discovery document"):
            jwt_validator._get_discovery_document()
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_jwks_success(self, mock_get, jwt_validator, mock_discovery_document, mock_jwks_response):
        """Test successful JWKS retrieval."""
        # Mock discovery document request
        mock_discovery_response = Mock()
        mock_discovery_response.json.return_value = mock_discovery_document
        mock_discovery_response.raise_for_status.return_value = None
        
        # Mock JWKS request
        mock_jwks_response_obj = Mock()
        mock_jwks_response_obj.json.return_value = mock_jwks_response
        mock_jwks_response_obj.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_discovery_response, mock_jwks_response_obj]
        
        result = jwt_validator._get_jwks()
        
        assert result == mock_jwks_response
        assert mock_get.call_count == 2
        
        # Verify JWKS endpoint was called
        jwks_call = mock_get.call_args_list[1]
        assert jwks_call[0][0] == mock_discovery_document["jwks_uri"]
    
    @patch('middleware.jwt_validator.requests.get')
    def test_get_jwks_cached(self, mock_get, jwt_validator, mock_jwks_response):
        """Test JWKS retrieval from cache."""
        # Set up cache
        jwt_validator._jwks_cache = mock_jwks_response
        jwt_validator._cache_expiry = time.time() + 3600
        
        result = jwt_validator._get_jwks()
        
        assert result == mock_jwks_response
        mock_get.assert_not_called()
    
    def test_extract_user_context_complete(self, jwt_validator, valid_jwt_payload):
        """Test user context extraction with complete payload."""
        user_context = jwt_validator._extract_user_context(valid_jwt_payload)
        
        assert user_context.user_id == "test-user-id-12345"
        assert user_context.username == "testuser"
        assert user_context.email == "testuser@example.com"
        assert user_context.token_claims == valid_jwt_payload
        assert isinstance(user_context.authenticated_at, datetime)
    
    def test_extract_user_context_minimal(self, jwt_validator):
        """Test user context extraction with minimal payload."""
        minimal_payload = {
            "sub": "minimal-user-id",
            "token_use": "access"
        }
        
        user_context = jwt_validator._extract_user_context(minimal_payload)
        
        assert user_context.user_id == "minimal-user-id"
        assert user_context.username == "minimal-user-id"  # Falls back to user_id
        assert user_context.email is None
        assert user_context.token_claims == minimal_payload
    
    def test_extract_user_context_missing_sub(self, jwt_validator):
        """Test user context extraction with missing sub claim."""
        invalid_payload = {
            "username": "testuser",
            "token_use": "access"
        }
        
        with pytest.raises(JWTValidationError, match="Token missing required 'sub' claim"):
            jwt_validator._extract_user_context(invalid_payload)
    
    def test_extract_user_context_cognito_username_format(self, jwt_validator):
        """Test user context extraction with Cognito username format."""
        cognito_payload = {
            "sub": "cognito-user-id",
            "cognito:username": "cognito-user",
            "email": "cognito@example.com",
            "token_use": "access"
        }
        
        user_context = jwt_validator._extract_user_context(cognito_payload)
        
        assert user_context.user_id == "cognito-user-id"
        assert user_context.username == "cognito-user"
        assert user_context.email == "cognito@example.com"
    
    def test_is_token_expired_valid(self, jwt_validator):
        """Test token expiration check for valid token."""
        future_exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        valid_payload = {"exp": future_exp}
        valid_token = jwt.encode(valid_payload, "secret", algorithm="HS256")
        
        assert jwt_validator.is_token_expired(valid_token) is False
    
    def test_is_token_expired_expired(self, jwt_validator):
        """Test token expiration check for expired token."""
        past_exp = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        expired_payload = {"exp": past_exp}
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        
        assert jwt_validator.is_token_expired(expired_token) is True
    
    def test_is_token_expired_no_exp_claim(self, jwt_validator):
        """Test token expiration check for token without exp claim."""
        no_exp_payload = {"sub": "user"}
        no_exp_token = jwt.encode(no_exp_payload, "secret", algorithm="HS256")
        
        # Token without exp claim should be considered expired
        assert jwt_validator.is_token_expired(no_exp_token) is True
    
    def test_is_token_expired_invalid_token(self, jwt_validator):
        """Test token expiration check for invalid token."""
        invalid_token = "invalid.jwt.token"
        
        # Invalid token should be considered expired
        assert jwt_validator.is_token_expired(invalid_token) is True
    
    def test_is_token_expired_malformed_exp(self, jwt_validator):
        """Test token expiration check for token with malformed exp claim."""
        malformed_exp_payload = {"exp": "not-a-timestamp"}
        malformed_token = jwt.encode(malformed_exp_payload, "secret", algorithm="HS256")
        
        # Token with malformed exp should be considered expired
        assert jwt_validator.is_token_expired(malformed_token) is True


class TestJWTValidationIntegration:
    """Integration tests for JWT validation process."""
    
    @pytest.fixture
    def jwt_validator(self):
        """Create JWT validator for integration testing."""
        config = CognitoConfig(
            user_pool_id="us-east-1_KePRX24Bn",
            client_id="1ofgeckef3po4i3us4j1m4chvd",
            region="us-east-1",
            discovery_url="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
        )
        return JWTValidator(config)
    
    @patch('middleware.jwt_validator.jwt.decode')
    @patch('middleware.jwt_validator.requests.get')
    def test_validate_token_success(self, mock_get, mock_jwt_decode, jwt_validator):
        """Test successful token validation."""
        # Mock discovery document
        mock_discovery_response = Mock()
        mock_discovery_response.json.return_value = {
            "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "jwks_uri": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json"
        }
        mock_discovery_response.raise_for_status.return_value = None
        
        # Mock JWKS response
        mock_jwks_response = Mock()
        mock_jwks_response.json.return_value = {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-modulus",
                    "e": "AQAB"
                }
            ]
        }
        mock_jwks_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_discovery_response, mock_jwks_response]
        
        # Mock JWT decode
        valid_payload = {
            "sub": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "token_use": "access",
            "aud": "1ofgeckef3po4i3us4j1m4chvd",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        mock_jwt_decode.return_value = valid_payload
        
        # Test token validation
        token = "valid.jwt.token"
        user_context = jwt_validator.validate_token(token)
        
        assert user_context.user_id == "test-user-id"
        assert user_context.username == "testuser"
        assert user_context.email == "test@example.com"
        
        # Verify JWT decode was called with correct parameters
        mock_jwt_decode.assert_called_once()
        decode_args = mock_jwt_decode.call_args
        assert decode_args[0][0] == token  # Token
        assert "algorithms" in decode_args[1]
        assert "audience" in decode_args[1]
        assert "issuer" in decode_args[1]
    
    @patch('middleware.jwt_validator.jwt.decode')
    def test_validate_token_expired(self, mock_jwt_decode, jwt_validator):
        """Test validation of expired token."""
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
        
        with pytest.raises(JWTValidationError, match="Token has expired"):
            jwt_validator.validate_token("expired.jwt.token")
    
    @patch('middleware.jwt_validator.jwt.decode')
    def test_validate_token_invalid_signature(self, mock_jwt_decode, jwt_validator):
        """Test validation of token with invalid signature."""
        mock_jwt_decode.side_effect = jwt.InvalidSignatureError("Invalid signature")
        
        with pytest.raises(JWTValidationError, match="Invalid token signature"):
            jwt_validator.validate_token("invalid.signature.token")
    
    @patch('middleware.jwt_validator.jwt.decode')
    def test_validate_token_invalid_audience(self, mock_jwt_decode, jwt_validator):
        """Test validation of token with invalid audience."""
        mock_jwt_decode.side_effect = jwt.InvalidAudienceError("Invalid audience")
        
        with pytest.raises(JWTValidationError, match="Invalid token audience"):
            jwt_validator.validate_token("invalid.audience.token")
    
    @patch('middleware.jwt_validator.jwt.decode')
    def test_validate_token_invalid_issuer(self, mock_jwt_decode, jwt_validator):
        """Test validation of token with invalid issuer."""
        mock_jwt_decode.side_effect = jwt.InvalidIssuerError("Invalid issuer")
        
        with pytest.raises(JWTValidationError, match="Invalid token issuer"):
            jwt_validator.validate_token("invalid.issuer.token")
    
    @patch('middleware.jwt_validator.jwt.decode')
    def test_validate_token_malformed(self, mock_jwt_decode, jwt_validator):
        """Test validation of malformed token."""
        mock_jwt_decode.side_effect = jwt.DecodeError("Invalid token format")
        
        with pytest.raises(JWTValidationError, match="Invalid token format"):
            jwt_validator.validate_token("malformed.token")
    
    @patch('middleware.jwt_validator.jwt.decode')
    @patch('middleware.jwt_validator.requests.get')
    def test_validate_token_wrong_token_use(self, mock_get, mock_jwt_decode, jwt_validator):
        """Test validation of token with wrong token_use claim."""
        # Mock JWKS retrieval
        mock_discovery_response = Mock()
        mock_discovery_response.json.return_value = {
            "jwks_uri": "https://example.com/jwks"
        }
        mock_discovery_response.raise_for_status.return_value = None
        
        mock_jwks_response = Mock()
        mock_jwks_response.json.return_value = {"keys": []}
        mock_jwks_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_discovery_response, mock_jwks_response]
        
        # Mock JWT decode with wrong token_use
        invalid_payload = {
            "sub": "test-user-id",
            "token_use": "refresh",  # Should be "access"
            "aud": "1ofgeckef3po4i3us4j1m4chvd",
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn"
        }
        mock_jwt_decode.return_value = invalid_payload
        
        with pytest.raises(JWTValidationError, match="Invalid token use"):
            jwt_validator.validate_token("wrong.token.use")


class TestUserContextDataClass:
    """Test UserContext dataclass functionality."""
    
    def test_user_context_creation_full(self):
        """Test UserContext creation with all fields."""
        token_claims = {
            "sub": "user-123",
            "username": "testuser",
            "email": "test@example.com"
        }
        auth_time = datetime.now(timezone.utc)
        
        user_context = UserContext(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            token_claims=token_claims,
            authenticated_at=auth_time
        )
        
        assert user_context.user_id == "user-123"
        assert user_context.username == "testuser"
        assert user_context.email == "test@example.com"
        assert user_context.token_claims == token_claims
        assert user_context.authenticated_at == auth_time
    
    def test_user_context_creation_minimal(self):
        """Test UserContext creation with minimal fields."""
        user_context = UserContext(
            user_id="minimal-user",
            username="minimaluser"
        )
        
        assert user_context.user_id == "minimal-user"
        assert user_context.username == "minimaluser"
        assert user_context.email is None
        assert user_context.token_claims == {}
        assert isinstance(user_context.authenticated_at, datetime)
    
    def test_user_context_equality(self):
        """Test UserContext equality comparison."""
        auth_time = datetime.now(timezone.utc)
        
        user_context1 = UserContext(
            user_id="user-123",
            username="testuser",
            authenticated_at=auth_time
        )
        
        user_context2 = UserContext(
            user_id="user-123",
            username="testuser",
            authenticated_at=auth_time
        )
        
        user_context3 = UserContext(
            user_id="user-456",
            username="testuser",
            authenticated_at=auth_time
        )
        
        assert user_context1 == user_context2
        assert user_context1 != user_context3
    
    def test_user_context_string_representation(self):
        """Test UserContext string representation."""
        user_context = UserContext(
            user_id="user-123",
            username="testuser",
            email="test@example.com"
        )
        
        str_repr = str(user_context)
        assert "user-123" in str_repr
        assert "testuser" in str_repr
        assert "test@example.com" in str_repr


class TestJWTValidationErrorHandling:
    """Test JWT validation error handling scenarios."""
    
    def test_jwt_validation_error_creation(self):
        """Test JWTValidationError creation."""
        error = JWTValidationError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_jwt_validation_error_with_cause(self):
        """Test JWTValidationError with underlying cause."""
        original_error = ValueError("Original error")
        
        try:
            raise original_error
        except ValueError as e:
            jwt_error = JWTValidationError("JWT validation failed") from e
            
            assert str(jwt_error) == "JWT validation failed"
            assert jwt_error.__cause__ == original_error
    
    @pytest.fixture
    def jwt_validator(self):
        """Create JWT validator for error testing."""
        config = CognitoConfig(
            user_pool_id="us-east-1_TEST",
            client_id="test-client-id",
            region="us-east-1",
            discovery_url="https://test.example.com/.well-known/openid-configuration"
        )
        return JWTValidator(config)
    
    def test_validate_empty_token(self, jwt_validator):
        """Test validation of empty token."""
        with pytest.raises(JWTValidationError, match="Token cannot be empty"):
            jwt_validator.validate_token("")
    
    def test_validate_none_token(self, jwt_validator):
        """Test validation of None token."""
        with pytest.raises(JWTValidationError, match="Token cannot be empty"):
            jwt_validator.validate_token(None)
    
    def test_validate_whitespace_token(self, jwt_validator):
        """Test validation of whitespace-only token."""
        with pytest.raises(JWTValidationError, match="Token cannot be empty"):
            jwt_validator.validate_token("   ")
    
    @patch('middleware.jwt_validator.requests.get')
    def test_network_timeout_error(self, mock_get, jwt_validator):
        """Test handling of network timeout errors."""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve discovery document"):
            jwt_validator._get_discovery_document()
    
    @patch('middleware.jwt_validator.requests.get')
    def test_http_error_response(self, mock_get, jwt_validator):
        """Test handling of HTTP error responses."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve discovery document"):
            jwt_validator._get_discovery_document()
    
    @patch('middleware.jwt_validator.requests.get')
    def test_invalid_json_response(self, mock_get, jwt_validator):
        """Test handling of invalid JSON responses."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        with pytest.raises(JWTValidationError, match="Failed to retrieve discovery document"):
            jwt_validator._get_discovery_document()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])