"""
Authentication middleware for AgentCore Gateway MCP Tools.

This module provides FastAPI middleware for JWT authentication with bypass paths
for health endpoints and proper user context extraction.
"""

import structlog
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Optional, List
from datetime import datetime, timezone

from .jwt_validator import JWTValidator, UserContext, JWTValidationError
from config.settings import get_settings

logger = structlog.get_logger(__name__)

# Global JWT validator instance
jwt_validator = JWTValidator()

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for JWT authentication with bypass paths.
    
    This middleware validates JWT tokens for all requests except those
    matching bypass paths (health endpoints, documentation, etc.).
    """
    
    def __init__(self, app, bypass_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.settings = get_settings()
        self.bypass_paths = bypass_paths or self.settings.app.bypass_paths
        
        logger.info(
            "Authentication middleware initialized",
            bypass_paths=self.bypass_paths
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with authentication validation."""
        start_time = datetime.now(timezone.utc)
        
        # Check if path should bypass authentication
        if self._should_bypass_auth(request.url.path):
            logger.debug(
                "Bypassing authentication",
                path=request.url.path,
                method=request.method
            )
            response = await call_next(request)
            return response
        
        # Extract and validate JWT token
        try:
            user_context = await self._authenticate_request(request)
            
            # Add user context to request state
            request.state.user = user_context
            
            logger.info(
                "Request authenticated",
                path=request.url.path,
                method=request.method,
                user_id=user_context.user_id,
                username=user_context.username
            )
            
            # Process request
            response = await call_next(request)
            
            # Log successful request
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                "Request completed",
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration_seconds=duration,
                user_id=user_context.user_id
            )
            
            return response
            
        except HTTPException as e:
            # Log authentication failure
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.warning(
                "Authentication failed",
                path=request.url.path,
                method=request.method,
                status_code=e.status_code,
                error=e.detail,
                duration_seconds=duration
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": {
                        "type": "AuthenticationError",
                        "message": e.detail,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
        except Exception as e:
            # Log unexpected error
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(
                "Unexpected authentication error",
                path=request.url.path,
                method=request.method,
                error=str(e),
                duration_seconds=duration
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "type": "InternalServerError",
                        "message": "Authentication service error",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
    
    def _should_bypass_auth(self, path: str) -> bool:
        """Check if the request path should bypass authentication."""
        # Normalize path
        normalized_path = path.rstrip('/')
        if not normalized_path:
            normalized_path = '/'
        
        # Check exact matches and prefix matches
        for bypass_path in self.bypass_paths:
            bypass_normalized = bypass_path.rstrip('/')
            if not bypass_normalized:
                bypass_normalized = '/'
            
            # Exact match
            if normalized_path == bypass_normalized:
                return True
            
            # Prefix match for paths ending with /*
            if bypass_path.endswith('/*'):
                prefix = bypass_path[:-2]  # Remove /*
                if normalized_path.startswith(prefix):
                    return True
        
        return False
    
    async def _authenticate_request(self, request: Request) -> UserContext:
        """Extract and validate JWT token from request."""
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header required. Please provide a valid JWT token in the format: 'Bearer <token>'"
            )
        
        # Parse Bearer token
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Expected: 'Bearer <token>'"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="JWT token is required"
            )
        
        # Validate token
        try:
            user_context = jwt_validator.validate_token(token)
            return user_context
            
        except JWTValidationError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid JWT token: {str(e)}"
            )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserContext:
    """
    FastAPI dependency to get current authenticated user.
    
    This function can be used as a dependency in FastAPI route handlers
    to get the current user context.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials (optional for bypass paths)
        
    Returns:
        UserContext: Current authenticated user context
        
    Raises:
        HTTPException: If authentication fails
    """
    # Check if user context is already available from middleware
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user
    
    # Check if path should bypass authentication
    settings = get_settings()
    bypass_paths = settings.app.bypass_paths
    
    path = request.url.path.rstrip('/')
    if not path:
        path = '/'
    
    for bypass_path in bypass_paths:
        bypass_normalized = bypass_path.rstrip('/')
        if not bypass_normalized:
            bypass_normalized = '/'
        
        if path == bypass_normalized or (bypass_path.endswith('/*') and path.startswith(bypass_path[:-2])):
            # For bypass paths, return a default user context
            return UserContext(
                user_id="anonymous",
                username="anonymous",
                email=None,
                token_claims={},
                authenticated_at=datetime.now(timezone.utc)
            )
    
    # Validate credentials
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required. Please provide a valid JWT token."
        )
    
    try:
        user_context = jwt_validator.validate_token(credentials.credentials)
        
        # Store in request state for future use
        request.state.user = user_context
        
        return user_context
        
    except JWTValidationError as e:
        logger.warning(
            "JWT validation failed in dependency",
            error=str(e),
            path=request.url.path
        )
        raise HTTPException(
            status_code=401,
            detail=f"Invalid JWT token: {str(e)}"
        )


def get_user_context(request: Request) -> Optional[UserContext]:
    """
    Get user context from request state if available.
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserContext or None if not authenticated
    """
    return getattr(request.state, 'user', None)


def require_authentication(request: Request) -> UserContext:
    """
    Require authentication and return user context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        UserContext: Current authenticated user context
        
    Raises:
        HTTPException: If not authenticated
    """
    user_context = get_user_context(request)
    
    if not user_context or user_context.user_id == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return user_context