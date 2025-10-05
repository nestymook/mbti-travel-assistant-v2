"""
Test suite for enhanced MCP status check data models.

This module tests all data models for dual health checking including
serialization, validation, and data integrity.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    MCPToolsListRequest,
    MCPToolsListResponse,
    MCPValidationResult,
    RESTHealthCheckResponse,
    RESTValidationResult,
    AggregationConfig,
    PriorityConfig,
    CombinedHealthMetrics,
    ServerStatus,
    EnhancedCircuitBreakerState
)
from models.validation_utils import (
    ConfigurationValidator,
    HealthCheckValidator,
    AggregationValidator,
    validate_configuration_data,
    validate_health_check_data
)


class TestMCPToolsListRequest:
    """Test MCP tools/list request model."""
    
    def test_create_default_request(self):
        """Test creating a default MCP tools/list request."""
        request = MCPToolsListRequest()
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id is not None
        assert request.params is None
    
    def test_create_custom_request(self):
        """Test creating a custom MCP tools/list request."""
        request = MCPToolsListRequest(
            id="test-123",
            params={"filter": "restaurant"}
        )
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id == "test-123"
        assert request.params == {"filter": "restaurant"}
    
    def test_serialization(self):
        """Test request serialization."""
        request = MCPToolsListRequest(id="test-123")
        data = request.to_dict()
        
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "tools/list"
        assert data["id"] == "test-123"
        assert "params" not in data
    
    def test_deserialization(self):
        """Test request deserialization."""
        data = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "test-123",
            "params": {"filter": "test"}
        }
        
        request = MCPToolsListRequest.from_dict(data)
        
        assert request.jsonrpc == "2.0"
        assert request.method == "tools/list"
        assert request.id == "test-123"
        assert request.params == {"filter": "test"}
    
    def test_validation_success(self):
        """Test successful request validation."""
        request = MCPToolsListRequest()
        errors = request.validate()
        
        assert len(errors) == 0
    
    def test_validation_errors(self):
        """Test request validation errors."""
        request = MCPToolsListRequest(
            jsonrpc="1.0",
            method="invalid",
            id=""
        )
        errors = request.validate()
        
        assert len(errors) == 3
        assert any("JSON-RPC version" in error for error in errors)
        assert any("method" in error for error in errors)
        assert any("Request ID" in error for error in errors)


class TestMCPToolsListResponse:
    """Test MCP tools/list response model."""
    
    def test_create_success_response(self):
        """Test creating a successful response."""
        response = MCPToolsListResponse(
            jsonrpc="2.0",
            id="test-123",
            result={
                "tools": [
                    {"name": "search_restaurants", "description": "Search for restaurants"}
                ]
            }
        )
        
        assert response.is_success()
        assert len(response.get_tools()) == 1
        assert response.get_tools()[0]["name"] == "search_restaurants"
    
    def test_create_error_response(self):
        """Test creating an error response."""
        response = MCPToolsListResponse(
            jsonrpc="2.0",
            id="test-123",
            error={"code": -32601, "message": "Method not found"}
        )
        
        assert not response.is_success()
        assert len(response.get_tools()) == 0
    
    def test_serialization(self):
        """Test response serialization."""
        response = MCPToolsListResponse(
            jsonrpc="2.0",
            id="test-123",
            result={"tools": []}
        )
        data = response.to_dict()
        
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-123"
        assert data["result"] == {"tools": []}
        assert "error" not in data


class TestEnhancedServerConfig:
    """Test enhanced server configuration model."""
    
    def test_create_minimal_config(self):
        """Test creating minimal server configuration."""
        config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080",
            rest_health_endpoint_url="http://localhost:8080/health"
        )
        
        assert config.server_name == "test-server"
        assert config.mcp_enabled is True
        assert config.rest_enabled is True
        assert config.mcp_timeout_seconds == 10
        assert config.rest_timeout_seconds == 8
    
    def test_create_full_config(self):
        """Test creating full server configuration."""
        config = EnhancedServerConfig(
            server_name="restaurant-server",
            mcp_endpoint_url="https://api.example.com/mcp",
            mcp_enabled=True,
            mcp_timeout_seconds=15,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            mcp_retry_attempts=5,
            rest_health_endpoint_url="https://api.example.com/health",
            rest_enabled=True,
            rest_timeout_seconds=10,
            rest_retry_attempts=3,
            jwt_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token",
            auth_headers={"X-API-Key": "test-key"},
            mcp_priority_weight=0.7,
            rest_priority_weight=0.3,
            require_both_success=True
        )
        
        assert config.server_name == "restaurant-server"
        assert len(config.mcp_expected_tools) == 2
        assert config.mcp_priority_weight == 0.7
        assert config.rest_priority_weight == 0.3
        assert config.require_both_success is True
    
    def test_serialization_deserialization(self):
        """Test config serialization and deserialization."""
        original_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_expected_tools=["tool1", "tool2"]
        )
        
        # Serialize
        data = original_config.to_dict()
        
        # Deserialize
        restored_config = EnhancedServerConfig.from_dict(data)
        
        assert restored_config.server_name == original_config.server_name
        assert restored_config.mcp_endpoint_url == original_config.mcp_endpoint_url
        assert restored_config.mcp_expected_tools == original_config.mcp_expected_tools
    
    def test_validation_success(self):
        """Test successful config validation."""
        config = EnhancedServerConfig(
            server_name="valid-server",
            mcp_endpoint_url="https://api.example.com/mcp",
            rest_health_endpoint_url="https://api.example.com/health"
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validation_errors(self):
        """Test config validation errors."""
        config = EnhancedServerConfig(
            server_name="",  # Invalid: empty name
            mcp_endpoint_url="",  # Invalid: empty URL when MCP enabled
            rest_health_endpoint_url="",  # Invalid: empty URL when REST enabled
            mcp_timeout_seconds=-1,  # Invalid: negative timeout
            mcp_priority_weight=1.5,  # Invalid: weight > 1.0
            rest_priority_weight=-0.5  # Invalid: negative weight
        )
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("Server name" in error for error in errors)
        assert any("MCP endpoint URL" in error for error in errors)
        assert any("REST health endpoint URL" in error for error in errors)


class TestDualHealthCheckResult:
    """Test dual health check result model."""
    
    def test_create_successful_result(self):
        """Test creating a successful dual health check result."""
        now = datetime.now()
        
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=now,
            success=True,
            response_time_ms=150.0,
            tools_count=3
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=now,
            success=True,
            response_time_ms=100.0,
            status_code=200
        )
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=now,
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=mcp_result,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            mcp_tools_count=3,
            rest_result=rest_result,
            rest_success=True,
            rest_response_time_ms=100.0,
            rest_status_code=200,
            combined_response_time_ms=125.0,
            health_score=1.0,
            available_paths=["both"]
        )
        
        assert dual_result.overall_status == ServerStatus.HEALTHY
        assert dual_result.overall_success is True
        assert dual_result.mcp_success is True
        assert dual_result.rest_success is True
        assert dual_result.health_score == 1.0
    
    def test_create_degraded_result(self):
        """Test creating a degraded health check result."""
        now = datetime.now()
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=now,
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_success=True,
            mcp_response_time_ms=150.0,
            rest_success=False,
            rest_error_message="Connection timeout",
            combined_response_time_ms=150.0,
            health_score=0.6,
            available_paths=["mcp"]
        )
        
        assert dual_result.overall_status == ServerStatus.DEGRADED
        assert dual_result.overall_success is False
        assert dual_result.mcp_success is True
        assert dual_result.rest_success is False
        assert dual_result.health_score == 0.6
        assert dual_result.available_paths == ["mcp"]
    
    def test_serialization_deserialization(self):
        """Test dual result serialization and deserialization."""
        now = datetime.now()
        
        original_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=now,
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            health_score=0.95,
            available_paths=["both"]
        )
        
        # Serialize
        data = original_result.to_dict()
        
        # Deserialize
        restored_result = DualHealthCheckResult.from_dict(data)
        
        assert restored_result.server_name == original_result.server_name
        assert restored_result.overall_status == original_result.overall_status
        assert restored_result.overall_success == original_result.overall_success
        assert restored_result.health_score == original_result.health_score
        assert restored_result.available_paths == original_result.available_paths


class TestPriorityConfig:
    """Test priority configuration model."""
    
    def test_create_default_config(self):
        """Test creating default priority configuration."""
        config = PriorityConfig()
        
        assert config.mcp_priority_weight == 0.6
        assert config.rest_priority_weight == 0.4
        assert config.require_both_success_for_healthy is False
        assert config.degraded_on_single_failure is True
    
    def test_create_custom_config(self):
        """Test creating custom priority configuration."""
        config = PriorityConfig(
            mcp_priority_weight=0.8,
            rest_priority_weight=0.2,
            require_both_success_for_healthy=True,
            degraded_on_single_failure=False
        )
        
        assert config.mcp_priority_weight == 0.8
        assert config.rest_priority_weight == 0.2
        assert config.require_both_success_for_healthy is True
        assert config.degraded_on_single_failure is False
    
    def test_validation_success(self):
        """Test successful priority config validation."""
        config = PriorityConfig(
            mcp_priority_weight=0.7,
            rest_priority_weight=0.3
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validation_errors(self):
        """Test priority config validation errors."""
        config = PriorityConfig(
            mcp_priority_weight=1.5,  # Invalid: > 1.0
            rest_priority_weight=-0.5  # Invalid: < 0.0
        )
        
        errors = config.validate()
        assert len(errors) >= 2
        assert any("MCP priority weight" in error for error in errors)
        assert any("REST priority weight" in error for error in errors)


class TestAggregationConfig:
    """Test aggregation configuration model."""
    
    def test_create_default_config(self):
        """Test creating default aggregation configuration."""
        priority_config = PriorityConfig()
        config = AggregationConfig(priority_config=priority_config)
        
        assert config.health_score_calculation == "weighted_average"
        assert config.failure_threshold == 0.5
        assert config.degraded_threshold == 0.7
    
    def test_validation_success(self):
        """Test successful aggregation config validation."""
        priority_config = PriorityConfig()
        config = AggregationConfig(
            priority_config=priority_config,
            health_score_calculation="weighted_average",
            failure_threshold=0.3,
            degraded_threshold=0.7
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validation_errors(self):
        """Test aggregation config validation errors."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.6,
            rest_priority_weight=0.6  # Invalid: sum > 1.0
        )
        config = AggregationConfig(
            priority_config=priority_config,
            health_score_calculation="invalid_method",  # Invalid method
            failure_threshold=1.5,  # Invalid: > 1.0
            degraded_threshold=0.3  # Invalid: < failure_threshold
        )
        
        errors = config.validate()
        assert len(errors) > 0


