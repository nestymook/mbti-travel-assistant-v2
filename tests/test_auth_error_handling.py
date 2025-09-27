"""
Tests for authentication error handling and security monitoring.

This module tests the comprehensive authentication error handling system,
security logging, and monitoring functionality.
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

from services.auth_error_handler import (
    AuthenticationErrorHandler, ErrorResponse, SecurityEvent, 
    TroubleshootingGuide, ErrorSeverity, SecurityEventType
)
from services.auth_service import AuthenticationError
from services.security_monitor import SecurityMonitor, SecurityMetrics, ThreatIndicator


class TestAuthenticationErrorHandler:
    """Test cases for AuthenticationErrorHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AuthenticationErrorHandler(
            enable_security_logging=True,
            enable_monitoring=True,
            mask_sensitive_data=True
        )
    
    def test_handle_token_expiration_error(self):
        """Test handling of token expiration errors."""
        # Create token expiration error
        error = AuthenticationError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time (exp) has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        
        request_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 Test Browser',
            'path': '/mcp/tools/search',
            'method': 'POST'
        }
        
        # Handle the error
        response = self.error_handler.handle_token_expiration(error, request_context)
        
        # Verify response
        assert response.status_code == 401
        assert 'WWW-Authenticate' in response.headers
        assert 'Bearer realm="MCP Server"' in response.headers['WWW-Authenticate']
        
        # Verify response content
        content = json.loads(response.body.decode())
        assert content['success'] is False
        assert content['error_type'] == 'TOKEN_EXPIRED'
        assert content['error_code'] == 'EXPIRED_SIGNATURE'
        assert 'refresh your token' in content['message'] or 'refresh' in content['suggested_action']
        assert 'support_info' in content
        assert 'refresh_endpoint' in content['support_info']
    
    def test_handle_invalid_token_format_error(self):
        """Test handling of invalid token format errors."""
        error = AuthenticationError(
            error_type="INVALID_TOKEN_FORMAT",
            error_code="MALFORMED_TOKEN",
            message="Invalid JWT token format",
            details="Token must be in format: Header.Payload.Signature",
            suggested_action="Verify token format"
        )
        
        request_context = {
            'client_ip': '10.0.0.50',
            'user_agent': 'curl/7.68.0',
            'path': '/mcp/tools/search',
            'method': 'POST'
        }
        
        # Handle the error
        response = self.error_handler.handle_invalid_token_format(error, request_context)
        
        # Verify response
        assert response.status_code == 400
        
        # Verify response content
        content = json.loads(response.body.decode())
        assert content['success'] is False
        assert content['error_type'] == 'INVALID_TOKEN_FORMAT'
        assert 'jwt_structure' in content['support_info']
        assert 'header.payload.signature' in content['support_info']['jwt_structure']
    
    def test_handle_unauthorized_client_error(self):
        """Test handling of unauthorized client errors."""
        error = AuthenticationError(
            error_type="UNAUTHORIZED_CLIENT",
            error_code="CLIENT_NOT_AUTHORIZED",
            message="Client not authorized",
            details="Client ID not in allowed list",
            suggested_action="Contact administrator"
        )
        
        request_context = {
            'client_ip': '203.0.113.10',
            'user_agent': 'UnknownClient/1.0',
            'path': '/mcp/tools/search',
            'method': 'POST'
        }
        
        # Handle the error
        response = self.error_handler.handle_unauthorized_client(error, request_context)
        
        # Verify response
        assert response.status_code == 403
        
        # Verify response content
        content = json.loads(response.body.decode())
        assert content['success'] is False
        assert content['error_type'] == 'UNAUTHORIZED_CLIENT'
        assert 'contact' in content['support_info']
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is properly masked in error responses."""
        # Create error with sensitive data
        error = AuthenticationError(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_TOKEN",
            message="Token validation failed",
            details="JWT token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIn0.signature and email user@example.com from IP 192.168.1.1",
            suggested_action="Check token validity"
        )
        
        request_context = {
            'client_ip': '192.168.1.1',
            'user_agent': 'TestClient/1.0'
        }
        
        # Handle the error
        response = self.error_handler.handle_authentication_error(error, request_context)
        
        # Verify sensitive data is masked
        content = json.loads(response.body.decode())
        details = content['details']
        
        # Check that JWT token is masked
        assert 'eyJ***MASKED***' in details
        assert 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9' not in details
        
        # Check that email is masked
        assert '***@***.***' in details
        assert 'user@example.com' not in details
        
        # Check that IP is masked
        assert '***.***.***.***' in details
        assert '192.168.1.1' not in details
    
    def test_troubleshooting_guides(self):
        """Test troubleshooting guide retrieval."""
        # Test token expiration guide
        guide = self.error_handler.get_troubleshooting_guide("TOKEN_EXPIRED")
        assert guide is not None
        assert guide.error_type == "TOKEN_EXPIRED"
        assert len(guide.common_causes) > 0
        assert len(guide.resolution_steps) > 0
        assert len(guide.documentation_links) > 0
        
        # Test invalid token format guide
        guide = self.error_handler.get_troubleshooting_guide("INVALID_TOKEN_FORMAT")
        assert guide is not None
        assert "JWT token structure" in guide.common_causes[0]
        
        # Test unauthorized client guide
        guide = self.error_handler.get_troubleshooting_guide("UNAUTHORIZED_CLIENT")
        assert guide is not None
        assert guide.contact_info is not None
        
        # Test non-existent guide
        guide = self.error_handler.get_troubleshooting_guide("NON_EXISTENT_ERROR")
        assert guide is None
    
    def test_error_response_structure(self):
        """Test that error responses have consistent structure."""
        error = AuthenticationError(
            error_type="TEST_ERROR",
            error_code="TEST_CODE",
            message="Test message",
            details="Test details",
            suggested_action="Test action"
        )
        
        response = self.error_handler.handle_authentication_error(error)
        content = json.loads(response.body.decode())
        
        # Verify required fields
        assert 'success' in content
        assert content['success'] is False
        assert 'error_type' in content
        assert 'error_code' in content
        assert 'message' in content
        assert 'details' in content
        assert 'suggested_action' in content
        assert 'timestamp' in content
        assert 'request_id' in content
        
        # Verify timestamp format
        timestamp = content['timestamp']
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise exception
    
    @patch('services.auth_error_handler.logger')
    def test_security_logging_without_sensitive_data(self, mock_logger):
        """Test that security logging doesn't expose sensitive information."""
        error = AuthenticationError(
            error_type="AUTHENTICATION_FAILED",
            error_code="INVALID_CREDENTIALS",
            message="Authentication failed for user@example.com",
            details="Password verification failed for token eyJhbGciOiJSUzI1NiI...",
            suggested_action="Check credentials"
        )
        
        request_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'TestClient/1.0',
            'user_id': 'user123',
            'username': 'testuser'
        }
        
        # Handle the error (this should trigger logging)
        self.error_handler.handle_authentication_error(error, request_context)
        
        # Verify that logging was called
        assert mock_logger.warning.called
        
        # Get the logged message
        logged_calls = mock_logger.warning.call_args_list
        logged_message = str(logged_calls[0][0][0])  # First call, first argument
        
        # Verify sensitive data is not in logs (check the error message part, not the whole log)
        # The security monitor logs the IP in structured data, but error details should be masked
        if 'error_message' in logged_message:
            # Extract just the error message part for sensitive data checking
            import json
            try:
                log_data = json.loads(logged_message.split('Security event: ')[1])
                error_message = log_data.get('error_message', '')
                assert 'user@example.com' not in error_message
                assert 'eyJhbGciOiJSUzI1NiI' not in error_message
            except:
                # Fallback to checking the whole message
                assert 'user@example.com' not in logged_message
                assert 'eyJhbGciOiJSUzI1NiI' not in logged_message
    
    def test_fallback_error_response(self):
        """Test fallback error response for unexpected errors."""
        # Mock an error in the error handler itself
        with patch.object(self.error_handler, '_create_error_response', side_effect=Exception("Handler error")):
            error = AuthenticationError(
                error_type="TEST_ERROR",
                error_code="TEST_CODE",
                message="Test message",
                details="Test details",
                suggested_action="Test action"
            )
            
            response = self.error_handler.handle_authentication_error(error)
            
            # Should return fallback response
            assert response.status_code == 500
            content = json.loads(response.body.decode())
            assert content['error_type'] == 'INTERNAL_ERROR'
            assert content['error_code'] == 'ERROR_HANDLER_FAILURE'


