"""
Integration tests for JWT Authentication Handler with existing components.

Tests the integration of JWT authentication with MCP client manager,
security monitoring, and audit logging components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

from services.jwt_auth_handler import JWTAuthHandler, AuthenticationContext
from services.security_monitor import get_security_monitor
from services.audit_logger import get_audit_logger, AuditEventType
from models.auth_models import CognitoConfig, JWTClaims, UserContext


class TestJWTIntegration:
    """Integration tests for JWT authentication system."""
    
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
    
    @pytest.mark.asyncio
    async def test_jwt_handler_with_security_monitoring(self, cognito_config, jwt_claims):
        """Test JWT handler integration with security monitoring."""
        with patch('services.jwt_auth_handler.get_security_monitor') as mock_get_monitor:
            with patch('services.jwt_auth_handler.boto3.client'):
                # Setup mock security monitor
                mock_monitor = Mock()
                mock_get_monitor.return_value = mock_monitor
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Mock token validation
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
                
                # Create authentication context
                auth_context = AuthenticationContext(
                    client_ip="192.168.1.100",
                    user_agent="Test Browser",
                    request_path="/api/restaurants",
                    request_method="POST",
                    timestamp=datetime.now(timezone.utc),
                    request_id="test-123"
                )
                
                # Validate token
                result = await jwt_handler.validate_request_token(
                    "Bearer valid.jwt.token", 
                    auth_context
                )
                
                # Verify successful validation
                assert result.is_valid is True
                assert result.user_context is not None
                assert result.user_context.user_id == jwt_claims.user_id
                
                # Verify security monitoring was called
                mock_monitor.log_authentication_attempt.assert_called_once()
                call_args = mock_monitor.log_authentication_attempt.call_args
                assert call_args[1]['success'] is True
                assert call_args[1]['user_context']['user_id'] == jwt_claims.user_id
    
    @pytest.mark.asyncio
    async def test_jwt_handler_with_audit_logging(self, cognito_config, jwt_claims):
        """Test JWT handler integration with audit logging."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                with patch('services.audit_logger.get_audit_logger') as mock_get_audit:
                    # Setup mock audit logger
                    mock_audit = Mock()
                    mock_get_audit.return_value = mock_audit
                    
                    # Create JWT handler
                    jwt_handler = JWTAuthHandler(cognito_config)
                    
                    # Mock token validation
                    jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
                    
                    # Create authentication context
                    auth_context = AuthenticationContext(
                        client_ip="10.0.1.50",
                        user_agent="Mobile App",
                        request_path="/api/search",
                        request_method="GET",
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Validate token
                    result = await jwt_handler.validate_request_token(
                        "Bearer valid.jwt.token",
                        auth_context
                    )
                    
                    # Verify successful validation
                    assert result.is_valid is True
                    
                    # Get audit logger and log authentication event
                    audit_logger = get_audit_logger()
                    audit_logger.log_authentication_event(
                        event_type=AuditEventType.TOKEN_VALIDATION,
                        user_context=result.user_context,
                        request_context={
                            'client_ip': auth_context.client_ip,
                            'user_agent': auth_context.user_agent,
                            'path': auth_context.request_path,
                            'method': auth_context.request_method
                        },
                        outcome="success"
                    )
    
    @pytest.mark.asyncio
    async def test_failed_authentication_monitoring(self, cognito_config):
        """Test failed authentication with security monitoring."""
        with patch('services.jwt_auth_handler.get_security_monitor') as mock_get_monitor:
            with patch('services.jwt_auth_handler.boto3.client'):
                # Setup mock security monitor
                mock_monitor = Mock()
                mock_get_monitor.return_value = mock_monitor
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Mock token validation failure
                from services.auth_service import AuthenticationError as AuthError
                auth_error = AuthError(
                    error_type="TOKEN_EXPIRED",
                    error_code="EXPIRED_SIGNATURE",
                    message="JWT token has expired",
                    details="Token expiration time has passed",
                    suggested_action="Refresh token"
                )
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
                
                # Create authentication context
                auth_context = AuthenticationContext(
                    client_ip="192.168.1.200",
                    user_agent="Suspicious Bot",
                    request_path="/api/admin",
                    request_method="POST",
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Validate token (should fail)
                result = await jwt_handler.validate_request_token(
                    "Bearer expired.jwt.token",
                    auth_context
                )
                
                # Verify failed validation
                assert result.is_valid is False
                assert result.error is not None
                assert result.error.error_code == "EXPIRED_SIGNATURE"
                
                # Verify security monitoring was called for failure
                mock_monitor.log_authentication_attempt.assert_called_once()
                call_args = mock_monitor.log_authentication_attempt.call_args
                assert call_args[1]['success'] is False
    
    def test_user_context_creation(self, jwt_claims):
        """Test user context creation from JWT claims."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                # Create JWT handler
                jwt_handler = JWTAuthHandler()
                
                # Create user context from claims
                user_context = jwt_handler._create_user_context(jwt_claims)
                
                # Verify user context
                assert user_context.user_id == jwt_claims.user_id
                assert user_context.username == jwt_claims.username
                assert user_context.email == jwt_claims.email
                assert user_context.authenticated is True
                assert user_context.token_claims == jwt_claims
    
    def test_authentication_context_creation(self):
        """Test authentication context creation."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                # Create JWT handler
                jwt_handler = JWTAuthHandler()
                
                # Create authentication context
                context = jwt_handler.create_authentication_context(
                    client_ip="172.16.0.100",
                    user_agent="Test Client",
                    request_path="/api/test",
                    request_method="PUT",
                    request_id="req-456"
                )
                
                # Verify context
                assert context.client_ip == "172.16.0.100"
                assert context.user_agent == "Test Client"
                assert context.request_path == "/api/test"
                assert context.request_method == "PUT"
                assert context.request_id == "req-456"
                assert isinstance(context.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_token_extraction_and_validation_flow(self, cognito_config, jwt_claims):
        """Test complete token extraction and validation flow."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Mock token validation
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
                
                # Test token extraction
                auth_header = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
                token = jwt_handler.extract_token_from_header(auth_header)
                assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
                
                # Test token validation
                validated_claims = await jwt_handler.validate_token_claims(token)
                assert validated_claims == jwt_claims
                
                # Test user context extraction
                user_context = jwt_handler._create_user_context(jwt_claims)
                assert user_context.user_id == jwt_claims.user_id
    
    def test_security_monitor_integration(self):
        """Test security monitor integration."""
        # Get security monitor instance
        security_monitor = get_security_monitor()
        
        # Verify it's properly initialized
        assert security_monitor is not None
        assert hasattr(security_monitor, 'log_authentication_attempt')
        assert hasattr(security_monitor, 'log_token_validation')
        assert hasattr(security_monitor, 'is_ip_blocked')
    
    def test_audit_logger_integration(self):
        """Test audit logger integration."""
        # Get audit logger instance
        audit_logger = get_audit_logger()
        
        # Verify it's properly initialized
        assert audit_logger is not None
        assert hasattr(audit_logger, 'log_authentication_event')
        assert hasattr(audit_logger, 'log_token_validation_event')
        assert hasattr(audit_logger, 'log_security_violation')
    
    @pytest.mark.asyncio
    async def test_cognito_user_info_integration(self, cognito_config):
        """Test Cognito user info retrieval integration."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client') as mock_boto:
                # Setup mock Cognito client
                mock_cognito = Mock()
                mock_boto.return_value = mock_cognito
                
                # Mock get_user response
                mock_cognito.get_user.return_value = {
                    'Username': 'testuser',
                    'UserAttributes': [
                        {'Name': 'email', 'Value': 'test@example.com'},
                        {'Name': 'cognito:user_status', 'Value': 'CONFIRMED'}
                    ],
                    'UserMFASettingList': [],
                    'PreferredMfaSetting': None
                }
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Get user info
                user_info = jwt_handler.get_cognito_user_info("valid.access.token")
                
                # Verify user info
                assert user_info['username'] == 'testuser'
                assert user_info['user_attributes']['email'] == 'test@example.com'
                assert user_info['user_attributes']['cognito:user_status'] == 'CONFIRMED'
                
                # Verify Cognito client was called
                mock_cognito.get_user.assert_called_once_with(AccessToken="valid.access.token")


if __name__ == "__main__":
    pytest.main([__file__])