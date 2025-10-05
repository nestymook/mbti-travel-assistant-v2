"""
Logging models for enhanced MCP status check system.

This module defines structured logging models for dual monitoring operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Log categories for classification."""
    HEALTH_CHECK = "health_check"
    MCP_PROTOCOL = "mcp_protocol"
    HTTP_REQUEST = "http_request"
    AUTHENTICATION = "authentication"
    CIRCUIT_BREAKER = "circuit_breaker"
    METRICS = "metrics"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SYSTEM = "system"


class OperationType(Enum):
    """Types of operations being logged."""
    DUAL_HEALTH_CHECK = "dual_health_check"
    MCP_TOOLS_LIST = "mcp_tools_list"
    REST_HEALTH_CHECK = "rest_health_check"
    RESULT_AGGREGATION = "result_aggregation"
    CIRCUIT_BREAKER_EVALUATION = "circuit_breaker_evaluation"
    AUTHENTICATION = "authentication"
    CONFIGURATION_LOAD = "configuration_load"
    METRICS_COLLECTION = "metrics_collection"


@dataclass
class LogContext:
    """Context information for structured logging."""
    server_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    operation_type: Optional[OperationType] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    additional_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "server_name": self.server_name,
            "endpoint_url": self.endpoint_url,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "operation_type": self.operation_type.value if self.operation_type else None,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            **self.additional_fields
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for logging."""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    network_bytes_sent: Optional[int] = None
    network_bytes_received: Optional[int] = None
    
    def calculate_duration(self) -> float:
        """Calculate duration in milliseconds."""
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds() * 1000
            self.duration_ms = duration
            return duration
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_received": self.network_bytes_received
        }


@dataclass
class SecurityContext:
    """Security context for logging."""
    auth_method: Optional[str] = None
    user_roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_authenticated: bool = False
    token_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "auth_method": self.auth_method,
            "user_roles": self.user_roles,
            "permissions": self.permissions,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_authenticated": self.is_authenticated,
            "token_type": self.token_type
        }


@dataclass
class StructuredLogEntry:
    """Structured log entry for dual monitoring operations."""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    context: Optional[LogContext] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    security_context: Optional[SecurityContext] = None
    error_details: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "context": self.context.to_dict() if self.context else None,
            "performance_metrics": self.performance_metrics.to_dict() if self.performance_metrics else None,
            "security_context": self.security_context.to_dict() if self.security_context else None,
            "error_details": self.error_details,
            "tags": self.tags
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class HealthCheckLogEntry(StructuredLogEntry):
    """Specific log entry for health check operations."""
    server_name: str = ""
    check_type: str = ""  # "mcp", "rest", "dual"
    success: bool = False
    response_time_ms: float = 0.0
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Set category to health check."""
        self.category = LogCategory.HEALTH_CHECK
        if not self.context:
            self.context = LogContext()
        self.context.server_name = self.server_name
        self.context.additional_fields.update({
            "check_type": self.check_type,
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "error_message": self.error_message
        })


@dataclass
class MCPProtocolLogEntry(StructuredLogEntry):
    """Specific log entry for MCP protocol operations."""
    method: str = ""
    request_id: str = ""
    jsonrpc_version: str = "2.0"
    tools_count: Optional[int] = None
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set category to MCP protocol."""
        self.category = LogCategory.MCP_PROTOCOL
        if not self.context:
            self.context = LogContext()
        self.context.operation_type = OperationType.MCP_TOOLS_LIST
        self.context.request_id = self.request_id
        self.context.additional_fields.update({
            "method": self.method,
            "jsonrpc_version": self.jsonrpc_version,
            "tools_count": self.tools_count,
            "validation_errors": self.validation_errors
        })


@dataclass
class HTTPRequestLogEntry(StructuredLogEntry):
    """Specific log entry for HTTP request operations."""
    method: str = ""
    url: str = ""
    status_code: Optional[int] = None
    response_size_bytes: Optional[int] = None
    request_headers: Dict[str, str] = field(default_factory=dict)
    response_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set category to HTTP request."""
        self.category = LogCategory.HTTP_REQUEST
        if not self.context:
            self.context = LogContext()
        self.context.operation_type = OperationType.REST_HEALTH_CHECK
        self.context.endpoint_url = self.url
        self.context.additional_fields.update({
            "method": self.method,
            "status_code": self.status_code,
            "response_size_bytes": self.response_size_bytes,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers
        })


