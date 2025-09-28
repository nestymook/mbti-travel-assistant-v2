"""
Comprehensive tests for security monitoring in reasoning server.

Tests security logging functionality, threat detection, and monitoring
without exposing sensitive data in reasoning operations.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.security_monitor import (
    SecurityMonitor, UserSession, SecurityMetrics, ThreatIndicator,
    get_security_monitor
)
from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity


class TestSecurityMonitor:
    """Test suite for SecurityMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.security_monitor = SecurityMonitor(
            enable_audit_logging=True,
            enable_threat_detection=True,
            max_failed_attempts=5,
            lockout_duration=300,
            suspicious_threshold=10
        )
        
        # Mock request context
        self.request_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'path': '/mcp/tools/recommend_restaurants',
            'method': 'POST',
            'request_id': 'test-request-123'
        }
        
        # Mock user context
        self.user_context = {
            'user_id': 'test-user-123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
    
    @patch('services.security_monitor.audit_logger')
    def test_log_successful_authentication_attempt(self, mock_audit_logger):
        """Test logging of successful authentication attempts."""
        # Log successful authentication
        self.security_monitor.log_authentication_attempt(
            success=True,
            user_context=self.user_context,
            request_context=self.request_context
        )
        
        # Verify audit logging was called
        mock_audit_logger.info.assert_called()
        
        # Verify log message format
        log_call = mock_audit_logger.info.call_args[0][0]
        assert 'AUTH_ATTEMPT:' in log_call
        
        # Parse and verify log content
        log_data = json.loads(log_call.split('AUTH_ATTEMPT: ')[1])
        assert log_data['event_type'] == 'authentication_attempt'
        assert log_data['success'] is True
        assert log_data['user_id'] == 'test-user-123'
        assert log_data['username'] == 'testuser'
        assert log_data['client_ip'] == '192.168.1.100'
        
        # Verify metrics updated
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.total_auth_attempts == 1
        assert metrics.successful_auths == 1
        assert metrics.failed_auths == 0
    
    @patch('services.security_monitor.audit_logger')
    def test_log_failed_authentication_attempt(self, mock_audit_logger):
        """Test logging of failed authentication attempts."""
        # Log failed authentication
        self.security_monitor.log_authentication_attempt(
            success=False,
            user_context=self.user_context,
            request_context=self.request_context
        )
        
        # Verify audit logging was called
        mock_audit_logger.info.assert_called()
        
        # Verify log message format
        log_call = mock_audit_logger.info.call_args[0][0]
        assert 'AUTH_ATTEMPT:' in log_call
        
        # Parse and verify log content
        log_data = json.loads(log_call.split('AUTH_ATTEMPT: ')[1])
        assert log_data['event_type'] == 'authentication_attempt'
        assert log_data['success'] is False
        
        # Verify metrics updated
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.total_auth_attempts == 1
        assert metrics.successful_auths == 0
        assert metrics.failed_auths == 1
    
    @patch('services.security_monitor.audit_logger')
    def test_log_token_validation(self, mock_audit_logger):
        """Test logging of JWT token validation events."""
        # Mock token info
        token_info = {
            'token_type': 'Bearer',
            'exp': 1234567890,
            'iat': 1234567800,
            'client_id': 'test-client-123',
            'user_id': 'test-user-123'
        }
        
        # Log successful token validation
        self.security_monitor.log_token_validation(
            success=True,
            token_info=token_info,
            request_context=self.request_context
        )
        
        # Verify audit logging was called
        mock_audit_logger.info.assert_called()
        
        # Verify log message format
        log_call = mock_audit_logger.info.call_args[0][0]
        assert 'TOKEN_VALIDATION:' in log_call
        
        # Parse and verify log content
        log_data = json.loads(log_call.split('TOKEN_VALIDATION: ')[1])
        assert log_data['event_type'] == 'token_validation'
        assert log_data['success'] is True
        assert log_data['token_type'] == 'Bearer'
        assert log_data['client_id'] == 'test-client-123'
        
        # Verify metrics updated
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.token_validations == 1
        assert metrics.token_failures == 0
    
    @patch('services.security_monitor.audit_logger')
    def test_log_mcp_tool_invocation(self, mock_audit_logger):
        """Test logging of MCP tool invocations for audit trail."""
        # Mock tool parameters
        parameters = {
            'restaurants': [{'id': '1', 'name': 'Test Restaurant'}],
            'ranking_method': 'sentiment_likes',
            'secret_key': 'should-be-redacted'
        }
        
        # Log MCP tool invocation
        self.security_monitor.log_mcp_tool_invocation(
            tool_name='recommend_restaurants',
            user_context=self.user_context,
            request_context=self.request_context,
            parameters=parameters
        )
        
        # Verify audit logging was called
        mock_audit_logger.info.assert_called()
        
        # Verify log message format
        log_call = mock_audit_logger.info.call_args[0][0]
        assert 'MCP_TOOL:' in log_call
        
        # Parse and verify log content
        log_data = json.loads(log_call.split('MCP_TOOL: ')[1])
        assert log_data['event_type'] == 'mcp_tool_invocation'
        assert log_data['tool_name'] == 'recommend_restaurants'
        assert log_data['user_id'] == 'test-user-123'
        assert log_data['username'] == 'testuser'
        
        # Verify sensitive parameters are redacted
        assert log_data['parameters']['secret_key'] == '***REDACTED***'
        assert log_data['parameters']['ranking_method'] == 'sentiment_likes'
    
    @patch('services.security_monitor.security_logger')
    def test_log_security_event(self, mock_security_logger):
        """Test logging of security events with appropriate severity levels."""
        # Create security event
        security_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip='192.168.1.100',
            user_agent='curl/7.68.0',
            error_message='Suspicious user agent detected'
        )
        
        # Log security event
        self.security_monitor.log_security_event(security_event)
        
        # Verify security logging was called with appropriate level
        mock_security_logger.log.assert_called()
        
        # Verify log level is ERROR for HIGH severity
        call_args = mock_security_logger.log.call_args
        assert call_args[0][0] == logging.ERROR  # First argument is log level
        
        # Verify log message contains security event
        log_message = call_args[0][1]
        assert 'SECURITY_EVENT:' in log_message
    
    def test_ip_blocking_after_failed_attempts(self):
        """Test IP blocking after exceeding failed attempt threshold."""
        client_ip = '192.168.1.200'
        request_context = {**self.request_context, 'client_ip': client_ip}
        
        # Initially IP should not be blocked
        assert self.security_monitor.is_ip_blocked(client_ip) is False
        
        # Simulate multiple failed attempts
        for i in range(6):  # Exceed threshold of 5
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=request_context
            )
        
        # IP should now be blocked
        assert self.security_monitor.is_ip_blocked(client_ip) is True
    
    def test_ip_block_expiration(self):
        """Test that IP blocks expire after lockout duration."""
        # Create monitor with short lockout duration for testing
        monitor = SecurityMonitor(lockout_duration=1)  # 1 second
        
        client_ip = '192.168.1.201'
        request_context = {**self.request_context, 'client_ip': client_ip}
        
        # Trigger IP block
        for i in range(6):
            monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=request_context
            )
        
        # IP should be blocked
        assert monitor.is_ip_blocked(client_ip) is True
        
        # Wait for block to expire
        import time
        time.sleep(1.1)
        
        # IP should no longer be blocked
        assert monitor.is_ip_blocked(client_ip) is False
    
    def test_successful_auth_clears_failed_attempts(self):
        """Test that successful authentication clears failed attempts."""
        client_ip = '192.168.1.202'
        request_context = {**self.request_context, 'client_ip': client_ip}
        
        # Make some failed attempts
        for i in range(3):
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=request_context
            )
        
        # Make successful attempt
        self.security_monitor.log_authentication_attempt(
            success=True,
            user_context=self.user_context,
            request_context=request_context
        )
        
        # IP should not be blocked even after more failed attempts
        for i in range(3):
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=request_context
            )
        
        assert self.security_monitor.is_ip_blocked(client_ip) is False
    
    def test_suspicious_user_agent_detection(self):
        """Test detection of suspicious user agents."""
        suspicious_agents = [
            'curl/7.68.0',
            'python-requests/2.25.1',
            'Googlebot/2.1',
            'sqlmap/1.5.2',
            'nikto/2.1.6'
        ]
        
        for user_agent in suspicious_agents:
            request_context = {**self.request_context, 'user_agent': user_agent}
            
            with patch.object(self.security_monitor, 'log_security_event') as mock_log:
                self.security_monitor.log_authentication_attempt(
                    success=False,
                    user_context=self.user_context,
                    request_context=request_context
                )
                
                # Verify suspicious activity was logged
                mock_log.assert_called()
                security_event = mock_log.call_args[0][0]
                assert security_event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
                assert 'user agent' in security_event.error_message.lower()
    
    def test_suspicious_path_detection(self):
        """Test detection of suspicious path access."""
        suspicious_paths = [
            '/admin/login',
            '/wp-admin/admin.php',
            '/.env',
            '/config/database.yml',
            '/backup/dump.sql'
        ]
        
        for path in suspicious_paths:
            request_context = {**self.request_context, 'path': path}
            
            with patch.object(self.security_monitor, 'log_security_event') as mock_log:
                self.security_monitor.log_authentication_attempt(
                    success=False,
                    user_context=self.user_context,
                    request_context=request_context
                )
                
                # Verify suspicious activity was logged
                mock_log.assert_called()
                security_event = mock_log.call_args[0][0]
                assert security_event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
                assert 'path' in security_event.error_message.lower()
    
    def test_security_metrics_collection(self):
        """Test collection of security metrics."""
        # Perform various authentication attempts
        self.security_monitor.log_authentication_attempt(True, self.user_context, self.request_context)
        self.security_monitor.log_authentication_attempt(False, self.user_context, self.request_context)
        self.security_monitor.log_authentication_attempt(True, self.user_context, self.request_context)
        
        # Perform token validations
        token_info = {'token_type': 'Bearer', 'user_id': 'test-user'}
        self.security_monitor.log_token_validation(True, token_info, self.request_context)
        self.security_monitor.log_token_validation(False, token_info, self.request_context)
        
        # Get metrics
        metrics = self.security_monitor.get_security_metrics()
        
        # Verify metrics
        assert metrics.total_auth_attempts == 3
        assert metrics.successful_auths == 2
        assert metrics.failed_auths == 1
        assert metrics.token_validations == 2
        assert metrics.token_failures == 1
    
    def test_threat_indicator_tracking(self):
        """Test tracking of threat indicators."""
        # Create security events that should generate threat indicators
        security_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip='192.168.1.100',
            user_agent='curl/7.68.0',
            path='/admin/login'
        )
        
        # Log multiple similar events
        for i in range(5):
            self.security_monitor.log_security_event(security_event)
        
        # Get threat indicators
        indicators = self.security_monitor.get_threat_indicators()
        
        # Verify threat indicators were created
        assert len(indicators) > 0
        
        # Find IP-based indicator
        ip_indicators = [i for i in indicators if i.indicator_type == 'ip']
        assert len(ip_indicators) > 0
        
        ip_indicator = ip_indicators[0]
        assert ip_indicator.value == '192.168.1.100'
        assert ip_indicator.count == 5
    
    def test_threat_indicator_escalation(self):
        """Test escalation of threat indicators based on count."""
        # Create monitor with low suspicious threshold
        monitor = SecurityMonitor(suspicious_threshold=3)
        
        security_event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(timezone.utc).isoformat(),
            client_ip='192.168.1.100'
        )
        
        # Log events to exceed threshold
        for i in range(5):
            monitor.log_security_event(security_event)
        
        # Get threat indicators
        indicators = monitor.get_threat_indicators()
        
        # Find escalated indicator
        ip_indicators = [i for i in indicators if i.indicator_type == 'ip']
        assert len(ip_indicators) > 0
        
        # Verify severity was escalated
        ip_indicator = ip_indicators[0]
        assert ip_indicator.severity == ErrorSeverity.HIGH
    
    def test_user_agent_sanitization(self):
        """Test sanitization of user agent strings."""
        malicious_user_agent = '<script>alert("xss")</script>Mozilla/5.0' + 'A' * 300
        
        request_context = {**self.request_context, 'user_agent': malicious_user_agent}
        
        with patch('services.security_monitor.audit_logger') as mock_logger:
            self.security_monitor.log_authentication_attempt(
                success=True,
                user_context=self.user_context,
                request_context=request_context
            )
            
            # Verify user agent was sanitized
            log_call = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call.split('AUTH_ATTEMPT: ')[1])
            
            # Should be truncated and have dangerous chars removed
            assert len(log_data['user_agent']) <= 200
            assert '<script>' not in log_data['user_agent']
            assert '"' not in log_data['user_agent']
    
    def test_parameter_sanitization(self):
        """Test sanitization of MCP tool parameters."""
        # Parameters with sensitive data
        parameters = {
            'restaurants': [{'id': '1', 'name': 'Test'}],
            'password': 'secret123',
            'api_key': 'sk-1234567890',
            'long_text': 'A' * 200,
            'normal_param': 'normal_value'
        }
        
        with patch('services.security_monitor.audit_logger') as mock_logger:
            self.security_monitor.log_mcp_tool_invocation(
                tool_name='test_tool',
                user_context=self.user_context,
                request_context=self.request_context,
                parameters=parameters
            )
            
            # Verify parameters were sanitized
            log_call = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call.split('MCP_TOOL: ')[1])
            
            sanitized_params = log_data['parameters']
            assert sanitized_params['password'] == '***REDACTED***'
            assert sanitized_params['api_key'] == '***REDACTED***'
            assert sanitized_params['long_text'].endswith('...')
            assert sanitized_params['normal_param'] == 'normal_value'
    
    def test_audit_logging_disabled(self):
        """Test that audit logging can be disabled."""
        # Create monitor with audit logging disabled
        monitor = SecurityMonitor(enable_audit_logging=False)
        
        with patch('services.security_monitor.audit_logger') as mock_logger:
            monitor.log_authentication_attempt(
                success=True,
                user_context=self.user_context,
                request_context=self.request_context
            )
            
            # Verify no audit logging occurred
            mock_logger.info.assert_not_called()
    
    def test_threat_detection_disabled(self):
        """Test that threat detection can be disabled."""
        # Create monitor with threat detection disabled
        monitor = SecurityMonitor(enable_threat_detection=False)
        
        suspicious_context = {**self.request_context, 'user_agent': 'curl/7.68.0'}
        
        with patch.object(monitor, 'log_security_event') as mock_log:
            monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=suspicious_context
            )
            
            # Verify no threat detection occurred
            mock_log.assert_not_called()
    
    def test_global_security_monitor_instance(self):
        """Test global security monitor instance management."""
        # Get global instance
        monitor1 = get_security_monitor()
        monitor2 = get_security_monitor()
        
        # Should be the same instance
        assert monitor1 is monitor2
        
        # Should be properly initialized
        assert isinstance(monitor1, SecurityMonitor)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])