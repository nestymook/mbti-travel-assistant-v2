"""
Observability middleware for AgentCore Gateway MCP Tools.

This middleware automatically tracks request performance, logs user context,
and records security events for all incoming requests.
"""

import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from middleware.jwt_validator import UserContext
from services.observability_service import (
    get_observability_service,
    SecurityEventType,
    ObservabilityService
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic observability tracking."""
    
    def __init__(self, app, bypass_paths: Optional[list] = None):
        super().__init__(app)
        self.bypass_paths = bypass_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        self.logger = structlog.get_logger(__name__)
        self.observability_service = get_observability_service()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability tracking."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract request information
        endpoint = request.url.path
        method = request.method
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Check if this is a bypass path
        is_bypass_path = any(endpoint.startswith(path) for path in self.bypass_paths)
        
        # Get user context if available
        user_context = getattr(request.state, "user_context", None)
        
        # Log request start
        start_time = self.observability_service.log_request_start(
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            user_context=user_context,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Track MCP server calls
        mcp_calls_start = getattr(request.state, "mcp_server_calls", 0)
        mcp_duration_start = getattr(request.state, "mcp_server_duration_ms", 0.0)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate MCP server metrics
            mcp_calls = getattr(request.state, "mcp_server_calls", 0) - mcp_calls_start
            mcp_duration = getattr(request.state, "mcp_server_duration_ms", 0.0) - mcp_duration_start
            
            # Log successful request completion
            self.observability_service.log_request_end(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                start_time=start_time,
                user_context=user_context,
                mcp_server_calls=mcp_calls,
                mcp_server_duration_ms=mcp_duration
            )
            
            # Log successful authentication if user is authenticated
            if user_context and not is_bypass_path:
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.AUTH_SUCCESS,
                    user_id=user_context.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "username": user_context.username,
                        "email": user_context.email,
                        "request_id": request_id
                    }
                )
            
            return response
            
        except Exception as e:
            # Calculate MCP server metrics even for failed requests
            mcp_calls = getattr(request.state, "mcp_server_calls", 0) - mcp_calls_start
            mcp_duration = getattr(request.state, "mcp_server_duration_ms", 0.0) - mcp_duration_start
            
            # Determine status code and error type
            status_code = 500
            error_msg = str(e)
            
            # Handle specific error types
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                status_code = 401
                # Log authentication failure
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.AUTH_FAILURE,
                    user_id=user_context.user_id if user_context else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "error": error_msg,
                        "request_id": request_id
                    }
                )
            elif "token" in error_msg.lower() and "expired" in error_msg.lower():
                status_code = 401
                # Log token expiration
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.TOKEN_EXPIRED,
                    user_id=user_context.user_id if user_context else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "error": error_msg,
                        "request_id": request_id
                    }
                )
            elif "token" in error_msg.lower() and "invalid" in error_msg.lower():
                status_code = 401
                # Log invalid token
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.TOKEN_INVALID,
                    user_id=user_context.user_id if user_context else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "error": error_msg,
                        "request_id": request_id
                    }
                )
            elif "forbidden" in error_msg.lower():
                status_code = 403
                # Log unauthorized access
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                    user_id=user_context.user_id if user_context else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "error": error_msg,
                        "request_id": request_id
                    }
                )
            elif "rate limit" in error_msg.lower():
                status_code = 429
                # Log rate limit exceeded
                self.observability_service.log_security_event(
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    user_id=user_context.user_id if user_context else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    details={
                        "error": error_msg,
                        "request_id": request_id
                    }
                )
            
            # Log failed request completion
            self.observability_service.log_request_end(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                start_time=start_time,
                user_context=user_context,
                mcp_server_calls=mcp_calls,
                mcp_server_duration_ms=mcp_duration,
                error=error_msg
            )
            
            # Return appropriate error response
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "error": {
                        "type": type(e).__name__,
                        "message": error_msg,
                        "request_id": request_id,
                        "timestamp": time.time()
                    }
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (common in load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


def add_mcp_server_call_tracking(request: Request, server_name: str, tool_name: str, duration_ms: float):
    """Add MCP server call tracking to the current request."""
    # Initialize tracking if not present
    if not hasattr(request.state, "mcp_server_calls"):
        request.state.mcp_server_calls = 0
        request.state.mcp_server_duration_ms = 0.0
        request.state.mcp_server_details = []
    
    # Update tracking
    request.state.mcp_server_calls += 1
    request.state.mcp_server_duration_ms += duration_ms
    request.state.mcp_server_details.append({
        "server_name": server_name,
        "tool_name": tool_name,
        "duration_ms": duration_ms
    })
    
    # Log the MCP server call
    observability_service = get_observability_service()
    observability_service.log_mcp_server_call(
        server_name=server_name,
        tool_name=tool_name,
        duration_ms=duration_ms,
        success=True  # If we reach here, the call was successful
    )


def add_mcp_server_error_tracking(request: Request, server_name: str, tool_name: str, duration_ms: float, error: str):
    """Add MCP server error tracking to the current request."""
    # Initialize tracking if not present
    if not hasattr(request.state, "mcp_server_calls"):
        request.state.mcp_server_calls = 0
        request.state.mcp_server_duration_ms = 0.0
        request.state.mcp_server_details = []
    
    # Update tracking (still count failed calls)
    request.state.mcp_server_calls += 1
    request.state.mcp_server_duration_ms += duration_ms
    request.state.mcp_server_details.append({
        "server_name": server_name,
        "tool_name": tool_name,
        "duration_ms": duration_ms,
        "error": error
    })
    
    # Log the MCP server error
    observability_service = get_observability_service()
    observability_service.log_mcp_server_call(
        server_name=server_name,
        tool_name=tool_name,
        duration_ms=duration_ms,
        success=False,
        error=error
    )