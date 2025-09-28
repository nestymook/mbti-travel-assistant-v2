"""
Comprehensive tests for authentication error handling in reasoning server.

Tests all authentication error scenarios with appropriate error responses,
security logging functionality, and error message clarity.
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
    AuthenticationErrorHandler, ErrorResponse, SecurityEvent, 
    TroubleshootingGuide, ErrorSeverity, SecurityEventType
)
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


class TestAuthenticationErrorHandler:
    """Test suite for AuthenticationErrorHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = AuthenticationErrorHandler(
            enable_security_logging=True,
            enable_monitoring=True,
            mask_sensitive_data=True
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
    
    def test_handle_token_expiration_error(self):
        """Test handling of token expiration errors."""
        # Create token expiration error
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired",
            details="JWT token expiration time (exp) has passed",
            suggested_action="Please refresh your token or re-authenticate"
        )
        
        # Handle the error
        response = self.error_handler.handle_token_expiration(error, self.request_context)
        
        # Verify response
        assert response.status_code == 401
        assert 'WWW-Authenticate' in response.headers
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['success'] is False
        assert content['error_type'] == 'TOKEN_EXPIRED'
        assert content['error_code'] == 'EXPIRED_SIGNATURE'
        assert 'refresh your token' in content['suggested_action']
        assert 'refresh_endpoint' in content['support_info']
    
    def test_handle_invalid_token_format_error(self):
        """Test handling of invalid token format errors."""
        # Create invalid token format error
        error = create_auth_error(
            error_type="INVALID_TOKEN_FORMAT",
            error_code="MALFORMED_TOKEN",
            message="Invalid JWT token format",
            details="Token does not match expected JWT structure",
            suggested_action="Verify token format and ensure it's a valid JWT token"
        )
        
        # Handle the error
        response = self.error_handler.handle_invalid_token_format(error, self.request_context)
        
        # Verify response
        assert response.status_code == 400
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['success'] is False
        assert content['error_type'] == 'INVALID_TOKEN_FORMAT'
        assert content['error_code'] == 'MALFORMED_TOKEN'
        assert 'Header.Payload.Signature' in content['details']
        assert 'jwt_structure' in content['support_info']
    
    def test_handle_unauthorized_client_error(self):
        """Test handling of unauthorized client errors."""
        # Create unauthorized client error
        error = create_auth_error(
            error_type="UNAUTHORIZED_CLIENT",
            error_code="CLIENT_NOT_AUTHORIZED",
            message="Client not authorized",
            details="Client ID not in allowed clients list",
            suggested_action="Contact administrator to authorize your client application"
        )
        
        # Handle the error
        response = self.error_handler.handle_unauthorized_client(error, self.request_context)
        
        # Verify response
        assert response.status_code == 403
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['success'] is False
        assert content['error_type'] == 'UNAUTHORIZED_CLIENT'
        assert content['error_code'] == 'CLIENT_NOT_AUTHORIZED'
        assert 'administrator' in content['suggested_action']
    
    def test_handle_general_authentication_error(self):
        """Test handling of general authentication errors."""
        # Create general authentication error
        error = create_auth_error(
            error_type="AUTHENTICATION_FAILED",
            error_code="INVALID_CREDENTIALS",
            message="Authentication failed",
            details="Invalid username or password",
            suggested_action="Please check your credentials and try again"
        )
        
        # Handle the error
        response = self.error_handler.handle_authentication_error(error, self.request_context)
        
        # Verify response
        assert response.status_code == 401
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['success'] is False
        assert content['error_type'] == 'AUTHENTICATION_FAILED'
        assert content['error_code'] == 'INVALID_CREDENTIALS'
        assert content['timestamp'] is not None
        assert content['request_id'] is not None
    
    @patch('services.auth_error_handler.logger')
    def test_security_logging_enabled(self, mock_logger):
        """Test that security events are logged when logging is enabled."""
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        # Handle error with logging enabled
        self.error_handler.handle_authentication_error(error, self.request_context)
        
        # Verify logging was called
        mock_logger.warning.assert_called()
        
        # Verify log message contains security event
        log_calls = mock_logger.warning.call_args_list
        assert any('Security event:' in str(call) for call in log_calls)
    
    def test_security_logging_disabled(self):
        """Test that security events are not logged when logging is disabled."""
        # Create handler with logging disabled
        handler = AuthenticationErrorHandler(
            enable_security_logging=False,
            enable_monitoring=False
        )
        
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        with patch('services.auth_error_handler.logger') as mock_logger:
            handler.handle_authentication_error(error, self.request_context)
            
            # Verify no security logging occurred
            mock_logger.warning.assert_not_called()
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is masked in error responses."""
        # Create error with sensitive details
        error = create_auth_error(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_SIGNATURE",
            message="Token validation failed",
            details="JWT token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.signature and email: user@example.com"
        )
        
        # Handle the error
        response = self.error_handler.handle_authentication_error(error, self.request_context)
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        # Verify sensitive data is masked
        assert 'eyJ***MASKED***' in content['details']
        assert '***@***.***' in content['details']
    
    def test_sensitive_data_not_masked_when_disabled(self):
        """Test that sensitive data is not masked when masking is disabled."""
        # Create handler with masking disabled
        handler = AuthenticationErrorHandler(mask_sensitive_data=False)
        
        error = create_auth_error(
            error_type="TOKEN_VALIDATION_ERROR",
            error_code="INVALID_SIGNATURE",
            message="Token validation failed",
            details="JWT token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.signature"
        )
        
        # Handle the error
        response = handler.handle_authentication_error(error, self.request_context)
        
        # Verify response content
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        # Verify sensitive data is not masked
        assert 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9' in content['details']
    
    def test_troubleshooting_guide_retrieval(self):
        """Test retrieval of troubleshooting guides."""
        # Test getting troubleshooting guide for token expiration
        guide = self.error_handler.get_troubleshooting_guide("TOKEN_EXPIRED")
        
        assert guide is not None
        assert guide.error_type == "TOKEN_EXPIRED"
        assert len(guide.common_causes) > 0
        assert len(guide.resolution_steps) > 0
        assert len(guide.documentation_links) > 0
        
        # Test getting guide for invalid token format
        guide = self.error_handler.get_troubleshooting_guide("INVALID_TOKEN_FORMAT")
        
        assert guide is not None
        assert guide.error_type == "INVALID_TOKEN_FORMAT"
        assert any('JWT token structure' in cause for cause in guide.common_causes)
        
        # Test getting guide for non-existent error type
        guide = self.error_handler.get_troubleshooting_guide("NON_EXISTENT_ERROR")
        assert guide is None
    
    def test_suspicious_activity_detection(self):
        """Test detection of suspicious activity patterns."""
        # Test with suspicious user agent
        suspicious_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'curl/7.68.0',
            'path': '/mcp/tools/recommend_restaurants'
        }
        
        is_suspicious = self.error_handler.detect_suspicious_activity(suspicious_context)
        assert is_suspicious is True
        
        # Test with normal user agent
        normal_context = {
            'client_ip': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'path': '/mcp/tools/recommend_restaurants'
        }
        
        is_suspicious = self.error_handler.detect_suspicious_activity(normal_context)
        assert is_suspicious is False
    
    def test_rapid_failed_attempts_detection(self):
        """Test detection of rapid failed authentication attempts."""
        # Simulate multiple failed attempts from same IP
        error = create_auth_error(
            error_type="AUTHENTICATION_FAILED",
            error_code="INVALID_CREDENTIALS",
            message="Authentication failed"
        )
        
        # Make multiple failed attempts
        for i in range(6):  # Exceed the threshold of 5
            self.error_handler.handle_authentication_error(error, self.request_context)
        
        # Check if IP is now considered suspicious
        is_suspicious = self.error_handler.detect_suspicious_activity(self.request_context)
        assert is_suspicious is True
    
    def test_error_response_headers(self):
        """Test that appropriate headers are set in error responses."""
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        response = self.error_handler.handle_token_expiration(error, self.request_context)
        
        # Verify security headers
        assert 'Cache-Control' in response.headers
        assert response.headers['Cache-Control'] == 'no-store'
        assert 'Pragma' in response.headers
        assert response.headers['Pragma'] == 'no-cache'
        assert 'WWW-Authenticate' in response.headers
    
    def test_fallback_error_response(self):
        """Test fallback error response for unexpected errors."""
        # Mock an error in the error handler
        with patch.object(self.error_handler, '_create_error_response', side_effect=Exception("Test error")):
            error = create_auth_error(
                error_type="TEST_ERROR",
                error_code="TEST_CODE",
                message="Test message"
            )
            
            response = self.error_handler.handle_authentication_error(error, self.request_context)
            
            # Verify fallback response
            assert response.status_code == 500
            
            content = response.content if hasattr(response, 'content') else json.loads(response.body)
            if isinstance(content, bytes):
                content = json.loads(content.decode())
            
            assert content['error_type'] == 'INTERNAL_ERROR'
            assert content['error_code'] == 'ERROR_HANDLER_FAILURE'
    
    def test_request_id_generation(self):
        """Test request ID generation and inclusion in responses."""
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        # Test with provided request ID
        context_with_id = {**self.request_context, 'request_id': 'custom-request-id'}
        response = self.error_handler.handle_authentication_error(error, context_with_id)
        
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['request_id'] == 'custom-request-id'
        
        # Test with generated request ID
        context_without_id = {k: v for k, v in self.request_context.items() if k != 'request_id'}
        response = self.error_handler.handle_authentication_error(error, context_without_id)
        
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert content['request_id'] is not None
        assert len(content['request_id']) == 12  # MD5 hash truncated to 12 chars
    
    def test_support_info_inclusion(self):
        """Test that appropriate support information is included in responses."""
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        response = self.error_handler.handle_token_expiration(error, self.request_context)
        
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert 'support_info' in content
        assert 'refresh_endpoint' in content['support_info']
        assert 'login_endpoint' in content['support_info']
        assert 'documentation' in content['support_info']
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and helpful."""
        # Test token expiration message
        error = create_auth_error(
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Token has expired"
        )
        
        response = self.error_handler.handle_token_expiration(error, self.request_context)
        
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        # Verify message clarity
        assert 'authentication token has expired' in content['message']
        assert 'refresh your token' in content['suggested_action']
        assert content['details'] is not None
        
        # Test invalid format message
        error = create_auth_error(
            error_type="INVALID_TOKEN_FORMAT",
            error_code="MALFORMED_TOKEN",
            message="Invalid token format"
        )
        
        response = self.error_handler.handle_invalid_token_format(error, self.request_context)
        
        content = response.content if hasattr(response, 'content') else json.loads(response.body)
        if isinstance(content, bytes):
            content = json.loads(content.decode())
        
        assert 'token format is invalid' in content['message']
        assert 'Header.Payload.Signature' in content['details']
        assert 'valid JWT token' in content['suggested_action']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])