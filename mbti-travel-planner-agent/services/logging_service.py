"""
Comprehensive Logging and Monitoring Service for MBTI Travel Planner Agent

This module provides structured logging for HTTP requests and responses with timing information,
error logging with detailed stack traces and context information, performance logging for
monitoring response times and success rates, and health check logging for gateway connectivity
and service availability.

Features:
- Structured logging with JSON format for better parsing
- HTTP request/response logging with timing metrics
- Performance monitoring with configurable thresholds
- Health check logging for service availability
- Error logging with stack traces and context
- Metrics collection for monitoring dashboards
- Log rotation and retention management
"""

import json
import logging
import logging.handlers
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from collections import defaultdict, deque
import statistics

import httpx


class LogLevel(Enum):
    """Log levels for different types of events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HTTPRequestLog:
    """Structured log entry for HTTP requests."""
    timestamp: str
    method: str
    url: str
    headers: Dict[str, str]
    body_size: int
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class HTTPResponseLog:
    """Structured log entry for HTTP responses."""
    timestamp: str
    status_code: int
    response_size: int
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    error_type: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class HealthCheckResult:
    """Health check result data structure."""
    service_name: str
    endpoint: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time_ms: float
    timestamp: datetime
    error_message: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class MetricsCollector:
    """Thread-safe metrics collector for performance monitoring."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self._lock = threading.Lock()
        self._metrics = defaultdict(lambda: deque(maxlen=max_history))
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            self._gauges[key] = value
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None) -> None:
        """Record a timer metric."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            self._metrics[key].append({
                'value': duration,
                'timestamp': datetime.utcnow(),
                'type': MetricType.TIMER.value
            })
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a histogram metric."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            self._metrics[key].append({
                'value': value,
                'timestamp': datetime.utcnow(),
                'type': MetricType.HISTOGRAM.value
            })
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> int:
        """Get current counter value."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get current gauge value."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            return self._gauges.get(key, 0.0)
    
    def get_timer_stats(self, name: str, tags: Dict[str, str] = None, 
                       window_minutes: int = 60) -> Dict[str, float]:
        """Get timer statistics for the specified time window."""
        with self._lock:
            key = self._create_metric_key(name, tags)
            metrics = self._metrics.get(key, deque())
            
            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_values = [
                m['value'] for m in metrics 
                if m['timestamp'] > cutoff_time and m['type'] == MetricType.TIMER.value
            ]
            
            if not recent_values:
                return {'count': 0, 'min': 0, 'max': 0, 'mean': 0, 'p95': 0, 'p99': 0}
            
            recent_values.sort()
            count = len(recent_values)
            
            return {
                'count': count,
                'min': min(recent_values),
                'max': max(recent_values),
                'mean': statistics.mean(recent_values),
                'p95': recent_values[int(count * 0.95)] if count > 0 else 0,
                'p99': recent_values[int(count * 0.99)] if count > 0 else 0
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'metrics_count': {k: len(v) for k, v in self._metrics.items()}
            }
    
    def _create_metric_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for the metric including tags."""
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


class LoggingService:
    """
    Comprehensive logging and monitoring service for the MBTI Travel Planner Agent.
    
    Provides structured logging, performance monitoring, health checks, and metrics collection.
    """
    
    def __init__(self, 
                 service_name: str = "mbti_travel_planner",
                 log_level: str = "INFO",
                 log_dir: str = None,
                 enable_file_logging: bool = True,
                 enable_json_logging: bool = True,
                 max_log_files: int = 10,
                 max_log_size_mb: int = 100):
        """
        Initialize the logging service.
        
        Args:
            service_name: Name of the service for logging context
            log_level: Minimum log level to record
            log_dir: Directory for log files (defaults to ./logs)
            enable_file_logging: Whether to write logs to files
            enable_json_logging: Whether to use JSON format for structured logging
            max_log_files: Maximum number of log files to keep
            max_log_size_mb: Maximum size of each log file in MB
        """
        self.service_name = service_name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.enable_file_logging = enable_file_logging
        self.enable_json_logging = enable_json_logging
        
        # Create log directory
        if self.enable_file_logging:
            self.log_dir.mkdir(exist_ok=True)
        
        # Initialize metrics collector
        self.metrics = MetricsCollector()
        
        # Setup loggers
        self._setup_loggers(max_log_files, max_log_size_mb)
        
        # Performance thresholds (in seconds)
        self.performance_thresholds = {
            'http_request': 5.0,
            'gateway_operation': 10.0,
            'recommendation_analysis': 15.0,
            'health_check': 3.0
        }
        
        # Health check configuration
        self.health_check_interval = 300  # 5 minutes
        self.last_health_checks = {}
        
        self.logger.info(f"Logging service initialized for {service_name}")
        self.logger.info(f"Log level: {log_level}, File logging: {enable_file_logging}, JSON logging: {enable_json_logging}")
    
    def _setup_loggers(self, max_log_files: int, max_log_size_mb: int) -> None:
        """Setup logging configuration with appropriate handlers and formatters."""
        # Main application logger
        self.logger = logging.getLogger(f"{self.service_name}.main")
        self.logger.setLevel(self.log_level)
        
        # HTTP request/response logger
        self.http_logger = logging.getLogger(f"{self.service_name}.http")
        self.http_logger.setLevel(self.log_level)
        
        # Performance logger
        self.performance_logger = logging.getLogger(f"{self.service_name}.performance")
        self.performance_logger.setLevel(self.log_level)
        
        # Health check logger
        self.health_logger = logging.getLogger(f"{self.service_name}.health")
        self.health_logger.setLevel(self.log_level)
        
        # Error logger
        self.error_logger = logging.getLogger(f"{self.service_name}.error")
        self.error_logger.setLevel(logging.WARNING)
        
        # Setup formatters
        if self.enable_json_logging:
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": %(message)s}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.log_level)
        
        # Add console handler to all loggers
        for logger in [self.logger, self.http_logger, self.performance_logger, 
                      self.health_logger, self.error_logger]:
            if not logger.handlers:  # Avoid duplicate handlers
                logger.addHandler(console_handler)
        
        # File handlers (if enabled)
        if self.enable_file_logging:
            max_bytes = max_log_size_mb * 1024 * 1024
            
            # Main log file
            main_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "main.log",
                maxBytes=max_bytes,
                backupCount=max_log_files
            )
            main_handler.setFormatter(formatter)
            self.logger.addHandler(main_handler)
            
            # HTTP log file
            http_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "http.log",
                maxBytes=max_bytes,
                backupCount=max_log_files
            )
            http_handler.setFormatter(formatter)
            self.http_logger.addHandler(http_handler)
            
            # Performance log file
            perf_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "performance.log",
                maxBytes=max_bytes,
                backupCount=max_log_files
            )
            perf_handler.setFormatter(formatter)
            self.performance_logger.addHandler(perf_handler)
            
            # Health check log file
            health_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "health.log",
                maxBytes=max_bytes,
                backupCount=max_log_files
            )
            health_handler.setFormatter(formatter)
            self.health_logger.addHandler(health_handler)
            
            # Error log file
            error_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "errors.log",
                maxBytes=max_bytes,
                backupCount=max_log_files
            )
            error_handler.setFormatter(formatter)
            self.error_logger.addHandler(error_handler)
    
    def log_http_request(self, 
                        method: str,
                        url: str,
                        headers: Dict[str, str] = None,
                        body: Any = None,
                        request_id: str = None,
                        user_id: str = None,
                        session_id: str = None,
                        environment: str = None) -> str:
        """
        Log HTTP request with structured information.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers (sensitive headers will be masked)
            body: Request body
            request_id: Unique request identifier
            user_id: User identifier
            session_id: Session identifier
            environment: Environment name
            
        Returns:
            Request ID for correlation with response
        """
        # Generate request ID if not provided
        if not request_id:
            request_id = f"req_{int(time.time() * 1000)}_{id(self)}"
        
        # Mask sensitive headers
        safe_headers = self._mask_sensitive_headers(headers or {})
        
        # Calculate body size
        body_size = 0
        if body:
            if isinstance(body, (str, bytes)):
                body_size = len(body)
            elif isinstance(body, dict):
                body_size = len(json.dumps(body))
        
        # Create request log entry
        request_log = HTTPRequestLog(
            timestamp=datetime.utcnow().isoformat(),
            method=method,
            url=url,
            headers=safe_headers,
            body_size=body_size,
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            environment=environment
        )
        
        # Log the request
        if self.enable_json_logging:
            self.http_logger.info(json.dumps(request_log.to_dict()))
        else:
            self.http_logger.info(f"HTTP Request: {method} {url} [ID: {request_id}]")
        
        # Update metrics
        self.metrics.increment_counter("http_requests_total", tags={
            "method": method,
            "environment": environment or "unknown"
        })
        
        return request_id
    
    def log_http_response(self,
                         request_id: str,
                         status_code: int,
                         response_size: int = 0,
                         duration_ms: float = 0,
                         error_message: str = None) -> None:
        """
        Log HTTP response with timing and status information.
        
        Args:
            request_id: Request ID from log_http_request
            status_code: HTTP status code
            response_size: Response body size in bytes
            duration_ms: Request duration in milliseconds
            error_message: Error message if request failed
        """
        success = 200 <= status_code < 400
        
        # Create response log entry
        response_log = HTTPResponseLog(
            timestamp=datetime.utcnow().isoformat(),
            status_code=status_code,
            response_size=response_size,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            request_id=request_id
        )
        
        # Log the response
        if self.enable_json_logging:
            self.http_logger.info(json.dumps(response_log.to_dict()))
        else:
            status_text = "SUCCESS" if success else "ERROR"
            self.http_logger.info(f"HTTP Response: {status_code} {status_text} [{duration_ms:.2f}ms] [ID: {request_id}]")
        
        # Update metrics
        self.metrics.increment_counter("http_responses_total", tags={
            "status_code": str(status_code),
            "success": str(success).lower()
        })
        
        self.metrics.record_timer("http_request_duration", duration_ms / 1000.0, tags={
            "status_code": str(status_code)
        })
        
        # Log performance issues
        if duration_ms > self.performance_thresholds.get('http_request', 5.0) * 1000:
            self.log_performance_issue(
                operation="http_request",
                duration=duration_ms / 1000.0,
                threshold=self.performance_thresholds['http_request'],
                additional_data={
                    "request_id": request_id,
                    "status_code": status_code,
                    "response_size": response_size
                }
            )
    
    def log_performance_metric(self,
                             operation: str,
                             duration: float,
                             success: bool = True,
                             error_type: str = None,
                             additional_data: Dict[str, Any] = None) -> None:
        """
        Log performance metrics for operations.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            success: Whether the operation succeeded
            error_type: Type of error if operation failed
            additional_data: Additional context data
        """
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=datetime.utcnow(),
            success=success,
            error_type=error_type,
            additional_data=additional_data or {}
        )
        
        # Log the metric
        if self.enable_json_logging:
            self.performance_logger.info(json.dumps(metric.to_dict()))
        else:
            status = "SUCCESS" if success else f"ERROR ({error_type})"
            self.performance_logger.info(f"Performance: {operation} - {duration:.3f}s - {status}")
        
        # Update metrics
        self.metrics.record_timer(f"operation_duration", duration, tags={
            "operation": operation,
            "success": str(success).lower()
        })
        
        self.metrics.increment_counter("operations_total", tags={
            "operation": operation,
            "success": str(success).lower()
        })
        
        # Check for performance issues
        threshold = self.performance_thresholds.get(operation, 5.0)
        if duration > threshold:
            self.log_performance_issue(operation, duration, threshold, additional_data)
    
    def log_performance_issue(self,
                            operation: str,
                            duration: float,
                            threshold: float,
                            additional_data: Dict[str, Any] = None) -> None:
        """
        Log performance issues when operations exceed thresholds.
        
        Args:
            operation: Name of the operation
            duration: Actual duration in seconds
            threshold: Expected threshold in seconds
            additional_data: Additional context data
        """
        severity = "HIGH" if duration > threshold * 2 else "MEDIUM"
        
        issue_data = {
            "operation": operation,
            "duration": duration,
            "threshold": threshold,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "additional_data": additional_data or {}
        }
        
        if self.enable_json_logging:
            self.performance_logger.warning(json.dumps(issue_data))
        else:
            self.performance_logger.warning(
                f"Performance Issue: {operation} took {duration:.3f}s (threshold: {threshold}s) - {severity}"
            )
        
        # Update metrics
        self.metrics.increment_counter("performance_issues_total", tags={
            "operation": operation,
            "severity": severity.lower()
        })
    
    def log_error(self,
                 error: Exception,
                 operation: str,
                 context: Dict[str, Any] = None,
                 include_stack_trace: bool = True) -> None:
        """
        Log errors with detailed stack traces and context information.
        
        Args:
            error: The exception that occurred
            operation: The operation that failed
            context: Additional context information
            include_stack_trace: Whether to include full stack trace
        """
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        
        if include_stack_trace:
            error_data["stack_trace"] = traceback.format_exc()
        
        # Log the error
        if self.enable_json_logging:
            self.error_logger.error(json.dumps(error_data))
        else:
            self.error_logger.error(f"Error in {operation}: {type(error).__name__}: {str(error)}")
            if include_stack_trace:
                self.error_logger.error(f"Stack trace:\n{traceback.format_exc()}")
        
        # Update metrics
        self.metrics.increment_counter("errors_total", tags={
            "operation": operation,
            "error_type": type(error).__name__
        })
    
    def log_health_check(self,
                        service_name: str,
                        endpoint: str,
                        status: str,
                        response_time_ms: float,
                        error_message: str = None,
                        additional_info: Dict[str, Any] = None) -> None:
        """
        Log health check results for service availability monitoring.
        
        Args:
            service_name: Name of the service being checked
            endpoint: Health check endpoint
            status: Health status ("healthy", "unhealthy", "degraded")
            response_time_ms: Response time in milliseconds
            error_message: Error message if unhealthy
            additional_info: Additional health check information
        """
        health_result = HealthCheckResult(
            service_name=service_name,
            endpoint=endpoint,
            status=status,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow(),
            error_message=error_message,
            additional_info=additional_info or {}
        )
        
        # Store for tracking
        self.last_health_checks[service_name] = health_result
        
        # Log the health check
        if self.enable_json_logging:
            self.health_logger.info(json.dumps(health_result.to_dict()))
        else:
            self.health_logger.info(f"Health Check: {service_name} - {status.upper()} ({response_time_ms:.2f}ms)")
        
        # Update metrics
        self.metrics.set_gauge(f"service_health", 1.0 if status == "healthy" else 0.0, tags={
            "service": service_name
        })
        
        self.metrics.record_timer("health_check_duration", response_time_ms / 1000.0, tags={
            "service": service_name,
            "status": status
        })
        
        self.metrics.increment_counter("health_checks_total", tags={
            "service": service_name,
            "status": status
        })
    
    async def perform_health_check(self, service_name: str, endpoint: str, timeout: float = 5.0) -> HealthCheckResult:
        """
        Perform a health check on a service endpoint.
        
        Args:
            service_name: Name of the service
            endpoint: Health check endpoint URL
            timeout: Request timeout in seconds
            
        Returns:
            HealthCheckResult with the check results
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(endpoint)
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = "healthy"
                    error_message = None
                elif 200 <= response.status_code < 400:
                    status = "degraded"
                    error_message = f"Non-200 status: {response.status_code}"
                else:
                    status = "unhealthy"
                    error_message = f"HTTP {response.status_code}: {response.reason_phrase}"
                
                # Try to parse response for additional info
                additional_info = {}
                try:
                    if response.headers.get("content-type", "").startswith("application/json"):
                        additional_info = response.json()
                except:
                    pass
                
                result = HealthCheckResult(
                    service_name=service_name,
                    endpoint=endpoint,
                    status=status,
                    response_time_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    error_message=error_message,
                    additional_info=additional_info
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                service_name=service_name,
                endpoint=endpoint,
                status="unhealthy",
                response_time_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error_message=str(e),
                additional_info={"error_type": type(e).__name__}
            )
        
        # Log the health check result
        self.log_health_check(
            service_name=result.service_name,
            endpoint=result.endpoint,
            status=result.status,
            response_time_ms=result.response_time_ms,
            error_message=result.error_message,
            additional_info=result.additional_info
        )
        
        return result
    
    def get_service_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all service health checks.
        
        Returns:
            Dictionary with health status of all monitored services
        """
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "overall_status": "healthy"
        }
        
        unhealthy_count = 0
        degraded_count = 0
        
        for service_name, health_result in self.last_health_checks.items():
            summary["services"][service_name] = {
                "status": health_result.status,
                "response_time_ms": health_result.response_time_ms,
                "last_check": health_result.timestamp.isoformat(),
                "error_message": health_result.error_message
            }
            
            if health_result.status == "unhealthy":
                unhealthy_count += 1
            elif health_result.status == "degraded":
                degraded_count += 1
        
        # Determine overall status
        if unhealthy_count > 0:
            summary["overall_status"] = "unhealthy"
        elif degraded_count > 0:
            summary["overall_status"] = "degraded"
        
        summary["summary"] = {
            "total_services": len(self.last_health_checks),
            "healthy": len(self.last_health_checks) - unhealthy_count - degraded_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count
        }
        
        return summary
    
    def get_performance_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance metrics summary for the specified time window.
        
        Args:
            window_minutes: Time window in minutes
            
        Returns:
            Dictionary with performance statistics
        """
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "window_minutes": window_minutes,
            "operations": {},
            "http_requests": {},
            "overall_metrics": self.metrics.get_all_metrics()
        }
        
        # Get operation performance stats
        operations = ["gateway_operation", "recommendation_analysis", "health_check"]
        for operation in operations:
            stats = self.metrics.get_timer_stats(f"operation_duration", 
                                               tags={"operation": operation}, 
                                               window_minutes=window_minutes)
            if stats['count'] > 0:
                summary["operations"][operation] = stats
        
        # Get HTTP request stats
        http_stats = self.metrics.get_timer_stats("http_request_duration", 
                                                window_minutes=window_minutes)
        if http_stats['count'] > 0:
            summary["http_requests"] = http_stats
        
        return summary
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Mask sensitive information in HTTP headers.
        
        Args:
            headers: Original headers dictionary
            
        Returns:
            Headers with sensitive values masked
        """
        sensitive_headers = {
            'authorization', 'x-api-key', 'x-auth-token', 'cookie', 
            'x-forwarded-for', 'x-real-ip'
        }
        
        masked_headers = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                if key.lower() == 'authorization' and value.startswith('Bearer '):
                    masked_headers[key] = f"Bearer ***{value[-4:]}"
                else:
                    masked_headers[key] = "***MASKED***"
            else:
                masked_headers[key] = value
        
        return masked_headers
    
    def shutdown(self) -> None:
        """Shutdown the logging service and flush all handlers."""
        self.logger.info("Shutting down logging service")
        
        # Flush all handlers
        for logger in [self.logger, self.http_logger, self.performance_logger, 
                      self.health_logger, self.error_logger]:
            for handler in logger.handlers:
                handler.flush()
                if hasattr(handler, 'close'):
                    handler.close()


# Global logging service instance
_logging_service = None


def get_logging_service() -> LoggingService:
    """Get the global logging service instance."""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service


def initialize_logging_service(**kwargs) -> LoggingService:
    """
    Initialize the global logging service with custom configuration.
    
    Args:
        **kwargs: Configuration parameters for LoggingService
        
    Returns:
        Initialized LoggingService instance
    """
    global _logging_service
    _logging_service = LoggingService(**kwargs)
    return _logging_service


# Export main classes and functions
__all__ = [
    'LoggingService',
    'MetricsCollector',
    'HTTPRequestLog',
    'HTTPResponseLog',
    'PerformanceMetric',
    'HealthCheckResult',
    'LogLevel',
    'MetricType',
    'get_logging_service',
    'initialize_logging_service'
]