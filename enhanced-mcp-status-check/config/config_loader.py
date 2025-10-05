"""
Configuration Loader with Hot-Reloading Support

This module provides configuration loading, hot-reloading, and migration utilities
for the enhanced MCP status check system.
"""

import asyncio
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

from .enhanced_status_config import (
    EnhancedStatusConfig,
    ConfigurationError,
    ConfigValidationError,
    ConfigFormat
)


logger = logging.getLogger(__name__)


class ConfigFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration hot-reloading."""
    
    def __init__(self, config_loader: 'ConfigLoader'):
        self.config_loader = config_loader
        self.last_reload_time = 0
        self.reload_debounce_seconds = 1.0  # Prevent rapid reloads
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Check if it's our config file
        if Path(event.src_path) == Path(self.config_loader.config_file_path):
            current_time = time.time()
            if current_time - self.last_reload_time > self.reload_debounce_seconds:
                self.last_reload_time = current_time
                logger.info(f"Configuration file changed: {event.src_path}")
                self.config_loader._trigger_reload()


class ConfigMigrator:
    """Utility for migrating legacy configurations to enhanced format."""
    
    @staticmethod
    def migrate_legacy_config(legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy configuration to enhanced format."""
        logger.info("Migrating legacy configuration to enhanced format")
        
        enhanced_data = {
            "system_name": "enhanced-mcp-status-check",
            "version": "1.0.0",
            "dual_monitoring_enabled": True,
            "mcp_health_checks": {},
            "rest_health_checks": {},
            "result_aggregation": {},
            "circuit_breaker": {},
            "monitoring": {},
            "servers": []
        }
        
        # Migrate basic settings
        if "system" in legacy_data:
            system_config = legacy_data["system"]
            enhanced_data["system_name"] = system_config.get("name", "enhanced-mcp-status-check")
            enhanced_data["version"] = system_config.get("version", "1.0.0")
        
        # Migrate MCP settings
        if "mcp" in legacy_data or "mcp_health_checks" in legacy_data:
            mcp_config = legacy_data.get("mcp", legacy_data.get("mcp_health_checks", {}))
            enhanced_data["mcp_health_checks"] = {
                "enabled": mcp_config.get("enabled", True),
                "default_timeout_seconds": mcp_config.get("timeout", 10),
                "default_retry_attempts": mcp_config.get("retry_attempts", 3),
                "tools_list_validation": mcp_config.get("validate_tools", True),
                "expected_tools_validation": mcp_config.get("validate_expected_tools", True),
                "default_expected_tools": mcp_config.get("expected_tools", [])
            }
        
        # Migrate REST settings
        if "rest" in legacy_data or "rest_health_checks" in legacy_data:
            rest_config = legacy_data.get("rest", legacy_data.get("rest_health_checks", {}))
            enhanced_data["rest_health_checks"] = {
                "enabled": rest_config.get("enabled", True),
                "default_timeout_seconds": rest_config.get("timeout", 8),
                "default_retry_attempts": rest_config.get("retry_attempts", 2),
                "health_endpoint_path": rest_config.get("health_path", "/status/health"),
                "metrics_endpoint_path": rest_config.get("metrics_path", "/status/metrics")
            }
        
        # Migrate circuit breaker settings
        if "circuit_breaker" in legacy_data:
            cb_config = legacy_data["circuit_breaker"]
            enhanced_data["circuit_breaker"] = {
                "enabled": cb_config.get("enabled", True),
                "failure_threshold": cb_config.get("failure_threshold", 5),
                "recovery_timeout_seconds": cb_config.get("recovery_timeout", 60)
            }
        
        # Migrate server configurations
        if "servers" in legacy_data:
            for legacy_server in legacy_data["servers"]:
                enhanced_server = {
                    "server_name": legacy_server.get("name", "unknown"),
                    "mcp_endpoint_url": legacy_server.get("mcp_url", ""),
                    "rest_health_endpoint_url": legacy_server.get("rest_url", ""),
                    "mcp_enabled": legacy_server.get("mcp_enabled", True),
                    "rest_enabled": legacy_server.get("rest_enabled", True),
                    "mcp_timeout_seconds": legacy_server.get("mcp_timeout", 10),
                    "rest_timeout_seconds": legacy_server.get("rest_timeout", 8),
                    "mcp_expected_tools": legacy_server.get("expected_tools", [])
                }
                enhanced_data["servers"].append(enhanced_server)
        
        logger.info("Legacy configuration migration completed")
        return enhanced_data
    
    @staticmethod
    def detect_legacy_format(data: Dict[str, Any]) -> bool:
        """Detect if configuration is in legacy format."""
        # Check for legacy indicators
        legacy_indicators = [
            "mcp" in data and "rest" in data,  # Old top-level structure
            "system" in data and "name" in data.get("system", {}),  # Old system config
            any(server.get("mcp_url") for server in data.get("servers", [])),  # Old server format
        ]
        
        # Check for enhanced format indicators
        enhanced_indicators = [
            "mcp_health_checks" in data,
            "rest_health_checks" in data,
            "result_aggregation" in data,
            "dual_monitoring_enabled" in data
        ]
        
        has_legacy = any(legacy_indicators)
        has_enhanced = any(enhanced_indicators)
        
        # If it has legacy indicators but no enhanced indicators, it's legacy
        return has_legacy and not has_enhanced
    
    @staticmethod
    def backup_config(config_path: Union[str, Path]) -> Path:
        """Create backup of existing configuration."""
        config_path = Path(config_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.parent / f"{config_path.stem}_backup_{timestamp}{config_path.suffix}"
        
        if config_path.exists():
            backup_path.write_text(config_path.read_text(), encoding='utf-8')
            logger.info(f"Configuration backed up to: {backup_path}")
        
        return backup_path


class ConfigLoader:
    """Configuration loader with hot-reloading and migration support."""
    
    def __init__(self, config_file_path: Union[str, Path]):
        self.config_file_path = Path(config_file_path)
        self.config: Optional[EnhancedStatusConfig] = None
        self.reload_callbacks: List[Callable[[EnhancedStatusConfig], None]] = []
        
        # Hot-reloading components
        self.hot_reload_enabled = False
        self.file_observer: Optional[Observer] = None
        self.file_watcher: Optional[ConfigFileWatcher] = None
        self._reload_lock = threading.Lock()
        
    def load_config(self, enable_hot_reload: bool = False) -> EnhancedStatusConfig:
        """Load configuration from file with optional hot-reloading."""
        logger.info(f"Loading configuration from: {self.config_file_path}")
        
        try:
            # Check if file exists
            if not self.config_file_path.exists():
                logger.warning(f"Configuration file not found: {self.config_file_path}")
                logger.info("Creating default configuration")
                self.config = EnhancedStatusConfig.create_default()
                self.config.save_to_file(self.config_file_path)
                return self.config
            
            # Load and parse configuration file
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine format and parse
            if self.config_file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)
            
            # Check if migration is needed
            if ConfigMigrator.detect_legacy_format(data):
                logger.info("Legacy configuration format detected, migrating...")
                
                # Backup original
                ConfigMigrator.backup_config(self.config_file_path)
                
                # Migrate
                data = ConfigMigrator.migrate_legacy_config(data)
                
                # Save migrated configuration
                migrated_config = EnhancedStatusConfig.from_dict(data)
                migrated_config.save_to_file(self.config_file_path)
                logger.info("Configuration migration completed and saved")
            
            # Create configuration instance
            self.config = EnhancedStatusConfig.from_dict(data)
            self.config.config_file_path = str(self.config_file_path)
            self.config.last_modified = datetime.fromtimestamp(self.config_file_path.stat().st_mtime)
            
            # Validate configuration
            validation_errors = self.config.validate()
            if validation_errors:
                raise ConfigValidationError(
                    "Configuration validation failed",
                    validation_errors
                )
            
            # Setup hot-reloading if requested
            if enable_hot_reload:
                self.enable_hot_reload()
            
            logger.info("Configuration loaded successfully")
            return self.config
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Invalid configuration file format: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")
    
    def reload_config(self) -> EnhancedStatusConfig:
        """Reload configuration from file."""
        with self._reload_lock:
            logger.info("Reloading configuration...")
            
            try:
                old_config = self.config
                new_config = self.load_config(enable_hot_reload=False)
                
                # Compare configurations to see if anything changed
                if old_config and old_config.to_dict() == new_config.to_dict():
                    logger.info("Configuration unchanged, skipping reload")
                    return self.config
                
                self.config = new_config
                
                # Notify callbacks
                for callback in self.reload_callbacks:
                    try:
                        callback(self.config)
                    except Exception as e:
                        logger.error(f"Error in reload callback: {e}")
                
                logger.info("Configuration reloaded successfully")
                return self.config
                
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")
                # Keep existing configuration on reload failure
                return self.config
    
    def enable_hot_reload(self) -> None:
        """Enable hot-reloading of configuration file."""
        if self.hot_reload_enabled:
            return
        
        logger.info("Enabling configuration hot-reloading")
        
        self.file_watcher = ConfigFileWatcher(self)
        self.file_observer = Observer()
        self.file_observer.schedule(
            self.file_watcher,
            str(self.config_file_path.parent),
            recursive=False
        )
        self.file_observer.start()
        self.hot_reload_enabled = True
        
        logger.info("Configuration hot-reloading enabled")
    
    def disable_hot_reload(self) -> None:
        """Disable hot-reloading of configuration file."""
        if not self.hot_reload_enabled:
            return
        
        logger.info("Disabling configuration hot-reloading")
        
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
        
        self.file_watcher = None
        self.hot_reload_enabled = False
        
        logger.info("Configuration hot-reloading disabled")
    
    def add_reload_callback(self, callback: Callable[[EnhancedStatusConfig], None]) -> None:
        """Add callback to be called when configuration is reloaded."""
        self.reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[EnhancedStatusConfig], None]) -> None:
        """Remove reload callback."""
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)
    
    def _trigger_reload(self) -> None:
        """Internal method to trigger configuration reload."""
        # Use a separate thread to avoid blocking the file watcher
        threading.Thread(target=self.reload_config, daemon=True).start()
    
    def get_config(self) -> Optional[EnhancedStatusConfig]:
        """Get current configuration."""
        return self.config
    
    def save_config(self, config: EnhancedStatusConfig) -> None:
        """Save configuration to file."""
        with self._reload_lock:
            config.save_to_file(self.config_file_path)
            self.config = config
            logger.info("Configuration saved successfully")
    
    def validate_config_file(self) -> List[str]:
        """Validate configuration file without loading it."""
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse file
            if self.config_file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
            else:
                data = json.loads(content)
            
            # Create temporary config instance for validation
            temp_config = EnhancedStatusConfig.from_dict(data)
            return temp_config.validate()
            
        except Exception as e:
            return [f"Configuration file error: {e}"]
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disable_hot_reload()


