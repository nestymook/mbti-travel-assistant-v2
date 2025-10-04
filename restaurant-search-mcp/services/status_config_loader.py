"""
Configuration loader for MCP server status check system.

This module handles loading, validation, and management of status check
configurations from JSON files and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.status_models import (
    MCPStatusCheckConfig,
    CircuitBreakerConfig,
    DEFAULT_MCP_SERVER_CONFIGS
)


class StatusCheckConfigLoader:
    """Loads and manages status check configuration."""
    
    def __init__(self, config_file_path: str = "config/status_check_config.json"):
        """Initialize the configuration loader.
        
        Args:
            config_file_path: Path to the status check configuration file
        """
        self.config_file_path = config_file_path
        self._config_data: Optional[Dict[str, Any]] = None
        self._last_loaded: Optional[datetime] = None
        
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            force_reload: Force reload even if already loaded
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if self._config_data is not None and not force_reload:
            return self._config_data
            
        config_path = Path(self.config_file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Status check config file not found: {config_path}")
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
                self._last_loaded = datetime.now()
                
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            return self._config_data
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in status check config file: {e.msg}",
                e.doc,
                e.pos
            )
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        if not self._config_data:
            return
            
        # Override global settings from environment
        env_mappings = {
            'MCP_STATUS_CHECK_ENABLED': ('status_check_system', 'enabled'),
            'MCP_STATUS_CHECK_INTERVAL': ('status_check_system', 'global_check_interval_seconds'),
            'MCP_STATUS_CHECK_TIMEOUT': ('status_check_system', 'global_timeout_seconds'),
            'MCP_GATEWAY_BASE_URL': None,  # Special handling for server URLs
            'JWT_TOKEN': None,  # Special handling for authentication
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                if config_path is None:
                    # Special handling
                    if env_var == 'MCP_GATEWAY_BASE_URL':
                        self._update_server_urls(env_value)
                    elif env_var == 'JWT_TOKEN':
                        self._update_jwt_tokens(env_value)
                else:
                    # Direct config path update
                    section, key = config_path
                    if section in self._config_data:
                        # Convert string values to appropriate types
                        if key.endswith('_seconds') or key.endswith('_minutes'):
                            try:
                                env_value = int(env_value)
                            except ValueError:
                                continue
                        elif key == 'enabled':
                            env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                            
                        self._config_data[section][key] = env_value
    
    def _update_server_urls(self, base_url: str) -> None:
        """Update server endpoint URLs with new base URL."""
        if 'servers' not in self._config_data:
            return
            
        base_url = base_url.rstrip('/')
        for server_name, server_config in self._config_data['servers'].items():
            # Update endpoint URL to use new base URL
            server_config['endpoint_url'] = f"{base_url}/mcp/{server_name}"
    
    def _update_jwt_tokens(self, jwt_token: str) -> None:
        """Update JWT tokens for all servers."""
        if 'servers' not in self._config_data:
            return
            
        for server_config in self._config_data['servers'].values():
            server_config['jwt_token'] = jwt_token
    
    def get_server_configs(self) -> Dict[str, MCPStatusCheckConfig]:
        """Get all server configurations as MCPStatusCheckConfig objects.
        
        Returns:
            Dictionary mapping server names to configuration objects
        """
        config_data = self.load_config()
        server_configs = {}
        
        servers_config = config_data.get('servers', {})
        circuit_breaker_defaults = config_data.get('circuit_breaker_defaults', {})
        
        for server_name, server_data in servers_config.items():
            # Merge circuit breaker config with defaults
            cb_config = {**circuit_breaker_defaults, **server_data.get('circuit_breaker', {})}
            circuit_breaker = CircuitBreakerConfig(**cb_config)
            
            # Create server config
            server_config = MCPStatusCheckConfig(
                server_name=server_data['server_name'],
                endpoint_url=server_data['endpoint_url'],
                check_interval_seconds=server_data.get('check_interval_seconds', 30),
                timeout_seconds=server_data.get('timeout_seconds', 10),
                jwt_token=server_data.get('jwt_token'),
                circuit_breaker=circuit_breaker,
                enabled=server_data.get('enabled', True),
                retry_attempts=server_data.get('retry_attempts', 3),
                retry_delay_seconds=server_data.get('retry_delay_seconds', 1.0),
                exponential_backoff=server_data.get('exponential_backoff', True),
                max_retry_delay_seconds=server_data.get('max_retry_delay_seconds', 30.0)
            )
            
            server_configs[server_name] = server_config
            
        return server_configs
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system-level configuration settings.
        
        Returns:
            System configuration dictionary
        """
        config_data = self.load_config()
        return config_data.get('status_check_system', {})
    
    def get_authentication_config(self) -> Dict[str, Any]:
        """Get authentication configuration.
        
        Returns:
            Authentication configuration dictionary
        """
        config_data = self.load_config()
        return config_data.get('authentication', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        config_data = self.load_config()
        return config_data.get('logging', {})
    
    def get_alerting_config(self) -> Dict[str, Any]:
        """Get alerting configuration.
        
        Returns:
            Alerting configuration dictionary
        """
        config_data = self.load_config()
        return config_data.get('alerting', {})
    
    def is_server_enabled(self, server_name: str) -> bool:
        """Check if a specific server is enabled for status checking.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is enabled, False otherwise
        """
        config_data = self.load_config()
        servers = config_data.get('servers', {})
        
        if server_name not in servers:
            return False
            
        return servers[server_name].get('enabled', True)
    
    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled server names.
        
        Returns:
            List of enabled server names
        """
        config_data = self.load_config()
        servers = config_data.get('servers', {})
        
        return [
            name for name, config in servers.items()
            if config.get('enabled', True)
        ]
    
    def validate_config(self) -> List[str]:
        """Validate the loaded configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            config_data = self.load_config()
        except Exception as e:
            return [f"Failed to load config: {str(e)}"]
        
        # Validate system config
        system_config = config_data.get('status_check_system', {})
        if not isinstance(system_config.get('enabled'), bool):
            errors.append("status_check_system.enabled must be a boolean")
            
        if not isinstance(system_config.get('global_check_interval_seconds'), int):
            errors.append("status_check_system.global_check_interval_seconds must be an integer")
        elif system_config.get('global_check_interval_seconds', 0) <= 0:
            errors.append("status_check_system.global_check_interval_seconds must be positive")
        
        # Validate server configs
        servers = config_data.get('servers', {})
        if not isinstance(servers, dict):
            errors.append("servers must be a dictionary")
        else:
            for server_name, server_config in servers.items():
                if not isinstance(server_config, dict):
                    errors.append(f"Server config for '{server_name}' must be a dictionary")
                    continue
                    
                # Validate required fields
                required_fields = ['server_name', 'endpoint_url']
                for field in required_fields:
                    if field not in server_config:
                        errors.append(f"Server '{server_name}' missing required field: {field}")
                
                # Validate URL format
                endpoint_url = server_config.get('endpoint_url', '')
                if not endpoint_url.startswith(('http://', 'https://')):
                    errors.append(f"Server '{server_name}' endpoint_url must be a valid HTTP/HTTPS URL")
                
                # Validate numeric fields
                numeric_fields = {
                    'check_interval_seconds': (1, 3600),
                    'timeout_seconds': (1, 300),
                    'retry_attempts': (0, 10),
                    'retry_delay_seconds': (0.1, 60.0),
                    'max_retry_delay_seconds': (1.0, 300.0)
                }
                
                for field, (min_val, max_val) in numeric_fields.items():
                    if field in server_config:
                        value = server_config[field]
                        if not isinstance(value, (int, float)):
                            errors.append(f"Server '{server_name}' {field} must be numeric")
                        elif not (min_val <= value <= max_val):
                            errors.append(f"Server '{server_name}' {field} must be between {min_val} and {max_val}")
        
        return errors
    
    def save_config(self, config_data: Dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config_data: Configuration data to save
            
        Raises:
            OSError: If unable to write to config file
        """
        config_path = Path(self.config_file_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
                
            # Update cached config
            self._config_data = config_data
            self._last_loaded = datetime.now()
            
        except OSError as e:
            raise OSError(f"Failed to save config file: {str(e)}")
    
    def reload_if_changed(self) -> bool:
        """Reload configuration if file has been modified.
        
        Returns:
            True if configuration was reloaded, False otherwise
        """
        if not self._last_loaded:
            return False
            
        config_path = Path(self.config_file_path)
        if not config_path.exists():
            return False
            
        try:
            file_mtime = datetime.fromtimestamp(config_path.stat().st_mtime)
            if file_mtime > self._last_loaded:
                self.load_config(force_reload=True)
                return True
        except OSError:
            pass
            
        return False


# Global configuration loader instance
_config_loader: Optional[StatusCheckConfigLoader] = None


def get_config_loader(config_file_path: str = "config/status_check_config.json") -> StatusCheckConfigLoader:
    """Get the global configuration loader instance.
    
    Args:
        config_file_path: Path to configuration file
        
    Returns:
        StatusCheckConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = StatusCheckConfigLoader(config_file_path)
    return _config_loader


def load_server_configs() -> Dict[str, MCPStatusCheckConfig]:
    """Convenience function to load server configurations.
    
    Returns:
        Dictionary mapping server names to configuration objects
    """
    loader = get_config_loader()
    return loader.get_server_configs()


def validate_status_check_config(config_file_path: str = "config/status_check_config.json") -> List[str]:
    """Validate status check configuration file.
    
    Args:
        config_file_path: Path to configuration file
        
    Returns:
        List of validation errors (empty if valid)
    """
    loader = StatusCheckConfigLoader(config_file_path)
    return loader.validate_config()