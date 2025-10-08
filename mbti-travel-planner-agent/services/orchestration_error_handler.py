"""
Orchestration Error Handler

This module provides structured error handling specifically for the tool orchestration system,
including typed error classification, recovery strategies, and graceful degradation mechanisms.

Features:
- Typed error classification for orchestration-specific errors
- Recovery strategies for different failure types
- Graceful degradation for partial system failures
- Integration with AgentCore monitoring and logging
- Circuit breaker pattern for tool failures
- Fallback mechanisms for tool unavailability
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable, Awaitable, TYPE_CHECKING
from dataclasses import dataclass, field
import json
import traceback
from collections import defaultdict, deque

# Import existing error handling components
from .error_handler import (
    ErrorHandler, ErrorContext, ErrorResponse, ErrorSeverity, ErrorCategory,
    GatewayError, get_error_handler
)
from .agentcore_error_handler import (
    AgentCoreErrorHandler, AgentCoreError, AgentCoreErrorType,
    CircuitBreaker, CircuitBreakerConfig, RetryConfig,
    get_agentcore_error_handler
)

# Import orchestration types
from .orchestration_types import (
    RequestType, ExecutionStrategy, UserContext, Intent, 
    SelectedTool, OrchestrationResult
)

if TYPE_CHECKING:
    from .agentcore_monitoring_service import AgentCoreMonitoringService


class OrchestrationErrorType(Enum):
    """Types of orchestration-specific errors."""
    INTENT_ANALYSIS_FAILED = "intent_analysis_failed"
    TOOL_SELECTION_FAILED = "tool_selection_failed"
    WORKFLOW_EXECUTION_FAILED = "workflow_execution_failed"
    TOOL_INVOCATION_FAILED = "tool_invocation_failed"
    PARTIAL_WORKFLOW_FAILURE = "partial_workflow_failure"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_TOOL = "fallback_tool"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"
    PARTIAL_RESULTS = "partial_results"
    USER_NOTIFICATION = "user_notification"
    NO_RECOVERY = "no_recovery"


@dataclass
class OrchestrationErrorContext:
    """Context information for orchestration errors."""
    operation: str
    correlation_id: str
    intent: Optional[Intent] = None
    selected_tools: Optional[List[SelectedTool]] = None
    user_context: Optional[UserContext] = None
    workflow_step: Optional[str] = None
    tool_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Represents a recovery action to be taken."""
    strategy: RecoveryStrategy
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Lower number = higher priority
    estimated_success_rate: float = 0.5
    execution_time_estimate_ms: float = 1000.0


