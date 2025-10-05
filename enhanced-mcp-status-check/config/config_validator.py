"""
Configuration Validator

This module provides comprehensive validation for enhanced MCP status check configurations
with custom validation rules and detailed error reporting.
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Union
from urllib.parse import urlparse
from pathlib import Path

from .enhanced_status_config import (
    EnhancedStatusConfig,
    MCPHealthCheckConfig,
    RESTHealthCheckConfig,
    ResultAggregationConfig,
    CircuitBreakerConfig,
    MonitoringConfig,
    ConfigValidationError
)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models.dual_health_models import EnhancedServerConfig


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """Add validation info."""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info)
        }


class ValidationRule(ABC):
    """Abstract base class for validation rules."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        """Validate configuration against this rule."""
        pass


class URLValidationRule(ValidationRule):
    """Validation rule for URL formats."""
    
    def __init__(self):
        super().__init__(
            "url_validation",
            "Validates URL formats for MCP and REST endpoints"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        for server in config.servers:
            # Validate MCP endpoint URL
            if server.mcp_enabled and server.mcp_endpoint_url:
                if not self._is_valid_url(server.mcp_endpoint_url):
                    result.add_error(f"Server '{server.server_name}': Invalid MCP endpoint URL: {server.mcp_endpoint_url}")
                elif not self._is_mcp_url(server.mcp_endpoint_url):
                    result.add_warning(f"Server '{server.server_name}': MCP endpoint URL may not be valid MCP protocol")
            
            # Validate REST endpoint URL
            if server.rest_enabled and server.rest_health_endpoint_url:
                if not self._is_valid_url(server.rest_health_endpoint_url):
                    result.add_error(f"Server '{server.server_name}': Invalid REST endpoint URL: {server.rest_health_endpoint_url}")
                elif not self._is_http_url(server.rest_health_endpoint_url):
                    result.add_warning(f"Server '{server.server_name}': REST endpoint should use HTTP/HTTPS protocol")
        
        return result
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _is_mcp_url(self, url: str) -> bool:
        """Check if URL looks like MCP endpoint."""
        try:
            parsed = urlparse(url)
            # MCP can use HTTP, HTTPS, or WebSocket protocols
            return parsed.scheme.lower() in ['http', 'https', 'ws', 'wss']
        except Exception:
            return False
    
    def _is_http_url(self, url: str) -> bool:
        """Check if URL uses HTTP/HTTPS protocol."""
        try:
            parsed = urlparse(url)
            return parsed.scheme.lower() in ['http', 'https']
        except Exception:
            return False


class TimeoutValidationRule(ValidationRule):
    """Validation rule for timeout configurations."""
    
    def __init__(self):
        super().__init__(
            "timeout_validation",
            "Validates timeout configurations are reasonable"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        # Check global timeout settings
        if config.mcp_health_checks.default_timeout_seconds > 300:  # 5 minutes
            result.add_warning("MCP default timeout is very high (>5 minutes)")
        
        if config.rest_health_checks.default_timeout_seconds > 300:
            result.add_warning("REST default timeout is very high (>5 minutes)")
        
        if config.mcp_health_checks.default_timeout_seconds < 1:
            result.add_error("MCP default timeout is too low (<1 second)")
        
        if config.rest_health_checks.default_timeout_seconds < 1:
            result.add_error("REST default timeout is too low (<1 second)")
        
        # Check server-specific timeouts
        for server in config.servers:
            if server.mcp_timeout_seconds > 300:
                result.add_warning(f"Server '{server.server_name}': MCP timeout is very high (>5 minutes)")
            
            if server.rest_timeout_seconds > 300:
                result.add_warning(f"Server '{server.server_name}': REST timeout is very high (>5 minutes)")
            
            if server.mcp_timeout_seconds < 1:
                result.add_error(f"Server '{server.server_name}': MCP timeout is too low (<1 second)")
            
            if server.rest_timeout_seconds < 1:
                result.add_error(f"Server '{server.server_name}': REST timeout is too low (<1 second)")
        
        return result


class MonitoringIntervalValidationRule(ValidationRule):
    """Validation rule for monitoring intervals."""
    
    def __init__(self):
        super().__init__(
            "monitoring_interval_validation",
            "Validates monitoring intervals are reasonable"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        interval = config.monitoring.health_check_interval_seconds
        
        if interval < 5:
            result.add_warning("Health check interval is very frequent (<5 seconds)")
        elif interval < 1:
            result.add_error("Health check interval is too frequent (<1 second)")
        
        if interval > 3600:  # 1 hour
            result.add_warning("Health check interval is very infrequent (>1 hour)")
        
        # Check if interval is reasonable compared to timeouts
        max_timeout = max(
            config.mcp_health_checks.default_timeout_seconds,
            config.rest_health_checks.default_timeout_seconds
        )
        
        if interval < max_timeout * 2:
            result.add_warning(
                f"Health check interval ({interval}s) should be at least 2x the maximum timeout ({max_timeout}s)"
            )
        
        return result


class ServerConfigValidationRule(ValidationRule):
    """Validation rule for server configurations."""
    
    def __init__(self):
        super().__init__(
            "server_config_validation",
            "Validates server configurations are complete and consistent"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        if not config.servers:
            result.add_warning("No servers configured for monitoring")
            return result
        
        server_names = set()
        
        for server in config.servers:
            # Check for duplicate names
            if server.server_name in server_names:
                result.add_error(f"Duplicate server name: {server.server_name}")
            server_names.add(server.server_name)
            
            # Check if at least one monitoring method is enabled
            if not server.mcp_enabled and not server.rest_enabled:
                result.add_error(f"Server '{server.server_name}': At least one monitoring method must be enabled")
            
            # Check if enabled methods have valid URLs
            if server.mcp_enabled and not server.mcp_endpoint_url:
                result.add_error(f"Server '{server.server_name}': MCP endpoint URL required when MCP is enabled")
            
            if server.rest_enabled and not server.rest_health_endpoint_url:
                result.add_error(f"Server '{server.server_name}': REST endpoint URL required when REST is enabled")
            
            # Check priority weights
            total_weight = server.mcp_priority_weight + server.rest_priority_weight
            if abs(total_weight - 1.0) > 0.001:
                result.add_error(f"Server '{server.server_name}': Priority weights must sum to 1.0, got {total_weight}")
            
            # Check expected tools configuration
            if server.mcp_enabled and config.mcp_health_checks.expected_tools_validation:
                if not server.mcp_expected_tools and not config.mcp_health_checks.default_expected_tools:
                    result.add_warning(f"Server '{server.server_name}': No expected tools configured for validation")
        
        return result


class SecurityValidationRule(ValidationRule):
    """Validation rule for security configurations."""
    
    def __init__(self):
        super().__init__(
            "security_validation",
            "Validates security configurations and best practices"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        # Check JWT configuration
        if config.mcp_health_checks.jwt_auth_enabled:
            if not config.mcp_health_checks.jwt_discovery_url:
                result.add_error("JWT discovery URL is required when JWT auth is enabled")
            else:
                # Validate JWT discovery URL format
                if not config.mcp_health_checks.jwt_discovery_url.endswith('/.well-known/openid-configuration'):
                    result.add_warning("JWT discovery URL should end with '/.well-known/openid-configuration'")
        
        # Check for insecure URLs in production-like environments
        for server in config.servers:
            if server.mcp_endpoint_url and server.mcp_endpoint_url.startswith('http://'):
                result.add_warning(f"Server '{server.server_name}': MCP endpoint uses insecure HTTP protocol")
            
            if server.rest_health_endpoint_url and server.rest_health_endpoint_url.startswith('http://'):
                result.add_warning(f"Server '{server.server_name}': REST endpoint uses insecure HTTP protocol")
            
            # Check for hardcoded tokens (basic check)
            if server.jwt_token and len(server.jwt_token) < 20:
                result.add_warning(f"Server '{server.server_name}': JWT token appears to be too short")
        
        return result


class PerformanceValidationRule(ValidationRule):
    """Validation rule for performance configurations."""
    
    def __init__(self):
        super().__init__(
            "performance_validation",
            "Validates performance-related configurations"
        )
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        result = ValidationResult(True, [], [], [])
        
        # Check connection pool sizes
        if config.mcp_health_checks.connection_pool_size > 100:
            result.add_warning("MCP connection pool size is very large (>100)")
        
        if config.rest_health_checks.connection_pool_size > 100:
            result.add_warning("REST connection pool size is very large (>100)")
        
        # Check concurrent checks configuration
        if config.monitoring.concurrent_health_checks:
            max_concurrent = config.monitoring.max_concurrent_checks
            server_count = len(config.servers)
            
            if max_concurrent > server_count * 2:
                result.add_warning(
                    f"Max concurrent checks ({max_concurrent}) is much higher than server count ({server_count})"
                )
            
            if max_concurrent > 50:
                result.add_warning("Max concurrent checks is very high (>50)")
        
        # Check retry configurations
        for server in config.servers:
            if server.mcp_retry_attempts > 10:
                result.add_warning(f"Server '{server.server_name}': MCP retry attempts is very high (>10)")
            
            if server.rest_retry_attempts > 10:
                result.add_warning(f"Server '{server.server_name}': REST retry attempts is very high (>10)")
        
        return result


class ConfigValidator:
    """Main configuration validator with pluggable rules."""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default validation rules."""
        self.rules = [
            URLValidationRule(),
            TimeoutValidationRule(),
            MonitoringIntervalValidationRule(),
            ServerConfigValidationRule(),
            SecurityValidationRule(),
            PerformanceValidationRule()
        ]
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add custom validation rule."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove validation rule by name."""
        original_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.name != rule_name]
        return len(self.rules) < original_count
    
    def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
        """Validate configuration using all rules."""
        logger.info("Starting comprehensive configuration validation")
        
        overall_result = ValidationResult(True, [], [], [])
        
        # First, run basic validation from the config itself
        basic_errors = config.validate()
        for error in basic_errors:
            overall_result.add_error(error)
        
        # Then run all validation rules
        for rule in self.rules:
            try:
                logger.debug(f"Running validation rule: {rule.name}")
                rule_result = rule.validate(config)
                overall_result.merge(rule_result)
            except Exception as e:
                logger.error(f"Error in validation rule '{rule.name}': {e}")
                overall_result.add_error(f"Validation rule '{rule.name}' failed: {e}")
        
        # Log validation summary
        if overall_result.is_valid:
            logger.info(f"Configuration validation passed with {len(overall_result.warnings)} warnings")
        else:
            logger.error(f"Configuration validation failed with {len(overall_result.errors)} errors")
        
        return overall_result
    
    def validate_and_raise(self, config: EnhancedStatusConfig) -> None:
        """Validate configuration and raise exception if invalid."""
        result = self.validate(config)
        if not result.is_valid:
            raise ConfigValidationError(
                f"Configuration validation failed with {len(result.errors)} errors",
                result.errors
            )
    
    def get_rule_names(self) -> List[str]:
        """Get names of all validation rules."""
        return [rule.name for rule in self.rules]
    
    def get_rule_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all validation rules."""
        return {rule.name: rule.description for rule in self.rules}


# Utility functions for validation

def validate_config_file(config_path: Union[str, Path]) -> ValidationResult:
    """Validate configuration file."""
    from .config_loader import ConfigLoader
    
    try:
        loader = ConfigLoader(config_path)
        config = loader.load_config()
        
        validator = ConfigValidator()
        return validator.validate(config)
        
    except Exception as e:
        result = ValidationResult(False, [], [], [])
        result.add_error(f"Failed to load configuration: {e}")
        return result


def create_custom_validation_rule(
    name: str,
    description: str,
    validation_func: Callable[[EnhancedStatusConfig], ValidationResult]
) -> ValidationRule:
    """Create custom validation rule from function."""
    
    class CustomValidationRule(ValidationRule):
        def validate(self, config: EnhancedStatusConfig) -> ValidationResult:
            return validation_func(config)
    
    return CustomValidationRule(name, description)


def validate_server_connectivity(server_config: EnhancedServerConfig) -> ValidationResult:
    """Validate server connectivity (basic URL reachability check)."""
    result = ValidationResult(True, [], [], [])
    
    # This is a basic validation - actual connectivity testing would be done
    # by the health check clients
    
    if server_config.mcp_enabled:
        if not server_config.mcp_endpoint_url:
            result.add_error("MCP endpoint URL is required")
        else:
            result.add_info(f"MCP endpoint configured: {server_config.mcp_endpoint_url}")
    
    if server_config.rest_enabled:
        if not server_config.rest_health_endpoint_url:
            result.add_error("REST endpoint URL is required")
        else:
            result.add_info(f"REST endpoint configured: {server_config.rest_health_endpoint_url}")
    
    return result