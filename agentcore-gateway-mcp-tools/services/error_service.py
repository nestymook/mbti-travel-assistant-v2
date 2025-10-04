"""
Error service for the AgentCore Gateway MCP Tools service.

This module provides utilities for error handling, logging, and response formatting
across the application.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import ValidationError

from middleware.error_handler import (
    AuthenticationException,
    MCPServerException,
    RateLimitException,
    create_authentication_error,
    create_mcp_server_error,
    create_rate_limit_error,
)
from models.error_models import ErrorType


logger = logging.getLogger(__name__)


class ErrorService:
    """Service for handling and formatting errors across the application."""
    
    def __init__(self):
        self.logger = logger
    
    def handle_validation_error(
        self,
        error: ValidationError,
        context: Optional[str] = None,
    ) -> HTTPException:
        """Handle Pydantic validation errors and convert to HTTP exceptions."""
        
        error_details = []
        for err in error.errors():
            field_path = ".".join(str(loc) for loc in err["loc"])
            error_details.append({
                "field": field_path,
                "message": err["msg"],
                "type": err["type"],
                "input": err.get("input"),
            })
        
        message = f"Validation failed{f' for {context}' if context else ''}"
        
        self.logger.warning(
            f"Validation error: {message}",
            extra={
                "error_details": error_details,
                "context": context,
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": message,
                "errors": error_details,
            }
        )
    
    def handle_mcp_connection_error(
        self,
        server_name: str,
        server_endpoint: str,
        original_error: Exception,
        retry_attempt: int = 1,
        max_retries: int = 3,
    ) -> MCPServerException:
        """Handle MCP server connection errors with retry logic."""
        
        error_message = f"Failed to connect to MCP server: {str(original_error)}"
        
        self.logger.error(
            f"MCP server connection failed: {server_name} at {server_endpoint}",
            extra={
                "server_name": server_name,
                "server_endpoint": server_endpoint,
                "retry_attempt": retry_attempt,
                "max_retries": max_retries,
                "original_error": str(original_error),
            },
            exc_info=True,
        )
        
        # Calculate retry delay based on attempt number (exponential backoff)
        retry_after = min(30, 2 ** retry_attempt)
        
        return create_mcp_server_error(
            server_name=server_name,
            server_endpoint=server_endpoint,
            error_message=error_message,
            retry_after=retry_after,
            max_retries=max_retries,
            current_attempt=retry_attempt,
        )
    
    def handle_mcp_tool_error(
        self,
        server_name: str,
        tool_name: str,
        original_error: Exception,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> MCPServerException:
        """Handle MCP tool execution errors."""
        
        error_message = f"MCP tool '{tool_name}' failed: {str(original_error)}"
        
        self.logger.error(
            f"MCP tool execution failed: {tool_name} on {server_name}",
            extra={
                "server_name": server_name,
                "tool_name": tool_name,
                "parameters": parameters,
                "original_error": str(original_error),
            },
            exc_info=True,
        )
        
        return create_mcp_server_error(
            server_name=server_name,
            server_endpoint="unknown",
            error_message=error_message,
            retry_after=10,
            max_retries=2,
            current_attempt=1,
        )
    
    def handle_authentication_error(
        self,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
        discovery_url: Optional[str] = None,
    ) -> AuthenticationException:
        """Handle authentication errors with appropriate details."""
        
        error_messages = {
            "missing_token": "Authentication token is required",
            "invalid_token": "Authentication token is invalid or expired",
            "expired_token": "Authentication token has expired",
            "insufficient_scope": "Insufficient permissions for this operation",
            "malformed_token": "Authentication token format is invalid",
        }
        
        message = error_messages.get(error_type, "Authentication failed")
        
        self.logger.warning(
            f"Authentication error: {error_type}",
            extra={
                "error_type": error_type,
                "details": details,
                "discovery_url": discovery_url,
            }
        )
        
        required_scopes = None
        if error_type == "insufficient_scope" and details:
            required_scopes = details.get("required_scopes")
        
        return create_authentication_error(
            message=message,
            discovery_url=discovery_url,
            required_scopes=required_scopes,
        )
    
    def handle_rate_limit_error(
        self,
        limit: int,
        window: int,
        current_usage: int,
        user_id: Optional[str] = None,
    ) -> RateLimitException:
        """Handle rate limiting errors."""
        
        retry_after = window  # Wait for the full window to reset
        
        self.logger.warning(
            f"Rate limit exceeded for user {user_id or 'unknown'}",
            extra={
                "user_id": user_id,
                "limit": limit,
                "window": window,
                "current_usage": current_usage,
                "retry_after": retry_after,
            }
        )
        
        return create_rate_limit_error(
            limit=limit,
            window=window,
            retry_after=retry_after,
            current_usage=current_usage,
        )
    
    def handle_timeout_error(
        self,
        operation: str,
        timeout_seconds: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> HTTPException:
        """Handle timeout errors."""
        
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        
        self.logger.error(
            f"Timeout error: {message}",
            extra={
                "operation": operation,
                "timeout_seconds": timeout_seconds,
                "context": context,
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "message": message,
                "timeout_seconds": timeout_seconds,
                "retry_guidance": "Please try again with a simpler request or contact support if the issue persists.",
            }
        )
    
    def handle_service_unavailable_error(
        self,
        service_name: str,
        reason: Optional[str] = None,
        retry_after: Optional[int] = None,
    ) -> HTTPException:
        """Handle service unavailable errors."""
        
        message = f"Service '{service_name}' is temporarily unavailable"
        if reason:
            message += f": {reason}"
        
        self.logger.error(
            f"Service unavailable: {service_name}",
            extra={
                "service_name": service_name,
                "reason": reason,
                "retry_after": retry_after,
            }
        )
        
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": message,
                "service_name": service_name,
                "retry_after": retry_after,
                "retry_guidance": "Please wait and try again later.",
            },
            headers=headers,
        )
    
    def log_error_context(
        self,
        error: Exception,
        context: Dict[str, Any],
        level: str = "error",
    ) -> None:
        """Log error with additional context information."""
        
        log_method = getattr(self.logger, level, self.logger.error)
        
        log_method(
            f"Error in {context.get('operation', 'unknown operation')}: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                **context,
            },
            exc_info=True,
        )
    
    def create_error_summary(
        self,
        errors: List[Exception],
        operation: str,
    ) -> Dict[str, Any]:
        """Create a summary of multiple errors for logging or response."""
        
        error_summary = {
            "operation": operation,
            "total_errors": len(errors),
            "error_types": {},
            "errors": [],
        }
        
        for error in errors:
            error_type = type(error).__name__
            error_summary["error_types"][error_type] = error_summary["error_types"].get(error_type, 0) + 1
            
            error_summary["errors"].append({
                "type": error_type,
                "message": str(error),
            })
        
        return error_summary
    
    def should_retry_error(
        self,
        error: Exception,
        attempt: int,
        max_attempts: int,
    ) -> bool:
        """Determine if an error should trigger a retry."""
        
        if attempt >= max_attempts:
            return False
        
        # Retry on specific error types
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            MCPServerException,
        )
        
        if isinstance(error, retryable_errors):
            return True
        
        # Retry on specific HTTP status codes
        if isinstance(error, HTTPException):
            retryable_status_codes = {
                status.HTTP_408_REQUEST_TIMEOUT,
                status.HTTP_429_TOO_MANY_REQUESTS,
                status.HTTP_502_BAD_GATEWAY,
                status.HTTP_503_SERVICE_UNAVAILABLE,
                status.HTTP_504_GATEWAY_TIMEOUT,
            }
            return error.status_code in retryable_status_codes
        
        return False
    
    def calculate_retry_delay(
        self,
        attempt: int,
        base_delay: int = 1,
        max_delay: int = 60,
        exponential: bool = True,
    ) -> int:
        """Calculate retry delay with exponential backoff."""
        
        if exponential:
            delay = base_delay * (2 ** (attempt - 1))
        else:
            delay = base_delay * attempt
        
        return min(delay, max_delay)


# Global error service instance
error_service = ErrorService()