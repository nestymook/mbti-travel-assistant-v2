"""
Comprehensive Error Logging and Monitoring Service

This module provides comprehensive error logging and monitoring capabilities
for the MBTI Travel Assistant system, including structured logging,
error correlation, alerting, and performance monitoring.

Requirements: 9.7
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import traceback
from pathlib import Path
import uuid

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert types for monitoring."""
    ERROR_RATE_HIGH = "error_rate_high"
    SERVICE_DOWN = "service_down"
    RESPONSE_TIME_HIGH = "response_time_high"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CACHE_MISS_RATE_HIGH = "cache_miss_rate_high"
    MEMORY_USAGE_HIGH = "memory_usage_high"


@dataclass
class ErrorEvent:
    """Structured error event."""
    id: str
    timestamp: datetime
    service_name: str
    operation_name: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    stack_trace: Optional[str]
    context: Dict[str, Any]
    correlation_id: Optional[str]
    user_id: Optional[str]
    request_id: Optional[str]
    response_time_ms: float
    retry_count: int = 0
    resolved: bool = False


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    timestamp: datetime
    service_name: str
    operation_name: str
    response_time_ms: float
    success: bool
    error_type: Optional[str] = None


@dataclass
class Alert:
    """System alert."""
    id: str
    timestamp: datetime
    alert_type: AlertType
    severity: ErrorSeverity
    title: str
    description: str
    service_name: str
    threshold_value: float
    current_value: float
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class MonitoringConfig:
    """Configuration for error monitoring."""
    error_rate_threshold: float = 10.0  # Percentage
    response_time_threshold_ms: float = 5000.0
    cache_miss_rate_threshold: float = 50.0  # Percentage
    memory_usage_threshold_mb: float = 500.0
    alert_cooldown_minutes: int = 15
    log_retention_days: int = 30
    enable_structured_logging: bool = True
    enable_performance_tracking: bool = True
    enable_alerting: bool = True