@dataclass
class AuthenticationLogEntry(StructuredLogEntry):
    """Specific log entry for authentication operations."""
    auth_method: str = ""
    success: bool = False
    token_type: Optional[str] = None
    expires_in_seconds: Optional[int] = None
    failure_reason: Optional[str] = None
    
    def __post_init__(self):
        """Set category to authentication."""
        self.category = LogCategory.AUTHENTICATION
        if not self.context:
            self.context = LogContext()
        self.context.operation_type = OperationType.AUTHENTICATION
        self.context.additional_fields.update({
            "auth_method": self.auth_method,
            "success": self.success,
            "token_type": self.token_type,
            "expires_in_seconds": self.expires_in_seconds,
            "failure_reason": self.failure_reason
        })


@dataclass
class CircuitBreakerLogEntry(StructuredLogEntry):
    """Specific log entry for circuit breaker operations."""
    server_name: str = ""
    state: str = ""  # "closed", "open", "half_open"
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    next_attempt_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Set category to circuit breaker."""
        self.category = LogCategory.CIRCUIT_BREAKER
        if not self.context:
            self.context = LogContext()
        self.context.server_name = self.server_name
        self.context.operation_type = OperationType.CIRCUIT_BREAKER_EVALUATION
        self.context.additional_fields.update({
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "next_attempt_time": self.next_attempt_time.isoformat() if self.next_attempt_time else None
        })


@dataclass
class MetricsLogEntry(StructuredLogEntry):
    """Specific log entry for metrics collection."""
    metric_name: str = ""
    metric_value: Union[int, float] = 0
    metric_type: str = "gauge"  # "counter", "gauge", "histogram", "timer"
    labels: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set category to metrics."""
        self.category = LogCategory.METRICS
        if not self.context:
            self.context = LogContext()
        self.context.operation_type = OperationType.METRICS_COLLECTION
        self.context.additional_fields.update({
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_type": self.metric_type,
            "labels": self.labels
        })


class LogEntryBuilder:
    """Builder class for creating structured log entries."""
    
    def __init__(self, level: LogLevel, category: LogCategory, message: str):
        """Initialize log entry builder."""
        self.level = level
        self.category = category
        self.message = message
        self.timestamp = datetime.utcnow()
        self.context = None
        self.performance_metrics = None
        self.security_context = None
        self.error_details = None
        self.tags = []
    
    def with_context(self, context: LogContext) -> 'LogEntryBuilder':
        """Set log context."""
        self.context = context
        return self
    
    def with_performance_metrics(self, metrics: PerformanceMetrics) -> 'LogEntryBuilder':
        """Set performance metrics."""
        self.performance_metrics = metrics
        return self
    
    def with_security_context(self, security: SecurityContext) -> 'LogEntryBuilder':
        """Set security context."""
        self.security_context = security
        return self
    
    def with_error_details(self, error_details: Dict[str, Any]) -> 'LogEntryBuilder':
        """Set error details."""
        self.error_details = error_details
        return self
    
    def with_tags(self, tags: List[str]) -> 'LogEntryBuilder':
        """Set tags."""
        self.tags = tags
        return self
    
    def build(self) -> StructuredLogEntry:
        """Build the log entry."""
        return StructuredLogEntry(
            timestamp=self.timestamp,
            level=self.level,
            category=self.category,
            message=self.message,
            context=self.context,
            performance_metrics=self.performance_metrics,
            security_context=self.security_context,
            error_details=self.error_details,
            tags=self.tags
        )
    
    def build_health_check_entry(self, server_name: str, check_type: str, 
                                success: bool, response_time_ms: float, **kwargs) -> HealthCheckLogEntry:
        """Build health check log entry."""
        return HealthCheckLogEntry(
            timestamp=self.timestamp,
            level=self.level,
            category=LogCategory.HEALTH_CHECK,
            message=self.message,
            context=self.context,
            performance_metrics=self.performance_metrics,
            security_context=self.security_context,
            error_details=self.error_details,
            tags=self.tags,
            server_name=server_name,
            check_type=check_type,
            success=success,
            response_time_ms=response_time_ms,
            **kwargs
        )