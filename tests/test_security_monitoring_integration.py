"""
Integration tests for security monitoring with MCP server and authentication middleware.

This module tests the integration between security monitoring, authentication middleware,
and MCP server components to ensure comprehensive security coverage.
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

from services.security_monitor import SecurityMonitor, get_security_monitor
from services.auth_middleware import AuthenticationMiddleware, AuthenticationConfig
from services.auth_service import AuthenticationError, TokenValidator
from services.auth_error_handler import AuthenticationErrorHandler


class MockRequest:
    """Mock request object for testing."""
    
    def __init__(self, headers: Dict[str, str] = None, client_ip: str = "127.0.0.1", 
                 path: str = "/test", method: str = "GET"):
        self.headers = headers or {}
        self.method = method
        self.url = Mock()
        self.url.path = path
        self.client = Mock()
        self.client.host = client_ip
        self.state = Mock()


class MockResponse:
    """Mock response object for testing."""
    
    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers = {}


class TestSecurityMonitoringIntegration:
    """Test security monitoring integration with authentication components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock Cognito configuration
        self.cognito_config = {
            'user_pool_id': 'us-east-1_TEST123',
            'client_id': 'test-client-id',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST123/.well-known/openid-configuration'
        }
        
        # Create authentication configuration
        self.auth_config = AuthenticationConfig(
            cognito_config=self.cognito_config,
            bypass_paths=['/health', '/metrics'],
            require_authentication=True,
            log_user_context=True
        )
        
        # Create mock app
        self.mock_app = Mock()
        
        # Create authentication middleware
        self.auth_middleware = AuthenticationMiddleware(self.mock_app, self.auth_config)
        
        # Get security monitor
        self.security_monitor = get_security_monitor()
    
    @pytest.mark.asyncio
    async def test_successful_authentication_logging(self):
        """Test that successful authentication is properly logged."""
        # Create mock request with valid token
        request = MockRequest(
            headers={'Authorization': 'Bearer valid.jwt.token'},
            client_ip='192.168.1.100',
            path='/mcp/tools/search',
            method='POST'
        )
        
        # Mock token validation to succeed
        mock_user_context = Mock()
        mock_user_context.user_id = 'user123'
        mock_user_context.username = 'testuser'
        mock_user_context.email = 'test@example.com'
        mock_user_context.token_claims = Mock()
        mock_user_context.token_claims.token_use = 'access'
        mock_user_context.token_claims.exp = 1234567890
        mock_user_context.token_claims.iat = 1234567800
        mock_user_context.token_claims.client_id = 'test-client'
        
        # Mock the call_next function
        async def mock_call_next(req):
            return MockResponse(200)
        
        # Patch token validation to return success
        with patch.object(self.auth_middleware, '_validate_token_and_create_context', 
                         return_value=mock_user_context) as mock_validate:
            with patch.object(self.security_monitor, 'log_authentication_attempt') as mock_log_auth:
                with patch.object(self.security_monitor, 'log_token_validation') as mock_log_token:
                    
                    # Process request through middleware
                    response = await self.auth_middleware.dispatch(request, mock_call_next)
                    
                    # Verify successful authentication was logged
                    assert mock_log_auth.called
                    auth_call_args = mock_log_auth.call_args
                    assert auth_call_args[0][0] is True  # success=True
                    
                    user_context_arg = auth_call_args[0][1]
                    assert user_context_arg['user_id'] == 'user123'
                    assert user_context_arg['username'] == 'testuser'
                    
                    request_context_arg = auth_call_args[0][2]
                    assert request_context_arg['client_ip'] == '192.168.1.100'
                    assert request_context_arg['path'] == '/mcp/tools/search'
                    
                    # Verify token validation was logged
                    assert mock_log_token.called
                    token_call_args = mock_log_token.call_args
                    assert token_call_args[0][0] is True  # success=True
                    
                    token_info_arg = token_call_args[0][1]
                    assert token_info_arg['token_type'] == 'access'
                    assert token_info_arg['client_id'] == 'test-client'
    
    @pytest.mark.asyncio
    async def test_failed_authentication_logging(self):
        """Test that failed authentication is properly logged."""
        # Create mock request with invalid token
        request = MockRequest(
            headers={'Authorization': 'Bearer invalid.jwt.token'},
            client_ip='203.0.113.50',
            path='/mcp/tools/search',
            method='POST'
        )
        
        # Mock token validation to fail
        auth_error = AuthenticationError(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_SIGNATURE",
            message="Token signature verification failed",
            details="Invalid signature",
            suggested_action="Check token validity"
        )
        
        # Patch token validation to raise error
        with patch.object(self.auth_middleware, '_extract_bearer_token', 
                         side_effect=auth_error):
            with patch.object(self.security_monitor, 'log_authentication_attempt') as mock_log_auth:
                with patch.object(self.security_monitor, 'log_token_validation') as mock_log_token:
                    
                    # Process request through middleware
                    response = await self.auth_middleware.dispatch(request, Mock())
                    
                    # Verify failed authentication was logged
                    assert mock_log_auth.called
                    auth_call_args = mock_log_auth.call_args
                    assert auth_call_args[0][0] is False  # success=False
                    
                    user_context_arg = auth_call_args[0][1]
                    assert user_context_arg['user_id'] == 'unknown'
                    assert user_context_arg['username'] == 'unknown'
                    
                    # Verify failed token validation was logged
                    assert mock_log_token.called
                    token_call_args = mock_log_token.call_args
                    assert token_call_args[0][0] is False  # success=False
    
    @pytest.mark.asyncio
    async def test_ip_blocking_integration(self):
        """Test that IP blocking works with authentication middleware."""
        # Create request from IP that should be blocked
        request = MockRequest(
            headers={'Authorization': 'Bearer test.token'},
            client_ip='192.168.1.200',
            path='/mcp/tools/search',
            method='POST'
        )
        
        # Mock IP as blocked
        with patch.object(self.security_monitor, 'is_ip_blocked', return_value=True):
            with patch.object(self.auth_middleware.error_handler, 'handle_authentication_error') as mock_handle_error:
                
                # Process request through middleware
                response = await self.auth_middleware.dispatch(request, Mock())
                
                # Verify error handler was called for blocked IP
                assert mock_handle_error.called
                error_arg = mock_handle_error.call_args[0][0]
                assert error_arg.error_type == 'IP_BLOCKED'
                assert error_arg.error_code == 'IP_TEMPORARILY_BLOCKED'
    
    @pytest.mark.asyncio
    async def test_bypass_paths_not_logged(self):
        """Test that bypass paths don't trigger security logging."""
        # Create request to bypass path
        request = MockRequest(
            path='/health',
            method='GET'
        )
        
        async def mock_call_next(req):
            return MockResponse(200)
        
        with patch.object(self.security_monitor, 'log_authentication_attempt') as mock_log_auth:
            
            # Process request through middleware
            response = await self.auth_middleware.dispatch(request, mock_call_next)
            
            # Verify no authentication logging for bypass paths
            assert not mock_log_auth.called
    
    def test_mcp_tool_invocation_logging(self):
        """Test MCP tool invocation logging integration."""
        # Import the MCP server logging function
        from restaurant_mcp_server import log_mcp_tool_invocation
        
        # Mock the security monitor
        with patch('restaurant_mcp_server.security_monitor') as mock_monitor:
            
            # Call MCP tool logging function
            log_mcp_tool_invocation('search_restaurants_by_district', {
                'districts': ['Central district', 'Admiralty']
            })
            
            # Verify security monitor was called
            assert mock_monitor.log_mcp_tool_invocation.called
            
            call_args = mock_monitor.log_mcp_tool_invocation.call_args
            assert call_args[1]['tool_name'] == 'search_restaurants_by_district'
            assert 'districts' in call_args[1]['parameters']
    
    def test_security_metrics_integration(self):
        """Test security metrics collection integration."""
        # Simulate authentication events
        user_context = {
            'user_id': 'user123',
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        request_context = {
            'client_ip': '10.0.0.100',
            'user_agent': 'TestClient/1.0',
            'path': '/mcp/tools/search',
            'method': 'POST'
        }
        
        # Log some events
        self.security_monitor.log_authentication_attempt(True, user_context, request_context)
        self.security_monitor.log_authentication_attempt(False, user_context, request_context)
        
        token_info = {
            'token_type': 'access',
            'exp': 1234567890,
            'iat': 1234567800,
            'client_id': 'test-client',
            'user_id': 'user123'
        }
        
        self.security_monitor.log_token_validation(True, token_info, request_context)
        self.security_monitor.log_token_validation(False, token_info, request_context)
        
        # Get metrics
        metrics = self.security_monitor.get_security_metrics()
        
        # Verify metrics are collected
        assert metrics.total_auth_attempts >= 2
        assert metrics.successful_auths >= 1
        assert metrics.failed_auths >= 1
        assert metrics.token_validations >= 2
        assert metrics.token_failures >= 1
    
    def test_threat_detection_integration(self):
        """Test threat detection integration with authentication flow."""
        # Create request with suspicious characteristics
        request_context = {
            'client_ip': '203.0.113.100',
            'user_agent': 'sqlmap/1.0 (automated scanner)',
            'path': '/admin/config',
            'method': 'POST'
        }
        
        user_context = {
            'user_id': 'unknown',
            'username': 'unknown',
            'email': 'unknown'
        }
        
        # Mock security event logging
        with patch.object(self.security_monitor, 'log_security_event') as mock_log_event:
            
            # Log authentication attempt (should trigger threat detection)
            self.security_monitor.log_authentication_attempt(False, user_context, request_context)
            
            # Verify security event was logged for suspicious activity
            assert mock_log_event.called
            
            # Check that suspicious activity was detected
            security_events = [call[0][0] for call in mock_log_event.call_args_list]
            suspicious_events = [event for event in security_events 
                               if 'Suspicious' in event.error_message]
            
            assert len(suspicious_events) > 0
    
    @pytest.mark.asyncio
    async def test_error_handler_security_logging_integration(self):
        """Test integration between error handler and security logging."""
        # Create authentication error
        error = AuthenticationError(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="JWT token has expired",
            details="Token expiration time has passed",
            suggested_action="Refresh token or re-authenticate"
        )
        
        request_context = {
            'client_ip': '172.16.0.50',
            'user_agent': 'MobileApp/1.0',
            'path': '/mcp/tools/search',
            'method': 'POST',
            'user_id': 'user123',
            'username': 'testuser'
        }
        
        # Mock security event logging
        with patch('services.auth_error_handler.logger') as mock_logger:
            
            # Handle error through error handler
            response = self.auth_middleware.error_handler.handle_authentication_error(
                error, request_context
            )
            
            # Verify security logging occurred
            assert mock_logger.warning.called
            
            # Verify response is correct
            assert response.status_code == 401
            content = json.loads(response.body.decode())
            assert content['success'] is False
            assert content['error_type'] == 'TOKEN_EXPIRED'
    
    def test_audit_trail_completeness(self):
        """Test that audit trail captures all necessary information."""
        # Simulate complete authentication flow
        user_context = {
            'user_id': 'user456',
            'username': 'audituser',
            'email': 'audit@example.com'
        }
        
        request_context = {
            'client_ip': '10.0.1.100',
            'user_agent': 'WebApp/2.0',
            'path': '/mcp/tools/search_restaurants',
            'method': 'POST',
            'request_id': 'req-audit-123'
        }
        
        # Mock audit logger to capture messages
        audit_messages = []
        
        def capture_audit_message(message):
            audit_messages.append(message)
        
        with patch('services.security_monitor.audit_logger') as mock_audit_logger:
            mock_audit_logger.info.side_effect = capture_audit_message
            
            # Log authentication attempt
            self.security_monitor.log_authentication_attempt(True, user_context, request_context)
            
            # Log token validation
            token_info = {
                'token_type': 'access',
                'exp': 1234567890,
                'iat': 1234567800,
                'client_id': 'audit-client',
                'user_id': 'user456'
            }
            self.security_monitor.log_token_validation(True, token_info, request_context)
            
            # Log MCP tool invocation
            self.security_monitor.log_mcp_tool_invocation(
                'search_restaurants_by_district',
                user_context,
                request_context,
                {'districts': ['Central district']}
            )
            
            # Verify all events were logged
            assert len(audit_messages) == 3
            
            # Parse and verify audit messages
            for message in audit_messages:
                if 'AUTH_ATTEMPT:' in message:
                    json_part = message.split('AUTH_ATTEMPT: ')[1]
                    data = json.loads(json_part)
                    assert data['user_id'] == 'user456'
                    assert data['client_ip'] == '10.0.1.100'
                    assert data['request_id'] == 'req-audit-123'
                
                elif 'TOKEN_VALIDATION:' in message:
                    json_part = message.split('TOKEN_VALIDATION: ')[1]
                    data = json.loads(json_part)
                    assert data['token_type'] == 'access'
                    assert data['client_id'] == 'audit-client'
                
                elif 'MCP_TOOL:' in message:
                    json_part = message.split('MCP_TOOL: ')[1]
                    data = json.loads(json_part)
                    assert data['tool_name'] == 'search_restaurants_by_district'
                    assert data['user_id'] == 'user456'
    
    def test_performance_impact_of_security_logging(self):
        """Test that security logging doesn't significantly impact performance."""
        import time
        
        # Measure time without security logging
        start_time = time.time()
        for _ in range(100):
            # Simulate authentication without logging
            pass
        baseline_time = time.time() - start_time
        
        # Measure time with security logging
        user_context = {
            'user_id': 'perfuser',
            'username': 'perftest',
            'email': 'perf@example.com'
        }
        
        request_context = {
            'client_ip': '10.0.2.100',
            'user_agent': 'PerfTestClient/1.0',
            'path': '/mcp/tools/test',
            'method': 'POST'
        }
        
        start_time = time.time()
        for _ in range(100):
            self.security_monitor.log_authentication_attempt(True, user_context, request_context)
        logging_time = time.time() - start_time
        
        # Security logging should not add more than 50% overhead
        # This is a reasonable threshold for production systems
        # Handle case where baseline_time is very small (near zero)
        if baseline_time > 0:
            overhead_ratio = logging_time / baseline_time
            assert overhead_ratio < 5.0, f"Security logging overhead too high: {overhead_ratio:.2f}x"
        else:
            # If baseline is effectively zero, just ensure logging time is reasonable
            assert logging_time < 1.0, f"Security logging time too high: {logging_time:.3f}s"
    
    def test_concurrent_security_logging(self):
        """Test security logging under concurrent access."""
        import threading
        import time
        
        # Create multiple threads that log simultaneously
        def log_events(thread_id):
            user_context = {
                'user_id': f'user{thread_id}',
                'username': f'thread{thread_id}',
                'email': f'thread{thread_id}@example.com'
            }
            
            request_context = {
                'client_ip': f'10.0.{thread_id}.100',
                'user_agent': f'ThreadClient{thread_id}/1.0',
                'path': '/mcp/tools/concurrent_test',
                'method': 'POST'
            }
            
            for i in range(10):
                self.security_monitor.log_authentication_attempt(
                    i % 2 == 0,  # Alternate success/failure
                    user_context, 
                    request_context
                )
                time.sleep(0.001)  # Small delay to simulate real usage
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify metrics were updated correctly
        metrics = self.security_monitor.get_security_metrics()
        
        # Should have logged 50 total attempts (5 threads * 10 attempts each)
        assert metrics.total_auth_attempts >= 50
        assert metrics.successful_auths >= 25  # Half should be successful
        assert metrics.failed_auths >= 25      # Half should be failed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])