@dataclass
class OrchestrationErrorResult:
    """Result of error handling with recovery actions."""
    success: bool
    error_type: OrchestrationErrorType
    error_message: str
    user_message: str
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    fallback_response: Optional[Dict[str, Any]] = None
    partial_results: Optional[List[Dict[str, Any]]] = None
    retry_after_seconds: Optional[int] = None
    support_reference: str = ""
    correlation_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class OrchestrationError(Exception):
    """Base exception for orchestration errors."""
    
    def __init__(self, 
                 message: str,
                 error_type: OrchestrationErrorType = OrchestrationErrorType.UNKNOWN_ERROR,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[OrchestrationErrorContext] = None,
                 recovery_strategies: Optional[List[RecoveryStrategy]] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_type = error_type
        self.severity = severity
        self.context = context
        self.recovery_strategies = recovery_strategies or []
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class IntentAnalysisError(OrchestrationError):
    """Error during intent analysis phase."""
    
    def __init__(self, message: str, request_text: str = None, **kwargs):
        self.request_text = request_text
        super().__init__(
            message=message,
            error_type=OrchestrationErrorType.INTENT_ANALYSIS_FAILED,
            recovery_strategies=[RecoveryStrategy.GRACEFUL_DEGRADATION, RecoveryStrategy.USER_NOTIFICATION],
            **kwargs
        )


class ToolSelectionError(OrchestrationError):
    """Error during tool selection phase."""
    
    def __init__(self, message: str, intent: Intent = None, available_tools: List[str] = None, **kwargs):
        self.intent = intent
        self.available_tools = available_tools or []
        super().__init__(
            message=message,
            error_type=OrchestrationErrorType.TOOL_SELECTION_FAILED,
            recovery_strategies=[RecoveryStrategy.FALLBACK_TOOL, RecoveryStrategy.GRACEFUL_DEGRADATION],
            **kwargs
        )


class WorkflowExecutionError(OrchestrationError):
    """Error during workflow execution."""
    
    def __init__(self, message: str, workflow_step: str = None, partial_results: List[Dict] = None, **kwargs):
        self.workflow_step = workflow_step
        self.partial_results = partial_results or []
        super().__init__(
            message=message,
            error_type=OrchestrationErrorType.WORKFLOW_EXECUTION_FAILED,
            recovery_strategies=[RecoveryStrategy.PARTIAL_RESULTS, RecoveryStrategy.RETRY_WITH_BACKOFF],
            **kwargs
        )


class ToolInvocationError(OrchestrationError):
    """Error during tool invocation."""
    
    def __init__(self, message: str, tool_id: str = None, tool_name: str = None, **kwargs):
        self.tool_id = tool_id
        self.tool_name = tool_name
        super().__init__(
            message=message,
            error_type=OrchestrationErrorType.TOOL_INVOCATION_FAILED,
            recovery_strategies=[RecoveryStrategy.FALLBACK_TOOL, RecoveryStrategy.CIRCUIT_BREAKER],
            **kwargs
        )


class PartialWorkflowFailure(OrchestrationError):
    """Partial failure in workflow execution."""
    
    def __init__(self, message: str, successful_results: List[Dict] = None, failed_tools: List[str] = None, **kwargs):
        self.successful_results = successful_results or []
        self.failed_tools = failed_tools or []
        super().__init__(
            message=message,
            error_type=OrchestrationErrorType.PARTIAL_WORKFLOW_FAILURE,
            recovery_strategies=[RecoveryStrategy.PARTIAL_RESULTS, RecoveryStrategy.FALLBACK_TOOL],
            **kwargs
        )


class OrchestrationErrorHandler:
    """
    Comprehensive error handling system for tool orchestration.
    
    Provides structured error classification, recovery strategies, and graceful degradation
    for orchestration-specific failures.
    """
    
    def __init__(self, 
                 monitoring_service: Optional['AgentCoreMonitoringService'] = None,
                 enable_circuit_breaker: bool = True,
                 enable_retry_logic: bool = True):
        """
        Initialize the orchestration error handler.
        
        Args:
            monitoring_service: AgentCore monitoring service for logging
            enable_circuit_breaker: Enable circuit breaker pattern
            enable_retry_logic: Enable retry logic for recoverable errors
        """
        self.logger = logging.getLogger("orchestration_error_handler")
        self.monitoring_service = monitoring_service
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_retry_logic = enable_retry_logic
        
        # Get existing error handlers
        self.base_error_handler = get_error_handler()
        self.agentcore_error_handler = get_agentcore_error_handler()
        
        # Circuit breaker configuration
        self.circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            half_open_max_calls=3,
            success_threshold=2
        )
        
        # Retry configuration
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Circuit breakers for tools
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error statistics
        self._error_stats = defaultdict(lambda: {
            'count': 0,
            'last_occurrence': None,
            'recovery_success_rate': 0.0
        })
        
        # Recovery strategy effectiveness tracking
        self._recovery_stats = defaultdict(lambda: {
            'attempts': 0,
            'successes': 0,
            'avg_execution_time_ms': 0.0
        })
        
        self._setup_logging()
        self.logger.info("Orchestration error handler initialized")
    
    def _setup_logging(self) -> None:
        """Configure logging for the error handler."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_circuit_breaker(self, tool_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for a tool."""
        if tool_id not in self._circuit_breakers:
            self._circuit_breakers[tool_id] = CircuitBreaker(
                tool_id, self.circuit_breaker_config
            )
        return self._circuit_breakers[tool_id]
    
    def _generate_support_reference(self, context: OrchestrationErrorContext) -> str:
        """Generate unique support reference for error tracking."""
        timestamp = context.timestamp.strftime("%Y%m%d_%H%M%S")
        operation = context.operation.replace(" ", "_").lower()
        correlation_id = context.correlation_id[-8:] if context.correlation_id else "unknown"
        return f"ORCH_{operation}_{correlation_id}_{timestamp}"
    
    def _classify_error(self, error: Exception, context: OrchestrationErrorContext) -> OrchestrationErrorType:
        """Classify an error into orchestration error types."""
        if isinstance(error, OrchestrationError):
            return error.error_type
        
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Classification based on error patterns
        if any(keyword in error_str for keyword in ['intent', 'analysis', 'parsing']):
            return OrchestrationErrorType.INTENT_ANALYSIS_FAILED
        
        if any(keyword in error_str for keyword in ['tool', 'selection', 'capability']):
            return OrchestrationErrorType.TOOL_SELECTION_FAILED
        
        if any(keyword in error_str for keyword in ['workflow', 'execution', 'step']):
            return OrchestrationErrorType.WORKFLOW_EXECUTION_FAILED
        
        if any(keyword in error_str for keyword in ['invocation', 'call', 'invoke']):
            return OrchestrationErrorType.TOOL_INVOCATION_FAILED
        
        if any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return OrchestrationErrorType.TIMEOUT_ERROR
        
        if any(keyword in error_str for keyword in ['validation', 'invalid', 'format']):
            return OrchestrationErrorType.VALIDATION_ERROR
        
        if any(keyword in error_str for keyword in ['config', 'configuration']):
            return OrchestrationErrorType.CONFIGURATION_ERROR
        
        if any(keyword in error_str for keyword in ['resource', 'memory', 'limit']):
            return OrchestrationErrorType.RESOURCE_EXHAUSTION
        
        if any(keyword in error_str for keyword in ['unavailable', 'unreachable', 'connection']):
            return OrchestrationErrorType.DEPENDENCY_UNAVAILABLE
        
        return OrchestrationErrorType.UNKNOWN_ERROR
    
    def _determine_severity(self, error_type: OrchestrationErrorType, context: OrchestrationErrorContext) -> ErrorSeverity:
        """Determine error severity based on type and context."""
        severity_mapping = {
            OrchestrationErrorType.INTENT_ANALYSIS_FAILED: ErrorSeverity.MEDIUM,
            OrchestrationErrorType.TOOL_SELECTION_FAILED: ErrorSeverity.HIGH,
            OrchestrationErrorType.WORKFLOW_EXECUTION_FAILED: ErrorSeverity.HIGH,
            OrchestrationErrorType.TOOL_INVOCATION_FAILED: ErrorSeverity.MEDIUM,
            OrchestrationErrorType.PARTIAL_WORKFLOW_FAILURE: ErrorSeverity.MEDIUM,
            OrchestrationErrorType.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            OrchestrationErrorType.RESOURCE_EXHAUSTION: ErrorSeverity.CRITICAL,
            OrchestrationErrorType.DEPENDENCY_UNAVAILABLE: ErrorSeverity.HIGH,
            OrchestrationErrorType.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            OrchestrationErrorType.VALIDATION_ERROR: ErrorSeverity.LOW,
            OrchestrationErrorType.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        
        base_severity = severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
        
        # Adjust severity based on context
        if context.selected_tools and len(context.selected_tools) == 1:
            # Single tool failure is more severe
            if base_severity == ErrorSeverity.MEDIUM:
                base_severity = ErrorSeverity.HIGH
        
        if context.user_context and context.user_context.session_id:
            # User session context makes errors more critical
            if base_severity == ErrorSeverity.LOW:
                base_severity = ErrorSeverity.MEDIUM
        
        return base_severity
    
    def _generate_recovery_actions(self, 
                                 error_type: OrchestrationErrorType,
                                 context: OrchestrationErrorContext,
                                 error: Exception) -> List[RecoveryAction]:
        """Generate appropriate recovery actions for the error."""
        actions = []
        
        if error_type == OrchestrationErrorType.INTENT_ANALYSIS_FAILED:
            actions.extend([
                RecoveryAction(
                    strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    description="Use default search parameters and provide general recommendations",
                    parameters={'use_defaults': True},
                    priority=1,
                    estimated_success_rate=0.8,
                    execution_time_estimate_ms=500.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.USER_NOTIFICATION,
                    description="Ask user to rephrase their request",
                    parameters={'suggest_rephrase': True},
                    priority=2,
                    estimated_success_rate=0.9,
                    execution_time_estimate_ms=100.0
                )
            ])
        
        elif error_type == OrchestrationErrorType.TOOL_SELECTION_FAILED:
            actions.extend([
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK_TOOL,
                    description="Use alternative tools with similar capabilities",
                    parameters={'use_fallback': True},
                    priority=1,
                    estimated_success_rate=0.7,
                    execution_time_estimate_ms=2000.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    description="Provide cached or default responses",
                    parameters={'use_cache': True},
                    priority=2,
                    estimated_success_rate=0.6,
                    execution_time_estimate_ms=300.0
                )
            ])
        
        elif error_type == OrchestrationErrorType.TOOL_INVOCATION_FAILED:
            if self.enable_circuit_breaker and context.tool_id:
                actions.append(
                    RecoveryAction(
                        strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                        description="Activate circuit breaker to prevent cascade failures",
                        parameters={'tool_id': context.tool_id},
                        priority=1,
                        estimated_success_rate=0.9,
                        execution_time_estimate_ms=50.0
                    )
                )
            
            if self.enable_retry_logic:
                actions.append(
                    RecoveryAction(
                        strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                        description="Retry tool invocation with exponential backoff",
                        parameters={'max_retries': self.retry_config.max_retries},
                        priority=2,
                        estimated_success_rate=0.6,
                        execution_time_estimate_ms=5000.0
                    )
                )
            
            actions.append(
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK_TOOL,
                    description="Use alternative tool for the same operation",
                    parameters={'find_alternative': True},
                    priority=3,
                    estimated_success_rate=0.5,
                    execution_time_estimate_ms=3000.0
                )
            )
        
        elif error_type == OrchestrationErrorType.PARTIAL_WORKFLOW_FAILURE:
            actions.extend([
                RecoveryAction(
                    strategy=RecoveryStrategy.PARTIAL_RESULTS,
                    description="Return successful results with failure notification",
                    parameters={'include_partial': True},
                    priority=1,
                    estimated_success_rate=0.9,
                    execution_time_estimate_ms=200.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK_TOOL,
                    description="Retry failed steps with alternative tools",
                    parameters={'retry_failed_only': True},
                    priority=2,
                    estimated_success_rate=0.6,
                    execution_time_estimate_ms=4000.0
                )
            ])
        
        elif error_type == OrchestrationErrorType.TIMEOUT_ERROR:
            actions.extend([
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    description="Retry with increased timeout",
                    parameters={'increase_timeout': True},
                    priority=1,
                    estimated_success_rate=0.7,
                    execution_time_estimate_ms=10000.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    description="Provide cached or simplified response",
                    parameters={'use_cache': True, 'simplify': True},
                    priority=2,
                    estimated_success_rate=0.8,
                    execution_time_estimate_ms=500.0
                )
            ])
        
        elif error_type == OrchestrationErrorType.DEPENDENCY_UNAVAILABLE:
            actions.extend([
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK_TOOL,
                    description="Use alternative service or tool",
                    parameters={'use_alternative_service': True},
                    priority=1,
                    estimated_success_rate=0.6,
                    execution_time_estimate_ms=3000.0
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    description="Provide offline or cached responses",
                    parameters={'offline_mode': True},
                    priority=2,
                    estimated_success_rate=0.7,
                    execution_time_estimate_ms=400.0
                )
            ])
        
        # Default recovery action
        if not actions:
            actions.append(
                RecoveryAction(
                    strategy=RecoveryStrategy.USER_NOTIFICATION,
                    description="Notify user of the issue and suggest alternatives",
                    parameters={'provide_alternatives': True},
                    priority=1,
                    estimated_success_rate=0.9,
                    execution_time_estimate_ms=100.0
                )
            )
        
        # Sort by priority
        actions.sort(key=lambda a: a.priority)
        return actions
    
    def _create_user_message(self, error_type: OrchestrationErrorType, context: OrchestrationErrorContext) -> str:
        """Create user-friendly error message."""
        user_messages = {
            OrchestrationErrorType.INTENT_ANALYSIS_FAILED: 
                "I'm having trouble understanding your request. Could you please rephrase it or be more specific about what you're looking for?",
            
            OrchestrationErrorType.TOOL_SELECTION_FAILED:
                "I'm having difficulty finding the right tools to help with your request. Let me try a different approach.",
            
            OrchestrationErrorType.WORKFLOW_EXECUTION_FAILED:
                "I encountered an issue while processing your request. Let me try to get you some information using an alternative method.",
            
            OrchestrationErrorType.TOOL_INVOCATION_FAILED:
                "One of my tools isn't responding properly right now. I'll try using a different approach to help you.",
            
            OrchestrationErrorType.PARTIAL_WORKFLOW_FAILURE:
                "I was able to get some information for you, but encountered issues getting the complete results. Here's what I found:",
            
            OrchestrationErrorType.TIMEOUT_ERROR:
                "Your request is taking longer than expected to process. Let me try a faster approach or provide you with some general information.",
            
            OrchestrationErrorType.DEPENDENCY_UNAVAILABLE:
                "Some of my services are temporarily unavailable. I can still help you with general information and suggestions.",
            
            OrchestrationErrorType.CONFIGURATION_ERROR:
                "I'm experiencing a configuration issue. Let me try to help you with the information I have available.",
            
            OrchestrationErrorType.RESOURCE_EXHAUSTION:
                "I'm currently handling a high volume of requests. Please try again in a moment, or I can provide some general recommendations now.",
            
            OrchestrationErrorType.VALIDATION_ERROR:
                "There seems to be an issue with the format of your request. Could you please try rephrasing it?",
            
            OrchestrationErrorType.UNKNOWN_ERROR:
                "I encountered an unexpected issue while processing your request. Let me try to help you in a different way."
        }
        
        return user_messages.get(error_type, user_messages[OrchestrationErrorType.UNKNOWN_ERROR])
    
    def _create_fallback_response(self, 
                                error_type: OrchestrationErrorType,
                                context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Create fallback response when normal processing fails."""
        fallback_responses = {
            OrchestrationErrorType.INTENT_ANALYSIS_FAILED: {
                "message": "I can help you with restaurant searches and recommendations in Hong Kong.",
                "suggestions": [
                    "Try asking: 'Find restaurants in Central district'",
                    "Or: 'Recommend good lunch places'",
                    "Or: 'Show me restaurants for dinner in Tsim Sha Tsui'"
                ],
                "available_actions": [
                    "Search restaurants by district",
                    "Search restaurants by meal type",
                    "Get restaurant recommendations"
                ]
            },
            
            OrchestrationErrorType.TOOL_SELECTION_FAILED: {
                "message": "I'm having trouble with my restaurant search tools, but I can provide some general recommendations.",
                "suggestions": [
                    "Central district: Great for business dining and international cuisine",
                    "Tsim Sha Tsui: Harbor views with diverse dining options",
                    "Causeway Bay: Popular for casual dining and local food"
                ],
                "available_actions": [
                    "Ask about specific districts",
                    "Request general dining tips",
                    "Get information about Hong Kong food culture"
                ]
            },
            
            OrchestrationErrorType.PARTIAL_WORKFLOW_FAILURE: {
                "message": "I was able to get some results, but not everything you requested.",
                "partial_data": context.additional_data.get('partial_results', []),
                "suggestions": [
                    "Try asking for more specific information",
                    "Ask about a particular district or cuisine type",
                    "Request general recommendations instead"
                ]
            }
        }
        
        default_response = {
            "message": "I'm experiencing some technical difficulties, but I'm here to help with your Hong Kong travel planning.",
            "suggestions": [
                "Ask me about popular dining districts",
                "Request general restaurant recommendations",
                "Get information about Hong Kong food culture"
            ],
            "available_actions": [
                "General travel advice",
                "District information",
                "Cuisine recommendations"
            ]
        }
        
        response = fallback_responses.get(error_type, default_response)
        
        # Add context-specific information
        response.update({
            "fallback": True,
            "error_type": error_type.value,
            "correlation_id": context.correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return response
    
    def _log_error(self, 
                  error: Exception,
                  context: OrchestrationErrorContext,
                  error_type: OrchestrationErrorType,
                  severity: ErrorSeverity) -> None:
        """Log error with comprehensive context information."""
        log_data = {
            "operation": context.operation,
            "correlation_id": context.correlation_id,
            "error_type": error_type.value,
            "error_message": str(error),
            "severity": severity.value,
            "timestamp": context.timestamp.isoformat(),
            "execution_time_ms": context.execution_time_ms,
            "workflow_step": context.workflow_step,
            "tool_id": context.tool_id,
            "additional_data": context.additional_data
        }
        
        # Add context information
        if context.intent:
            log_data["intent"] = {
                "type": context.intent.type.value,
                "confidence": context.intent.confidence,
                "parameters": context.intent.parameters
            }
        
        if context.selected_tools:
            log_data["selected_tools"] = [
                {"tool_id": tool.tool_id, "tool_name": tool.tool_name, "confidence": tool.confidence}
                for tool in context.selected_tools
            ]
        
        if context.user_context:
            log_data["user_context"] = {
                "user_id": context.user_context.user_id,
                "session_id": context.user_context.session_id,
                "has_mbti_type": context.user_context.mbti_type is not None
            }
        
        # Add stack trace for high severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log_data["stack_trace"] = traceback.format_exc()
        
        # Log with appropriate level
        log_message = f"Orchestration error in {context.operation}: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra={"error_data": log_data})
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra={"error_data": log_data})
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra={"error_data": log_data})
        else:  # LOW
            self.logger.info(log_message, extra={"error_data": log_data})
        
        # Log to monitoring service if available
        if self.monitoring_service:
            try:
                self.monitoring_service.log_error(
                    error=error,
                    context=log_data,
                    correlation_id=context.correlation_id
                )
            except Exception as e:
                self.logger.warning(f"Failed to log to monitoring service: {e}")
    
    def _update_error_statistics(self, error_type: OrchestrationErrorType) -> None:
        """Update error statistics for monitoring and analysis."""
        stats = self._error_stats[error_type.value]
        stats['count'] += 1
        stats['last_occurrence'] = datetime.utcnow()
    
    def _update_recovery_statistics(self, strategy: RecoveryStrategy, success: bool, execution_time_ms: float) -> None:
        """Update recovery strategy effectiveness statistics."""
        stats = self._recovery_stats[strategy.value]
        stats['attempts'] += 1
        
        if success:
            stats['successes'] += 1
        
        # Update average execution time
        current_avg = stats['avg_execution_time_ms']
        attempts = stats['attempts']
        stats['avg_execution_time_ms'] = ((current_avg * (attempts - 1)) + execution_time_ms) / attempts
    
    async def handle_error(self, 
                          error: Exception,
                          context: OrchestrationErrorContext) -> OrchestrationErrorResult:
        """
        Handle orchestration error with comprehensive recovery strategies.
        
        Args:
            error: The exception that occurred
            context: Orchestration error context
            
        Returns:
            OrchestrationErrorResult with recovery actions and fallback response
        """
        start_time = time.time()
        
        # Classify error
        error_type = self._classify_error(error, context)
        severity = self._determine_severity(error_type, context)
        
        # Log error
        self._log_error(error, context, error_type, severity)
        
        # Update statistics
        self._update_error_statistics(error_type)
        
        # Generate support reference
        support_reference = self._generate_support_reference(context)
        
        # Generate recovery actions
        recovery_actions = self._generate_recovery_actions(error_type, context, error)
        
        # Create user message
        user_message = self._create_user_message(error_type, context)
        
        # Create fallback response
        fallback_response = self._create_fallback_response(error_type, context)
        
        # Extract partial results if available
        partial_results = None
        if isinstance(error, PartialWorkflowFailure):
            partial_results = error.successful_results
        elif context.additional_data.get('partial_results'):
            partial_results = context.additional_data['partial_results']
        
        # Determine retry timing
        retry_after_seconds = None
        if error_type in [OrchestrationErrorType.RESOURCE_EXHAUSTION, OrchestrationErrorType.TIMEOUT_ERROR]:
            retry_after_seconds = 30
        elif error_type == OrchestrationErrorType.DEPENDENCY_UNAVAILABLE:
            retry_after_seconds = 60
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        result = OrchestrationErrorResult(
            success=False,
            error_type=error_type,
            error_message=str(error),
            user_message=user_message,
            recovery_actions=recovery_actions,
            fallback_response=fallback_response,
            partial_results=partial_results,
            retry_after_seconds=retry_after_seconds,
            support_reference=support_reference,
            correlation_id=context.correlation_id,
            details={
                "severity": severity.value,
                "error_classification": error_type.value,
                "context_operation": context.operation,
                "execution_time_ms": execution_time_ms,
                "recovery_actions_count": len(recovery_actions)
            }
        )
        
        self.logger.info(f"Error handling completed", extra={
            "correlation_id": context.correlation_id,
            "error_type": error_type.value,
            "recovery_actions": len(recovery_actions),
            "has_partial_results": partial_results is not None,
            "execution_time_ms": execution_time_ms
        })
        
        return result
    
    async def execute_recovery_action(self, 
                                    action: RecoveryAction,
                                    context: OrchestrationErrorContext) -> Dict[str, Any]:
        """
        Execute a specific recovery action.
        
        Args:
            action: Recovery action to execute
            context: Error context
            
        Returns:
            Result of recovery action execution
        """
        start_time = time.time()
        
        self.logger.info(f"Executing recovery action: {action.strategy.value}", extra={
            "correlation_id": context.correlation_id,
            "strategy": action.strategy.value,
            "description": action.description
        })
        
        try:
            if action.strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._execute_circuit_breaker_action(action, context)
            
            elif action.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                return await self._execute_retry_action(action, context)
            
            elif action.strategy == RecoveryStrategy.FALLBACK_TOOL:
                return await self._execute_fallback_tool_action(action, context)
            
            elif action.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return await self._execute_graceful_degradation_action(action, context)
            
            elif action.strategy == RecoveryStrategy.PARTIAL_RESULTS:
                return await self._execute_partial_results_action(action, context)
            
            elif action.strategy == RecoveryStrategy.USER_NOTIFICATION:
                return await self._execute_user_notification_action(action, context)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown recovery strategy: {action.strategy.value}"
                }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._update_recovery_statistics(action.strategy, False, execution_time_ms)
            
            self.logger.error(f"Recovery action failed: {action.strategy.value}", extra={
                "correlation_id": context.correlation_id,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            })
            
            return {
                "success": False,
                "message": f"Recovery action failed: {str(e)}",
                "execution_time_ms": execution_time_ms
            }
        
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
    
    async def _execute_circuit_breaker_action(self, 
                                            action: RecoveryAction,
                                            context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute circuit breaker recovery action."""
        tool_id = action.parameters.get('tool_id') or context.tool_id
        
        if not tool_id:
            return {"success": False, "message": "No tool ID provided for circuit breaker"}
        
        circuit_breaker = self._get_circuit_breaker(tool_id)
        
        # The circuit breaker is automatically updated when errors occur
        # This action just confirms the circuit breaker state
        stats = circuit_breaker.get_stats()
        
        return {
            "success": True,
            "message": f"Circuit breaker activated for tool {tool_id}",
            "circuit_breaker_state": stats['state'],
            "failure_count": stats['failure_count']
        }
    
    async def _execute_retry_action(self, 
                                  action: RecoveryAction,
                                  context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute retry with backoff recovery action."""
        max_retries = action.parameters.get('max_retries', self.retry_config.max_retries)
        
        # This is a placeholder - actual retry logic would be implemented
        # in the calling orchestration engine
        return {
            "success": True,
            "message": f"Retry action prepared with max {max_retries} attempts",
            "retry_config": {
                "max_retries": max_retries,
                "base_delay": self.retry_config.base_delay,
                "max_delay": self.retry_config.max_delay
            }
        }
    
    async def _execute_fallback_tool_action(self, 
                                          action: RecoveryAction,
                                          context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute fallback tool recovery action."""
        # This would integrate with the tool registry to find alternative tools
        return {
            "success": True,
            "message": "Fallback tool selection prepared",
            "action": "find_alternative_tools",
            "parameters": action.parameters
        }
    
    async def _execute_graceful_degradation_action(self, 
                                                 action: RecoveryAction,
                                                 context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute graceful degradation recovery action."""
        use_cache = action.parameters.get('use_cache', False)
        use_defaults = action.parameters.get('use_defaults', False)
        
        return {
            "success": True,
            "message": "Graceful degradation activated",
            "degradation_mode": {
                "use_cache": use_cache,
                "use_defaults": use_defaults,
                "simplified_response": True
            }
        }
    
    async def _execute_partial_results_action(self, 
                                            action: RecoveryAction,
                                            context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute partial results recovery action."""
        partial_results = context.additional_data.get('partial_results', [])
        
        return {
            "success": True,
            "message": f"Returning {len(partial_results)} partial results",
            "partial_results": partial_results,
            "incomplete_operations": context.additional_data.get('failed_operations', [])
        }
    
    async def _execute_user_notification_action(self, 
                                              action: RecoveryAction,
                                              context: OrchestrationErrorContext) -> Dict[str, Any]:
        """Execute user notification recovery action."""
        return {
            "success": True,
            "message": "User notification prepared",
            "notification": {
                "type": "error_recovery",
                "suggest_rephrase": action.parameters.get('suggest_rephrase', False),
                "provide_alternatives": action.parameters.get('provide_alternatives', True)
            }
        }
    
    def create_error_context(self, 
                           operation: str,
                           correlation_id: str,
                           **kwargs) -> OrchestrationErrorContext:
        """
        Create orchestration error context.
        
        Args:
            operation: Operation being performed
            correlation_id: Correlation ID for tracking
            **kwargs: Additional context data
            
        Returns:
            OrchestrationErrorContext object
        """
        return OrchestrationErrorContext(
            operation=operation,
            correlation_id=correlation_id,
            intent=kwargs.get('intent'),
            selected_tools=kwargs.get('selected_tools'),
            user_context=kwargs.get('user_context'),
            workflow_step=kwargs.get('workflow_step'),
            tool_id=kwargs.get('tool_id'),
            execution_time_ms=kwargs.get('execution_time_ms'),
            additional_data=kwargs.get('additional_data', {})
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring and analysis."""
        return {
            "error_counts": dict(self._error_stats),
            "recovery_effectiveness": dict(self._recovery_stats),
            "circuit_breaker_states": {
                tool_id: cb.get_stats() 
                for tool_id, cb in self._circuit_breakers.items()
            }
        }
    
    def reset_statistics(self) -> None:
        """Reset error and recovery statistics."""
        self._error_stats.clear()
        self._recovery_stats.clear()
        self.logger.info("Error and recovery statistics reset")


# Global orchestration error handler instance
_orchestration_error_handler = None


def get_orchestration_error_handler() -> OrchestrationErrorHandler:
    """Get the global orchestration error handler instance."""
    global _orchestration_error_handler
    if _orchestration_error_handler is None:
        _orchestration_error_handler = OrchestrationErrorHandler()
    return _orchestration_error_handler


# Export main classes and functions
__all__ = [
    'OrchestrationErrorHandler',
    'OrchestrationErrorContext',
    'OrchestrationError',
    'IntentAnalysisError',
    'ToolSelectionError',
    'WorkflowExecutionError',
    'ToolInvocationError',
    'PartialWorkflowFailure',
    'OrchestrationErrorType',
    'RecoveryStrategy',
    'RecoveryAction',
    'OrchestrationErrorResult',
    'get_orchestration_error_handler'
]