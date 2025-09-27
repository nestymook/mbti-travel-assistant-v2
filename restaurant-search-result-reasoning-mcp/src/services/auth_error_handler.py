"""
Comprehensive authentication error handling system.

This module provides standardized error responses, security logging, and monitoring
for authentication failures in the restaurant search MCP server.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re

try:
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for testing without FastAPI
    FASTAPI_AVAILABLE = False
    
    class JSONResponse:
        def __init__(self, status_code: int, content: dict, headers: dict = None):
            self.status_code = status_code
            self.content = content
            self.headers = headers or {}
            self.body = json.dumps(content).encode()

from src.services.auth_service import AuthenticationError


# Configure logging
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for security monitoring."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events for monitoring."""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    TOKEN_VALIDATION_FAILURE = "token_validation_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    INVALID_TOKEN_FORMAT = "invalid_token_format"
    EXPIRED_TOKEN_ACCESS = "expired_token_access"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"


@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    success: bool = False
    error_type: str = ""
    error_code: str = ""
    message: str = ""
    details: str = ""
    suggested_action: str = ""
    timestamp: str = ""
    request_id: Optional[str] = None
    support_info: Optional[Dict[str, str]] = None


@dataclass
class SecurityEvent:
    """Security event for logging and monitoring."""
    event_type: SecurityEventType
    severity: ErrorSeverity
    timestamp: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class TroubleshootingGuide:
    """Troubleshooting guidance for specific error types."""
    error_type: str
    common_causes: List[str]
    resolution_steps: List[str]
    documentation_links: List[str]
    contact_info: Optional[str] = None


