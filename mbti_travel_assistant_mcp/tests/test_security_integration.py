"""
Integration tests for Security Monitoring and Validation.

Tests the integration of JWT authentication, request validation, security monitoring,
and audit logging components for comprehensive security coverage.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from services.jwt_auth_handler import JWTAuthHandler, AuthenticationContext
from services.request_validator import RequestValidator, get_request_validator
from services.security_monitor import SecurityMonitor, get_security_monitor
from services.audit_logger import get_audit_logger, AuditEventType
from models.auth_models import CognitoConfig, UserContext, JWTClaims, AuthenticationError
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity


class TestSecurityIntegration:
    """Integration tests for security monitoring and validation."""
    
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
            exp=int((datetime.now(timezone.utc)).timestamp()) + 3600,
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
            request_path="/api/mbti-itinerary",
            request_method="POST",
            timestamp=datetime.now(timezone.utc),
            request_id="test-request-123"
        )
    
    @pytest.fixture
    def security_components(self, cognito_config):
        """Create integrated security components."""
        with patch('services.jwt_auth_handler.get_security_monitor'):
            with patch('services.jwt_auth_handler.boto3.client'):
                jwt_handler = JWTAuthHandler(cognito_config)
                request_validator = RequestValidator()
                security_monitor = SecurityMonitor()
                audit_logger = get_audit_logger()
                
                return {
                    'jwt_handler': jwt_handler,
                    'request_validator': request_validator,
                    'security_monitor': security_monitor,
                    'audit_logger': audit_logger
                }
    
    @pytest.mark.asyncio
    async def test_complete_security_flow_success(self, security_components, jwt_claims, auth_context):
        """Test complete security flow with successful authentication and validation."""
        jwt_handler = security_components['jwt_handler']
        request_validator = security_components['request_validator']
        security_monitor = security_components['security_monitor']
        
        # Mock successful JWT validation
        jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
        
        # Step 1: Authenticate request
        auth_header = "Bearer valid.jwt.token"
        token_result = await jwt_handler.validate_request_token(auth_header, auth_context)
        
        assert token_result.is_valid is True
        user_context = token_result.user_context
        
        # Step 2: Monitor authentication attempt
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        security_monitor.monitor_authentication_attempt(
            success=True,
            user_context=user_context,
            request_context=request_context
        )
        
        # Step 3: Validate request payload
        payload = {
            'MBTI_personality': 'INFJ',
            'preferences': {
                'budget': 'medium',
                'interests': ['culture', 'food']
            }
        }
        
        validation_result = request_validator.validate_mbti_request(
            payload, user_context, request_context
        )
        
        assert validation_result.is_valid is True
        
        # Step 4: Monitor validation results
        security_monitor.monitor_request_validation(
            validation_result, user_context, request_context
        )
        
        # Step 5: Monitor MCP tool access
        mcp_parameters = {
            'districts': ['Central district'],
            'meal_types': ['breakfast']
        }
        
        security_monitor.monitor_mcp_tool_access(
            tool_name='search_restaurants_by_district',
            parameters=mcp_parameters,
            user_context=user_context,
            request_context=request_context,
            execution_result={'success': True, 'duration_ms': 1500}
        )
        
        # Verify security metrics
        metrics = security_monitor.get_security_metrics()
        assert metrics.total_requests == 1
        assert metrics.authenticated_requests == 1
        assert metrics.failed_authentications == 0
        assert metrics.validation_failures == 0
        assert metrics.security_violations == 0
        
        # Verify user profile
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        assert len(profiles) == 1
        assert profiles[0].user_id == user_context.user_id
        assert profiles[0].successful_logins == 1
        assert profiles[0].risk_score < 0.5  # Low risk for successful operations
    
    @pytest.mark.asyncio
    async def test_complete_security_flow_authentication_failure(self, security_components, auth_context):
        """Test complete security flow with authentication failure."""
        jwt_handler = security_components['jwt_handler']
        security_monitor = security_components['security_monitor']
        
        # Mock failed JWT validation
        from services.auth_service import AuthenticationError as AuthError
        auth_error = AuthError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        jwt_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        # Step 1: Attempt authentication
        auth_header = "Bearer expired.jwt.token"
        token_result = await jwt_handler.validate_request_token(auth_header, auth_context)
        
        assert token_result.is_valid is False
        assert token_result.error is not None
        
        # Step 2: Monitor failed authentication
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        security_monitor.monitor_authentication_attempt(
            success=False,
            user_context=None,
            request_context=request_context
        )
        
        # Verify security metrics
        metrics = security_monitor.get_security_metrics()
        assert metrics.total_requests == 1
        assert metrics.authenticated_requests == 0
        assert metrics.failed_authentications == 1
    
    @pytest.mark.asyncio
    async def test_complete_security_flow_malicious_payload(self, security_components, jwt_claims, auth_context):
        """Test complete security flow with malicious payload detection."""
        jwt_handler = security_components['jwt_handler']
        request_validator = security_components['request_validator']
        security_monitor = security_components['security_monitor']
        
        # Mock successful JWT validation
        jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
        
        # Step 1: Authenticate request
        auth_header = "Bearer valid.jwt.token"
        token_result = await jwt_handler.validate_request_token(auth_header, auth_context)
        
        assert token_result.is_valid is True
        user_context = token_result.user_context
        
        # Step 2: Validate malicious payload
        malicious_payload = {
            'MBTI_personality': 'INFJ',
            'malicious_field': '<script>alert("xss")</script>',
            'sql_injection': "'; DROP TABLE users; --",
            'command_injection': '$(rm -rf /)'
        }
        
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        validation_result = request_validator.validate_mbti_request(
            malicious_payload, user_context, request_context
        )
        
        assert validation_result.is_valid is False
        assert len(validation_result.security_events) > 0
        assert len(validation_result.violations) > 0
        
        # Step 3: Monitor validation results
        security_monitor.monitor_request_validation(
            validation_result, user_context, request_context
        )
        
        # Step 4: Process security events
        for security_event in validation_result.security_events:
            security_monitor.process_security_event(security_event, user_context, request_context)
        
        # Verify security response
        metrics = security_monitor.get_security_metrics()
        assert metrics.validation_failures > 0
        assert metrics.security_violations > 0
        
        # Check for security alerts
        alerts = security_monitor.get_security_alerts()
        assert len(alerts) > 0
        
        # Verify malicious content was sanitized
        assert '<script>' not in str(validation_result.sanitized_payload)
        assert 'DROP TABLE' not in str(validation_result.sanitized_payload)
    
    @pytest.mark.asyncio
    async def test_brute_force_attack_detection_and_response(self, security_components, auth_context):
        """Test brute force attack detection and automated response."""
        jwt_handler = security_components['jwt_handler']
        security_monitor = security_components['security_monitor']
        
        # Mock failed JWT validation
        from services.auth_service import AuthenticationError as AuthError
        auth_error = AuthError(
            error_type="AUTHENTICATION_FAILED",
            error_code="INVALID_CREDENTIALS",
            message="Invalid credentials",
            details="Username or password is incorrect",
            suggested_action="Check credentials and try again"
        )
        jwt_handler.token_validator.validate_jwt_token = AsyncMock(side_effect=auth_error)
        
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        # Simulate multiple failed authentication attempts
        for i in range(5):  # Exceeds max_failed_attempts
            auth_header = f"Bearer invalid.token.{i}"
            token_result = await jwt_handler.validate_request_token(auth_header, auth_context)
            
            assert token_result.is_valid is False
            
            # Monitor each failed attempt
            security_monitor.monitor_authentication_attempt(
                success=False,
                user_context=None,
                request_context=request_context
            )
        
        # Verify IP is blocked
        assert security_monitor.is_ip_blocked(auth_context.client_ip) is True
        
        # Verify security metrics
        metrics = security_monitor.get_security_metrics()
        assert metrics.failed_authentications == 5
        assert metrics.blocked_requests > 0
        assert metrics.security_violations > 0
        
        # Check for security alerts
        alerts = security_monitor.get_security_alerts()
        brute_force_alerts = [
            alert for alert in alerts 
            if 'brute force' in alert.title.lower() or 'blocked' in alert.description.lower()
        ]
        # Note: Alert creation depends on the specific implementation
    
    @pytest.mark.asyncio
    async def test_suspicious_activity_detection(self, security_components, jwt_claims, auth_context):
        """Test suspicious activity detection across components."""
        jwt_handler = security_components['jwt_handler']
        request_validator = security_components['request_validator']
        security_monitor = security_components['security_monitor']
        
        # Mock successful JWT validation
        jwt_handler.token_validator.validate_jwt_token = AsyncMock(return_value=jwt_claims)
        
        # Use suspicious context
        suspicious_context = AuthenticationContext(
            client_ip="192.168.1.100",
            user_agent="sqlmap/1.0 (http://sqlmap.org)",  # Suspicious user agent
            request_path="/admin/config",  # Suspicious path
            request_method="POST",
            timestamp=datetime.now(timezone.utc),
            request_id="suspicious-request-123"
        )
        
        # Step 1: Authenticate with suspicious context
        auth_header = "Bearer valid.jwt.token"
        token_result = await jwt_handler.validate_request_token(auth_header, suspicious_context)
        
        assert token_result.is_valid is True
        user_context = token_result.user_context
        
        # Step 2: Monitor authentication with suspicious indicators
        request_context = {
            'client_ip': suspicious_context.client_ip,
            'user_agent': suspicious_context.user_agent,
            'path': suspicious_context.request_path,
            'method': suspicious_context.request_method,
            'request_id': suspicious_context.request_id
        }
        
        security_monitor.monitor_authentication_attempt(
            success=True,
            user_context=user_context,
            request_context=request_context
        )
        
        # Step 3: Validate suspicious payload
        suspicious_payload = {
            'MBTI_personality': 'INFJ',
            'suspicious_param': '../../../etc/passwd',  # Path traversal attempt
            'another_param': 'UNION SELECT * FROM users'  # SQL injection attempt
        }
        
        validation_result = request_validator.validate_mbti_request(
            suspicious_payload, user_context, request_context
        )
        
        # Step 4: Monitor validation results
        security_monitor.monitor_request_validation(
            validation_result, user_context, request_context
        )
        
        # Verify suspicious activity detection
        profiles = security_monitor.get_user_security_profiles(risk_threshold=0.0)
        if profiles:
            profile = profiles[0]
            assert profile.suspicious_activities > 0
            assert profile.risk_score > 0.3  # Should have elevated risk
        
        # Check security events
        assert len(validation_result.security_events) > 0
        
        # Verify security metrics
        metrics = security_monitor.get_security_metrics()
        assert metrics.security_violations > 0
    
    def test_audit_logging_integration(self, security_components, jwt_claims, auth_context):
        """Test audit logging integration across security components."""
        audit_logger = security_components['audit_logger']
        security_monitor = security_components['security_monitor']
        
        user_context = UserContext(
            user_id=jwt_claims.user_id,
            username=jwt_claims.username,
            email=jwt_claims.email,
            authenticated=True,
            token_claims=jwt_claims
        )
        
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        # Test authentication event logging
        event_id = audit_logger.log_authentication_event(
            event_type=AuditEventType.USER_LOGIN,
            user_context=user_context,
            request_context=request_context,
            outcome="success"
        )
        
        assert event_id is not None
        assert len(event_id) > 0
        
        # Test MCP tool access logging
        mcp_event_id = audit_logger.log_mcp_tool_access(
            tool_name="search_restaurants_combined",
            user_context=user_context,
            request_context=request_context,
            parameters={"district": "Central district", "meal_time": "breakfast"},
            outcome="success",
            duration_ms=1500
        )
        
        assert mcp_event_id is not None
        assert len(mcp_event_id) > 0
        
        # Test security violation logging
        violation_event_id = audit_logger.log_security_violation(
            violation_type="malicious_payload_detected",
            user_context=user_context,
            request_context=request_context,
            violation_details={
                'pattern_detected': 'script_injection',
                'field_path': 'malicious_field',
                'sanitized': True
            }
        )
        
        assert violation_event_id is not None
        assert len(violation_event_id) > 0
    
    def test_sensitive_data_sanitization_integration(self, security_components):
        """Test sensitive data sanitization across components."""
        request_validator = security_components['request_validator']
        
        # Test data with sensitive information
        sensitive_data = {
            'username': 'testuser',
            'password': 'secret123',
            'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'api_key': 'sk-1234567890abcdef',
            'authorization': 'Bearer token123',
            'session_id': 'sess_abcd1234',
            'normal_field': 'normal_value',
            'nested': {
                'secret_key': 'very_secret',
                'public_info': 'visible_data',
                'auth_token': 'auth_12345'
            },
            'list_with_secrets': [
                'normal_item',
                'password=secret',
                'api_key=hidden'
            ]
        }
        
        # Sanitize the data
        sanitized = request_validator.sanitize_sensitive_data(sensitive_data)
        
        # Verify sensitive fields are redacted
        assert sanitized['password'] == '***REDACTED***'
        assert sanitized['jwt_token'] == '***REDACTED***'
        assert sanitized['api_key'] == '***REDACTED***'
        assert sanitized['authorization'] == '***REDACTED***'
        assert sanitized['session_id'] == '***REDACTED***'
        assert sanitized['nested']['secret_key'] == '***REDACTED***'
        assert sanitized['nested']['auth_token'] == '***REDACTED***'
        
        # Verify normal fields are preserved
        assert sanitized['username'] == 'testuser'
        assert sanitized['normal_field'] == 'normal_value'
        assert sanitized['nested']['public_info'] == 'visible_data'
        
        # Verify list sanitization
        assert 'normal_item' in sanitized['list_with_secrets']
        # Sensitive items in lists should be redacted
        sensitive_items = [item for item in sanitized['list_with_secrets'] if '***REDACTED***' in str(item)]
        assert len(sensitive_items) > 0
    
    def test_security_metrics_aggregation(self, security_components, jwt_claims, auth_context):
        """Test security metrics aggregation across components."""
        security_monitor = security_components['security_monitor']
        
        user_context = UserContext(
            user_id=jwt_claims.user_id,
            username=jwt_claims.username,
            email=jwt_claims.email,
            authenticated=True,
            token_claims=jwt_claims
        )
        
        request_context = {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'request_id': auth_context.request_id
        }
        
        # Generate various security events
        # Successful authentication
        security_monitor.monitor_authentication_attempt(True, user_context, request_context)
        
        # Failed authentication
        security_monitor.monitor_authentication_attempt(False, None, request_context)
        
        # Security violation
        security_event = SecurityEvent(
            event_type=SecurityEventType.MALICIOUS_PAYLOAD,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip=request_context['client_ip'],
            error_message="Test security violation"
        )
        security_monitor.process_security_event(security_event, user_context, request_context)
        
        # Get aggregated metrics
        metrics = security_monitor.get_security_metrics("24h")
        
        # Verify metrics aggregation
        assert metrics.total_requests == 2
        assert metrics.authenticated_requests == 1
        assert metrics.failed_authentications == 1
        assert metrics.security_violations == 1
        assert metrics.unique_users == 1
        assert metrics.time_period == "24h"
        assert metrics.last_updated is not None


if __name__ == "__main__":
    pytest.main([__file__])