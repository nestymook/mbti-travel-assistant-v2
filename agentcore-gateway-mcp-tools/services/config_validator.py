"""
Configuration validation service.

This module provides comprehensive validation for configuration files and settings
to ensure they meet all requirements and constraints.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from pydantic import ValidationError

from services.config_manager import EnvironmentConfig, MCPServerConfig

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error."""
    
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(message)


class ConfigValidator:
    """Configuration validator with comprehensive checks."""
    
    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    async def validate_configuration(self, config: EnvironmentConfig) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a complete configuration.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        try:
            # Validate basic configuration structure
            self._validate_basic_structure(config)
            
            # Validate MCP server configurations
            await self._validate_mcp_servers(config.mcp_servers)
            
            # Validate environment-specific settings
            self._validate_environment_settings(config)
            
            # Check for configuration consistency
            self._validate_configuration_consistency(config)
            
        except Exception as e:
            self.validation_errors.append(f"Unexpected validation error: {str(e)}")
        
        is_valid = len(self.validation_errors) == 0
        return is_valid, self.validation_errors.copy(), self.validation_warnings.copy()
    
    def validate_mcp_server_config(self, server_config: MCPServerConfig) -> Tuple[bool, List[str]]:
        """
        Validate a single MCP server configuration.
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        try:
            # Pydantic validation is already done, check additional constraints
            if not server_config.name.strip():
                errors.append("Server name cannot be empty")
            
            if server_config.timeout <= 0:
                errors.append("Timeout must be positive")
            
            if server_config.max_retries < 0:
                errors.append("Max retries cannot be negative")
            
            if server_config.retry_delay < 0:
                errors.append("Retry delay cannot be negative")
            
            if not server_config.health_check_path.startswith('/'):
                errors.append("Health check path must start with '/'")
            
            if not server_config.tools:
                errors.append("Server must have at least one tool defined")
            
        except Exception as e:
            errors.append(f"Server config validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    async def validate_server_connectivity(self, server_config: MCPServerConfig) -> Tuple[bool, Optional[str]]:
        """
        Validate that an MCP server is reachable.
        
        Returns:
            Tuple of (is_reachable, error_message)
        """
        if not server_config.enabled:
            return True, None  # Skip disabled servers
        
        try:
            health_url = f"{server_config.url.rstrip('/')}{server_config.health_check_path}"
            
            timeout = aiohttp.ClientTimeout(total=server_config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        return True, None
                    else:
                        return False, f"Health check returned status {response.status}"
                        
        except asyncio.TimeoutError:
            return False, f"Connection timeout after {server_config.timeout} seconds"
        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _validate_basic_structure(self, config: EnvironmentConfig):
        """Validate basic configuration structure."""
        if not config.name:
            self.validation_errors.append("Configuration name is required")
        
        if config.name not in ['development', 'staging', 'production', 'test']:
            self.validation_warnings.append(
                f"Unusual environment name '{config.name}'. "
                "Expected: development, staging, production, or test"
            )
        
        if not config.mcp_servers:
            self.validation_errors.append("At least one MCP server must be configured")
    
    async def _validate_mcp_servers(self, servers: Dict[str, MCPServerConfig]):
        """Validate all MCP server configurations."""
        if not servers:
            self.validation_errors.append("No MCP servers configured")
            return
        
        # Check for required servers
        required_servers = ['search', 'reasoning']
        for required_server in required_servers:
            if required_server not in servers:
                self.validation_errors.append(f"Required MCP server '{required_server}' not configured")
        
        # Validate each server configuration
        for server_name, server_config in servers.items():
            is_valid, errors = self.validate_mcp_server_config(server_config)
            if not is_valid:
                for error in errors:
                    self.validation_errors.append(f"Server '{server_name}': {error}")
            
            # Check server connectivity (optional, may be slow)
            # This is commented out for startup validation but can be enabled for health checks
            # is_reachable, error_msg = await self.validate_server_connectivity(server_config)
            # if not is_reachable:
            #     self.validation_warnings.append(f"Server '{server_name}' not reachable: {error_msg}")
    
    def _validate_environment_settings(self, config: EnvironmentConfig):
        """Validate environment-specific settings."""
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level not in valid_log_levels:
            self.validation_errors.append(
                f"Invalid log level '{config.log_level}'. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Production environment checks
        if config.name == 'production':
            if config.debug:
                self.validation_warnings.append("Debug mode is enabled in production")
            
            if config.enable_hot_reload:
                self.validation_warnings.append("Hot reload is enabled in production")
            
            if config.log_level == 'DEBUG':
                self.validation_warnings.append("Debug logging is enabled in production")
        
        # Development environment checks
        if config.name == 'development':
            if not config.debug:
                self.validation_warnings.append("Debug mode is disabled in development")
            
            if not config.enable_hot_reload:
                self.validation_warnings.append("Hot reload is disabled in development")
    
    def _validate_configuration_consistency(self, config: EnvironmentConfig):
        """Validate configuration consistency and relationships."""
        # Check for duplicate server URLs
        urls = {}
        for server_name, server_config in config.mcp_servers.items():
            if server_config.url in urls:
                self.validation_warnings.append(
                    f"Servers '{server_name}' and '{urls[server_config.url]}' "
                    f"have the same URL: {server_config.url}"
                )
            else:
                urls[server_config.url] = server_name
        
        # Check for overlapping tools
        all_tools = {}
        for server_name, server_config in config.mcp_servers.items():
            for tool in server_config.tools:
                if tool in all_tools:
                    self.validation_warnings.append(
                        f"Tool '{tool}' is defined on both servers "
                        f"'{server_name}' and '{all_tools[tool]}'"
                    )
                else:
                    all_tools[tool] = server_name
        
        # Validate required tools are present
        required_tools = [
            'search_restaurants_by_district',
            'search_restaurants_by_meal_type',
            'search_restaurants_combined',
            'recommend_restaurants',
            'analyze_restaurant_sentiment'
        ]
        
        for required_tool in required_tools:
            if required_tool not in all_tools:
                self.validation_errors.append(f"Required tool '{required_tool}' not found in any server")


async def validate_configuration_file(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a configuration file.
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ConfigValidator()
    
    try:
        # Try to load and parse the configuration
        import json
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        # Create EnvironmentConfig instance for validation
        config = EnvironmentConfig(**config_data)
        
        # Validate the configuration
        return await validator.validate_configuration(config)
        
    except FileNotFoundError:
        return False, [f"Configuration file not found: {file_path}"], []
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in configuration file: {str(e)}"], []
    except ValidationError as e:
        errors = [f"Configuration validation error: {error['msg']}" for error in e.errors()]
        return False, errors, []
    except Exception as e:
        return False, [f"Unexpected error validating configuration: {str(e)}"], []


async def validate_all_environment_configs() -> Dict[str, Tuple[bool, List[str], List[str]]]:
    """
    Validate all environment configuration files.
    
    Returns:
        Dictionary mapping environment names to validation results
    """
    environments = ['development', 'staging', 'production', 'test']
    results = {}
    
    for env in environments:
        config_file = f"config/{env}.json"
        results[env] = await validate_configuration_file(config_file)
    
    return results


# Global validator instance
_validator: Optional[ConfigValidator] = None


def get_config_validator() -> ConfigValidator:
    """Get the global configuration validator instance."""
    global _validator
    if _validator is None:
        _validator = ConfigValidator()
    return _validator