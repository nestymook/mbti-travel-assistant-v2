"""
Enhanced MCP Status Check Data Models

This module contains all data models for the enhanced MCP status check system
that supports dual monitoring using both MCP tools/list requests and REST API health checks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
import json
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from models.auth_models import AuthenticationConfig


class ServerStatus(Enum):
    """Server health status enumeration."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class EnhancedCircuitBreakerState(Enum):
    """Enhanced circuit breaker state for dual monitoring."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    MCP_ONLY = "MCP_ONLY"
    REST_ONLY = "REST_ONLY"


class SerializableModel(ABC):
    """Abstract base class for serializable models."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        pass
    
    def to_json(self) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SerializableModel':
        """Create model instance from dictionary."""
        pass


@dataclass
class MCPToolsListRequest(SerializableModel):
    """MCP tools/list JSON-RPC 2.0 request model."""
    
    jsonrpc: str = "2.0"
    method: str = "tools/list"
    id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id
        }
        if self.params:
            result["params"] = self.params
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPToolsListRequest':
        """Create instance from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method", "tools/list"),
            id=data.get("id", str(datetime.now().timestamp())),
            params=data.get("params")
        )
    
    def validate(self) -> List[str]:
        """Validate MCP request format."""
        errors = []
        if self.jsonrpc != "2.0":
            errors.append("Invalid JSON-RPC version, must be '2.0'")
        if self.method != "tools/list":
            errors.append("Invalid method, must be 'tools/list'")
        if not self.id:
            errors.append("Request ID is required")
        return errors


@dataclass
class MCPToolsListResponse(SerializableModel):
    """MCP tools/list JSON-RPC 2.0 response model."""
    
    jsonrpc: str
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPToolsListResponse':
        """Create instance from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id", ""),
            result=data.get("result"),
            error=data.get("error")
        )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Extract tools list from response."""
        if self.result and "tools" in self.result:
            return self.result["tools"]
        return []
    
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.error is None and self.result is not None
    
    def validate(self) -> List[str]:
        """Validate MCP response format."""
        errors = []
        if self.jsonrpc != "2.0":
            errors.append("Invalid JSON-RPC version, must be '2.0'")
        if not self.id:
            errors.append("Response ID is required")
        if self.result is None and self.error is None:
            errors.append("Response must contain either result or error")
        if self.result is not None and self.error is not None:
            errors.append("Response cannot contain both result and error")
        return errors


@dataclass
class MCPValidationResult(SerializableModel):
    """MCP tools/list validation result."""
    
    is_valid: bool
    tools_count: int
    expected_tools_found: List[str]
    missing_tools: List[str]
    validation_errors: List[str]
    tool_schemas_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "tools_count": self.tools_count,
            "expected_tools_found": self.expected_tools_found,
            "missing_tools": self.missing_tools,
            "validation_errors": self.validation_errors,
            "tool_schemas_valid": self.tool_schemas_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPValidationResult':
        """Create instance from dictionary."""
        return cls(
            is_valid=data.get("is_valid", False),
            tools_count=data.get("tools_count", 0),
            expected_tools_found=data.get("expected_tools_found", []),
            missing_tools=data.get("missing_tools", []),
            validation_errors=data.get("validation_errors", []),
            tool_schemas_valid=data.get("tool_schemas_valid", True)
        )


@dataclass
class RESTHealthCheckResponse(SerializableModel):
    """REST health check HTTP response model."""
    
    status_code: int
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]] = None
    response_time_ms: float = 0.0
    url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "response_time_ms": self.response_time_ms,
            "url": self.url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RESTHealthCheckResponse':
        """Create instance from dictionary."""
        return cls(
            status_code=data.get("status_code", 0),
            headers=data.get("headers", {}),
            body=data.get("body"),
            response_time_ms=data.get("response_time_ms", 0.0),
            url=data.get("url", "")
        )
    
    def is_success(self) -> bool:
        """Check if HTTP response indicates success."""
        return 200 <= self.status_code < 300
    
    def get_health_status(self) -> Optional[str]:
        """Extract health status from response body."""
        if self.body and isinstance(self.body, dict):
            return self.body.get("status") or self.body.get("health")
        return None


@dataclass
class RESTValidationResult(SerializableModel):
    """REST health check validation result."""
    
    is_valid: bool
    http_status_valid: bool
    response_format_valid: bool
    health_indicators_present: bool
    validation_errors: List[str]
    server_metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "http_status_valid": self.http_status_valid,
            "response_format_valid": self.response_format_valid,
            "health_indicators_present": self.health_indicators_present,
            "validation_errors": self.validation_errors,
            "server_metrics": self.server_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RESTValidationResult':
        """Create instance from dictionary."""
        return cls(
            is_valid=data.get("is_valid", False),
            http_status_valid=data.get("http_status_valid", False),
            response_format_valid=data.get("response_format_valid", False),
            health_indicators_present=data.get("health_indicators_present", False),
            validation_errors=data.get("validation_errors", []),
            server_metrics=data.get("server_metrics")
        )


@dataclass
class MCPHealthCheckResult(SerializableModel):
    """MCP health check result with tools/list validation data."""
    
    server_name: str
    timestamp: datetime
    success: bool
    response_time_ms: float
    
    # MCP-specific data
    tools_list_response: Optional[MCPToolsListResponse] = None
    tools_count: Optional[int] = None
    expected_tools_found: List[str] = field(default_factory=list)
    missing_tools: List[str] = field(default_factory=list)
    validation_result: Optional[MCPValidationResult] = None
    
    # Request/Response details
    request_id: str = ""
    jsonrpc_version: str = "2.0"
    mcp_error: Optional[Dict[str, Any]] = None
    connection_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "tools_list_response": self.tools_list_response.to_dict() if self.tools_list_response else None,
            "tools_count": self.tools_count,
            "expected_tools_found": self.expected_tools_found,
            "missing_tools": self.missing_tools,
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
            "request_id": self.request_id,
            "jsonrpc_version": self.jsonrpc_version,
            "mcp_error": self.mcp_error,
            "connection_error": self.connection_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPHealthCheckResult':
        """Create instance from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        tools_list_response = None
        if data.get("tools_list_response"):
            tools_list_response = MCPToolsListResponse.from_dict(data["tools_list_response"])
        
        validation_result = None
        if data.get("validation_result"):
            validation_result = MCPValidationResult.from_dict(data["validation_result"])
        
        return cls(
            server_name=data.get("server_name", ""),
            timestamp=timestamp,
            success=data.get("success", False),
            response_time_ms=data.get("response_time_ms", 0.0),
            tools_list_response=tools_list_response,
            tools_count=data.get("tools_count"),
            expected_tools_found=data.get("expected_tools_found", []),
            missing_tools=data.get("missing_tools", []),
            validation_result=validation_result,
            request_id=data.get("request_id", ""),
            jsonrpc_version=data.get("jsonrpc_version", "2.0"),
            mcp_error=data.get("mcp_error"),
            connection_error=data.get("connection_error")
        )


