"""
Comprehensive Error Handling System for MBTI Travel Planner Agent

This module provides a centralized error handling system that converts technical errors
to user-friendly messages, implements logging with appropriate severity levels, and
creates fallback responses to maintain user experience when services are unavailable.
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
import json


class ErrorSeverity(Enum):
    """Error severity levels for logging and monitoring."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for classification and handling."""
    CONNECTION = "connection"
    SERVICE = "service"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONFIGURATION = "configuration"
    UNEXPECTED = "unexpected"


@dataclass
class ErrorContext:
    """Context information for error handling and logging."""
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    environment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    success: bool = False
    error_type: str = ""
    message: str = ""
    user_message: str = ""
    fallback_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    retry_after: Optional[int] = None
    support_reference: Optional[str] = None


class GatewayError(Exception):
    """Base exception for gateway communication errors."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNEXPECTED, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Dict[str, Any] = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class GatewayConnectionError(GatewayError):
    """Network connection errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class GatewayServiceError(GatewayError):
    """Gateway service errors (4xx, 5xx)."""
    
    def __init__(self, message: str, status_code: int = None, 
                 response_data: Dict = None, details: Dict[str, Any] = None):
        self.status_code = status_code
        self.response_data = response_data or {}
        
        # Determine severity based on status code
        if status_code:
            if 400 <= status_code < 500:
                severity = ErrorSeverity.MEDIUM
            elif 500 <= status_code < 600:
                severity = ErrorSeverity.HIGH
            else:
                severity = ErrorSeverity.MEDIUM
        else:
            severity = ErrorSeverity.MEDIUM
        
        super().__init__(
            message=message,
            category=ErrorCategory.SERVICE,
            severity=severity,
            details=details or {}
        )


class GatewayValidationError(GatewayError):
    """Request/response validation errors."""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None, 
                 details: Dict[str, Any] = None):
        self.field_errors = field_errors or {}
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details=details
        )


class GatewayAuthenticationError(GatewayError):
    """Authentication and authorization errors."""
    
    def __init__(self, message: str, auth_type: str = None, 
                 details: Dict[str, Any] = None):
        self.auth_type = auth_type
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class GatewayTimeoutError(GatewayError):
    """Request timeout errors."""
    
    def __init__(self, message: str, timeout_duration: int = None, 
                 details: Dict[str, Any] = None):
        self.timeout_duration = timeout_duration
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details=details
        )


class GatewayRateLimitError(GatewayError):
    """Rate limiting errors."""
    
    def __init__(self, message: str, retry_after: int = None, 
                 details: Dict[str, Any] = None):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details=details
        )


class GatewayConfigurationError(GatewayError):
    """Configuration and setup errors."""
    
    def __init__(self, message: str, config_key: str = None, 
                 details: Dict[str, Any] = None):
        self.config_key = config_key
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details=details
        )


