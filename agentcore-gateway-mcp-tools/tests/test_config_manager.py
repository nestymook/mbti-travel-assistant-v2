"""
Tests for configuration management functionality.

This module tests the configuration manager, including:
- Configuration loading from files
- Hot reloading capabilities
- Environment-specific configurations
- Configuration validation
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import time

from services.config_manager import (
    ConfigManager,
    EnvironmentConfig,
    MCPServerConfig,
    ConfigurationChangeHandler,
    initialize_config_manager,
    get_config_manager,
    shutdown_config_manager
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        yield config_dir


@pytest.fixture
def sample_config():
    """Sample configuration data."""
    return {
        "name": "test",
        "log_level": "DEBUG",
        "debug": True,
        "enable_hot_reload": True,
        "mcp_servers": {
            "search": {
                "name": "search",
                "url": "http://localhost:8081",
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
                "health_check_path": "/health",
                "enabled": True,
                "tools": ["search_restaurants_by_district"]
            },
            "reasoning": {
                "name": "reasoning",
                "url": "http://localhost:8082",
                "timeout": 30,
                "max_retries": 3,
                "retry_delay": 1.0,
                "health_check_path": "/health",
                "enabled": True,
                "tools": ["recommend_restaurants"]
            }
        }
    }


@pytest.fixture
def config_file(temp_config_dir, sample_config):
    """Create a sample configuration file."""
    config_file = temp_config_dir / "test.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f)
    return config_file


class TestMCPServerConfig:
    """Test MCP server configuration model."""
    
    def test_valid_config(self):
        """Test creating a valid MCP server configuration."""
        config = MCPServerConfig(
            name="test-server",
            url="http://localhost:8080",
            timeout=30,
            max_retries=3,
            retry_delay=1.0,
            tools=["test_tool"]
        )
        
        assert config.name == "test-server"
        assert config.url == "http://localhost:8080"
        assert config.timeout == 30
        assert config.enabled is True
        assert "test_tool" in config.tools
    
    def test_invalid_url(self):
        """Test validation of invalid URL."""
        with pytest.raises(ValueError, match="URL must start with http"):
            MCPServerConfig(
                name="test-server",
                url="invalid-url",
                tools=["test_tool"]
            )
    
    def test_invalid_timeout(self):
        """Test validation of invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            MCPServerConfig(
                name="test-server",
                url="http://localhost:8080",
                timeout=0,
                tools=["test_tool"]
            )


class TestEnvironmentConfig:
    """Test environment configuration model."""
    
    def test_valid_config(self, sample_config):
        """Test creating a valid environment configuration."""
        config = EnvironmentConfig(**sample_config)
        
        assert config.name == "test"
        assert config.debug is True
        assert config.enable_hot_reload is True
        assert len(config.mcp_servers) == 2
        assert "search" in config.mcp_servers
        assert "reasoning" in config.mcp_servers
    
    def test_invalid_environment_name(self, sample_config):
        """Test validation of invalid environment name."""
        sample_config["name"] = "invalid"
        
        with pytest.raises(ValueError, match="Environment must be one of"):
            EnvironmentConfig(**sample_config)
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EnvironmentConfig(name="development")
        
        assert config.log_level == "INFO"
        assert config.debug is False
        assert config.enable_hot_reload is True
        assert len(config.mcp_servers) == 0


class TestConfigManager:
    """Test configuration manager functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, temp_config_dir):
        """Test configuration manager initialization."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config = await config_manager.initialize()
        
        assert config is not None
        assert config.name == "test"
        assert config_manager.get_current_config() == config
    
    @pytest.mark.asyncio
    async def test_load_configuration_from_file(self, temp_config_dir, config_file, sample_config):
        """Test loading configuration from file."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config = await config_manager.load_configuration()
        
        assert config.name == "test"
        assert config.debug is True
        assert len(config.mcp_servers) == 2
    
    @pytest.mark.asyncio
    async def test_load_configuration_fallback(self, temp_config_dir):
        """Test fallback configuration when no file exists."""
        config_manager = ConfigManager(str(temp_config_dir), "development")
        config = await config_manager.load_configuration()
        
        assert config.name == "development"
        assert len(config.mcp_servers) >= 2  # Default servers from settings
    
    @pytest.mark.asyncio
    async def test_reload_configuration(self, temp_config_dir, config_file, sample_config):
        """Test configuration reloading."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Modify configuration file
        sample_config["debug"] = False
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Reload configuration
        await config_manager.reload_configuration()
        
        config = config_manager.get_current_config()
        assert config.debug is False
    
    def test_get_mcp_server_config(self, temp_config_dir, sample_config):
        """Test getting specific MCP server configuration."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config_manager.current_config = EnvironmentConfig(**sample_config)
        
        search_config = config_manager.get_mcp_server_config("search")
        assert search_config is not None
        assert search_config.name == "search"
        assert search_config.url == "http://localhost:8081"
        
        # Test non-existent server
        missing_config = config_manager.get_mcp_server_config("missing")
        assert missing_config is None
    
    def test_get_all_mcp_servers(self, temp_config_dir, sample_config):
        """Test getting all MCP server configurations."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config_manager.current_config = EnvironmentConfig(**sample_config)
        
        servers = config_manager.get_all_mcp_servers()
        assert len(servers) == 2
        assert "search" in servers
        assert "reasoning" in servers
    
    def test_change_callbacks(self, temp_config_dir, sample_config):
        """Test configuration change callbacks."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        
        callback_called = False
        received_config = None
        
        def test_callback(config):
            nonlocal callback_called, received_config
            callback_called = True
            received_config = config
        
        config_manager.add_change_callback(test_callback)
        
        # Simulate configuration change
        new_config = EnvironmentConfig(**sample_config)
        config_manager.current_config = new_config
        
        # This would normally be called by load_configuration
        # We'll call it directly for testing
        asyncio.create_task(config_manager._notify_change_callbacks(new_config))
        
        # Remove callback
        config_manager.remove_change_callback(test_callback)
        assert test_callback not in config_manager.change_callbacks
    
    @pytest.mark.asyncio
    async def test_file_watching(self, temp_config_dir):
        """Test file watching functionality."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config_manager.current_config = EnvironmentConfig(name="test")
        
        # Start file watching
        config_manager.start_file_watching()
        assert len(config_manager.observers) > 0
        
        # Stop file watching
        config_manager.stop_file_watching()
        assert len(config_manager.observers) == 0