@dataclass
class RESTHealthCheckResult(SerializableModel):
    """REST health check result with HTTP response validation."""
    
    server_name: str
    timestamp: datetime
    success: bool
    response_time_ms: float
    
    # HTTP-specific data
    status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    health_endpoint_url: str = ""
    validation_result: Optional[RESTValidationResult] = None
    
    # Server health data from REST response
    server_metrics: Optional[Dict[str, Any]] = None
    circuit_breaker_states: Optional[Dict[str, Any]] = None
    system_health: Optional[Dict[str, Any]] = None
    
    # Error details
    http_error: Optional[str] = None
    connection_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "response_body": self.response_body,
            "health_endpoint_url": self.health_endpoint_url,
            "validation_result": self.validation_result.to_dict() if self.validation_result else None,
            "server_metrics": self.server_metrics,
            "circuit_breaker_states": self.circuit_breaker_states,
            "system_health": self.system_health,
            "http_error": self.http_error,
            "connection_error": self.connection_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RESTHealthCheckResult':
        """Create instance from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        validation_result = None
        if data.get("validation_result"):
            validation_result = RESTValidationResult.from_dict(data["validation_result"])
        
        return cls(
            server_name=data.get("server_name", ""),
            timestamp=timestamp,
            success=data.get("success", False),
            response_time_ms=data.get("response_time_ms", 0.0),
            status_code=data.get("status_code"),
            response_body=data.get("response_body"),
            health_endpoint_url=data.get("health_endpoint_url", ""),
            validation_result=validation_result,
            server_metrics=data.get("server_metrics"),
            circuit_breaker_states=data.get("circuit_breaker_states"),
            system_health=data.get("system_health"),
            http_error=data.get("http_error"),
            connection_error=data.get("connection_error")
        )


@dataclass
class CombinedHealthMetrics(SerializableModel):
    """Combined health metrics from both MCP and REST checks."""
    
    # Response time metrics
    mcp_response_time_ms: float
    rest_response_time_ms: float
    combined_response_time_ms: float
    
    # Success rate metrics
    mcp_success_rate: float
    rest_success_rate: float
    combined_success_rate: float
    
    # Tool-specific metrics
    tools_available_count: int
    tools_expected_count: int
    tools_availability_percentage: float
    
    # HTTP-specific metrics
    http_status_codes: Dict[int, int] = field(default_factory=dict)
    health_endpoint_availability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mcp_response_time_ms": self.mcp_response_time_ms,
            "rest_response_time_ms": self.rest_response_time_ms,
            "combined_response_time_ms": self.combined_response_time_ms,
            "mcp_success_rate": self.mcp_success_rate,
            "rest_success_rate": self.rest_success_rate,
            "combined_success_rate": self.combined_success_rate,
            "tools_available_count": self.tools_available_count,
            "tools_expected_count": self.tools_expected_count,
            "tools_availability_percentage": self.tools_availability_percentage,
            "http_status_codes": self.http_status_codes,
            "health_endpoint_availability": self.health_endpoint_availability
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombinedHealthMetrics':
        """Create instance from dictionary."""
        return cls(
            mcp_response_time_ms=data.get("mcp_response_time_ms", 0.0),
            rest_response_time_ms=data.get("rest_response_time_ms", 0.0),
            combined_response_time_ms=data.get("combined_response_time_ms", 0.0),
            mcp_success_rate=data.get("mcp_success_rate", 0.0),
            rest_success_rate=data.get("rest_success_rate", 0.0),
            combined_success_rate=data.get("combined_success_rate", 0.0),
            tools_available_count=data.get("tools_available_count", 0),
            tools_expected_count=data.get("tools_expected_count", 0),
            tools_availability_percentage=data.get("tools_availability_percentage", 0.0),
            http_status_codes=data.get("http_status_codes", {}),
            health_endpoint_availability=data.get("health_endpoint_availability", 0.0)
        )


@dataclass
class PriorityConfig(SerializableModel):
    """Priority configuration for dual health check aggregation."""
    
    mcp_priority_weight: float = 0.6
    rest_priority_weight: float = 0.4
    require_both_success_for_healthy: bool = False
    degraded_on_single_failure: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mcp_priority_weight": self.mcp_priority_weight,
            "rest_priority_weight": self.rest_priority_weight,
            "require_both_success_for_healthy": self.require_both_success_for_healthy,
            "degraded_on_single_failure": self.degraded_on_single_failure
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriorityConfig':
        """Create instance from dictionary."""
        return cls(
            mcp_priority_weight=data.get("mcp_priority_weight", 0.6),
            rest_priority_weight=data.get("rest_priority_weight", 0.4),
            require_both_success_for_healthy=data.get("require_both_success_for_healthy", False),
            degraded_on_single_failure=data.get("degraded_on_single_failure", True)
        )
    
    def validate(self) -> List[str]:
        """Validate priority configuration."""
        errors = []
        
        if not (0.0 <= self.mcp_priority_weight <= 1.0):
            errors.append("MCP priority weight must be between 0.0 and 1.0")
        
        if not (0.0 <= self.rest_priority_weight <= 1.0):
            errors.append("REST priority weight must be between 0.0 and 1.0")
        
        total_weight = self.mcp_priority_weight + self.rest_priority_weight
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            errors.append(f"Priority weights must sum to 1.0, got {total_weight}")
        
        return errors


@dataclass
class AggregationConfig(SerializableModel):
    """Configuration for aggregating dual health check results."""
    
    priority_config: PriorityConfig
    health_score_calculation: str = "weighted_average"  # weighted_average, minimum, maximum
    failure_threshold: float = 0.5
    degraded_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "priority_config": self.priority_config.to_dict(),
            "health_score_calculation": self.health_score_calculation,
            "failure_threshold": self.failure_threshold,
            "degraded_threshold": self.degraded_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AggregationConfig':
        """Create instance from dictionary."""
        priority_config = PriorityConfig.from_dict(data.get("priority_config", {}))
        
        return cls(
            priority_config=priority_config,
            health_score_calculation=data.get("health_score_calculation", "weighted_average"),
            failure_threshold=data.get("failure_threshold", 0.5),
            degraded_threshold=data.get("degraded_threshold", 0.7)
        )
    
    def validate(self) -> List[str]:
        """Validate aggregation configuration."""
        errors = []
        
        # Validate priority config
        errors.extend(self.priority_config.validate())
        
        # Validate health score calculation method
        valid_methods = ["weighted_average", "minimum", "maximum"]
        if self.health_score_calculation not in valid_methods:
            errors.append(f"Invalid health score calculation method: {self.health_score_calculation}")
        
        # Validate thresholds
        if not (0.0 <= self.failure_threshold <= 1.0):
            errors.append("Failure threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.degraded_threshold <= 1.0):
            errors.append("Degraded threshold must be between 0.0 and 1.0")
        
        if self.failure_threshold >= self.degraded_threshold:
            errors.append("Failure threshold must be less than degraded threshold")
        
        return errors


@dataclass
class DualHealthCheckResult(SerializableModel):
    """Combined result from both MCP and REST health checks."""
    
    server_name: str
    timestamp: datetime
    overall_status: ServerStatus
    overall_success: bool
    
    # MCP Health Check Results
    mcp_result: Optional[MCPHealthCheckResult] = None
    mcp_success: bool = False
    mcp_response_time_ms: float = 0.0
    mcp_tools_count: Optional[int] = None
    mcp_error_message: Optional[str] = None
    
    # REST Health Check Results
    rest_result: Optional[RESTHealthCheckResult] = None
    rest_success: bool = False
    rest_response_time_ms: float = 0.0
    rest_status_code: Optional[int] = None
    rest_error_message: Optional[str] = None
    
    # Combined Metrics
    combined_response_time_ms: float = 0.0
    health_score: float = 0.0  # 0.0 to 1.0
    available_paths: List[str] = field(default_factory=list)
    combined_metrics: Optional[CombinedHealthMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "overall_success": self.overall_success,
            "mcp_result": self.mcp_result.to_dict() if self.mcp_result else None,
            "mcp_success": self.mcp_success,
            "mcp_response_time_ms": self.mcp_response_time_ms,
            "mcp_tools_count": self.mcp_tools_count,
            "mcp_error_message": self.mcp_error_message,
            "rest_result": self.rest_result.to_dict() if self.rest_result else None,
            "rest_success": self.rest_success,
            "rest_response_time_ms": self.rest_response_time_ms,
            "rest_status_code": self.rest_status_code,
            "rest_error_message": self.rest_error_message,
            "combined_response_time_ms": self.combined_response_time_ms,
            "health_score": self.health_score,
            "available_paths": self.available_paths,
            "combined_metrics": self.combined_metrics.to_dict() if self.combined_metrics else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DualHealthCheckResult':
        """Create instance from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        overall_status = ServerStatus(data.get("overall_status", "UNKNOWN"))
        
        mcp_result = None
        if data.get("mcp_result"):
            mcp_result = MCPHealthCheckResult.from_dict(data["mcp_result"])
        
        rest_result = None
        if data.get("rest_result"):
            rest_result = RESTHealthCheckResult.from_dict(data["rest_result"])
        
        combined_metrics = None
        if data.get("combined_metrics"):
            combined_metrics = CombinedHealthMetrics.from_dict(data["combined_metrics"])
        
        return cls(
            server_name=data.get("server_name", ""),
            timestamp=timestamp,
            overall_status=overall_status,
            overall_success=data.get("overall_success", False),
            mcp_result=mcp_result,
            mcp_success=data.get("mcp_success", False),
            mcp_response_time_ms=data.get("mcp_response_time_ms", 0.0),
            mcp_tools_count=data.get("mcp_tools_count"),
            mcp_error_message=data.get("mcp_error_message"),
            rest_result=rest_result,
            rest_success=data.get("rest_success", False),
            rest_response_time_ms=data.get("rest_response_time_ms", 0.0),
            rest_status_code=data.get("rest_status_code"),
            rest_error_message=data.get("rest_error_message"),
            combined_response_time_ms=data.get("combined_response_time_ms", 0.0),
            health_score=data.get("health_score", 0.0),
            available_paths=data.get("available_paths", []),
            combined_metrics=combined_metrics
        )


