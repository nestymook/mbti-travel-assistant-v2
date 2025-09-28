"""
Integration tests for security and error handling components working together.

Tests the complete security pipeline including error handling, logging,
monitoring, and threat detection in reasoning server context.
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_error_handler import (
    AuthenticationErrorHandler, SecurityEvent, SecurityEventType, ErrorSeverity
)
from services.security_monitor import SecurityMonitor, get_security_monitor
from services.auth_service import AuthenticationError


def create_auth_error(error_type: str, error_code: str, message: str, 
                     details: str = None, suggested_action: str = None) -> AuthenticationError:
    """Helper function to create AuthenticationError with all required parameters."""
    return AuthenticationError(
        error_type=error_type,
        error_code=error_code,
        message=message,
        details=details or f"Details for {error_type}",
        suggested_action=suggested_action or f"Please resolve {error_type}"
    )


class TestSecurityIntegration:
    """Integration test suite for security components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AuthenticationErrorHandler(
            enable_security_logging=True,
            enable_monitoring=True,
            mask_sensitive_data=True
        )
        
        self.security_monitor = SecurityMonitor(
            enable_audit_logging=True,
            enable_threat_detection=True,
            max_failed_attempts=3,  # Lower for testing
            lockout_duration=60,    # Shorter for testing
            suspicious_threshold=5
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
    @patch('services.auth_error_handler.logger')
    def test_complete_authentication_failure_pipeline(self, mock_error_logger, mock_audit_logger):
        """Test complete pipeline for authentication failure handling."""
        # Create authentication error
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time (exp) has passed",
            suggested_action="Please refresh your token"
        )
        
        # Step 1: Handle authentication error
        response = self.error_handler.handle_token_expiration(error, self.request_context)
        
        # Step 2: Log authentication attempt in security monitor
        self.security_monitor.log_authentication_attempt(
            success=False,
            user_context=self.user_context,
            request_context=self.request_context
        )
        
        # Verify error response
        assert response.status_code == 401
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['success'] is False
        assert content['error_type'] == 'TOKEN_EXPIRED'
        
        # Verify security logging occurred
        mock_error_logger.warning.assert_called()
        mock_audit_logger.info.assert_called()
        
        # Verify metrics updated
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.failed_auths >= 1
    
    @patch('services.security_monitor.security_logger')
    def test_brute_force_attack_detection_and_blocking(self, mock_security_logger):
        """Test detection and blocking of brute force attacks."""
        attacker_ip = '192.168.1.200'
        attack_context = {**self.request_context, 'client_ip': attacker_ip}
        
        # Simulate brute force attack
        for attempt in range(5):  # Exceed threshold of 3
            # Create authentication error
            error = create_auth_error(
                error_type="AUTHENTICATION_FAILED",
                error_code="INVALID_CREDENTIALS",
                message="Invalid credentials",
                details=f"Failed attempt #{attempt + 1}",
                suggested_action="Please check your credentials"
            )
            
            # Handle error
            self.error_handler.handle_authentication_error(error, attack_context)
            
            # Log failed attempt
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=attack_context
            )
        
        # Verify IP is blocked
        assert self.security_monitor.is_ip_blocked(attacker_ip) is True
        
        # Verify brute force event was logged
        mock_security_logger.log.assert_called()
        
        # Find brute force log entry
        log_calls = mock_security_logger.log.call_args_list
        brute_force_logged = False
        for call in log_calls:
            if len(call[0]) > 1 and 'BRUTE_FORCE_ATTEMPT' in str(call[0][1]):
                brute_force_logged = True
                break
        
        assert brute_force_logged is True
    
    @patch('services.security_monitor.audit_logger')
    def test_suspicious_activity_detection_across_components(self, mock_audit_logger):
        """Test suspicious activity detection across error handler and monitor."""
        # Use suspicious user agent
        suspicious_context = {
            **self.request_context,
            'user_agent': 'sqlmap/1.5.2',
            'path': '/admin/login'
        }
        
        # Create authentication error
        error = create_auth_error(
            error_type="UNAUTHORIZED_CLIENT",
            error_code="CLIENT_NOT_AUTHORIZED",
            message="Unauthorized client access attempt",
            details="Client not in allowed list",
            suggested_action="Contact administrator"
        )
        
        with patch.object(self.security_monitor, 'log_security_event') as mock_log_event:
            # Handle error (should detect suspicious activity)
            response = self.error_handler.handle_unauthorized_client(error, suspicious_context)
            
            # Log authentication attempt (should also detect suspicious activity)
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=suspicious_context
            )
            
            # Verify suspicious activity was detected and logged
            mock_log_event.assert_called()
            
            # Verify response indicates high severity
            assert response.status_code == 403
    
    @patch('services.security_monitor.audit_logger')
    def test_mcp_tool_invocation_audit_trail(self, mock_audit_logger):
        """Test complete audit trail for MCP tool invocations."""
        # Simulate successful authentication first
        self.security_monitor.log_authentication_attempt(
            success=True,
            user_context=self.user_context,
            request_context=self.request_context
        )
        
        # Simulate MCP tool invocation
        tool_parameters = {
            'restaurants': [
                {'id': '1', 'name': 'Test Restaurant', 'sentiment': {'likes': 10, 'dislikes': 2, 'neutral': 3}},
                {'id': '2', 'name': 'Another Restaurant', 'sentiment': {'likes': 8, 'dislikes': 1, 'neutral': 2}}
            ],
            'ranking_method': 'sentiment_likes'
        }
        
        self.security_monitor.log_mcp_tool_invocation(
            tool_name='recommend_restaurants',
            user_context=self.user_context,
            request_context=self.request_context,
            parameters=tool_parameters
        )
        
        # Verify audit logging occurred
        mock_audit_logger.info.assert_called()
        
        # Verify both authentication and tool invocation were logged
        log_calls = mock_audit_logger.info.call_args_list
        auth_logged = any('AUTH_ATTEMPT:' in str(call) for call in log_calls)
        tool_logged = any('MCP_TOOL:' in str(call) for call in log_calls)
        
        assert auth_logged is True
        assert tool_logged is True
    
    def test_error_response_consistency_with_monitoring(self):
        """Test that error responses are consistent with monitoring data."""
        # Create multiple different error types
        errors = [
            create_auth_error("TOKEN_EXPIRED", "EXPIRED_SIGNATURE", "Token expired"),
            create_auth_error("INVALID_TOKEN_FORMAT", "MALFORMED_TOKEN", "Invalid format"),
            create_auth_error("UNAUTHORIZED_CLIENT", "CLIENT_NOT_AUTHORIZED", "Unauthorized")
        ]
        
        responses = []
        for error in errors:
            # Handle error
            if error.error_type == "TOKEN_EXPIRED":
                response = self.error_handler.handle_token_expiration(error, self.request_context)
            elif error.error_type == "INVALID_TOKEN_FORMAT":
                response = self.error_handler.handle_invalid_token_format(error, self.request_context)
            else:
                response = self.error_handler.handle_unauthorized_client(error, self.request_context)
            
            responses.append(response)
            
            # Log corresponding authentication attempt
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=self.request_context
            )
        
        # Verify all responses have consistent structure
        for response in responses:
            content = response.content if hasattr(response, 'content') else json.loads(response.body)
            if isinstance(content, bytes):
                content = json.loads(content.decode())
            
            # Verify required fields
            assert 'success' in content
            assert 'error_type' in content
            assert 'error_code' in content
            assert 'message' in content
            assert 'timestamp' in content
            assert 'request_id' in content
            
            assert content['success'] is False
        
        # Verify monitoring metrics match
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.failed_auths == len(errors)
    
    def test_sensitive_data_protection_across_components(self):
        """Test that sensitive data is protected across all components."""
        # Create error with sensitive information
        sensitive_details = "JWT token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.signature, user email: sensitive@example.com, IP: 192.168.1.100"
        
        error = create_auth_error(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_SIGNATURE",
            message="Token validation failed",
            details=sensitive_details,
            suggested_action="Please check your token"
        )
        
        # Mock sensitive parameters for MCP tool
        sensitive_params = {
            'restaurants': [{'id': '1', 'name': 'Test'}],
            'api_secret': 'sk-1234567890abcdef',
            'user_password': 'secret123',
            'normal_param': 'safe_value'
        }
        
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            # Handle authentication error
            response = self.error_handler.handle_authentication_error(error, self.request_context)
            
            # Log MCP tool invocation with sensitive parameters
            self.security_monitor.log_mcp_tool_invocation(
                tool_name='test_tool',
                user_context=self.user_context,
                request_context=self.request_context,
                parameters=sensitive_params
            )
            
            # Verify error response masks sensitive data
            content = response.content if hasattr(response, 'content') else json.loads(response.body)
            if isinstance(content, bytes):
                content = json.loads(content.decode())
            
            assert 'eyJ***MASKED***' in content['details']
            assert '***@***.***' in content['details']
            assert '***.***.***.***' in content['details']
            
            # Verify audit log masks sensitive parameters
            log_calls = mock_audit_logger.info.call_args_list
            mcp_log_call = None
            for call in log_calls:
                if 'MCP_TOOL:' in str(call):
                    mcp_log_call = call
                    break
            
            assert mcp_log_call is not None
            log_data = json.loads(str(mcp_log_call[0][0]).split('MCP_TOOL: ')[1])
            
            assert log_data['parameters']['api_secret'] == '***REDACTED***'
            assert log_data['parameters']['user_password'] == '***REDACTED***'
            assert log_data['parameters']['normal_param'] == 'safe_value'
    
    def test_threat_indicator_correlation(self):
        """Test correlation of threat indicators across components."""
        malicious_ip = '192.168.1.250'
        malicious_context = {
            **self.request_context,
            'client_ip': malicious_ip,
            'user_agent': 'nikto/2.1.6'
        }
        
        # Simulate multiple attack vectors
        attack_scenarios = [
            ("TOKEN_EXPIRED", "EXPIRED_SIGNATURE"),
            ("INVALID_TOKEN_FORMAT", "MALFORMED_TOKEN"),
            ("UNAUTHORIZED_CLIENT", "CLIENT_NOT_AUTHORIZED"),
            ("AUTHENTICATION_FAILED", "INVALID_CREDENTIALS")
        ]
        
        for error_type, error_code in attack_scenarios:
            error = create_auth_error(error_type, error_code, f"Attack: {error_type}")
            
            # Handle error
            self.error_handler.handle_authentication_error(error, malicious_context)
            
            # Log failed attempt
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context=self.user_context,
                request_context=malicious_context
            )
        
        # Get threat indicators
        indicators = self.security_monitor.get_threat_indicators()
        
        # Verify IP-based threat indicator exists
        ip_indicators = [i for i in indicators if i.indicator_type == 'ip' and i.value == malicious_ip]
        assert len(ip_indicators) > 0
        
        # Verify user agent threat indicator exists
        ua_indicators = [i for i in indicators if i.indicator_type == 'user_agent_hash']
        assert len(ua_indicators) > 0
        
        # Verify IP is blocked due to multiple failures
        assert self.security_monitor.is_ip_blocked(malicious_ip) is True
    
    def test_performance_under_load(self):
        """Test performance of security components under simulated load."""
        import time
        
        start_time = time.time()
        
        # Simulate high load with many authentication attempts
        for i in range(100):
            error = create_auth_error(
                error_type="AUTHENTICATION_FAILED",
                error_code="INVALID_CREDENTIALS",
                message=f"Failed attempt {i}"
            )
            
            # Vary IP addresses to avoid blocking
            varied_context = {
                **self.request_context,
                'client_ip': f'192.168.1.{i % 50 + 1}',
                'request_id': f'request-{i}'
            }
            
            # Handle error (should be fast)
            self.error_handler.handle_authentication_error(error, varied_context)
            
            # Log attempt (should be fast)
            self.security_monitor.log_authentication_attempt(
                success=i % 3 == 0,  # Some successful attempts
                user_context={**self.user_context, 'user_id': f'user-{i}'},
                request_context=varied_context
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 200 operations (100 error handling + 100 logging) in reasonable time
        assert total_time < 5.0  # Less than 5 seconds for 200 operations
        
        # Verify metrics are accurate
        metrics = self.security_monitor.get_security_metrics()
        assert metrics.total_auth_attempts == 100
        assert metrics.successful_auths > 0
        assert metrics.failed_auths > 0
    
    def test_error_recovery_and_resilience(self):
        """Test error recovery and resilience of security components."""
        # Test error handler resilience
        with patch.object(self.error_handler, '_create_error_response', side_effect=Exception("Test error")):
            error = create_auth_error("TEST_ERROR", "TEST_CODE", "Test message")
            
            # Should return fallback response instead of crashing
            response = self.error_handler.handle_authentication_error(error, self.request_context)
            assert response.status_code == 500
            
            content = response.content if hasattr(response, 'content') else json.loads(response.body)
            if isinstance(content, bytes):
                content = json.loads(content.decode())
            
            assert content['error_type'] == 'INTERNAL_ERROR'
        
        # Test security monitor resilience
        with patch('services.security_monitor.audit_logger.info', side_effect=Exception("Logging error")):
            # Should not crash even if logging fails
            try:
                self.security_monitor.log_authentication_attempt(
                    success=True,
                    user_context=self.user_context,
                    request_context=self.request_context
                )
                # Should complete without raising exception
                assert True
            except Exception:
                pytest.fail("Security monitor should handle logging errors gracefully")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])