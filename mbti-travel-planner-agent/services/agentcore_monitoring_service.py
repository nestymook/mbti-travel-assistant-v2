"""
AgentCore Monitoring and Observability Service

This module provides comprehensive monitoring and observability features specifically
for AgentCore agent invocations, including structured logging, performance metrics,
health checks, and correlation tracking.

Features:
- Structured logging for AgentCore agent invocations
- Performance metrics tracking (response times, success rates)
- Health check service for agent connectivity
- Correlation IDs for request tracing
- Integration with existing logging service
- AgentCore-specific error tracking and analysis
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import statistics

from .logging_service import LoggingService, get_logging_service, PerformanceMetric
from .health_check_service import HealthCheckService, ServiceEndpoint, HealthStatus
from .agentcore_error_handler import AgentCoreError, AgentInvocationError

# Type hints only imports to avoid circular dependency
if TYPE_CHECKING:
    from .agentcore_runtime_client import AgentCoreRuntimeClient, AgentResponse


class AgentOperationType(Enum):
    """Types of AgentCore operations to monitor."""
    RESTAURANT_SEARCH = "restaurant_search"
    RESTAURANT_REASONING = "restaurant_reasoning"
    CENTRAL_DISTRICT_WORKFLOW = "central_district_workflow"
    HEALTH_CHECK = "health_check"
    AUTHENTICATION = "authentication"


@dataclass
class AgentInvocationLog:
    """Structured log entry for AgentCore agent invocations."""
    correlation_id: str
    timestamp: str
    agent_arn: str
    operation_type: str
    input_size: int
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    environment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class AgentInvocationResult:
    """Result of AgentCore agent invocation for monitoring."""
    correlation_id: str
    timestamp: str
    agent_arn: str
    operation_type: str
    success: bool
    response_time_ms: float
    output_size: int
    session_id: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    circuit_breaker_triggered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class AgentHealthCheckResult:
    """Health check result specific to AgentCore agents."""
    agent_arn: str
    agent_name: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time_ms: float
    timestamp: datetime
    test_input: str
    test_output: Optional[str] = None
    error_message: Optional[str] = None
    authentication_status: str = "unknown"  # "valid", "expired", "invalid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AgentCoreMetricsCollector:
    """Specialized metrics collector for AgentCore operations."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize AgentCore metrics collector.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self._lock = threading.Lock()
        
        # Agent-specific metrics
        self._agent_metrics = defaultdict(lambda: deque(maxlen=max_history))
        self._operation_metrics = defaultdict(lambda: deque(maxlen=max_history))
        
        # Counters
        self._invocation_counters = defaultdict(int)
        self._error_counters = defaultdict(int)
        self._success_counters = defaultdict(int)
        
        # Response time tracking
        self._response_times = defaultdict(lambda: deque(maxlen=max_history))
        
        # Circuit breaker events
        self._circuit_breaker_events = deque(maxlen=100)
        
        # Authentication events
        self._auth_events = deque(maxlen=100)
    
    def record_invocation(self, 
                         agent_arn: str, 
                         operation_type: str,
                         response_time_ms: float,
                         success: bool,
                         error_type: Optional[str] = None,
                         retry_count: int = 0,
                         circuit_breaker_triggered: bool = False) -> None:
        """Record an agent invocation for metrics."""
        with self._lock:
            timestamp = datetime.utcnow()
            
            # Record in agent-specific metrics
            agent_key = self._get_agent_key(agent_arn)
            self._agent_metrics[agent_key].append({
                'timestamp': timestamp,
                'operation_type': operation_type,
                'response_time_ms': response_time_ms,
                'success': success,
                'error_type': error_type,
                'retry_count': retry_count,
                'circuit_breaker_triggered': circuit_breaker_triggered
            })
            
            # Record in operation-specific metrics
            self._operation_metrics[operation_type].append({
                'timestamp': timestamp,
                'agent_arn': agent_arn,
                'response_time_ms': response_time_ms,
                'success': success,
                'error_type': error_type,
                'retry_count': retry_count,
                'circuit_breaker_triggered': circuit_breaker_triggered
            })
            
            # Update counters
            self._invocation_counters[f"{agent_key}:{operation_type}"] += 1
            
            if success:
                self._success_counters[f"{agent_key}:{operation_type}"] += 1
            else:
                self._error_counters[f"{agent_key}:{operation_type}"] += 1
                if error_type:
                    self._error_counters[f"{agent_key}:{operation_type}:{error_type}"] += 1
            
            # Record response time
            self._response_times[f"{agent_key}:{operation_type}"].append(response_time_ms)
            
            # Record circuit breaker events
            if circuit_breaker_triggered:
                self._circuit_breaker_events.append({
                    'timestamp': timestamp,
                    'agent_arn': agent_arn,
                    'operation_type': operation_type,
                    'event_type': 'triggered'
                })
    
    def record_authentication_event(self, 
                                   event_type: str,
                                   success: bool,
                                   error_message: Optional[str] = None) -> None:
        """Record authentication events."""
        with self._lock:
            self._auth_events.append({
                'timestamp': datetime.utcnow(),
                'event_type': event_type,  # 'token_refresh', 'token_validation', etc.
                'success': success,
                'error_message': error_message
            })
    
    def get_agent_metrics(self, agent_arn: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics for a specific agent."""
        with self._lock:
            agent_key = self._get_agent_key(agent_arn)
            metrics = self._agent_metrics.get(agent_key, deque())
            
            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_metrics = [
                m for m in metrics 
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return self._empty_metrics()
            
            # Calculate statistics
            total_calls = len(recent_metrics)
            successful_calls = sum(1 for m in recent_metrics if m['success'])
            failed_calls = total_calls - successful_calls
            
            response_times = [m['response_time_ms'] for m in recent_metrics]
            response_times.sort()
            
            # Error breakdown
            error_types = defaultdict(int)
            for m in recent_metrics:
                if not m['success'] and m['error_type']:
                    error_types[m['error_type']] += 1
            
            # Retry statistics
            retry_counts = [m['retry_count'] for m in recent_metrics]
            circuit_breaker_triggers = sum(1 for m in recent_metrics if m['circuit_breaker_triggered'])
            
            return {
                'agent_arn': agent_arn,
                'window_minutes': window_minutes,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': (successful_calls / total_calls) * 100 if total_calls > 0 else 0,
                'response_time_stats': self._calculate_response_time_stats(response_times),
                'error_breakdown': dict(error_types),
                'retry_stats': {
                    'total_retries': sum(retry_counts),
                    'avg_retries_per_call': statistics.mean(retry_counts) if retry_counts else 0,
                    'max_retries': max(retry_counts) if retry_counts else 0
                },
                'circuit_breaker_triggers': circuit_breaker_triggers
            }
    
    def get_operation_metrics(self, operation_type: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics for a specific operation type."""
        with self._lock:
            metrics = self._operation_metrics.get(operation_type, deque())
            
            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_metrics = [
                m for m in metrics 
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return self._empty_metrics()
            
            # Calculate statistics
            total_calls = len(recent_metrics)
            successful_calls = sum(1 for m in recent_metrics if m['success'])
            failed_calls = total_calls - successful_calls
            
            response_times = [m['response_time_ms'] for m in recent_metrics]
            response_times.sort()
            
            # Agent breakdown
            agent_breakdown = defaultdict(int)
            for m in recent_metrics:
                agent_key = self._get_agent_key(m['agent_arn'])
                agent_breakdown[agent_key] += 1
            
            return {
                'operation_type': operation_type,
                'window_minutes': window_minutes,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': (successful_calls / total_calls) * 100 if total_calls > 0 else 0,
                'response_time_stats': self._calculate_response_time_stats(response_times),
                'agent_breakdown': dict(agent_breakdown)
            }
    
    def get_authentication_metrics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get authentication metrics."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_events = [
                e for e in self._auth_events 
                if e['timestamp'] > cutoff_time
            ]
            
            if not recent_events:
                return {
                    'window_minutes': window_minutes,
                    'total_events': 0,
                    'successful_events': 0,
                    'failed_events': 0,
                    'success_rate': 0,
                    'event_breakdown': {}
                }
            
            total_events = len(recent_events)
            successful_events = sum(1 for e in recent_events if e['success'])
            failed_events = total_events - successful_events
            
            # Event type breakdown
            event_breakdown = defaultdict(int)
            for e in recent_events:
                status = 'success' if e['success'] else 'failure'
                event_breakdown[f"{e['event_type']}_{status}"] += 1
            
            return {
                'window_minutes': window_minutes,
                'total_events': total_events,
                'successful_events': successful_events,
                'failed_events': failed_events,
                'success_rate': (successful_events / total_events) * 100 if total_events > 0 else 0,
                'event_breakdown': dict(event_breakdown)
            }
    
    def _get_agent_key(self, agent_arn: str) -> str:
        """Extract a readable key from agent ARN."""
        if 'restaurant_search_agent' in agent_arn:
            return 'restaurant_search'
        elif 'restaurant_search_result_reasoning_agent' in agent_arn:
            return 'restaurant_reasoning'
        else:
            # Extract the last part of the ARN
            return agent_arn.split('/')[-1] if '/' in agent_arn else agent_arn
    
    def _calculate_response_time_stats(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate response time statistics."""
        if not response_times:
            return {'count': 0, 'min': 0, 'max': 0, 'mean': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        
        count = len(response_times)
        return {
            'count': count,
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times),
            'p50': response_times[int(count * 0.5)] if count > 0 else 0,
            'p95': response_times[int(count * 0.95)] if count > 0 else 0,
            'p99': response_times[int(count * 0.99)] if count > 0 else 0
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'success_rate': 0,
            'response_time_stats': self._calculate_response_time_stats([]),
            'error_breakdown': {},
            'retry_stats': {
                'total_retries': 0,
                'avg_retries_per_call': 0,
                'max_retries': 0
            },
            'circuit_breaker_triggers': 0
        }


class AgentCoreMonitoringService:
    """
    Comprehensive monitoring and observability service for AgentCore operations.
    
    Features:
    - Structured logging for agent invocations
    - Performance metrics tracking
    - Health checks for agent connectivity
    - Correlation ID management
    - Integration with existing logging infrastructure
    """
    
    def __init__(self, 
                 environment: str = "production",
                 enable_detailed_logging: bool = True,
                 enable_performance_tracking: bool = True,
                 enable_health_checks: bool = True):
        """
        Initialize the AgentCore monitoring service.
        
        Args:
            environment: Environment name for configuration
            enable_detailed_logging: Whether to enable detailed logging
            enable_performance_tracking: Whether to track performance metrics
            enable_health_checks: Whether to perform health checks
        """
        self.environment = environment
        self.enable_detailed_logging = enable_detailed_logging
        self.enable_performance_tracking = enable_performance_tracking
        self.enable_health_checks = enable_health_checks
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.logger = logging.getLogger(f"mbti_travel_planner.agentcore_monitoring")
        
        # Initialize specialized metrics collector
        self.metrics_collector = AgentCoreMetricsCollector()
        
        # Initialize health check service for AgentCore agents
        self.health_check_service = None
        if self.enable_health_checks:
            self._initialize_health_checks()
        
        # Correlation ID tracking
        self._correlation_context = threading.local()
        
        self.logger.info(f"AgentCore monitoring service initialized for {environment} environment")
    
    def _initialize_health_checks(self) -> None:
        """Initialize health check service with AgentCore agent endpoints."""
        self.health_check_service = HealthCheckService(
            environment=self.environment,
            enable_background_checks=True
        )
        
        # Add AgentCore agent health check endpoints
        # Note: These are synthetic health checks since AgentCore agents don't have direct health endpoints
        # We'll use minimal invocations to test connectivity
        
        self.logger.info("AgentCore health checks initialized")
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracing."""
        correlation_id = f"agentcore_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        self._correlation_context.correlation_id = correlation_id
        return correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID from thread-local storage."""
        return getattr(self._correlation_context, 'correlation_id', None)
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID in thread-local storage."""
        self._correlation_context.correlation_id = correlation_id
    
    def log_agent_invocation_start(self,
                                  agent_arn: str,
                                  operation_type: AgentOperationType,
                                  input_text: str,
                                  session_id: Optional[str] = None,
                                  user_id: Optional[str] = None,
                                  request_id: Optional[str] = None,
                                  correlation_id: Optional[str] = None) -> str:
        """
        Log the start of an AgentCore agent invocation.
        
        Args:
            agent_arn: ARN of the target agent
            operation_type: Type of operation being performed
            input_text: Input text for the agent
            session_id: Optional session ID
            user_id: Optional user ID
            request_id: Optional request ID
            correlation_id: Optional correlation ID (will generate if not provided)
            
        Returns:
            Correlation ID for tracking this invocation
        """
        if not correlation_id:
            correlation_id = self.generate_correlation_id()
        else:
            self.set_correlation_id(correlation_id)
        
        if not self.enable_detailed_logging:
            return correlation_id
        
        # Create invocation log entry
        invocation_log = AgentInvocationLog(
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_arn=agent_arn,
            operation_type=operation_type.value,
            input_size=len(input_text),
            session_id=session_id,
            user_id=user_id,
            request_id=request_id,
            environment=self.environment
        )
        
        # Log the invocation start
        self.logger.info(
            f"AgentCore invocation started",
            extra={
                "event_type": "agent_invocation_start",
                "correlation_id": correlation_id,
                "agent_arn": agent_arn,
                "operation_type": operation_type.value,
                "input_size": len(input_text),
                "session_id": session_id,
                "user_id": user_id,
                "request_id": request_id
            }
        )
        
        # Log structured data
        self.logging_service.logger.info(json.dumps(invocation_log.to_dict()))
        
        return correlation_id
    
    def log_agent_invocation_result(self,
                                   correlation_id: str,
                                   agent_arn: str,
                                   operation_type: AgentOperationType,
                                   response: Optional["AgentResponse"] = None,
                                   error: Optional[Exception] = None,
                                   retry_count: int = 0,
                                   circuit_breaker_triggered: bool = False) -> None:
        """
        Log the result of an AgentCore agent invocation.
        
        Args:
            correlation_id: Correlation ID from invocation start
            agent_arn: ARN of the target agent
            operation_type: Type of operation performed
            response: Agent response if successful
            error: Exception if failed
            retry_count: Number of retries attempted
            circuit_breaker_triggered: Whether circuit breaker was triggered
        """
        success = response is not None and error is None
        response_time_ms = response.execution_time_ms if response else 0
        output_size = len(response.output_text) if response else 0
        error_type = type(error).__name__ if error else None
        error_message = str(error) if error else None
        
        # Create result log entry
        result_log = AgentInvocationResult(
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            agent_arn=agent_arn,
            operation_type=operation_type.value,
            success=success,
            response_time_ms=response_time_ms,
            output_size=output_size,
            session_id=response.session_id if response else None,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count,
            circuit_breaker_triggered=circuit_breaker_triggered
        )
        
        # Log the result
        log_level = logging.INFO if success else logging.ERROR
        self.logger.log(
            log_level,
            f"AgentCore invocation {'completed' if success else 'failed'}",
            extra={
                "event_type": "agent_invocation_result",
                "correlation_id": correlation_id,
                "agent_arn": agent_arn,
                "operation_type": operation_type.value,
                "success": success,
                "response_time_ms": response_time_ms,
                "output_size": output_size,
                "error_type": error_type,
                "retry_count": retry_count,
                "circuit_breaker_triggered": circuit_breaker_triggered
            }
        )
        
        # Log structured data
        if self.enable_detailed_logging:
            self.logging_service.logger.info(json.dumps(result_log.to_dict()))
        
        # Record metrics
        if self.enable_performance_tracking:
            self.metrics_collector.record_invocation(
                agent_arn=agent_arn,
                operation_type=operation_type.value,
                response_time_ms=response_time_ms,
                success=success,
                error_type=error_type,
                retry_count=retry_count,
                circuit_breaker_triggered=circuit_breaker_triggered
            )
        
        # Log performance metrics to existing service
        self.logging_service.log_performance_metric(
            operation=f"agentcore_{operation_type.value}",
            duration=response_time_ms / 1000.0,
            success=success,
            error_type=error_type,
            additional_data={
                "correlation_id": correlation_id,
                "agent_arn": agent_arn,
                "retry_count": retry_count,
                "circuit_breaker_triggered": circuit_breaker_triggered
            }
        )
        
        # Log errors to existing service
        if error:
            self.logging_service.log_error(
                error=error,
                operation=f"agentcore_{operation_type.value}",
                context={
                    "correlation_id": correlation_id,
                    "agent_arn": agent_arn,
                    "retry_count": retry_count,
                    "circuit_breaker_triggered": circuit_breaker_triggered
                }
            )
    
    def log_authentication_event(self,
                                event_type: str,
                                success: bool,
                                error_message: Optional[str] = None,
                                correlation_id: Optional[str] = None) -> None:
        """
        Log authentication events for AgentCore operations.
        
        Args:
            event_type: Type of authentication event
            success: Whether the event was successful
            error_message: Error message if failed
            correlation_id: Optional correlation ID
        """
        if not correlation_id:
            correlation_id = self.get_correlation_id()
        
        # Log the authentication event
        log_level = logging.INFO if success else logging.WARNING
        self.logger.log(
            log_level,
            f"AgentCore authentication {event_type} {'succeeded' if success else 'failed'}",
            extra={
                "event_type": "agent_authentication",
                "auth_event_type": event_type,
                "success": success,
                "error_message": error_message,
                "correlation_id": correlation_id
            }
        )
        
        # Record authentication metrics
        if self.enable_performance_tracking:
            self.metrics_collector.record_authentication_event(
                event_type=event_type,
                success=success,
                error_message=error_message
            )
    
    async def perform_agent_health_check(self,
                                        agent_arn: str,
                                        agent_name: str,
                                        runtime_client: "AgentCoreRuntimeClient",
                                        test_input: str = "health check") -> AgentHealthCheckResult:
        """
        Perform a health check on an AgentCore agent.
        
        Args:
            agent_arn: ARN of the agent to check
            agent_name: Human-readable name of the agent
            runtime_client: AgentCore runtime client
            test_input: Test input for the health check
            
        Returns:
            AgentHealthCheckResult with the check results
        """
        start_time = time.time()
        correlation_id = self.generate_correlation_id()
        
        try:
            # Attempt to invoke the agent with minimal input
            response = await runtime_client.invoke_agent(
                agent_arn=agent_arn,
                input_text=test_input,
                session_id=f"health_check_{correlation_id}"
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine health status based on response
            if response and response.output_text:
                if response_time_ms < 5000:  # Less than 5 seconds
                    status = "healthy"
                elif response_time_ms < 15000:  # Less than 15 seconds
                    status = "degraded"
                else:
                    status = "unhealthy"
                error_message = None
            else:
                status = "unhealthy"
                error_message = "Empty or invalid response"
            
            result = AgentHealthCheckResult(
                agent_arn=agent_arn,
                agent_name=agent_name,
                status=status,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                test_input=test_input,
                test_output=response.output_text[:200] if response else None,  # Truncate for logging
                error_message=error_message,
                authentication_status="valid"  # If we got here, auth worked
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine authentication status from error
            auth_status = "unknown"
            if isinstance(e, AgentCoreError):
                if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                    auth_status = "invalid"
                elif "expired" in str(e).lower():
                    auth_status = "expired"
            
            result = AgentHealthCheckResult(
                agent_arn=agent_arn,
                agent_name=agent_name,
                status="unhealthy",
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                test_input=test_input,
                test_output=None,
                error_message=str(e),
                authentication_status=auth_status
            )
        
        # Log the health check result
        self.logger.info(
            f"AgentCore health check completed for {agent_name}",
            extra={
                "event_type": "agent_health_check",
                "agent_arn": agent_arn,
                "agent_name": agent_name,
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "authentication_status": result.authentication_status,
                "correlation_id": correlation_id
            }
        )
        
        # Log to existing health check service
        if self.health_check_service:
            self.logging_service.log_health_check(
                service_name=agent_name,
                endpoint=agent_arn,
                status=result.status,
                response_time_ms=result.response_time_ms,
                error_message=result.error_message,
                additional_info={
                    "authentication_status": result.authentication_status,
                    "test_input": test_input,
                    "correlation_id": correlation_id
                }
            )
        
        return result
    
    def get_agent_performance_summary(self, agent_arn: str, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance summary for a specific agent.
        
        Args:
            agent_arn: ARN of the agent
            window_minutes: Time window for metrics
            
        Returns:
            Performance summary dictionary
        """
        if not self.enable_performance_tracking:
            return {"error": "Performance tracking is disabled"}
        
        return self.metrics_collector.get_agent_metrics(agent_arn, window_minutes)
    
    def get_operation_performance_summary(self, operation_type: AgentOperationType, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance summary for a specific operation type.
        
        Args:
            operation_type: Type of operation
            window_minutes: Time window for metrics
            
        Returns:
            Performance summary dictionary
        """
        if not self.enable_performance_tracking:
            return {"error": "Performance tracking is disabled"}
        
        return self.metrics_collector.get_operation_metrics(operation_type.value, window_minutes)
    
    def get_authentication_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get authentication metrics summary.
        
        Args:
            window_minutes: Time window for metrics
            
        Returns:
            Authentication summary dictionary
        """
        if not self.enable_performance_tracking:
            return {"error": "Performance tracking is disabled"}
        
        return self.metrics_collector.get_authentication_metrics(window_minutes)
    
    def get_comprehensive_monitoring_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive monitoring report for all AgentCore operations.
        
        Returns:
            Comprehensive monitoring report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "monitoring_config": {
                "detailed_logging": self.enable_detailed_logging,
                "performance_tracking": self.enable_performance_tracking,
                "health_checks": self.enable_health_checks
            }
        }
        
        if self.enable_performance_tracking:
            # Get metrics for all known agents and operations
            agent_arns = [
                "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j",
                "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE"
            ]
            
            report["agent_metrics"] = {}
            for agent_arn in agent_arns:
                report["agent_metrics"][agent_arn] = self.get_agent_performance_summary(agent_arn)
            
            report["operation_metrics"] = {}
            for operation_type in AgentOperationType:
                report["operation_metrics"][operation_type.value] = self.get_operation_performance_summary(operation_type)
            
            report["authentication_metrics"] = self.get_authentication_summary()
        
        if self.health_check_service:
            report["health_status"] = self.health_check_service.get_overall_health_status()
        
        return report


# Global monitoring service instance
_agentcore_monitoring_service = None


def get_agentcore_monitoring_service() -> AgentCoreMonitoringService:
    """Get the global AgentCore monitoring service instance."""
    global _agentcore_monitoring_service
    if _agentcore_monitoring_service is None:
        _agentcore_monitoring_service = AgentCoreMonitoringService()
    return _agentcore_monitoring_service


def initialize_agentcore_monitoring_service(**kwargs) -> AgentCoreMonitoringService:
    """
    Initialize the global AgentCore monitoring service with custom configuration.
    
    Args:
        **kwargs: Configuration parameters for AgentCoreMonitoringService
        
    Returns:
        Initialized AgentCoreMonitoringService instance
    """
    global _agentcore_monitoring_service
    _agentcore_monitoring_service = AgentCoreMonitoringService(**kwargs)
    return _agentcore_monitoring_service


# Export main classes and functions
__all__ = [
    'AgentCoreMonitoringService',
    'AgentCoreMetricsCollector',
    'AgentOperationType',
    'AgentInvocationLog',
    'AgentInvocationResult',
    'AgentHealthCheckResult',
    'get_agentcore_monitoring_service',
    'initialize_agentcore_monitoring_service'
]