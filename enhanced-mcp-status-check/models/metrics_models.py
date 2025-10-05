"""
Enhanced MCP Status Check Metrics Models

This module contains data models for metrics collection in the enhanced MCP status check system.
Supports separate metrics tracking for MCP tools/list requests and REST health checks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import statistics
from .dual_health_models import SerializableModel


class MetricType(Enum):
    """Types of metrics collected."""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    FAILURE_RATE = "failure_rate"
    TOOL_COUNT = "tool_count"
    HTTP_STATUS = "http_status"
    AVAILABILITY = "availability"


class TimeWindow(Enum):
    """Time windows for metric aggregation."""
    LAST_MINUTE = "1m"
    LAST_5_MINUTES = "5m"
    LAST_15_MINUTES = "15m"
    LAST_HOUR = "1h"
    LAST_DAY = "24h"


@dataclass
class MetricDataPoint(SerializableModel):
    """Individual metric data point."""
    
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricDataPoint':
        """Create instance from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            timestamp=timestamp,
            value=data.get("value", 0.0),
            labels=data.get("labels", {})
        )


@dataclass
class MetricSeries(SerializableModel):
    """Time series of metric data points."""
    
    metric_name: str
    metric_type: MetricType
    server_name: str
    monitoring_method: str  # "mcp" or "rest"
    data_points: List[MetricDataPoint] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_name": self.metric_name,
            "metric_type": self.metric_type.value,
            "server_name": self.server_name,
            "monitoring_method": self.monitoring_method,
            "data_points": [dp.to_dict() for dp in self.data_points]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricSeries':
        """Create instance from dictionary."""
        data_points = []
        for dp_data in data.get("data_points", []):
            data_points.append(MetricDataPoint.from_dict(dp_data))
        
        return cls(
            metric_name=data.get("metric_name", ""),
            metric_type=MetricType(data.get("metric_type", "response_time")),
            server_name=data.get("server_name", ""),
            monitoring_method=data.get("monitoring_method", "mcp"),
            data_points=data_points
        )
    
    def add_data_point(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add a new data point to the series."""
        data_point = MetricDataPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.data_points.append(data_point)
    
    def get_data_points_in_window(self, time_window: TimeWindow) -> List[MetricDataPoint]:
        """Get data points within the specified time window."""
        now = datetime.now()
        
        # Define time deltas for each window
        window_deltas = {
            TimeWindow.LAST_MINUTE: timedelta(minutes=1),
            TimeWindow.LAST_5_MINUTES: timedelta(minutes=5),
            TimeWindow.LAST_15_MINUTES: timedelta(minutes=15),
            TimeWindow.LAST_HOUR: timedelta(hours=1),
            TimeWindow.LAST_DAY: timedelta(days=1)
        }
        
        cutoff_time = now - window_deltas[time_window]
        return [dp for dp in self.data_points if dp.timestamp >= cutoff_time]
    
    def calculate_average(self, time_window: TimeWindow) -> float:
        """Calculate average value for the time window."""
        data_points = self.get_data_points_in_window(time_window)
        if not data_points:
            return 0.0
        return statistics.mean([dp.value for dp in data_points])
    
    def calculate_percentile(self, time_window: TimeWindow, percentile: float) -> float:
        """Calculate percentile value for the time window."""
        data_points = self.get_data_points_in_window(time_window)
        if not data_points:
            return 0.0
        
        values = sorted([dp.value for dp in data_points])
        if not values:
            return 0.0
        
        index = int(percentile / 100.0 * (len(values) - 1))
        return values[index]
    
    def cleanup_old_data(self, retention_period: timedelta) -> None:
        """Remove data points older than retention period."""
        cutoff_time = datetime.now() - retention_period
        self.data_points = [dp for dp in self.data_points if dp.timestamp >= cutoff_time]


@dataclass
class MCPMetrics(SerializableModel):
    """MCP-specific metrics collection."""
    
    server_name: str
    
    # Response time metrics
    response_times: MetricSeries = field(init=False)
    
    # Success/failure metrics
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    
    # Tool-specific metrics
    tools_count_series: MetricSeries = field(init=False)
    expected_tools_found_series: MetricSeries = field(init=False)
    missing_tools_count_series: MetricSeries = field(init=False)
    
    # Validation metrics
    validation_success_count: int = 0
    validation_failure_count: int = 0
    
    # Error tracking
    connection_errors: int = 0
    timeout_errors: int = 0
    protocol_errors: int = 0
    
    def __post_init__(self):
        """Initialize metric series after dataclass creation."""
        self.response_times = MetricSeries(
            metric_name="mcp_response_time",
            metric_type=MetricType.RESPONSE_TIME,
            server_name=self.server_name,
            monitoring_method="mcp"
        )
        
        self.tools_count_series = MetricSeries(
            metric_name="mcp_tools_count",
            metric_type=MetricType.TOOL_COUNT,
            server_name=self.server_name,
            monitoring_method="mcp"
        )
        
        self.expected_tools_found_series = MetricSeries(
            metric_name="mcp_expected_tools_found",
            metric_type=MetricType.TOOL_COUNT,
            server_name=self.server_name,
            monitoring_method="mcp"
        )
        
        self.missing_tools_count_series = MetricSeries(
            metric_name="mcp_missing_tools_count",
            metric_type=MetricType.TOOL_COUNT,
            server_name=self.server_name,
            monitoring_method="mcp"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "response_times": self.response_times.to_dict(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "tools_count_series": self.tools_count_series.to_dict(),
            "expected_tools_found_series": self.expected_tools_found_series.to_dict(),
            "missing_tools_count_series": self.missing_tools_count_series.to_dict(),
            "validation_success_count": self.validation_success_count,
            "validation_failure_count": self.validation_failure_count,
            "connection_errors": self.connection_errors,
            "timeout_errors": self.timeout_errors,
            "protocol_errors": self.protocol_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMetrics':
        """Create instance from dictionary."""
        instance = cls(server_name=data.get("server_name", ""))
        
        # Load metric series
        if "response_times" in data:
            instance.response_times = MetricSeries.from_dict(data["response_times"])
        
        if "tools_count_series" in data:
            instance.tools_count_series = MetricSeries.from_dict(data["tools_count_series"])
        
        if "expected_tools_found_series" in data:
            instance.expected_tools_found_series = MetricSeries.from_dict(data["expected_tools_found_series"])
        
        if "missing_tools_count_series" in data:
            instance.missing_tools_count_series = MetricSeries.from_dict(data["missing_tools_count_series"])
        
        # Load counters
        instance.success_count = data.get("success_count", 0)
        instance.failure_count = data.get("failure_count", 0)
        instance.total_requests = data.get("total_requests", 0)
        instance.validation_success_count = data.get("validation_success_count", 0)
        instance.validation_failure_count = data.get("validation_failure_count", 0)
        instance.connection_errors = data.get("connection_errors", 0)
        instance.timeout_errors = data.get("timeout_errors", 0)
        instance.protocol_errors = data.get("protocol_errors", 0)
        
        return instance
    
    def record_response_time(self, response_time_ms: float) -> None:
        """Record MCP response time."""
        self.response_times.add_data_point(response_time_ms)
    
    def record_success(self) -> None:
        """Record successful MCP request."""
        self.success_count += 1
        self.total_requests += 1
    
    def record_failure(self, error_type: str = "general") -> None:
        """Record failed MCP request."""
        self.failure_count += 1
        self.total_requests += 1
        
        # Track specific error types
        if error_type == "connection":
            self.connection_errors += 1
        elif error_type == "timeout":
            self.timeout_errors += 1
        elif error_type == "protocol":
            self.protocol_errors += 1
    
    def record_tools_count(self, tools_count: int) -> None:
        """Record number of tools returned."""
        self.tools_count_series.add_data_point(float(tools_count))
    
    def record_expected_tools_found(self, found_count: int) -> None:
        """Record number of expected tools found."""
        self.expected_tools_found_series.add_data_point(float(found_count))
    
    def record_missing_tools(self, missing_count: int) -> None:
        """Record number of missing tools."""
        self.missing_tools_count_series.add_data_point(float(missing_count))
    
    def record_validation_result(self, is_valid: bool) -> None:
        """Record validation result."""
        if is_valid:
            self.validation_success_count += 1
        else:
            self.validation_failure_count += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests
    
    def get_validation_success_rate(self) -> float:
        """Calculate validation success rate."""
        total_validations = self.validation_success_count + self.validation_failure_count
        if total_validations == 0:
            return 0.0
        return self.validation_success_count / total_validations
    
    def get_average_response_time(self, time_window: TimeWindow = TimeWindow.LAST_HOUR) -> float:
        """Get average response time for time window."""
        return self.response_times.calculate_average(time_window)
    
    def get_response_time_percentile(self, percentile: float, time_window: TimeWindow = TimeWindow.LAST_HOUR) -> float:
        """Get response time percentile for time window."""
        return self.response_times.calculate_percentile(time_window, percentile)


@dataclass
class RESTMetrics(SerializableModel):
    """REST-specific metrics collection."""
    
    server_name: str
    
    # Response time metrics
    response_times: MetricSeries = field(init=False)
    
    # Success/failure metrics
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    
    # HTTP status code tracking
    status_code_counts: Dict[int, int] = field(default_factory=dict)
    
    # Health endpoint metrics
    health_endpoint_available_count: int = 0
    health_endpoint_unavailable_count: int = 0
    
    # Response body validation metrics
    valid_response_body_count: int = 0
    invalid_response_body_count: int = 0
    
    # Error tracking
    connection_errors: int = 0
    timeout_errors: int = 0
    http_errors: int = 0
    
    def __post_init__(self):
        """Initialize metric series after dataclass creation."""
        self.response_times = MetricSeries(
            metric_name="rest_response_time",
            metric_type=MetricType.RESPONSE_TIME,
            server_name=self.server_name,
            monitoring_method="rest"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "response_times": self.response_times.to_dict(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_requests": self.total_requests,
            "status_code_counts": self.status_code_counts,
            "health_endpoint_available_count": self.health_endpoint_available_count,
            "health_endpoint_unavailable_count": self.health_endpoint_unavailable_count,
            "valid_response_body_count": self.valid_response_body_count,
            "invalid_response_body_count": self.invalid_response_body_count,
            "connection_errors": self.connection_errors,
            "timeout_errors": self.timeout_errors,
            "http_errors": self.http_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RESTMetrics':
        """Create instance from dictionary."""
        instance = cls(server_name=data.get("server_name", ""))
        
        # Load metric series
        if "response_times" in data:
            instance.response_times = MetricSeries.from_dict(data["response_times"])
        
        # Load counters
        instance.success_count = data.get("success_count", 0)
        instance.failure_count = data.get("failure_count", 0)
        instance.total_requests = data.get("total_requests", 0)
        instance.status_code_counts = data.get("status_code_counts", {})
        instance.health_endpoint_available_count = data.get("health_endpoint_available_count", 0)
        instance.health_endpoint_unavailable_count = data.get("health_endpoint_unavailable_count", 0)
        instance.valid_response_body_count = data.get("valid_response_body_count", 0)
        instance.invalid_response_body_count = data.get("invalid_response_body_count", 0)
        instance.connection_errors = data.get("connection_errors", 0)
        instance.timeout_errors = data.get("timeout_errors", 0)
        instance.http_errors = data.get("http_errors", 0)
        
        return instance
    
    def record_response_time(self, response_time_ms: float) -> None:
        """Record REST response time."""
        self.response_times.add_data_point(response_time_ms)
    
    def record_success(self) -> None:
        """Record successful REST request."""
        self.success_count += 1
        self.total_requests += 1
    
    def record_failure(self, error_type: str = "general") -> None:
        """Record failed REST request."""
        self.failure_count += 1
        self.total_requests += 1
        
        # Track specific error types
        if error_type == "connection":
            self.connection_errors += 1
        elif error_type == "timeout":
            self.timeout_errors += 1
        elif error_type == "http":
            self.http_errors += 1
    
    def record_status_code(self, status_code: int) -> None:
        """Record HTTP status code."""
        if status_code not in self.status_code_counts:
            self.status_code_counts[status_code] = 0
        self.status_code_counts[status_code] += 1
    
    def record_health_endpoint_availability(self, is_available: bool) -> None:
        """Record health endpoint availability."""
        if is_available:
            self.health_endpoint_available_count += 1
        else:
            self.health_endpoint_unavailable_count += 1
    
    def record_response_body_validation(self, is_valid: bool) -> None:
        """Record response body validation result."""
        if is_valid:
            self.valid_response_body_count += 1
        else:
            self.invalid_response_body_count += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests
    
    def get_health_endpoint_availability_rate(self) -> float:
        """Calculate health endpoint availability rate."""
        total_checks = self.health_endpoint_available_count + self.health_endpoint_unavailable_count
        if total_checks == 0:
            return 0.0
        return self.health_endpoint_available_count / total_checks
    
    def get_response_body_validation_rate(self) -> float:
        """Calculate response body validation success rate."""
        total_validations = self.valid_response_body_count + self.invalid_response_body_count
        if total_validations == 0:
            return 0.0
        return self.valid_response_body_count / total_validations
    
    def get_average_response_time(self, time_window: TimeWindow = TimeWindow.LAST_HOUR) -> float:
        """Get average response time for time window."""
        return self.response_times.calculate_average(time_window)
    
    def get_response_time_percentile(self, percentile: float, time_window: TimeWindow = TimeWindow.LAST_HOUR) -> float:
        """Get response time percentile for time window."""
        return self.response_times.calculate_percentile(time_window, percentile)
    
    def get_most_common_status_codes(self, limit: int = 5) -> List[tuple]:
        """Get most common HTTP status codes."""
        sorted_codes = sorted(self.status_code_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_codes[:limit]


@dataclass
class CombinedMetrics(SerializableModel):
    """Combined metrics from both MCP and REST monitoring."""
    
    server_name: str
    mcp_metrics: MCPMetrics
    rest_metrics: RESTMetrics
    
    # Combined response time metrics
    combined_response_times: MetricSeries = field(init=False)
    
    # Combined availability metrics
    overall_availability_count: int = 0
    overall_unavailability_count: int = 0
    
    def __post_init__(self):
        """Initialize combined metric series after dataclass creation."""
        self.combined_response_times = MetricSeries(
            metric_name="combined_response_time",
            metric_type=MetricType.RESPONSE_TIME,
            server_name=self.server_name,
            monitoring_method="combined"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "mcp_metrics": self.mcp_metrics.to_dict(),
            "rest_metrics": self.rest_metrics.to_dict(),
            "combined_response_times": self.combined_response_times.to_dict(),
            "overall_availability_count": self.overall_availability_count,
            "overall_unavailability_count": self.overall_unavailability_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombinedMetrics':
        """Create instance from dictionary."""
        mcp_metrics = MCPMetrics.from_dict(data.get("mcp_metrics", {}))
        rest_metrics = RESTMetrics.from_dict(data.get("rest_metrics", {}))
        
        instance = cls(
            server_name=data.get("server_name", ""),
            mcp_metrics=mcp_metrics,
            rest_metrics=rest_metrics
        )
        
        # Load combined metric series
        if "combined_response_times" in data:
            instance.combined_response_times = MetricSeries.from_dict(data["combined_response_times"])
        
        instance.overall_availability_count = data.get("overall_availability_count", 0)
        instance.overall_unavailability_count = data.get("overall_unavailability_count", 0)
        
        return instance
    
    def record_combined_response_time(self, mcp_time: float, rest_time: float) -> None:
        """Record combined response time (average of both)."""
        combined_time = (mcp_time + rest_time) / 2.0
        self.combined_response_times.add_data_point(combined_time)
    
    def record_overall_availability(self, is_available: bool) -> None:
        """Record overall system availability."""
        if is_available:
            self.overall_availability_count += 1
        else:
            self.overall_unavailability_count += 1
    
    def get_combined_success_rate(self) -> float:
        """Calculate combined success rate."""
        mcp_total = self.mcp_metrics.total_requests
        rest_total = self.rest_metrics.total_requests
        total_requests = mcp_total + rest_total
        
        if total_requests == 0:
            return 0.0
        
        mcp_successes = self.mcp_metrics.success_count
        rest_successes = self.rest_metrics.success_count
        total_successes = mcp_successes + rest_successes
        
        return total_successes / total_requests
    
    def get_overall_availability_rate(self) -> float:
        """Calculate overall availability rate."""
        total_checks = self.overall_availability_count + self.overall_unavailability_count
        if total_checks == 0:
            return 0.0
        return self.overall_availability_count / total_checks
    
    def get_combined_average_response_time(self, time_window: TimeWindow = TimeWindow.LAST_HOUR) -> float:
        """Get combined average response time."""
        return self.combined_response_times.calculate_average(time_window)


@dataclass
class MetricsAggregationReport(SerializableModel):
    """Aggregated metrics report for a server."""
    
    server_name: str
    report_timestamp: datetime
    time_window: TimeWindow
    
    # MCP metrics summary
    mcp_success_rate: float
    mcp_average_response_time: float
    mcp_p95_response_time: float
    mcp_tools_availability_rate: float
    
    # REST metrics summary
    rest_success_rate: float
    rest_average_response_time: float
    rest_p95_response_time: float
    rest_endpoint_availability_rate: float
    
    # Combined metrics summary
    combined_success_rate: float
    combined_average_response_time: float
    overall_availability_rate: float
    
    # Top status codes and errors
    top_http_status_codes: List[tuple] = field(default_factory=list)
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "report_timestamp": self.report_timestamp.isoformat(),
            "time_window": self.time_window.value,
            "mcp_success_rate": self.mcp_success_rate,
            "mcp_average_response_time": self.mcp_average_response_time,
            "mcp_p95_response_time": self.mcp_p95_response_time,
            "mcp_tools_availability_rate": self.mcp_tools_availability_rate,
            "rest_success_rate": self.rest_success_rate,
            "rest_average_response_time": self.rest_average_response_time,
            "rest_p95_response_time": self.rest_p95_response_time,
            "rest_endpoint_availability_rate": self.rest_endpoint_availability_rate,
            "combined_success_rate": self.combined_success_rate,
            "combined_average_response_time": self.combined_average_response_time,
            "overall_availability_rate": self.overall_availability_rate,
            "top_http_status_codes": self.top_http_status_codes,
            "error_breakdown": self.error_breakdown
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricsAggregationReport':
        """Create instance from dictionary."""
        timestamp = data.get("report_timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            server_name=data.get("server_name", ""),
            report_timestamp=timestamp,
            time_window=TimeWindow(data.get("time_window", "1h")),
            mcp_success_rate=data.get("mcp_success_rate", 0.0),
            mcp_average_response_time=data.get("mcp_average_response_time", 0.0),
            mcp_p95_response_time=data.get("mcp_p95_response_time", 0.0),
            mcp_tools_availability_rate=data.get("mcp_tools_availability_rate", 0.0),
            rest_success_rate=data.get("rest_success_rate", 0.0),
            rest_average_response_time=data.get("rest_average_response_time", 0.0),
            rest_p95_response_time=data.get("rest_p95_response_time", 0.0),
            rest_endpoint_availability_rate=data.get("rest_endpoint_availability_rate", 0.0),
            combined_success_rate=data.get("combined_success_rate", 0.0),
            combined_average_response_time=data.get("combined_average_response_time", 0.0),
            overall_availability_rate=data.get("overall_availability_rate", 0.0),
            top_http_status_codes=data.get("top_http_status_codes", []),
            error_breakdown=data.get("error_breakdown", {})
        )