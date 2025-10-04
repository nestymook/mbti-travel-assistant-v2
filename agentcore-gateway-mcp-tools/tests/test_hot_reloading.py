"""
Tests for configuration hot reloading functionality.

This module tests the hot reloading capabilities including:
- File system watching
- Automatic configuration reloading
- Configuration change notifications
- Integration with MCP client manager
"""

import pytest
import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from services.config_manager import (
    ConfigManager,
    ConfigurationChangeHandler,
    EnvironmentConfig,
    MCPServerConfig
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
            }
        }
    }


class TestHotReloading:
    """Test hot reloading functionality."""
    
    @pytest.mark.asyncio
    async def test_file_watching_initialization(self, temp_config_dir):
        """Test file watching initialization."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config_manager.current_config = EnvironmentConfig(name="test", enable_hot_reload=True)
        
        # Start file watching
        config_manager.start_file_watching()
        
        # Verify observers are created
        assert len(config_manager.observers) > 0
        
        # Stop file watching
        config_manager.stop_file_watching()
        assert len(config_manager.observers) == 0
    
    @pytest.mark.asyncio
    async def test_configuration_change_detection(self, temp_config_dir, sample_config):
        """Test detection of configuration file changes."""
        # Create initial configuration file
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Mock the reload method to track calls
        original_reload = config_manager.reload_configuration
        config_manager.reload_configuration = AsyncMock()
        
        # Create change handler
        handler = ConfigurationChangeHandler(config_manager)
        
        # Simulate file change event
        event = Mock()
        event.is_directory = False
        event.src_path = str(config_file)
        
        # Handle the change
        handler.on_modified(event)
        
        # Give some time for async task to be created
        await asyncio.sleep(0.1)
        
        # Verify reload was called
        config_manager.reload_configuration.assert_called_once()
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_configuration_change_debouncing(self, temp_config_dir, sample_config):
        """Test debouncing of rapid configuration changes."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config_manager.reload_configuration = AsyncMock()
        
        handler = ConfigurationChangeHandler(config_manager)
        
        # Create mock event
        event = Mock()
        event.is_directory = False
        event.src_path = str(config_file)
        
        # First change
        handler.on_modified(event)
        first_time = handler.last_modified.get(str(config_file))
        
        # Immediate second change (should be debounced)
        handler.on_modified(event)
        second_time = handler.last_modified.get(str(config_file))
        
        # Times should be the same (debounced)
        assert first_time == second_time
    
    @pytest.mark.asyncio
    async def test_configuration_change_callbacks(self, temp_config_dir, sample_config):
        """Test configuration change callbacks."""
        config_manager = ConfigManager(str(temp_config_dir), "test")
        
        # Track callback calls
        callback_calls = []
        
        def test_callback(config):
            callback_calls.append(config)
        
        async def async_test_callback(config):
            callback_calls.append(config)
        
        # Add callbacks
        config_manager.add_change_callback(test_callback)
        config_manager.add_change_callback(async_test_callback)
        
        # Create configuration
        config = EnvironmentConfig(**sample_config)
        
        # Notify callbacks
        await config_manager._notify_change_callbacks(config)
        
        # Verify callbacks were called
        assert len(callback_calls) == 2
        assert all(call == config for call in callback_calls)
        
        # Remove callbacks
        config_manager.remove_change_callback(test_callback)
        config_manager.remove_change_callback(async_test_callback)
        assert len(config_manager.change_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_configuration_reload_with_changes(self, temp_config_dir, sample_config):
        """Test configuration reload with actual changes."""
        # Create initial configuration file
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        initial_config = await config_manager.initialize()
        
        # Verify initial configuration
        assert initial_config.debug is True
        assert initial_config.mcp_servers["search"].timeout == 30
        
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
        assert updated_config.mcp_servers["search"].timeout == 60
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_mcp_server_configuration_changes(self, temp_config_dir, sample_config):
        """Test MCP server configuration changes."""
        # Create initial configuration file
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Verify initial servers
        initial_servers = config_manager.get_all_mcp_servers()
        assert len(initial_servers) == 1
        assert "search" in initial_servers
        
        # Add new server
        sample_config["mcp_servers"]["reasoning"] = {
            "name": "reasoning",
            "url": "http://localhost:8082",
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 1.0,
            "health_check_path": "/health",
            "enabled": True,
            "tools": ["recommend_restaurants"]
        }
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Reload configuration
        await config_manager.reload_configuration()
        
        # Verify new server was added
        updated_servers = config_manager.get_all_mcp_servers()
        assert len(updated_servers) == 2
        assert "search" in updated_servers
        assert "reasoning" in updated_servers
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_hot_reload_disabled(self, temp_config_dir, sample_config):
        """Test behavior when hot reload is disabled."""
        # Disable hot reload
        sample_config["enable_hot_reload"] = False
        
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        config = await config_manager.initialize()
        
        # Verify hot reload is disabled
        assert config.enable_hot_reload is False
        
        # Verify no file watchers are started
        assert len(config_manager.observers) == 0
    
    @pytest.mark.asyncio
    async def test_configuration_validation_on_reload(self, temp_config_dir, sample_config):
        """Test configuration validation during hot reload."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Create invalid configuration
        invalid_config = sample_config.copy()
        invalid_config["name"] = "invalid_environment"  # Invalid environment name
        
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        # Reload should handle validation errors gracefully
        try:
            await config_manager.reload_configuration()
            # Should use previous valid configuration
            current_config = config_manager.get_current_config()
            assert current_config.name == "test"  # Previous valid config
        except Exception as e:
            # Or raise appropriate error
            assert "validation" in str(e).lower()
        
        # Clean up
        config_manager.stop_file_watching()


class TestHotReloadingIntegration:
    """Integration tests for hot reloading with other components."""
    
    @pytest.mark.asyncio
    async def test_mcp_client_manager_integration(self, temp_config_dir, sample_config):
        """Test hot reloading integration with MCP client manager."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Mock MCP client manager callback
        mcp_callback_called = False
        received_config = None
        
        async def mcp_config_change_callback(config):
            nonlocal mcp_callback_called, received_config
            mcp_callback_called = True
            received_config = config
        
        # Register callback (simulating MCP client manager registration)
        config_manager.add_change_callback(mcp_config_change_callback)
        
        # Modify configuration
        sample_config["mcp_servers"]["search"]["timeout"] = 120
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Reload configuration
        await config_manager.reload_configuration()
        
        # Verify callback was called
        assert mcp_callback_called is True
        assert received_config is not None
        assert received_config.mcp_servers["search"].timeout == 120
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_multiple_file_changes(self, temp_config_dir, sample_config):
        """Test handling multiple file changes in sequence."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Track configuration changes
        config_changes = []
        
        def track_changes(config):
            config_changes.append(config.debug)
        
        config_manager.add_change_callback(track_changes)
        
        # Make multiple changes
        for debug_value in [False, True, False]:
            sample_config["debug"] = debug_value
            with open(config_file, 'w') as f:
                json.dump(sample_config, f)
            
            await config_manager.reload_configuration()
            await asyncio.sleep(0.1)  # Small delay between changes
        
        # Verify all changes were tracked
        assert len(config_changes) == 3
        assert config_changes == [False, True, False]
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_concurrent_configuration_access(self, temp_config_dir, sample_config):
        """Test concurrent access to configuration during reload."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Simulate concurrent access during reload
        async def access_config():
            for _ in range(10):
                config = config_manager.get_current_config()
                assert config is not None
                await asyncio.sleep(0.01)
        
        async def reload_config():
            for i in range(5):
                sample_config["debug"] = i % 2 == 0
                with open(config_file, 'w') as f:
                    json.dump(sample_config, f)
                await config_manager.reload_configuration()
                await asyncio.sleep(0.02)
        
        # Run concurrent tasks
        await asyncio.gather(
            access_config(),
            reload_config(),
            access_config()
        )
        
        # Verify final state
        final_config = config_manager.get_current_config()
        assert final_config is not None
        
        # Clean up
        config_manager.stop_file_watching()


@pytest.mark.slow
class TestHotReloadingPerformance:
    """Performance tests for hot reloading."""
    
    @pytest.mark.asyncio
    async def test_reload_performance(self, temp_config_dir, sample_config):
        """Test configuration reload performance."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Measure reload time
        start_time = time.time()
        
        for _ in range(10):
            await config_manager.reload_configuration()
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        # Should reload quickly (less than 100ms per reload)
        assert avg_time < 0.1, f"Average reload time too slow: {avg_time:.3f}s"
        
        # Clean up
        config_manager.stop_file_watching()
    
    @pytest.mark.asyncio
    async def test_callback_performance(self, temp_config_dir, sample_config):
        """Test performance with many callbacks."""
        config_file = temp_config_dir / "test.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir), "test")
        await config_manager.initialize()
        
        # Add many callbacks
        callbacks = []
        for i in range(100):
            def callback(config, i=i):
                pass
            callbacks.append(callback)
            config_manager.add_change_callback(callback)
        
        # Measure callback notification time
        config = config_manager.get_current_config()
        start_time = time.time()
        
        await config_manager._notify_change_callbacks(config)
        
        end_time = time.time()
        callback_time = end_time - start_time
        
        # Should handle many callbacks quickly (less than 50ms)
        assert callback_time < 0.05, f"Callback notification too slow: {callback_time:.3f}s"
        
        # Clean up
        for callback in callbacks:
            config_manager.remove_change_callback(callback)
        config_manager.stop_file_watching()


if __name__ == "__main__":
    pytest.main([__file__])