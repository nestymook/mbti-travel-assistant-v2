#!/usr/bin/env python3
"""
Performance Dashboard Service

This module provides real-time performance monitoring and dashboard capabilities
for the MBTI Travel Assistant MCP service, including metrics collection,
alerting, and performance analytics.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from .cloudwatch_monitor import CloudWatchMonitor, MetricUnit
from .health_check import HealthChecker, HealthStatus

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    dimensions: Dict[str, str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AlertRule:
    """Performance alert rule configuration"""
    name: str
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True
    notification_channels: List[str] = None


@dataclass
class PerformanceAlert:
    """Performance alert instance"""
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history_size: Maximum number of metric points to keep in memory
        """
        self.max_history_size = max_history_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.metric_aggregates: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.last_aggregation = datetime.now()
        
    def add_metric(self, metric: PerformanceMetric):
        """Add a metric to the collection"""
        metric_key = f"{metric.name}_{metric.dimensions or {}}"
        self.metrics_history[metric_key].append(metric)
        
        # Update aggregates periodically
        if (datetime.now() - self.last_aggregation).seconds >= 60:
            self._update_aggregates()
            self.last_aggregation = datetime.now()
    
    def get_metric_history(self, metric_name: str, duration_minutes: int = 60) -> List[PerformanceMetric]:
        """Get metric history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        all_metrics = []
        for key, metrics in self.metrics_history.items():
            if metric_name in key:
                all_metrics.extend([m for m in metrics if m.timestamp >= cutoff_time])
        
        return sorted(all_metrics, key=lambda x: x.timestamp)
    
    def get_metric_aggregate(self, metric_name: str) -> Dict[str, float]:
        """Get aggregated statistics for a metric"""
        return self.metric_aggregates.get(metric_name, {})
    
    def _update_aggregates(self):
        """Update metric aggregates"""
        for metric_key, metrics in self.metrics_history.items():
            if not metrics:
                continue
            
            # Extract base metric name
            base_name = metric_key.split('_')[0]
            values = [m.value for m in metrics if m.timestamp >= datetime.now() - timedelta(hours=1)]
            
            if values:
                self.metric_aggregates[base_name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                    'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
                }


class AlertManager:
    """Manages performance alerts and notifications"""
    
    def __init__(self, cloudwatch_monitor: Optional[CloudWatchMonitor] = None):
        """
        Initialize alert manager.
        
        Args:
            cloudwatch_monitor: Optional CloudWatch monitor for sending alerts
        """
        self.cloudwatch_monitor = cloudwatch_monitor
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        self.notification_handlers: Dict[str, Callable] = {}
        
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def register_notification_handler(self, channel: str, handler: Callable):
        """Register a notification handler for a channel"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel}")
    
    async def evaluate_alerts(self, metrics: List[PerformanceMetric]):
        """Evaluate alert rules against current metrics"""
        metric_values = {m.name: m.value for m in metrics}
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            if rule.metric_name not in metric_values:
                continue
            
            current_value = metric_values[rule.metric_name]
            should_alert = self._evaluate_threshold(current_value, rule.threshold, rule.comparison)
            
            if should_alert:
                await self._trigger_alert(rule, current_value)
            else:
                await self._resolve_alert(rule_name)
    
    def _evaluate_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate if value meets threshold condition"""
        if comparison == 'gt':
            return value > threshold
        elif comparison == 'lt':
            return value < threshold
        elif comparison == 'eq':
            return abs(value - threshold) < 0.001
        else:
            return False
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert"""
        alert_key = f"{rule.name}_{rule.metric_name}"
        
        # Check if alert is already active
        if alert_key in self.active_alerts:
            return
        
        alert = PerformanceAlert(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            message=f"{rule.metric_name} is {current_value}, threshold is {rule.threshold}",
            timestamp=datetime.now()
        )
        
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Alert triggered: {alert.message}")
        
        # Send notifications
        await self._send_notifications(alert, rule.notification_channels or [])
        
        # Send to CloudWatch if available
        if self.cloudwatch_monitor:
            await self._send_alert_to_cloudwatch(alert)
    
    async def _resolve_alert(self, rule_name: str):
        """Resolve an active alert"""
        alert_keys_to_remove = [key for key in self.active_alerts.keys() if key.startswith(rule_name)]
        
        for alert_key in alert_keys_to_remove:
            alert = self.active_alerts[alert_key]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[alert_key]
            
            logger.info(f"Alert resolved: {alert.rule_name}")
            
            # Send resolution notifications
            await self._send_resolution_notifications(alert)
    
    async def _send_notifications(self, alert: PerformanceAlert, channels: List[str]):
        """Send alert notifications to specified channels"""
        for channel in channels:
            if channel in self.notification_handlers:
                try:
                    await self.notification_handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send notification to {channel}: {e}")
    
    async def _send_resolution_notifications(self, alert: PerformanceAlert):
        """Send alert resolution notifications"""
        # Implementation for resolution notifications
        pass
    
    async def _send_alert_to_cloudwatch(self, alert: PerformanceAlert):
        """Send alert to CloudWatch"""
        try:
            self.cloudwatch_monitor.put_metric(
                f"Alert_{alert.rule_name}",
                1.0,
                MetricUnit.COUNT,
                {
                    "Severity": alert.severity,
                    "MetricName": alert.metric_name
                }
            )
        except Exception as e:
            logger.error(f"Failed to send alert to CloudWatch: {e}")
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[PerformanceAlert]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]


