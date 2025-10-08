"""
Runtime Configuration Manager

This module provides runtime configuration management capabilities including
hot-reloading, validation, rollback, and audit trail functionality.
"""

import asyncio
import logging
import threading
import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
import copy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .orchestration_config import OrchestrationConfig, ConfigurationError

logger = logging.getLogger(__name__)


class ConfigChangeType(Enum):
    """Types of configuration changes."""
    RELOAD = "reload"
    UPDATE = "update"
    ROLLBACK = "rollback"
    VALIDATION_FAILURE = "validation_failure"


@dataclass
class ConfigChangeEvent:
    """Configuration change event record."""
    timestamp: datetime
    change_type: ConfigChangeType
    source: str  # file, api, manual
    user_id: Optional[str] = None
    changes: Dict[str, Any] = None
    previous_config_hash: Optional[str] = None
    new_config_hash: Optional[str] = None
    validation_errors: List[str] = None
    rollback_reason: Optional[str] = None
    success: bool = True


class ConfigurationFileWatcher(FileSystemEventHandler):
    """File system watcher for configuration changes."""
    
    def __init__(self, config_manager: 'RuntimeConfigManager'):
        self.config_manager = config_manager
        self.last_modified = {}
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix in ['.yaml', '.yml', '.json']:
            # Debounce rapid file changes
            current_time = time.time()
            last_mod = self.last_modified.get(file_path, 0)
            
            if current_time - last_mod > 1.0:  # 1 second debounce
                self.last_modified[file_path] = current_time
                logger.info(f"Configuration file modified: {file_path}")
                
                # Schedule reload in the background
                asyncio.create_task(
                    self.config_manager._handle_file_change(str(file_path))
                )


