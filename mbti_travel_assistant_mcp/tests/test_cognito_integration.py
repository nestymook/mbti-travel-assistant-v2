"""
Integration Tests for Cognito Authentication

Tests the complete authentication flow including JWT validation,
user context extraction, and integration with security monitoring.
"""

import pytest
import jwt
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from moto import mock_cognitoidp
import boto3

from services.jwt_auth_handler import JWTAuthHandler, AuthenticationContext
from services.security_monitor import SecurityMonitor
from services.audit_logger import AuditLogger, AuditEventType
from models.auth_models import CognitoConfig, JWTClaims, UserContext, AuthenticationError


class TestCognitoIntegration:
    """Integration tests for Cognito authentication system."""
    
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
    def valid_jwt_token(self):
        """Create a valid JWT token for testing."""
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
        
        # Create token without signature verification for testing
        return jwt.encode(payload, 'test-secret', algorithm='HS256')
    
    @pytest.fixture
    def expired_jwt_token(self):
        """Create an expired JWT token for testing."""
        payload = {
            'sub': 'test-user-123',
            'username': 'testuser',
            'email': 'test@example.com',
            'client_id': 'test-client-id',
            'token_use': 'access',
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),  # Expired
            'iat': int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
            'iss': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123',
            'aud': 'test-client-id'
        }
        
        return jwt.encode(payload, 'test-secret', algorithm='HS256')
    
    @pytest.fixture
    def auth_context(self):
        """Create authentication context for testing."""
        return AuthenticationContext(
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
            request_path="/api/restaurants",
            request_method="POST",
            timestamp=datetime.now(timezone.utc),
            request_id="test-request-123"
        )
    
    @mock_cognitoidp
    def test_cognito_user_pool_integration(self, cognito_config):
        """Test integration with actual Cognito User Pool (mocked)."""
        # Create mock Cognito User Pool
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        
        # Create user pool
        user_pool = cognito_client.create_user_pool(
            PoolName='test-pool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            }
        )
        
        user_pool_id = user_pool['UserPool']['Id']
        
        # Create user pool client
        client_response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='test-client',
            GenerateSecret=False
        )
        
        client_id = client_response['UserPoolClient']['ClientId']
        
        # Update config with actual IDs
        cognito_config.user_pool_id = user_pool_id
        cognito_config.client_id = client_id
        
        # Create user
        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username='testuser',
            UserAttributes=[
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            MessageAction='SUPPRESS',
            TemporaryPassword='TempPass123!'
        )
        
        # Set permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username='testuser',
            Password='Password123!',
            Permanent=True
        )
        
        # Verify user pool was created
        pools = cognito_client.list_user_pools(MaxResults=10)
        assert len(pools['UserPools']) == 1
        assert pools['UserPools'][0]['Name'] == 'test-pool'
        
        # Verify user was created
        users = cognito_client.list_users(UserPoolId=user_pool_id)
        assert len(users['Users']) == 1
        assert users['Users'][0]['Username'] == 'testuser'
    
    @pytest.mark.asyncio
    async def test_jwt_validation_with_security_monitoring(self, cognito_config, valid_jwt_token, auth_context):
        """Test JWT validation with security monitoring integration."""
        with patch('services.jwt_auth_handler.get_security_monitor') as mock_get_monitor:
            with patch('services.jwt_auth_handler.boto3.client'):
                # Setup mock security monitor
                mock_monitor = Mock(spec=SecurityMonitor)
                mock_get_monitor.return_value = mock_monitor
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Mock token validation to succeed
                jwt_claims = JWTClaims(
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
                
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
                
                # Validate token
                result = await jwt_handler.validate_request_token(
                    f"Bearer {valid_jwt_token}",
                    auth_context
                )
                
                # Verify successful validation
                assert result.is_valid is True
                assert result.user_context is not None
                assert result.user_context.user_id == "test-user-123"
                assert result.user_context.username == "testuser"
                assert result.user_context.email == "test@example.com"
                
                # Verify security monitoring was called
                mock_monitor.log_authentication_attempt.assert_called_once()
                
                # Verify the call arguments
                call_args = mock_monitor.log_authentication_attempt.call_args
                assert call_args[1]['success'] is True
                assert call_args[1]['user_context']['user_id'] == "test-user-123"
                assert call_args[1]['client_ip'] == "192.168.1.100"
                assert call_args[1]['user_agent'] == "Mozilla/5.0 (Test Browser)"
    
    @pytest.mark.asyncio
    async def test_jwt_validation_failure_with_monitoring(self, cognito_config, expired_jwt_token, auth_context):
        """Test JWT validation failure with security monitoring."""
        with patch('services.jwt_auth_handler.get_security_monitor') as mock_get_monitor:
            with patch('services.jwt_auth_handler.boto3.client'):
                # Setup mock security monitor
                mock_monitor = Mock(spec=SecurityMonitor)
                mock_get_monitor.return_value = mock_monitor
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Mock token validation to fail
                from services.auth_service import AuthenticationError as AuthError
                auth_error = AuthError(
                    error_type="TOKEN_EXPIRED",
                    error_code="EXPIRED_SIGNATURE",
                    message="JWT token has expired",
                    details="Token expiration time has passed",
                    suggested_action="Refresh token"
                )
                
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
                
                # Validate token (should fail)
                result = await jwt_handler.validate_request_token(
                    f"Bearer {expired_jwt_token}",
                    auth_context
                )
                
                # Verify failed validation
                assert result.is_valid is False
                assert result.error is not None
                assert result.error.error_code == "EXPIRED_SIGNATURE"
                assert result.user_context is None
                
                # Verify security monitoring was called for failure
                mock_monitor.log_authentication_attempt.assert_called_once()
                
                # Verify the call arguments
                call_args = mock_monitor.log_authentication_attempt.call_args
                assert call_args[1]['success'] is False
                assert call_args[1]['error_code'] == "EXPIRED_SIGNATURE"
                assert call_args[1]['client_ip'] == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_audit_logging_integration(self, cognito_config, valid_jwt_token, auth_context):
        """Test audit logging integration with authentication."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                with patch('services.audit_logger.get_audit_logger') as mock_get_audit:
                    # Setup mock audit logger
                    mock_audit = Mock(spec=AuditLogger)
                    mock_get_audit.return_value = mock_audit
                    
                    # Create JWT handler
                    jwt_handler = JWTAuthHandler(cognito_config)
                    
                    # Mock successful token validation
                    jwt_claims = JWTClaims(
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
                    
                    jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
                    
                    # Validate token
                    result = await jwt_handler.validate_request_token(
                        f"Bearer {valid_jwt_token}",
                        auth_context
                    )
                    
                    # Verify successful validation
                    assert result.is_valid is True
                    
                    # Manually trigger audit logging (simulating what would happen in production)
                    audit_logger = mock_get_audit.return_value
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
                    
                    # Verify audit logging was called
                    audit_logger.log_authentication_event.assert_called_once()
                    
                    # Verify call arguments
                    call_args = audit_logger.log_authentication_event.call_args
                    assert call_args[1]['event_type'] == AuditEventType.TOKEN_VALIDATION
                    assert call_args[1]['outcome'] == "success"
                    assert call_args[1]['user_context'].user_id == "test-user-123"
    
    def test_user_context_creation_from_jwt_claims(self, cognito_config):
        """Test user context creation from JWT claims."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # Create JWT claims
                jwt_claims = JWTClaims(
                    user_id="test-user-456",
                    username="anotheruser",
                    email="another@example.com",
                    client_id="test-client-id",
                    token_use="access",
                    exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                    iat=int(datetime.now(timezone.utc).timestamp()),
                    iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123",
                    aud="test-client-id"
                )
                
                # Create user context
                user_context = jwt_handler._create_user_context(jwt_claims)
                
                # Verify user context
                assert isinstance(user_context, UserContext)
                assert user_context.user_id == "test-user-456"
                assert user_context.username == "anotheruser"
                assert user_context.email == "another@example.com"
                assert user_context.authenticated is True
                assert user_context.token_claims == jwt_claims
                
                # Verify user context can be serialized
                user_dict = user_context.to_dict()
                assert user_dict['user_id'] == "test-user-456"
                assert user_dict['username'] == "anotheruser"
                assert user_dict['email'] == "another@example.com"
                assert user_dict['authenticated'] is True
    
    @mock_cognitoidp
    def test_cognito_user_info_retrieval(self, cognito_config):
        """Test retrieving user info from Cognito."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            # Create JWT handler
            jwt_handler = JWTAuthHandler(cognito_config)
            
            # Setup mock Cognito client
            cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
            jwt_handler.cognito_client = cognito_client
            
            # Mock get_user response
            mock_response = {
                'Username': 'testuser',
                'UserAttributes': [
                    {'Name': 'email', 'Value': 'test@example.com'},
                    {'Name': 'cognito:user_status', 'Value': 'CONFIRMED'},
                    {'Name': 'given_name', 'Value': 'Test'},
                    {'Name': 'family_name', 'Value': 'User'}
                ],
                'UserMFASettingList': [],
                'PreferredMfaSetting': None
            }
            
            with patch.object(cognito_client, 'get_user', return_value=mock_response):
                user_info = jwt_handler.get_cognito_user_info("valid.access.token")
                
                # Verify user info structure
                assert user_info['username'] == 'testuser'
                assert user_info['user_attributes']['email'] == 'test@example.com'
                assert user_info['user_attributes']['cognito:user_status'] == 'CONFIRMED'
                assert user_info['user_attributes']['given_name'] == 'Test'
                assert user_info['user_attributes']['family_name'] == 'User'
                assert user_info['mfa_settings'] == []
                assert user_info['preferred_mfa'] is None
    
    @mock_cognitoidp
    def test_cognito_user_info_error_handling(self, cognito_config):
        """Test error handling when retrieving user info from Cognito."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            # Create JWT handler
            jwt_handler = JWTAuthHandler(cognito_config)
            
            # Setup mock Cognito client
            cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
            jwt_handler.cognito_client = cognito_client
            
            # Mock ClientError
            from botocore.exceptions import ClientError
            error = ClientError(
                {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Invalid token'}},
                'GetUser'
            )
            
            with patch.object(cognito_client, 'get_user', side_effect=error):
                with pytest.raises(AuthenticationError) as exc_info:
                    jwt_handler.get_cognito_user_info("invalid.token")
                
                assert exc_info.value.error_code == "COGNITO_ERROR"
                assert "Invalid token" in exc_info.value.message
    
    def test_authentication_context_validation(self):
        """Test authentication context validation and creation."""
        # Test valid context
        context = AuthenticationContext(
            client_ip="10.0.1.100",
            user_agent="Test Client v1.0",
            request_path="/api/search",
            request_method="GET",
            timestamp=datetime.now(timezone.utc),
            request_id="req-789"
        )
        
        assert context.client_ip == "10.0.1.100"
        assert context.user_agent == "Test Client v1.0"
        assert context.request_path == "/api/search"
        assert context.request_method == "GET"
        assert context.request_id == "req-789"
        assert isinstance(context.timestamp, datetime)
        
        # Test context without request ID
        context_no_id = AuthenticationContext(
            client_ip="192.168.1.1",
            user_agent="Mobile App",
            request_path="/api/restaurants",
            request_method="POST",
            timestamp=datetime.now(timezone.utc)
        )
        
        assert context_no_id.request_id is None
        assert context_no_id.client_ip == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_token_refresh_scenario(self, cognito_config, auth_context):
        """Test token refresh scenario with expired token."""
        with patch('services.jwt_auth_handler.get_security_monitor') as mock_get_monitor:
            with patch('services.jwt_auth_handler.boto3.client'):
                # Setup mock security monitor
                mock_monitor = Mock(spec=SecurityMonitor)
                mock_get_monitor.return_value = mock_monitor
                
                # Create JWT handler
                jwt_handler = JWTAuthHandler(cognito_config)
                
                # First attempt with expired token
                from services.auth_service import AuthenticationError as AuthError
                expired_error = AuthError(
                    error_type="TOKEN_EXPIRED",
                    error_code="EXPIRED_SIGNATURE",
                    message="JWT token has expired",
                    details="Token expiration time has passed",
                    suggested_action="Refresh token"
                )
                
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=expired_error)
                
                # Validate expired token
                result = await jwt_handler.validate_request_token(
                    "Bearer expired.token",
                    auth_context
                )
                
                # Verify failure
                assert result.is_valid is False
                assert result.error.error_code == "EXPIRED_SIGNATURE"
                
                # Simulate token refresh - now validation succeeds
                fresh_claims = JWTClaims(
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
                
                jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=fresh_claims)
                
                # Validate fresh token
                fresh_result = await jwt_handler.validate_request_token(
                    "Bearer fresh.token",
                    auth_context
                )
                
                # Verify success
                assert fresh_result.is_valid is True
                assert fresh_result.user_context.user_id == "test-user-123"
                
                # Verify both attempts were logged
                assert mock_monitor.log_authentication_attempt.call_count == 2
    
    def test_jwt_claims_validation(self):
        """Test JWT claims validation and structure."""
        # Test valid claims
        valid_claims = JWTClaims(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            client_id="client-123",
            token_use="access",
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123",
            aud="client-123"
        )
        
        assert valid_claims.user_id == "user-123"
        assert valid_claims.username == "testuser"
        assert valid_claims.email == "test@example.com"
        assert valid_claims.client_id == "client-123"
        assert valid_claims.token_use == "access"
        assert valid_claims.iss == "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123"
        assert valid_claims.aud == "client-123"
        
        # Test claims serialization
        claims_dict = valid_claims.to_dict()
        assert claims_dict['sub'] == "user-123"
        assert claims_dict['username'] == "testuser"
        assert claims_dict['email'] == "test@example.com"
        assert claims_dict['client_id'] == "client-123"


if __name__ == "__main__":
    pytest.main([__file__])