class TestValidationUtils:
    """Test validation utility functions."""
    
    def test_validate_url_success(self):
        """Test successful URL validation."""
        valid_urls = [
            "https://api.example.com",
            "http://localhost:8080",
            "https://api.example.com:443/health"
        ]
        
        for url in valid_urls:
            errors = ConfigurationValidator.validate_url(url)
            assert len(errors) == 0, f"URL {url} should be valid"
    
    def test_validate_url_errors(self):
        """Test URL validation errors."""
        invalid_urls = [
            "",  # Empty URL
            "not-a-url",  # No scheme
            "ftp://example.com",  # Invalid scheme
            "https://",  # No hostname
            "https://example.com:99999"  # Invalid port
        ]
        
        for url in invalid_urls:
            errors = ConfigurationValidator.validate_url(url)
            assert len(errors) > 0, f"URL {url} should be invalid"
    
    def test_validate_server_name_success(self):
        """Test successful server name validation."""
        valid_names = [
            "test-server",
            "restaurant_api",
            "server123",
            "my-test-server-01"
        ]
        
        for name in valid_names:
            errors = ConfigurationValidator.validate_server_name(name)
            assert len(errors) == 0, f"Server name {name} should be valid"
    
    def test_validate_server_name_errors(self):
        """Test server name validation errors."""
        invalid_names = [
            "",  # Empty
            "ab",  # Too short
            "a" * 65,  # Too long
            "-server",  # Starts with hyphen
            "server-",  # Ends with hyphen
            "server with spaces",  # Contains spaces
            "server@domain"  # Contains invalid characters
        ]
        
        for name in invalid_names:
            errors = ConfigurationValidator.validate_server_name(name)
            assert len(errors) > 0, f"Server name {name} should be invalid"
    
    def test_validate_configuration_data(self):
        """Test comprehensive configuration data validation."""
        valid_config_data = {
            "server_name": "test-server",
            "mcp_endpoint_url": "https://api.example.com/mcp",
            "rest_health_endpoint_url": "https://api.example.com/health",
            "mcp_enabled": True,
            "rest_enabled": True,
            "mcp_timeout_seconds": 10,
            "rest_timeout_seconds": 8,
            "mcp_expected_tools": ["search_restaurants"],
            "auth_headers": {"Authorization": "Bearer token123"}
        }
        
        errors = validate_configuration_data(valid_config_data)
        assert len(errors) == 0
    
    def test_validate_health_check_data(self):
        """Test health check data validation."""
        valid_health_data = {
            "server_name": "test-server",
            "health_score": 0.85,
            "available_paths": ["both"]
        }
        
        errors = validate_health_check_data(valid_health_data)
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])