"""
Tests for Configuration Validator

This module tests the configuration validation functionality with custom rules
and comprehensive error reporting.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from config.config_validator import (
    ConfigValidator,
    ValidationResult,
    ValidationRule,
    URLValidationRule,
    TimeoutValidationRule,
    MonitoringIntervalValidationRule,
    ServerConfigValidationRule,
    SecurityValidationRule,
    PerformanceValidationRule,
    validate_config_file,
    create_custom_validation_rule,
    validate_server_connectivity
)
from config.enhanced_status_config import EnhancedStatusConfig
from models.dual_health_models import EnhancedServerConfig


class TestValidationResult:
    """Test validation result functionality."""
    
    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(True, [], [], [])
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.info == []
    
    def test_add_error(self):
        """Test adding validation error."""
        result = ValidationResult(True, [], [], [])
        
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
        assert len(result.errors) == 1
    
    def test_add_warning(self):
        """Test adding validation warning."""
        result = ValidationResult(True, [], [], [])
        
        result.add_warning("Test warning")
        
        assert result.is_valid is True  # Warnings don't affect validity
        assert "Test warning" in result.warnings
        assert len(result.warnings) == 1
    
    def test_add_info(self):
        """Test adding validation info."""
        result = ValidationResult(True, [], [], [])
        
        result.add_info("Test info")
        
        assert result.is_valid is True
        assert "Test info" in result.info
        assert len(result.info) == 1
    
    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(True, [], [], [])
        result1.add_warning("Warning 1")
        result1.add_info("Info 1")
        
        result2 = ValidationResult(False, ["Error 1"], ["Warning 2"], ["Info 2"])
        
        result1.merge(result2)
        
        assert result1.is_valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 2
        assert len(result1.info) == 2
        assert "Error 1" in result1.errors
        assert "Warning 1" in result1.warnings
        assert "Warning 2" in result1.warnings
    
    def test_to_dict(self):
        """Test converting validation result to dictionary."""
        result = ValidationResult(False, ["Error 1"], ["Warning 1"], ["Info 1"])
        
        data = result.to_dict()
        
        assert data["is_valid"] is False
        assert data["errors"] == ["Error 1"]
        assert data["warnings"] == ["Warning 1"]
        assert data["info"] == ["Info 1"]
        assert data["error_count"] == 1
        assert data["warning_count"] == 1
        assert data["info_count"] == 1


class TestURLValidationRule:
    """Test URL validation rule."""
    
    def test_valid_urls(self):
        """Test validation of valid URLs."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with valid URLs
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="https://example.com/health"
        )
        config.add_server(server)
        
        rule = URLValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_invalid_urls(self):
        """Test validation of invalid URLs."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with invalid URLs
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="invalid-url",
            rest_health_endpoint_url="also-invalid"
        )
        config.add_server(server)
        
        rule = URLValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any("Invalid MCP endpoint URL" in error for error in result.errors)
        assert any("Invalid REST endpoint URL" in error for error in result.errors)
    
    def test_disabled_monitoring_methods(self):
        """Test validation when monitoring methods are disabled."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with disabled MCP and invalid URL
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="invalid-url",
            rest_health_endpoint_url="https://example.com/health",
            mcp_enabled=False,
            rest_enabled=True
        )
        config.add_server(server)
        
        rule = URLValidationRule()
        result = rule.validate(config)
        
        # Should not validate disabled MCP URL
        assert not any("Invalid MCP endpoint URL" in error for error in result.errors)


class TestTimeoutValidationRule:
    """Test timeout validation rule."""
    
    def test_reasonable_timeouts(self):
        """Test validation of reasonable timeout values."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.default_timeout_seconds = 10
        config.rest_health_checks.default_timeout_seconds = 8
        
        rule = TimeoutValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_very_high_timeouts(self):
        """Test validation of very high timeout values."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.default_timeout_seconds = 400  # > 5 minutes
        config.rest_health_checks.default_timeout_seconds = 350
        
        rule = TimeoutValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True  # Warnings don't affect validity
        assert len(result.warnings) >= 2
        assert any("very high" in warning for warning in result.warnings)
    
    def test_very_low_timeouts(self):
        """Test validation of very low timeout values."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.default_timeout_seconds = 0  # Too low
        config.rest_health_checks.default_timeout_seconds = -1  # Invalid
        
        rule = TimeoutValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any("too low" in error for error in result.errors)
    
    def test_server_specific_timeouts(self):
        """Test validation of server-specific timeout values."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with high timeouts
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_timeout_seconds=400,  # Very high
            rest_timeout_seconds=0    # Too low
        )
        config.add_server(server)
        
        rule = TimeoutValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1  # Low timeout error
        assert len(result.warnings) >= 1  # High timeout warning