class ComprehensiveErrorMonitor:
    """
    Comprehensive error logging and monitoring service.
    
    This service provides:
    - Structured error logging with correlation
    - Performance metrics collection
    - Real-time alerting based on thresholds
    - Error pattern analysis
    - Automated error correlation and grouping
    - Health status monitoring
    """
    
    def __init__(
        self,
        config: Optional[MonitoringConfig] = None,
        log_directory: str = "logs"
    ):
        """Initialize comprehensive error monitor.
        
        Args:
            config: Monitoring configuration
            log_directory: Directory for log files
        """
        self.config = config or MonitoringConfig()
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self._error_events: List[ErrorEvent] = []
        self._error_patterns: Dict[str, List[ErrorEvent]] = {}
        self._error_correlations: Dict[str, Set[str]] = {}
        
        # Performance tracking
        self._performance_metrics: List[PerformanceMetric] = []
        self._service_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Alerting
        self._alerts: List[Alert] = []
        self._alert_cooldowns: Dict[str, datetime] = {}
        self._alert_handlers: List[Callable[[Alert], None]] = []
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize structured logging
        if self.config.enable_structured_logging:
            self._setup_structured_logging()
        
        logger.info(
            "Comprehensive Error Monitor initialized",
            config=asdict(self.config),
            log_directory=str(self.log_directory)
        )
    
    def _setup_structured_logging(self) -> None:
        """Setup structured logging configuration."""
        try:
            # Configure structured logging with JSON format
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_directory / "application.log"),
                    logging.StreamHandler()
                ]
            )
            
            # Create separate error log file
            error_handler = logging.FileHandler(self.log_directory / "errors.log")
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            error_handler.setFormatter(error_formatter)
            
            # Add error handler to root logger
            logging.getLogger().addHandler(error_handler)
            
        except Exception as e:
            logger.warning(
                "Failed to setup structured logging",
                error=str(e)
            )
    
    async def start(self) -> None:
        """Start monitoring background tasks."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Comprehensive error monitor started")
    
    async def stop(self) -> None:
        """Stop monitoring background tasks."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Persist final logs
        await self._persist_logs()
        
        logger.info("Comprehensive error monitor stopped")
    
    async def log_error(
        self,
        service_name: str,
        operation_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        response_time_ms: float = 0.0,
        retry_count: int = 0
    ) -> str:
        """Log an error event with comprehensive context.
        
        Args:
            service_name: Name of the service where error occurred
            operation_name: Name of the operation that failed
            error: The exception that occurred
            context: Additional context information
            correlation_id: Request correlation ID
            user_id: User ID if available
            request_id: Request ID if available
            response_time_ms: Response time when error occurred
            retry_count: Number of retries attempted
            
        Returns:
            Error event ID
        """
        error_id = str(uuid.uuid4())
        severity = self._classify_error_severity(error)
        
        error_event = ErrorEvent(
            id=error_id,
            timestamp=datetime.now(),
            service_name=service_name,
            operation_name=operation_name,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            stack_trace=traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None,
            context=context or {},
            correlation_id=correlation_id,
            user_id=user_id,
            request_id=request_id,
            response_time_ms=response_time_ms,
            retry_count=retry_count
        )
        
        # Store error event
        self._error_events.append(error_event)
        
        # Update error patterns
        await self._update_error_patterns(error_event)
        
        # Check for correlations
        await self._check_error_correlations(error_event)
        
        # Update service metrics
        await self._update_service_error_metrics(service_name, error_event)
        
        # Check for alerts
        if self.config.enable_alerting:
            await self._check_error_alerts(service_name, error_event)
        
        # Log structured error
        logger.error(
            "Error logged",
            error_id=error_id,
            service_name=service_name,
            operation_name=operation_name,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity.value,
            correlation_id=correlation_id,
            user_id=user_id,
            request_id=request_id,
            response_time_ms=response_time_ms,
            retry_count=retry_count,
            context=context
        )
        
        return error_id
    
    async def log_performance_metric(
        self,
        service_name: str,
        operation_name: str,
        response_time_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ) -> None:
        """Log a performance metric.
        
        Args:
            service_name: Name of the service
            operation_name: Name of the operation
            response_time_ms: Response time in milliseconds
            success: Whether the operation was successful
            error_type: Type of error if operation failed
        """
        if not self.config.enable_performance_tracking:
            return
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            service_name=service_name,
            operation_name=operation_name,
            response_time_ms=response_time_ms,
            success=success,
            error_type=error_type
        )
        
        self._performance_metrics.append(metric)
        
        # Update service metrics
        await self._update_service_performance_metrics(service_name, metric)
        
        # Check for performance alerts
        if self.config.enable_alerting:
            await self._check_performance_alerts(service_name, metric)
        
        logger.debug(
            "Performance metric logged",
            service_name=service_name,
            operation_name=operation_name,
            response_time_ms=response_time_ms,
            success=success,
            error_type=error_type
        )
    
    def _classify_error_severity(self, error: Exception) -> ErrorSeverity:
        """Classify error severity based on error type and message.
        
        Args:
            error: Exception to classify
            
        Returns:
            ErrorSeverity enum value
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if any(keyword in error_str for keyword in [
            'authentication', 'authorization', 'security', 'credential'
        ]):
            return ErrorSeverity.CRITICAL
        
        if any(keyword in error_type for keyword in [
            'security', 'authentication', 'authorization'
        ]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_str for keyword in [
            'connection', 'timeout', 'unavailable', 'service'
        ]):
            return ErrorSeverity.HIGH
        
        if any(keyword in error_type for keyword in [
            'connection', 'timeout', 'service'
        ]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_str for keyword in [
            'validation', 'parsing', 'format'
        ]):
            return ErrorSeverity.MEDIUM
        
        if any(keyword in error_type for keyword in [
            'value', 'type', 'attribute'
        ]):
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    async def _update_error_patterns(self, error_event: ErrorEvent) -> None:
        """Update error patterns for analysis."""
        pattern_key = f"{error_event.service_name}:{error_event.error_type}"
        
        if pattern_key not in self._error_patterns:
            self._error_patterns[pattern_key] = []
        
        self._error_patterns[pattern_key].append(error_event)
        
        # Keep only recent patterns (last 100 errors per pattern)
        if len(self._error_patterns[pattern_key]) > 100:
            self._error_patterns[pattern_key] = self._error_patterns[pattern_key][-100:]
    
    async def _check_error_correlations(self, error_event: ErrorEvent) -> None:
        """Check for error correlations across services."""
        if not error_event.correlation_id:
            return
        
        correlation_id = error_event.correlation_id
        
        if correlation_id not in self._error_correlations:
            self._error_correlations[correlation_id] = set()
        
        self._error_correlations[correlation_id].add(error_event.id)
        
        # Check if this correlation has multiple errors (potential cascade)
        if len(self._error_correlations[correlation_id]) > 1:
            logger.warning(
                "Error correlation detected",
                correlation_id=correlation_id,
                error_count=len(self._error_correlations[correlation_id]),
                services_affected=list(set(
                    event.service_name for event in self._error_events
                    if event.correlation_id == correlation_id
                ))
            )
    
    async def _update_service_error_metrics(
        self,
        service_name: str,
        error_event: ErrorEvent
    ) -> None:
        """Update error metrics for a service."""
        if service_name not in self._service_metrics:
            self._service_metrics[service_name] = {
                'total_errors': 0,
                'error_types': {},
                'severity_counts': {severity.value: 0 for severity in ErrorSeverity},
                'last_error_time': None,
                'error_rate': 0.0
            }
        
        metrics = self._service_metrics[service_name]
        metrics['total_errors'] += 1
        metrics['error_types'][error_event.error_type] = (
            metrics['error_types'].get(error_event.error_type, 0) + 1
        )
        metrics['severity_counts'][error_event.severity.value] += 1
        metrics['last_error_time'] = error_event.timestamp.isoformat()
    
    async def _update_service_performance_metrics(
        self,
        service_name: str,
        metric: PerformanceMetric
    ) -> None:
        """Update performance metrics for a service."""
        if service_name not in self._service_metrics:
            self._service_metrics[service_name] = {
                'total_operations': 0,
                'successful_operations': 0,
                'avg_response_time_ms': 0.0,
                'max_response_time_ms': 0.0,
                'min_response_time_ms': float('inf')
            }
        
        metrics = self._service_metrics[service_name]
        metrics['total_operations'] += 1
        
        if metric.success:
            metrics['successful_operations'] += 1
        
        # Update response time statistics
        current_avg = metrics['avg_response_time_ms']
        total_ops = metrics['total_operations']
        metrics['avg_response_time_ms'] = (
            (current_avg * (total_ops - 1) + metric.response_time_ms) / total_ops
        )
        
        metrics['max_response_time_ms'] = max(
            metrics['max_response_time_ms'], metric.response_time_ms
        )
        metrics['min_response_time_ms'] = min(
            metrics['min_response_time_ms'], metric.response_time_ms
        )
        
        # Calculate error rate
        if 'total_errors' in metrics:
            metrics['error_rate'] = (
                metrics['total_errors'] / metrics['total_operations']
            ) * 100
    
    async def _check_error_alerts(
        self,
        service_name: str,
        error_event: ErrorEvent
    ) -> None:
        """Check if error conditions trigger alerts."""
        # Check error rate alert
        if service_name in self._service_metrics:
            metrics = self._service_metrics[service_name]
            error_rate = metrics.get('error_rate', 0.0)
            
            if error_rate > self.config.error_rate_threshold:
                await self._create_alert(
                    AlertType.ERROR_RATE_HIGH,
                    ErrorSeverity.HIGH,
                    f"High error rate for {service_name}",
                    f"Error rate ({error_rate:.1f}%) exceeds threshold ({self.config.error_rate_threshold}%)",
                    service_name,
                    self.config.error_rate_threshold,
                    error_rate
                )
        
        # Check critical error alert
        if error_event.severity == ErrorSeverity.CRITICAL:
            await self._create_alert(
                AlertType.SERVICE_DOWN,
                ErrorSeverity.CRITICAL,
                f"Critical error in {service_name}",
                f"Critical error: {error_event.error_message}",
                service_name,
                0,
                1
            )
    
    async def _check_performance_alerts(
        self,
        service_name: str,
        metric: PerformanceMetric
    ) -> None:
        """Check if performance conditions trigger alerts."""
        # Check response time alert
        if metric.response_time_ms > self.config.response_time_threshold_ms:
            await self._create_alert(
                AlertType.RESPONSE_TIME_HIGH,
                ErrorSeverity.MEDIUM,
                f"High response time for {service_name}",
                f"Response time ({metric.response_time_ms:.1f}ms) exceeds threshold ({self.config.response_time_threshold_ms}ms)",
                service_name,
                self.config.response_time_threshold_ms,
                metric.response_time_ms
            )
    
    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: ErrorSeverity,
        title: str,
        description: str,
        service_name: str,
        threshold_value: float,
        current_value: float
    ) -> None:
        """Create a new alert if not in cooldown."""
        alert_key = f"{alert_type.value}:{service_name}"
        
        # Check cooldown
        if alert_key in self._alert_cooldowns:
            cooldown_end = self._alert_cooldowns[alert_key] + timedelta(
                minutes=self.config.alert_cooldown_minutes
            )
            if datetime.now() < cooldown_end:
                return  # Still in cooldown
        
        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            service_name=service_name,
            threshold_value=threshold_value,
            current_value=current_value
        )
        
        self._alerts.append(alert)
        self._alert_cooldowns[alert_key] = datetime.now()
        
        # Notify alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(
                    "Alert handler failed",
                    handler=str(handler),
                    error=str(e)
                )
        
        logger.warning(
            "Alert created",
            alert_id=alert.id,
            alert_type=alert_type.value,
            severity=severity.value,
            title=title,
            service_name=service_name,
            threshold_value=threshold_value,
            current_value=current_value
        )
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function.
        
        Args:
            handler: Function to call when alerts are created
        """
        self._alert_handlers.append(handler)
        logger.info(
            "Alert handler added",
            handler=str(handler)
        )
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Update service metrics
                await self._update_aggregated_metrics()
                
                # Check for pattern-based alerts
                await self._check_pattern_alerts()
                
                # Log health summary
                await self._log_health_summary()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Monitoring loop error",
                    error=str(e)
                )
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Clean old error events
                await self._cleanup_old_errors()
                
                # Clean old performance metrics
                await self._cleanup_old_metrics()
                
                # Clean old alerts
                await self._cleanup_old_alerts()
                
                # Persist logs
                await self._persist_logs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Cleanup loop error",
                    error=str(e)
                )
    
    async def _update_aggregated_metrics(self) -> None:
        """Update aggregated metrics across all services."""
        # This could include cross-service correlation analysis,
        # system-wide error rates, etc.
        pass
    
    async def _check_pattern_alerts(self) -> None:
        """Check for error pattern-based alerts."""
        # Analyze error patterns for anomalies
        for pattern_key, events in self._error_patterns.items():
            if len(events) >= 5:  # Pattern threshold
                recent_events = [
                    event for event in events
                    if event.timestamp > datetime.now() - timedelta(minutes=10)
                ]
                
                if len(recent_events) >= 3:
                    service_name = pattern_key.split(':')[0]
                    error_type = pattern_key.split(':')[1]
                    
                    await self._create_alert(
                        AlertType.ERROR_RATE_HIGH,
                        ErrorSeverity.MEDIUM,
                        f"Error pattern detected in {service_name}",
                        f"Repeated {error_type} errors ({len(recent_events)} in 10 minutes)",
                        service_name,
                        3,
                        len(recent_events)
                    )
    
    async def _log_health_summary(self) -> None:
        """Log periodic health summary."""
        total_errors = len(self._error_events)
        total_metrics = len(self._performance_metrics)
        active_alerts = len([alert for alert in self._alerts if not alert.resolved])
        
        logger.info(
            "Health summary",
            total_errors=total_errors,
            total_metrics=total_metrics,
            active_alerts=active_alerts,
            services_monitored=len(self._service_metrics)
        )
    
    async def _cleanup_old_errors(self) -> None:
        """Clean up old error events."""
        cutoff_date = datetime.now() - timedelta(days=self.config.log_retention_days)
        
        original_count = len(self._error_events)
        self._error_events = [
            event for event in self._error_events
            if event.timestamp > cutoff_date
        ]
        
        cleaned_count = original_count - len(self._error_events)
        if cleaned_count > 0:
            logger.info(
                "Old error events cleaned",
                cleaned_count=cleaned_count,
                remaining_count=len(self._error_events)
            )
    
    async def _cleanup_old_metrics(self) -> None:
        """Clean up old performance metrics."""
        cutoff_date = datetime.now() - timedelta(days=self.config.log_retention_days)
        
        original_count = len(self._performance_metrics)
        self._performance_metrics = [
            metric for metric in self._performance_metrics
            if metric.timestamp > cutoff_date
        ]
        
        cleaned_count = original_count - len(self._performance_metrics)
        if cleaned_count > 0:
            logger.info(
                "Old performance metrics cleaned",
                cleaned_count=cleaned_count,
                remaining_count=len(self._performance_metrics)
            )
    
    async def _cleanup_old_alerts(self) -> None:
        """Clean up old resolved alerts."""
        cutoff_date = datetime.now() - timedelta(days=7)  # Keep alerts for 7 days
        
        original_count = len(self._alerts)
        self._alerts = [
            alert for alert in self._alerts
            if not alert.resolved or alert.timestamp > cutoff_date
        ]
        
        cleaned_count = original_count - len(self._alerts)
        if cleaned_count > 0:
            logger.info(
                "Old alerts cleaned",
                cleaned_count=cleaned_count,
                remaining_count=len(self._alerts)
            )
    
    async def _persist_logs(self) -> None:
        """Persist logs to files."""
        try:
            # Persist error events
            error_log_file = self.log_directory / f"error_events_{datetime.now().strftime('%Y%m%d')}.json"
            with open(error_log_file, 'w') as f:
                json.dump([
                    {
                        **asdict(event),
                        'timestamp': event.timestamp.isoformat()
                    }
                    for event in self._error_events
                ], f, indent=2)
            
            # Persist performance metrics
            metrics_log_file = self.log_directory / f"performance_metrics_{datetime.now().strftime('%Y%m%d')}.json"
            with open(metrics_log_file, 'w') as f:
                json.dump([
                    {
                        **asdict(metric),
                        'timestamp': metric.timestamp.isoformat()
                    }
                    for metric in self._performance_metrics
                ], f, indent=2)
            
            # Persist alerts
            alerts_log_file = self.log_directory / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
            with open(alerts_log_file, 'w') as f:
                json.dump([
                    {
                        **asdict(alert),
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in self._alerts
                ], f, indent=2)
            
        except Exception as e:
            logger.error(
                "Failed to persist logs",
                error=str(e)
            )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary.
        
        Returns:
            Dictionary with error summary data
        """
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_errors = [
            event for event in self._error_events
            if event.timestamp > last_hour
        ]
        
        daily_errors = [
            event for event in self._error_events
            if event.timestamp > last_day
        ]
        
        return {
            'total_errors': len(self._error_events),
            'recent_errors_1h': len(recent_errors),
            'daily_errors_24h': len(daily_errors),
            'error_by_severity': {
                severity.value: len([
                    event for event in self._error_events
                    if event.severity == severity
                ])
                for severity in ErrorSeverity
            },
            'error_by_service': {
                service: len([
                    event for event in self._error_events
                    if event.service_name == service
                ])
                for service in set(event.service_name for event in self._error_events)
            },
            'top_error_types': self._get_top_error_types(),
            'error_correlations': len(self._error_correlations),
            'active_alerts': len([alert for alert in self._alerts if not alert.resolved])
        }
    
    def _get_top_error_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top error types by frequency."""
        error_type_counts = {}
        
        for event in self._error_events:
            key = f"{event.service_name}:{event.error_type}"
            error_type_counts[key] = error_type_counts.get(key, 0) + 1
        
        sorted_errors = sorted(
            error_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                'service_error_type': error_type,
                'count': count
            }
            for error_type, count in sorted_errors[:limit]
        ]
    
    def get_service_health_report(self) -> Dict[str, Any]:
        """Get comprehensive service health report.
        
        Returns:
            Dictionary with service health data
        """
        return {
            'services': self._service_metrics.copy(),
            'alerts': {
                'active': [
                    asdict(alert) for alert in self._alerts
                    if not alert.resolved
                ],
                'total': len(self._alerts)
            },
            'performance_summary': self._get_performance_summary(),
            'error_patterns': {
                pattern: len(events)
                for pattern, events in self._error_patterns.items()
            }
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all services."""
        if not self._performance_metrics:
            return {}
        
        total_operations = len(self._performance_metrics)
        successful_operations = len([
            metric for metric in self._performance_metrics
            if metric.success
        ])
        
        response_times = [
            metric.response_time_ms for metric in self._performance_metrics
        ]
        
        return {
            'total_operations': total_operations,
            'success_rate': (successful_operations / total_operations) * 100,
            'avg_response_time_ms': sum(response_times) / len(response_times),
            'max_response_time_ms': max(response_times),
            'min_response_time_ms': min(response_times)
        }
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            
        Returns:
            True if alert was found and acknowledged
        """
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(
                    "Alert acknowledged",
                    alert_id=alert_id,
                    alert_type=alert.alert_type.value
                )
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            True if alert was found and resolved
        """
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                logger.info(
                    "Alert resolved",
                    alert_id=alert_id,
                    alert_type=alert.alert_type.value
                )
                return True
        
        return False