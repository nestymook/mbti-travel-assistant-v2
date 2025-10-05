"""
Tests for Enhanced Status Configuration Classes

This module tests the configuration classes for the enhanced MCP status check system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from config.enhanced_status_config import (
    EnhancedStatusConfig,
    MCPHealthCheckConfig,
    RESTHealthCheckConfig,
    ResultAggregationConfig,
    CircuitBreakerConfig,
    MonitoringConfig,
    ConfigurationError,
    ConfigValidationError,
    ConfigFormat
)
from models.dual_health_models import EnhancedServerConfig


class TestMCPHealthCheckConfig:
    """Test MCP health check configuration."""
    
    def test_default_config(self):
        """Test default MCP configuration."""
        config = MCPHealthCheckConfig()
        
        assert config.enabled is True
        assert config.default_timeout_seconds == 10
        assert config.default_retry_attempts == 3
        assert config.tools_list_validation is True
        assert config.expected_tools_validation is True
        assert config.default_expected_tools == []
        assert config.jwt_auth_enabled is False
    
    def test_from_dict(self):
        """Test creating MCP config from dictionary."""
        data = {
            "enabled": False,
            "default_timeout_seconds": 15,
            "default_retry_attempts": 5,
            "jwt_auth_enabled": True,
            "jwt_discovery_url": "https://example.com/.well-known/openid-configuration"
        }
        
        config = MCPHealthCheckConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.default_timeout_seconds == 15
        assert config.default_retry_attempts == 5
        assert config.jwt_auth_enabled is True
        assert config.jwt_discovery_url == "https://example.com/.well-known/openid-configuration"
    
    def test_to_dict(self):
        """Test converting MCP config to dictionary."""
        config = MCPHealthCheckConfig(
            enabled=False,
            default_timeout_seconds=15,
            jwt_auth_enabled=True,
            jwt_discovery_url="https://example.com/.well-known/openid-configuration"
        )
        
        data = config.to_dict()
        
        assert data["enabled"] is False
        assert data["default_timeout_seconds"] == 15
        assert data["jwt_auth_enabled"] is True
        assert data["jwt_discovery_url"] == "https://example.com/.well-known/openid-configuration"
    
    def test_validation(self):
        """Test MCP config validation."""
        # Valid config
        config = MCPHealthCheckConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid timeout
        config.default_timeout_seconds = -1
        errors = config.validate()
        assert len(errors) > 0
        assert any("timeout must be positive" in error for error in errors)
        
        # Invalid retry attempts
        config.default_timeout_seconds = 10
        config.default_retry_attempts = -1
        errors = config.validate()
        assert len(errors) > 0
        assert any("retry attempts cannot be negative" in error for error in errors)
        
        # JWT auth without discovery URL
        config.default_retry_attempts = 3
        config.jwt_auth_enabled = True
        config.jwt_discovery_url = None
        errors = config.validate()
        assert len(errors) > 0
        assert any("JWT discovery URL is required" in error for error in errors)


class TestRESTHealthCheckConfig:
    """Test REST health check configuration."""
    
    def test_default_config(self):
        """Test default REST configuration."""
        config = RESTHealthCheckConfig()
        
        assert config.enabled is True
        assert config.default_timeout_seconds == 8
        assert config.default_retry_attempts == 2
        assert config.health_endpoint_path == "/status/health"
        assert config.metrics_endpoint_path == "/status/metrics"
        assert config.expected_status_codes == [200, 201, 202]
        assert config.auth_type == "none"
    
    def test_from_dict(self):
        """Test creating REST config from dictionary."""
        data = {
            "enabled": False,
            "default_timeout_seconds": 12,
            "health_endpoint_path": "/health",
            "auth_type": "bearer"
        }
        
        config = RESTHealthCheckConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.default_timeout_seconds == 12
        assert config.health_endpoint_path == "/health"
        assert config.auth_type == "bearer"
    
    def test_validation(self):
        """Test REST config validation."""
        # Valid config
        config = RESTHealthCheckConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid endpoint path
        config.health_endpoint_path = "health"  # Missing leading slash
        errors = config.validate()
        assert len(errors) > 0
        assert any("must start with '/'" in error for error in errors)
        
        # Invalid auth type
        config.health_endpoint_path = "/status/health"
        config.auth_type = "invalid"
        errors = config.validate()
        assert len(errors) > 0
        assert any("Invalid auth type" in error for error in errors)


class TestResultAggregationConfig:
    """Test result aggregation configuration."""
    
    def test_default_config(self):
        """Test default aggregation configuration."""
        config = ResultAggregationConfig()
        
        assert config.mcp_priority_weight == 0.6
        assert config.rest_priority_weight == 0.4
        assert config.require_both_success_for_healthy is False
        assert config.degraded_on_single_failure is True
        assert config.health_score_calculation == "weighted_average"
    
    def test_validation(self):
        """Test aggregation config validation."""
        # Valid config
        config = ResultAggregationConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid priority weights (don't sum to 1.0)
        config.mcp_priority_weight = 0.8
        config.rest_priority_weight = 0.5
        errors = config.validate()
        assert len(errors) > 0
        assert any("must sum to 1.0" in error for error in errors)
        
        # Invalid health score calculation
        config.mcp_priority_weight = 0.6
        config.rest_priority_weight = 0.4
        config.health_score_calculation = "invalid"
        errors = config.validate()
        assert len(errors) > 0
        assert any("Invalid health score calculation" in error for error in errors)
        
        # Invalid thresholds
        config.health_score_calculation = "weighted_average"
        config.failure_threshold = 0.8
        config.degraded_threshold = 0.6  # Should be higher than failure threshold
        errors = config.validate()
        assert len(errors) > 0
        assert any("Failure threshold must be less than degraded threshold" in error for error in errors)


class TestEnhancedStatusConfig:
    """Test main enhanced status configuration."""
    
    def test_default_config(self):
        """Test default enhanced configuration."""
        config = EnhancedStatusConfig.create_default()
        
        assert config.system_name == "enhanced-mcp-status-check"
        assert config.version == "1.0.0"
        assert config.dual_monitoring_enabled is True
        assert isinstance(config.mcp_health_checks, MCPHealthCheckConfig)
        assert isinstance(config.rest_health_checks, RESTHealthCheckConfig)
        assert isinstance(config.result_aggregation, ResultAggregationConfig)
        assert isinstance(config.circuit_breaker, CircuitBreakerConfig)
        assert isinstance(config.monitoring, MonitoringConfig)
        assert config.servers == []
    
    def test_from_dict(self):
        """Test creating enhanced config from dictionary."""
        data = {
            "system_name": "test-system",
            "version": "2.0.0",
            "dual_monitoring_enabled": False,
            "mcp_health_checks": {
                "enabled": False,
                "default_timeout_seconds": 15
            },
            "servers": [
                {
                    "server_name": "test-server",
                    "mcp_endpoint_url": "http://localhost:8080/mcp",
                    "rest_health_endpoint_url": "http://localhost:8080/health"
                }
            ]
        }
        
        config = EnhancedStatusConfig.from_dict(data)
        
        assert config.system_name == "test-system"
        assert config.version == "2.0.0"
        assert config.dual_monitoring_enabled is False
        assert config.mcp_health_checks.enabled is False
        assert config.mcp_health_checks.default_timeout_seconds == 15
        assert len(config.servers) == 1
        assert config.servers[0].server_name == "test-server"
    
    def test_to_dict(self):
        """Test converting enhanced config to dictionary."""
        config = EnhancedStatusConfig.create_default()
        config.system_name = "test-system"
        
        data = config.to_dict()
        
        assert data["system_name"] == "test-system"
        assert data["version"] == "1.0.0"
        assert data["dual_monitoring_enabled"] is True
        assert "mcp_health_checks" in data
        assert "rest_health_checks" in data
        assert "result_aggregation" in data
        assert "circuit_breaker" in data
        assert "monitoring" in data
        assert "servers" in data
    
    def test_validation(self):
        """Test enhanced config validation."""
        # Valid config
        config = EnhancedStatusConfig.create_default()
        errors = config.validate()
        assert len(errors) == 0
        
        # Missing system name
        config.system_name = ""
        errors = config.validate()
        assert len(errors) > 0
        assert any("System name is required" in error for error in errors)
        
        # No monitoring methods enabled
        config.system_name = "test"
        config.dual_monitoring_enabled = False
        config.mcp_health_checks.enabled = False
        config.rest_health_checks.enabled = False
        errors = config.validate()
        assert len(errors) > 0
        assert any("At least one monitoring method must be enabled" in error for error in errors)
    
    def test_server_management(self):
        """Test server configuration management."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        config.add_server(server)
        
        assert len(config.servers) == 1
        assert config.get_server_config("test-server") is not None
        
        # Add another server with same name (should replace)
        server2 = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8081/mcp",
            rest_health_endpoint_url="http://localhost:8081/health"
        )
        config.add_server(server2)
        
        assert len(config.servers) == 1
        assert config.get_server_config("test-server").mcp_endpoint_url == "http://localhost:8081/mcp"
        
        # Remove server
        removed = config.remove_server("test-server")
        assert removed is True
        assert len(config.servers) == 0
        assert config.get_server_config("test-server") is None
        
        # Remove non-existent server
        removed = config.remove_server("non-existent")
        assert removed is False
    
    def test_monitoring_methods(self):
        """Test monitoring methods detection."""
        config = EnhancedStatusConfig.create_default()
        
        # Both enabled
        assert config.is_dual_monitoring_enabled() is True
        methods = config.get_enabled_monitoring_methods()
        assert "mcp" in methods
        assert "rest" in methods
        
        # Only MCP enabled
        config.rest_health_checks.enabled = False
        assert config.is_dual_monitoring_enabled() is False
        methods = config.get_enabled_monitoring_methods()
        assert "mcp" in methods
        assert "rest" not in methods
        
        # Only REST enabled
        config.mcp_health_checks.enabled = False
        config.rest_health_checks.enabled = True
        assert config.is_dual_monitoring_enabled() is False
        methods = config.get_enabled_monitoring_methods()
        assert "mcp" not in methods
        assert "rest" in methods
    
    def test_file_operations(self):
        """Test file save/load operations."""
        config = EnhancedStatusConfig.create_default()
        config.system_name = "test-file-ops"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON save/load
            json_path = Path(temp_dir) / "config.json"
            config.save_to_file(json_path)
            
            assert json_path.exists()
            assert config.config_format == ConfigFormat.JSON
            
            loaded_config = EnhancedStatusConfig.load_from_file(json_path)
            assert loaded_config.system_name == "test-file-ops"
            assert loaded_config.config_file_path == str(json_path)
            
            # Test YAML save/load
            yaml_path = Path(temp_dir) / "config.yaml"
            config.save_to_file(yaml_path)
            
            assert yaml_path.exists()
            assert config.config_format == ConfigFormat.YAML
            
            loaded_config = EnhancedStatusConfig.load_from_file(yaml_path)
            assert loaded_config.system_name == "test-file-ops"
    
    def test_json_yaml_conversion(self):
        """Test JSON and YAML conversion."""
        config = EnhancedStatusConfig.create_default()
        config.system_name = "test-conversion"
        
        # Test JSON conversion
        json_str = config.to_json()
        assert isinstance(json_str, str)
        json_data = json.loads(json_str)
        assert json_data["system_name"] == "test-conversion"
        
        # Test YAML conversion
        yaml_str = config.to_yaml()
        assert isinstance(yaml_str, str)
        assert "system_name: test-conversion" in yaml_str
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent configuration file."""
        with pytest.raises(ConfigurationError) as exc_info:
            EnhancedStatusConfig.load_from_file("/nonexistent/config.json")
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            f.flush()
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                EnhancedStatusConfig.load_from_file(temp_path)
            
            assert "Invalid configuration file format" in str(exc_info.value)
        finally:
            try:
                Path(temp_path).unlink()
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors on Windows


class TestConfigurationErrors:
    """Test configuration error handling."""
    
    def test_configuration_error(self):
        """Test basic configuration error."""
        error = ConfigurationError("Test error")
        assert str(error) == "Test error"
    
    def test_config_validation_error(self):
        """Test configuration validation error."""
        errors = ["Error 1", "Error 2"]
        error = ConfigValidationError("Validation failed", errors)
        
        assert str(error) == "Validation failed"
        assert error.errors == errors
        assert len(error.errors) == 2


if __name__ == "__main__":
    pytest.main([__file__])