class TestMonitoringIntervalValidationRule:
    """Test monitoring interval validation rule."""
    
    def test_reasonable_interval(self):
        """Test validation of reasonable monitoring interval."""
        config = EnhancedStatusConfig.create_default()
        config.monitoring.health_check_interval_seconds = 30
        
        rule = MonitoringIntervalValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_very_frequent_interval(self):
        """Test validation of very frequent monitoring interval."""
        config = EnhancedStatusConfig.create_default()
        config.monitoring.health_check_interval_seconds = 0.5  # Too frequent
        
        rule = MonitoringIntervalValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("too frequent" in error for error in result.errors)
    
    def test_very_infrequent_interval(self):
        """Test validation of very infrequent monitoring interval."""
        config = EnhancedStatusConfig.create_default()
        config.monitoring.health_check_interval_seconds = 7200  # 2 hours
        
        rule = MonitoringIntervalValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("very infrequent" in warning for warning in result.warnings)
    
    def test_interval_vs_timeout_comparison(self):
        """Test validation of interval compared to timeouts."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.default_timeout_seconds = 20
        config.rest_health_checks.default_timeout_seconds = 15
        config.monitoring.health_check_interval_seconds = 25  # Less than 2x max timeout
        
        rule = MonitoringIntervalValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("should be at least 2x" in warning for warning in result.warnings)


class TestServerConfigValidationRule:
    """Test server configuration validation rule."""
    
    def test_no_servers_configured(self):
        """Test validation when no servers are configured."""
        config = EnhancedStatusConfig.create_default()
        
        rule = ServerConfigValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("No servers configured" in warning for warning in result.warnings)
    
    def test_duplicate_server_names(self):
        """Test validation of duplicate server names."""
        config = EnhancedStatusConfig.create_default()
        
        # Add servers with duplicate names
        server1 = EnhancedServerConfig(
            server_name="duplicate-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        server2 = EnhancedServerConfig(
            server_name="duplicate-server",
            mcp_endpoint_url="http://localhost:8081/mcp",
            rest_health_endpoint_url="http://localhost:8081/health"
        )
        config.servers = [server1, server2]
        
        rule = ServerConfigValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("Duplicate server name" in error for error in result.errors)
    
    def test_no_monitoring_methods_enabled(self):
        """Test validation when no monitoring methods are enabled."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with both methods disabled
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_enabled=False,
            rest_enabled=False
        )
        config.add_server(server)
        
        rule = ServerConfigValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("At least one monitoring method must be enabled" in error for error in result.errors)
    
    def test_missing_urls_for_enabled_methods(self):
        """Test validation when URLs are missing for enabled methods."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with enabled methods but missing URLs
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="",  # Missing
            rest_health_endpoint_url="",  # Missing
            mcp_enabled=True,
            rest_enabled=True
        )
        config.add_server(server)
        
        rule = ServerConfigValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        assert any("MCP endpoint URL required" in error for error in result.errors)
        assert any("REST endpoint URL required" in error for error in result.errors)
    
    def test_invalid_priority_weights(self):
        """Test validation of invalid priority weights."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with invalid priority weights
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_priority_weight=0.8,
            rest_priority_weight=0.5  # Sum > 1.0
        )
        config.add_server(server)
        
        rule = ServerConfigValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("Priority weights must sum to 1.0" in error for error in result.errors)


class TestSecurityValidationRule:
    """Test security validation rule."""
    
    def test_jwt_auth_without_discovery_url(self):
        """Test validation of JWT auth without discovery URL."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.jwt_auth_enabled = True
        config.mcp_health_checks.jwt_discovery_url = None
        
        rule = SecurityValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        assert any("JWT discovery URL is required" in error for error in result.errors)
    
    def test_invalid_jwt_discovery_url_format(self):
        """Test validation of invalid JWT discovery URL format."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.jwt_auth_enabled = True
        config.mcp_health_checks.jwt_discovery_url = "https://example.com/invalid"
        
        rule = SecurityValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("should end with" in warning for warning in result.warnings)
    
    def test_insecure_http_urls(self):
        """Test validation of insecure HTTP URLs."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with HTTP URLs
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://example.com/mcp",  # Insecure
            rest_health_endpoint_url="http://example.com/health"  # Insecure
        )
        config.add_server(server)
        
        rule = SecurityValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 2
        assert any("insecure HTTP protocol" in warning for warning in result.warnings)
    
    def test_short_jwt_token(self):
        """Test validation of suspiciously short JWT token."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with short JWT token
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="https://example.com/mcp",
            rest_health_endpoint_url="https://example.com/health",
            jwt_token="short"  # Too short
        )
        config.add_server(server)
        
        rule = SecurityValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("appears to be too short" in warning for warning in result.warnings)