class RuntimeConfigManager:
    """
    Runtime configuration manager with hot-reloading, validation, and rollback capabilities.
    
    Provides advanced configuration management features including:
    - Hot-reloading of configuration changes
    - Configuration validation and rollback
    - Change audit trail and logging
    - Thread-safe configuration updates
    - Configuration change notifications
    """
    
    def __init__(self, 
                 config: OrchestrationConfig,
                 enable_hot_reload: bool = True,
                 enable_audit_trail: bool = True,
                 max_audit_entries: int = 1000):
        """
        Initialize runtime configuration manager.
        
        Args:
            config: Base orchestration configuration
            enable_hot_reload: Enable automatic configuration reloading
            enable_audit_trail: Enable configuration change audit trail
            max_audit_entries: Maximum number of audit entries to keep
        """
        self.config = config
        self.enable_hot_reload = enable_hot_reload
        self.enable_audit_trail = enable_audit_trail
        self.max_audit_entries = max_audit_entries
        
        # Configuration state management
        self._config_lock = threading.RLock()
        self._config_history: List[Dict[str, Any]] = []
        self._audit_trail: List[ConfigChangeEvent] = []
        self._change_callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        
        # File watching
        self._file_observer: Optional[Observer] = None
        self._file_watcher: Optional[ConfigurationFileWatcher] = None
        
        # Configuration backup for rollback
        self._config_backup: Optional[Dict[str, Any]] = None
        self._backup_timestamp: Optional[datetime] = None
        
        # Initialize
        self._initialize_manager()
        
        logger.info("Runtime configuration manager initialized")
    
    def _initialize_manager(self) -> None:
        """Initialize the configuration manager."""
        # Create initial backup
        self._create_config_backup()
        
        # Start file watching if enabled
        if self.enable_hot_reload:
            self._start_file_watching()
        
        # Log initial state
        if self.enable_audit_trail:
            self._log_config_change(ConfigChangeEvent(
                timestamp=datetime.now(timezone.utc),
                change_type=ConfigChangeType.RELOAD,
                source="initialization",
                new_config_hash=self._calculate_config_hash(),
                success=True
            ))
    
    def _start_file_watching(self) -> None:
        """Start file system watching for configuration changes."""
        try:
            config_dir = Path(self.config.config_path).parent
            
            self._file_watcher = ConfigurationFileWatcher(self)
            self._file_observer = Observer()
            self._file_observer.schedule(
                self._file_watcher, 
                str(config_dir), 
                recursive=False
            )
            self._file_observer.start()
            
            logger.info(f"Started configuration file watching: {config_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")
            self.enable_hot_reload = False
    
    def _stop_file_watching(self) -> None:
        """Stop file system watching."""
        if self._file_observer:
            self._file_observer.stop()
            self._file_observer.join()
            self._file_observer = None
            self._file_watcher = None
            logger.info("Stopped configuration file watching")
    
    async def _handle_file_change(self, file_path: str) -> None:
        """Handle configuration file changes."""
        if file_path != self.config.config_path:
            return
        
        logger.info(f"Handling configuration file change: {file_path}")
        
        try:
            # Attempt to reload configuration
            await self.reload_configuration(source="file_watcher")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration after file change: {e}")
            
            # Log the failure
            if self.enable_audit_trail:
                self._log_config_change(ConfigChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    change_type=ConfigChangeType.VALIDATION_FAILURE,
                    source="file_watcher",
                    validation_errors=[str(e)],
                    success=False
                ))
    
    def _create_config_backup(self) -> None:
        """Create a backup of the current configuration."""
        with self._config_lock:
            self._config_backup = self.config.to_dict()
            self._backup_timestamp = datetime.now(timezone.utc)
            
            # Add to history
            self._config_history.append({
                'timestamp': self._backup_timestamp.isoformat(),
                'config': copy.deepcopy(self._config_backup),
                'hash': self._calculate_config_hash()
            })
            
            # Limit history size
            if len(self._config_history) > self.max_audit_entries:
                self._config_history = self._config_history[-self.max_audit_entries:]
    
    def _calculate_config_hash(self) -> str:
        """Calculate hash of current configuration."""
        config_str = json.dumps(self.config.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def _log_config_change(self, event: ConfigChangeEvent) -> None:
        """Log configuration change event."""
        if not self.enable_audit_trail:
            return
        
        with self._config_lock:
            self._audit_trail.append(event)
            
            # Limit audit trail size
            if len(self._audit_trail) > self.max_audit_entries:
                self._audit_trail = self._audit_trail[-self.max_audit_entries:]
        
        # Notify callbacks
        for callback in self._change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in configuration change callback: {e}")
        
        # Log the event
        log_level = logging.INFO if event.success else logging.ERROR
        logger.log(log_level, 
                  f"Configuration change: {event.change_type.value} "
                  f"from {event.source} - Success: {event.success}")
    
    async def reload_configuration(self, 
                                 source: str = "manual",
                                 user_id: Optional[str] = None,
                                 validate: bool = True) -> bool:
        """
        Reload configuration from file with validation and rollback support.
        
        Args:
            source: Source of the reload request
            user_id: User ID initiating the reload
            validate: Whether to validate the new configuration
            
        Returns:
            True if reload was successful, False otherwise
        """
        previous_hash = self._calculate_config_hash()
        
        try:
            with self._config_lock:
                # Create backup before reload
                self._create_config_backup()
                
                # Attempt to reload
                self.config.reload_config()
                
                # Validate if requested
                if validate:
                    self.config.validate_configuration()
                
                new_hash = self._calculate_config_hash()
                
                # Log successful change
                if self.enable_audit_trail:
                    self._log_config_change(ConfigChangeEvent(
                        timestamp=datetime.now(timezone.utc),
                        change_type=ConfigChangeType.RELOAD,
                        source=source,
                        user_id=user_id,
                        previous_config_hash=previous_hash,
                        new_config_hash=new_hash,
                        success=True
                    ))
                
                logger.info(f"Configuration reloaded successfully from {source}")
                return True
                
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            
            # Log failure
            if self.enable_audit_trail:
                self._log_config_change(ConfigChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    change_type=ConfigChangeType.VALIDATION_FAILURE,
                    source=source,
                    user_id=user_id,
                    previous_config_hash=previous_hash,
                    validation_errors=[str(e)],
                    success=False
                ))
            
            return False
    
    async def update_configuration(self,
                                 updates: Dict[str, Any],
                                 source: str = "api",
                                 user_id: Optional[str] = None,
                                 validate: bool = True) -> bool:
        """
        Update configuration with specific changes.
        
        Args:
            updates: Dictionary of configuration updates
            source: Source of the update request
            user_id: User ID making the update
            validate: Whether to validate after update
            
        Returns:
            True if update was successful, False otherwise
        """
        previous_hash = self._calculate_config_hash()
        
        # Pre-validate updates if validation is enabled
        if validate:
            validation_errors = validate_config_updates(updates)
            if validation_errors:
                logger.error(f"Configuration update validation failed: {validation_errors}")
                
                # Log failure without attempting update
                if self.enable_audit_trail:
                    self._log_config_change(ConfigChangeEvent(
                        timestamp=datetime.now(timezone.utc),
                        change_type=ConfigChangeType.VALIDATION_FAILURE,
                        source=source,
                        user_id=user_id,
                        changes=updates,
                        previous_config_hash=previous_hash,
                        validation_errors=validation_errors,
                        success=False
                    ))
                
                return False
        
        try:
            with self._config_lock:
                # Create backup before update
                self._create_config_backup()
                
                # Apply updates to raw config
                self._apply_config_updates(updates)
                
                # Reload configuration with updates
                self.config.load_config()
                
                # Validate if requested
                if validate:
                    self.config.validate_configuration()
                
                new_hash = self._calculate_config_hash()
                
                # Log successful change
                if self.enable_audit_trail:
                    self._log_config_change(ConfigChangeEvent(
                        timestamp=datetime.now(timezone.utc),
                        change_type=ConfigChangeType.UPDATE,
                        source=source,
                        user_id=user_id,
                        changes=updates,
                        previous_config_hash=previous_hash,
                        new_config_hash=new_hash,
                        success=True
                    ))
                
                logger.info(f"Configuration updated successfully from {source}")
                return True
                
        except Exception as e:
            logger.error(f"Configuration update failed: {e}")
            
            # Attempt rollback
            await self.rollback_configuration(
                reason=f"Update validation failed: {e}",
                source=source,
                user_id=user_id
            )
            
            # Log failure
            if self.enable_audit_trail:
                self._log_config_change(ConfigChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    change_type=ConfigChangeType.VALIDATION_FAILURE,
                    source=source,
                    user_id=user_id,
                    changes=updates,
                    previous_config_hash=previous_hash,
                    validation_errors=[str(e)],
                    success=False
                ))
            
            return False
    
    def _apply_config_updates(self, updates: Dict[str, Any]) -> None:
        """Apply configuration updates to the raw config."""
        # Read current config from file
        with open(self.config.config_path, 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
        
        # Apply updates
        self._deep_update(current_config, updates)
        
        # Write back to file
        with open(self.config.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, default_flow_style=False)
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Deep update dictionary with nested updates."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    async def rollback_configuration(self,
                                   reason: str,
                                   source: str = "system",
                                   user_id: Optional[str] = None) -> bool:
        """
        Rollback configuration to the last known good state.
        
        Args:
            reason: Reason for rollback
            source: Source of rollback request
            user_id: User ID initiating rollback
            
        Returns:
            True if rollback was successful, False otherwise
        """
        if not self._config_backup:
            logger.error("No configuration backup available for rollback")
            return False
        
        previous_hash = self._calculate_config_hash()
        
        try:
            with self._config_lock:
                # Get the backup config from history (not current backup which might be corrupted)
                if len(self._config_history) >= 2:
                    # Use the second-to-last config (last known good)
                    backup_config = self._config_history[-2]['config']
                else:
                    # Fallback to current backup
                    backup_config = self._config_backup
                
                # Extract just the config sections for writing
                config_to_write = {
                    'orchestration': backup_config.get('orchestration', {}),
                    'tools': backup_config.get('tools', {}),
                    'logging': backup_config.get('logging', {}),
                    'integrations': backup_config.get('integrations', {}),
                    'environments': backup_config.get('environments', {})
                }
                
                with open(self.config.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_to_write, f, default_flow_style=False)
                
                # Reload from file
                self.config.load_config()
                self.config.validate_configuration()
                
                new_hash = self._calculate_config_hash()
                
                # Log rollback
                if self.enable_audit_trail:
                    self._log_config_change(ConfigChangeEvent(
                        timestamp=datetime.now(timezone.utc),
                        change_type=ConfigChangeType.ROLLBACK,
                        source=source,
                        user_id=user_id,
                        previous_config_hash=previous_hash,
                        new_config_hash=new_hash,
                        rollback_reason=reason,
                        success=True
                    ))
                
                logger.info(f"Configuration rolled back successfully: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Configuration rollback failed: {e}")
            
            # Log rollback failure
            if self.enable_audit_trail:
                self._log_config_change(ConfigChangeEvent(
                    timestamp=datetime.now(timezone.utc),
                    change_type=ConfigChangeType.ROLLBACK,
                    source=source,
                    user_id=user_id,
                    previous_config_hash=previous_hash,
                    rollback_reason=reason,
                    validation_errors=[str(e)],
                    success=False
                ))
            
            return False
    
    def add_change_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Add callback for configuration changes."""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """Remove configuration change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def get_audit_trail(self, 
                       limit: Optional[int] = None,
                       change_type: Optional[ConfigChangeType] = None) -> List[ConfigChangeEvent]:
        """
        Get configuration change audit trail.
        
        Args:
            limit: Maximum number of entries to return
            change_type: Filter by specific change type
            
        Returns:
            List of configuration change events
        """
        with self._config_lock:
            trail = self._audit_trail.copy()
        
        # Filter by change type if specified
        if change_type:
            trail = [event for event in trail if event.change_type == change_type]
        
        # Apply limit
        if limit:
            trail = trail[-limit:]
        
        return trail
    
    def get_configuration_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get configuration history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of historical configuration states
        """
        with self._config_lock:
            history = self._config_history.copy()
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_current_config_info(self) -> Dict[str, Any]:
        """Get current configuration information."""
        return {
            'config_path': self.config.config_path,
            'environment': self.config.environment,
            'config_hash': self._calculate_config_hash(),
            'backup_available': self._config_backup is not None,
            'backup_timestamp': self._backup_timestamp.isoformat() if self._backup_timestamp else None,
            'hot_reload_enabled': self.enable_hot_reload,
            'audit_trail_enabled': self.enable_audit_trail,
            'audit_entries': len(self._audit_trail),
            'history_entries': len(self._config_history)
        }
    
    def export_audit_trail(self, file_path: str) -> None:
        """Export audit trail to file."""
        with self._config_lock:
            audit_data = []
            for event in self._audit_trail:
                audit_data.append({
                    'timestamp': event.timestamp.isoformat(),
                    'change_type': event.change_type.value,
                    'source': event.source,
                    'user_id': event.user_id,
                    'changes': event.changes,
                    'previous_config_hash': event.previous_config_hash,
                    'new_config_hash': event.new_config_hash,
                    'validation_errors': event.validation_errors,
                    'rollback_reason': event.rollback_reason,
                    'success': event.success
                })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Audit trail exported to: {file_path}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self._stop_file_watching()
        self._change_callbacks.clear()
        logger.info("Runtime configuration manager cleaned up")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Utility functions for configuration management
async def create_runtime_config_manager(
    config_path: Optional[str] = None,
    environment: Optional[str] = None,
    enable_hot_reload: bool = True,
    enable_audit_trail: bool = True
) -> RuntimeConfigManager:
    """
    Create and initialize a runtime configuration manager.
    
    Args:
        config_path: Path to configuration file
        environment: Environment name
        enable_hot_reload: Enable hot-reloading
        enable_audit_trail: Enable audit trail
        
    Returns:
        Initialized runtime configuration manager
    """
    # Load base configuration
    base_config = OrchestrationConfig(
        config_path=config_path,
        environment=environment,
        validate_on_load=True
    )
    
    # Create runtime manager
    runtime_manager = RuntimeConfigManager(
        config=base_config,
        enable_hot_reload=enable_hot_reload,
        enable_audit_trail=enable_audit_trail
    )
    
    return runtime_manager


def validate_config_updates(updates: Dict[str, Any]) -> List[str]:
    """
    Validate configuration updates before applying them.
    
    Args:
        updates: Configuration updates to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate orchestration updates
    if 'orchestration' in updates:
        orch_updates = updates['orchestration']
        
        # Validate intent analysis
        if 'intent_analysis' in orch_updates:
            intent = orch_updates['intent_analysis']
            if 'confidence_threshold' in intent:
                threshold = intent['confidence_threshold']
                if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                    errors.append("Intent analysis confidence threshold must be between 0.0 and 1.0")
        
        # Validate tool selection weights
        if 'tool_selection' in orch_updates:
            selection = orch_updates['tool_selection']
            weights = []
            for weight_key in ['performance_weight', 'health_weight', 'capability_weight']:
                if weight_key in selection:
                    weight = selection[weight_key]
                    if not isinstance(weight, (int, float)) or weight < 0:
                        errors.append(f"Tool selection {weight_key} must be non-negative")
                    weights.append(weight)
            
            if len(weights) == 3 and abs(sum(weights) - 1.0) > 0.01:
                errors.append("Tool selection weights must sum to 1.0")
    
    # Validate tools updates
    if 'tools' in updates:
        tools_updates = updates['tools']
        for tool_name, tool_config in tools_updates.items():
            if 'priority' in tool_config:
                priority = tool_config['priority']
                if not isinstance(priority, int) or priority < 0:
                    errors.append(f"Tool {tool_name} priority must be a non-negative integer")
            
            if 'performance' in tool_config:
                perf = tool_config['performance']
                if 'expected_success_rate' in perf:
                    rate = perf['expected_success_rate']
                    if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
                        errors.append(f"Tool {tool_name} expected success rate must be between 0.0 and 1.0")
    
    return errors