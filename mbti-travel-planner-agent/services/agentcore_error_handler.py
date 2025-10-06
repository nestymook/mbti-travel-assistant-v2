"""
Comprehensive Error Handling System for AgentCore Integration

This module provides error handling specifically for AgentCore agent calls, including:
- Custom exception classes for different error types
- Circuit breaker pattern for agent calls
- Retry logic with configurable backoff strategies
- Graceful fallback mechanisms for agent unavailability
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Union, List, Callable, Awaitable
from dataclasses import dataclass, field
import json


class AgentCoreErrorType(Enum):
    """Types of AgentCore-specific errors."""
    AGENT_INVOCATION = "agent_invocation"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AGENT_UNAVAILABLE = "agent_unavailable"
    INVALID_RESPONSE = "invalid_response"
    CONFIGURATION = "configuration"
    CIRCUIT_BREAKER = "circuit_breaker"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[str] = field(default_factory=lambda: [
        "ServiceUnavailable",
        "ThrottlingException",
        "InternalServerError",
        "TimeoutError",
        "ConnectionError",
        "TemporaryFailure"
    ])


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3
    success_threshold: int = 2


@dataclass
class AgentCoreErrorContext:
    """Context information for AgentCore errors."""
    agent_arn: str
    operation: str
    input_text: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = field(default_factory=dict)


class AgentCoreError(Exception):
    """Base exception for AgentCore operations."""
    
    def __init__(self, message: str, error_type: AgentCoreErrorType = AgentCoreErrorType.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Dict[str, Any] = None, retryable: bool = False):
        super().__init__(message)
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.retryable = retryable
        self.timestamp = datetime.utcnow()


class AgentInvocationError(AgentCoreError):
    """Agent invocation specific errors."""
    
    def __init__(self, message: str, agent_arn: str, status_code: Optional[int] = None,
                 response_data: Dict = None, retryable: bool = True):
        self.agent_arn = agent_arn
        self.status_code = status_code
        self.response_data = response_data or {}
        
        # Determine if error is retryable based on status code
        if status_code:
            retryable = status_code >= 500 or status_code == 429
        
        super().__init__(
            message=message,
            error_type=AgentCoreErrorType.AGENT_INVOCATION,
            severity=ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM,
            details={"agent_arn": agent_arn, "status_code": status_code, "response_data": response_data},
            retryable=retryable
        )


class AuthenticationError(AgentCoreError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, auth_type: str = None, details: Dict[str, Any] = None):
        self.auth_type = auth_type
        super().__init__(
            message=message,
            error_type=AgentCoreErrorType.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details or {"auth_type": auth_type},
            retryable=True  # Token might be refreshable
        )


class AgentTimeoutError(AgentCoreError):
    """Agent call timeout errors."""
    
    def __init__(self, message: str, timeout_duration: int = None, agent_arn: str = None):
        self.timeout_duration = timeout_duration
        self.agent_arn = agent_arn
        super().__init__(
            message=message,
            error_type=AgentCoreErrorType.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details={"timeout_duration": timeout_duration, "agent_arn": agent_arn},
            retryable=True
        )


class AgentUnavailableError(AgentCoreError):
    """Agent unavailable errors."""
    
    def __init__(self, message: str, agent_arn: str, retry_after: Optional[int] = None):
        self.agent_arn = agent_arn
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_type=AgentCoreErrorType.AGENT_UNAVAILABLE,
            severity=ErrorSeverity.HIGH,
            details={"agent_arn": agent_arn, "retry_after": retry_after},
            retryable=True
        )


class CircuitBreakerOpenError(AgentCoreError):
    """Circuit breaker is open, preventing calls."""
    
    def __init__(self, message: str, agent_arn: str, retry_after: int):
        self.agent_arn = agent_arn
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_type=AgentCoreErrorType.CIRCUIT_BREAKER,
            severity=ErrorSeverity.MEDIUM,
            details={"agent_arn": agent_arn, "retry_after": retry_after},
            retryable=False  # Don't retry when circuit breaker is open
        )


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    half_open_calls: int = 0


class CircuitBreaker:
    """Circuit breaker implementation for AgentCore agent calls."""
    
    def __init__(self, agent_arn: str, config: CircuitBreakerConfig):
        self.agent_arn = agent_arn
        self.config = config
        self.stats = CircuitBreakerStats()
        self.logger = logging.getLogger(f"circuit_breaker.{agent_arn.split('/')[-1]}")
    
    def _should_attempt_call(self) -> bool:
        """Check if a call should be attempted based on circuit breaker state."""
        now = datetime.utcnow()
        
        if self.stats.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.stats.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (self.stats.last_failure_time and 
                now - self.stats.last_failure_time >= timedelta(seconds=self.config.recovery_timeout)):
                self.stats.state = CircuitBreakerState.HALF_OPEN
                self.stats.half_open_calls = 0
                self.logger.info(f"Circuit breaker transitioning to HALF_OPEN for {self.agent_arn}")
                return True
            return False
        
        elif self.stats.state == CircuitBreakerState.HALF_OPEN:
            return self.stats.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def _record_success(self) -> None:
        """Record a successful call."""
        now = datetime.utcnow()
        self.stats.last_success_time = now
        
        if self.stats.state == CircuitBreakerState.HALF_OPEN:
            self.stats.success_count += 1
            if self.stats.success_count >= self.config.success_threshold:
                self.stats.state = CircuitBreakerState.CLOSED
                self.stats.failure_count = 0
                self.stats.success_count = 0
                self.logger.info(f"Circuit breaker CLOSED for {self.agent_arn}")
        else:
            self.stats.failure_count = 0  # Reset failure count on success
    
    def _record_failure(self) -> None:
        """Record a failed call."""
        now = datetime.utcnow()
        self.stats.last_failure_time = now
        self.stats.failure_count += 1
        
        if self.stats.state == CircuitBreakerState.HALF_OPEN:
            self.stats.state = CircuitBreakerState.OPEN
            self.stats.half_open_calls = 0
            self.logger.warning(f"Circuit breaker OPEN (from half-open) for {self.agent_arn}")
        elif (self.stats.state == CircuitBreakerState.CLOSED and 
              self.stats.failure_count >= self.config.failure_threshold):
            self.stats.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker OPEN for {self.agent_arn} after {self.stats.failure_count} failures")
    
    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute function with circuit breaker protection."""
        if not self._should_attempt_call():
            retry_after = self.config.recovery_timeout
            if self.stats.last_failure_time:
                elapsed = (datetime.utcnow() - self.stats.last_failure_time).total_seconds()
                retry_after = max(0, self.config.recovery_timeout - int(elapsed))
            
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN for agent {self.agent_arn}",
                self.agent_arn,
                retry_after
            )
        
        if self.stats.state == CircuitBreakerState.HALF_OPEN:
            self.stats.half_open_calls += 1
        
        try:
            result = await func()
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "agent_arn": self.agent_arn,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "half_open_calls": self.stats.half_open_calls
        }


