"""
Status check data models for MCP server monitoring system.

This module contains all data models related to MCP server status checking,
circuit breaker functionality, and health monitoring.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class ServerStatus(Enum):
    """Enumeration of possible server status states."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class CircuitBreakerState(Enum):
    """Enumeration of circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Circuit breaker tripped, requests blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class HealthCheckResult:
    """Result of a single health check operation."""
    server_name: str
    timestamp: datetime
    success: bool
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    tools_count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "tools_count": self.tools_count
        }


@dataclass
class ServerMetrics:
    """Metrics tracking for a specific MCP server."""
    server_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        return 100.0 - self.success_rate
    
    def update_with_result(self, result: HealthCheckResult) -> None:
        """Update metrics with a new health check result."""
        self.total_requests += 1
        
        if result.success:
            self.successful_requests += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_success_time = result.timestamp
            
            # Update average response time (simple moving average)
            if self.successful_requests == 1:
                self.average_response_time_ms = result.response_time_ms
            else:
                self.average_response_time_ms = (
                    (self.average_response_time_ms * (self.successful_requests - 1) + 
                     result.response_time_ms) / self.successful_requests
                )
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = result.timestamp
        
        # Update uptime percentage
        self.uptime_percentage = self.success_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_response_time_ms": self.average_response_time_ms,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "uptime_percentage": self.uptime_percentage,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes
        }


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker functionality."""
    failure_threshold: int = 5  # Number of consecutive failures to open circuit
    recovery_threshold: int = 3  # Number of consecutive successes to close circuit
    timeout_seconds: int = 60   # Time to wait before attempting recovery
    half_open_max_calls: int = 3  # Max calls allowed in half-open state
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MCPStatusCheckConfig:
    """Configuration for MCP server status checking."""
    server_name: str
    endpoint_url: str
    check_interval_seconds: int = 30
    timeout_seconds: int = 10
    jwt_token: Optional[str] = None
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    max_retry_delay_seconds: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "endpoint_url": self.endpoint_url,
            "check_interval_seconds": self.check_interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "jwt_token": "***REDACTED***" if self.jwt_token else None,
            "circuit_breaker": self.circuit_breaker.to_dict(),
            "enabled": self.enabled,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "exponential_backoff": self.exponential_backoff,
            "max_retry_delay_seconds": self.max_retry_delay_seconds
        }


@dataclass
class ServerStatusSummary:
    """Summary of server status for API responses."""
    server_name: str
    status: ServerStatus
    circuit_breaker_state: CircuitBreakerState
    last_check_time: Optional[datetime]
    last_success_time: Optional[datetime]
    last_failure_time: Optional[datetime]
    consecutive_failures: int
    response_time_ms: Optional[float]
    error_message: Optional[str] = None
    tools_available: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "status": self.status.value,
            "circuit_breaker_state": self.circuit_breaker_state.value,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "consecutive_failures": self.consecutive_failures,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "tools_available": self.tools_available
        }


@dataclass
class SystemStatusSummary:
    """Overall system status summary."""
    timestamp: datetime
    total_servers: int
    healthy_servers: int
    unhealthy_servers: int
    degraded_servers: int
    unknown_servers: int
    servers: List[ServerStatusSummary]
    
    @property
    def overall_health_percentage(self) -> float:
        """Calculate overall system health percentage."""
        if self.total_servers == 0:
            return 100.0
        return (self.healthy_servers / self.total_servers) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_servers": self.total_servers,
            "healthy_servers": self.healthy_servers,
            "unhealthy_servers": self.unhealthy_servers,
            "degraded_servers": self.degraded_servers,
            "unknown_servers": self.unknown_servers,
            "overall_health_percentage": self.overall_health_percentage,
            "servers": [server.to_dict() for server in self.servers]
        }


# Default configurations for known MCP servers
DEFAULT_MCP_SERVER_CONFIGS = {
    "restaurant-search-mcp": MCPStatusCheckConfig(
        server_name="restaurant-search-mcp",
        endpoint_url="https://your-gateway-url/mcp/restaurant-search-mcp",
        check_interval_seconds=30,
        timeout_seconds=10,
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_threshold=3,
            timeout_seconds=60
        )
    ),
    "restaurant-search-result-reasoning-mcp": MCPStatusCheckConfig(
        server_name="restaurant-search-result-reasoning-mcp", 
        endpoint_url="https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp",
        check_interval_seconds=30,
        timeout_seconds=10,
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_threshold=3,
            timeout_seconds=60
        )
    )
}


def create_status_check_config(
    server_name: str,
    endpoint_url: str,
    **kwargs
) -> MCPStatusCheckConfig:
    """Factory function to create status check configuration."""
    return MCPStatusCheckConfig(
        server_name=server_name,
        endpoint_url=endpoint_url,
        **kwargs
    )


def serialize_status_data(data: Any) -> str:
    """Serialize status data to JSON string with proper datetime handling."""
    if hasattr(data, 'to_dict'):
        data = data.to_dict()
    elif isinstance(data, list):
        data = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
    
    return json.dumps(data, indent=2, default=str)


def deserialize_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    """Deserialize ISO datetime string back to datetime object."""
    if iso_string is None:
        return None
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None