class PerformanceDashboard:
    """
    Real-time performance dashboard for MBTI Travel Assistant.
    
    Provides comprehensive performance monitoring, metrics collection,
    alerting, and dashboard capabilities.
    """
    
    def __init__(
        self,
        cloudwatch_monitor: Optional[CloudWatchMonitor] = None,
        health_checker: Optional[HealthChecker] = None,
        environment: str = "development"
    ):
        """
        Initialize performance dashboard.
        
        Args:
            cloudwatch_monitor: Optional CloudWatch monitor
            health_checker: Optional health checker
            environment: Environment name
        """
        self.cloudwatch_monitor = cloudwatch_monitor
        self.health_checker = health_checker
        self.environment = environment
        
        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(cloudwatch_monitor)
        
        # Performance tracking
        self.request_metrics = deque(maxlen=1000)
        self.mcp_metrics = deque(maxlen=1000)
        self.system_metrics = deque(maxlen=1000)
        
        # Dashboard state
        self.dashboard_data = {}
        self.last_update = datetime.now()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        logger.info(f"Initialized PerformanceDashboard for {environment}")
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_response_time",
                metric_name="response_time",
                threshold=5.0,  # 5 seconds
                comparison="gt",
                duration_seconds=300,
                severity="warning",
                notification_channels=["cloudwatch", "logs"]
            ),
            AlertRule(
                name="high_error_rate",
                metric_name="error_rate",
                threshold=0.05,  # 5%
                comparison="gt",
                duration_seconds=300,
                severity="critical",
                notification_channels=["cloudwatch", "logs"]
            ),
            AlertRule(
                name="low_throughput",
                metric_name="throughput",
                threshold=1.0,  # 1 request per second
                comparison="lt",
                duration_seconds=600,
                severity="warning",
                notification_channels=["cloudwatch", "logs"]
            ),
            AlertRule(
                name="high_mcp_latency",
                metric_name="mcp_latency",
                threshold=3.0,  # 3 seconds
                comparison="gt",
                duration_seconds=300,
                severity="warning",
                notification_channels=["cloudwatch", "logs"]
            ),
            AlertRule(
                name="cache_miss_rate_high",
                metric_name="cache_miss_rate",
                threshold=0.8,  # 80%
                comparison="gt",
                duration_seconds=600,
                severity="warning",
                notification_channels=["cloudwatch", "logs"]
            )
        ]
        
        for rule in default_rules:
            self.alert_manager.add_alert_rule(rule)
    
    async def record_request_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None
    ):
        """Record HTTP request metric"""
        metric = PerformanceMetric(
            name="http_request",
            value=duration_ms,
            unit="milliseconds",
            timestamp=datetime.now(),
            dimensions={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
                "environment": self.environment
            },
            metadata={
                "user_id": user_id,
                "success": 200 <= status_code < 400
            }
        )
        
        self.request_metrics.append(metric)
        self.metrics_collector.add_metric(metric)
        
        # Send to CloudWatch
        if self.cloudwatch_monitor:
            await self._send_request_metrics_to_cloudwatch(metric)
    
    async def record_mcp_metric(
        self,
        server_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record MCP operation metric"""
        metric = PerformanceMetric(
            name="mcp_operation",
            value=duration_ms,
            unit="milliseconds",
            timestamp=datetime.now(),
            dimensions={
                "server": server_name,
                "operation": operation,
                "success": str(success),
                "environment": self.environment
            },
            metadata={
                "error_message": error_message
            }
        )
        
        self.mcp_metrics.append(metric)
        self.metrics_collector.add_metric(metric)
        
        # Send to CloudWatch
        if self.cloudwatch_monitor:
            await self._send_mcp_metrics_to_cloudwatch(metric)
    
    async def record_system_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record system metric"""
        metric = PerformanceMetric(
            name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            dimensions={
                **(dimensions or {}),
                "environment": self.environment
            }
        )
        
        self.system_metrics.append(metric)
        self.metrics_collector.add_metric(metric)
        
        # Send to CloudWatch
        if self.cloudwatch_monitor:
            self.cloudwatch_monitor.put_metric(
                metric_name,
                value,
                getattr(MetricUnit, unit.upper(), MetricUnit.COUNT),
                metric.dimensions
            )
    
    async def update_dashboard_data(self):
        """Update dashboard data with latest metrics"""
        now = datetime.now()
        
        # Calculate time-based metrics
        last_hour_requests = [m for m in self.request_metrics if m.timestamp >= now - timedelta(hours=1)]
        last_hour_mcp = [m for m in self.mcp_metrics if m.timestamp >= now - timedelta(hours=1)]
        
        # Request metrics
        request_data = self._calculate_request_metrics(last_hour_requests)
        
        # MCP metrics
        mcp_data = self._calculate_mcp_metrics(last_hour_mcp)
        
        # System metrics
        system_data = await self._get_system_metrics()
        
        # Health status
        health_data = await self._get_health_status()
        
        # Alert status
        alert_data = self._get_alert_status()
        
        self.dashboard_data = {
            "timestamp": now.isoformat(),
            "environment": self.environment,
            "requests": request_data,
            "mcp": mcp_data,
            "system": system_data,
            "health": health_data,
            "alerts": alert_data,
            "uptime_seconds": (now - self.last_update).total_seconds()
        }
        
        self.last_update = now
        
        # Evaluate alerts
        current_metrics = self._extract_current_metrics()
        await self.alert_manager.evaluate_alerts(current_metrics)
    
    def _calculate_request_metrics(self, requests: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate request-based metrics"""
        if not requests:
            return {
                "total_requests": 0,
                "requests_per_second": 0.0,
                "avg_response_time": 0.0,
                "error_rate": 0.0,
                "status_codes": {}
            }
        
        total_requests = len(requests)
        duration_hours = 1.0  # Last hour
        requests_per_second = total_requests / (duration_hours * 3600)
        
        response_times = [r.value for r in requests]
        avg_response_time = statistics.mean(response_times)
        
        error_requests = [r for r in requests if not r.metadata.get("success", True)]
        error_rate = len(error_requests) / total_requests if total_requests > 0 else 0.0
        
        # Status code distribution
        status_codes = defaultdict(int)
        for request in requests:
            status_code = request.dimensions.get("status_code", "unknown")
            status_codes[status_code] += 1
        
        return {
            "total_requests": total_requests,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
            "error_rate": error_rate,
            "status_codes": dict(status_codes)
        }
    
    def _calculate_mcp_metrics(self, mcp_calls: List[PerformanceMetric]) -> Dict[str, Any]:
        """Calculate MCP-based metrics"""
        if not mcp_calls:
            return {
                "total_calls": 0,
                "calls_per_second": 0.0,
                "avg_latency": 0.0,
                "error_rate": 0.0,
                "servers": {}
            }
        
        total_calls = len(mcp_calls)
        duration_hours = 1.0
        calls_per_second = total_calls / (duration_hours * 3600)
        
        latencies = [m.value for m in mcp_calls]
        avg_latency = statistics.mean(latencies)
        
        error_calls = [m for m in mcp_calls if m.dimensions.get("success") == "False"]
        error_rate = len(error_calls) / total_calls if total_calls > 0 else 0.0
        
        # Server-specific metrics
        servers = defaultdict(lambda: {"calls": 0, "errors": 0, "avg_latency": 0.0})
        for call in mcp_calls:
            server = call.dimensions.get("server", "unknown")
            servers[server]["calls"] += 1
            if call.dimensions.get("success") == "False":
                servers[server]["errors"] += 1
        
        # Calculate average latencies per server
        for server in servers:
            server_calls = [m for m in mcp_calls if m.dimensions.get("server") == server]
            if server_calls:
                servers[server]["avg_latency"] = statistics.mean([m.value for m in server_calls])
        
        return {
            "total_calls": total_calls,
            "calls_per_second": calls_per_second,
            "avg_latency": avg_latency,
            "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "error_rate": error_rate,
            "servers": dict(servers)
        }
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        if not self.health_checker:
            return {"status": "unknown", "message": "Health checker not available"}
        
        try:
            quick_status = await self.health_checker.get_quick_health_status()
            return quick_status
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_alert_status(self) -> Dict[str, Any]:
        """Get current alert status"""
        active_alerts = self.alert_manager.get_active_alerts()
        recent_alerts = self.alert_manager.get_alert_history(hours=24)
        
        # Count alerts by severity
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity] += 1
        
        return {
            "active_alerts": len(active_alerts),
            "recent_alerts_24h": len(recent_alerts),
            "severity_counts": dict(severity_counts),
            "alerts": [
                {
                    "rule_name": alert.rule_name,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ]
        }
    
    def _extract_current_metrics(self) -> List[PerformanceMetric]:
        """Extract current metrics for alert evaluation"""
        current_metrics = []
        
        # Add aggregated metrics
        for metric_name, aggregates in self.metrics_collector.metric_aggregates.items():
            if 'mean' in aggregates:
                current_metrics.append(PerformanceMetric(
                    name=metric_name,
                    value=aggregates['mean'],
                    unit="average",
                    timestamp=datetime.now()
                ))
        
        return current_metrics
    
    async def _send_request_metrics_to_cloudwatch(self, metric: PerformanceMetric):
        """Send request metrics to CloudWatch"""
        try:
            # Send response time
            self.cloudwatch_monitor.put_metric(
                "ResponseTime",
                metric.value,
                MetricUnit.MILLISECONDS,
                metric.dimensions
            )
            
            # Send request count
            self.cloudwatch_monitor.put_metric(
                "RequestCount",
                1.0,
                MetricUnit.COUNT,
                metric.dimensions
            )
            
            # Send error count if applicable
            if not metric.metadata.get("success", True):
                self.cloudwatch_monitor.put_metric(
                    "ErrorCount",
                    1.0,
                    MetricUnit.COUNT,
                    metric.dimensions
                )
        except Exception as e:
            logger.error(f"Failed to send request metrics to CloudWatch: {e}")
    
    async def _send_mcp_metrics_to_cloudwatch(self, metric: PerformanceMetric):
        """Send MCP metrics to CloudWatch"""
        try:
            # Send MCP call duration
            self.cloudwatch_monitor.put_metric(
                "MCPCallDuration",
                metric.value,
                MetricUnit.MILLISECONDS,
                metric.dimensions
            )
            
            # Send MCP call count
            self.cloudwatch_monitor.put_metric(
                "MCPCallCount",
                1.0,
                MetricUnit.COUNT,
                metric.dimensions
            )
            
            # Send MCP error count if applicable
            if metric.dimensions.get("success") == "False":
                self.cloudwatch_monitor.put_metric(
                    "MCPErrorCount",
                    1.0,
                    MetricUnit.COUNT,
                    metric.dimensions
                )
        except Exception as e:
            logger.error(f"Failed to send MCP metrics to CloudWatch: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_requests = [m for m in self.request_metrics if m.timestamp >= cutoff_time]
        recent_mcp = [m for m in self.mcp_metrics if m.timestamp >= cutoff_time]
        
        return {
            "time_range_hours": hours,
            "requests": self._calculate_request_metrics(recent_requests),
            "mcp": self._calculate_mcp_metrics(recent_mcp),
            "alerts": self._get_alert_status()
        }
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        await self.update_dashboard_data()
        
        if format.lower() == "json":
            return json.dumps(self.dashboard_data, indent=2)
        elif format.lower() == "prometheus":
            return self._export_prometheus_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Request metrics
        if "requests" in self.dashboard_data:
            req_data = self.dashboard_data["requests"]
            lines.append(f"# HELP http_requests_total Total HTTP requests")
            lines.append(f"# TYPE http_requests_total counter")
            lines.append(f"http_requests_total{{environment=\"{self.environment}\"}} {req_data.get('total_requests', 0)}")
            
            lines.append(f"# HELP http_request_duration_seconds HTTP request duration")
            lines.append(f"# TYPE http_request_duration_seconds histogram")
            lines.append(f"http_request_duration_seconds_sum{{environment=\"{self.environment}\"}} {req_data.get('avg_response_time', 0) * req_data.get('total_requests', 0) / 1000}")
            lines.append(f"http_request_duration_seconds_count{{environment=\"{self.environment}\"}} {req_data.get('total_requests', 0)}")
        
        # MCP metrics
        if "mcp" in self.dashboard_data:
            mcp_data = self.dashboard_data["mcp"]
            lines.append(f"# HELP mcp_calls_total Total MCP calls")
            lines.append(f"# TYPE mcp_calls_total counter")
            lines.append(f"mcp_calls_total{{environment=\"{self.environment}\"}} {mcp_data.get('total_calls', 0)}")
        
        # System metrics
        if "system" in self.dashboard_data:
            sys_data = self.dashboard_data["system"]
            lines.append(f"# HELP system_cpu_percent CPU usage percentage")
            lines.append(f"# TYPE system_cpu_percent gauge")
            lines.append(f"system_cpu_percent{{environment=\"{self.environment}\"}} {sys_data.get('cpu_percent', 0)}")
            
            lines.append(f"# HELP system_memory_percent Memory usage percentage")
            lines.append(f"# TYPE system_memory_percent gauge")
            lines.append(f"system_memory_percent{{environment=\"{self.environment}\"}} {sys_data.get('memory_percent', 0)}")
        
        return "\n".join(lines)