class TestPerformanceValidationRule:
    """Test performance validation rule."""
    
    def test_large_connection_pools(self):
        """Test validation of large connection pool sizes."""
        config = EnhancedStatusConfig.create_default()
        config.mcp_health_checks.connection_pool_size = 150  # Very large
        config.rest_health_checks.connection_pool_size = 120  # Very large
        
        rule = PerformanceValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 2
        assert any("very large" in warning for warning in result.warnings)
    
    def test_high_concurrent_checks(self):
        """Test validation of high concurrent checks configuration."""
        config = EnhancedStatusConfig.create_default()
        config.monitoring.concurrent_health_checks = True
        config.monitoring.max_concurrent_checks = 60  # Very high
        
        # Add only a few servers
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        config.add_server(server)
        
        rule = PerformanceValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 1
        assert any("much higher than server count" in warning or "very high" in warning 
                  for warning in result.warnings)
    
    def test_high_retry_attempts(self):
        """Test validation of high retry attempts."""
        config = EnhancedStatusConfig.create_default()
        
        # Add server with high retry attempts
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_retry_attempts=15,  # Very high
            rest_retry_attempts=12  # Very high
        )
        config.add_server(server)
        
        rule = PerformanceValidationRule()
        result = rule.validate(config)
        
        assert result.is_valid is True
        assert len(result.warnings) >= 2
        assert any("very high" in warning for warning in result.warnings)


class TestConfigValidator:
    """Test main configuration validator."""
    
    def test_validator_creation(self):
        """Test creating config validator with default rules."""
        validator = ConfigValidator()
        
        assert len(validator.rules) > 0
        rule_names = validator.get_rule_names()
        assert "url_validation" in rule_names
        assert "timeout_validation" in rule_names
        assert "server_config_validation" in rule_names
    
    def test_add_remove_rules(self):
        """Test adding and removing validation rules."""
        validator = ConfigValidator()
        initial_count = len(validator.rules)
        
        # Add custom rule
        custom_rule = Mock(spec=ValidationRule)
        custom_rule.name = "custom_rule"
        custom_rule.description = "Custom test rule"
        
        validator.add_rule(custom_rule)
        assert len(validator.rules) == initial_count + 1
        assert "custom_rule" in validator.get_rule_names()
        
        # Remove rule
        removed = validator.remove_rule("custom_rule")
        assert removed is True
        assert len(validator.rules) == initial_count
        assert "custom_rule" not in validator.get_rule_names()
        
        # Try to remove non-existent rule
        removed = validator.remove_rule("non_existent")
        assert removed is False
    
    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        config = EnhancedStatusConfig.create_default()
        
        # Add valid server
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        config.add_server(server)
        
        validator = ConfigValidator()
        result = validator.validate(config)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_config(self):
        """Test validating an invalid configuration."""
        config = EnhancedStatusConfig.create_default()
        config.system_name = ""  # Invalid
        
        # Add invalid server
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="invalid-url",
            rest_health_endpoint_url="also-invalid"
        )
        config.add_server(server)
        
        validator = ConfigValidator()
        result = validator.validate(config)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_and_raise(self):
        """Test validate_and_raise method."""
        config = EnhancedStatusConfig.create_default()
        config.system_name = ""  # Invalid
        
        validator = ConfigValidator()
        
        with pytest.raises(Exception):  # Should raise ConfigValidationError
            validator.validate_and_raise(config)
    
    def test_rule_descriptions(self):
        """Test getting rule descriptions."""
        validator = ConfigValidator()
        descriptions = validator.get_rule_descriptions()
        
        assert isinstance(descriptions, dict)
        assert len(descriptions) > 0
        assert "url_validation" in descriptions
        assert isinstance(descriptions["url_validation"], str)


class TestUtilityFunctions:
    """Test utility functions for validation."""
    
    def test_validate_config_file(self):
        """Test validating configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create valid config file
            config = EnhancedStatusConfig.create_default()
            config.save_to_file(config_path)
            
            result = validate_config_file(config_path)
            assert result.is_valid is True
    
    def test_validate_nonexistent_config_file(self):
        """Test validating non-existent configuration file."""
        result = validate_config_file("/nonexistent/config.json")
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Failed to load configuration" in error for error in result.errors)
    
    def test_create_custom_validation_rule(self):
        """Test creating custom validation rule."""
        def custom_validation(config):
            result = ValidationResult(True, [], [], [])
            if config.system_name == "invalid":
                result.add_error("Custom validation failed")
            return result
        
        rule = create_custom_validation_rule(
            "custom_test",
            "Custom test rule",
            custom_validation
        )
        
        assert rule.name == "custom_test"
        assert rule.description == "Custom test rule"
        
        # Test the rule
        config = EnhancedStatusConfig.create_default()
        config.system_name = "invalid"
        
        result = rule.validate(config)
        assert result.is_valid is False
        assert "Custom validation failed" in result.errors
    
    def test_validate_server_connectivity(self):
        """Test server connectivity validation."""
        # Valid server config
        server = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        
        result = validate_server_connectivity(server)
        assert result.is_valid is True
        assert len(result.info) >= 2  # Should have info about both endpoints
        
        # Invalid server config
        invalid_server = EnhancedServerConfig(
            server_name="invalid-server",
            mcp_endpoint_url="",
            rest_health_endpoint_url=""
        )
        
        result = validate_server_connectivity(invalid_server)
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Should have errors for missing URLs


if __name__ == "__main__":
    pytest.main([__file__])