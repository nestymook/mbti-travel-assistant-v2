"""
Environment Configuration Loader

This module provides enhanced environment configuration loading with validation,
error handling, and automatic environment detection for the MBTI Travel Planner Agent.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class GatewayEnvironmentConfig:
    """Gateway configuration loaded from environment variables."""
    environment: str
    base_url: str
    timeout: int
    max_retries: int
    auth_required: bool
    
    # Agent configuration
    agent_model: str
    agent_temperature: float
    agent_max_tokens: int
    agent_timeout: int
    
    # AWS configuration
    aws_region: str
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration parameters."""
        errors = []
        
        # Validate required fields
        if not self.environment:
            errors.append("Environment name is required")
        
        if not self.base_url:
            errors.append("Gateway base URL is required")
        elif not (self.base_url.startswith('http://') or self.base_url.startswith('https://')):
            errors.append(f"Invalid gateway base URL format: {self.base_url}")
        
        # Validate timeout
        if self.timeout <= 0 or self.timeout > 300:
            errors.append(f"Gateway timeout must be between 1-300 seconds, got: {self.timeout}")
        
        # Validate max_retries
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append(f"Gateway max_retries must be between 0-10, got: {self.max_retries}")
        
        # Validate agent model
        if not self.agent_model:
            errors.append("Agent model is required")
        
        # Validate agent temperature
        if not (0.0 <= self.agent_temperature <= 1.0):
            errors.append(f"Agent temperature must be between 0.0-1.0, got: {self.agent_temperature}")
        
        # Validate agent max_tokens
        if self.agent_max_tokens <= 0 or self.agent_max_tokens > 100000:
            errors.append(f"Agent max_tokens must be between 1-100000, got: {self.agent_max_tokens}")
        
        # Validate agent timeout
        if self.agent_timeout <= 0 or self.agent_timeout > 3600:
            errors.append(f"Agent timeout must be between 1-3600 seconds, got: {self.agent_timeout}")
        
        # Validate AWS region
        if not self.aws_region:
            errors.append("AWS region is required")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"Configuration validation passed for environment: {self.environment}")