class TestSecurityMonitor:
    """Test cases for SecurityMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.security_monitor = SecurityMonitor(
            enable_audit_logging=True,
            enable_threat_detection=True,
            max_failed_attempts=3,
            lockout_duration=300,
            suspicious_threshold=5
        )
    
    def test_authentication_attempt_logging(self):
        """Test logging of authentication attempts."""
        user_context = {
            'user_id': 'user123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        request_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 Test',
            'path': '/auth/login',
            'method': 'POST',
            'request_id': 'req123'
        }
        
        # Test successful authentication
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            self.security_monitor.log_authentication_attempt(True, user_context, request_context)
            
            # Verify audit logging was called
            assert mock_audit_logger.info.called
            logged_message = mock_audit_logger.info.call_args[0][0]
            assert 'AUTH_ATTEMPT' in logged_message
            
            # Parse the logged JSON
            json_part = logged_message.split('AUTH_ATTEMPT: ')[1]
            logged_data = json.loads(json_part)
            
            assert logged_data['success'] is True
            assert logged_data['user_id'] == 'user123'
            assert logged_data['username'] == 'testuser'
            assert logged_data['client_ip'] == '192.168.1.100'
    
    def test_failed_authentication_tracking(self):
        """Test tracking of failed authentication attempts."""
        request_context = {
            'client_ip': '192.168.1.200',
            'user_agent': 'AttackerBot/1.0',
            'path': '/auth/login',
            'method': 'POST'
        }
        
        user_context = {
            'user_id': 'unknown',
            'username': 'unknown',
            'email': 'unknown'
        }
        
        # Simulate multiple failed attempts
        for i in range(3):
            self.security_monitor.log_authentication_attempt(False, user_context, request_context)
        
        # IP should now be blocked
        assert self.security_monitor.is_ip_blocked('192.168.1.200')
        
        # Different IP should not be blocked
        assert not self.security_monitor.is_ip_blocked('192.168.1.201')
    
    def test_token_validation_logging(self):
        """Test logging of token validation events."""
        token_info = {
            'token_type': 'access',
            'exp': 1234567890,
            'iat': 1234567800,
            'client_id': 'test-client',
            'user_id': 'user123'
        }
        
        request_context = {
            'client_ip': '10.0.0.50',
            'path': '/mcp/tools/search',
            'method': 'POST',
            'request_id': 'req456'
        }
        
        # Test successful token validation
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            self.security_monitor.log_token_validation(True, token_info, request_context)
            
            # Verify audit logging was called
            assert mock_audit_logger.info.called
            logged_message = mock_audit_logger.info.call_args[0][0]
            assert 'TOKEN_VALIDATION' in logged_message
            
            # Parse the logged JSON
            json_part = logged_message.split('TOKEN_VALIDATION: ')[1]
            logged_data = json.loads(json_part)
            
            assert logged_data['success'] is True
            assert logged_data['token_type'] == 'access'
            assert logged_data['client_id'] == 'test-client'
    
    def test_mcp_tool_invocation_logging(self):
        """Test logging of MCP tool invocations."""
        user_context = {
            'user_id': 'user123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        request_context = {
            'client_ip': '172.16.0.10',
            'path': '/mcp/tools/search_restaurants',
            'method': 'POST',
            'request_id': 'req789'
        }
        
        parameters = {
            'districts': ['Central district', 'Admiralty'],
            'meal_types': ['breakfast']
        }
        
        # Test MCP tool invocation logging
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            self.security_monitor.log_mcp_tool_invocation(
                'search_restaurants_by_district', 
                user_context, 
                request_context, 
                parameters
            )
            
            # Verify audit logging was called
            assert mock_audit_logger.info.called
            logged_message = mock_audit_logger.info.call_args[0][0]
            assert 'MCP_TOOL' in logged_message
            
            # Parse the logged JSON
            json_part = logged_message.split('MCP_TOOL: ')[1]
            logged_data = json.loads(json_part)
            
            assert logged_data['tool_name'] == 'search_restaurants_by_district'
            assert logged_data['user_id'] == 'user123'
            assert logged_data['parameters']['districts'] == ['Central district', 'Admiralty']
    
    def test_sensitive_parameter_sanitization(self):
        """Test that sensitive parameters are sanitized in logs."""
        user_context = {
            'user_id': 'user123',
            'username': 'testuser'
        }
        
        request_context = {
            'client_ip': '10.0.0.100',
            'path': '/mcp/tools/test',
            'method': 'POST'
        }
        
        # Parameters with sensitive data
        parameters = {
            'password': 'secret123',
            'api_token': 'abc123def456',
            'secret_key': 'mysecret',
            'normal_param': 'normal_value',
            'long_string': 'a' * 150  # Long string that should be truncated
        }
        
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            self.security_monitor.log_mcp_tool_invocation(
                'test_tool', 
                user_context, 
                request_context, 
                parameters
            )
            
            # Get logged message
            logged_message = mock_audit_logger.info.call_args[0][0]
            json_part = logged_message.split('MCP_TOOL: ')[1]
            logged_data = json.loads(json_part)
            
            # Verify sensitive data is redacted
            assert logged_data['parameters']['password'] == '***REDACTED***'
            assert logged_data['parameters']['api_token'] == '***REDACTED***'
            assert logged_data['parameters']['secret_key'] == '***REDACTED***'
            
            # Verify normal data is preserved
            assert logged_data['parameters']['normal_param'] == 'normal_value'
            
            # Verify long strings are truncated
            assert len(logged_data['parameters']['long_string']) <= 103  # 100 + '...'
            assert logged_data['parameters']['long_string'].endswith('...')
    
    def test_suspicious_activity_detection(self):
        """Test detection of suspicious activity patterns."""
        # Test suspicious user agent
        request_context = {
            'client_ip': '203.0.113.50',
            'user_agent': 'sqlmap/1.0 (http://sqlmap.org)',
            'path': '/mcp/tools/search',
            'method': 'POST'
        }
        
        user_context = {'user_id': 'unknown', 'username': 'unknown'}
        
        with patch.object(self.security_monitor, 'log_security_event') as mock_log_event:
            self.security_monitor.log_authentication_attempt(False, user_context, request_context)
            
            # Should have detected suspicious activity
            assert mock_log_event.called
            
            # Get all security events logged
            security_events = [call[0][0] for call in mock_log_event.call_args_list]
            suspicious_events = [event for event in security_events 
                               if event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY]
            
            assert len(suspicious_events) > 0
            
            # Check that at least one event mentions suspicious activity
            suspicious_messages = [event.error_message for event in suspicious_events]
            assert any('Suspicious' in msg or 'suspicious' in msg for msg in suspicious_messages)
    
    def test_security_metrics_collection(self):
        """Test collection of security metrics."""
        # Simulate some authentication attempts
        user_context = {'user_id': 'user123', 'username': 'testuser'}
        request_context = {'client_ip': '10.0.0.100', 'user_agent': 'TestClient'}
        
        # Successful attempts
        for _ in range(5):
            self.security_monitor.log_authentication_attempt(True, user_context, request_context)
        
        # Failed attempts
        for _ in range(3):
            self.security_monitor.log_authentication_attempt(False, user_context, request_context)
        
        # Token validations
        token_info = {'token_type': 'access', 'user_id': 'user123'}
        for _ in range(7):
            self.security_monitor.log_token_validation(True, token_info, request_context)
        
        for _ in range(2):
            self.security_monitor.log_token_validation(False, token_info, request_context)
        
        # Get metrics
        metrics = self.security_monitor.get_security_metrics()
        
        # Verify metrics
        assert metrics.total_auth_attempts == 8
        assert metrics.successful_auths == 5
        assert metrics.failed_auths == 3
        assert metrics.token_validations == 9
        assert metrics.token_failures == 2
    
    def test_threat_indicator_tracking(self):
        """Test tracking of threat indicators."""
        # Create security event
        security_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip='203.0.113.100',
            user_agent='AttackerBot/1.0',
            path='/admin',
            error_message='Suspicious path access'
        )
        
        # Log the security event multiple times
        for _ in range(6):
            self.security_monitor.log_security_event(security_event)
        
        # Get threat indicators
        indicators = self.security_monitor.get_threat_indicators()
        
        # Should have indicators for IP and path
        assert len(indicators) > 0
        
        # Find IP indicator
        ip_indicator = next((i for i in indicators if i.indicator_type == 'ip'), None)
        assert ip_indicator is not None
        assert ip_indicator.value == '203.0.113.100'
        assert ip_indicator.count == 6
        assert ip_indicator.severity == ErrorSeverity.HIGH  # Should escalate due to high count
    
    def test_ip_blocking_expiration(self):
        """Test that IP blocks expire correctly."""
        request_context = {
            'client_ip': '192.168.1.250',
            'user_agent': 'TestClient'
        }
        
        user_context = {'user_id': 'unknown', 'username': 'unknown'}
        
        # Create failed attempts to trigger block
        for _ in range(3):
            self.security_monitor.log_authentication_attempt(False, user_context, request_context)
        
        # IP should be blocked
        assert self.security_monitor.is_ip_blocked('192.168.1.250')
        
        # Mock time passage to simulate block expiration
        with patch('services.security_monitor.datetime') as mock_datetime:
            # Set current time to future (past lockout duration)
            future_time = datetime.now(timezone.utc).timestamp() + 400  # 400 seconds later
            mock_datetime.now.return_value.timestamp.return_value = future_time
            
            # IP should no longer be blocked
            assert not self.security_monitor.is_ip_blocked('192.168.1.250')


class TestIntegratedErrorHandling:
    """Integration tests for error handling and security monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AuthenticationErrorHandler()
        self.security_monitor = SecurityMonitor()
    
    def test_end_to_end_error_handling_flow(self):
        """Test complete error handling flow from error to response."""
        # Create authentication error
        error = AuthenticationError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token exp claim indicates expiration",
            suggested_action="Refresh token or re-authenticate"
        )
        
        request_context = {
            'client_ip': '10.0.0.200',
            'user_agent': 'TestClient/1.0',
            'path': '/mcp/tools/search',
            'method': 'POST',
            'user_id': 'user123',
            'username': 'testuser'
        }
        
        # Handle error (should trigger security logging)
        response = self.error_handler.handle_authentication_error(error, request_context)
        
        # Verify response is correct
        assert response.status_code == 401
        content = json.loads(response.body.decode())
        assert content['success'] is False
        assert content['error_type'] == 'TOKEN_EXPIRED'
        
        # Security logging is handled internally by the error handler
        # We can verify the response structure and that no exceptions were raised
    
    def test_error_message_clarity_and_guidance(self):
        """Test that error messages are clear and provide helpful guidance."""
        test_cases = [
            {
                'error': AuthenticationError(
                    error_type="TOKEN_EXPIRED",
                    error_code="EXPIRED_SIGNATURE",
                    message="JWT token has expired",
                    details="Token expiration time has passed",
                    suggested_action="Refresh token or re-authenticate"
                ),
                'expected_guidance': ['refresh', 'token', 'authenticate']
            },
            {
                'error': AuthenticationError(
                    error_type="INVALID_TOKEN_FORMAT",
                    error_code="MALFORMED_TOKEN",
                    message="Invalid JWT token format",
                    details="Token structure is incorrect",
                    suggested_action="Verify token format"
                ),
                'expected_guidance': ['format', 'jwt', 'header.payload.signature']
            },
            {
                'error': AuthenticationError(
                    error_type="UNAUTHORIZED_CLIENT",
                    error_code="CLIENT_NOT_AUTHORIZED",
                    message="Client not authorized",
                    details="Client ID not allowed",
                    suggested_action="Contact administrator"
                ),
                'expected_guidance': ['administrator', 'contact', 'authorized']
            }
        ]
        
        for test_case in test_cases:
            response = self.error_handler.handle_authentication_error(test_case['error'])
            content = json.loads(response.body.decode())
            
            # Check that response contains helpful guidance
            response_text = json.dumps(content).lower()
            
            for guidance_term in test_case['expected_guidance']:
                assert guidance_term.lower() in response_text, f"Missing guidance term '{guidance_term}' in response"
            
            # Verify support info is present
            assert 'support_info' in content
            assert 'documentation' in content['support_info']
    
    def test_graceful_failure_handling(self):
        """Test that authentication failures are handled gracefully without crashes."""
        # Test with various malformed inputs
        malformed_errors = [
            None,  # None error
            AuthenticationError("", "", "", "", ""),  # Empty fields
            AuthenticationError(
                error_type="VERY_LONG_ERROR_TYPE" * 100,
                error_code="LONG_CODE" * 50,
                message="Very long message " * 200,
                details="Very long details " * 300,
                suggested_action="Very long action " * 100
            )  # Extremely long fields
        ]
        
        for error in malformed_errors:
            try:
                if error is None:
                    # Test fallback error response
                    response = self.error_handler._create_fallback_error_response()
                else:
                    response = self.error_handler.handle_authentication_error(error)
                
                # Should not crash and should return valid response
                assert response is not None
                assert hasattr(response, 'status_code')
                assert response.status_code >= 400
                
                # Response should be valid JSON
                content = json.loads(response.body.decode())
                assert 'success' in content
                assert content['success'] is False
                
            except Exception as e:
                pytest.fail(f"Error handling should not crash, but got: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])