class AuthenticationErrorHandler:
    """
    Comprehensive authentication error response system.
    
    Provides standardized error responses, security logging, and monitoring
    for different types of authentication failures.
    """
    
    def __init__(self, enable_security_logging: bool = True, 
                 enable_monitoring: bool = True,
                 mask_sensitive_data: bool = True):
        """
        Initialize the authentication error handler.
        
        Args:
            enable_security_logging: Whether to enable security event logging
            enable_monitoring: Whether to enable security monitoring
            mask_sensitive_data: Whether to mask sensitive data in logs
        """
        self.enable_security_logging = enable_security_logging
        self.enable_monitoring = enable_monitoring
        self.mask_sensitive_data = mask_sensitive_data
        
        # Initialize error type mappings
        self._init_error_mappings()
        self._init_troubleshooting_guides()
        
        # Security monitoring state
        self._failed_attempts = {}  # Track failed attempts by IP/user
        self._suspicious_patterns = []
        
        logger.info("Authentication error handler initialized")
    
    def handle_authentication_error(self, error: AuthenticationError,
                                  request_context: Optional[Dict[str, Any]] = None) -> JSONResponse:
        """
        Handle authentication error and create standardized response.
        
        Args:
            error: Authentication error to handle
            request_context: Optional request context for logging
            
        Returns:
            Standardized JSON error response
        """
        try:
            # Create standardized error response
            error_response = self._create_error_response(error, request_context)
            
            # Log security event
            if self.enable_security_logging:
                self._log_security_event(error, request_context)
            
            # Update security monitoring
            if self.enable_monitoring:
                self._update_security_monitoring(error, request_context)
            
            # Get HTTP status code
            status_code = self._get_http_status_code(error.error_type)
            
            # Create response headers
            headers = self._create_response_headers(error, status_code)
            
            return JSONResponse(
                status_code=status_code,
                content=asdict(error_response),
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"Error in authentication error handler: {e}")
            return self._create_fallback_error_response()
    
    def handle_token_expiration(self, error: AuthenticationError,
                              request_context: Optional[Dict[str, Any]] = None) -> JSONResponse:
        """
        Handle token expiration with specific guidance.
        
        Args:
            error: Token expiration error
            request_context: Optional request context
            
        Returns:
            JSON response with token refresh guidance
        """
        error_response = ErrorResponse(
            success=False,
            error_type="TOKEN_EXPIRED",
            error_code="EXPIRED_SIGNATURE",
            message="Your authentication token has expired",
            details="The JWT token expiration time (exp) has passed",
            suggested_action="Please refresh your token or re-authenticate to continue",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=self._generate_request_id(request_context),
            support_info={
                "refresh_endpoint": "/auth/refresh",
                "login_endpoint": "/auth/login",
                "documentation": "https://docs.example.com/authentication#token-refresh"
            }
        )
        
        # Log security event
        if self.enable_security_logging:
            self._log_security_event(error, request_context, SecurityEventType.EXPIRED_TOKEN_ACCESS)
        
        headers = {
            'WWW-Authenticate': 'Bearer realm="MCP Server", error="invalid_token", error_description="The access token expired"',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
        
        return JSONResponse(
            status_code=401,
            content=asdict(error_response),
            headers=headers
        )
    
    def handle_invalid_token_format(self, error: AuthenticationError,
                                  request_context: Optional[Dict[str, Any]] = None) -> JSONResponse:
        """
        Handle invalid token format with specific guidance.
        
        Args:
            error: Invalid token format error
            request_context: Optional request context
            
        Returns:
            JSON response with format guidance
        """
        error_response = ErrorResponse(
            success=False,
            error_type="INVALID_TOKEN_FORMAT",
            error_code="MALFORMED_TOKEN",
            message="The provided authentication token format is invalid",
            details="JWT token must be in the format: Header.Payload.Signature",
            suggested_action="Verify token format and ensure it's a valid JWT token",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=self._generate_request_id(request_context),
            support_info={
                "token_format": "Authorization: Bearer <jwt_token>",
                "jwt_structure": "header.payload.signature",
                "documentation": "https://docs.example.com/authentication#jwt-format"
            }
        )
        
        # Log security event
        if self.enable_security_logging:
            self._log_security_event(error, request_context, SecurityEventType.INVALID_TOKEN_FORMAT)
        
        return JSONResponse(
            status_code=400,
            content=asdict(error_response)
        )
    
    def handle_unauthorized_client(self, error: AuthenticationError,
                                 request_context: Optional[Dict[str, Any]] = None) -> JSONResponse:
        """
        Handle unauthorized client access.
        
        Args:
            error: Unauthorized client error
            request_context: Optional request context
            
        Returns:
            JSON response with client authorization guidance
        """
        error_response = ErrorResponse(
            success=False,
            error_type="UNAUTHORIZED_CLIENT",
            error_code="CLIENT_NOT_AUTHORIZED",
            message="Client is not authorized to access this resource",
            details="The client ID in the token is not in the allowed clients list",
            suggested_action="Contact administrator to authorize your client application",
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=self._generate_request_id(request_context),
            support_info={
                "contact": "support@example.com",
                "documentation": "https://docs.example.com/authentication#client-authorization"
            }
        )
        
        # Log security event with higher severity
        if self.enable_security_logging:
            self._log_security_event(error, request_context, 
                                   SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                                   ErrorSeverity.HIGH)
        
        return JSONResponse(
            status_code=403,
            content=asdict(error_response)
        )
    
    def get_troubleshooting_guide(self, error_type: str) -> Optional[TroubleshootingGuide]:
        """
        Get troubleshooting guide for specific error type.
        
        Args:
            error_type: Type of authentication error
            
        Returns:
            Troubleshooting guide if available
        """
        return self.troubleshooting_guides.get(error_type)
    
    def get_security_events(self, limit: int = 100) -> List[SecurityEvent]:
        """
        Get recent security events for monitoring.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent security events
        """
        # In a real implementation, this would query a persistent store
        # For now, return empty list as events are logged to external systems
        return []
    
    def detect_suspicious_activity(self, request_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Detect suspicious authentication activity patterns.
        
        Args:
            request_context: Request context for analysis
            
        Returns:
            True if suspicious activity detected
        """
        if not request_context:
            return False
        
        client_ip = request_context.get('client_ip', 'unknown')
        user_agent = request_context.get('user_agent', '')
        
        # Check for rapid failed attempts from same IP
        current_time = datetime.now(timezone.utc).timestamp()
        if client_ip in self._failed_attempts:
            attempts = self._failed_attempts[client_ip]
            recent_attempts = [t for t in attempts if current_time - t < 300]  # 5 minutes
            
            if len(recent_attempts) >= 5:  # 5 attempts in 5 minutes
                return True
        
        # Check for suspicious user agent patterns
        suspicious_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'curl', r'wget', r'python-requests'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent.lower()):
                return True
        
        return False
    
    def _create_error_response(self, error: AuthenticationError,
                             request_context: Optional[Dict[str, Any]] = None) -> ErrorResponse:
        """Create standardized error response."""
        return ErrorResponse(
            success=False,
            error_type=error.error_type,
            error_code=error.error_code,
            message=error.message,
            details=error.details if not self.mask_sensitive_data else self._mask_sensitive_details(error.details),
            suggested_action=error.suggested_action,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=self._generate_request_id(request_context),
            support_info=self._get_support_info(error.error_type)
        )
    
    def _log_security_event(self, error: AuthenticationError,
                          request_context: Optional[Dict[str, Any]] = None,
                          event_type: Optional[SecurityEventType] = None,
                          severity: Optional[ErrorSeverity] = None) -> None:
        """Log security event for monitoring and audit."""
        try:
            # Determine event type and severity
            if event_type is None:
                event_type = self._map_error_to_event_type(error.error_type)
            
            if severity is None:
                severity = self._map_error_to_severity(error.error_type)
            
            # Create security event
            security_event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                timestamp=datetime.now(timezone.utc).isoformat(),
                user_id=request_context.get('user_id') if request_context else None,
                username=request_context.get('username') if request_context else None,
                client_ip=request_context.get('client_ip') if request_context else None,
                user_agent=request_context.get('user_agent') if request_context else None,
                path=request_context.get('path') if request_context else None,
                method=request_context.get('method') if request_context else None,
                error_code=error.error_code,
                error_message=error.message if not self.mask_sensitive_data else self._mask_sensitive_details(error.message),
                additional_data={
                    'error_type': error.error_type,
                    'request_id': self._generate_request_id(request_context)
                }
            )
            
            # Log the security event
            logger.warning(f"Security event: {json.dumps(asdict(security_event), default=str)}")
            
            # Send to external monitoring systems (placeholder)
            self._send_to_monitoring_system(security_event)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _update_security_monitoring(self, error: AuthenticationError,
                                  request_context: Optional[Dict[str, Any]] = None) -> None:
        """Update security monitoring state."""
        try:
            if not request_context:
                return
            
            client_ip = request_context.get('client_ip', 'unknown')
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Track failed attempts by IP
            if client_ip not in self._failed_attempts:
                self._failed_attempts[client_ip] = []
            
            self._failed_attempts[client_ip].append(current_time)
            
            # Clean up old attempts (older than 1 hour)
            self._failed_attempts[client_ip] = [
                t for t in self._failed_attempts[client_ip] 
                if current_time - t < 3600
            ]
            
            # Check for suspicious activity
            if self.detect_suspicious_activity(request_context):
                self._log_security_event(
                    error, request_context,
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ErrorSeverity.HIGH
                )
            
        except Exception as e:
            logger.error(f"Failed to update security monitoring: {e}")
    
    def _get_http_status_code(self, error_type: str) -> int:
        """Map error type to HTTP status code."""
        return self.error_status_map.get(error_type, 401)
    
    def _create_response_headers(self, error: AuthenticationError, status_code: int) -> Dict[str, str]:
        """Create appropriate response headers."""
        headers = {
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
        }
        
        if status_code == 401:
            headers['WWW-Authenticate'] = f'Bearer realm="MCP Server", error="invalid_token"'
        
        return headers
    
    def _create_fallback_error_response(self) -> JSONResponse:
        """Create fallback error response for unexpected errors."""
        error_response = ErrorResponse(
            success=False,
            error_type="INTERNAL_ERROR",
            error_code="ERROR_HANDLER_FAILURE",
            message="An unexpected error occurred during authentication processing",
            details="The authentication error handler encountered an internal error",
            suggested_action="Contact system administrator if problem persists",
            timestamp=datetime.now(timezone.utc).isoformat(),
            support_info={
                "contact": "support@example.com"
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=asdict(error_response)
        )
    
    def _generate_request_id(self, request_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate unique request ID for tracking."""
        if request_context and 'request_id' in request_context:
            return request_context['request_id']
        
        # Generate based on timestamp and hash
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _mask_sensitive_details(self, details: str) -> str:
        """Mask sensitive information in error details."""
        if not self.mask_sensitive_data:
            return details
        
        # Mask JWT tokens
        details = re.sub(r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*', 
                        'eyJ***MASKED***', details)
        
        # Mask email addresses
        details = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                        '***@***.***', details)
        
        # Mask IP addresses
        details = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 
                        '***.***.***.***', details)
        
        return details
    
    def _get_support_info(self, error_type: str) -> Dict[str, str]:
        """Get support information for error type."""
        base_info = {
            "documentation": "https://docs.example.com/authentication",
            "contact": "support@example.com"
        }
        
        specific_info = {
            "TOKEN_EXPIRED": {
                "refresh_endpoint": "/auth/refresh",
                "documentation": "https://docs.example.com/authentication#token-refresh"
            },
            "INVALID_TOKEN_FORMAT": {
                "jwt_validator": "https://jwt.io",
                "documentation": "https://docs.example.com/authentication#jwt-format"
            },
            "UNAUTHORIZED_CLIENT": {
                "client_registration": "/auth/register-client",
                "documentation": "https://docs.example.com/authentication#client-authorization"
            }
        }
        
        return {**base_info, **specific_info.get(error_type, {})}
    
    def _map_error_to_event_type(self, error_type: str) -> SecurityEventType:
        """Map error type to security event type."""
        mapping = {
            "TOKEN_EXPIRED": SecurityEventType.EXPIRED_TOKEN_ACCESS,
            "INVALID_TOKEN_FORMAT": SecurityEventType.INVALID_TOKEN_FORMAT,
            "UNAUTHORIZED_CLIENT": SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            "TOKEN_VALIDATION_ERROR": SecurityEventType.TOKEN_VALIDATION_FAILURE,
            "AUTHENTICATION_FAILED": SecurityEventType.AUTHENTICATION_FAILURE
        }
        
        return mapping.get(error_type, SecurityEventType.AUTHENTICATION_FAILURE)
    
    def _map_error_to_severity(self, error_type: str) -> ErrorSeverity:
        """Map error type to severity level."""
        severity_map = {
            "TOKEN_EXPIRED": ErrorSeverity.LOW,
            "INVALID_TOKEN_FORMAT": ErrorSeverity.MEDIUM,
            "UNAUTHORIZED_CLIENT": ErrorSeverity.HIGH,
            "TOKEN_VALIDATION_ERROR": ErrorSeverity.MEDIUM,
            "AUTHENTICATION_FAILED": ErrorSeverity.MEDIUM,
            "SUSPICIOUS_ACTIVITY": ErrorSeverity.HIGH,
            "BRUTE_FORCE_ATTEMPT": ErrorSeverity.CRITICAL
        }
        
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    def _send_to_monitoring_system(self, security_event: SecurityEvent) -> None:
        """Send security event to external monitoring system."""
        # Placeholder for integration with monitoring systems
        # In production, this would send to CloudWatch, Splunk, etc.
        pass
    
    def _init_error_mappings(self) -> None:
        """Initialize error type to HTTP status code mappings."""
        self.error_status_map = {
            "MISSING_AUTHORIZATION": 401,
            "INVALID_AUTHORIZATION_FORMAT": 401,
            "EMPTY_TOKEN": 401,
            "TOKEN_EXPIRED": 401,
            "TOKEN_VALIDATION_ERROR": 401,
            "INVALID_SIGNATURE": 401,
            "INVALID_AUDIENCE": 401,
            "INVALID_ISSUER": 401,
            "INVALID_TOKEN_FORMAT": 400,
            "UNAUTHORIZED_CLIENT": 403,
            "KEY_NOT_FOUND": 401,
            "JWKS_FETCH_ERROR": 503,
            "COGNITO_ERROR": 503,
            "INTERNAL_ERROR": 500
        }
    
    def _init_troubleshooting_guides(self) -> None:
        """Initialize troubleshooting guides for different error types."""
        self.troubleshooting_guides = {
            "TOKEN_EXPIRED": TroubleshootingGuide(
                error_type="TOKEN_EXPIRED",
                common_causes=[
                    "JWT token has exceeded its expiration time",
                    "System clock skew between client and server",
                    "Token was issued with short expiration time"
                ],
                resolution_steps=[
                    "Use the refresh token to obtain a new access token",
                    "Re-authenticate if refresh token is also expired",
                    "Check system clock synchronization",
                    "Verify token expiration time in JWT payload"
                ],
                documentation_links=[
                    "https://docs.example.com/authentication#token-refresh",
                    "https://jwt.io/introduction/"
                ],
                contact_info="support@example.com"
            ),
            "INVALID_TOKEN_FORMAT": TroubleshootingGuide(
                error_type="INVALID_TOKEN_FORMAT",
                common_causes=[
                    "Malformed JWT token structure",
                    "Missing Authorization header",
                    "Incorrect Bearer token format",
                    "Token corruption during transmission"
                ],
                resolution_steps=[
                    "Verify Authorization header format: 'Bearer <token>'",
                    "Check JWT token structure: header.payload.signature",
                    "Ensure token is not truncated or corrupted",
                    "Validate token using jwt.io debugger"
                ],
                documentation_links=[
                    "https://docs.example.com/authentication#jwt-format",
                    "https://jwt.io/"
                ]
            ),
            "UNAUTHORIZED_CLIENT": TroubleshootingGuide(
                error_type="UNAUTHORIZED_CLIENT",
                common_causes=[
                    "Client ID not in allowed clients list",
                    "Token issued for different client application",
                    "Client authorization revoked",
                    "Incorrect Cognito User Pool configuration"
                ],
                resolution_steps=[
                    "Contact administrator to authorize client",
                    "Verify client ID in token matches registered client",
                    "Check Cognito User Pool client configuration",
                    "Ensure client has necessary permissions"
                ],
                documentation_links=[
                    "https://docs.example.com/authentication#client-authorization",
                    "https://docs.aws.amazon.com/cognito/latest/developerguide/"
                ],
                contact_info="admin@example.com"
            )
        }


# Export main classes
__all__ = [
    'AuthenticationErrorHandler',
    'ErrorResponse',
    'SecurityEvent',
    'TroubleshootingGuide',
    'ErrorSeverity',
    'SecurityEventType'
]