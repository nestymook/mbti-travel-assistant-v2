"""
Performance Monitor

This module provides comprehensive performance monitoring and metrics collection
for the tool orchestration system. It tracks tool usage, response times, success rates,
and generates performance reports for analysis and optimization.

Features:
- Tool invocation tracking with response times and success rates
- Performance report generation and analysis
- Integration with AgentCore monitoring service
- Historical performance data management
- Performance trend analysis and alerting
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import statistics

from .agentcore_monitoring_service import AgentCoreMonitoringService
from .orchestration_types import SelectedTool, OrchestrationResult


class PerformanceMetricType(Enum):
    """Types of performance metrics to track."""
    TOOL_INVOCATION = "tool_invocation"
    WORKFLOW_EXECUTION = "workflow_execution"
    INTENT_ANALYSIS = "intent_analysis"
    TOOL_SELECTION = "tool_selection"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class ToolInvocationMetric:
    """Metrics for a single tool invocation."""
    tool_id: str
    tool_name: str
    correlation_id: str
    timestamp: datetime
    response_time_ms: float
    success: bool
    input_size: int
    output_size: int
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class WorkflowExecutionMetric:
    """Metrics for workflow execution."""
    workflow_id: str
    correlation_id: str
    timestamp: datetime
    total_execution_time_ms: float
    tools_used: List[str]
    success: bool
    steps_completed: int
    total_steps: int
    error_type: Optional[str] = None
    fallback_workflows_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    report_id: str
    generated_at: datetime
    time_window_minutes: int
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    overall_success_rate: float
    average_response_time_ms: float
    tool_performance: Dict[str, Dict[str, Any]]
    workflow_performance: Dict[str, Dict[str, Any]]
    error_analysis: Dict[str, Any]
    performance_trends: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for tool orchestration.
    
    Features:
    - Tool invocation tracking with detailed metrics
    - Performance report generation and analysis
    - Integration with AgentCore monitoring service
    - Historical performance data management
    - Performance trend analysis and alerting
    """
    
    def __init__(self, 
                 monitoring_service: Optional[AgentCoreMonitoringService] = None,
                 max_history: int = 10000,
                 enable_detailed_tracking: bool = True,
                 enable_trend_analysis: bool = True):
        """
        Initialize the performance monitor.
        
        Args:
            monitoring_service: AgentCore monitoring service for integration
            max_history: Maximum number of metrics to keep in memory
            enable_detailed_tracking: Whether to enable detailed performance tracking
            enable_trend_analysis: Whether to enable performance trend analysis
        """
        self.monitoring_service = monitoring_service
        self.max_history = max_history
        self.enable_detailed_tracking = enable_detailed_tracking
        self.enable_trend_analysis = enable_trend_analysis
        
        # Initialize logger
        self.logger = logging.getLogger(f"mbti_travel_planner.performance_monitor")
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Metrics storage
        self._tool_metrics = deque(maxlen=max_history)
        self._workflow_metrics = deque(maxlen=max_history)
        
        # Performance counters
        self._tool_counters = defaultdict(lambda: {
            'invocations': 0,
            'successes': 0,
            'failures': 0,
            'total_response_time': 0.0,
            'error_types': defaultdict(int)
        })
        
        self._workflow_counters = defaultdict(lambda: {
            'executions': 0,
            'successes': 0,
            'failures': 0,
            'total_execution_time': 0.0,
            'total_steps': 0,
            'completed_steps': 0
        })
        
        # Performance thresholds for alerting
        self._performance_thresholds = {
            'max_response_time_ms': 30000,  # 30 seconds
            'min_success_rate': 0.95,  # 95%
            'max_error_rate': 0.05,  # 5%
            'max_workflow_time_ms': 60000  # 60 seconds
        }
        
        # Trend analysis data
        self._performance_history = deque(maxlen=1000)
        
        self.logger.info("Performance monitor initialized")
    
    def track_tool_invocation(self,
                             tool: SelectedTool,
                             correlation_id: str,
                             response_time_ms: float,
                             success: bool,
                             input_size: int = 0,
                             output_size: int = 0,
                             error_type: Optional[str] = None,
                             error_message: Optional[str] = None,
                             retry_count: int = 0,
                             fallback_used: bool = False) -> None:
        """
        Track a tool invocation for performance monitoring.
        
        Args:
            tool: Selected tool that was invoked
            correlation_id: Correlation ID for request tracing
            response_time_ms: Response time in milliseconds
            success: Whether the invocation was successful
            input_size: Size of input data in bytes
            output_size: Size of output data in bytes
            error_type: Type of error if failed
            error_message: Error message if failed
            retry_count: Number of retries attempted
            fallback_used: Whether fallback tool was used
        """
        if not self.enable_detailed_tracking:
            return
        
        timestamp = datetime.utcnow()
        
        # Create metric record
        metric = ToolInvocationMetric(
            tool_id=tool.tool_id,
            tool_name=tool.tool_name,
            correlation_id=correlation_id,
            timestamp=timestamp,
            response_time_ms=response_time_ms,
            success=success,
            input_size=input_size,
            output_size=output_size,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count,
            fallback_used=fallback_used
        )
        
        with self._lock:
            # Store metric
            self._tool_metrics.append(metric)
            
            # Update counters
            tool_key = f"{tool.tool_id}:{tool.tool_name}"
            counters = self._tool_counters[tool_key]
            counters['invocations'] += 1
            counters['total_response_time'] += response_time_ms
            
            if success:
                counters['successes'] += 1
            else:
                counters['failures'] += 1
                if error_type:
                    counters['error_types'][error_type] += 1
        
        # Log the metric
        self.logger.info(
            f"Tool invocation tracked: {tool.tool_name} "
            f"({'success' if success else 'failure'}) "
            f"in {response_time_ms:.2f}ms",
            extra={
                "event_type": "tool_invocation_tracked",
                "correlation_id": correlation_id,
                "tool_id": tool.tool_id,
                "tool_name": tool.tool_name,
                "response_time_ms": response_time_ms,
                "success": success,
                "retry_count": retry_count,
                "fallback_used": fallback_used
            }
        )
        
        # Integrate with AgentCore monitoring if available
        if self.monitoring_service:
            try:
                # Log as custom metric to AgentCore monitoring
                self.monitoring_service.logger.info(
                    f"Tool performance metric",
                    extra={
                        "metric_type": "tool_performance",
                        "tool_metric": metric.to_dict()
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to log to AgentCore monitoring: {e}")
        
        # Check performance thresholds
        self._check_performance_thresholds(tool, response_time_ms, success)
    
    def track_workflow_execution(self,
                                workflow_id: str,
                                correlation_id: str,
                                execution_time_ms: float,
                                tools_used: List[str],
                                success: bool,
                                steps_completed: int,
                                total_steps: int,
                                error_type: Optional[str] = None,
                                fallback_workflows_used: int = 0) -> None:
        """
        Track workflow execution for performance monitoring.
        
        Args:
            workflow_id: ID of the executed workflow
            correlation_id: Correlation ID for request tracing
            execution_time_ms: Total execution time in milliseconds
            tools_used: List of tools used in the workflow
            success: Whether the workflow was successful
            steps_completed: Number of steps completed
            total_steps: Total number of steps in workflow
            error_type: Type of error if failed
            fallback_workflows_used: Number of fallback workflows used
        """
        if not self.enable_detailed_tracking:
            return
        
        timestamp = datetime.utcnow()
        
        # Create metric record
        metric = WorkflowExecutionMetric(
            workflow_id=workflow_id,
            correlation_id=correlation_id,
            timestamp=timestamp,
            total_execution_time_ms=execution_time_ms,
            tools_used=tools_used,
            success=success,
            steps_completed=steps_completed,
            total_steps=total_steps,
            error_type=error_type,
            fallback_workflows_used=fallback_workflows_used
        )
        
        with self._lock:
            # Store metric
            self._workflow_metrics.append(metric)
            
            # Update counters
            counters = self._workflow_counters[workflow_id]
            counters['executions'] += 1
            counters['total_execution_time'] += execution_time_ms
            counters['total_steps'] += total_steps
            counters['completed_steps'] += steps_completed
            
            if success:
                counters['successes'] += 1
            else:
                counters['failures'] += 1
        
        # Log the metric
        self.logger.info(
            f"Workflow execution tracked: {workflow_id} "
            f"({'success' if success else 'failure'}) "
            f"in {execution_time_ms:.2f}ms "
            f"({steps_completed}/{total_steps} steps)",
            extra={
                "event_type": "workflow_execution_tracked",
                "correlation_id": correlation_id,
                "workflow_id": workflow_id,
                "execution_time_ms": execution_time_ms,
                "success": success,
                "steps_completed": steps_completed,
                "total_steps": total_steps,
                "tools_used": tools_used
            }
        )
    
    def get_tool_performance_metrics(self, 
                                   tool_id: Optional[str] = None,
                                   time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance metrics for tools.
        
        Args:
            tool_id: Optional specific tool ID to get metrics for
            time_window_minutes: Time window for metrics in minutes
            
        Returns:
            Dictionary containing performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            # Filter metrics by time window
            recent_metrics = [
                m for m in self._tool_metrics
                if m.timestamp > cutoff_time
            ]
            
            # Filter by tool ID if specified
            if tool_id:
                recent_metrics = [
                    m for m in recent_metrics
                    if m.tool_id == tool_id
                ]
            
            if not recent_metrics:
                return self._empty_tool_metrics()
            
            # Calculate overall statistics
            total_invocations = len(recent_metrics)
            successful_invocations = sum(1 for m in recent_metrics if m.success)
            failed_invocations = total_invocations - successful_invocations
            
            response_times = [m.response_time_ms for m in recent_metrics]
            response_times.sort()
            
            # Tool-specific breakdown
            tool_breakdown = defaultdict(lambda: {
                'invocations': 0,
                'successes': 0,
                'failures': 0,
                'response_times': [],
                'error_types': defaultdict(int),
                'retry_counts': [],
                'fallback_usage': 0
            })
            
            for metric in recent_metrics:
                tool_key = f"{metric.tool_id}:{metric.tool_name}"
                breakdown = tool_breakdown[tool_key]
                breakdown['invocations'] += 1
                breakdown['response_times'].append(metric.response_time_ms)
                breakdown['retry_counts'].append(metric.retry_count)
                
                if metric.success:
                    breakdown['successes'] += 1
                else:
                    breakdown['failures'] += 1
                    if metric.error_type:
                        breakdown['error_types'][metric.error_type] += 1
                
                if metric.fallback_used:
                    breakdown['fallback_usage'] += 1
            
            # Calculate statistics for each tool
            tool_stats = {}
            for tool_key, breakdown in tool_breakdown.items():
                response_times = breakdown['response_times']
                response_times.sort()
                
                tool_stats[tool_key] = {
                    'invocations': breakdown['invocations'],
                    'success_rate': (breakdown['successes'] / breakdown['invocations']) * 100,
                    'failure_rate': (breakdown['failures'] / breakdown['invocations']) * 100,
                    'response_time_stats': self._calculate_response_time_stats(response_times),
                    'error_breakdown': dict(breakdown['error_types']),
                    'average_retries': statistics.mean(breakdown['retry_counts']) if breakdown['retry_counts'] else 0,
                    'fallback_usage_rate': (breakdown['fallback_usage'] / breakdown['invocations']) * 100
                }
            
            return {
                'time_window_minutes': time_window_minutes,
                'total_invocations': total_invocations,
                'successful_invocations': successful_invocations,
                'failed_invocations': failed_invocations,
                'overall_success_rate': (successful_invocations / total_invocations) * 100,
                'overall_response_time_stats': self._calculate_response_time_stats(response_times),
                'tool_breakdown': tool_stats
            }
    
    def get_workflow_performance_metrics(self, 
                                       workflow_id: Optional[str] = None,
                                       time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance metrics for workflows.
        
        Args:
            workflow_id: Optional specific workflow ID to get metrics for
            time_window_minutes: Time window for metrics in minutes
            
        Returns:
            Dictionary containing workflow performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            # Filter metrics by time window
            recent_metrics = [
                m for m in self._workflow_metrics
                if m.timestamp > cutoff_time
            ]
            
            # Filter by workflow ID if specified
            if workflow_id:
                recent_metrics = [
                    m for m in recent_metrics
                    if m.workflow_id == workflow_id
                ]
            
            if not recent_metrics:
                return self._empty_workflow_metrics()
            
            # Calculate overall statistics
            total_executions = len(recent_metrics)
            successful_executions = sum(1 for m in recent_metrics if m.success)
            failed_executions = total_executions - successful_executions
            
            execution_times = [m.total_execution_time_ms for m in recent_metrics]
            execution_times.sort()
            
            # Workflow-specific breakdown
            workflow_breakdown = defaultdict(lambda: {
                'executions': 0,
                'successes': 0,
                'failures': 0,
                'execution_times': [],
                'completion_rates': [],
                'tools_used': set(),
                'fallback_usage': 0
            })
            
            for metric in recent_metrics:
                breakdown = workflow_breakdown[metric.workflow_id]
                breakdown['executions'] += 1
                breakdown['execution_times'].append(metric.total_execution_time_ms)
                breakdown['tools_used'].update(metric.tools_used)
                breakdown['fallback_usage'] += metric.fallback_workflows_used
                
                completion_rate = (metric.steps_completed / metric.total_steps) * 100 if metric.total_steps > 0 else 0
                breakdown['completion_rates'].append(completion_rate)
                
                if metric.success:
                    breakdown['successes'] += 1
                else:
                    breakdown['failures'] += 1
            
            # Calculate statistics for each workflow
            workflow_stats = {}
            for wf_id, breakdown in workflow_breakdown.items():
                execution_times = breakdown['execution_times']
                execution_times.sort()
                
                workflow_stats[wf_id] = {
                    'executions': breakdown['executions'],
                    'success_rate': (breakdown['successes'] / breakdown['executions']) * 100,
                    'failure_rate': (breakdown['failures'] / breakdown['executions']) * 100,
                    'execution_time_stats': self._calculate_response_time_stats(execution_times),
                    'average_completion_rate': statistics.mean(breakdown['completion_rates']) if breakdown['completion_rates'] else 0,
                    'unique_tools_used': len(breakdown['tools_used']),
                    'tools_used': list(breakdown['tools_used']),
                    'fallback_usage': breakdown['fallback_usage']
                }
            
            return {
                'time_window_minutes': time_window_minutes,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'overall_success_rate': (successful_executions / total_executions) * 100,
                'overall_execution_time_stats': self._calculate_response_time_stats(execution_times),
                'workflow_breakdown': workflow_stats
            }
    
    def generate_performance_report(self, 
                                  time_window_minutes: int = 60,
                                  include_recommendations: bool = True) -> PerformanceReport:
        """
        Generate a comprehensive performance report.
        
        Args:
            time_window_minutes: Time window for the report in minutes
            include_recommendations: Whether to include performance recommendations
            
        Returns:
            PerformanceReport with comprehensive analysis
        """
        report_id = f"perf_report_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        generated_at = datetime.utcnow()
        
        # Get tool and workflow metrics
        tool_metrics = self.get_tool_performance_metrics(time_window_minutes=time_window_minutes)
        workflow_metrics = self.get_workflow_performance_metrics(time_window_minutes=time_window_minutes)
        
        # Calculate overall statistics
        total_invocations = tool_metrics['total_invocations']
        successful_invocations = tool_metrics['successful_invocations']
        failed_invocations = tool_metrics['failed_invocations']
        overall_success_rate = tool_metrics['overall_success_rate']
        
        # Calculate average response time
        if tool_metrics['overall_response_time_stats']['count'] > 0:
            average_response_time_ms = tool_metrics['overall_response_time_stats']['mean']
        else:
            average_response_time_ms = 0.0
        
        # Analyze errors
        error_analysis = self._analyze_errors(time_window_minutes)
        
        # Analyze performance trends if enabled
        performance_trends = {}
        if self.enable_trend_analysis:
            performance_trends = self._analyze_performance_trends(time_window_minutes)
        
        # Generate recommendations
        recommendations = []
        if include_recommendations:
            recommendations = self._generate_recommendations(
                tool_metrics, workflow_metrics, error_analysis, performance_trends
            )
        
        # Create report
        report = PerformanceReport(
            report_id=report_id,
            generated_at=generated_at,
            time_window_minutes=time_window_minutes,
            total_invocations=total_invocations,
            successful_invocations=successful_invocations,
            failed_invocations=failed_invocations,
            overall_success_rate=overall_success_rate,
            average_response_time_ms=average_response_time_ms,
            tool_performance=tool_metrics['tool_breakdown'],
            workflow_performance=workflow_metrics['workflow_breakdown'],
            error_analysis=error_analysis,
            performance_trends=performance_trends,
            recommendations=recommendations
        )
        
        # Log report generation
        self.logger.info(
            f"Performance report generated: {report_id}",
            extra={
                "event_type": "performance_report_generated",
                "report_id": report_id,
                "time_window_minutes": time_window_minutes,
                "total_invocations": total_invocations,
                "overall_success_rate": overall_success_rate,
                "average_response_time_ms": average_response_time_ms
            }
        )
        
        return report
    
    def _check_performance_thresholds(self, 
                                    tool: SelectedTool,
                                    response_time_ms: float,
                                    success: bool) -> None:
        """Check if performance thresholds are exceeded and alert if necessary."""
        alerts = []
        
        # Check response time threshold
        if response_time_ms > self._performance_thresholds['max_response_time_ms']:
            alerts.append(f"Tool {tool.tool_name} exceeded response time threshold: {response_time_ms:.2f}ms")
        
        # Check success rate (requires recent history)
        with self._lock:
            recent_metrics = [
                m for m in self._tool_metrics
                if m.tool_id == tool.tool_id and 
                   m.timestamp > datetime.utcnow() - timedelta(minutes=10)
            ]
            
            if len(recent_metrics) >= 5:  # Only check if we have enough data
                success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
                if success_rate < self._performance_thresholds['min_success_rate']:
                    alerts.append(f"Tool {tool.tool_name} success rate below threshold: {success_rate:.2%}")
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(
                f"Performance threshold exceeded: {alert}",
                extra={
                    "event_type": "performance_threshold_exceeded",
                    "tool_id": tool.tool_id,
                    "tool_name": tool.tool_name,
                    "alert_message": alert
                }
            )
    
    def _analyze_errors(self, time_window_minutes: int) -> Dict[str, Any]:
        """Analyze error patterns in the specified time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            failed_metrics = [
                m for m in self._tool_metrics
                if not m.success and m.timestamp > cutoff_time
            ]
        
        if not failed_metrics:
            return {'total_errors': 0, 'error_types': {}, 'error_trends': {}}
        
        # Analyze error types
        error_types = defaultdict(int)
        error_by_tool = defaultdict(int)
        
        for metric in failed_metrics:
            if metric.error_type:
                error_types[metric.error_type] += 1
            error_by_tool[f"{metric.tool_id}:{metric.tool_name}"] += 1
        
        return {
            'total_errors': len(failed_metrics),
            'error_types': dict(error_types),
            'errors_by_tool': dict(error_by_tool),
            'error_rate': len(failed_metrics) / len(self._tool_metrics) if self._tool_metrics else 0
        }
    
    def _analyze_performance_trends(self, time_window_minutes: int) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not self.enable_trend_analysis:
            return {}
        
        # This is a simplified trend analysis
        # In a production system, you might want more sophisticated trend detection
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self._lock:
            recent_metrics = [
                m for m in self._tool_metrics
                if m.timestamp > cutoff_time
            ]
        
        if len(recent_metrics) < 10:  # Need minimum data for trend analysis
            return {'insufficient_data': True}
        
        # Split into time buckets for trend analysis
        bucket_size_minutes = max(1, time_window_minutes // 10)
        buckets = defaultdict(list)
        
        for metric in recent_metrics:
            bucket_key = int((metric.timestamp - cutoff_time).total_seconds() // (bucket_size_minutes * 60))
            buckets[bucket_key].append(metric)
        
        # Calculate trends
        bucket_stats = []
        for bucket_key in sorted(buckets.keys()):
            bucket_metrics = buckets[bucket_key]
            success_rate = sum(1 for m in bucket_metrics if m.success) / len(bucket_metrics)
            avg_response_time = statistics.mean(m.response_time_ms for m in bucket_metrics)
            
            bucket_stats.append({
                'bucket': bucket_key,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'count': len(bucket_metrics)
            })
        
        return {
            'bucket_size_minutes': bucket_size_minutes,
            'bucket_stats': bucket_stats,
            'trend_analysis': 'basic'  # Placeholder for more sophisticated analysis
        }
    
    def _generate_recommendations(self, 
                                tool_metrics: Dict[str, Any],
                                workflow_metrics: Dict[str, Any],
                                error_analysis: Dict[str, Any],
                                performance_trends: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze tool performance
        for tool_key, stats in tool_metrics.get('tool_breakdown', {}).items():
            if stats['success_rate'] < 90:
                recommendations.append(
                    f"Tool {tool_key} has low success rate ({stats['success_rate']:.1f}%). "
                    f"Consider investigating error causes or implementing better fallbacks."
                )
            
            if stats['response_time_stats']['p95'] > 10000:  # 10 seconds
                recommendations.append(
                    f"Tool {tool_key} has high response times (P95: {stats['response_time_stats']['p95']:.0f}ms). "
                    f"Consider optimizing or implementing caching."
                )
            
            if stats['fallback_usage_rate'] > 20:
                recommendations.append(
                    f"Tool {tool_key} has high fallback usage ({stats['fallback_usage_rate']:.1f}%). "
                    f"Consider improving primary tool reliability."
                )
        
        # Analyze workflow performance
        for workflow_id, stats in workflow_metrics.get('workflow_breakdown', {}).items():
            if stats['success_rate'] < 95:
                recommendations.append(
                    f"Workflow {workflow_id} has low success rate ({stats['success_rate']:.1f}%). "
                    f"Consider reviewing workflow design and error handling."
                )
            
            if stats['average_completion_rate'] < 90:
                recommendations.append(
                    f"Workflow {workflow_id} has low completion rate ({stats['average_completion_rate']:.1f}%). "
                    f"Consider optimizing workflow steps or timeouts."
                )
        
        # Analyze error patterns
        if error_analysis.get('error_rate', 0) > 0.1:  # 10% error rate
            recommendations.append(
                f"Overall error rate is high ({error_analysis['error_rate']:.1%}). "
                f"Consider implementing better error handling and monitoring."
            )
        
        # Add general recommendations if no specific issues found
        if not recommendations:
            recommendations.append("Performance is within acceptable thresholds. Continue monitoring.")
        
        return recommendations
    
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
    
    def _empty_tool_metrics(self) -> Dict[str, Any]:
        """Return empty tool metrics structure."""
        return {
            'time_window_minutes': 0,
            'total_invocations': 0,
            'successful_invocations': 0,
            'failed_invocations': 0,
            'overall_success_rate': 0,
            'overall_response_time_stats': self._calculate_response_time_stats([]),
            'tool_breakdown': {}
        }
    
    def _empty_workflow_metrics(self) -> Dict[str, Any]:
        """Return empty workflow metrics structure."""
        return {
            'time_window_minutes': 0,
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'overall_success_rate': 0,
            'overall_execution_time_stats': self._calculate_response_time_stats([]),
            'workflow_breakdown': {}
        }


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def initialize_performance_monitor(monitoring_service: Optional[AgentCoreMonitoringService] = None,
                                 **kwargs) -> PerformanceMonitor:
    """Initialize the global performance monitor instance."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(monitoring_service=monitoring_service, **kwargs)
    return _performance_monitor