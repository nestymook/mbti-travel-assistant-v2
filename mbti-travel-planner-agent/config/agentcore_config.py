"""
AgentCore Configuration Management

This module provides configuration management for AgentCore integration,
including environment-specific settings and validation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.authentication_manager import CognitoConfig

logger = logging.getLogger(__name__)


@dataclass
class AgentCoreConfig:
    """Configuration for AgentCore integration."""
    restaurant_search_agent_arn: str
    restaurant_reasoning_agent_arn: str
    region: str = "us-east-1"
    timeout_seconds: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate AgentCore configuration."""
        errors = []
        
        # Validate ARNs
        if not self.restaurant_search_agent_arn:
            errors.append("Restaurant search agent ARN is required")
        elif not self._is_valid_arn(self.restaurant_search_agent_arn):
            errors.append(f"Invalid restaurant search agent ARN: {self.restaurant_search_agent_arn}")
        
        if not self.restaurant_reasoning_agent_arn:
            errors.append("Restaurant reasoning agent ARN is required")
        elif not self._is_valid_arn(self.restaurant_reasoning_agent_arn):
            errors.append(f"Invalid restaurant reasoning agent ARN: {self.restaurant_reasoning_agent_arn}")
        
        # Validate region
        if not self.region:
            errors.append("AWS region is required")
        
        # Validate timeout
        if self.timeout_seconds <= 0 or self.timeout_seconds > 300:
            errors.append(f"Timeout must be between 1-300 seconds, got: {self.timeout_seconds}")
        
        # Validate max_retries
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append(f"Max retries must be between 0-10, got: {self.max_retries}")
        
        if errors:
            error_msg = "AgentCore configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _is_valid_arn(self, arn: str) -> bool:
        """Validate ARN format."""
        try:
            # Basic ARN format validation
            parts = arn.split(':')
            return (
                len(parts) >= 6 and
                parts[0] == 'arn' and
                parts[1] == 'aws' and
                'bedrock-agentcore' in parts[2]
            )
        except Exception:
            return False


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_connection_pooling: bool = True
    max_connections: int = 100
    max_connections_per_host: int = 10
    enable_parallel_execution: bool = True
    
    def __post_init__(self):
        """Validate performance configuration."""
        if self.cache_ttl_seconds <= 0:
            raise ValueError("Cache TTL must be positive")
        
        if self.max_connections <= 0:
            raise ValueError("Max connections must be positive")
        
        if self.max_connections_per_host <= 0:
            raise ValueError("Max connections per host must be positive")


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and observability."""
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 60
    metrics_namespace: str = "AgentCore/MBTI-Travel-Planner"
    
    def __post_init__(self):
        """Validate monitoring configuration."""
        if self.health_check_interval_seconds <= 0:
            raise ValueError("Health check interval must be positive")


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration."""
    environment: str  # development, staging, production
    agentcore: AgentCoreConfig
    cognito: CognitoConfig
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate environment configuration."""
        if not self.environment:
            raise ValueError("Environment name is required")
        
        valid_environments = ['development', 'staging', 'production']
        if self.environment not in valid_environments:
            logger.warning(f"Unknown environment: {self.environment}. Valid options: {valid_environments}")


class AgentCoreConfigurationManager:
    """Manages AgentCore configuration loading and validation."""
    
    # Default agent ARNs for different environments
    DEFAULT_AGENT_ARNS = {
        'development': {
            'restaurant_search': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j',
            'restaurant_reasoning': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE'
        },
        'staging': {
            'restaurant_search': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-staging',
            'restaurant_reasoning': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-staging'
        },
        'production': {
            'restaurant_search': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j',
            'restaurant_reasoning': 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE'
        }
    }
    
    # Default configuration values
    DEFAULTS = {
        'AGENTCORE_REGION': 'us-east-1',
        'AGENTCORE_TIMEOUT': '30',
        'AGENTCORE_MAX_RETRIES': '3',
        'PERFORMANCE_ENABLE_CACHING': 'true',
        'PERFORMANCE_CACHE_TTL': '300',
        'PERFORMANCE_MAX_CONNECTIONS': '100',
        'PERFORMANCE_MAX_CONNECTIONS_PER_HOST': '10',
        'PERFORMANCE_ENABLE_PARALLEL': 'true',
        'MONITORING_ENABLE_METRICS': 'true',
        'MONITORING_ENABLE_TRACING': 'true',
        'MONITORING_ENABLE_HEALTH_CHECKS': 'true',
        'MONITORING_HEALTH_CHECK_INTERVAL': '60',
        'MONITORING_METRICS_NAMESPACE': 'AgentCore/MBTI-Travel-Planner'
    }
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__))
        self.current_config: Optional[EnvironmentConfig] = None
    
    def detect_environment(self) -> str:
        """Detect current environment from various sources."""
        # Check environment variable (highest priority)
        env_var = os.getenv('ENVIRONMENT', '').lower().strip()
        if env_var:
            logger.debug(f"Environment detected from ENVIRONMENT variable: {env_var}")
            return env_var
        
        # Check AWS-specific environment variables
        aws_env = os.getenv('AWS_ENVIRONMENT', '').lower().strip()
        if aws_env:
            logger.debug(f"Environment detected from AWS_ENVIRONMENT: {aws_env}")
            return aws_env
        
        # Check deployment stage
        stage = os.getenv('DEPLOYMENT_STAGE', '').lower().strip()
        if stage:
            logger.debug(f"Environment detected from DEPLOYMENT_STAGE: {stage}")
            return stage
        
        # Check for local development indicators
        if (os.getenv('LOCAL_DEVELOPMENT') or 
            os.getenv('DEBUG') or 
            os.path.exists('.env.development')):
            logger.debug("Local development environment detected")
            return 'development'
        
        # Default to development for safety
        logger.warning("No environment indicators found, defaulting to development")
        return 'development'
    
    def load_environment_file(self, environment: str) -> None:
        """Load environment file for the specified environment."""
        env_file_paths = [
            os.path.join(self.config_dir, "environments", f"{environment}.env"),
            f".env.{environment}",
            f"{environment}.env"
        ]
        
        loaded = False
        for env_file in env_file_paths:
            if os.path.exists(env_file):
                logger.debug(f"Loading environment file: {env_file}")
                load_dotenv(env_file, override=False)
                loaded = True
                break
        
        if not loaded:
            logger.warning(f"No environment file found for {environment}, using environment variables and defaults")
    
    def get_config_value(self, key: str, required: bool = True) -> str:
        """Get configuration value from environment variables with fallback to defaults."""
        value = os.getenv(key)
        
        if value is None:
            if key in self.DEFAULTS:
                value = self.DEFAULTS[key]
                logger.debug(f"Using default value for {key}: {value}")
            elif required:
                raise ValueError(f"Required configuration value missing: {key}")
        
        return value
    
    def load_cognito_config(self) -> CognitoConfig:
        """Load Cognito configuration from file."""
        cognito_config_path = os.path.join(self.config_dir, "cognito_config.json")
        
        try:
            with open(cognito_config_path, 'r') as f:
                config_data = json.load(f)
            
            return CognitoConfig(
                user_pool_id=config_data["user_pool"]["user_pool_id"],
                client_id=config_data["app_client"]["client_id"],
                client_secret=config_data["app_client"]["client_secret"],
                region=config_data["region"],
                discovery_url=config_data.get("discovery_url", "")
            )
            
        except Exception as e:
            raise ValueError(f"Failed to load Cognito configuration: {str(e)}")
    
    def load_config(self, environment: str = None) -> EnvironmentConfig:
        """
        Load complete configuration for the specified environment.
        
        Args:
            environment: Environment name (auto-detected if None)
            
        Returns:
            EnvironmentConfig object
        """
        # Detect environment if not specified
        if not environment:
            environment = self.detect_environment()
        
        # Load environment file
        self.load_environment_file(environment)
        
        try:
            # Load Cognito configuration
            cognito_config = self.load_cognito_config()
            
            # Get agent ARNs
            search_arn = os.getenv('RESTAURANT_SEARCH_AGENT_ARN')
            reasoning_arn = os.getenv('RESTAURANT_REASONING_AGENT_ARN')
            
            # Use defaults if not specified
            if not search_arn and environment in self.DEFAULT_AGENT_ARNS:
                search_arn = self.DEFAULT_AGENT_ARNS[environment]['restaurant_search']
                logger.debug(f"Using default search agent ARN for {environment}")
            
            if not reasoning_arn and environment in self.DEFAULT_AGENT_ARNS:
                reasoning_arn = self.DEFAULT_AGENT_ARNS[environment]['restaurant_reasoning']
                logger.debug(f"Using default reasoning agent ARN for {environment}")
            
            if not search_arn:
                raise ValueError("Restaurant search agent ARN not configured")
            
            if not reasoning_arn:
                raise ValueError("Restaurant reasoning agent ARN not configured")
            
            # Create AgentCore configuration
            agentcore_config = AgentCoreConfig(
                restaurant_search_agent_arn=search_arn,
                restaurant_reasoning_agent_arn=reasoning_arn,
                region=self.get_config_value('AGENTCORE_REGION'),
                timeout_seconds=int(self.get_config_value('AGENTCORE_TIMEOUT')),
                max_retries=int(self.get_config_value('AGENTCORE_MAX_RETRIES'))
            )
            
            # Create performance configuration
            performance_config = PerformanceConfig(
                enable_caching=self.get_config_value('PERFORMANCE_ENABLE_CACHING').lower() == 'true',
                cache_ttl_seconds=int(self.get_config_value('PERFORMANCE_CACHE_TTL')),
                enable_connection_pooling=True,  # Always enabled
                max_connections=int(self.get_config_value('PERFORMANCE_MAX_CONNECTIONS')),
                max_connections_per_host=int(self.get_config_value('PERFORMANCE_MAX_CONNECTIONS_PER_HOST')),
                enable_parallel_execution=self.get_config_value('PERFORMANCE_ENABLE_PARALLEL').lower() == 'true'
            )
            
            # Create monitoring configuration
            monitoring_config = MonitoringConfig(
                enable_metrics=self.get_config_value('MONITORING_ENABLE_METRICS').lower() == 'true',
                enable_tracing=self.get_config_value('MONITORING_ENABLE_TRACING').lower() == 'true',
                enable_health_checks=self.get_config_value('MONITORING_ENABLE_HEALTH_CHECKS').lower() == 'true',
                health_check_interval_seconds=int(self.get_config_value('MONITORING_HEALTH_CHECK_INTERVAL')),
                metrics_namespace=self.get_config_value('MONITORING_METRICS_NAMESPACE')
            )
            
            # Create complete environment configuration
            config = EnvironmentConfig(
                environment=environment,
                agentcore=agentcore_config,
                cognito=cognito_config,
                performance=performance_config,
                monitoring=monitoring_config,
                debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true'
            )
            
            self.current_config = config
            logger.info(f"Successfully loaded AgentCore configuration for environment: {environment}")
            
            return config
            
        except Exception as e:
            error_msg = f"Failed to load AgentCore configuration for environment '{environment}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def validate_configuration(self, config: EnvironmentConfig) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        issues = []
        
        try:
            # Validate AgentCore config
            config.agentcore._validate()
        except ValueError as e:
            issues.append(f"AgentCore config: {str(e)}")
        
        try:
            # Validate performance config
            config.performance.__post_init__()
        except ValueError as e:
            issues.append(f"Performance config: {str(e)}")
        
        try:
            # Validate monitoring config
            config.monitoring.__post_init__()
        except ValueError as e:
            issues.append(f"Monitoring config: {str(e)}")
        
        # Additional cross-validation
        if config.performance.max_connections_per_host > config.performance.max_connections:
            issues.append("Max connections per host cannot exceed total max connections")
        
        return issues
    
    def get_current_config(self) -> Optional[EnvironmentConfig]:
        """Get the currently loaded configuration."""
        return self.current_config
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        if not self.current_config:
            return {"error": "No configuration loaded"}
        
        config = self.current_config
        
        return {
            "environment": config.environment,
            "agentcore": {
                "restaurant_search_agent_arn": config.agentcore.restaurant_search_agent_arn,
                "restaurant_reasoning_agent_arn": config.agentcore.restaurant_reasoning_agent_arn,
                "region": config.agentcore.region,
                "timeout_seconds": config.agentcore.timeout_seconds,
                "max_retries": config.agentcore.max_retries
            },
            "cognito": {
                "user_pool_id": config.cognito.user_pool_id,
                "client_id": config.cognito.client_id,
                "region": config.cognito.region,
                "discovery_url": config.cognito.discovery_url
            },
            "performance": {
                "enable_caching": config.performance.enable_caching,
                "cache_ttl_seconds": config.performance.cache_ttl_seconds,
                "max_connections": config.performance.max_connections,
                "max_connections_per_host": config.performance.max_connections_per_host,
                "enable_parallel_execution": config.performance.enable_parallel_execution
            },
            "monitoring": {
                "enable_metrics": config.monitoring.enable_metrics,
                "enable_tracing": config.monitoring.enable_tracing,
                "enable_health_checks": config.monitoring.enable_health_checks,
                "health_check_interval_seconds": config.monitoring.health_check_interval_seconds,
                "metrics_namespace": config.monitoring.metrics_namespace
            },
            "debug_mode": config.debug_mode
        }


# Global configuration manager instance
_config_manager = None


def get_config_manager(config_dir: str = None) -> AgentCoreConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = AgentCoreConfigurationManager(config_dir)
    
    return _config_manager


def load_agentcore_config(environment: str = None, config_dir: str = None) -> EnvironmentConfig:
    """
    Convenience function to load AgentCore configuration.
    
    Args:
        environment: Environment name (auto-detected if None)
        config_dir: Directory containing configuration files
        
    Returns:
        EnvironmentConfig object
    """
    manager = get_config_manager(config_dir)
    return manager.load_config(environment)


# Export main classes and functions
__all__ = [
    'AgentCoreConfig',
    'PerformanceConfig',
    'MonitoringConfig',
    'EnvironmentConfig',
    'AgentCoreConfigurationManager',
    'get_config_manager',
    'load_agentcore_config'
]