class EnvironmentConfigLoader:
    """
    Loads and validates environment configuration from various sources.
    """
    
    # Default values for configuration
    DEFAULTS = {
        'GATEWAY_TIMEOUT': '30',
        'GATEWAY_MAX_RETRIES': '3',
        'GATEWAY_AUTH_REQUIRED': 'true',
        'AGENT_MODEL': 'amazon.nova-pro-v1:0',
        'AGENT_TEMPERATURE': '0.1',
        'AGENT_MAX_TOKENS': '2048',
        'AGENT_TIMEOUT': '60',
        'AWS_REGION': 'us-east-1'
    }
    
    # Environment-specific gateway URLs
    GATEWAY_URLS = {
        'development': 'http://localhost:8080',
        'staging': 'https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com',
        'production': 'https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com'
    }
    
    def __init__(self, config_dir: str = None):
        """
        Initialize environment configuration loader.
        
        Args:
            config_dir: Directory containing environment files
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'environments')
        self.current_environment = None
        self.config = None
    
    def detect_environment(self) -> str:
        """
        Detect current environment from various sources.
        
        Returns:
            Detected environment name
        """
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
            os.path.exists('.env.development') or
            os.path.exists('development.env')):
            logger.debug("Local development environment detected")
            return 'development'
        
        # Check for staging indicators
        if (os.getenv('STAGING') or 
            os.path.exists('.env.staging') or
            os.path.exists('staging.env')):
            logger.debug("Staging environment detected")
            return 'staging'
        
        # Check for production indicators
        if (os.getenv('PRODUCTION') or 
            os.path.exists('.env.production') or
            os.path.exists('production.env')):
            logger.debug("Production environment detected")
            return 'production'
        
        # Default to development for safety
        logger.warning("No environment indicators found, defaulting to development")
        return 'development'
    
    def load_environment_file(self, environment: str) -> None:
        """
        Load environment file for the specified environment.
        
        Args:
            environment: Environment name
        """
        env_file_paths = [
            os.path.join(self.config_dir, f"{environment}.env"),
            f".env.{environment}",
            f"{environment}.env"
        ]
        
        loaded = False
        for env_file in env_file_paths:
            if os.path.exists(env_file):
                logger.debug(f"Loading environment file: {env_file}")
                # Don't override existing environment variables - they take precedence
                load_dotenv(env_file, override=False)
                loaded = True
                break
        
        if not loaded:
            logger.warning(f"No environment file found for {environment}, using environment variables and defaults")
    
    def get_config_value(self, key: str, required: bool = True) -> str:
        """
        Get configuration value from environment variables with fallback to defaults.
        
        Args:
            key: Configuration key
            required: Whether the value is required
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required value is missing
        """
        value = os.getenv(key)
        
        if value is None:
            if key in self.DEFAULTS:
                value = self.DEFAULTS[key]
                logger.debug(f"Using default value for {key}: {value}")
            elif required:
                raise ValueError(f"Required configuration value missing: {key}")
        
        return value
    
    def load_config(self, environment: str = None) -> GatewayEnvironmentConfig:
        """
        Load complete configuration for the specified environment.
        
        Args:
            environment: Environment name (auto-detected if None)
            
        Returns:
            GatewayEnvironmentConfig object
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Detect environment if not specified
        if not environment:
            environment = self.detect_environment()
        
        self.current_environment = environment
        
        # Load environment file
        self.load_environment_file(environment)
        
        try:
            # Get gateway base URL
            gateway_url = os.getenv('GATEWAY_BASE_URL')
            if not gateway_url and environment in self.GATEWAY_URLS:
                gateway_url = self.GATEWAY_URLS[environment]
                logger.debug(f"Using default gateway URL for {environment}: {gateway_url}")
            
            if not gateway_url:
                raise ValueError(f"Gateway base URL not configured for environment: {environment}")
            
            # Parse boolean values
            auth_required_str = self.get_config_value('GATEWAY_AUTH_REQUIRED', required=False)
            auth_required = auth_required_str.lower() in ('true', '1', 'yes', 'on')
            
            # Create configuration object
            config = GatewayEnvironmentConfig(
                environment=environment,
                base_url=gateway_url,
                timeout=int(self.get_config_value('GATEWAY_TIMEOUT')),
                max_retries=int(self.get_config_value('GATEWAY_MAX_RETRIES')),
                auth_required=auth_required,
                agent_model=self.get_config_value('AGENT_MODEL'),
                agent_temperature=float(self.get_config_value('AGENT_TEMPERATURE')),
                agent_max_tokens=int(self.get_config_value('AGENT_MAX_TOKENS')),
                agent_timeout=int(self.get_config_value('AGENT_TIMEOUT')),
                aws_region=self.get_config_value('AWS_REGION')
            )
            
            self.config = config
            logger.info(f"Successfully loaded configuration for environment: {environment}")
            logger.debug(f"Gateway URL: {config.base_url}")
            logger.debug(f"Auth required: {config.auth_required}")
            
            return config
            
        except (ValueError, TypeError) as e:
            error_msg = f"Failed to load configuration for environment '{environment}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def validate_environment_variables(self) -> List[str]:
        """
        Validate current environment variables and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Check required environment variables
        required_vars = [
            'GATEWAY_BASE_URL',
            'AGENT_MODEL',
            'AWS_REGION'
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value and var not in self.DEFAULTS:
                issues.append(f"Required environment variable missing: {var}")
        
        # Validate specific values
        try:
            timeout = int(os.getenv('GATEWAY_TIMEOUT', self.DEFAULTS['GATEWAY_TIMEOUT']))
            if timeout <= 0 or timeout > 300:
                issues.append(f"GATEWAY_TIMEOUT must be between 1-300, got: {timeout}")
        except ValueError:
            issues.append("GATEWAY_TIMEOUT must be a valid integer")
        
        try:
            max_retries = int(os.getenv('GATEWAY_MAX_RETRIES', self.DEFAULTS['GATEWAY_MAX_RETRIES']))
            if max_retries < 0 or max_retries > 10:
                issues.append(f"GATEWAY_MAX_RETRIES must be between 0-10, got: {max_retries}")
        except ValueError:
            issues.append("GATEWAY_MAX_RETRIES must be a valid integer")
        
        try:
            temperature = float(os.getenv('AGENT_TEMPERATURE', self.DEFAULTS['AGENT_TEMPERATURE']))
            if not (0.0 <= temperature <= 1.0):
                issues.append(f"AGENT_TEMPERATURE must be between 0.0-1.0, got: {temperature}")
        except ValueError:
            issues.append("AGENT_TEMPERATURE must be a valid float")
        
        try:
            max_tokens = int(os.getenv('AGENT_MAX_TOKENS', self.DEFAULTS['AGENT_MAX_TOKENS']))
            if max_tokens <= 0 or max_tokens > 100000:
                issues.append(f"AGENT_MAX_TOKENS must be between 1-100000, got: {max_tokens}")
        except ValueError:
            issues.append("AGENT_MAX_TOKENS must be a valid integer")
        
        # Validate URL format
        gateway_url = os.getenv('GATEWAY_BASE_URL')
        if gateway_url and not (gateway_url.startswith('http://') or gateway_url.startswith('https://')):
            issues.append(f"GATEWAY_BASE_URL must start with http:// or https://, got: {gateway_url}")
        
        return issues
    
    def get_current_config(self) -> Optional[GatewayEnvironmentConfig]:
        """Get the currently loaded configuration."""
        return self.config
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get summary of current environment configuration.
        
        Returns:
            Dictionary with environment configuration summary
        """
        if not self.config:
            return {"error": "No configuration loaded"}
        
        return {
            "environment": self.config.environment,
            "gateway": {
                "base_url": self.config.base_url,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "auth_required": self.config.auth_required
            },
            "agent": {
                "model": self.config.agent_model,
                "temperature": self.config.agent_temperature,
                "max_tokens": self.config.agent_max_tokens,
                "timeout": self.config.agent_timeout
            },
            "aws": {
                "region": self.config.aws_region
            }
        }


# Global configuration loader instance
_config_loader = None


def get_config_loader(config_dir: str = None) -> EnvironmentConfigLoader:
    """
    Get the global configuration loader instance.
    
    Args:
        config_dir: Directory containing environment files
        
    Returns:
        EnvironmentConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = EnvironmentConfigLoader(config_dir)
    
    return _config_loader


def load_environment_config(environment: str = None, config_dir: str = None) -> GatewayEnvironmentConfig:
    """
    Convenience function to load environment configuration.
    
    Args:
        environment: Environment name (auto-detected if None)
        config_dir: Directory containing environment files
        
    Returns:
        GatewayEnvironmentConfig object
    """
    loader = get_config_loader(config_dir)
    return loader.load_config(environment)


def validate_current_environment() -> List[str]:
    """
    Validate current environment variables.
    
    Returns:
        List of validation error messages
    """
    loader = get_config_loader()
    return loader.validate_environment_variables()


# Export main classes and functions
__all__ = [
    'GatewayEnvironmentConfig',
    'EnvironmentConfigLoader',
    'get_config_loader',
    'load_environment_config',
    'validate_current_environment'
]