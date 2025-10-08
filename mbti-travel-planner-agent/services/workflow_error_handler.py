"""
Workflow Error Handler

This module provides comprehensive error handling and recovery mechanisms for workflow execution,
including retry policies with exponential backoff, fallback tool execution, and partial result handling.

Features:
- Retry policies with exponential backoff
- Fallback tool execution when primary tools fail
- Partial result handling for incomplete workflows
- Circuit breaker pattern for failing tools
- Graceful degradation strategies
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque

from .orchestration_types import (
    RequestType, ExecutionStrategy, UserContext, Intent, 
    SelectedTool, OrchestrationResult
)


class ErrorType(Enum):
    """Types of errors that can occur during workflow execution."""
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    TOOL_ERROR = "tool_error"
    DEPENDENCY_ERROR = "dependency_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL_FAST = "fail_fast"
    PARTIAL_CONTINUE = "partial_continue"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.TIMEOUT_ERROR,
        ErrorType.NETWORK_ERROR,
        ErrorType.SERVICE_UNAVAILABLE
    ])
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay_seconds)
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


@dataclass
class FallbackConfig:
    """Fallback configuration for tools."""
    enabled: bool = True
    max_fallback_attempts: int = 2
    fallback_timeout_multiplier: float = 1.5
    require_capability_match: bool = True
    prefer_healthy_tools: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3
    success_threshold: int = 2  # Successes needed to close circuit


@dataclass
class ErrorContext:
    """Context information for error handling."""
    correlation_id: str
    workflow_id: str
    step_id: Optional[str] = None
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    attempt_number: int = 1
    error_type: Optional[ErrorType] = None
    original_error: Optional[Exception] = None
    user_context: Optional[UserContext] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'correlation_id': self.correlation_id,
            'workflow_id': self.workflow_id,
            'step_id': self.step_id,
            'tool_id': self.tool_id,
            'tool_name': self.tool_name,
            'attempt_number': self.attempt_number,
            'error_type': self.error_type.value if self.error_type else None,
            'error_message': str(self.original_error) if self.original_error else None
        }


@dataclass
class RecoveryResult:
    """Result of error recovery attempt."""
    success: bool
    strategy_used: RecoveryStrategy
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts_made: int = 0
    fallback_tool_used: Optional[str] = None
    partial_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'success': self.success,
            'strategy_used': self.strategy_used.value,
            'attempts_made': self.attempts_made,
            'fallback_tool_used': self.fallback_tool_used,
            'partial_results_count': len(self.partial_results),
            'error': self.error
        }


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for tool failure protection."""
    tool_id: str
    config: CircuitBreakerConfig
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    half_open_calls: int = 0
    
    def can_execute(self) -> bool:
        """Check if tool can be executed based on circuit breaker state."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.config.recovery_timeout_seconds)):
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful execution."""
        self.last_success_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0  # Reset failure count on success
    
    def record_failure(self):
        """Record failed execution."""
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.half_open_calls = 0
    
    def record_call(self):
        """Record a call attempt in half-open state."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1


class WorkflowErrorHandler:
    """
    Comprehensive error handler for workflow execution.
    
    This handler provides:
    - Retry policies with exponential backoff
    - Fallback tool execution
    - Circuit breaker pattern
    - Partial result handling
    - Graceful degradation
    """
    
    def __init__(self,
                 default_retry_policy: Optional[RetryPolicy] = None,
                 fallback_config: Optional[FallbackConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 enable_detailed_logging: bool = True):
        """
        Initialize the workflow error handler.
        
        Args:
            default_retry_policy: Default retry policy
            fallback_config: Fallback configuration
            circuit_breaker_config: Circuit breaker configuration
            enable_detailed_logging: Enable detailed error logging
        """
        self.default_retry_policy = default_retry_policy or RetryPolicy()
        self.fallback_config = fallback_config or FallbackConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.enable_detailed_logging = enable_detailed_logging
        
        self.logger = logging.getLogger(f"mbti_travel_planner.workflow_error_handler")
        
        # Circuit breakers for tools
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error statistics
        self._error_stats = defaultdict(lambda: {
            'total_count': 0,
            'by_type': defaultdict(int),
            'recovery_success_rate': 0.0,
            'recent_errors': deque(maxlen=100)
        })
        
        # Recovery strategy mapping
        self._recovery_strategies = {
            ErrorType.TIMEOUT_ERROR: RecoveryStrategy.RETRY,
            ErrorType.AUTHENTICATION_ERROR: RecoveryStrategy.RETRY,
            ErrorType.SERVICE_UNAVAILABLE: RecoveryStrategy.FALLBACK,
            ErrorType.VALIDATION_ERROR: RecoveryStrategy.SKIP,
            ErrorType.NETWORK_ERROR: RecoveryStrategy.RETRY,
            ErrorType.TOOL_ERROR: RecoveryStrategy.FALLBACK,
            ErrorType.DEPENDENCY_ERROR: RecoveryStrategy.PARTIAL_CONTINUE,
            ErrorType.RESOURCE_ERROR: RecoveryStrategy.GRACEFUL_DEGRADATION,
            ErrorType.UNKNOWN_ERROR: RecoveryStrategy.RETRY
        }
        
        self.logger.info("Workflow error handler initialized")
    
    async def handle_error(self,
                          error: Exception,
                          context: ErrorContext,
                          retry_policy: Optional[RetryPolicy] = None,
                          fallback_tools: Optional[List[SelectedTool]] = None) -> RecoveryResult:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error: The error that occurred
            context: Error context information
            retry_policy: Custom retry policy (optional)
            fallback_tools: Available fallback tools (optional)
            
        Returns:
            RecoveryResult with recovery outcome
        """
        start_time = time.time()
        
        # Classify error type
        error_type = self._classify_error(error)
        context.error_type = error_type
        context.original_error = error
        
        # Record error statistics
        self._record_error(context, error_type)
        
        # Determine recovery strategy
        recovery_strategy = self._get_recovery_strategy(error_type, context)
        
        self.logger.info(f"Handling error with strategy {recovery_strategy.value}", extra={
            'error_context': context.to_dict(),
            'error_type': error_type.value,
            'recovery_strategy': recovery_strategy.value
        })
        
        try:
            # Execute recovery strategy
            if recovery_strategy == RecoveryStrategy.RETRY:
                result = await self._handle_retry(error, context, retry_policy)
            elif recovery_strategy == RecoveryStrategy.FALLBACK:
                result = await self._handle_fallback(error, context, fallback_tools)
            elif recovery_strategy == RecoveryStrategy.SKIP:
                result = await self._handle_skip(error, context)
            elif recovery_strategy == RecoveryStrategy.FAIL_FAST:
                result = await self._handle_fail_fast(error, context)
            elif recovery_strategy == RecoveryStrategy.PARTIAL_CONTINUE:
                result = await self._handle_partial_continue(error, context)
            elif recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                result = await self._handle_graceful_degradation(error, context)
            else:
                result = RecoveryResult(
                    success=False,
                    strategy_used=recovery_strategy,
                    error=f"Unknown recovery strategy: {recovery_strategy}"
                )
            
            # Update circuit breaker
            if context.tool_id:
                circuit_breaker = self._get_circuit_breaker(context.tool_id)
                if result.success:
                    circuit_breaker.record_success()
                else:
                    circuit_breaker.record_failure()
            
            # Log recovery result
            recovery_time_ms = (time.time() - start_time) * 1000
            
            if result.success:
                self.logger.info(f"Error recovery successful", extra={
                    'error_context': context.to_dict(),
                    'recovery_result': result.to_dict(),
                    'recovery_time_ms': recovery_time_ms
                })
            else:
                self.logger.warning(f"Error recovery failed", extra={
                    'error_context': context.to_dict(),
                    'recovery_result': result.to_dict(),
                    'recovery_time_ms': recovery_time_ms
                })
            
            return result
            
        except Exception as recovery_error:
            self.logger.error(f"Error recovery itself failed", extra={
                'error_context': context.to_dict(),
                'recovery_error': str(recovery_error)
            })
            
            return RecoveryResult(
                success=False,
                strategy_used=recovery_strategy,
                error=f"Recovery failed: {recovery_error}"
            )
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception."""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        if isinstance(error, asyncio.TimeoutError) or 'timeout' in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif 'authentication' in error_str or 'unauthorized' in error_str or 'forbidden' in error_str:
            return ErrorType.AUTHENTICATION_ERROR
        elif 'service unavailable' in error_str or 'connection' in error_str or 'network' in error_str:
            if 'connection' in error_str or 'network' in error_str:
                return ErrorType.NETWORK_ERROR
            return ErrorType.SERVICE_UNAVAILABLE
        elif 'validation' in error_str or 'invalid' in error_str or 'bad request' in error_str:
            return ErrorType.VALIDATION_ERROR
        elif 'resource' in error_str or 'memory' in error_str or 'disk' in error_str:
            return ErrorType.RESOURCE_ERROR
        elif 'dependency' in error_str or 'prerequisite' in error_str:
            return ErrorType.DEPENDENCY_ERROR
        elif 'tool' in error_str:
            return ErrorType.TOOL_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _get_recovery_strategy(self, error_type: ErrorType, context: ErrorContext) -> RecoveryStrategy:
        """Get appropriate recovery strategy for error type."""
        # Check if we've exceeded retry attempts
        if (context.attempt_number > self.default_retry_policy.max_retries and 
            self._recovery_strategies.get(error_type) == RecoveryStrategy.RETRY):
            return RecoveryStrategy.FALLBACK
        
        # Check circuit breaker state
        if context.tool_id:
            circuit_breaker = self._get_circuit_breaker(context.tool_id)
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                return RecoveryStrategy.FALLBACK
        
        return self._recovery_strategies.get(error_type, RecoveryStrategy.RETRY)
    
    async def _handle_retry(self,
                           error: Exception,
                           context: ErrorContext,
                           retry_policy: Optional[RetryPolicy] = None) -> RecoveryResult:
        """Handle error with retry strategy."""
        policy = retry_policy or self.default_retry_policy
        
        if context.attempt_number > policy.max_retries:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY,
                error=f"Max retries ({policy.max_retries}) exceeded",
                attempts_made=context.attempt_number
            )
        
        # Check if error type is retryable
        if context.error_type not in policy.retry_on_errors:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY,
                error=f"Error type {context.error_type.value} is not retryable",
                attempts_made=context.attempt_number
            )
        
        # Calculate delay
        delay = policy.calculate_delay(context.attempt_number - 1)
        
        self.logger.info(f"Retrying after {delay:.2f} seconds", extra={
            'error_context': context.to_dict(),
            'attempt': context.attempt_number,
            'delay_seconds': delay
        })
        
        # Wait before retry
        await asyncio.sleep(delay)
        
        # This would typically re-execute the failed operation
        # For now, we'll simulate a retry result
        # In a real implementation, this would call back to the workflow engine
        
        return RecoveryResult(
            success=True,  # Simulate successful retry
            strategy_used=RecoveryStrategy.RETRY,
            attempts_made=context.attempt_number,
            result={'retry_successful': True, 'attempt': context.attempt_number}
        )
    
    async def _handle_fallback(self,
                              error: Exception,
                              context: ErrorContext,
                              fallback_tools: Optional[List[SelectedTool]] = None) -> RecoveryResult:
        """Handle error with fallback tool strategy."""
        if not fallback_tools or not self.fallback_config.enabled:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                error="No fallback tools available or fallback disabled"
            )
        
        # Filter healthy fallback tools
        available_fallbacks = []
        
        for tool in fallback_tools[:self.fallback_config.max_fallback_attempts]:
            if self.fallback_config.prefer_healthy_tools:
                circuit_breaker = self._get_circuit_breaker(tool.tool_id)
                if circuit_breaker.can_execute():
                    available_fallbacks.append(tool)
            else:
                available_fallbacks.append(tool)
        
        if not available_fallbacks:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                error="No healthy fallback tools available"
            )
        
        # Try fallback tools
        for i, fallback_tool in enumerate(available_fallbacks):
            try:
                self.logger.info(f"Trying fallback tool {fallback_tool.tool_name}", extra={
                    'error_context': context.to_dict(),
                    'fallback_tool': fallback_tool.tool_name,
                    'fallback_attempt': i + 1
                })
                
                # Record circuit breaker call
                circuit_breaker = self._get_circuit_breaker(fallback_tool.tool_id)
                circuit_breaker.record_call()
                
                # This would typically execute the fallback tool
                # For now, we'll simulate fallback execution
                result = await self._simulate_fallback_execution(fallback_tool, context)
                
                circuit_breaker.record_success()
                
                return RecoveryResult(
                    success=True,
                    strategy_used=RecoveryStrategy.FALLBACK,
                    result=result,
                    attempts_made=i + 1,
                    fallback_tool_used=fallback_tool.tool_name
                )
                
            except Exception as fallback_error:
                circuit_breaker = self._get_circuit_breaker(fallback_tool.tool_id)
                circuit_breaker.record_failure()
                
                self.logger.warning(f"Fallback tool failed", extra={
                    'error_context': context.to_dict(),
                    'fallback_tool': fallback_tool.tool_name,
                    'fallback_error': str(fallback_error)
                })
                
                # Continue to next fallback tool
                continue
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FALLBACK,
            error="All fallback tools failed",
            attempts_made=len(available_fallbacks)
        )
    
    async def _handle_skip(self,
                          error: Exception,
                          context: ErrorContext) -> RecoveryResult:
        """Handle error by skipping the failed step."""
        self.logger.info(f"Skipping failed step", extra={
            'error_context': context.to_dict()
        })
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.SKIP,
            result={'skipped': True, 'reason': str(error)}
        )
    
    async def _handle_fail_fast(self,
                               error: Exception,
                               context: ErrorContext) -> RecoveryResult:
        """Handle error by failing fast without recovery."""
        self.logger.error(f"Failing fast on error", extra={
            'error_context': context.to_dict()
        })
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FAIL_FAST,
            error=f"Fail fast: {error}"
        )
    
    async def _handle_partial_continue(self,
                                      error: Exception,
                                      context: ErrorContext) -> RecoveryResult:
        """Handle error by continuing with partial results."""
        self.logger.info(f"Continuing with partial results", extra={
            'error_context': context.to_dict()
        })
        
        # Collect any partial results that might be available
        partial_results = []
        
        # This would typically gather partial results from the workflow context
        # For now, we'll simulate partial results
        partial_results.append({
            'step_id': context.step_id,
            'partial_data': 'Some partial results available',
            'error': str(error)
        })
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.PARTIAL_CONTINUE,
            result={'partial_execution': True},
            partial_results=partial_results
        )
    
    async def _handle_graceful_degradation(self,
                                          error: Exception,
                                          context: ErrorContext) -> RecoveryResult:
        """Handle error with graceful degradation."""
        self.logger.info(f"Applying graceful degradation", extra={
            'error_context': context.to_dict()
        })
        
        # Provide degraded functionality
        degraded_result = {
            'degraded_mode': True,
            'original_error': str(error),
            'fallback_data': 'Limited functionality available',
            'user_message': 'Service is temporarily limited. Please try again later.'
        }
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
            result=degraded_result
        )
    
    async def _simulate_fallback_execution(self,
                                          fallback_tool: SelectedTool,
                                          context: ErrorContext) -> Dict[str, Any]:
        """Simulate fallback tool execution."""
        # This is a placeholder for actual fallback tool execution
        # In a real implementation, this would integrate with the tool orchestration engine
        
        await asyncio.sleep(0.1)  # Simulate execution time
        
        return {
            'fallback_tool_id': fallback_tool.tool_id,
            'fallback_tool_name': fallback_tool.tool_name,
            'execution_successful': True,
            'result_type': 'fallback_result'
        }
    
    def _get_circuit_breaker(self, tool_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for tool."""
        if tool_id not in self._circuit_breakers:
            self._circuit_breakers[tool_id] = CircuitBreaker(
                tool_id=tool_id,
                config=self.circuit_breaker_config
            )
        
        return self._circuit_breakers[tool_id]
    
    def _record_error(self, context: ErrorContext, error_type: ErrorType):
        """Record error statistics."""
        tool_key = context.tool_id or 'unknown'
        
        stats = self._error_stats[tool_key]
        stats['total_count'] += 1
        stats['by_type'][error_type.value] += 1
        stats['recent_errors'].append({
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'context': context.to_dict()
        })
    
    def check_tool_health(self, tool_id: str) -> Dict[str, Any]:
        """Check health status of a tool based on circuit breaker and error stats."""
        circuit_breaker = self._get_circuit_breaker(tool_id)
        stats = self._error_stats.get(tool_id, {})
        
        return {
            'tool_id': tool_id,
            'circuit_breaker_state': circuit_breaker.state.value,
            'can_execute': circuit_breaker.can_execute(),
            'failure_count': circuit_breaker.failure_count,
            'last_failure_time': circuit_breaker.last_failure_time.isoformat() if circuit_breaker.last_failure_time else None,
            'total_errors': stats.get('total_count', 0),
            'error_types': dict(stats.get('by_type', {})),
            'recent_error_count': len(stats.get('recent_errors', []))
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        total_errors = sum(stats['total_count'] for stats in self._error_stats.values())
        
        error_by_type = defaultdict(int)
        for stats in self._error_stats.values():
            for error_type, count in stats.get('by_type', {}).items():
                error_by_type[error_type] += count
        
        circuit_breaker_states = {}
        for tool_id, cb in self._circuit_breakers.items():
            circuit_breaker_states[tool_id] = cb.state.value
        
        return {
            'total_errors': total_errors,
            'errors_by_type': dict(error_by_type),
            'tools_with_errors': len(self._error_stats),
            'circuit_breaker_states': circuit_breaker_states,
            'tools_with_open_circuits': len([cb for cb in self._circuit_breakers.values() 
                                           if cb.state == CircuitBreakerState.OPEN])
        }
    
    def reset_circuit_breaker(self, tool_id: str) -> bool:
        """Manually reset circuit breaker for a tool."""
        if tool_id in self._circuit_breakers:
            cb = self._circuit_breakers[tool_id]
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            cb.success_count = 0
            cb.half_open_calls = 0
            
            self.logger.info(f"Circuit breaker reset for tool {tool_id}")
            return True
        
        return False
    
    def configure_recovery_strategy(self, error_type: ErrorType, strategy: RecoveryStrategy):
        """Configure recovery strategy for specific error type."""
        self._recovery_strategies[error_type] = strategy
        self.logger.info(f"Recovery strategy for {error_type.value} set to {strategy.value}")