# Utility functions for configuration management

def load_config_from_file(
    config_path: Union[str, Path],
    enable_hot_reload: bool = False
) -> EnhancedStatusConfig:
    """Utility function to load configuration from file."""
    loader = ConfigLoader(config_path)
    return loader.load_config(enable_hot_reload=enable_hot_reload)


def create_default_config_file(config_path: Union[str, Path]) -> EnhancedStatusConfig:
    """Create a default configuration file."""
    config = EnhancedStatusConfig.create_default()
    config.save_to_file(config_path)
    logger.info(f"Default configuration created at: {config_path}")
    return config


def migrate_legacy_config_file(
    legacy_path: Union[str, Path],
    enhanced_path: Union[str, Path]
) -> EnhancedStatusConfig:
    """Migrate legacy configuration file to enhanced format."""
    legacy_path = Path(legacy_path)
    enhanced_path = Path(enhanced_path)
    
    if not legacy_path.exists():
        raise ConfigurationError(f"Legacy configuration file not found: {legacy_path}")
    
    # Load legacy configuration
    with open(legacy_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if legacy_path.suffix.lower() in ['.yaml', '.yml']:
        legacy_data = yaml.safe_load(content)
    else:
        legacy_data = json.loads(content)
    
    # Migrate to enhanced format
    enhanced_data = ConfigMigrator.migrate_legacy_config(legacy_data)
    enhanced_config = EnhancedStatusConfig.from_dict(enhanced_data)
    
    # Save enhanced configuration
    enhanced_config.save_to_file(enhanced_path)
    
    logger.info(f"Configuration migrated from {legacy_path} to {enhanced_path}")
    return enhanced_config


async def async_config_loader(
    config_path: Union[str, Path],
    reload_interval_seconds: int = 60
) -> EnhancedStatusConfig:
    """Asynchronous configuration loader with periodic reloading."""
    loader = ConfigLoader(config_path)
    config = loader.load_config()
    
    async def reload_periodically():
        while True:
            await asyncio.sleep(reload_interval_seconds)
            try:
                loader.reload_config()
            except Exception as e:
                logger.error(f"Error in periodic config reload: {e}")
    
    # Start periodic reload task
    asyncio.create_task(reload_periodically())
    
    return config