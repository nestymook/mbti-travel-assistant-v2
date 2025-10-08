"""
Orchestration Logging and Observability Service

This module provides comprehensive logging and observability specifically for the
tool orchestration system, including structured logging, correlation ID tracking,
and integration with AgentCore monitoring.

Features:
- Structured logging for all orchestration decisions and actions
- Correlation ID tracking for request tracing across components
- Performance metrics collection for orchestration operations
- Integration with existing AgentCore monitoring service
- Detailed logging of tool selection decisions
- Workflow execution tracking and analysis
- Error correlation and pattern analysis
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import statistics
import traceback
from pathlib import Path

# Import existing monitoring components
from .agentcore_monitoring_service import (
    AgentCoreMonitoringService, AgentOperationType, AgentInvocationLog, AgentInvocationResult
)
from .logging_service import LoggingService, PerformanceMetric, get_logging_service

# Import orchestration types
from .orchestration_types import (
    RequestType, ExecutionStrategy, UserContext, Intent, 
    SelectedTool, OrchestrationResult
)

if TYPE_CHECKING:
    from .orchestration_error_handler import OrchestrationErrorHandler, OrchestrationErrorContext


class OrchestrationLogLevel(Enum):
    """Orchestration-specific log levels."""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OrchestrationEventType(Enum):
    """Types of orchestration events to log."""
    REQUEST_RECEIVED = "request_received"
    INTENT_ANALYSIS_STARTED = "intent_analysis_started"
    INTENT_ANALYSIS_COMPLETED = "intent_analysis_completed"
    TOOL_SELECTION_STARTED = "tool_selection_started"
    TOOL_SELECTION_COMPLETED = "tool_selection_completed"
    WORKFLOW_EXECUTION_STARTED = "workflow_execution_started"
    WORKFLOW_STEP_STARTED = "workflow_step_started"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    TOOL_INVOCATION_STARTED = "tool_invocation_started"
    TOOL_INVOCATION_COMPLETED = "tool_invocation_completed"
    WORKFLOW_EXECUTION_COMPLETED = "workflow_execution_completed"
    REQUEST_COMPLETED = "request_completed"
    ERROR_OCCURRED = "error_occurred"
    RECOVERY_ACTION_STARTED = "recovery_action_started"
    RECOVERY_ACTION_COMPLETED = "recovery_action_completed"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"
    FALLBACK_EXECUTED = "fallback_executed"
    PERFORMANCE_THRESHOLD_EXCEEDED = "performance_threshold_exceeded"


@dataclass
class OrchestrationLogEntry:
    """Structured log entry for orchestration events."""
    correlation_id: str
    timestamp: str
    event_type: str
    level: str
    message: str
    component: str = "orchestration_engine"
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class IntentAnalysisLog:
    """Log entry for intent analysis operations."""
    correlation_id: str
    timestamp: str
    request_text: str
    request_length: int
    analysis_duration_ms: float
    intent_type: str
    confidence: float
    parameters_extracted: Dict[str, Any]
    required_capabilities: List[str]
    optional_capabilities: List[str]
    context_used: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class ToolSelectionLog:
    """Log entry for tool selection operations."""
    correlation_id: str
    timestamp: str
    intent_type: str
    available_tools_count: int
    selected_tools_count: int
    selection_duration_ms: float
    selection_criteria: Dict[str, float]
    selected_tools: List[Dict[str, Any]]
    rejected_tools: List[Dict[str, Any]]
    health_checks_performed: int
    performance_data_used: bool = False
    user_context_considered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class WorkflowExecutionLog:
    """Log entry for workflow execution operations."""
    correlation_id: str
    timestamp: str
    workflow_type: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    total_duration_ms: float
    parallel_execution: bool
    tools_used: List[str]
    step_details: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class ToolInvocationLog:
    """Log entry for individual tool invocations."""
    correlation_id: str
    timestamp: str
    tool_id: str
    tool_name: str
    operation: str
    input_parameters: Dict[str, Any]
    execution_duration_ms: float
    success: bool
    output_size_bytes: int
    retry_count: int = 0
    circuit_breaker_state: str = "closed"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """Performance metrics for orchestration operations."""
    correlation_id: str
    timestamp: str
    operation_type: str
    total_duration_ms: float
    intent_analysis_duration_ms: float
    tool_selection_duration_ms: float
    workflow_execution_duration_ms: float
    tools_invoked: int
    successful_tools: int
    failed_tools: int
    retry_attempts: int
    circuit_breaker_triggers: int
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


class CorrelationIDManager:
    """Manages correlation IDs for request tracing."""
    
    def __init__(self):
        """Initialize correlation ID manager."""
        self._current_correlation_id = None
        self._correlation_stack = []
        self._lock = threading.Lock()
    
    def generate_correlation_id(self, prefix: str = "orch") -> str:
        """Generate a new correlation ID."""
        timestamp = int(time.time() * 1000)
        random_part = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{random_part}"
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the current correlation ID for the thread."""
        with self._lock:
            if self._current_correlation_id:
                self._correlation_stack.append(self._current_correlation_id)
            self._current_correlation_id = correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID."""
        return self._current_correlation_id
    
    def clear_correlation_id(self) -> None:
        """Clear the current correlation ID."""
        with self._lock:
            if self._correlation_stack:
                self._current_correlation_id = self._correlation_stack.pop()
            else:
                self._current_correlation_id = None
    
    def create_child_correlation_id(self, operation: str) -> str:
        """Create a child correlation ID for sub-operations."""
        parent_id = self._current_correlation_id or "unknown"
        child_suffix = f"{operation}_{uuid.uuid4().hex[:6]}"
        return f"{parent_id}.{child_suffix}"


class OrchestrationMetricsCollector:
    """Collects and aggregates orchestration performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self._lock = threading.Lock()
        
        # Metrics storage
        self._performance_metrics = deque(maxlen=max_history)
        self._intent_analysis_metrics = deque(maxlen=max_history)
        self._tool_selection_metrics = deque(maxlen=max_history)
        self._workflow_execution_metrics = deque(maxlen=max_history)
        self._tool_invocation_metrics = deque(maxlen=max_history)
        
        # Aggregated statistics
        self._operation_stats = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'total_duration_ms': 0.0,
            'min_duration_ms': float('inf'),
            'max_duration_ms': 0.0,
            'error_count': 0
        })
        
        # Tool performance tracking
        self._tool_performance = defaultdict(lambda: {
            'invocation_count': 0,
            'success_count': 0,
            'total_duration_ms': 0.0,
            'error_types': defaultdict(int)
        })
        
        # Circuit breaker events
        self._circuit_breaker_events = deque(maxlen=100)
        
        # Performance thresholds
        self.performance_thresholds = {
            'intent_analysis_ms': 1000,
            'tool_selection_ms': 2000,
            'workflow_execution_ms': 30000,
            'tool_invocation_ms': 10000,
            'total_request_ms': 60000
        }
    
    def record_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics."""
        with self._lock:
            self._performance_metrics.append(metrics)
            
            # Update operation statistics
            op_stats = self._operation_stats[metrics.operation_type]
            op_stats['count'] += 1
            op_stats['total_duration_ms'] += metrics.total_duration_ms
            op_stats['min_duration_ms'] = min(op_stats['min_duration_ms'], metrics.total_duration_ms)
            op_stats['max_duration_ms'] = max(op_stats['max_duration_ms'], metrics.total_duration_ms)
            
            if metrics.failed_tools == 0:
                op_stats['success_count'] += 1
            else:
                op_stats['error_count'] += 1
    
    def record_intent_analysis(self, log_entry: IntentAnalysisLog) -> None:
        """Record intent analysis metrics."""
        with self._lock:
            self._intent_analysis_metrics.append(log_entry)
    
    def record_tool_selection(self, log_entry: ToolSelectionLog) -> None:
        """Record tool selection metrics."""
        with self._lock:
            self._tool_selection_metrics.append(log_entry)
    
    def record_workflow_execution(self, log_entry: WorkflowExecutionLog) -> None:
        """Record workflow execution metrics."""
        with self._lock:
            self._workflow_execution_metrics.append(log_entry)
    
    def record_tool_invocation(self, log_entry: ToolInvocationLog) -> None:
        """Record tool invocation metrics."""
        with self._lock:
            self._tool_invocation_metrics.append(log_entry)
            
            # Update tool performance statistics
            tool_perf = self._tool_performance[log_entry.tool_id]
            tool_perf['invocation_count'] += 1
            tool_perf['total_duration_ms'] += log_entry.execution_duration_ms
            
            if log_entry.success:
                tool_perf['success_count'] += 1
            else:
                if log_entry.error_type:
                    tool_perf['error_types'][log_entry.error_type] += 1
    
    def record_circuit_breaker_event(self, 
                                   tool_id: str, 
                                   event_type: str,
                                   correlation_id: str) -> None:
        """Record circuit breaker events."""
        with self._lock:
            self._circuit_breaker_events.append({
                'timestamp': datetime.utcnow().isoformat(),
                'tool_id': tool_id,
                'event_type': event_type,
                'correlation_id': correlation_id
            })
    
    def get_performance_summary(self, 
                              operation_type: Optional[str] = None,
                              time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Get performance summary statistics."""
        with self._lock:
            if time_window_minutes:
                cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
                metrics = [
                    m for m in self._performance_metrics 
                    if datetime.fromisoformat(m.timestamp) >= cutoff_time
                ]
            else:
                metrics = list(self._performance_metrics)
            
            if operation_type:
                metrics = [m for m in metrics if m.operation_type == operation_type]
            
            if not metrics:
                return {"message": "No metrics available for the specified criteria"}
            
            # Calculate statistics
            durations = [m.total_duration_ms for m in metrics]
            success_rate = sum(1 for m in metrics if m.failed_tools == 0) / len(metrics)
            
            return {
                "total_requests": len(metrics),
                "success_rate": success_rate,
                "average_duration_ms": statistics.mean(durations),
                "median_duration_ms": statistics.median(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
                "total_tools_invoked": sum(m.tools_invoked for m in metrics),
                "total_retry_attempts": sum(m.retry_attempts for m in metrics),
                "circuit_breaker_triggers": sum(m.circuit_breaker_triggers for m in metrics)
            }
    
    def get_tool_performance_summary(self, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tool performance summary."""
        with self._lock:
            if tool_id:
                if tool_id not in self._tool_performance:
                    return {"message": f"No performance data for tool {tool_id}"}
                
                perf = self._tool_performance[tool_id]
                success_rate = perf['success_count'] / perf['invocation_count'] if perf['invocation_count'] > 0 else 0
                avg_duration = perf['total_duration_ms'] / perf['invocation_count'] if perf['invocation_count'] > 0 else 0
                
                return {
                    "tool_id": tool_id,
                    "invocation_count": perf['invocation_count'],
                    "success_rate": success_rate,
                    "average_duration_ms": avg_duration,
                    "error_types": dict(perf['error_types'])
                }
            else:
                # Return summary for all tools
                summary = {}
                for tool_id, perf in self._tool_performance.items():
                    success_rate = perf['success_count'] / perf['invocation_count'] if perf['invocation_count'] > 0 else 0
                    avg_duration = perf['total_duration_ms'] / perf['invocation_count'] if perf['invocation_count'] > 0 else 0
                    
                    summary[tool_id] = {
                        "invocation_count": perf['invocation_count'],
                        "success_rate": success_rate,
                        "average_duration_ms": avg_duration,
                        "error_count": sum(perf['error_types'].values())
                    }
                
                return summary
    
    def check_performance_thresholds(self, metrics: PerformanceMetrics) -> List[str]:
        """Check if performance metrics exceed thresholds."""
        violations = []
        
        if metrics.intent_analysis_duration_ms > self.performance_thresholds['intent_analysis_ms']:
            violations.append(f"Intent analysis duration ({metrics.intent_analysis_duration_ms:.2f}ms) exceeds threshold ({self.performance_thresholds['intent_analysis_ms']}ms)")
        
        if metrics.tool_selection_duration_ms > self.performance_thresholds['tool_selection_ms']:
            violations.append(f"Tool selection duration ({metrics.tool_selection_duration_ms:.2f}ms) exceeds threshold ({self.performance_thresholds['tool_selection_ms']}ms)")
        
        if metrics.workflow_execution_duration_ms > self.performance_thresholds['workflow_execution_ms']:
            violations.append(f"Workflow execution duration ({metrics.workflow_execution_duration_ms:.2f}ms) exceeds threshold ({self.performance_thresholds['workflow_execution_ms']}ms)")
        
        if metrics.total_duration_ms > self.performance_thresholds['total_request_ms']:
            violations.append(f"Total request duration ({metrics.total_duration_ms:.2f}ms) exceeds threshold ({self.performance_thresholds['total_request_ms']}ms)")
        
        return violations


class OrchestrationLoggingService:
    """
    Comprehensive logging and observability service for tool orchestration.
    
    Provides structured logging, correlation tracking, performance monitoring,
    and integration with AgentCore monitoring systems.
    """
    
    def __init__(self, 
                 environment: str = "production",
                 log_level: str = "INFO",
                 enable_performance_monitoring: bool = True,
                 enable_detailed_logging: bool = True,
                 monitoring_service: Optional[AgentCoreMonitoringService] = None):
        """
        Initialize orchestration logging service.
        
        Args:
            environment: Environment name (development, staging, production)
            log_level: Logging level
            enable_performance_monitoring: Enable performance metrics collection
            enable_detailed_logging: Enable detailed operation logging
            monitoring_service: Existing AgentCore monitoring service
        """
        self.environment = environment
        self.enable_performance_monitoring = enable_performance_monitoring
        self.enable_detailed_logging = enable_detailed_logging
        
        # Log file paths (initialize before logging setup)
        self.log_directory = Path("logs/orchestration")
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger("orchestration_logging")
        self._setup_logging(log_level)
        
        # Initialize components
        self.correlation_manager = CorrelationIDManager()
        self.metrics_collector = OrchestrationMetricsCollector()
        
        # Integration with existing services
        self.monitoring_service = monitoring_service
        self.base_logging_service = get_logging_service()
        
        # Performance tracking
        self._operation_start_times = {}
        self._operation_lock = threading.Lock()
        
        self.logger.info(f"Orchestration logging service initialized for {environment} environment")
    
    def _setup_logging(self, log_level: str) -> None:
        """Configure logging with structured formatters."""
        # Create formatter for structured JSON logging
        json_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(json_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler for orchestration logs
            file_handler = logging.FileHandler(
                self.log_directory / f"orchestration_{self.environment}.log"
            )
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)
            
            self.logger.setLevel(getattr(logging, log_level.upper()))
    
    def start_operation(self, 
                       operation: str,
                       correlation_id: Optional[str] = None,
                       **context) -> str:
        """
        Start tracking an orchestration operation.
        
        Args:
            operation: Operation name
            correlation_id: Optional correlation ID (will generate if not provided)
            **context: Additional context information
            
        Returns:
            Correlation ID for the operation
        """
        if not correlation_id:
            correlation_id = self.correlation_manager.generate_correlation_id()
        
        self.correlation_manager.set_correlation_id(correlation_id)
        
        with self._operation_lock:
            self._operation_start_times[correlation_id] = {
                'start_time': time.time(),
                'operation': operation,
                'context': context
            }
        
        # Log operation start
        self._log_event(
            event_type=OrchestrationEventType.REQUEST_RECEIVED,
            level=OrchestrationLogLevel.INFO,
            message=f"Started orchestration operation: {operation}",
            correlation_id=correlation_id,
            operation=operation,
            metadata=context
        )
        
        return correlation_id
    
    def end_operation(self, 
                     correlation_id: str,
                     success: bool = True,
                     error_message: Optional[str] = None,
                     **results) -> None:
        """
        End tracking an orchestration operation.
        
        Args:
            correlation_id: Correlation ID of the operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
            **results: Operation results
        """
        with self._operation_lock:
            operation_data = self._operation_start_times.pop(correlation_id, None)
        
        if operation_data:
            duration_ms = (time.time() - operation_data['start_time']) * 1000
            
            # Log operation completion
            self._log_event(
                event_type=OrchestrationEventType.REQUEST_COMPLETED,
                level=OrchestrationLogLevel.INFO if success else OrchestrationLogLevel.ERROR,
                message=f"Completed orchestration operation: {operation_data['operation']} ({'success' if success else 'failed'})",
                correlation_id=correlation_id,
                operation=operation_data['operation'],
                execution_time_ms=duration_ms,
                metadata={
                    'success': success,
                    'error_message': error_message,
                    'results': results
                }
            )
        
        self.correlation_manager.clear_correlation_id()
    
    def log_intent_analysis(self, 
                           request_text: str,
                           intent: Intent,
                           analysis_duration_ms: float,
                           context_used: bool = False,
                           correlation_id: Optional[str] = None) -> None:
        """Log intent analysis operation."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        log_entry = IntentAnalysisLog(
            correlation_id=correlation_id or "unknown",
            timestamp=datetime.utcnow().isoformat(),
            request_text=request_text[:200] + "..." if len(request_text) > 200 else request_text,
            request_length=len(request_text),
            analysis_duration_ms=analysis_duration_ms,
            intent_type=intent.type.value,
            confidence=intent.confidence,
            parameters_extracted=intent.parameters,
            required_capabilities=intent.required_capabilities,
            optional_capabilities=intent.optional_capabilities,
            context_used=context_used
        )
        
        if self.enable_performance_monitoring:
            self.metrics_collector.record_intent_analysis(log_entry)
        
        self._log_event(
            event_type=OrchestrationEventType.INTENT_ANALYSIS_COMPLETED,
            level=OrchestrationLogLevel.INFO,
            message=f"Intent analysis completed: {intent.type.value} (confidence: {intent.confidence:.2f})",
            correlation_id=correlation_id,
            execution_time_ms=analysis_duration_ms,
            metadata=log_entry.to_dict()
        )
    
    def log_tool_selection(self, 
                          intent: Intent,
                          selected_tools: List[SelectedTool],
                          available_tools_count: int,
                          selection_duration_ms: float,
                          selection_criteria: Dict[str, float],
                          rejected_tools: List[Dict[str, Any]] = None,
                          correlation_id: Optional[str] = None) -> None:
        """Log tool selection operation."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        selected_tools_data = [
            {
                'tool_id': tool.tool_id,
                'tool_name': tool.tool_name,
                'confidence': tool.confidence,
                'selection_reason': tool.selection_reason
            }
            for tool in selected_tools
        ]
        
        log_entry = ToolSelectionLog(
            correlation_id=correlation_id or "unknown",
            timestamp=datetime.utcnow().isoformat(),
            intent_type=intent.type.value,
            available_tools_count=available_tools_count,
            selected_tools_count=len(selected_tools),
            selection_duration_ms=selection_duration_ms,
            selection_criteria=selection_criteria,
            selected_tools=selected_tools_data,
            rejected_tools=rejected_tools or [],
            health_checks_performed=0,  # This would be populated by the tool selector
            performance_data_used=True,
            user_context_considered=True
        )
        
        if self.enable_performance_monitoring:
            self.metrics_collector.record_tool_selection(log_entry)
        
        self._log_event(
            event_type=OrchestrationEventType.TOOL_SELECTION_COMPLETED,
            level=OrchestrationLogLevel.INFO,
            message=f"Tool selection completed: {len(selected_tools)} tools selected from {available_tools_count} available",
            correlation_id=correlation_id,
            execution_time_ms=selection_duration_ms,
            metadata=log_entry.to_dict()
        )
    
    def log_workflow_execution(self, 
                             workflow_type: str,
                             tools_used: List[str],
                             step_details: List[Dict[str, Any]],
                             total_duration_ms: float,
                             success: bool,
                             error_message: Optional[str] = None,
                             correlation_id: Optional[str] = None) -> None:
        """Log workflow execution operation."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        completed_steps = sum(1 for step in step_details if step.get('success', False))
        failed_steps = len(step_details) - completed_steps
        
        log_entry = WorkflowExecutionLog(
            correlation_id=correlation_id or "unknown",
            timestamp=datetime.utcnow().isoformat(),
            workflow_type=workflow_type,
            total_steps=len(step_details),
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_duration_ms=total_duration_ms,
            parallel_execution=False,  # This would be determined by the workflow engine
            tools_used=tools_used,
            step_details=step_details,
            success=success,
            error_message=error_message
        )
        
        if self.enable_performance_monitoring:
            self.metrics_collector.record_workflow_execution(log_entry)
        
        self._log_event(
            event_type=OrchestrationEventType.WORKFLOW_EXECUTION_COMPLETED,
            level=OrchestrationLogLevel.INFO if success else OrchestrationLogLevel.ERROR,
            message=f"Workflow execution {'completed' if success else 'failed'}: {workflow_type} ({completed_steps}/{len(step_details)} steps successful)",
            correlation_id=correlation_id,
            execution_time_ms=total_duration_ms,
            metadata=log_entry.to_dict()
        )
    
    def log_tool_invocation(self, 
                           tool_id: str,
                           tool_name: str,
                           operation: str,
                           input_parameters: Dict[str, Any],
                           execution_duration_ms: float,
                           success: bool,
                           output_size_bytes: int = 0,
                           retry_count: int = 0,
                           circuit_breaker_state: str = "closed",
                           error_type: Optional[str] = None,
                           error_message: Optional[str] = None,
                           correlation_id: Optional[str] = None) -> None:
        """Log tool invocation operation."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        # Sanitize input parameters for logging (remove sensitive data)
        sanitized_params = self._sanitize_parameters(input_parameters)
        
        log_entry = ToolInvocationLog(
            correlation_id=correlation_id or "unknown",
            timestamp=datetime.utcnow().isoformat(),
            tool_id=tool_id,
            tool_name=tool_name,
            operation=operation,
            input_parameters=sanitized_params,
            execution_duration_ms=execution_duration_ms,
            success=success,
            output_size_bytes=output_size_bytes,
            retry_count=retry_count,
            circuit_breaker_state=circuit_breaker_state,
            error_type=error_type,
            error_message=error_message
        )
        
        if self.enable_performance_monitoring:
            self.metrics_collector.record_tool_invocation(log_entry)
        
        # Log to AgentCore monitoring service if available
        if self.monitoring_service:
            try:
                self.monitoring_service.log_agent_invocation_result(
                    correlation_id=correlation_id,
                    agent_arn=f"tool://{tool_id}",
                    operation_type=AgentOperationType.RESTAURANT_SEARCH,  # This would be mapped appropriately
                    response=None,  # Would contain actual response if needed
                    error=Exception(error_message) if error_message else None
                )
            except Exception as e:
                self.logger.warning(f"Failed to log to AgentCore monitoring: {e}")
        
        self._log_event(
            event_type=OrchestrationEventType.TOOL_INVOCATION_COMPLETED,
            level=OrchestrationLogLevel.INFO if success else OrchestrationLogLevel.WARNING,
            message=f"Tool invocation {'completed' if success else 'failed'}: {tool_name} ({operation})",
            correlation_id=correlation_id,
            execution_time_ms=execution_duration_ms,
            metadata=log_entry.to_dict()
        )
    
    def log_error(self, 
                 error: Exception,
                 context: 'OrchestrationErrorContext',
                 recovery_actions: Optional[List[str]] = None) -> None:
        """Log orchestration error with context."""
        correlation_id = context.correlation_id
        
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'operation': context.operation,
            'workflow_step': context.workflow_step,
            'tool_id': context.tool_id,
            'execution_time_ms': context.execution_time_ms,
            'recovery_actions': recovery_actions or [],
            'stack_trace': traceback.format_exc()
        }
        
        # Add context information
        if context.intent:
            error_data['intent'] = {
                'type': context.intent.type.value,
                'confidence': context.intent.confidence
            }
        
        if context.selected_tools:
            error_data['selected_tools'] = [
                {'tool_id': tool.tool_id, 'tool_name': tool.tool_name}
                for tool in context.selected_tools
            ]
        
        self._log_event(
            event_type=OrchestrationEventType.ERROR_OCCURRED,
            level=OrchestrationLogLevel.ERROR,
            message=f"Orchestration error in {context.operation}: {str(error)}",
            correlation_id=correlation_id,
            metadata=error_data
        )
    
    def log_performance_metrics(self, 
                              operation_type: str,
                              total_duration_ms: float,
                              intent_analysis_duration_ms: float,
                              tool_selection_duration_ms: float,
                              workflow_execution_duration_ms: float,
                              tools_invoked: int,
                              successful_tools: int,
                              failed_tools: int,
                              retry_attempts: int = 0,
                              circuit_breaker_triggers: int = 0,
                              correlation_id: Optional[str] = None) -> None:
        """Log performance metrics for an orchestration operation."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        metrics = PerformanceMetrics(
            correlation_id=correlation_id or "unknown",
            timestamp=datetime.utcnow().isoformat(),
            operation_type=operation_type,
            total_duration_ms=total_duration_ms,
            intent_analysis_duration_ms=intent_analysis_duration_ms,
            tool_selection_duration_ms=tool_selection_duration_ms,
            workflow_execution_duration_ms=workflow_execution_duration_ms,
            tools_invoked=tools_invoked,
            successful_tools=successful_tools,
            failed_tools=failed_tools,
            retry_attempts=retry_attempts,
            circuit_breaker_triggers=circuit_breaker_triggers
        )
        
        if self.enable_performance_monitoring:
            self.metrics_collector.record_performance_metrics(metrics)
            
            # Check performance thresholds
            violations = self.metrics_collector.check_performance_thresholds(metrics)
            if violations:
                self._log_event(
                    event_type=OrchestrationEventType.PERFORMANCE_THRESHOLD_EXCEEDED,
                    level=OrchestrationLogLevel.WARNING,
                    message=f"Performance thresholds exceeded: {'; '.join(violations)}",
                    correlation_id=correlation_id,
                    metadata={'violations': violations, 'metrics': metrics.to_dict()}
                )
    
    def log_circuit_breaker_event(self, 
                                 tool_id: str,
                                 event_type: str,
                                 correlation_id: Optional[str] = None) -> None:
        """Log circuit breaker events."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id()
        
        self.metrics_collector.record_circuit_breaker_event(tool_id, event_type, correlation_id)
        
        self._log_event(
            event_type=OrchestrationEventType.CIRCUIT_BREAKER_TRIGGERED,
            level=OrchestrationLogLevel.WARNING,
            message=f"Circuit breaker {event_type} for tool {tool_id}",
            correlation_id=correlation_id,
            metadata={'tool_id': tool_id, 'event_type': event_type}
        )
    
    def _log_event(self, 
                  event_type: OrchestrationEventType,
                  level: OrchestrationLogLevel,
                  message: str,
                  correlation_id: Optional[str] = None,
                  operation: Optional[str] = None,
                  execution_time_ms: Optional[float] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a structured orchestration event."""
        correlation_id = correlation_id or self.correlation_manager.get_correlation_id() or "unknown"
        
        log_entry = OrchestrationLogEntry(
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type.value,
            level=level.value,
            message=message,
            operation=operation,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
        
        # Log with appropriate level
        log_level = getattr(logging, level.value.upper())
        self.logger.log(log_level, message, extra={
            'orchestration_event': log_entry.to_dict(),
            'correlation_id': correlation_id
        })
        
        # Write to structured log file if detailed logging is enabled
        if self.enable_detailed_logging:
            self._write_structured_log(log_entry)
    
    def _write_structured_log(self, log_entry: OrchestrationLogEntry) -> None:
        """Write structured log entry to file."""
        try:
            log_file = self.log_directory / f"orchestration_events_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a') as f:
                f.write(log_entry.to_json() + '\n')
        except Exception as e:
            self.logger.warning(f"Failed to write structured log: {e}")
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for logging (remove sensitive information)."""
        sanitized = {}
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth', 'credential'}
        
        for key, value in parameters.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[TRUNCATED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def get_performance_summary(self, 
                              operation_type: Optional[str] = None,
                              time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Get performance summary from metrics collector."""
        return self.metrics_collector.get_performance_summary(operation_type, time_window_minutes)
    
    def get_tool_performance_summary(self, tool_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tool performance summary from metrics collector."""
        return self.metrics_collector.get_tool_performance_summary(tool_id)
    
    def create_child_correlation_id(self, operation: str) -> str:
        """Create a child correlation ID for sub-operations."""
        return self.correlation_manager.create_child_correlation_id(operation)


# Global orchestration logging service instance
_orchestration_logging_service = None


def get_orchestration_logging_service() -> OrchestrationLoggingService:
    """Get the global orchestration logging service instance."""
    global _orchestration_logging_service
    if _orchestration_logging_service is None:
        _orchestration_logging_service = OrchestrationLoggingService()
    return _orchestration_logging_service


# Export main classes and functions
__all__ = [
    'OrchestrationLoggingService',
    'OrchestrationLogEntry',
    'IntentAnalysisLog',
    'ToolSelectionLog',
    'WorkflowExecutionLog',
    'ToolInvocationLog',
    'PerformanceMetrics',
    'OrchestrationEventType',
    'OrchestrationLogLevel',
    'CorrelationIDManager',
    'OrchestrationMetricsCollector',
    'get_orchestration_logging_service'
]