class ErrorHandler:
    """
    Centralized error handling system for the MBTI Travel Planner Agent.
    
    Provides comprehensive error processing, logging, and user-friendly response generation.
    """
    
    def __init__(self, logger_name: str = "mbti_travel_planner"):
        """
        Initialize the error handler.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self._setup_logging()
        
        # User-friendly error messages
        self.user_messages = {
            ErrorCategory.CONNECTION: {
                "message": "I'm having trouble connecting to the restaurant search service right now.",
                "fallback": "I can still help you with general travel planning questions while we work on this.",
                "suggestions": [
                    "Please try again in a few moments",
                    "Check your internet connection",
                    "Ask me about other travel planning topics"
                ]
            },
            ErrorCategory.SERVICE: {
                "message": "The restaurant search service is experiencing some issues.",
                "fallback": "Let me know if you'd like help with other travel planning topics.",
                "suggestions": [
                    "Try rephrasing your restaurant search request",
                    "Ask about tourist attractions instead",
                    "I can help with general Hong Kong travel information"
                ]
            },
            ErrorCategory.VALIDATION: {
                "message": "There seems to be an issue with your request format.",
                "fallback": "Let me help you rephrase your request.",
                "suggestions": [
                    "Try asking about restaurants in a specific district",
                    "Specify meal types like 'lunch' or 'dinner'",
                    "Ask for recommendations in Central district"
                ]
            },
            ErrorCategory.AUTHENTICATION: {
                "message": "I'm having trouble accessing the restaurant database right now.",
                "fallback": "I can still provide general travel advice while this is resolved.",
                "suggestions": [
                    "Please try again in a few minutes",
                    "Ask me about Hong Kong attractions",
                    "I can help with travel planning tips"
                ]
            },
            ErrorCategory.TIMEOUT: {
                "message": "The restaurant search is taking longer than expected.",
                "fallback": "Let me try a different approach or help with other travel topics.",
                "suggestions": [
                    "Try searching for restaurants in a smaller area",
                    "Ask about specific types of cuisine",
                    "I can recommend popular districts for dining"
                ]
            },
            ErrorCategory.RATE_LIMIT: {
                "message": "I'm making too many restaurant searches right now.",
                "fallback": "Let's wait a moment before trying again, or I can help with other topics.",
                "suggestions": [
                    "Please wait a moment before searching again",
                    "Ask me about tourist attractions instead",
                    "I can provide general dining recommendations"
                ]
            },
            ErrorCategory.CONFIGURATION: {
                "message": "There's a configuration issue with the restaurant search system.",
                "fallback": "I can still help with general travel planning while this is resolved.",
                "suggestions": [
                    "Please try again later",
                    "Ask about Hong Kong attractions",
                    "I can provide general travel advice"
                ]
            },
            ErrorCategory.UNEXPECTED: {
                "message": "Something unexpected happened while searching for restaurants.",
                "fallback": "Please try rephrasing your request or ask about other travel topics.",
                "suggestions": [
                    "Try asking about restaurants differently",
                    "Ask about tourist attractions instead",
                    "I can help with general Hong Kong travel information"
                ]
            }
        }
    
    def _setup_logging(self) -> None:
        """Configure logging with appropriate formatters and handlers."""
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Ensure logger has handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _generate_support_reference(self, context: ErrorContext) -> str:
        """Generate a unique support reference for error tracking."""
        timestamp = context.timestamp.strftime("%Y%m%d_%H%M%S")
        operation = context.operation.replace(" ", "_").lower()
        return f"MBTI_{operation}_{timestamp}"
    
    def _log_error(self, error: Exception, context: ErrorContext, 
                   severity: ErrorSeverity) -> None:
        """
        Log error with appropriate severity level and context information.
        
        Args:
            error: The exception that occurred
            context: Error context information
            severity: Error severity level
        """
        # Prepare log data
        log_data = {
            "operation": context.operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity.value,
            "timestamp": context.timestamp.isoformat(),
            "environment": context.environment,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "request_id": context.request_id,
            "additional_data": context.additional_data
        }
        
        # Add error-specific details
        if isinstance(error, GatewayError):
            log_data.update({
                "category": error.category.value,
                "details": error.details
            })
        
        if isinstance(error, GatewayServiceError):
            log_data.update({
                "status_code": error.status_code,
                "response_data": error.response_data
            })
        
        # Log with appropriate level based on severity
        log_message = f"Error in {context.operation}: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra={"error_data": log_data})
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra={"error_data": log_data})
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra={"error_data": log_data})
        else:  # LOW
            self.logger.info(log_message, extra={"error_data": log_data})
        
        # Log stack trace for unexpected errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug("Stack trace:", exc_info=True)
    
    def handle_error(self, error: Exception, context: ErrorContext) -> ErrorResponse:
        """
        Process an error and generate a user-friendly response.
        
        Args:
            error: The exception that occurred
            context: Error context information
            
        Returns:
            ErrorResponse with user-friendly message and fallback options
        """
        # Determine error category and severity
        if isinstance(error, GatewayError):
            category = error.category
            severity = error.severity
        else:
            # Classify unknown errors
            category = self._classify_error(error)
            severity = ErrorSeverity.MEDIUM
        
        # Log the error
        self._log_error(error, context, severity)
        
        # Generate support reference
        support_reference = self._generate_support_reference(context)
        
        # Get user-friendly messages
        message_config = self.user_messages.get(category, self.user_messages[ErrorCategory.UNEXPECTED])
        
        # Build error response
        response = ErrorResponse(
            success=False,
            error_type=category.value,
            message=str(error),
            user_message=message_config["message"],
            fallback_message=message_config["fallback"],
            suggestions=message_config["suggestions"].copy(),
            support_reference=support_reference
        )
        
        # Add specific details based on error type
        response.details = {
            "operation": context.operation,
            "timestamp": context.timestamp.isoformat(),
            "severity": severity.value,
            "category": category.value
        }
        
        # Add error-specific information
        if isinstance(error, GatewayServiceError):
            response.details.update({
                "status_code": error.status_code,
                "service_response": error.response_data
            })
        
        if isinstance(error, GatewayRateLimitError) and error.retry_after:
            response.retry_after = error.retry_after
            response.suggestions.insert(0, f"Please wait {error.retry_after} seconds before trying again")
        
        if isinstance(error, GatewayValidationError) and error.field_errors:
            response.details["field_errors"] = error.field_errors
            response.suggestions.insert(0, "Check your request parameters")
        
        return response
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """
        Classify unknown errors into appropriate categories.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorCategory for the error
        """
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()
        
        # Connection-related errors
        if any(keyword in error_type for keyword in ['connection', 'network', 'timeout']):
            return ErrorCategory.CONNECTION
        
        if any(keyword in error_message for keyword in ['connection', 'network', 'unreachable']):
            return ErrorCategory.CONNECTION
        
        # Validation errors
        if any(keyword in error_type for keyword in ['validation', 'value', 'type']):
            return ErrorCategory.VALIDATION
        
        if any(keyword in error_message for keyword in ['invalid', 'required', 'format']):
            return ErrorCategory.VALIDATION
        
        # Authentication errors
        if any(keyword in error_type for keyword in ['auth', 'permission', 'forbidden']):
            return ErrorCategory.AUTHENTICATION
        
        if any(keyword in error_message for keyword in ['unauthorized', 'forbidden', 'token']):
            return ErrorCategory.AUTHENTICATION
        
        # Timeout errors
        if any(keyword in error_type for keyword in ['timeout']):
            return ErrorCategory.TIMEOUT
        
        if any(keyword in error_message for keyword in ['timeout', 'timed out']):
            return ErrorCategory.TIMEOUT
        
        # Default to unexpected
        return ErrorCategory.UNEXPECTED
    
    def create_fallback_response(self, operation: str, 
                               partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a fallback response when services are unavailable.
        
        Args:
            operation: The operation that failed
            partial_data: Any partial data that was retrieved
            
        Returns:
            Fallback response with helpful information
        """
        fallback_responses = {
            "search_restaurants_by_district": {
                "message": "I can't search the restaurant database right now, but I can suggest some popular dining areas in Hong Kong.",
                "suggestions": [
                    "Central district has many international restaurants",
                    "Tsim Sha Tsui offers great harbor views with dining",
                    "Causeway Bay is known for shopping and casual dining",
                    "Wan Chai has excellent local Hong Kong cuisine"
                ],
                "alternative_help": [
                    "Ask me about tourist attractions in these areas",
                    "I can provide general dining tips for Hong Kong",
                    "Let me know what type of cuisine you're interested in"
                ]
            },
            "recommend_restaurants": {
                "message": "I can't analyze restaurant recommendations right now, but I can share some general dining advice.",
                "suggestions": [
                    "Look for restaurants with high customer ratings",
                    "Try local Hong Kong specialties like dim sum",
                    "Consider restaurants in popular tourist areas",
                    "Check restaurant operating hours before visiting"
                ],
                "alternative_help": [
                    "Ask about specific types of cuisine",
                    "I can suggest popular dining districts",
                    "Let me know your dining preferences"
                ]
            },
            "search_restaurants_combined": {
                "message": "The restaurant search isn't working right now, but I can help you plan your dining experience.",
                "suggestions": [
                    "Popular lunch spots are usually in business districts",
                    "Dinner restaurants often have extended evening hours",
                    "Breakfast places are common in hotel areas",
                    "Central and Tsim Sha Tsui have diverse dining options"
                ],
                "alternative_help": [
                    "Tell me about your meal preferences",
                    "Ask about dining customs in Hong Kong",
                    "I can suggest areas known for specific cuisines"
                ]
            }
        }
        
        # Get operation-specific fallback or use default
        fallback = fallback_responses.get(operation, {
            "message": "I'm having trouble with that request right now, but I'm here to help with your Hong Kong travel planning.",
            "suggestions": [
                "Try asking about tourist attractions",
                "I can provide general travel tips",
                "Ask about transportation or accommodation"
            ],
            "alternative_help": [
                "Let me know what other travel information you need",
                "I can help with Hong Kong travel basics",
                "Ask about specific areas or activities you're interested in"
            ]
        })
        
        response = {
            "success": False,
            "fallback": True,
            "message": fallback["message"],
            "suggestions": fallback["suggestions"],
            "alternative_help": fallback["alternative_help"],
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Include any partial data that was retrieved
        if partial_data:
            response["partial_data"] = partial_data
            response["message"] += " I do have some limited information that might help."
        
        return response
    
    def log_performance_issue(self, operation: str, duration: float, 
                            threshold: float = 5.0, context: ErrorContext = None) -> None:
        """
        Log performance issues when operations take too long.
        
        Args:
            operation: The operation that was slow
            duration: Time taken in seconds
            threshold: Performance threshold in seconds
            context: Additional context information
        """
        if duration > threshold:
            severity = ErrorSeverity.MEDIUM if duration < threshold * 2 else ErrorSeverity.HIGH
            
            log_data = {
                "operation": operation,
                "duration": duration,
                "threshold": threshold,
                "performance_issue": True
            }
            
            if context:
                log_data.update({
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "environment": context.environment
                })
            
            if severity == ErrorSeverity.HIGH:
                self.logger.warning(
                    f"Performance issue in {operation}: {duration:.2f}s (threshold: {threshold}s)",
                    extra={"performance_data": log_data}
                )
            else:
                self.logger.info(
                    f"Slow operation {operation}: {duration:.2f}s",
                    extra={"performance_data": log_data}
                )
    
    def create_error_context(self, operation: str, **kwargs) -> ErrorContext:
        """
        Create an error context object with provided information.
        
        Args:
            operation: The operation being performed
            **kwargs: Additional context data
            
        Returns:
            ErrorContext object
        """
        return ErrorContext(
            operation=operation,
            user_id=kwargs.get("user_id"),
            session_id=kwargs.get("session_id"),
            request_id=kwargs.get("request_id"),
            environment=kwargs.get("environment"),
            additional_data=kwargs.get("additional_data", {})
        )


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_gateway_error(error: Exception, operation: str, **context_kwargs) -> Dict[str, Any]:
    """
    Convenience function to handle gateway errors.
    
    Args:
        error: The exception that occurred
        operation: The operation that failed
        **context_kwargs: Additional context information
        
    Returns:
        Error response dictionary
    """
    handler = get_error_handler()
    context = handler.create_error_context(operation, **context_kwargs)
    response = handler.handle_error(error, context)
    
    # Convert to dictionary format
    return {
        "success": response.success,
        "error": {
            "type": response.error_type,
            "message": response.user_message,
            "fallback": response.fallback_message,
            "suggestions": response.suggestions,
            "details": response.details,
            "support_reference": response.support_reference,
            "retry_after": response.retry_after
        }
    }


def create_fallback_response(operation: str, partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to create fallback responses.
    
    Args:
        operation: The operation that failed
        partial_data: Any partial data available
        
    Returns:
        Fallback response dictionary
    """
    handler = get_error_handler()
    return handler.create_fallback_response(operation, partial_data)


# Export main classes and functions
__all__ = [
    'ErrorHandler',
    'ErrorContext',
    'ErrorResponse',
    'ErrorSeverity',
    'ErrorCategory',
    'GatewayError',
    'GatewayConnectionError',
    'GatewayServiceError',
    'GatewayValidationError',
    'GatewayAuthenticationError',
    'GatewayTimeoutError',
    'GatewayRateLimitError',
    'GatewayConfigurationError',
    'get_error_handler',
    'handle_gateway_error',
    'create_fallback_response'
]