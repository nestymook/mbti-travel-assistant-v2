"""
Orchestration Configuration Management System

This module provides comprehensive configuration management for the tool orchestration system,
including YAML configuration loading, environment-specific overrides, and validation.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
from datetime import timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Workflow execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class RankingAlgorithm(Enum):
    """Tool ranking algorithms."""
    WEIGHTED_PERFORMANCE = "weighted_performance"
    CAPABILITY_MATCH = "capability_match"
    HEALTH_PRIORITY = "health_priority"
    ROUND_ROBIN = "round_robin"


@dataclass
class IntentAnalysisConfig:
    """Configuration for intent analysis system."""
    confidence_threshold: float = 0.8
    enable_context_analysis: bool = True
    nlp_model: str = "intent-classifier-v1"
    parameter_extraction_enabled: bool = True
    parameter_extraction_timeout: int = 5


@dataclass
class ToolSelectionConfig:
    """Configuration for tool selection system."""
    ranking_algorithm: RankingAlgorithm = RankingAlgorithm.WEIGHTED_PERFORMANCE
    performance_weight: float = 0.4
    health_weight: float = 0.3
    capability_weight: float = 0.3
    max_fallback_tools: int = 2
    selection_timeout: int = 10


@dataclass
class RetryPolicyConfig:
    """Configuration for retry policies."""
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 60
    retry_on_errors: List[str] = field(default_factory=lambda: [
        "timeout", "connection_error", "service_unavailable"
    ])


@dataclass
class WorkflowEngineConfig:
    """Configuration for workflow engine."""
    max_concurrent_workflows: int = 50
    step_timeout_seconds: int = 30
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    retry_policy: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)


@dataclass
class AlertThresholds:
    """Configuration for alert thresholds."""
    error_rate: float = 0.1
    response_time_ms: int = 10000
    success_rate: float = 0.9


@dataclass
class PerformanceMonitoringConfig:
    """Configuration for performance monitoring."""
    enable_metrics_collection: bool = True
    health_check_interval_seconds: int = 30
    performance_window_seconds: int = 300
    metrics_retention_hours: int = 24
    alert_thresholds: AlertThresholds = field(default_factory=AlertThresholds)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling."""
    enable_circuit_breaker: bool = True
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    graceful_degradation: bool = True
    fallback_strategies: List[str] = field(default_factory=lambda: [
        "alternative_tool", "cached_response", "partial_results"
    ])


@dataclass
class OrchestrationSystemConfig:
    """Main orchestration system configuration."""
    intent_analysis: IntentAnalysisConfig = field(default_factory=IntentAnalysisConfig)
    tool_selection: ToolSelectionConfig = field(default_factory=ToolSelectionConfig)
    workflow_engine: WorkflowEngineConfig = field(default_factory=WorkflowEngineConfig)
    performance_monitoring: PerformanceMonitoringConfig = field(default_factory=PerformanceMonitoringConfig)
    error_handling: ErrorHandlingConfig = field(default_factory=ErrorHandlingConfig)


@dataclass
class HealthCheckConfig:
    """Configuration for tool health checks."""
    endpoint: str = "/health"
    interval_seconds: int = 60
    timeout_seconds: int = 15


@dataclass
class PerformanceConfig:
    """Configuration for tool performance expectations."""
    expected_response_time_ms: int = 2000
    max_response_time_ms: int = 10000
    expected_success_rate: float = 0.98


@dataclass
class ToolConfig:
    """Configuration for individual tools."""
    priority: int = 1
    enabled: bool = True
    capabilities: List[str] = field(default_factory=list)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    structured_logging: bool = True
    correlation_tracking: bool = True
    performance_logging: bool = True
    error_logging: bool = True
    log_destinations: List[str] = field(default_factory=lambda: [
        "console", "file", "agentcore_monitoring"
    ])


