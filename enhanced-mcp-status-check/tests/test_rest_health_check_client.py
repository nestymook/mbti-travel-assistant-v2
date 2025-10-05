"""
Unit tests for REST Health Check Client

This module contains comprehensive unit tests for the REST Health Check Client
functionality including HTTP request handling, response validation, retry logic,
and error handling scenarios.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError, ClientTimeout
from aiohttp.web_response import Response

from services.rest_health_check_client import RESTHealthCheckClient
from models.dual_health_models import (
    RESTHealthCheckResponse,
    RESTValidationResult,
    RESTHealthCheckResult,
    EnhancedServerConfig
)


class TestRESTHealthCheckClient:
    """Test cases for REST Health Check Client."""
    
    @pytest.fixture
    def client(self):
        """Create REST health check client for testing."""
        return RESTHealthCheckClient()
    
    @pytest.fixture
    def sample_server_config(self):
        """Create sample server configuration for testing."""
        return EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            rest_enabled=True,
            rest_timeout_seconds=5,
            rest_retry_attempts=2,
            jwt_token="test-token",
            auth_headers={"X-API-Key": "test-key"}
        )
    
    @pytest.fixture
    def healthy_response_body(self):
        """Sample healthy response body."""
        return {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "metrics": {
                "uptime": 3600,
                "memory_usage": 0.75,
                "cpu_usage": 0.25,
                "request_count": 1000,
                "error_count": 5
            },
            "circuit_breaker": {
                "state": "CLOSED",
                "failure_count": 0
            },
            "system": {
                "version": "1.0.0",
                "environment": "production"
            }
        }
    
    @pytest.mark.asyncio
    async def test_send_health_request_success(self, client, healthy_response_body):
        """Test successful health request."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value=json.dumps(healthy_response_body))
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context
        
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 0.1]):  # 100ms response time
            response = await client.send_health_request(
                health_endpoint_url="http://localhost:8080/status/health",
                auth_headers={"Authorization": "Bearer test-token"},
                timeout=10
            )
        
        assert response.status_code == 200
        assert response.body == healthy_response_body
        assert response.response_time_ms == 100.0
        assert response.url == "http://localhost:8080/status/health"
        assert response.headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_send_health_request_http_error(self, client):
        """Test health request with HTTP error."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"error": "Internal server error"}')
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context
        
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 0.05]):
            response = await client.send_health_request(
                health_endpoint_url="http://localhost:8080/status/health",
                timeout=10
            )
        
        assert response.status_code == 500
        assert response.body["error"] == "Internal server error"
        assert not response.is_success()
    
    @pytest.mark.asyncio
    async def test_send_health_request_invalid_json(self, client):
        """Test health request with invalid JSON response."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = AsyncMock(return_value="Not JSON content")
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context
        
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 0.05]):
            response = await client.send_health_request(
                health_endpoint_url="http://localhost:8080/status/health",
                timeout=10
            )
        
        assert response.status_code == 200
        assert response.body == {"raw_response": "Not JSON content"}
    
    def test_validate_rest_response_healthy(self, client, healthy_response_body):
        """Test validation of healthy REST response."""
        response = RESTHealthCheckResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=healthy_response_body,
            response_time_ms=100.0,
            url="http://localhost:8080/status/health"
        )
        
        validation_result = client.validate_rest_response(response)
        
        assert validation_result.is_valid
        assert validation_result.http_status_valid
        assert validation_result.response_format_valid
        assert validation_result.health_indicators_present
        assert len(validation_result.validation_errors) == 0
        assert validation_result.server_metrics == healthy_response_body["metrics"] 
   
    def test_validate_rest_response_unhealthy_status(self, client):
        """Test validation of unhealthy REST response."""
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
    
    def test_validate_rest_response_empty_body(self, client):
        """Test validation of response with empty body."""
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
    
    def test_validate_rest_response_no_health_indicators(self, client):
        """Test validation of response without health indicators."""
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
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_with_retry_success(self, client):
        """Test retry logic with eventual success."""
        mock_session = AsyncMock()
        
        # First attempt fails, second succeeds
        mock_response_1 = AsyncMock()
        mock_response_1.status = 500
        mock_response_1.headers = {}
        mock_response_1.text = AsyncMock(return_value='{"error": "temporary error"}')
        
        mock_response_2 = AsyncMock()
        mock_response_2.status = 200
        mock_response_2.headers = {}
        mock_response_2.text = AsyncMock(return_value='{"status": "healthy"}')
        
        # Create context managers for each response
        mock_context_1 = AsyncMock()
        mock_context_1.__aenter__ = AsyncMock(return_value=mock_response_1)
        mock_context_1.__aexit__ = AsyncMock(return_value=None)
        
        mock_context_2 = AsyncMock()
        mock_context_2.__aenter__ = AsyncMock(return_value=mock_response_2)
        mock_context_2.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get.side_effect = [mock_context_1, mock_context_2]
        client._session = mock_session
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # Mock sleep to speed up test
            with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 0.05, 0.1, 0.15]):
                response = await client.perform_rest_health_check_with_retry(
                    health_endpoint_url="http://localhost:8080/status/health",
                    max_retries=2,
                    backoff_factor=0.1
                )
        
        assert response.status_code == 200
        assert response.body["status"] == "healthy"
        assert mock_session.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_with_retry_all_fail(self, client):
        """Test retry logic when all attempts fail."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = ClientError("Connection failed")
        client._session = mock_session
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with patch('services.rest_health_check_client.logger'):  # Mock logger to avoid time.time issues
                with pytest.raises(ClientError):
                    await client.perform_rest_health_check_with_retry(
                        health_endpoint_url="http://localhost:8080/status/health",
                        max_retries=2,
                        backoff_factor=0.1
                    )
        
        assert mock_session.get.call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_success(self, client, sample_server_config, healthy_response_body):
        """Test complete REST health check success."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value=json.dumps(healthy_response_body))
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context
        
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 0.05, 0.1, 0.15]):
            with patch('services.rest_health_check_client.logger'):  # Mock logger
                result = await client.perform_rest_health_check(sample_server_config)
        
        assert result.success
        assert result.server_name == "test-server"
        assert result.status_code == 200
        assert result.response_body == healthy_response_body
        assert result.server_metrics == healthy_response_body["metrics"]
        assert result.circuit_breaker_states == healthy_response_body["circuit_breaker"]
        assert result.system_health == healthy_response_body["system"]
        assert result.http_error is None
        assert result.connection_error is None
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_disabled(self, client, sample_server_config):
        """Test REST health check when disabled."""
        sample_server_config.rest_enabled = False
        
        result = await client.perform_rest_health_check(sample_server_config)
        
        assert not result.success
        assert result.connection_error == "REST health checks disabled in configuration"
        assert result.response_time_ms == 0.0
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_no_url(self, client, sample_server_config):
        """Test REST health check with missing URL."""
        sample_server_config.rest_health_endpoint_url = ""
        
        result = await client.perform_rest_health_check(sample_server_config)
        
        assert not result.success
        assert result.connection_error == "REST health endpoint URL not configured"
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_timeout(self, client, sample_server_config):
        """Test REST health check timeout."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError()
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 5.0]):
            with patch('services.rest_health_check_client.logger'):  # Mock logger
                result = await client.perform_rest_health_check(sample_server_config)
        
        assert not result.success
        assert "Request timeout after 5 seconds" in result.connection_error
        assert result.response_time_ms == 5000.0
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_client_error(self, client, sample_server_config):
        """Test REST health check with client error."""
        mock_session = AsyncMock()
        mock_session.get.side_effect = ClientError("DNS resolution failed")
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', side_effect=[0.0, 1.0]):
            with patch('services.rest_health_check_client.logger'):  # Mock logger
                result = await client.perform_rest_health_check(sample_server_config)
        
        assert not result.success
        assert result.http_error is not None
        assert "HTTP client error: DNS resolution failed" in result.http_error
    
    @pytest.mark.asyncio
    async def test_check_multiple_servers_rest(self, client):
        """Test concurrent REST health checks for multiple servers."""
        configs = [
            EnhancedServerConfig(
                server_name=f"server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health",
                rest_enabled=True
            )
            for i in range(3)
        ]
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{"status": "healthy"}')
        
        # Create a proper async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context
        
        client._session = mock_session
        
        with patch('services.rest_health_check_client.time.time', return_value=0.0):
            with patch('services.rest_health_check_client.logger'):  # Mock logger
                results = await client.check_multiple_servers_rest(configs, max_concurrent=2)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.server_name == f"server-{i}"
            assert result.success
    
    def test_extract_health_metrics(self, client):
        """Test health metrics extraction."""
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
    
    def test_determine_health_status_healthy(self, client):
        """Test health status determination for healthy response."""
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
    
    def test_determine_health_status_degraded(self, client):
        """Test health status determination for degraded response."""
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
    
    def test_determine_health_status_unhealthy(self, client):
        """Test health status determination for unhealthy response."""
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
    async def test_context_manager_usage(self):
        """Test proper context manager usage."""
        async with RESTHealthCheckClient() as client:
            assert client._session is not None
            assert client._owned_session is True
        
        # Session should be closed after context exit
        # Note: In real usage, the session would be closed, but in tests we can't easily verify this
    
    @pytest.mark.asyncio
    async def test_session_not_initialized_error(self, client):
        """Test error when session is not initialized."""
        # Don't initialize session
        with pytest.raises(RuntimeError, match="Client session not initialized"):
            await client.send_health_request("http://localhost:8080/status/health")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])