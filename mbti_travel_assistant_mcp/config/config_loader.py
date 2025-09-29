"""
Configuration loader for MBTI Travel Assistant MCP

This module provides environment-specific configuration loading with validation
and fallback mechanisms for different deployment environments.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .settings import ApplicationSettings

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading fails"""
    pass


class ConfigLoader:
    """Configuration loader with environment-specific support"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration loader
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or Path(__file__).parent
        self.environments_dir = self.config_dir / "environments"
        
    def load_environment_config(self, environment: Optional[str] = None) -> ApplicationSettings:
        """Load configuration for specified environment
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            ApplicationSettings instance with loaded configuration
            
        Raises:
            ConfigurationError: If configuration loading fails
        """
        # Determine environment
        env = environment or os.getenv("ENVIRONMENT", "development")
        
        logger.info(f"Loading configuration for environment: {env}")
        
        # Load base .env file if it exists
        base_env_file = self.config_dir.parent / ".env"
        if base_env_file.exists():
            load_dotenv(base_env_file)
            logger.debug(f"Loaded base environment file: {base_env_file}")
        
        # Load environment-specific configuration
        env_file = self.environments_dir / f"{env}.env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            logger.debug(f"Loaded environment-specific file: {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
        
        # Create and validate settings
        try:
            settings = ApplicationSettings()
            self._validate_configuration(settings, env)
            logger.info(f"Configuration loaded successfully for {env} environment")
            return settings
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration for {env}: {str(e)}")
    
    def _validate_configuration(self, settings: ApplicationSettings, environment: str) -> None:
        """Validate configuration settings
        
        Args:
            settings: Application settings to validate
            environment: Environment name for context
            
        Raises:
            ConfigurationError: If validation fails
        """
        errors = []
        
        # Validate MCP endpoints
        if not settings.mcp_client.search_mcp_endpoint:
            errors.append("SEARCH_MCP_ENDPOINT is required")
        
        if not settings.mcp_client.reasoning_mcp_endpoint:
            errors.append("REASONING_MCP_ENDPOINT is required")
        
        # Validate authentication settings for non-development environments
        if environment != "development":
            if not settings.authentication.cognito_user_pool_id:
                errors.append("COGNITO_USER_POOL_ID is required for non-development environments")
        
        # Validate AWS region
        if not settings.aws_region:
            errors.append("AWS_REGION is required")
        
        # Validate agent model
        if not settings.agentcore.agent_model:
            errors.append("AGENT_MODEL is required")
        
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {', '.join(errors)}")
    
    def get_mcp_endpoints(self, environment: Optional[str] = None) -> Dict[str, str]:
        """Get MCP server endpoints for environment
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with MCP endpoint configurations
        """
        settings = self.load_environment_config(environment)
        
        return {
            "search_mcp_endpoint": settings.mcp_client.search_mcp_endpoint,
            "reasoning_mcp_endpoint": settings.mcp_client.reasoning_mcp_endpoint,
            "connection_timeout": settings.mcp_client.mcp_connection_timeout,
            "retry_attempts": settings.mcp_client.mcp_retry_attempts
        }
    
    def get_cognito_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get Cognito authentication configuration
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with Cognito configuration
        """
        settings = self.load_environment_config(environment)
        
        return {
            "user_pool_id": settings.authentication.cognito_user_pool_id,
            "region": settings.authentication.cognito_region,
            "jwt_algorithm": settings.authentication.jwt_algorithm,
            "jwt_audience": settings.authentication.jwt_audience,
            "token_cache_ttl": settings.authentication.token_cache_ttl
        }
    
    def get_agentcore_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get AgentCore runtime configuration
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with AgentCore configuration
        """
        settings = self.load_environment_config(environment)
        
        return {
            "runtime_port": settings.agentcore.runtime_port,
            "agent_model": settings.agentcore.agent_model,
            "agent_temperature": settings.agentcore.agent_temperature,
            "agent_max_tokens": settings.agentcore.agent_max_tokens
        }
    
    def load_mcp_endpoints_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load MCP endpoints configuration from JSON file
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with MCP endpoints configuration
        """
        env = environment or os.getenv("ENVIRONMENT", "development")
        
        mcp_config_file = self.config_dir / "mcp_endpoints.json"
        if not mcp_config_file.exists():
            raise ConfigurationError(f"MCP endpoints configuration file not found: {mcp_config_file}")
        
        try:
            with open(mcp_config_file, 'r') as f:
                config = json.load(f)
            
            if env not in config:
                raise ConfigurationError(f"Environment '{env}' not found in MCP endpoints configuration")
            
            # Merge environment-specific config with common config
            env_config = config[env].copy()
            if "common" in config:
                for key, value in config["common"].items():
                    if key not in env_config:
                        env_config[key] = value
            
            return env_config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in MCP endpoints configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load MCP endpoints configuration: {e}")
    
    def load_cognito_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load Cognito configuration from JSON file
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with Cognito configuration
        """
        env = environment or os.getenv("ENVIRONMENT", "development")
        
        cognito_config_file = self.config_dir / "cognito_config.json"
        if not cognito_config_file.exists():
            raise ConfigurationError(f"Cognito configuration file not found: {cognito_config_file}")
        
        try:
            with open(cognito_config_file, 'r') as f:
                config = json.load(f)
            
            if env not in config:
                raise ConfigurationError(f"Environment '{env}' not found in Cognito configuration")
            
            # Merge environment-specific config with common config
            env_config = config[env].copy()
            if "common" in config:
                for key, value in config["common"].items():
                    if key not in env_config:
                        env_config[key] = value
            
            return env_config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in Cognito configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load Cognito configuration: {e}")
    
    def load_knowledge_base_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load Knowledge Base configuration from JSON file
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary with Knowledge Base configuration
        """
        env = environment or os.getenv("ENVIRONMENT", "development")
        
        kb_config_file = self.config_dir / "knowledge_base_config.json"
        if not kb_config_file.exists():
            raise ConfigurationError(f"Knowledge Base configuration file not found: {kb_config_file}")
        
        try:
            with open(kb_config_file, 'r') as f:
                config = json.load(f)
            
            if env not in config:
                raise ConfigurationError(f"Environment '{env}' not found in Knowledge Base configuration")
            
            # Merge environment-specific config with common config
            env_config = config[env].copy()
            if "common" in config:
                for key, value in config["common"].items():
                    if key not in env_config:
                        env_config[key] = value
            
            return env_config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in Knowledge Base configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load Knowledge Base configuration: {e}")


# Global configuration loader instance
config_loader = ConfigLoader()


def load_config(environment: Optional[str] = None) -> ApplicationSettings:
    """Convenience function to load configuration
    
    Args:
        environment: Environment name
        
    Returns:
        ApplicationSettings instance
    """
    return config_loader.load_environment_config(environment)


def get_current_environment() -> str:
    """Get current environment name
    
    Returns:
        Current environment name
    """
    return os.getenv("ENVIRONMENT", "development")