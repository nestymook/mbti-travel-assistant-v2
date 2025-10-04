"""
Tests for configuration validation functionality.

This module tests the configuration validator including:
- Configuration structure validation
- MCP server configuration validation
- Server connectivity validation
- Environment-specific validation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from services.config_validator import (
    ConfigValidator,
    ConfigValidationError,
    validate_configuration_file,
    validate_all_environment_configs,
    get_config_validator
)
from services.config_manager import EnvironmentConfig, MCPServerConfig


@pytest.fixture
def valid_server_config():
    """Valid MCP server configuration."""
    return MCPServerConfig(
        name="test-server",
        url="http://localhost:8080",
        timeout=30,
        max_retries=3,
        retry_delay=1.0,
        health_check_path="/health",
        enabled=True,
        tools=["test_tool"]
    )


@pytest.fixture
def valid_environment_config(valid_server_config):
    """Valid environment configuration."""
    return EnvironmentConfig(
        name="development",
        log_level="INFO",
        debug=True,
        enable_hot_reload=True,
        mcp_servers={"test": valid_server_config}
    )


class TestConfigValidator:
    """Test configuration validator functionality."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = ConfigValidator()
        assert validator.validation_errors == []
        assert validator.validation_warnings == []
    
    def test_validate_mcp_server_config_valid(self, valid_server_config):
        """Test validation of valid MCP server configuration."""
        validator = ConfigValidator()
        is_valid, errors = validator.validate_mcp_server_config(valid_server_config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_mcp_server_config_invalid(self):
        """Test validation of invalid MCP server configuration."""
        validator = ConfigValidator()
        
        # Create invalid server config
        invalid_config = MCPServerConfig(
            name="",  # Empty name
            url="http://localhost:8080",
            timeout=-1,  # Invalid timeout
            max_retries=-1,  # Invalid retries
            retry_delay=-1,  # Invalid delay
            health_check_path="invalid",  # Invalid path
            tools=[]  # No tools
        )
        
        is_valid, errors = validator.validate_mcp_server_config(invalid_config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("name cannot be empty" in error for error in errors)
        assert any("Timeout must be positive" in error for error in errors)
        assert any("Max retries cannot be negative" in error for error in errors)
        assert any("Retry delay cannot be negative" in error for error in errors)
        assert any("Health check path must start with" in error for error in errors)
        assert any("must have at least one tool" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self, valid_environment_config):
        """Test validation of valid environment configuration."""
        validator = ConfigValidator()
        is_valid, errors, warnings = await validator.validate_configuration(valid_environment_config)
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_invalid(self):
        """Test validation of invalid environment configuration."""
        validator = ConfigValidator()
        
        # Create invalid configuration
        invalid_config = EnvironmentConfig(
            name="development",
            log_level="INVALID",  # Invalid log level
            mcp_servers={}  # No servers
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(invalid_config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid log level" in error for error in errors)
        assert any("No MCP servers configured" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_missing_required_servers(self):
        """Test validation when required servers are missing."""
        validator = ConfigValidator()
        
        # Configuration missing required servers
        config = EnvironmentConfig(
            name="development",
            mcp_servers={
                "other": MCPServerConfig(
                    name="other",
                    url="http://localhost:8080",
                    tools=["other_tool"]
                )
            }
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        assert is_valid is False
        assert any("Required MCP server 'search' not configured" in error for error in errors)
        assert any("Required MCP server 'reasoning' not configured" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_missing_required_tools(self):
        """Test validation when required tools are missing."""
        validator = ConfigValidator()
        
        # Configuration with servers but missing required tools
        config = EnvironmentConfig(
            name="development",
            mcp_servers={
                "search": MCPServerConfig(
                    name="search",
                    url="http://localhost:8080",
                    tools=["wrong_tool"]  # Missing required tools
                ),
                "reasoning": MCPServerConfig(
                    name="reasoning",
                    url="http://localhost:8081",
                    tools=["wrong_tool"]  # Missing required tools
                )
            }
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        assert is_valid is False
        # Should have errors for missing required tools
        required_tools = [
            'search_restaurants_by_district',
            'search_restaurants_by_meal_type',
            'search_restaurants_combined',
            'recommend_restaurants',
            'analyze_restaurant_sentiment'
        ]
        
        for tool in required_tools:
            assert any(f"Required tool '{tool}' not found" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_warnings(self):
        """Test configuration validation warnings."""
        validator = ConfigValidator()
        
        # Production configuration with debug enabled
        config = EnvironmentConfig(
            name="production",
            debug=True,  # Should warn in production
            enable_hot_reload=True,  # Should warn in production
            log_level="DEBUG",  # Should warn in production
            mcp_servers={
                "search": MCPServerConfig(
                    name="search",
                    url="http://localhost:8080",
                    tools=["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]
                ),
                "reasoning": MCPServerConfig(
                    name="reasoning",
                    url="http://localhost:8081",
                    tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
                )
            }
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        assert is_valid is True
        assert len(warnings) > 0
        assert any("Debug mode is enabled in production" in warning for warning in warnings)
        assert any("Hot reload is enabled in production" in warning for warning in warnings)
        assert any("Debug logging is enabled in production" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_duplicate_urls(self):
        """Test validation of duplicate server URLs."""
        validator = ConfigValidator()
        
        config = EnvironmentConfig(
            name="development",
            mcp_servers={
                "search": MCPServerConfig(
                    name="search",
                    url="http://localhost:8080",  # Same URL
                    tools=["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]
                ),
                "reasoning": MCPServerConfig(
                    name="reasoning",
                    url="http://localhost:8080",  # Same URL
                    tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
                )
            }
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        assert len(warnings) > 0
        assert any("have the same URL" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_overlapping_tools(self):
        """Test validation of overlapping tools."""
        validator = ConfigValidator()
        
        config = EnvironmentConfig(
            name="development",
            mcp_servers={
                "search": MCPServerConfig(
                    name="search",
                    url="http://localhost:8080",
                    tools=["search_restaurants_by_district", "shared_tool"]  # Shared tool
                ),
                "reasoning": MCPServerConfig(
                    name="reasoning",
                    url="http://localhost:8081",
                    tools=["recommend_restaurants", "shared_tool"]  # Shared tool
                )
            }
        )
        
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        assert len(warnings) > 0
        assert any("Tool 'shared_tool' is defined on both servers" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_validate_server_connectivity_success(self, valid_server_config):
        """Test successful server connectivity validation."""
        validator = ConfigValidator()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            is_reachable, error_msg = await validator.validate_server_connectivity(valid_server_config)
            
            assert is_reachable is True
            assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_validate_server_connectivity_failure(self, valid_server_config):
        """Test failed server connectivity validation."""
        validator = ConfigValidator()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            is_reachable, error_msg = await validator.validate_server_connectivity(valid_server_config)
            
            assert is_reachable is False
            assert "Health check returned status 500" in error_msg
    
    @pytest.mark.asyncio
    async def test_validate_server_connectivity_timeout(self, valid_server_config):
        """Test server connectivity timeout."""
        validator = ConfigValidator()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = asyncio.TimeoutError()
            
            is_reachable, error_msg = await validator.validate_server_connectivity(valid_server_config)
            
            assert is_reachable is False
            assert "Connection timeout" in error_msg
    
    @pytest.mark.asyncio
    async def test_validate_server_connectivity_disabled(self):
        """Test connectivity validation for disabled server."""
        validator = ConfigValidator()
        
        disabled_config = MCPServerConfig(
            name="disabled-server",
            url="http://localhost:8080",
            enabled=False,
            tools=["test_tool"]
        )
        
        is_reachable, error_msg = await validator.validate_server_connectivity(disabled_config)
        
        assert is_reachable is True  # Skip disabled servers
        assert error_msg is None


class TestConfigValidationFunctions:
    """Test standalone configuration validation functions."""
    
    @pytest.mark.asyncio
    async def test_validate_configuration_file_valid(self, tmp_path):
        """Test validation of valid configuration file."""
        config_data = {
            "name": "development",
            "mcp_servers": {
                "search": {
                    "name": "search",
                    "url": "http://localhost:8080",
                    "tools": ["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]
                },
                "reasoning": {
                    "name": "reasoning",
                    "url": "http://localhost:8081",
                    "tools": ["recommend_restaurants", "analyze_restaurant_sentiment"]
                }
            }
        }
        
        config_file = tmp_path / "test.json"
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        is_valid, errors, warnings = await validate_configuration_file(str(config_file))
        
        assert is_valid is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_file_not_found(self):
        """Test validation of non-existent configuration file."""
        is_valid, errors, warnings = await validate_configuration_file("nonexistent.json")
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Configuration file not found" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_configuration_file_invalid_json(self, tmp_path):
        """Test validation of invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        is_valid, errors, warnings = await validate_configuration_file(str(config_file))
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid JSON" in error for error in errors)
    
    @pytest.mark.asyncio
    @patch('services.config_validator.validate_configuration_file')
    async def test_validate_all_environment_configs(self, mock_validate_file):
        """Test validation of all environment configurations."""
        # Mock validation results for different environments
        mock_validate_file.side_effect = [
            (True, [], []),  # development
            (True, [], ["warning"]),  # staging
            (False, ["error"], []),  # production
            (True, [], [])  # test
        ]
        
        results = await validate_all_environment_configs()
        
        assert len(results) == 4
        assert "development" in results
        assert "staging" in results
        assert "production" in results
        assert "test" in results
        
        # Check specific results
        assert results["development"] == (True, [], [])
        assert results["staging"] == (True, [], ["warning"])
        assert results["production"] == (False, ["error"], [])
        assert results["test"] == (True, [], [])


class TestGlobalConfigValidator:
    """Test global configuration validator functions."""
    
    def test_get_config_validator_singleton(self):
        """Test configuration validator singleton behavior."""
        validator1 = get_config_validator()
        validator2 = get_config_validator()
        
        assert validator1 is validator2
        assert isinstance(validator1, ConfigValidator)


@pytest.mark.integration
class TestConfigValidatorIntegration:
    """Integration tests for configuration validator."""
    
    @pytest.mark.asyncio
    async def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Create a comprehensive configuration
        config = EnvironmentConfig(
            name="development",
            log_level="INFO",
            debug=True,
            enable_hot_reload=True,
            mcp_servers={
                "search": MCPServerConfig(
                    name="search",
                    url="http://localhost:8080",
                    timeout=30,
                    max_retries=3,
                    retry_delay=1.0,
                    health_check_path="/health",
                    enabled=True,
                    tools=["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]
                ),
                "reasoning": MCPServerConfig(
                    name="reasoning",
                    url="http://localhost:8081",
                    timeout=30,
                    max_retries=3,
                    retry_delay=1.0,
                    health_check_path="/health",
                    enabled=True,
                    tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
                )
            }
        )
        
        validator = ConfigValidator()
        
        # Validate configuration
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        # Should be valid
        assert is_valid is True
        assert len(errors) == 0
        
        # Test individual server validation
        for server_name, server_config in config.mcp_servers.items():
            server_valid, server_errors = validator.validate_mcp_server_config(server_config)
            assert server_valid is True
            assert len(server_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__])