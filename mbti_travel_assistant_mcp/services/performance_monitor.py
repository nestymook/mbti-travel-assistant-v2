"""
Performance Monitor Service

This module provides performance monitoring and metrics collection for the
MBTI Travel Assistant MCP client operations and system performance.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
from contextlib import asynccontextmanager
import psutil
import threading

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    CONNECTION_COUNT = "connection_count"
    CACHE_HIT_RATE = "cache_hit_rate"
    MCP_CALL_DURATION = "mcp_call_duration"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    metric_type: MetricType
    count: int = 0
    min_value: float = float('inf')
    max_value: float = float('-inf')
    avg_value: float = 0.0
    median_value: float = 0.0
    p95_value: float = 0.0
    p99_value: float = 0.0
    total_value: float = 0.0
    last_updated: Optional[datetime] = None
    values: List[float] = field(default_factory=list)
    
    def update(self, value: float, timestamp: datetime):
        """Update statistics with new value"""
        self.count += 1
        self.total_value += value
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.avg_value = self.total_value / self.count
        self.last_updated = timestamp
        
        # Keep last 1000 values for percentile calculations
        self.values.append(value)
        if len(self.values) > 1000:
            self.values.pop(0)
        
        # Calculate percentiles
        if self.values:
            sorted_values = sorted(self.values)
            self.median_value = statistics.median(sorted_values)
            self.p95_value = self._percentile(sorted_values, 95)
            self.p99_value = self._percentile(sorted_values, 99)
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class PerformanceMonitor:
    """
    Performance monitoring service for MCP client operations.
    
    Collects and aggregates performance metrics including response times,
    throughput, error rates, and system resource usage.
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize performance monitor.
        
        Args:
            retention_hours: How long to retain metrics data
        """
        self.retention_hours = retention_hours
        self._metrics: List[PerformanceMetric] = []
        self._stats: Dict[str, PerformanceStats] = {}
        self._lock = threading.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._system_monitor_task: Optional[asyncio.Task] = None
        self._start_time = datetime.now()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info(f"Initialized PerformanceMonitor with {retention_hours}h retention")
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._cleanup_old_metrics())
            self._system_monitor_task = loop.create_task(self._monitor_system_resources())
        except RuntimeError:
            # No event loop running, tasks will be started when needed
            pass
    
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            labels: Optional labels for metric categorization
            metadata: Optional metadata
        """
        timestamp = datetime.now()
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            labels=labels or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
            
            # Update aggregated statistics
            stats_key = self._get_stats_key(metric_type, labels or {})
            if stats_key not in self._stats:
                self._stats[stats_key] = PerformanceStats(metric_type=metric_type)
            
            self._stats[stats_key].update(value, timestamp)
        
        logger.debug(f"Recorded metric: {metric_type.value} = {value}")
    
    def _get_stats_key(self, metric_type: MetricType, labels: Dict[str, str]) -> str:
        """Generate key for statistics storage"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric_type.value}:{label_str}" if label_str else metric_type.value
    
    @asynccontextmanager
    async def measure_operation(
        self,
        operation_name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Context manager to measure operation duration.
        
        Args:
            operation_name: Name of the operation being measured
            labels: Optional labels for categorization
        """
        start_time = time.time()
        operation_labels = {"operation": operation_name}
        if labels:
            operation_labels.update(labels)
        
        try:
            yield
            # Record successful operation
            duration = time.time() - start_time
            self.record_metric(
                MetricType.RESPONSE_TIME,
                duration,
                operation_labels,
                {"status": "success"}
            )
            
        except Exception as e:
            # Record failed operation
            duration = time.time() - start_time
            self.record_metric(
                MetricType.RESPONSE_TIME,
                duration,
                operation_labels,
                {"status": "error", "error_type": type(e).__name__}
            )
            raise
    
    def record_mcp_call(
        self,
        server_name: str,
        tool_name: str,
        duration: float,
        success: bool,
        error_type: Optional[str] = None
    ):
        """
        Record MCP call performance metrics.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the MCP tool called
            duration: Call duration in seconds
            success: Whether the call was successful
            error_type: Type of error if call failed
        """
        labels = {
            "server": server_name,
            "tool": tool_name,
            "status": "success" if success else "error"
        }
        
        metadata = {"error_type": error_type} if error_type else {}
        
        self.record_metric(
            MetricType.MCP_CALL_DURATION,
            duration,
            labels,
            metadata
        )
        
        # Record error rate
        error_rate = 0.0 if success else 1.0
        self.record_metric(
            MetricType.ERROR_RATE,
            error_rate,
            {"server": server_name, "tool": tool_name}
        )
    
    def record_cache_performance(self, hit: bool, operation_type: str):
        """
        Record cache performance metrics.
        
        Args:
            hit: Whether it was a cache hit
            operation_type: Type of cache operation
        """
        hit_rate = 1.0 if hit else 0.0
        self.record_metric(
            MetricType.CACHE_HIT_RATE,
            hit_rate,
            {"operation": operation_type}
        )
    
    def record_throughput(self, requests_per_second: float, endpoint: str):
        """
        Record throughput metrics.
        
        Args:
            requests_per_second: Current throughput
            endpoint: Endpoint being measured
        """
        self.record_metric(
            MetricType.THROUGHPUT,
            requests_per_second,
            {"endpoint": endpoint}
        )
    
    def get_stats(
        self,
        metric_type: Optional[MetricType] = None,
        labels: Optional[Dict[str, str]] = None,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, PerformanceStats]:
        """
        Get performance statistics.
        
        Args:
            metric_type: Filter by metric type
            labels: Filter by labels
            time_window_minutes: Only include metrics from last N minutes
            
        Returns:
            Dictionary of performance statistics
        """
        with self._lock:
            filtered_stats = {}
            
            for stats_key, stats in self._stats.items():
                # Filter by metric type
                if metric_type and stats.metric_type != metric_type:
                    continue
                
                # Filter by time window
                if time_window_minutes and stats.last_updated:
                    cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
                    if stats.last_updated < cutoff_time:
                        continue
                
                # Filter by labels (simplified matching)
                if labels:
                    stats_labels = self._extract_labels_from_key(stats_key)
                    if not all(stats_labels.get(k) == v for k, v in labels.items()):
                        continue
                
                filtered_stats[stats_key] = stats
            
            return filtered_stats
    
    def _extract_labels_from_key(self, stats_key: str) -> Dict[str, str]:
        """Extract labels from statistics key"""
        if ":" not in stats_key:
            return {}
        
        _, label_str = stats_key.split(":", 1)
        labels = {}
        
        for pair in label_str.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                labels[key] = value
        
        return labels
    
    def get_system_metrics(self) -> Dict[str, float]:
        """
        Get current system performance metrics.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
                "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "network_bytes_sent": psutil.net_io_counters().bytes_sent,
                "network_bytes_recv": psutil.net_io_counters().bytes_recv,
                "process_count": len(psutil.pids()),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds()
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        with self._lock:
            total_metrics = len(self._metrics)
            
            # Calculate metrics by type
            metrics_by_type = {}
            for metric in self._metrics:
                metric_type = metric.metric_type.value
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = 0
                metrics_by_type[metric_type] += 1
            
            # Get recent performance (last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_metrics = [m for m in self._metrics if m.timestamp >= recent_cutoff]
            
            # Calculate error rates
            error_metrics = [m for m in recent_metrics 
                           if m.metadata.get("status") == "error"]
            error_rate = len(error_metrics) / len(recent_metrics) if recent_metrics else 0
            
            return {
                "total_metrics_collected": total_metrics,
                "metrics_by_type": metrics_by_type,
                "recent_metrics_count": len(recent_metrics),
                "recent_error_rate": error_rate,
                "stats_count": len(self._stats),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "system_metrics": self.get_system_metrics(),
                "retention_hours": self.retention_hours
            }
    
    def get_mcp_performance_report(self) -> Dict[str, Any]:
        """
        Get MCP-specific performance report.
        
        Returns:
            Dictionary with MCP performance metrics
        """
        mcp_stats = self.get_stats(MetricType.MCP_CALL_DURATION)
        
        report = {
            "servers": {},
            "tools": {},
            "overall": {
                "total_calls": 0,
                "avg_duration": 0.0,
                "error_rate": 0.0
            }
        }
        
        total_calls = 0
        total_duration = 0.0
        total_errors = 0
        
        for stats_key, stats in mcp_stats.items():
            labels = self._extract_labels_from_key(stats_key)
            server = labels.get("server", "unknown")
            tool = labels.get("tool", "unknown")
            status = labels.get("status", "unknown")
            
            # Server-level metrics
            if server not in report["servers"]:
                report["servers"][server] = {
                    "total_calls": 0,
                    "avg_duration": 0.0,
                    "error_rate": 0.0,
                    "tools": {}
                }
            
            # Tool-level metrics
            if tool not in report["tools"]:
                report["tools"][tool] = {
                    "total_calls": 0,
                    "avg_duration": 0.0,
                    "error_rate": 0.0,
                    "servers": {}
                }
            
            # Update counts
            report["servers"][server]["total_calls"] += stats.count
            report["tools"][tool]["total_calls"] += stats.count
            total_calls += stats.count
            
            # Update durations
            if status == "success":
                report["servers"][server]["avg_duration"] = stats.avg_value
                report["tools"][tool]["avg_duration"] = stats.avg_value
                total_duration += stats.total_value
            else:
                total_errors += stats.count
        
        # Calculate overall metrics
        if total_calls > 0:
            report["overall"]["total_calls"] = total_calls
            report["overall"]["avg_duration"] = total_duration / total_calls
            report["overall"]["error_rate"] = total_errors / total_calls
        
        return report
    
    async def _cleanup_old_metrics(self):
        """Background task to clean up old metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                
                with self._lock:
                    # Remove old metrics
                    old_count = len(self._metrics)
                    self._metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]
                    new_count = len(self._metrics)
                    
                    if old_count > new_count:
                        logger.info(f"Cleaned up {old_count - new_count} old metrics")
                
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
    
    async def _monitor_system_resources(self):
        """Background task to monitor system resources"""
        while True:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                
                # Record system metrics
                system_metrics = self.get_system_metrics()
                
                for metric_name, value in system_metrics.items():
                    if metric_name.endswith("_percent"):
                        metric_type = MetricType.CPU_USAGE if "cpu" in metric_name else MetricType.MEMORY_USAGE
                    else:
                        continue  # Skip non-percentage metrics for now
                    
                    self.record_metric(
                        metric_type,
                        value,
                        {"resource": metric_name}
                    )
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
    
    def shutdown(self):
        """Shutdown the performance monitor"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._system_monitor_task:
            self._system_monitor_task.cancel()
        
        logger.info("Performance monitor shutdown")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()