@dataclass
class EnhancedServerConfig(SerializableModel):
    """Enhanced server configuration for dual monitoring."""
    
    server_name: str
    mcp_endpoint_url: str
    rest_health_endpoint_url: str
    
    # MCP Configuration
    mcp_enabled: bool = True
    mcp_timeout_seconds: int = 10
    mcp_expected_tools: List[str] = field(default_factory=list)
    mcp_retry_attempts: int = 3
    
    # REST Configuration
    rest_enabled: bool = True
    rest_timeout_seconds: int = 8
    rest_retry_attempts: int = 2
    
    # Authentication (legacy fields for backward compatibility)
    jwt_token: Optional[str] = None
    auth_headers: Dict[str, str] = field(default_factory=dict)
    
    # Enhanced Authentication Configuration
    auth_config: Optional['AuthenticationConfig'] = None
    
    # Aggregation Settings
    mcp_priority_weight: float = 0.6
    rest_priority_weight: float = 0.4
    require_both_success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "server_name": self.server_name,
            "mcp_endpoint_url": self.mcp_endpoint_url,
            "mcp_enabled": self.mcp_enabled,
            "mcp_timeout_seconds": self.mcp_timeout_seconds,
            "mcp_expected_tools": self.mcp_expected_tools,
            "mcp_retry_attempts": self.mcp_retry_attempts,
            "rest_health_endpoint_url": self.rest_health_endpoint_url,
            "rest_enabled": self.rest_enabled,
            "rest_timeout_seconds": self.rest_timeout_seconds,
            "rest_retry_attempts": self.rest_retry_attempts,
            "jwt_token": self.jwt_token,
            "auth_headers": self.auth_headers,
            "auth_config": self.auth_config.to_dict() if self.auth_config else None,
            "mcp_priority_weight": self.mcp_priority_weight,
            "rest_priority_weight": self.rest_priority_weight,
            "require_both_success": self.require_both_success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedServerConfig':
        """Create instance from dictionary."""
        return cls(
            server_name=data.get("server_name", ""),
            mcp_endpoint_url=data.get("mcp_endpoint_url", ""),
            mcp_enabled=data.get("mcp_enabled", True),
            mcp_timeout_seconds=data.get("mcp_timeout_seconds", 10),
            mcp_expected_tools=data.get("mcp_expected_tools", []),
            mcp_retry_attempts=data.get("mcp_retry_attempts", 3),
            rest_health_endpoint_url=data.get("rest_health_endpoint_url", ""),
            rest_enabled=data.get("rest_enabled", True),
            rest_timeout_seconds=data.get("rest_timeout_seconds", 8),
            rest_retry_attempts=data.get("rest_retry_attempts", 2),
            jwt_token=data.get("jwt_token"),
            auth_headers=data.get("auth_headers", {}),
            auth_config=None,  # Will be set separately to avoid circular imports
            mcp_priority_weight=data.get("mcp_priority_weight", 0.6),
            rest_priority_weight=data.get("rest_priority_weight", 0.4),
            require_both_success=data.get("require_both_success", False)
        )
    
    def validate(self) -> List[str]:
        """Validate server configuration."""
        errors = []
        
        # Validate required fields
        if not self.server_name:
            errors.append("Server name is required")
        
        if self.mcp_enabled and not self.mcp_endpoint_url:
            errors.append("MCP endpoint URL is required when MCP is enabled")
        
        if self.rest_enabled and not self.rest_health_endpoint_url:
            errors.append("REST health endpoint URL is required when REST is enabled")
        
        if not self.mcp_enabled and not self.rest_enabled:
            errors.append("At least one monitoring method (MCP or REST) must be enabled")
        
        # Validate timeout values
        if self.mcp_timeout_seconds <= 0:
            errors.append("MCP timeout must be positive")
        
        if self.rest_timeout_seconds <= 0:
            errors.append("REST timeout must be positive")
        
        # Validate retry attempts
        if self.mcp_retry_attempts < 0:
            errors.append("MCP retry attempts cannot be negative")
        
        if self.rest_retry_attempts < 0:
            errors.append("REST retry attempts cannot be negative")
        
        # Validate priority weights
        if not (0.0 <= self.mcp_priority_weight <= 1.0):
            errors.append("MCP priority weight must be between 0.0 and 1.0")
        
        if not (0.0 <= self.rest_priority_weight <= 1.0):
            errors.append("REST priority weight must be between 0.0 and 1.0")
        
        total_weight = self.mcp_priority_weight + self.rest_priority_weight
        if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
            errors.append(f"Priority weights must sum to 1.0, got {total_weight}")
        
        return errors
    
    def get_priority_config(self) -> PriorityConfig:
        """Get priority configuration from server config."""
        return PriorityConfig(
            mcp_priority_weight=self.mcp_priority_weight,
            rest_priority_weight=self.rest_priority_weight,
            require_both_success_for_healthy=self.require_both_success,
            degraded_on_single_failure=True
        )
    
    def get_aggregation_config(self) -> AggregationConfig:
        """Get aggregation configuration from server config."""
        return AggregationConfig(
            priority_config=self.get_priority_config(),
            health_score_calculation="weighted_average",
            failure_threshold=0.5,
            degraded_threshold=0.7
        )