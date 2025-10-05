"""
Enhanced Status Configuration Classes

This module contains configuration classes for the enhanced MCP status check system
supporting dual monitoring with MCP and REST health checks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import yaml
from datetime import datetime
from enum import Enum

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.dual_health_models import SerializableModel, EnhancedServerConfig


class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigValidationError(ConfigurationError):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"


@dataclass
class MCPHealthCheckConfig(SerializableModel):
    """Configuration for MCP health checks."""
    
    enabled: bool = True
    default_timeout_seconds: int = 10
    default_retry_attempts: int = 3
    tools_list_validation: bool = True
    expected_tools_validation: bool = True
    default_expected_tools: List[str] = field(default_factory=list)
    request_timeout_ms: int = 30000
    connection_pool_size: int = 10
    
    # Authentication settings
    jwt_auth_enabled: bool = False
    jwt_discovery_url: Optional[str] = None
    jwt_audience: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "default_timeout_seconds": self.default_timeout_seconds,
            "default_retry_attempts": self.default_retry_attempts,
            "tools_list_validation": self.tools_list_validation,
            "expected_tools_validation": self.expected_tools_validation,
            "default_expected_tools": self.default_expected_tools,
            "request_timeout_ms": self.request_timeout_ms,
            "connection_pool_size": self.connection_pool_size,
            "jwt_auth_enabled": self.jwt_auth_enabled,
            "jwt_discovery_url": self.jwt_discovery_url,
            "jwt_audience": self.jwt_audience
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPHealthCheckConfig':
        """Create instance from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            default_timeout_seconds=data.get("default_timeout_seconds", 10),
            default_retry_attempts=data.get("default_retry_attempts", 3),
            tools_list_validation=data.get("tools_list_validation", True),
            expected_tools_validation=data.get("expected_tools_validation", True),
            default_expected_tools=data.get("default_expected_tools", []),
            request_timeout_ms=data.get("request_timeout_ms", 30000),
            connection_pool_size=data.get("connection_pool_size", 10),
            jwt_auth_enabled=data.get("jwt_auth_enabled", False),
            jwt_discovery_url=data.get("jwt_discovery_url"),
            jwt_audience=data.get("jwt_audience")
        )
    
    def validate(self) -> List[str]:
        """Validate MCP health check configuration."""
        errors = []
        
        if self.default_timeout_seconds <= 0:
            errors.append("MCP default timeout must be positive")
        
        if self.default_retry_attempts < 0:
            errors.append("MCP retry attempts cannot be negative")
        
        if self.request_timeout_ms <= 0:
            errors.append("MCP request timeout must be positive")
        
        if self.connection_pool_size <= 0:
            errors.append("MCP connection pool size must be positive")
        
        if self.jwt_auth_enabled and not self.jwt_discovery_url:
            errors.append("JWT discovery URL is required when JWT auth is enabled")
        
        return errors


