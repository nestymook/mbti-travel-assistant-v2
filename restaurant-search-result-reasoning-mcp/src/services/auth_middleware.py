"""
Authentication middleware for FastMCP server integration.

This module provides JWT-based authentication middleware for the FastMCP server,
including token validation, user context extraction, and error handling.
"""

import json
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime, timezone

try:
    from fastapi import Request, Response, HTTPException
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for testing without FastAPI
    FASTAPI_AVAILABLE = False
    
    class Request:
        def __init__(self):
            self.headers = {}
            self.state = type('State', (), {})()
    
    class Response:
        def __init__(self, status_code: int = 200):
            self.status_code = status_code
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
    
    class JSONResponse:
        def __init__(self, status_code: int, content: dict):
            self.status_code = status_code
            self.content = content
    
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app

from src.services.auth_service import TokenValidator, AuthenticationError, UserContext, JWTClaims
from src.services.auth_error_handler import AuthenticationErrorHandler
from src.services.security_monitor import get_security_monitor


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AuthenticationConfig:
    """Configuration for authentication middleware."""
    cognito_config: Dict[str, Any]
    bypass_paths: list = None
    require_authentication: bool = True
    log_user_context: bool = True
    
    def __post_init__(self):
        if self.bypass_paths is None:
            self.bypass_paths = ['/health', '/metrics', '/docs', '/openapi.json']


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    FastMCP authentication middleware for JWT token validation.
    
    This middleware validates JWT tokens from Authorization Bearer headers,
    extracts user context, and handles authentication errors appropriately.
    """
    
    def __init__(self, app, config: AuthenticationConfig):
        """
        Initialize authentication middleware.
        
        Args:
            app: FastAPI application instance
            config: Authentication configuration
        """
        super().__init__(app)
        self.config = config
        self.token_validator = TokenValidator(config.cognito_config)
        self.error_handler = AuthenticationErrorHandler(
            enable_security_logging=True,
            enable_monitoring=True,
            mask_sensitive_data=True
        )
        self.security_monitor = get_security_monitor()
        
        logger.info("Authentication middleware initialized")
        logger.info(f"Bypass paths: {config.bypass_paths}")
        logger.info(f"Authentication required: {config.require_authentication}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through authentication pipeline.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        try:
            # Check if path should bypass authentication
            if self._should_bypass_auth(request):
                logger.debug(f"Bypassing authentication for path: {request.url.path}")
                return await call_next(request)
            
            # Skip authentication if not required
            if not self.config.require_authentication:
                logger.debug("Authentication not required, proceeding without validation")
                return await call_next(request)
            
            # Create request context for monitoring
            request_context = self._create_request_context(request)
            
            # Check if IP is blocked
            if self.security_monitor.is_ip_blocked(request_context.get('client_ip', 'unknown')):
                blocked_error = AuthenticationError(
                    error_type="IP_BLOCKED",
                    error_code="IP_TEMPORARILY_BLOCKED",
                    message="IP address temporarily blocked due to suspicious activity",
                    details="Multiple failed authentication attempts detected",
                    suggested_action="Wait for lockout period to expire or contact administrator"
                )
                return self.error_handler.handle_authentication_error(blocked_error, request_context)
            
            # Extract and validate JWT token
            try:
                token = self._extract_bearer_token(request)
                user_context = await self._validate_token_and_create_context(token)
                
                # Log successful authentication
                user_context_dict = {
                    'user_id': user_context.user_id,
                    'username': user_context.username,
                    'email': user_context.email
                }
                self.security_monitor.log_authentication_attempt(True, user_context_dict, request_context)
                
                # Log token validation
                token_info = {
                    'token_type': user_context.token_claims.token_use,
                    'exp': user_context.token_claims.exp,
                    'iat': user_context.token_claims.iat,
                    'client_id': user_context.token_claims.client_id,
                    'user_id': user_context.user_id
                }
                self.security_monitor.log_token_validation(True, token_info, request_context)
                
                # Inject user context into request state
                request.state.user_context = user_context
                request.state.authenticated = True
                
                # Log user context for audit purposes
                if self.config.log_user_context:
                    self._log_user_context(request, user_context)
                
                # Proceed to next handler
                response = await call_next(request)
                
                # Add authentication headers to response
                self._add_auth_headers(response, user_context)
                
                return response
                
            except AuthenticationError as e:
                logger.warning(f"Authentication failed: {e.message}")
                
                # Log failed authentication attempt
                user_context_dict = {'user_id': 'unknown', 'username': 'unknown', 'email': 'unknown'}
                self.security_monitor.log_authentication_attempt(False, user_context_dict, request_context)
                
                # Log failed token validation if it was a token-related error
                if 'TOKEN' in e.error_type:
                    token_info = {'token_type': 'unknown', 'exp': 0, 'iat': 0, 'client_id': 'unknown', 'user_id': 'unknown'}
                    self.security_monitor.log_token_validation(False, token_info, request_context)
                
                # Use comprehensive error handler
                return self.error_handler.handle_authentication_error(e, request_context)
            
        except Exception as e:
            logger.error(f"Unexpected error in authentication middleware: {e}")
            return self._create_internal_error_response(str(e))
    
    def _should_bypass_auth(self, request: Request) -> bool:
        """
        Check if request path should bypass authentication.
        
        Args:
            request: HTTP request
            
        Returns:
            True if authentication should be bypassed
        """
        path = request.url.path
        
        # Check exact matches and prefix matches
        for bypass_path in self.config.bypass_paths:
            if path == bypass_path or path.startswith(bypass_path + '/'):
                return True
        
        return False
    
    def _extract_bearer_token(self, request: Request) -> str:
        """
        Extract JWT token from Authorization Bearer header.
        
        Args:
            request: HTTP request
            
        Returns:
            JWT token string
            
        Raises:
            AuthenticationError: If token extraction fails
        """
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise AuthenticationError(
                error_type="MISSING_AUTHORIZATION",
                error_code="MISSING_AUTH_HEADER",
                message="Authorization header is required",
                details="Request must include 'Authorization: Bearer <token>' header",
                suggested_action="Include valid JWT token in Authorization header"
            )
        
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError(
                error_type="INVALID_AUTHORIZATION_FORMAT",
                error_code="INVALID_AUTH_FORMAT",
                message="Authorization header must use Bearer token format",
                details=f"Expected 'Bearer <token>', got: {auth_header[:20]}...",
                suggested_action="Use 'Authorization: Bearer <jwt_token>' format"
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not token.strip():
            raise AuthenticationError(
                error_type="EMPTY_TOKEN",
                error_code="EMPTY_BEARER_TOKEN",
                message="Bearer token cannot be empty",
                details="Authorization header contains 'Bearer' but no token",
                suggested_action="Provide valid JWT token after 'Bearer '"
            )
        
        return token.strip()
    
    async def _validate_token_and_create_context(self, token: str) -> UserContext:
        """
        Validate JWT token and create user context.
        
        Args:
            token: JWT token string
            
        Returns:
            UserContext with validated user information
            
        Raises:
            AuthenticationError: If token validation fails
        """
        try:
            # Validate JWT token
            jwt_claims = await self.token_validator.validate_jwt_token(token)
            
            # Create user context
            user_context = UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims,
                session_id=None  # Could be extracted from token if needed
            )
            
            logger.debug(f"Successfully authenticated user: {user_context.username}")
            return user_context
            
        except AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise AuthenticationError(
                error_type="TOKEN_VALIDATION_ERROR",
                error_code="VALIDATION_FAILED",
                message=f"Token validation failed: {str(e)}",
                details=str(e),
                suggested_action="Verify token format and validity"
            )
    
    def _log_user_context(self, request: Request, user_context: UserContext) -> None:
        """
        Log user context for audit purposes.
        
        Args:
            request: HTTP request
            user_context: Authenticated user context
        """
        try:
            audit_info = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_context.user_id,
                'username': user_context.username,
                'email': user_context.email,
                'path': request.url.path,
                'method': request.method,
                'client_ip': request.client.host if hasattr(request, 'client') else 'unknown',
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'token_exp': user_context.token_claims.exp,
                'token_iat': user_context.token_claims.iat
            }
            
            logger.info(f"User authenticated: {json.dumps(audit_info)}")
            
        except Exception as e:
            logger.warning(f"Failed to log user context: {e}")
    
    def _add_auth_headers(self, response: Response, user_context: UserContext) -> None:
        """
        Add authentication-related headers to response.
        
        Args:
            response: HTTP response
            user_context: Authenticated user context
        """
        try:
            if hasattr(response, 'headers'):
                response.headers['X-Authenticated-User'] = user_context.username
                response.headers['X-User-ID'] = user_context.user_id
                
        except Exception as e:
            logger.warning(f"Failed to add auth headers: {e}")
    
    def _create_authentication_error_response(self, error: AuthenticationError) -> JSONResponse:
        """
        Create standardized authentication error response.
        
        Args:
            error: Authentication error
            
        Returns:
            JSON error response
        """
        # Map error types to HTTP status codes
        status_code_map = {
            'MISSING_AUTHORIZATION': 401,
            'INVALID_AUTHORIZATION_FORMAT': 401,
            'EMPTY_TOKEN': 401,
            'TOKEN_EXPIRED': 401,
            'TOKEN_VALIDATION_ERROR': 401,
            'INVALID_SIGNATURE': 401,
            'INVALID_AUDIENCE': 401,
            'INVALID_ISSUER': 401,
            'KEY_NOT_FOUND': 401,
            'JWKS_FETCH_ERROR': 503,
            'COGNITO_ERROR': 503
        }
        
        status_code = status_code_map.get(error.error_type, 401)
        
        error_response = {
            'success': False,
            'error': {
                'type': error.error_type,
                'code': error.error_code,
                'message': error.message,
                'details': error.details,
                'suggested_action': error.suggested_action,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add WWW-Authenticate header for 401 responses
        headers = {}
        if status_code == 401:
            headers['WWW-Authenticate'] = 'Bearer realm="MCP Server", error="invalid_token"'
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers=headers
        )
    
    def _create_request_context(self, request: Request) -> Dict[str, Any]:
        """
        Create request context for error handling and logging.
        
        Args:
            request: HTTP request
            
        Returns:
            Dictionary containing request context information
        """
        try:
            return {
                'path': request.url.path if hasattr(request.url, 'path') else 'unknown',
                'method': request.method if hasattr(request, 'method') else 'unknown',
                'client_ip': request.client.host if hasattr(request, 'client') and request.client else 'unknown',
                'user_agent': request.headers.get('User-Agent', 'unknown') if hasattr(request, 'headers') else 'unknown',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'request_id': request.headers.get('X-Request-ID') if hasattr(request, 'headers') else None
            }
        except Exception as e:
            logger.warning(f"Failed to create request context: {e}")
            return {
                'path': 'unknown',
                'method': 'unknown',
                'client_ip': 'unknown',
                'user_agent': 'unknown',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _create_internal_error_response(self, error_message: str) -> JSONResponse:
        """
        Create internal server error response.
        
        Args:
            error_message: Error message
            
        Returns:
            JSON error response
        """
        # Use error handler for internal errors too
        internal_error = AuthenticationError(
            error_type="INTERNAL_ERROR",
            error_code="MIDDLEWARE_ERROR",
            message="Internal authentication error occurred",
            details="An unexpected error occurred during authentication processing",
            suggested_action="Contact system administrator if problem persists"
        )
        
        return self.error_handler.handle_authentication_error(internal_error)


class AuthenticationHelper:
    """
    Helper class for authentication-related utilities.
    
    Provides utility functions for working with authenticated requests
    and user context in MCP tools.
    """
    
    @staticmethod
    def get_user_context(request: Request) -> Optional[UserContext]:
        """
        Get user context from authenticated request.
        
        Args:
            request: HTTP request with user context
            
        Returns:
            UserContext if available, None otherwise
        """
        try:
            return getattr(request.state, 'user_context', None)
        except AttributeError:
            return None
    
    @staticmethod
    def is_authenticated(request: Request) -> bool:
        """
        Check if request is authenticated.
        
        Args:
            request: HTTP request
            
        Returns:
            True if request is authenticated
        """
        try:
            return getattr(request.state, 'authenticated', False)
        except AttributeError:
            return False
    
    @staticmethod
    def require_authentication(request: Request) -> UserContext:
        """
        Require authentication and return user context.
        
        Args:
            request: HTTP request
            
        Returns:
            UserContext for authenticated user
            
        Raises:
            HTTPException: If request is not authenticated
        """
        user_context = AuthenticationHelper.get_user_context(request)
        
        if not user_context:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        return user_context
    
    @staticmethod
    def get_user_id(request: Request) -> Optional[str]:
        """
        Get user ID from authenticated request.
        
        Args:
            request: HTTP request
            
        Returns:
            User ID if available, None otherwise
        """
        user_context = AuthenticationHelper.get_user_context(request)
        return user_context.user_id if user_context else None
    
    @staticmethod
    def get_username(request: Request) -> Optional[str]:
        """
        Get username from authenticated request.
        
        Args:
            request: HTTP request
            
        Returns:
            Username if available, None otherwise
        """
        user_context = AuthenticationHelper.get_user_context(request)
        return user_context.username if user_context else None


# Factory function for creating authentication middleware
def create_authentication_middleware(cognito_config: Dict[str, Any], 
                                   bypass_paths: list = None,
                                   require_authentication: bool = True,
                                   log_user_context: bool = True) -> AuthenticationMiddleware:
    """
    Factory function to create authentication middleware.
    
    Args:
        cognito_config: Cognito configuration dictionary
        bypass_paths: List of paths to bypass authentication
        require_authentication: Whether to require authentication
        log_user_context: Whether to log user context for audit
        
    Returns:
        Configured AuthenticationMiddleware instance
    """
    config = AuthenticationConfig(
        cognito_config=cognito_config,
        bypass_paths=bypass_paths,
        require_authentication=require_authentication,
        log_user_context=log_user_context
    )
    
    def middleware_factory(app):
        return AuthenticationMiddleware(app, config)
    
    return middleware_factory


# Async context manager for testing authentication
class MockAuthenticationContext:
    """Mock authentication context for testing."""
    
    def __init__(self, user_context: UserContext):
        self.user_context = user_context
    
    async def __aenter__(self):
        return self.user_context
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Export main classes and functions
__all__ = [
    'AuthenticationMiddleware',
    'AuthenticationConfig', 
    'AuthenticationHelper',
    'create_authentication_middleware',
    'MockAuthenticationContext'
]