@dataclass
class IntegrationsConfig:
    """Configuration for integrations."""
    agentcore_monitoring_enabled: bool = True
    agentcore_monitoring_detailed_logging: bool = True
    agentcore_monitoring_performance_tracking: bool = True
    agentcore_monitoring_health_checks: bool = True
    existing_services_logging_service: bool = True
    existing_services_health_check_service: bool = True
    existing_services_error_handler: bool = True
    existing_services_authentication_manager: bool = True


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class OrchestrationConfig:
    """
    Comprehensive configuration management system for tool orchestration.
    
    Provides YAML configuration loading, environment-specific overrides,
    validation, and runtime configuration management.
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 environment: Optional[str] = None,
                 validate_on_load: bool = True):
        """
        Initialize orchestration configuration.
        
        Args:
            config_path: Path to configuration file (defaults to orchestration_config.yaml)
            environment: Environment name for overrides (development, staging, production)
            validate_on_load: Whether to validate configuration on load
        """
        self.config_path = config_path or self._get_default_config_path()
        self.environment = environment or self._detect_environment()
        self.validate_on_load = validate_on_load
        
        # Configuration data
        self._raw_config: Dict[str, Any] = {}
        self._orchestration: Optional[OrchestrationSystemConfig] = None
        self._tools: Dict[str, ToolConfig] = {}
        self._logging: Optional[LoggingConfig] = None
        self._integrations: Optional[IntegrationsConfig] = None
        
        # Load configuration
        self.load_config()
        
        logger.info(f"Orchestration configuration loaded from {self.config_path} "
                   f"for environment: {self.environment}")
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "orchestration_config.yaml")
    
    def _detect_environment(self) -> str:
        """Detect environment from environment variables."""
        env = os.getenv("ORCHESTRATION_ENV", 
                       os.getenv("ENVIRONMENT", 
                                os.getenv("ENV", "development")))
        return env.lower()
    
    def load_config(self) -> None:
        """Load configuration from YAML file with environment overrides."""
        try:
            # Load base configuration
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._raw_config = yaml.safe_load(file)
            
            # Apply environment-specific overrides
            self._apply_environment_overrides()
            
            # Parse configuration sections
            self._parse_orchestration_config()
            self._parse_tools_config()
            self._parse_logging_config()
            self._parse_integrations_config()
            
            # Validate configuration if requested
            if self.validate_on_load:
                self.validate_configuration()
                
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        environments = self._raw_config.get("environments", {})
        env_config = environments.get(self.environment, {})
        
        if env_config:
            logger.info(f"Applying environment overrides for: {self.environment}")
            self._deep_merge(self._raw_config, env_config)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override configuration into base configuration."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _parse_orchestration_config(self) -> None:
        """Parse orchestration system configuration."""
        orchestration_data = self._raw_config.get("orchestration", {})
        
        # Parse intent analysis config
        intent_data = orchestration_data.get("intent_analysis", {})
        intent_config = IntentAnalysisConfig(
            confidence_threshold=intent_data.get("confidence_threshold", 0.8),
            enable_context_analysis=intent_data.get("enable_context_analysis", True),
            nlp_model=intent_data.get("nlp_model", "intent-classifier-v1"),
            parameter_extraction_enabled=intent_data.get("parameter_extraction", {}).get("enabled", True),
            parameter_extraction_timeout=intent_data.get("parameter_extraction", {}).get("timeout_seconds", 5)
        )
        
        # Parse tool selection config
        selection_data = orchestration_data.get("tool_selection", {})
        selection_config = ToolSelectionConfig(
            ranking_algorithm=RankingAlgorithm(selection_data.get("ranking_algorithm", "weighted_performance")),
            performance_weight=selection_data.get("performance_weight", 0.4),
            health_weight=selection_data.get("health_weight", 0.3),
            capability_weight=selection_data.get("capability_weight", 0.3),
            max_fallback_tools=selection_data.get("max_fallback_tools", 2),
            selection_timeout=selection_data.get("selection_timeout_seconds", 10)
        )
        
        # Parse workflow engine config
        workflow_data = orchestration_data.get("workflow_engine", {})
        retry_data = workflow_data.get("retry_policy", {})
        retry_config = RetryPolicyConfig(
            max_retries=retry_data.get("max_retries", 3),
            backoff_multiplier=retry_data.get("backoff_multiplier", 2.0),
            max_backoff_seconds=retry_data.get("max_backoff_seconds", 60),
            retry_on_errors=retry_data.get("retry_on_errors", [
                "timeout", "connection_error", "service_unavailable"
            ])
        )
        
        workflow_config = WorkflowEngineConfig(
            max_concurrent_workflows=workflow_data.get("max_concurrent_workflows", 50),
            step_timeout_seconds=workflow_data.get("step_timeout_seconds", 30),
            execution_strategy=ExecutionStrategy(workflow_data.get("execution_strategy", "sequential")),
            retry_policy=retry_config
        )
        
        # Parse performance monitoring config
        monitoring_data = orchestration_data.get("performance_monitoring", {})
        alert_data = monitoring_data.get("alert_thresholds", {})
        alert_config = AlertThresholds(
            error_rate=alert_data.get("error_rate", 0.1),
            response_time_ms=alert_data.get("response_time_ms", 10000),
            success_rate=alert_data.get("success_rate", 0.9)
        )
        
        monitoring_config = PerformanceMonitoringConfig(
            enable_metrics_collection=monitoring_data.get("enable_metrics_collection", True),
            health_check_interval_seconds=monitoring_data.get("health_check_interval_seconds", 30),
            performance_window_seconds=monitoring_data.get("performance_window_seconds", 300),
            metrics_retention_hours=monitoring_data.get("metrics_retention_hours", 24),
            alert_thresholds=alert_config
        )
        
        # Parse error handling config
        error_data = orchestration_data.get("error_handling", {})
        cb_data = error_data.get("circuit_breaker", {})
        cb_config = CircuitBreakerConfig(
            failure_threshold=cb_data.get("failure_threshold", 5),
            recovery_timeout_seconds=cb_data.get("recovery_timeout_seconds", 60),
            half_open_max_calls=cb_data.get("half_open_max_calls", 3)
        )
        
        error_config = ErrorHandlingConfig(
            enable_circuit_breaker=error_data.get("enable_circuit_breaker", True),
            circuit_breaker=cb_config,
            graceful_degradation=error_data.get("graceful_degradation", True),
            fallback_strategies=error_data.get("fallback_strategies", [
                "alternative_tool", "cached_response", "partial_results"
            ])
        )
        
        # Create orchestration config
        self._orchestration = OrchestrationSystemConfig(
            intent_analysis=intent_config,
            tool_selection=selection_config,
            workflow_engine=workflow_config,
            performance_monitoring=monitoring_config,
            error_handling=error_config
        )
    
    def _parse_tools_config(self) -> None:
        """Parse tools configuration."""
        tools_data = self._raw_config.get("tools", {})
        
        for tool_name, tool_data in tools_data.items():
            # Parse health check config
            hc_data = tool_data.get("health_check", {})
            health_config = HealthCheckConfig(
                endpoint=hc_data.get("endpoint", "/health"),
                interval_seconds=hc_data.get("interval_seconds", 60),
                timeout_seconds=hc_data.get("timeout_seconds", 15)
            )
            
            # Parse performance config
            perf_data = tool_data.get("performance", {})
            performance_config = PerformanceConfig(
                expected_response_time_ms=perf_data.get("expected_response_time_ms", 2000),
                max_response_time_ms=perf_data.get("max_response_time_ms", 10000),
                expected_success_rate=perf_data.get("expected_success_rate", 0.98)
            )
            
            # Parse circuit breaker config
            cb_data = tool_data.get("circuit_breaker", {})
            cb_config = CircuitBreakerConfig(
                failure_threshold=cb_data.get("failure_threshold", 5),
                recovery_timeout_seconds=cb_data.get("recovery_timeout_seconds", 60),
                half_open_max_calls=cb_data.get("half_open_max_calls", 3)
            )
            
            # Create tool config
            tool_config = ToolConfig(
                priority=tool_data.get("priority", 1),
                enabled=tool_data.get("enabled", True),
                capabilities=tool_data.get("capabilities", []),
                health_check=health_config,
                performance=performance_config,
                circuit_breaker=cb_config
            )
            
            self._tools[tool_name] = tool_config
    
    def _parse_logging_config(self) -> None:
        """Parse logging configuration."""
        logging_data = self._raw_config.get("logging", {})
        
        self._logging = LoggingConfig(
            level=logging_data.get("level", "INFO"),
            structured_logging=logging_data.get("structured_logging", True),
            correlation_tracking=logging_data.get("correlation_tracking", True),
            performance_logging=logging_data.get("performance_logging", True),
            error_logging=logging_data.get("error_logging", True),
            log_destinations=logging_data.get("log_destinations", [
                "console", "file", "agentcore_monitoring"
            ])
        )
    
    def _parse_integrations_config(self) -> None:
        """Parse integrations configuration."""
        integrations_data = self._raw_config.get("integrations", {})
        agentcore_data = integrations_data.get("agentcore_monitoring", {})
        existing_data = integrations_data.get("existing_services", {})
        
        self._integrations = IntegrationsConfig(
            agentcore_monitoring_enabled=agentcore_data.get("enabled", True),
            agentcore_monitoring_detailed_logging=agentcore_data.get("detailed_logging", True),
            agentcore_monitoring_performance_tracking=agentcore_data.get("performance_tracking", True),
            agentcore_monitoring_health_checks=agentcore_data.get("health_checks", True),
            existing_services_logging_service=existing_data.get("logging_service", True),
            existing_services_health_check_service=existing_data.get("health_check_service", True),
            existing_services_error_handler=existing_data.get("error_handler", True),
            existing_services_authentication_manager=existing_data.get("authentication_manager", True)
        )
    
    def validate_configuration(self) -> None:
        """Validate configuration for consistency and correctness."""
        errors = []
        
        # Validate orchestration config
        if self._orchestration:
            if not (0.0 <= self._orchestration.intent_analysis.confidence_threshold <= 1.0):
                errors.append("Intent analysis confidence threshold must be between 0.0 and 1.0")
            
            selection = self._orchestration.tool_selection
            total_weight = selection.performance_weight + selection.health_weight + selection.capability_weight
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"Tool selection weights must sum to 1.0, got {total_weight}")
            
            if self._orchestration.workflow_engine.max_concurrent_workflows <= 0:
                errors.append("Max concurrent workflows must be positive")
            
            if self._orchestration.performance_monitoring.health_check_interval_seconds <= 0:
                errors.append("Health check interval must be positive")
        
        # Validate tools config
        for tool_name, tool_config in self._tools.items():
            if tool_config.priority < 0:
                errors.append(f"Tool {tool_name} priority must be non-negative")
            
            if not tool_config.capabilities:
                errors.append(f"Tool {tool_name} must have at least one capability")
            
            if tool_config.health_check.timeout_seconds <= 0:
                errors.append(f"Tool {tool_name} health check timeout must be positive")
            
            if not (0.0 <= tool_config.performance.expected_success_rate <= 1.0):
                errors.append(f"Tool {tool_name} expected success rate must be between 0.0 and 1.0")
        
        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(errors))
        
        logger.info("Configuration validation passed")
    
    # Property accessors
    @property
    def orchestration(self) -> OrchestrationSystemConfig:
        """Get orchestration system configuration."""
        if self._orchestration is None:
            raise ConfigurationError("Orchestration configuration not loaded")
        return self._orchestration
    
    @property
    def tools(self) -> Dict[str, ToolConfig]:
        """Get tools configuration."""
        return self._tools.copy()
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration."""
        if self._logging is None:
            raise ConfigurationError("Logging configuration not loaded")
        return self._logging
    
    @property
    def integrations(self) -> IntegrationsConfig:
        """Get integrations configuration."""
        if self._integrations is None:
            raise ConfigurationError("Integrations configuration not loaded")
        return self._integrations
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Get configuration for a specific tool."""
        return self._tools.get(tool_name)
    
    def get_enabled_tools(self) -> Dict[str, ToolConfig]:
        """Get all enabled tools."""
        return {name: config for name, config in self._tools.items() if config.enabled}
    
    def get_tools_by_capability(self, capability: str) -> Dict[str, ToolConfig]:
        """Get tools that have a specific capability."""
        return {
            name: config for name, config in self._tools.items()
            if capability in config.capabilities and config.enabled
        }
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading orchestration configuration")
        self.load_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "config_path": self.config_path,
            "environment": self.environment,
            "orchestration": self._raw_config.get("orchestration", {}),
            "tools": self._raw_config.get("tools", {}),
            "logging": self._raw_config.get("logging", {}),
            "integrations": self._raw_config.get("integrations", {})
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"OrchestrationConfig(path={self.config_path}, env={self.environment})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"OrchestrationConfig(config_path='{self.config_path}', "
                f"environment='{self.environment}', "
                f"tools={len(self._tools)}, "
                f"validated={self.validate_on_load})")