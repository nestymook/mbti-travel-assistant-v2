"""
Error handler middleware for the AgentCore Gateway MCP Tools service.

This module provides comprehensive error handling with proper HTTP status code mapping,
detailed error responses, and retry guidance for different error types.
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from models.error_models import (
    AuthenticationErrorDetail,
    AuthenticationErrorInfo,
    AuthenticationErrorResponse,
    ErrorInfo,
    ErrorResponse,
    ErrorType,
    MCPServerErrorDetail,
    MCPServerErrorInfo,
    MCPServerErrorResponse,
    RateLimitErrorDetail,
    RateLimitErrorInfo,
    RateLimitErrorResponse,
    ValidationErrorDetail,
    ValidationErrorInfo,
    ValidationErrorResponse,
)


logger = logging.getLogger(__name__)


class MCPServerException(Exception):
    """Custom exception for MCP server errors."""
    
    def __init__(
        self,
        message: str,
        server_name: str,
        server_endpoint: str,
        retry_after: Optional[int] = None,
        max_retries: Optional[int] = None,
        current_attempt: Optional[int] = None,
        health_check_url: Optional[str] = None,
    ):
        super().__init__(message)
        self.server_name = server_name
        self.server_endpoint = server_endpoint
        self.retry_after = retry_after
        self.max_retries = max_retries
        self.current_attempt = current_attempt
        self.health_check_url = health_check_url


class AuthenticationException(Exception):
    """Custom exception for authentication errors."""
    
    def __init__(
        self,
        message: str,
        auth_type: str = "JWT",
        discovery_url: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        required_scopes: Optional[List[str]] = None,
        token_format: Optional[str] = None,
        example_header: Optional[str] = None,
        help_url: Optional[str] = None,
    ):
        super().__init__(message)
        self.auth_type = auth_type
        self.discovery_url = discovery_url
        self.token_endpoint = token_endpoint
        self.required_scopes = required_scopes
        self.token_format = token_format
        self.example_header = example_header
        self.help_url = help_url


class RateLimitException(Exception):
    """Custom exception for rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        limit: int,
        window: int,
        retry_after: int,
        current_usage: Optional[int] = None,
    ):
        super().__init__(message)
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        self.current_usage = current_usage


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling and response formatting."""
    
    def __init__(self, app, include_trace_id: bool = True, log_errors: bool = True):
        super().__init__(app)
        self.include_trace_id = include_trace_id
        self.log_errors = log_errors
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any errors that occur."""
        trace_id = str(uuid.uuid4()) if self.include_trace_id else None
        
        # Add trace ID to request state for use in handlers
        if trace_id:
            request.state.trace_id = trace_id
        
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self._handle_exception(request, exc, trace_id)
    
    async def _handle_exception(
        self,
        request: Request,
        exc: Exception,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle different types of exceptions and return appropriate responses."""
        
        if self.log_errors:
            logger.error(
                f"Error processing request {request.method} {request.url}: {str(exc)}",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "url": str(request.url),
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )
        
        # Handle validation errors
        if isinstance(exc, (RequestValidationError, ValidationError)):
            return await self._handle_validation_error(exc, trace_id)
        
        # Handle authentication errors
        if isinstance(exc, AuthenticationException):
            return await self._handle_authentication_error(exc, trace_id)
        
        # Handle MCP server errors
        if isinstance(exc, MCPServerException):
            return await self._handle_mcp_server_error(exc, trace_id)
        
        # Handle rate limiting errors
        if isinstance(exc, RateLimitException):
            return await self._handle_rate_limit_error(exc, trace_id)
        
        # Handle HTTP exceptions
        if isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, trace_id)
        
        # Handle unexpected errors
        return await self._handle_internal_error(exc, trace_id)
    
    async def _handle_validation_error(
        self,
        exc: Union[RequestValidationError, ValidationError],
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle validation errors with detailed field information."""
        
        field_errors = []
        invalid_fields = []
        
        if isinstance(exc, RequestValidationError):
            errors = exc.errors()
        else:
            errors = exc.errors()
        
        for error in errors:
            field_path = ".".join(str(loc) for loc in error["loc"])
            field_name = field_path if field_path else "unknown"
            
            # Extract validation details
            error_type = error.get("type", "validation_error")
            message = error.get("msg", "Validation failed")
            invalid_value = error.get("input")
            
            # Generate suggestions based on error type
            suggestion = self._generate_validation_suggestion(error_type, error)
            
            field_error = ValidationErrorDetail(
                field=field_name,
                message=message,
                invalid_value=invalid_value,
                constraint=error_type,
                suggestion=suggestion,
            )
            
            field_errors.append(field_error)
            invalid_fields.append(field_name)
        
        error_info = ValidationErrorInfo(
            message="Request validation failed",
            code="VALIDATION_FAILED",
            field_errors=field_errors,
            invalid_fields=list(set(invalid_fields)),
            trace_id=trace_id,
        )
        
        error_response = ValidationErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )
    
    async def _handle_authentication_error(
        self,
        exc: AuthenticationException,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle authentication errors with clear requirements."""
        
        auth_details = AuthenticationErrorDetail(
            auth_type=exc.auth_type,
            discovery_url=exc.discovery_url,
            token_endpoint=exc.token_endpoint,
            required_scopes=exc.required_scopes,
            token_format=exc.token_format,
            example_header=exc.example_header,
        )
        
        error_info = AuthenticationErrorInfo(
            message=str(exc),
            code="AUTHENTICATION_REQUIRED",
            auth_details=auth_details,
            help_url=exc.help_url,
            trace_id=trace_id,
        )
        
        error_response = AuthenticationErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump(),
            headers={"WWW-Authenticate": f"{exc.auth_type} realm=\"AgentCore Gateway\""},
        )
    
    async def _handle_mcp_server_error(
        self,
        exc: MCPServerException,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle MCP server errors with retry guidance."""
        
        server_details = MCPServerErrorDetail(
            server_name=exc.server_name,
            server_endpoint=exc.server_endpoint,
            error_message=str(exc),
            retry_after=exc.retry_after,
            max_retries=exc.max_retries,
            current_attempt=exc.current_attempt,
            health_check_url=exc.health_check_url,
        )
        
        retry_guidance = self._generate_retry_guidance(exc)
        
        error_info = MCPServerErrorInfo(
            message=f"MCP server '{exc.server_name}' is unavailable",
            code="MCP_SERVER_UNAVAILABLE",
            server_details=server_details,
            retry_guidance=retry_guidance,
            trace_id=trace_id,
        )
        
        error_response = MCPServerErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(),
            headers=headers,
        )
    
    async def _handle_rate_limit_error(
        self,
        exc: RateLimitException,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle rate limiting errors with retry information."""
        
        rate_limit_details = RateLimitErrorDetail(
            limit=exc.limit,
            window=exc.window,
            retry_after=exc.retry_after,
            current_usage=exc.current_usage,
        )
        
        error_info = RateLimitErrorInfo(
            message=str(exc),
            code="RATE_LIMIT_EXCEEDED",
            rate_limit_details=rate_limit_details,
            trace_id=trace_id,
        )
        
        error_response = RateLimitErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response.model_dump(),
            headers={
                "Retry-After": str(exc.retry_after),
                "X-RateLimit-Limit": str(exc.limit),
                "X-RateLimit-Window": str(exc.window),
                "X-RateLimit-Remaining": str(max(0, exc.limit - (exc.current_usage or 0))),
            },
        )
    
    async def _handle_http_exception(
        self,
        exc: HTTPException,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        
        error_type = self._map_status_to_error_type(exc.status_code)
        
        error_info = ErrorInfo(
            type=error_type,
            message=exc.detail,
            code=f"HTTP_{exc.status_code}",
            trace_id=trace_id,
        )
        
        error_response = ErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
            headers=getattr(exc, "headers", None),
        )
    
    async def _handle_internal_error(
        self,
        exc: Exception,
        trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """Handle unexpected internal errors."""
        
        error_info = ErrorInfo(
            type=ErrorType.INTERNAL_ERROR,
            message="An unexpected error occurred",
            code="INTERNAL_SERVER_ERROR",
            details={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
            trace_id=trace_id,
        )
        
        error_response = ErrorResponse(
            error=error_info,
            request_id=trace_id,
            timestamp=datetime.utcnow(),
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
    
    def _generate_validation_suggestion(self, error_type: str, error: Dict[str, Any]) -> Optional[str]:
        """Generate helpful suggestions for validation errors."""
        
        suggestions = {
            "missing": "This field is required. Please provide a value.",
            "string_too_short": "The value is too short. Please provide a longer string.",
            "string_too_long": "The value is too long. Please provide a shorter string.",
            "value_error": "The value format is invalid. Please check the expected format.",
            "type_error": "The value type is incorrect. Please provide the correct data type.",
            "enum": "The value is not allowed. Please use one of the valid options.",
            "list_too_short": "The list needs more items. Please add additional elements.",
            "list_too_long": "The list has too many items. Please remove some elements.",
        }
        
        # Check for specific validation contexts
        if "districts" in str(error.get("loc", [])):
            return "Please provide valid Hong Kong district names such as 'Central district', 'Admiralty', 'Causeway Bay'."
        
        if "meal_types" in str(error.get("loc", [])):
            return "Please use valid meal types: 'breakfast', 'lunch', or 'dinner'."
        
        return suggestions.get(error_type, "Please check the value and try again.")
    
    def _generate_retry_guidance(self, exc: MCPServerException) -> str:
        """Generate retry guidance for MCP server errors."""
        
        guidance_parts = []
        
        if exc.retry_after:
            guidance_parts.append(f"Wait {exc.retry_after} seconds before retrying.")
        
        if exc.max_retries and exc.current_attempt:
            remaining = exc.max_retries - exc.current_attempt
            if remaining > 0:
                guidance_parts.append(f"You have {remaining} retry attempts remaining.")
            else:
                guidance_parts.append("Maximum retry attempts exceeded.")
        
        if exc.health_check_url:
            guidance_parts.append(f"Check server health at: {exc.health_check_url}")
        
        if not guidance_parts:
            guidance_parts.append("The MCP server is temporarily unavailable. Please try again later.")
        
        return " ".join(guidance_parts)
    
    def _map_status_to_error_type(self, status_code: int) -> ErrorType:
        """Map HTTP status codes to error types."""
        
        mapping = {
            400: ErrorType.VALIDATION_ERROR,
            401: ErrorType.AUTHENTICATION_ERROR,
            403: ErrorType.AUTHORIZATION_ERROR,
            408: ErrorType.TIMEOUT_ERROR,
            429: ErrorType.RATE_LIMIT_ERROR,
            503: ErrorType.SERVICE_UNAVAILABLE,
        }
        
        return mapping.get(status_code, ErrorType.INTERNAL_ERROR)


# Utility functions for creating specific exceptions
def create_authentication_error(
    message: str,
    discovery_url: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
) -> AuthenticationException:
    """Create a standardized authentication error."""
    
    return AuthenticationException(
        message=message,
        auth_type="JWT",
        discovery_url=discovery_url,
        token_format="Bearer <JWT_TOKEN>",
        example_header="Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        required_scopes=required_scopes,
        help_url="https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-authentication.html",
    )


def create_mcp_server_error(
    server_name: str,
    server_endpoint: str,
    error_message: str,
    retry_after: Optional[int] = 30,
    max_retries: int = 3,
    current_attempt: int = 1,
) -> MCPServerException:
    """Create a standardized MCP server error."""
    
    health_check_url = f"{server_endpoint.rstrip('/')}/health"
    
    return MCPServerException(
        message=error_message,
        server_name=server_name,
        server_endpoint=server_endpoint,
        retry_after=retry_after,
        max_retries=max_retries,
        current_attempt=current_attempt,
        health_check_url=health_check_url,
    )


def create_rate_limit_error(
    limit: int,
    window: int,
    retry_after: int,
    current_usage: Optional[int] = None,
) -> RateLimitException:
    """Create a standardized rate limit error."""
    
    message = f"Rate limit exceeded: {current_usage or 'unknown'}/{limit} requests per {window} seconds"
    
    return RateLimitException(
        message=message,
        limit=limit,
        window=window,
        retry_after=retry_after,
        current_usage=current_usage,
    )