@dataclass
class RESTHealthCheckConfig(SerializableModel):
    """Configuration for REST health checks."""
    
    enabled: bool = True
    default_timeout_seconds: int = 8
    default_retry_attempts: int = 2
    health_endpoint_path: str = "/status/health"
    metrics_endpoint_path: str = "/status/metrics"
    expected_status_codes: List[int] = field(default_factory=lambda: [200, 201, 202])
    retry_backoff_factor: float = 1.5
    max_retry_delay_seconds: int = 30
    connection_pool_size: int = 20
    
    # Response validation settings
    validate_response_format: bool = True
    required_health_fields: List[str] = field(default_factory=lambda: ["status"])
    
    # Authentication settings
    auth_type: str = "none"  # none, bearer, basic, custom
    auth_header_name: str = "Authorization"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "default_timeout_seconds": self.default_timeout_seconds,
            "default_retry_attempts": self.default_retry_attempts,
            "health_endpoint_path": self.health_endpoint_path,
            "metrics_endpoint_path": self.metrics_endpoint_path,
            "expected_status_codes": self.expected_status_codes,
            "retry_backoff_factor": self.retry_backoff_factor,
            "max_retry_delay_seconds": self.max_retry_delay_seconds,
            "connection_pool_size": self.connection_pool_size,
            "validate_response_format": self.validate_response_format,
            "required_health_fields": self.required_health_fields,
            "auth_type": self.auth_type,
            "auth_header_name": self.auth_header_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RESTHealthCheckConfig':
        """Create instance from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            default_timeout_seconds=data.get("default_timeout_seconds", 8),
            default_retry_attempts=data.get("default_retry_attempts", 2),
            health_endpoint_path=data.get("health_endpoint_path", "/status/health"),
            metrics_endpoint_path=data.get("metrics_endpoint_path", "/status/metrics"),
            expected_status_codes=data.get("expected_status_codes", [200, 201, 202]),
            retry_backoff_factor=data.get("retry_backoff_factor", 1.5),
            max_retry_delay_seconds=data.get("max_retry_delay_seconds", 30),
            connection_pool_size=data.get("connection_pool_size", 20),
            validate_response_format=data.get("validate_response_format", True),
            required_health_fields=data.get("required_health_fields", ["status"]),
            auth_type=data.get("auth_type", "none"),
            auth_header_name=data.get("auth_header_name", "Authorization")
        )
    
    def validate(self) -> List[str]:
        """Validate REST health check configuration."""
        errors = []
        
        if self.default_timeout_seconds <= 0:
            errors.append("REST default timeout must be positive")
        
        if self.default_retry_attempts < 0:
            errors.append("REST retry attempts cannot be negative")
        
        if not self.health_endpoint_path.startswith("/"):
            errors.append("Health endpoint path must start with '/'")
        
        if not self.metrics_endpoint_path.startswith("/"):
            errors.append("Metrics endpoint path must start with '/'")
        
        if self.retry_backoff_factor <= 0:
            errors.append("Retry backoff factor must be positive")
        
        if self.max_retry_delay_seconds <= 0:
            errors.append("Max retry delay must be positive")
        
        if self.connection_pool_size <= 0:
            errors.append("REST connection pool size must be positive")
        
        valid_auth_types = ["none", "bearer", "basic", "custom"]
        if self.auth_type not in valid_auth_types:
            errors.append(f"Invalid auth type: {self.auth_type}. Must be one of {valid_auth_types}")
        
        return errors


@dataclass
class ResultAggregationConfig(SerializableModel):
    """Configuration for aggregating dual health check results."""
    
    mcp_priority_weight: float = 0.6
    rest_priority_weight: float = 0.4
    require_both_success_for_healthy: bool = False
    degraded_on_single_failure: bool = True
    health_score_calculation: str = "weighted_average"
    failure_threshold: float = 0.5
    degraded_threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mcp_priority_weight": self.mcp_priority_weight,
            "rest_priority_weight": self.rest_priority_weight,
            "require_both_success_for_healthy": self.require_both_success_for_healthy,
            "degraded_on_single_failure": self.degraded_on_single_failure,
            "health_score_calculation": self.health_score_calculation,
            "failure_threshold": self.failure_threshold,
            "degraded_threshold": self.degraded_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultAggregationConfig':
        """Create instance from dictionary."""
        return cls(
            mcp_priority_weight=data.get("mcp_priority_weight", 0.6),
            rest_priority_weight=data.get("rest_priority_weight", 0.4),
            require_both_success_for_healthy=data.get("require_both_success_for_healthy", False),
            degraded_on_single_failure=data.get("degraded_on_single_failure", True),
            health_score_calculation=data.get("health_score_calculation", "weighted_average"),
            failure_threshold=data.get("failure_threshold", 0.5),
            degraded_threshold=data.get("degraded_threshold", 0.7)
        )
    
    def validate(self) -> List[str]:
        """Validate result aggregation configuration."""
        errors = []
        
        if not (0.0 <= self.mcp_priority_weight <= 1.0):
            errors.append("MCP priority weight must be between 0.0 and 1.0")
        
        if not (0.0 <= self.rest_priority_weight <= 1.0):
            errors.append("REST priority weight must be between 0.0 and 1.0")
        
        total_weight = self.mcp_priority_weight + self.rest_priority_weight
        if abs(total_weight - 1.0) > 0.001:
            errors.append(f"Priority weights must sum to 1.0, got {total_weight}")
        
        valid_calculations = ["weighted_average", "minimum", "maximum"]
        if self.health_score_calculation not in valid_calculations:
            errors.append(f"Invalid health score calculation: {self.health_score_calculation}")
        
        if not (0.0 <= self.failure_threshold <= 1.0):
            errors.append("Failure threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.degraded_threshold <= 1.0):
            errors.append("Degraded threshold must be between 0.0 and 1.0")
        
        if self.failure_threshold >= self.degraded_threshold:
            errors.append("Failure threshold must be less than degraded threshold")
        
        return errors


@dataclass
class CircuitBreakerConfig(SerializableModel):
    """Configuration for enhanced circuit breaker."""
    
    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3
    
    # Dual path circuit breaker settings
    mcp_circuit_breaker_enabled: bool = True
    rest_circuit_breaker_enabled: bool = True
    independent_circuit_breakers: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
            "half_open_max_calls": self.half_open_max_calls,
            "mcp_circuit_breaker_enabled": self.mcp_circuit_breaker_enabled,
            "rest_circuit_breaker_enabled": self.rest_circuit_breaker_enabled,
            "independent_circuit_breakers": self.independent_circuit_breakers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircuitBreakerConfig':
        """Create instance from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            failure_threshold=data.get("failure_threshold", 5),
            recovery_timeout_seconds=data.get("recovery_timeout_seconds", 60),
            half_open_max_calls=data.get("half_open_max_calls", 3),
            mcp_circuit_breaker_enabled=data.get("mcp_circuit_breaker_enabled", True),
            rest_circuit_breaker_enabled=data.get("rest_circuit_breaker_enabled", True),
            independent_circuit_breakers=data.get("independent_circuit_breakers", True)
        )
    
    def validate(self) -> List[str]:
        """Validate circuit breaker configuration."""
        errors = []
        
        if self.failure_threshold <= 0:
            errors.append("Failure threshold must be positive")
        
        if self.recovery_timeout_seconds <= 0:
            errors.append("Recovery timeout must be positive")
        
        if self.half_open_max_calls <= 0:
            errors.append("Half-open max calls must be positive")
        
        return errors


