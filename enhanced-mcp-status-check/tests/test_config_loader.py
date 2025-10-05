"""
Tests for Configuration Loader with Hot-Reloading

This module tests the configuration loading, hot-reloading, and migration functionality.
"""

import pytest
import json
import yaml
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from config.config_loader import (
    ConfigLoader,
    ConfigFileWatcher,
    ConfigMigrator,
    load_config_from_file,
    create_default_config_file,
    migrate_legacy_config_file
)
from config.enhanced_status_config import (
    EnhancedStatusConfig,
    ConfigurationError,
    ConfigValidationError
)


class TestConfigMigrator:
    """Test configuration migration functionality."""
    
    def test_detect_legacy_format(self):
        """Test detection of legacy configuration format."""
        # Legacy format
        legacy_data = {
            "system": {"name": "old-system"},
            "mcp": {"enabled": True, "timeout": 10},
            "rest": {"enabled": True, "timeout": 8},
            "servers": [
                {"name": "server1", "mcp_url": "http://localhost:8080/mcp"}
            ]
        }
        
        assert ConfigMigrator.detect_legacy_format(legacy_data) is True
        
        # Enhanced format
        enhanced_data = {
            "system_name": "new-system",
            "mcp_health_checks": {"enabled": True},
            "rest_health_checks": {"enabled": True},
            "dual_monitoring_enabled": True
        }
        
        assert ConfigMigrator.detect_legacy_format(enhanced_data) is False
        
        # Mixed format (has both legacy and enhanced indicators)
        mixed_data = {
            "system": {"name": "mixed-system"},
            "mcp_health_checks": {"enabled": True},
            "dual_monitoring_enabled": True
        }
        
        assert ConfigMigrator.detect_legacy_format(mixed_data) is False
    
    def test_migrate_legacy_config(self):
        """Test migration of legacy configuration."""
        legacy_data = {
            "system": {
                "name": "legacy-system",
                "version": "0.9.0"
            },
            "mcp": {
                "enabled": True,
                "timeout": 15,
                "retry_attempts": 5,
                "validate_tools": True,
                "expected_tools": ["tool1", "tool2"]
            },
            "rest": {
                "enabled": False,
                "timeout": 12,
                "retry_attempts": 3,
                "health_path": "/health"
            },
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 3,
                "recovery_timeout": 120
            },
            "servers": [
                {
                    "name": "server1",
                    "mcp_url": "http://localhost:8080/mcp",
                    "rest_url": "http://localhost:8080/health",
                    "mcp_enabled": True,
                    "rest_enabled": True,
                    "mcp_timeout": 20,
                    "rest_timeout": 15,
                    "expected_tools": ["search", "recommend"]
                }
            ]
        }
        
        enhanced_data = ConfigMigrator.migrate_legacy_config(legacy_data)
        
        # Check system settings
        assert enhanced_data["system_name"] == "legacy-system"
        assert enhanced_data["version"] == "0.9.0"
        assert enhanced_data["dual_monitoring_enabled"] is True
        
        # Check MCP settings
        mcp_config = enhanced_data["mcp_health_checks"]
        assert mcp_config["enabled"] is True
        assert mcp_config["default_timeout_seconds"] == 15
        assert mcp_config["default_retry_attempts"] == 5
        assert mcp_config["tools_list_validation"] is True
        assert mcp_config["default_expected_tools"] == ["tool1", "tool2"]
        
        # Check REST settings
        rest_config = enhanced_data["rest_health_checks"]
        assert rest_config["enabled"] is False
        assert rest_config["default_timeout_seconds"] == 12
        assert rest_config["default_retry_attempts"] == 3
        assert rest_config["health_endpoint_path"] == "/health"
        
        # Check circuit breaker settings
        cb_config = enhanced_data["circuit_breaker"]
        assert cb_config["enabled"] is True
        assert cb_config["failure_threshold"] == 3
        assert cb_config["recovery_timeout_seconds"] == 120
        
        # Check server settings
        servers = enhanced_data["servers"]
        assert len(servers) == 1
        server = servers[0]
        assert server["server_name"] == "server1"
        assert server["mcp_endpoint_url"] == "http://localhost:8080/mcp"
        assert server["rest_health_endpoint_url"] == "http://localhost:8080/health"
        assert server["mcp_enabled"] is True
        assert server["rest_enabled"] is True
        assert server["mcp_timeout_seconds"] == 20
        assert server["rest_timeout_seconds"] == 15
        assert server["mcp_expected_tools"] == ["search", "recommend"]
    
    def test_backup_config(self):
        """Test configuration backup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_content = '{"test": "data"}'
            config_path.write_text(config_content)
            
            backup_path = ConfigMigrator.backup_config(config_path)
            
            assert backup_path.exists()
            assert backup_path.read_text() == config_content
            assert "backup" in backup_path.name
            assert backup_path.suffix == ".json"


class TestConfigFileWatcher:
    """Test configuration file watcher for hot-reloading."""
    
    def test_file_watcher_creation(self):
        """Test file watcher creation."""
        mock_loader = Mock()
        watcher = ConfigFileWatcher(mock_loader)
        
        assert watcher.config_loader == mock_loader
        assert watcher.last_reload_time == 0
        assert watcher.reload_debounce_seconds == 1.0
    
    @patch('time.time')
    def test_on_modified_debounce(self, mock_time):
        """Test file modification event with debouncing."""
        mock_loader = Mock()
        mock_loader.config_file_path = "/test/config.json"
        mock_loader._trigger_reload = Mock()
        
        watcher = ConfigFileWatcher(mock_loader)
        
        # Mock file modification event
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/test/config.json"
        
        # First modification
        mock_time.return_value = 100.0
        watcher.on_modified(mock_event)
        
        assert watcher.last_reload_time == 100.0
        mock_loader._trigger_reload.assert_called_once()
        
        # Second modification within debounce period
        mock_loader._trigger_reload.reset_mock()
        mock_time.return_value = 100.5  # Within 1 second
        watcher.on_modified(mock_event)
        
        mock_loader._trigger_reload.assert_not_called()
        
        # Third modification after debounce period
        mock_time.return_value = 102.0  # After 1 second
        watcher.on_modified(mock_event)
        
        mock_loader._trigger_reload.assert_called_once()
    
    def test_on_modified_different_file(self):
        """Test file modification event for different file."""
        mock_loader = Mock()
        mock_loader.config_file_path = "/test/config.json"
        mock_loader._trigger_reload = Mock()
        
        watcher = ConfigFileWatcher(mock_loader)
        
        # Mock file modification event for different file
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = "/test/other.json"
        
        watcher.on_modified(mock_event)
        
        mock_loader._trigger_reload.assert_not_called()
    
    def test_on_modified_directory(self):
        """Test file modification event for directory."""
        mock_loader = Mock()
        mock_loader._trigger_reload = Mock()
        
        watcher = ConfigFileWatcher(mock_loader)
        
        # Mock directory modification event
        mock_event = Mock()
        mock_event.is_directory = True
        
        watcher.on_modified(mock_event)
        
        mock_loader._trigger_reload.assert_not_called()


class TestConfigLoader:
    """Test configuration loader functionality."""
    
    def test_config_loader_creation(self):
        """Test config loader creation."""
        config_path = "/test/config.json"
        loader = ConfigLoader(config_path)
        
        assert loader.config_file_path == Path(config_path)
        assert loader.config is None
        assert loader.reload_callbacks == []
        assert loader.hot_reload_enabled is False
        assert loader.file_observer is None
        assert loader.file_watcher is None
    
    def test_load_config_create_default(self):
        """Test loading config when file doesn't exist (creates default)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            loader = ConfigLoader(config_path)
            
            config = loader.load_config()
            
            assert config is not None
            assert config.system_name == "enhanced-mcp-status-check"
            assert config_path.exists()
            assert loader.config == config
    
    def test_load_config_existing_file(self):
        """Test loading existing configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create test config
            test_config = EnhancedStatusConfig.create_default()
            test_config.system_name = "test-system"
            test_config.save_to_file(config_path)
            
            loader = ConfigLoader(config_path)
            config = loader.load_config()
            
            assert config.system_name == "test-system"
            assert loader.config == config
    
    def test_load_config_yaml_file(self):
        """Test loading YAML configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            
            # Create YAML config
            yaml_content = """
            system_name: yaml-test-system
            version: 1.0.0
            dual_monitoring_enabled: true
            mcp_health_checks:
              enabled: true
            rest_health_checks:
              enabled: true
            servers: []
            """
            config_path.write_text(yaml_content)
            
            loader = ConfigLoader(config_path)
            config = loader.load_config()
            
            assert config.system_name == "yaml-test-system"
    
    def test_load_config_legacy_migration(self):
        """Test loading legacy configuration with automatic migration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create legacy config
            legacy_config = {
                "system": {"name": "legacy-system"},
                "mcp": {"enabled": True, "timeout": 10},
                "rest": {"enabled": True, "timeout": 8},
                "servers": []
            }
            config_path.write_text(json.dumps(legacy_config))
            
            loader = ConfigLoader(config_path)
            config = loader.load_config()
            
            assert config.system_name == "legacy-system"
            
            # Check that backup was created
            backup_files = list(config_path.parent.glob("*backup*"))
            assert len(backup_files) > 0
    
    def test_load_config_invalid_json(self):
        """Test loading invalid JSON configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text("{ invalid json }")
            
            loader = ConfigLoader(config_path)
            
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_config()
            
            assert "Invalid configuration file format" in str(exc_info.value)
    
    def test_load_config_validation_error(self):
        """Test loading configuration with validation errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create invalid config (missing system name)
            invalid_config = {
                "system_name": "",  # Invalid: empty system name
                "version": "1.0.0",
                "dual_monitoring_enabled": True,
                "mcp_health_checks": {"enabled": True},
                "rest_health_checks": {"enabled": True},
                "servers": []
            }
            config_path.write_text(json.dumps(invalid_config))
            
            loader = ConfigLoader(config_path)
            
            with pytest.raises(ConfigValidationError) as exc_info:
                loader.load_config()
            
            assert "Configuration validation failed" in str(exc_info.value)
            assert len(exc_info.value.errors) > 0
    
    def test_reload_config(self):
        """Test configuration reloading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create initial config
            initial_config = EnhancedStatusConfig.create_default()
            initial_config.system_name = "initial-system"
            initial_config.save_to_file(config_path)
            
            loader = ConfigLoader(config_path)
            config = loader.load_config()
            assert config.system_name == "initial-system"
            
            # Modify config file
            modified_config = EnhancedStatusConfig.create_default()
            modified_config.system_name = "modified-system"
            modified_config.save_to_file(config_path)
            
            # Reload config
            reloaded_config = loader.reload_config()
            assert reloaded_config.system_name == "modified-system"
            assert loader.config.system_name == "modified-system"
    
    def test_reload_config_unchanged(self):
        """Test reloading unchanged configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create config
            test_config = EnhancedStatusConfig.create_default()
            test_config.system_name = "unchanged-system"
            test_config.save_to_file(config_path)
            
            loader = ConfigLoader(config_path)
            config = loader.load_config()
            
            # Reload without changes
            reloaded_config = loader.reload_config()
            assert reloaded_config == config
    
    def test_reload_callbacks(self):
        """Test reload callbacks functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create config
            test_config = EnhancedStatusConfig.create_default()
            test_config.save_to_file(config_path)
            
            loader = ConfigLoader(config_path)
            loader.load_config()
            
            # Add callback
            callback_called = []
            def test_callback(config):
                callback_called.append(config.system_name)
            
            loader.add_reload_callback(test_callback)
            
            # Modify and reload
            modified_config = EnhancedStatusConfig.create_default()
            modified_config.system_name = "callback-test"
            modified_config.save_to_file(config_path)
            
            loader.reload_config()
            
            assert len(callback_called) == 1
            assert callback_called[0] == "callback-test"
            
            # Remove callback
            loader.remove_reload_callback(test_callback)
            
            # Modify and reload again
            modified_config.system_name = "callback-test-2"
            modified_config.save_to_file(config_path)
            
            loader.reload_config()
            
            # Callback should not be called again
            assert len(callback_called) == 1
    
    def test_save_config(self):
        """Test saving configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            loader = ConfigLoader(config_path)
            
            # Create and save config
            test_config = EnhancedStatusConfig.create_default()
            test_config.system_name = "saved-system"
            
            loader.save_config(test_config)
            
            assert config_path.exists()
            assert loader.config == test_config
            
            # Verify saved content
            loaded_config = EnhancedStatusConfig.load_from_file(config_path)
            assert loaded_config.system_name == "saved-system"
    
    def test_validate_config_file(self):
        """Test configuration file validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create valid config
            valid_config = EnhancedStatusConfig.create_default()
            valid_config.save_to_file(config_path)
            
            loader = ConfigLoader(config_path)
            errors = loader.validate_config_file()
            assert len(errors) == 0
            
            # Create invalid config
            invalid_config = {
                "system_name": "",  # Invalid
                "version": "1.0.0"
            }
            config_path.write_text(json.dumps(invalid_config))
            
            errors = loader.validate_config_file()
            assert len(errors) > 0
    
    def test_context_manager(self):
        """Test config loader as context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with ConfigLoader(config_path) as loader:
                config = loader.load_config()
                assert config is not None
                
                # Enable hot reload to test cleanup
                loader.enable_hot_reload()
                assert loader.hot_reload_enabled is True
            
            # Should be disabled after context exit
            assert loader.hot_reload_enabled is False


class TestUtilityFunctions:
    """Test utility functions for configuration management."""
    
    def test_load_config_from_file(self):
        """Test utility function to load config from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create test config
            test_config = EnhancedStatusConfig.create_default()
            test_config.system_name = "utility-test"
            test_config.save_to_file(config_path)
            
            loaded_config = load_config_from_file(config_path)
            assert loaded_config.system_name == "utility-test"
    
    def test_create_default_config_file(self):
        """Test utility function to create default config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "default_config.json"
            
            config = create_default_config_file(config_path)
            
            assert config_path.exists()
            assert config.system_name == "enhanced-mcp-status-check"
    
    def test_migrate_legacy_config_file(self):
        """Test utility function to migrate legacy config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_path = Path(temp_dir) / "legacy.json"
            enhanced_path = Path(temp_dir) / "enhanced.json"
            
            # Create legacy config
            legacy_config = {
                "system": {"name": "legacy-migration-test"},
                "mcp": {"enabled": True, "timeout": 10},
                "rest": {"enabled": True, "timeout": 8},
                "servers": []
            }
            legacy_path.write_text(json.dumps(legacy_config))
            
            migrated_config = migrate_legacy_config_file(legacy_path, enhanced_path)
            
            assert enhanced_path.exists()
            assert migrated_config.system_name == "legacy-migration-test"
            
            # Verify migrated file content
            loaded_config = EnhancedStatusConfig.load_from_file(enhanced_path)
            assert loaded_config.system_name == "legacy-migration-test"
    
    def test_migrate_nonexistent_legacy_file(self):
        """Test migrating non-existent legacy file."""
        with pytest.raises(ConfigurationError) as exc_info:
            migrate_legacy_config_file("/nonexistent/legacy.json", "/tmp/enhanced.json")
        
        assert "Legacy configuration file not found" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])