class TestConfigurationChangeHandler:
    """Test configuration change handler."""
    
    def test_is_config_file(self):
        """Test configuration file detection."""
        config_manager = Mock()
        handler = ConfigurationChangeHandler(config_manager)
        
        assert handler._is_config_file("config.json") is True
        assert handler._is_config_file("config.yaml") is True
        assert handler._is_config_file("config.yml") is True
        assert handler._is_config_file(".env") is True
        assert handler._is_config_file("other.txt") is False
    
    @patch('asyncio.create_task')
    def test_on_modified(self, mock_create_task):
        """Test file modification handling."""
        config_manager = Mock()
        handler = ConfigurationChangeHandler(config_manager)
        
        # Create mock event
        event = Mock()
        event.is_directory = False
        event.src_path = "config/test.json"
        
        # Handle modification
        handler.on_modified(event)
        
        # Should create task for reload
        mock_create_task.assert_called_once()
    
    def test_debounce_rapid_changes(self):
        """Test debouncing of rapid file changes."""
        config_manager = Mock()
        handler = ConfigurationChangeHandler(config_manager)
        
        # Create mock event
        event = Mock()
        event.is_directory = False
        event.src_path = "config/test.json"
        
        # First modification
        handler.on_modified(event)
        first_time = handler.last_modified.get(event.src_path)
        
        # Immediate second modification (should be debounced)
        handler.on_modified(event)
        second_time = handler.last_modified.get(event.src_path)
        
        # Times should be the same (debounced)
        assert first_time == second_time


class TestGlobalConfigManager:
    """Test global configuration manager functions."""
    
    @pytest.mark.asyncio
    async def test_initialize_config_manager(self):
        """Test global configuration manager initialization."""
        # Clean up any existing instance
        shutdown_config_manager()
        
        config = await initialize_config_manager("development")
        assert config is not None
        assert config.name == "development"
        
        # Get the same instance
        manager = get_config_manager()
        assert manager is not None
        assert manager.get_current_config() == config
        
        # Clean up
        shutdown_config_manager()
    
    def test_get_config_manager_singleton(self):
        """Test configuration manager singleton behavior."""
        # Clean up any existing instance
        shutdown_config_manager()
        
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
        
        # Clean up
        shutdown_config_manager()


@pytest.mark.integration
class TestConfigManagerIntegration:
    """Integration tests for configuration manager."""
    
    @pytest.mark.asyncio
    async def test_full_configuration_lifecycle(self, temp_config_dir, sample_config):
        """Test complete configuration lifecycle."""
        # Create configuration file
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Initialize configuration manager
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config = await config_manager.initialize()
        
        # Verify initial configuration
        assert config.name == "test"
        assert config.debug is True
        assert len(config.mcp_servers) == 2
        
        # Test server configuration access
        search_config = config_manager.get_mcp_server_config("search")
        assert search_config.url == "http://localhost:8081"
        
        # Modify configuration
        sample_config["debug"] = False
        sample_config["mcp_servers"]["search"]["timeout"] = 60
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Reload configuration
        await config_manager.reload_configuration()
        
        # Verify changes
        updated_config = config_manager.get_current_config()
        assert updated_config.debug is False
        
        updated_search_config = config_manager.get_mcp_server_config("search")
        assert updated_search_config.timeout == 60
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_configuration_validation_integration(self, temp_config_dir):
        """Test configuration validation integration."""
        # Create invalid configuration
        invalid_config = {
            "name": "invalid_env",  # Invalid environment name
            "mcp_servers": {
                "invalid_server": {
                    "name": "invalid",
                    "url": "invalid-url",  # Invalid URL
                    "timeout": -1,  # Invalid timeout
                    "tools": []  # No tools
                }
            }
        }
        
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        # Try to load invalid configuration
        config_manager = ConfigManager(str(temp_config_dir), "test")
        
        with pytest.raises(Exception):  # Should fail validation
            await config_manager.load_configuration()


if __name__ == "__main__":
    pytest.main([__file__])