class RetryHandler:
    """Handles retry logic with configurable backoff strategies."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger("retry_handler")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff and jitter."""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            # Add random jitter (±25% of delay)
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter
        
        return max(0, delay)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        if isinstance(error, AgentCoreError):
            return error.retryable
        
        # Check error type/message against retryable patterns
        error_str = str(error)
        error_type = type(error).__name__
        
        return any(
            retryable in error_str or retryable in error_type
            for retryable in self.config.retryable_errors
        )
    
    async def execute_with_retry(self, func: Callable[[], Awaitable[Any]], 
                               context: AgentCoreErrorContext) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt - 1)
                    self.logger.info(
                        f"Retrying {context.operation} for {context.agent_arn} "
                        f"(attempt {attempt + 1}/{self.config.max_retries + 1}) "
                        f"after {delay:.2f}s delay"
                    )
                    await asyncio.sleep(delay)
                
                return await func()
                
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_retries:
                    self.logger.error(
                        f"All retry attempts exhausted for {context.operation} "
                        f"on {context.agent_arn}: {str(e)}"
                    )
                    break
                
                if not self._is_retryable_error(e):
                    self.logger.info(
                        f"Non-retryable error for {context.operation} "
                        f"on {context.agent_arn}: {str(e)}"
                    )
                    break
                
                self.logger.warning(
                    f"Retryable error for {context.operation} "
                    f"on {context.agent_arn} (attempt {attempt + 1}): {str(e)}"
                )
        
        # If we get here, all retries failed
        raise last_exception


