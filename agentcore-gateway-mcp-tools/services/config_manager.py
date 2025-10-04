"""
Configuration management service with hot reloading support.

This module provides centralized configuration management with support for:
- Loading configuration from multiple sources (files, environment variables)
- Hot reloading of configuration changes
- Environment-specific configurations
- Configuration validation
"""

import json
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import BaseModel, Field, validator
from threading import Lock
import yaml

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    
    name: str = Field(..., description="Server name identifier")
    url: str = Field(..., description="Server URL endpoint")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    health_check_path: str = Field(default="/health", description="Health check endpoint path")
    enabled: bool = Field(default=True, description="Whether server is enabled")
    tools: List[str] = Field(default_factory=list, description="Available tools on this server")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    
    name: str = Field(..., description="Environment name (development, staging, production)")
    mcp_servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="MCP server configurations"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    enable_hot_reload: bool = Field(default=True, description="Enable configuration hot reloading")
    
    @validator('name')
    def validate_environment_name(cls, v):
        """Validate environment name."""
        valid_envs = ['development', 'staging', 'production', 'test']
        if v not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v


class ConfigurationChangeHandler(FileSystemEventHandler):
    """File system event handler for configuration changes."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self.last_modified = {}
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Check if this is a configuration file
        if not self._is_config_file(file_path):
            return
            
        # Debounce rapid file changes
        current_time = datetime.now().timestamp()
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < 1.0:  # 1 second debounce
                return
                
        self.last_modified[file_path] = current_time
        
        logger.info(f"Configuration file changed: {file_path}")
        
        # Trigger configuration reload
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.config_manager.reload_configuration())
        except RuntimeError:
            # No event loop running, schedule for later
            logger.warning("No event loop running, configuration reload skipped")
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_extensions = ['.json', '.yaml', '.yml', '.env']
        return any(file_path.endswith(ext) for ext in config_extensions)


class ConfigManager:
    """Configuration manager with hot reloading support."""
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.current_config: Optional[EnvironmentConfig] = None
        self.observers: List[Observer] = []
        self.change_callbacks: List[Callable[[EnvironmentConfig], None]] = []
        self._lock = Lock()
        self._settings = get_settings()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
    async def initialize(self) -> EnvironmentConfig:
        """Initialize configuration manager and load initial configuration."""
        logger.info(f"Initializing configuration manager for environment: {self.environment}")
        
        # Load initial configuration
        config = await self.load_configuration()
        
        # Start file watching if hot reload is enabled
        if config.enable_hot_reload:
            self.start_file_watching()
            
        return config
    
    async def load_configuration(self) -> EnvironmentConfig:
        """Load configuration from files and environment variables."""
        with self._lock:
            try:
                # Load base configuration
                base_config = self._load_base_config()
                
                # Load environment-specific configuration
                env_config = self._load_environment_config()
                
                # Merge configurations
                merged_config = self._merge_configurations(base_config, env_config)
                
                # Validate configuration
                config = EnvironmentConfig(**merged_config)
                
                # Update current configuration
                old_config = self.current_config
                self.current_config = config
                
                # Notify callbacks if configuration changed
                if old_config != config:
                    await self._notify_change_callbacks(config)
                
                logger.info("Configuration loaded successfully")
                return config
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                if self.current_config:
                    logger.warning("Using previous configuration")
                    return self.current_config
                raise
    
    async def reload_configuration(self):
        """Reload configuration from files."""
        logger.info("Reloading configuration...")
        try:
            await self.load_configuration()
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def get_current_config(self) -> Optional[EnvironmentConfig]:
        """Get the current configuration."""
        return self.current_config
    
    def get_mcp_server_config(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get configuration for a specific MCP server."""
        if not self.current_config:
            return None
        return self.current_config.mcp_servers.get(server_name)
    
    def get_all_mcp_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all MCP server configurations."""
        if not self.current_config:
            return {}
        return self.current_config.mcp_servers
    
    def add_change_callback(self, callback: Callable[[EnvironmentConfig], None]):
        """Add a callback to be notified when configuration changes."""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[EnvironmentConfig], None]):
        """Remove a configuration change callback."""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)
    
    def start_file_watching(self):
        """Start watching configuration files for changes."""
        if self.observers:
            return  # Already watching
            
        try:
            observer = Observer()
            handler = ConfigurationChangeHandler(self)
            
            # Watch config directory
            observer.schedule(handler, str(self.config_dir), recursive=True)
            
            # Watch root directory for .env files
            observer.schedule(handler, ".", recursive=False)
            
            observer.start()
            self.observers.append(observer)
            
            logger.info("Started configuration file watching")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
    
    def stop_file_watching(self):
        """Stop watching configuration files."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        logger.info("Stopped configuration file watching")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration."""
        config = {
            "name": self.environment,
            "mcp_servers": {},
            "log_level": self._settings.app.log_level,
            "debug": self._settings.app.debug,
            "enable_hot_reload": True
        }
        
        # Add default MCP servers from settings
        config["mcp_servers"]["search"] = {
            "name": "search",
            "url": self._settings.mcp.search_server_url,
            "timeout": self._settings.mcp.connection_timeout,
            "max_retries": self._settings.mcp.max_retries,
            "retry_delay": self._settings.mcp.retry_delay,
            "tools": [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ]
        }
        
        config["mcp_servers"]["reasoning"] = {
            "name": "reasoning",
            "url": self._settings.mcp.reasoning_server_url,
            "timeout": self._settings.mcp.connection_timeout,
            "max_retries": self._settings.mcp.max_retries,
            "retry_delay": self._settings.mcp.retry_delay,
            "tools": [
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]
        }
        
        return config
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        config_files = [
            self.config_dir / f"{self.environment}.json",
            self.config_dir / f"{self.environment}.yaml",
            self.config_dir / f"{self.environment}.yml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                return self._load_config_file(config_file)
        
        logger.warning(f"No environment-specific config found for {self.environment}")
        return {}
    
    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    return json.load(f)
                elif file_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {file_path.suffix}")
                    
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
            return {}
    
    def _merge_configurations(self, base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and environment configurations."""
        merged = base.copy()
        
        for key, value in env.items():
            if key == "mcp_servers" and isinstance(value, dict):
                # Merge MCP server configurations
                if "mcp_servers" not in merged:
                    merged["mcp_servers"] = {}
                merged["mcp_servers"].update(value)
            else:
                merged[key] = value
        
        return merged
    
    async def _notify_change_callbacks(self, config: EnvironmentConfig):
        """Notify all registered callbacks about configuration changes."""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(config)
                else:
                    callback(config)
            except Exception as e:
                logger.error(f"Error in configuration change callback: {e}")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


async def initialize_config_manager(environment: Optional[str] = None) -> EnvironmentConfig:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigManager(environment=environment)
    return await _config_manager.initialize()


def shutdown_config_manager():
    """Shutdown the global configuration manager."""
    global _config_manager
    if _config_manager:
        _config_manager.stop_file_watching()
        _config_manager = None