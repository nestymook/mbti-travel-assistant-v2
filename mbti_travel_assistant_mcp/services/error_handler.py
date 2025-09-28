"""
Error Handler Service

This module provides comprehensive error handling functionality for the
MBTI Travel Assistant, converting various exception types into structured
error responses suitable for frontend consumption.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from services.mcp_client_manager import (
    MCPConnectionError, 
    MCPToolCallError, 
    MCPCircuitBreakerOpenError,
    MCPErrorType
)
from models.auth_models import AuthenticationError
from services.auth_service import AuthenticationError as AuthError

logger = logging.getLogger(__name__)


class SystemErrorType(Enum):
    """System error types for categorization"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    MCP_CONNECTION_ERROR = "mcp_connection_error"
    MCP_TOOL_ERROR = "mcp_tool_error"
    MCP_CIRCUIT_BREAKER_ERROR = "mcp_circuit_breaker_error"
    PARSING_ERROR = "parsing_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INTERNAL_ERROR = "internal_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorHandler:
    """
    Service for handling and formatting errors into structured responses.
    
    This service converts various exception types into standardized error
    responses that provide meaningful information to frontend applications
    and users while maintaining security by not exposing internal details.
    """
    
    def __init__(self):
        """Initialize error handler with configuration"""
        self.include_debug_info = False  # Set to True for development
        self.max_error_message_length = 500
    
    def handle_error(
        self,
        error: Exception,
        correlation_id: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return a structured error response.
        
        Args:
            error: The exception that occurred
            correlation_id: Request correlation ID for logging
            request_context: Additional context about the request
            
        Returns:
            Structured error response dictionary
        """
        error_type = self._classify_error(error)
        
        # Log error with appropriate level
        log_level = self._get_log_level_for_error(error_type)
        logger.log(
            log_level,
            f"Handling {error_type.value}: {type(error).__name__}: {str(error)}",
            extra={
                "correlation_id": correlation_id,
                "error_type": error_type.value,
                "request_context": request_context
            },
            exc_info=log_level >= logging.ERROR
        )
        
        # Route to specific error handler
        if error_type == SystemErrorType.VALIDATION_ERROR:
            return self._handle_validation_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.AUTHENTICATION_ERROR:
            return self._handle_authentication_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.AUTHORIZATION_ERROR:
            return self._handle_authorization_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.MCP_CONNECTION_ERROR:
            return self._handle_mcp_connection_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.MCP_TOOL_ERROR:
            return self._handle_mcp_tool_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.MCP_CIRCUIT_BREAKER_ERROR:
            return self._handle_mcp_circuit_breaker_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.PARSING_ERROR:
            return self._handle_parsing_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.TIMEOUT_ERROR:
            return self._handle_timeout_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.RATE_LIMIT_ERROR:
            return self._handle_rate_limit_error(error, correlation_id, request_context)
        elif error_type == SystemErrorType.CONFIGURATION_ERROR:
            return self._handle_configuration_error(error, correlation_id, request_context)
        else:
            return self._handle_generic_error(error, correlation_id, request_context)
    
    def _classify_error(self, error: Exception) -> SystemErrorType:
        """
        Classify error type for proper handling.
        
        Args:
            error: Exception to classify
            
        Returns:
            SystemErrorType enum value
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # MCP-specific errors
        if isinstance(error, MCPCircuitBreakerOpenError):
            return SystemErrorType.MCP_CIRCUIT_BREAKER_ERROR
        elif isinstance(error, MCPConnectionError):
            return SystemErrorType.MCP_CONNECTION_ERROR
        elif isinstance(error, MCPToolCallError):
            return SystemErrorType.MCP_TOOL_ERROR
        
        # Authentication errors
        elif isinstance(error, (AuthenticationError, AuthError)):
            return SystemErrorType.AUTHENTICATION_ERROR
        elif "authentication" in error_str or "unauthorized" in error_str:
            return SystemErrorType.AUTHENTICATION_ERROR
        elif "authorization" in error_str or "forbidden" in error_str:
            return SystemErrorType.AUTHORIZATION_ERROR
        
        # Validation errors
        elif isinstance(error, ValueError) or "validation" in error_str:
            return SystemErrorType.VALIDATION_ERROR
        
        # Network and timeout errors
        elif isinstance(error, (ConnectionError, TimeoutError)):
            if "timeout" in error_str:
                return SystemErrorType.TIMEOUT_ERROR
            else:
                return SystemErrorType.MCP_CONNECTION_ERROR
        
        # Parsing errors
        elif "json" in error_str or "parse" in error_str or "decode" in error_str:
            return SystemErrorType.PARSING_ERROR
        
        # Rate limiting
        elif "rate limit" in error_str or "429" in error_str:
            return SystemErrorType.RATE_LIMIT_ERROR
        
        # Configuration errors
        elif "config" in error_str or "setting" in error_str:
            return SystemErrorType.CONFIGURATION_ERROR
        
        else:
            return SystemErrorType.INTERNAL_ERROR
    
    def _get_log_level_for_error(self, error_type: SystemErrorType) -> int:
        """
        Get appropriate log level for error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Logging level constant
        """
        # Errors that should be logged as warnings (expected/recoverable)
        warning_errors = {
            SystemErrorType.VALIDATION_ERROR,
            SystemErrorType.AUTHENTICATION_ERROR,
            SystemErrorType.AUTHORIZATION_ERROR,
            SystemErrorType.RATE_LIMIT_ERROR,
            SystemErrorType.MCP_CIRCUIT_BREAKER_ERROR
        }
        
        if error_type in warning_errors:
            return logging.WARNING
        else:
            return logging.ERROR
    
    def _create_base_error_response(
        self,
        error_type: str,
        message: str,
        suggested_actions: List[str],
        correlation_id: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create base error response structure.
        
        Args:
            error_type: Type of error
            message: Error message
            suggested_actions: List of suggested actions
            correlation_id: Request correlation ID
            additional_info: Additional error information
            
        Returns:
            Base error response dictionary
        """
        # Truncate message if too long
        if len(message) > self.max_error_message_length:
            message = message[:self.max_error_message_length - 3] + "..."
        
        error_response = {
            "recommendation": None,
            "candidates": [],
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id,
                "error_handled": True
            },
            "error": {
                "error_type": error_type,
                "message": message,
                "suggested_actions": suggested_actions
            }
        }
        
        # Add additional info if provided
        if additional_info:
            error_response["error"].update(additional_info)
        
        return error_response
    
    def _handle_validation_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle validation errors from request processing."""
        error_message = str(error)
        
        # Provide specific guidance based on error content
        suggested_actions = []
        if "district" in error_message.lower():
            suggested_actions.extend([
                "Provide a valid district name (e.g., 'Central district', 'Admiralty')",
                "Check the spelling of the district name"
            ])
        if "meal_time" in error_message.lower() or "meal" in error_message.lower():
            suggested_actions.extend([
                "Specify meal_time as one of: 'breakfast', 'lunch', 'dinner'",
                "Ensure meal_time parameter is provided"
            ])
        if not suggested_actions:
            suggested_actions = [
                "Check that all required parameters are provided",
                "Ensure parameter values are in the correct format",
                "Verify the request payload structure"
            ]
        
        return self._create_base_error_response(
            error_type="validation_error",
            message=f"Request validation failed: {error_message}",
            suggested_actions=suggested_actions,
            correlation_id=correlation_id,
            additional_info={
                "request_context": request_context if self.include_debug_info else None
            }
        )
    
    def _handle_authentication_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle authentication errors."""
        error_message = str(error)
        
        # Provide specific guidance based on error type
        if isinstance(error, (AuthenticationError, AuthError)):
            if "expired" in str(error).lower():
                message = "Invalid or expired authentication token"
                suggested_actions = [
                    "Obtain a new authentication token",
                    "Check that the token is properly formatted",
                    "Ensure the token has not expired"
                ]
            elif "invalid" in str(error).lower():
                message = "Authentication failed"
                suggested_actions = [
                    "Check your authentication credentials",
                    "Ensure you have permission to access this service",
                    "Contact support if authentication issues persist"
                ]
            else:
                message = "Authentication failed"
                suggested_actions = [
                    "Check your authentication credentials",
                    "Ensure you have permission to access this service",
                    "Contact support if authentication issues persist"
                ]
        else:
            message = "Authentication required"
            suggested_actions = [
                "Provide a valid authentication token",
                "Log in to obtain authentication credentials",
                "Contact support for authentication assistance"
            ]
        
        return self._create_base_error_response(
            error_type="authentication_error",
            message=message,
            suggested_actions=suggested_actions,
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 0,  # Don't retry authentication errors
                "error_details": error_message if self.include_debug_info else None
            }
        )
    
    def _handle_authorization_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle authorization errors."""
        return self._create_base_error_response(
            error_type="authorization_error",
            message="Access denied - insufficient permissions",
            suggested_actions=[
                "Check that you have permission to access restaurant data",
                "Contact your administrator for access",
                "Verify your account has the required permissions"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 0  # Don't retry authorization errors
            }
        )
    
    def _handle_mcp_connection_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle MCP connection errors."""
        if isinstance(error, MCPConnectionError):
            server_name = getattr(error, 'server_name', 'restaurant service')
            message = f"Unable to connect to {server_name}"
        else:
            message = "Unable to connect to restaurant services"
        
        return self._create_base_error_response(
            error_type="connection_error",
            message=message,
            suggested_actions=[
                "Try again in a few moments",
                "Check your internet connection",
                "Contact support if the issue persists"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 30,  # Suggest retry after 30 seconds
                "service_status": "degraded"
            }
        )
    
    def _handle_mcp_tool_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle MCP tool call errors."""
        if isinstance(error, MCPToolCallError):
            tool_name = getattr(error, 'tool_name', 'restaurant tool')
            server_name = getattr(error, 'server_name', 'restaurant service')
            message = f"Error calling {tool_name} on {server_name}"
        else:
            message = "Restaurant service error"
        
        return self._create_base_error_response(
            error_type="service_error",
            message=message,
            suggested_actions=[
                "Try again with different search criteria",
                "Simplify your search parameters",
                "Contact support if the error persists"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 10,  # Suggest retry after 10 seconds
                "service_status": "degraded"
            }
        )
    
    def _handle_mcp_circuit_breaker_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle MCP circuit breaker errors."""
        if isinstance(error, MCPCircuitBreakerOpenError):
            server_name = getattr(error, 'server_name', 'restaurant service')
            recovery_time = getattr(error, 'recovery_time', None)
            message = f"{server_name} is temporarily unavailable"
            
            retry_after = 60  # Default retry after 1 minute
            if recovery_time:
                retry_after = max(int((recovery_time - datetime.now()).total_seconds()), 10)
        else:
            message = "Restaurant service is temporarily unavailable"
            retry_after = 60
        
        return self._create_base_error_response(
            error_type="service_unavailable",
            message=message,
            suggested_actions=[
                f"Try again in {retry_after // 60} minute(s)",
                "Use cached results if available",
                "Contact support if the service remains unavailable"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": retry_after,
                "service_status": "unavailable"
            }
        )
    
    def _handle_parsing_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle parsing errors."""
        return self._create_base_error_response(
            error_type="parsing_error",
            message="Error processing restaurant data",
            suggested_actions=[
                "Try again with a simpler request",
                "Contact support if the issue persists"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 5,  # Suggest retry after 5 seconds
                "error_details": str(error) if self.include_debug_info else None
            }
        )
    
    def _handle_timeout_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle timeout errors from MCP server calls."""
        return self._create_base_error_response(
            error_type="timeout_error",
            message="Request timed out while processing restaurant data",
            suggested_actions=[
                "Try again with a simpler search",
                "Wait a moment and retry",
                "Contact support if timeouts persist"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 15,  # Suggest retry after 15 seconds
                "timeout_duration": "30s"
            }
        )
    
    def _handle_rate_limit_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle rate limiting errors."""
        return self._create_base_error_response(
            error_type="rate_limit_error",
            message="Too many requests - please slow down",
            suggested_actions=[
                "Wait before making another request",
                "Reduce the frequency of your requests",
                "Contact support for rate limit increases"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 60,  # Suggest retry after 1 minute
                "rate_limit_info": "Standard rate limits apply"
            }
        )
    
    def _handle_configuration_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle configuration errors."""
        return self._create_base_error_response(
            error_type="configuration_error",
            message="Service configuration error",
            suggested_actions=[
                "Contact support for assistance",
                "Try again later"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 300,  # Suggest retry after 5 minutes
                "error_details": str(error) if self.include_debug_info else None
            }
        )
    
    def _handle_generic_error(
        self,
        error: Exception,
        correlation_id: Optional[str],
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle generic or unknown errors."""
        error_message = "An unexpected error occurred while processing your request"
        
        # Add more specific message for known error types
        error_str = str(error).lower()
        if "memory" in error_str or "out of memory" in error_str:
            error_message = "System temporarily overloaded"
        elif "disk" in error_str or "space" in error_str:
            error_message = "System storage temporarily unavailable"
        elif "network" in error_str:
            error_message = "Network connectivity issue"
        
        return self._create_base_error_response(
            error_type="internal_error",
            message=error_message,
            suggested_actions=[
                "Try again in a few moments",
                f"Contact support with correlation ID: {correlation_id}" if correlation_id else "Contact support for assistance",
                "Use simpler search criteria if the issue persists"
            ],
            correlation_id=correlation_id,
            additional_info={
                "retry_after": 30,
                "error_class": type(error).__name__ if self.include_debug_info else None,
                "stack_trace": traceback.format_exc() if self.include_debug_info else None
            }
        )
    
    def handle_malformed_payload_error(
        self,
        payload: Any,
        validation_errors: List[str],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle malformed payload errors with detailed validation feedback.
        
        Args:
            payload: The malformed payload
            validation_errors: List of validation error messages
            correlation_id: Request correlation ID
            
        Returns:
            Structured error response
        """
        error_message = "Request payload is malformed or invalid"
        
        suggested_actions = [
            "Check the request payload format",
            "Ensure all required fields are provided",
            "Verify field types and values"
        ]
        
        # Add specific suggestions based on validation errors
        for validation_error in validation_errors:
            if "district" in validation_error.lower():
                suggested_actions.append("Provide a valid district name")
            elif "meal_time" in validation_error.lower():
                suggested_actions.append("Use valid meal_time: breakfast, lunch, or dinner")
            elif "json" in validation_error.lower():
                suggested_actions.append("Ensure payload is valid JSON format")
        
        return self._create_base_error_response(
            error_type="validation_error",
            message=error_message,
            suggested_actions=suggested_actions[:5],  # Limit to 5 suggestions
            correlation_id=correlation_id,
            additional_info={
                "validation_errors": validation_errors,
                "payload_type": type(payload).__name__ if self.include_debug_info else None
            }
        )
    
    def handle_authentication_failure(
        self,
        failure_reason: str,
        correlation_id: Optional[str] = None,
        request_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle authentication failures with specific guidance.
        
        Args:
            failure_reason: Reason for authentication failure
            correlation_id: Request correlation ID
            request_headers: Request headers for context
            
        Returns:
            Structured error response
        """
        failure_lower = failure_reason.lower()
        
        if "token" in failure_lower and "expired" in failure_lower:
            message = "Authentication token has expired"
            suggested_actions = [
                "Obtain a new authentication token",
                "Check token expiration time",
                "Implement automatic token refresh"
            ]
        elif "token" in failure_lower and "invalid" in failure_lower:
            message = "Authentication token is invalid"
            suggested_actions = [
                "Check token format and encoding",
                "Verify token was issued by the correct authority",
                "Ensure token has not been tampered with"
            ]
        elif "missing" in failure_lower:
            message = "Authentication token is missing"
            suggested_actions = [
                "Include Authorization header in request",
                "Use format: Authorization: Bearer <token>",
                "Obtain authentication token before making requests"
            ]
        else:
            message = f"Authentication failed: {failure_reason}"
            suggested_actions = [
                "Check authentication credentials",
                "Verify token is valid and not expired",
                "Contact support for authentication assistance"
            ]
        
        return self._create_base_error_response(
            error_type="authentication_error",
            message=message,
            suggested_actions=suggested_actions,
            correlation_id=correlation_id,
            additional_info={
                "failure_reason": failure_reason,
                "has_auth_header": bool(request_headers and request_headers.get("Authorization")) if self.include_debug_info else None
            }
        )