class AgentCoreFallbackHandler:
    """Handles fallback responses when agents are unavailable."""
    
    def __init__(self):
        self.logger = logging.getLogger("fallback_handler")
        
        # Fallback responses for different operations
        self.fallback_responses = {
            "restaurant_search": {
                "message": "I can't search the restaurant database right now, but I can suggest some popular dining areas in Hong Kong.",
                "data": {
                    "restaurants": [],
                    "suggestions": [
                        {
                            "district": "Central district",
                            "description": "International restaurants and business dining",
                            "popular_cuisines": ["Western", "Japanese", "Chinese"]
                        },
                        {
                            "district": "Tsim Sha Tsui",
                            "description": "Harbor views with diverse dining options",
                            "popular_cuisines": ["Cantonese", "International", "Seafood"]
                        },
                        {
                            "district": "Causeway Bay",
                            "description": "Shopping and casual dining hub",
                            "popular_cuisines": ["Local", "Asian Fusion", "Fast Food"]
                        }
                    ]
                },
                "alternative_actions": [
                    "Ask me about tourist attractions in these areas",
                    "I can provide general dining tips for Hong Kong",
                    "Let me know what type of cuisine you're interested in"
                ]
            },
            "restaurant_reasoning": {
                "message": "I can't analyze restaurant recommendations right now, but I can share some general dining advice based on MBTI preferences.",
                "data": {
                    "recommendations": [],
                    "general_advice": {
                        "extroverted_types": "Look for lively restaurants with social atmospheres",
                        "introverted_types": "Consider quieter, more intimate dining settings",
                        "sensing_types": "Try restaurants known for traditional, authentic cuisine",
                        "intuitive_types": "Explore innovative or fusion restaurants",
                        "thinking_types": "Check reviews and ratings for quality assurance",
                        "feeling_types": "Choose restaurants with good service and ambiance",
                        "judging_types": "Make reservations at well-established restaurants",
                        "perceiving_types": "Be open to discovering new places spontaneously"
                    }
                },
                "alternative_actions": [
                    "Tell me your specific dining preferences",
                    "Ask about dining customs in Hong Kong",
                    "I can suggest areas known for specific cuisines"
                ]
            }
        }
    
    def create_fallback_response(self, operation: str, context: AgentCoreErrorContext,
                               partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a fallback response for when agents are unavailable."""
        
        # Determine operation type from context
        operation_type = self._classify_operation(operation, context)
        
        # Get fallback template
        fallback_template = self.fallback_responses.get(
            operation_type, 
            self._get_default_fallback()
        )
        
        # Build response
        response = {
            "success": False,
            "fallback": True,
            "agent_arn": context.agent_arn,
            "operation": operation,
            "message": fallback_template["message"],
            "data": fallback_template["data"].copy(),
            "alternative_actions": fallback_template["alternative_actions"].copy(),
            "timestamp": datetime.utcnow().isoformat(),
            "context": {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": context.request_id
            }
        }
        
        # Include partial data if available
        if partial_data:
            response["partial_data"] = partial_data
            response["message"] += " I do have some limited information that might help."
        
        self.logger.info(
            f"Created fallback response for {operation} on {context.agent_arn}"
        )
        
        return response
    
    def _classify_operation(self, operation: str, context: AgentCoreErrorContext) -> str:
        """Classify operation to determine appropriate fallback."""
        operation_lower = operation.lower()
        
        if "search" in operation_lower and "restaurant" in operation_lower:
            return "restaurant_search"
        elif "recommend" in operation_lower or "reasoning" in operation_lower:
            return "restaurant_reasoning"
        else:
            return "general"
    
    def _get_default_fallback(self) -> Dict[str, Any]:
        """Get default fallback response for unknown operations."""
        return {
            "message": "I'm having trouble with that request right now, but I'm here to help with your Hong Kong travel planning.",
            "data": {
                "suggestions": [
                    "Try asking about tourist attractions",
                    "I can provide general travel tips",
                    "Ask about transportation or accommodation"
                ]
            },
            "alternative_actions": [
                "Let me know what other travel information you need",
                "I can help with Hong Kong travel basics",
                "Ask about specific areas or activities you're interested in"
            ]
        }


class AgentCoreErrorHandler:
    """Comprehensive error handling system for AgentCore integration."""
    
    def __init__(self, retry_config: RetryConfig = None, 
                 circuit_breaker_config: CircuitBreakerConfig = None):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        
        self.retry_handler = RetryHandler(self.retry_config)
        self.fallback_handler = AgentCoreFallbackHandler()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        self.logger = logging.getLogger("agentcore_error_handler")
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for error handler."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_circuit_breaker(self, agent_arn: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent."""
        if agent_arn not in self.circuit_breakers:
            self.circuit_breakers[agent_arn] = CircuitBreaker(
                agent_arn, self.circuit_breaker_config
            )
        return self.circuit_breakers[agent_arn]
    
    async def execute_with_protection(self, func: Callable[[], Awaitable[Any]], 
                                    context: AgentCoreErrorContext) -> Any:
        """Execute function with full error protection (circuit breaker + retry)."""
        circuit_breaker = self._get_circuit_breaker(context.agent_arn)
        
        async def protected_call():
            return await circuit_breaker.call(func)
        
        try:
            return await self.retry_handler.execute_with_retry(protected_call, context)
        except Exception as e:
            self._log_error(e, context)
            raise
    
    def _log_error(self, error: Exception, context: AgentCoreErrorContext) -> None:
        """Log error with context information."""
        log_data = {
            "agent_arn": context.agent_arn,
            "operation": context.operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": context.timestamp.isoformat(),
            "user_id": context.user_id,
            "session_id": context.session_id,
            "request_id": context.request_id,
            "additional_data": context.additional_data
        }
        
        if isinstance(error, AgentCoreError):
            log_data.update({
                "error_category": error.error_type.value,
                "severity": error.severity.value,
                "retryable": error.retryable,
                "details": error.details
            })
            
            # Log with appropriate level
            if error.severity == ErrorSeverity.CRITICAL:
                self.logger.critical(f"Critical error in {context.operation}: {str(error)}", 
                                   extra={"error_data": log_data})
            elif error.severity == ErrorSeverity.HIGH:
                self.logger.error(f"High severity error in {context.operation}: {str(error)}", 
                                extra={"error_data": log_data})
            elif error.severity == ErrorSeverity.MEDIUM:
                self.logger.warning(f"Medium severity error in {context.operation}: {str(error)}", 
                                  extra={"error_data": log_data})
            else:
                self.logger.info(f"Low severity error in {context.operation}: {str(error)}", 
                               extra={"error_data": log_data})
        else:
            self.logger.error(f"Unexpected error in {context.operation}: {str(error)}", 
                            extra={"error_data": log_data})
    
    def create_fallback_response(self, operation: str, context: AgentCoreErrorContext,
                               partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create fallback response when agents are unavailable."""
        return self.fallback_handler.create_fallback_response(operation, context, partial_data)
    
    def get_circuit_breaker_stats(self, agent_arn: str = None) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        if agent_arn:
            if agent_arn in self.circuit_breakers:
                return self.circuit_breakers[agent_arn].get_stats()
            else:
                return {"agent_arn": agent_arn, "state": "not_initialized"}
        else:
            return {
                agent_arn: cb.get_stats() 
                for agent_arn, cb in self.circuit_breakers.items()
            }
    
    def reset_circuit_breaker(self, agent_arn: str) -> bool:
        """Reset circuit breaker for an agent."""
        if agent_arn in self.circuit_breakers:
            cb = self.circuit_breakers[agent_arn]
            cb.stats = CircuitBreakerStats()
            self.logger.info(f"Reset circuit breaker for {agent_arn}")
            return True
        return False
    
    def create_error_context(self, agent_arn: str, operation: str, **kwargs) -> AgentCoreErrorContext:
        """Create error context for AgentCore operations."""
        return AgentCoreErrorContext(
            agent_arn=agent_arn,
            operation=operation,
            input_text=kwargs.get("input_text"),
            session_id=kwargs.get("session_id"),
            user_id=kwargs.get("user_id"),
            request_id=kwargs.get("request_id"),
            additional_data=kwargs.get("additional_data", {})
        )


# Global error handler instance
_agentcore_error_handler = None


def get_agentcore_error_handler() -> AgentCoreErrorHandler:
    """Get the global AgentCore error handler instance."""
    global _agentcore_error_handler
    if _agentcore_error_handler is None:
        _agentcore_error_handler = AgentCoreErrorHandler()
    return _agentcore_error_handler


# Export main classes and functions
__all__ = [
    'AgentCoreErrorHandler',
    'AgentCoreErrorContext',
    'AgentCoreError',
    'AgentInvocationError',
    'AuthenticationError',
    'AgentTimeoutError',
    'AgentUnavailableError',
    'CircuitBreakerOpenError',
    'CircuitBreaker',
    'RetryHandler',
    'AgentCoreFallbackHandler',
    'RetryConfig',
    'CircuitBreakerConfig',
    'AgentCoreErrorType',
    'ErrorSeverity',
    'get_agentcore_error_handler'
]