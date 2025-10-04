"""
Gateway Configuration Management

This module provides environment-based configuration management for different
gateway endpoints (development, staging, production) with validation and
automatic environment detection.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    name: str
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    auth_required: bool = True
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentConfig':
        """Create from dictionary."""
        return cls(**data)


class GatewayConfigManager:
    """
    Manages gateway configuration for different environments with validation
    and automatic environment detection.
    """
    
    # Default configurations for each environment
    DEFAULT_CONFIGS = {
        "development": EnvironmentConfig(
            name="development",
            base_url="http://localhost:8080",
            timeout=30,
            max_retries=2,
            auth_required=False,
            description="Local development environment"
        ),
        "staging": EnvironmentConfig(
            name="staging", 
            base_url="https://agentcore-gateway-mcp-tools-staging.bedrock-agentcore.us-east-1.amazonaws.com",
            timeout=45,
            max_retries=3,
            auth_required=True,
            description="Staging environment for testing"
        ),
        "production": EnvironmentConfig(
            name="production",
            base_url="https://agentcore_gateway_mcp_tools-UspJsMG7Fi.bedrock-agentcore.us-east-1.amazonaws.com",
            timeout=60,
            max_retries=3,
            auth_required=True,
            description="Production environment"
        )
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to custom configuration file
        """
        self.config_file = config_file
        self.configs = self.DEFAULT_CONFIGS.copy()
        
        # Load custom configurations if file provided
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
    
    def _load_config_file(self, config_file: str) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                custom_configs = json.load(f)
            
            for env_name, config_data in custom_configs.items():
                if isinstance(config_data, dict):
                    self.configs[env_name] = EnvironmentConfig.from_dict({
                        "name": env_name,
                        **config_data
                    })
                    logger.info(f"Loaded custom configuration for {env_name}")
                    
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
    
    def get_config(self, environment: str = None) -> EnvironmentConfig:
        """
        Get configuration for specified environment.
        
        Args:
            environment: Environment name (auto-detected if None)
            
        Returns:
            EnvironmentConfig for the specified environment
        """
        # Auto-detect environment if not specified
        if not environment:
            environment = self.detect_environment()
        
        # Normalize environment name
        env_name = environment.lower().strip()
        
        # Get configuration
        if env_name in self.configs:
            config = self.configs[env_name]
            logger.debug(f"Using {env_name} configuration: {config.base_url}")
            return config
        else:
            logger.warning(f"Unknown environment '{env_name}', using production")
            return self.configs["production"]
    
    def detect_environment(self) -> str:
        """
        Auto-detect current environment from various sources.
        
        Returns:
            Detected environment name
        """
        # Check environment variable
        env_var = os.getenv('ENVIRONMENT', '').lower().strip()
        if env_var in self.configs:
            logger.debug(f"Environment detected from ENVIRONMENT variable: {env_var}")
            return env_var
        
        # Check AWS environment variables
        aws_env = os.getenv('AWS_ENVIRONMENT', '').lower().strip()
        if aws_env in self.configs:
            logger.debug(f"Environment detected from AWS_ENVIRONMENT: {aws_env}")
            return aws_env
        
        # Check deployment stage
        stage = os.getenv('DEPLOYMENT_STAGE', '').lower().strip()
        if stage in self.configs:
            logger.debug(f"Environment detected from DEPLOYMENT_STAGE: {stage}")
            return stage
        
        # Check for local development indicators
        if (os.getenv('LOCAL_DEVELOPMENT') or 
            os.getenv('DEBUG') or 
            os.path.exists('.env.development')):
            logger.debug("Local development environment detected")
            return "development"
        
        # Check for staging indicators
        if (os.getenv('STAGING') or 
            os.path.exists('.env.staging')):
            logger.debug("Staging environment detected")
            return "staging"
        
        # Default to production
        logger.debug("No environment indicators found, defaulting to production")
        return "production"
    
    def validate_config(self, config: EnvironmentConfig) -> bool:
        """
        Validate configuration parameters.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            # Validate required fields
            if not config.name or not config.base_url:
                logger.error("Configuration missing required fields (name, base_url)")
                return False
            
            # Validate URL format
            if not (config.base_url.startswith('http://') or 
                   config.base_url.startswith('https://')):
                logger.error(f"Invalid base URL format: {config.base_url}")
                return False
            
            # Validate timeout
            if config.timeout <= 0 or config.timeout > 300:
                logger.error(f"Invalid timeout value: {config.timeout}")
                return False
            
            # Validate max_retries
            if config.max_retries < 0 or config.max_retries > 10:
                logger.error(f"Invalid max_retries value: {config.max_retries}")
                return False
            
            logger.debug(f"Configuration validation passed for {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, EnvironmentConfig]:
        """Get all available configurations."""
        return self.configs.copy()
    
    def add_custom_config(self, name: str, config: EnvironmentConfig) -> None:
        """
        Add a custom environment configuration.
        
        Args:
            name: Environment name
            config: Configuration object
        """
        if self.validate_config(config):
            self.configs[name.lower()] = config
            logger.info(f"Added custom configuration for {name}")
        else:
            raise ValueError(f"Invalid configuration for {name}")
    
    def save_config_file(self, file_path: str) -> None:
        """
        Save current configurations to JSON file.
        
        Args:
            file_path: Path to save configuration file
        """
        try:
            config_data = {}
            for name, config in self.configs.items():
                # Skip default configs, only save custom ones
                if name not in self.DEFAULT_CONFIGS or config != self.DEFAULT_CONFIGS[name]:
                    config_dict = config.to_dict()
                    # Remove name field as it's the key
                    config_dict.pop('name', None)
                    config_data[name] = config_dict
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration file: {e}")
            raise
    
    def get_environment_variables(self, environment: str = None) -> Dict[str, str]:
        """
        Get environment variables for the specified environment.
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary of environment variables
        """
        config = self.get_config(environment)
        
        return {
            'GATEWAY_BASE_URL': config.base_url,
            'GATEWAY_TIMEOUT': str(config.timeout),
            'GATEWAY_MAX_RETRIES': str(config.max_retries),
            'GATEWAY_AUTH_REQUIRED': str(config.auth_required).lower(),
            'ENVIRONMENT': config.name
        }


# Global configuration manager instance
_config_manager = None


def get_config_manager(config_file: str = None) -> GatewayConfigManager:
    """
    Get the global configuration manager instance.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        GatewayConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = GatewayConfigManager(config_file)
    
    return _config_manager


def get_gateway_config(environment: str = None, config_file: str = None) -> EnvironmentConfig:
    """
    Convenience function to get gateway configuration.
    
    Args:
        environment: Environment name (auto-detected if None)
        config_file: Optional path to configuration file
        
    Returns:
        EnvironmentConfig for the specified environment
    """
    manager = get_config_manager(config_file)
    return manager.get_config(environment)


def create_environment_file(environment: str, output_path: str = None) -> str:
    """
    Create environment file with gateway configuration.
    
    Args:
        environment: Environment name
        output_path: Output file path (auto-generated if None)
        
    Returns:
        Path to created environment file
    """
    if not output_path:
        output_path = f".env.{environment}"
    
    manager = get_config_manager()
    env_vars = manager.get_environment_variables(environment)
    
    try:
        with open(output_path, 'w') as f:
            f.write(f"# Gateway configuration for {environment} environment\n")
            f.write(f"# Generated automatically - do not edit manually\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Environment file created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to create environment file: {e}")
        raise


# Export main classes and functions
__all__ = [
    'EnvironmentConfig',
    'GatewayConfigManager',
    'get_config_manager',
    'get_gateway_config',
    'create_environment_file'
]