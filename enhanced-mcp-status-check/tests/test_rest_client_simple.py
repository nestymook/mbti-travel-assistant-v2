"""
Simplified unit tests for REST Health Check Client

This module contains basic unit tests for the REST Health Check Client
to verify core functionality without complex mocking.
"""

import pytest
from datetime import datetime
from models.dual_health_models import (
    RESTHealthCheckResponse,
    RESTValidationResult,
    RESTHealthCheckResult,
    EnhancedServerConfig
)
from services.rest_health_check_client import RESTHealthCheckClient


class TestRESTHealthCheckClientSimple:
    """Simplified test cases for REST Health Check Client."""
    
    def test_validate_rest_response_healthy(self):
        """Test validation of healthy REST response."""
        client = RESTHealthCheckClient()
        
        healthy_body = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "metrics": {
                "uptime": 3600,
                "memory_usage": 0.75,
                "cpu_usage": 0.25
            }
        }
        
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=healthy_body,
            response_time_ms=100.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = client.validate_rest_response(response)
        
        assert validation_result.is_valid
        assert validation_result.http_status_valid
        assert validation_result.response_format_valid
        assert validation_result.health_indicators_present
        assert len(validation_result.validation_errors) == 0
        assert validation_result.server_metrics == healthy_body["metrics"]
    
    def test_validate_rest_response_unhealthy_status(self):
        """Test validation of unhealthy REST response."""
        client = RESTHealthCheckClient()
        
        unhealthy_body = {
            "status": "unhealthy",
            "error": "Database connection failed"
        }
        
        response = RESTHealthCheckResponse(
            status_code=503,
            headers={"Content-Type": "application/json"},
            body=unhealthy_body,
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = client.validate_rest_response(response)
        
        assert not validation_result.is_valid
        assert not validation_result.http_status_valid
        assert validation_result.response_format_valid
        assert validation_result.health_indicators_present
        assert "HTTP status 503 indicates failure" in validation_result.validation_errors
        assert "Response contains error indicator: error" in validation_result.validation_errors
    
    def test_validate_rest_response_empty_body(self):
        """Test validation of response with empty body."""
        client = RESTHealthCheckClient()
        
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=None,
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = client.validate_rest_response(response)
        
        assert not validation_result.is_valid
        assert validation_result.http_status_valid
        assert not validation_result.response_format_valid
        assert not validation_result.health_indicators_present
        assert "Empty response body" in validation_result.validation_errors
    
    def test_validate_rest_response_no_health_indicators(self):
        """Test validation of response without health indicators."""
        client = RESTHealthCheckClient()
        
        response_body = {
            "data": "some data",
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=response_body,
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = client.validate_rest_response(response)
        
        assert not validation_result.is_valid
        assert validation_result.http_status_valid
        assert validation_result.response_format_valid
        assert not validation_result.health_indicators_present
    
    def test_extract_health_metrics(self):
        """Test health metrics extraction."""
        client = RESTHealthCheckClient()
        
        response_body = {
            "uptime": 3600,
            "memory": 0.75,
            "cpu_usage": 0.25,
            "requests": 1000,
            "metrics": {
                "avg_response_time": 50.0,
                "active_connections": 10
            },
            "stats": {
                "cache_hit_rate": 0.95
            }
        }
        
        metrics = client.extract_health_metrics(response_body)
        
        assert metrics["uptime"] == 3600
        assert metrics["memory_usage"] == 0.75
        assert metrics["cpu_usage"] == 0.25
        assert metrics["request_count"] == 1000
        assert metrics["avg_response_time"] == 50.0
        assert metrics["active_connections"] == 10
        assert metrics["cache_hit_rate"] == 0.95
    
    def test_determine_health_status_healthy(self):
        """Test health status determination for healthy response."""
        client = RESTHealthCheckClient()
        
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={},
            body={"status": "healthy"},
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = RESTValidationResult(
            is_valid=True,
            http_status_valid=True,
            response_format_valid=True,
            health_indicators_present=True,
            validation_errors=[]
        )
        
        status = client.determine_health_status(response, validation_result)
        assert status == "HEALTHY"
    
    def test_determine_health_status_degraded(self):
        """Test health status determination for degraded response."""
        client = RESTHealthCheckClient()
        
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={},
            body={"status": "degraded"},
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = RESTValidationResult(
            is_valid=True,
            http_status_valid=True,
            response_format_valid=True,
            health_indicators_present=True,
            validation_errors=[]
        )
        
        status = client.determine_health_status(response, validation_result)
        assert status == "DEGRADED"
    
    def test_determine_health_status_unhealthy(self):
        """Test health status determination for unhealthy response."""
        client = RESTHealthCheckClient()
        
        response = RESTHealthCheckResponse(
            status_code=503,
            headers={},
            body={"status": "unhealthy"},
            response_time_ms=50.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = RESTValidationResult(
            is_valid=False,
            http_status_valid=False,
            response_format_valid=True,
            health_indicators_present=True,
            validation_errors=["HTTP status 503 indicates failure"]
        )
        
        status = client.determine_health_status(response, validation_result)
        assert status == "UNHEALTHY"
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_disabled(self):
        """Test REST health check when disabled."""
        client = RESTHealthCheckClient()
        
        server_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            rest_enabled=False
        )
        
        result = await client.perform_rest_health_check(server_config)
        
        assert not result.success
        assert result.connection_error == "REST health checks disabled in configuration"
        assert result.response_time_ms == 0.0
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_no_url(self):
        """Test REST health check with missing URL."""
        client = RESTHealthCheckClient()
        
        server_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="",
            rest_enabled=True
        )
        
        result = await client.perform_rest_health_check(server_config)
        
        assert not result.success
        assert result.connection_error == "REST health endpoint URL not configured"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])