@dataclass
class MonitoringConfig(SerializableModel):
    """Configuration for monitoring and metrics collection."""
    
    enabled: bool = True
    metrics_collection_enabled: bool = True
    health_check_interval_seconds: int = 30
    metrics_retention_hours: int = 24
    
    # Performance monitoring
    concurrent_health_checks: bool = True
    max_concurrent_checks: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "metrics_collection_enabled": self.metrics_collection_enabled,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "metrics_retention_hours": self.metrics_retention_hours,
            "concurrent_health_checks": self.concurrent_health_checks,
            "max_concurrent_checks": self.max_concurrent_checks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringConfig':
        """Create instance from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            metrics_collection_enabled=data.get("metrics_collection_enabled", True),
            health_check_interval_seconds=data.get("health_check_interval_seconds", 30),
            metrics_retention_hours=data.get("metrics_retention_hours", 24),
            concurrent_health_checks=data.get("concurrent_health_checks", True),
            max_concurrent_checks=data.get("max_concurrent_checks", 10)
        )
    
    def validate(self) -> List[str]:
        """Validate monitoring configuration."""
        errors = []
        
        if self.health_check_interval_seconds <= 0:
            errors.append("Health check interval must be positive")
        
        if self.metrics_retention_hours <= 0:
            errors.append("Metrics retention hours must be positive")
        
        if self.max_concurrent_checks <= 0:
            errors.append("Max concurrent checks must be positive")
        
        return errors


@dataclass
class EnhancedStatusConfig(SerializableModel):
    """Main configuration class for enhanced MCP status check system."""
    
    # System settings
    system_name: str = "enhanced-mcp-status-check"
    version: str = "1.0.0"
    dual_monitoring_enabled: bool = True
    
    # Component configurations
    mcp_health_checks: MCPHealthCheckConfig = field(default_factory=MCPHealthCheckConfig)
    rest_health_checks: RESTHealthCheckConfig = field(default_factory=RESTHealthCheckConfig)
    result_aggregation: ResultAggregationConfig = field(default_factory=ResultAggregationConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Server configurations
    servers: List[EnhancedServerConfig] = field(default_factory=list)
    
    # Configuration metadata
    config_file_path: Optional[str] = None
    last_modified: Optional[datetime] = None
    config_format: ConfigFormat = ConfigFormat.JSON
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "system_name": self.system_name,
            "version": self.version,
            "dual_monitoring_enabled": self.dual_monitoring_enabled,
            "mcp_health_checks": self.mcp_health_checks.to_dict(),
            "rest_health_checks": self.rest_health_checks.to_dict(),
            "result_aggregation": self.result_aggregation.to_dict(),
            "circuit_breaker": self.circuit_breaker.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "servers": [server.to_dict() for server in self.servers],
            "config_file_path": self.config_file_path,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "config_format": self.config_format.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedStatusConfig':
        """Create instance from dictionary."""
        last_modified = data.get("last_modified")
        if isinstance(last_modified, str):
            last_modified = datetime.fromisoformat(last_modified)
        
        config_format = ConfigFormat(data.get("config_format", "json"))
        
        servers = []
        for server_data in data.get("servers", []):
            servers.append(EnhancedServerConfig.from_dict(server_data))
        
        return cls(
            system_name=data.get("system_name", "enhanced-mcp-status-check"),
            version=data.get("version", "1.0.0"),
            dual_monitoring_enabled=data.get("dual_monitoring_enabled", True),
            mcp_health_checks=MCPHealthCheckConfig.from_dict(data.get("mcp_health_checks", {})),
            rest_health_checks=RESTHealthCheckConfig.from_dict(data.get("rest_health_checks", {})),
            result_aggregation=ResultAggregationConfig.from_dict(data.get("result_aggregation", {})),
            circuit_breaker=CircuitBreakerConfig.from_dict(data.get("circuit_breaker", {})),
            monitoring=MonitoringConfig.from_dict(data.get("monitoring", {})),
            servers=servers,
            config_file_path=data.get("config_file_path"),
            last_modified=last_modified,
            config_format=config_format
        )
    
    def validate(self) -> List[str]:
        """Validate entire configuration."""
        errors = []
        
        # Validate system settings
        if not self.system_name:
            errors.append("System name is required")
        
        if not self.version:
            errors.append("Version is required")
        
        if not self.dual_monitoring_enabled:
            if not self.mcp_health_checks.enabled and not self.rest_health_checks.enabled:
                errors.append("At least one monitoring method must be enabled")
        
        # Validate component configurations
        errors.extend(self.mcp_health_checks.validate())
        errors.extend(self.rest_health_checks.validate())
        errors.extend(self.result_aggregation.validate())
        errors.extend(self.circuit_breaker.validate())
        errors.extend(self.monitoring.validate())
        
        # Validate server configurations
        server_names = set()
        for i, server in enumerate(self.servers):
            server_errors = server.validate()
            for error in server_errors:
                errors.append(f"Server {i} ({server.server_name}): {error}")
            
            # Check for duplicate server names
            if server.server_name in server_names:
                errors.append(f"Duplicate server name: {server.server_name}")
            server_names.add(server.server_name)
        
        return errors
    
    def get_server_config(self, server_name: str) -> Optional[EnhancedServerConfig]:
        """Get configuration for a specific server."""
        for server in self.servers:
            if server.server_name == server_name:
                return server
        return None
    
    def add_server(self, server_config: EnhancedServerConfig) -> None:
        """Add a server configuration."""
        # Remove existing server with same name
        self.servers = [s for s in self.servers if s.server_name != server_config.server_name]
        self.servers.append(server_config)
    
    def remove_server(self, server_name: str) -> bool:
        """Remove a server configuration."""
        original_count = len(self.servers)
        self.servers = [s for s in self.servers if s.server_name != server_name]
        return len(self.servers) < original_count
    
    def is_dual_monitoring_enabled(self) -> bool:
        """Check if dual monitoring is enabled and configured."""
        return (
            self.dual_monitoring_enabled and
            self.mcp_health_checks.enabled and
            self.rest_health_checks.enabled
        )
    
    def get_enabled_monitoring_methods(self) -> List[str]:
        """Get list of enabled monitoring methods."""
        methods = []
        if self.mcp_health_checks.enabled:
            methods.append("mcp")
        if self.rest_health_checks.enabled:
            methods.append("rest")
        return methods
    
    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, indent=2)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        file_path = Path(file_path)
        
        # Determine format from file extension
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            content = self.to_yaml()
            self.config_format = ConfigFormat.YAML
        else:
            content = self.to_json()
            self.config_format = ConfigFormat.JSON
        
        # Update metadata
        self.config_file_path = str(file_path)
        self.last_modified = datetime.now()
        
        # Write file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'EnhancedStatusConfig':
        """Load configuration from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine format from file extension
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
                config_format = ConfigFormat.YAML
            else:
                data = json.loads(content)
                config_format = ConfigFormat.JSON
            
            # Create configuration instance
            config = cls.from_dict(data)
            config.config_file_path = str(file_path)
            config.config_format = config_format
            config.last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            return config
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Invalid configuration file format: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    @classmethod
    def create_default(cls) -> 'EnhancedStatusConfig':
        """Create default configuration."""
        return cls(
            system_name="enhanced-mcp-status-check",
            version="1.0.0",
            dual_monitoring_enabled=True,
            mcp_health_checks=MCPHealthCheckConfig(),
            rest_health_checks=RESTHealthCheckConfig(),
            result_aggregation=ResultAggregationConfig(),
            circuit_breaker=CircuitBreakerConfig(),
            monitoring=MonitoringConfig(),
            servers=[]
        )