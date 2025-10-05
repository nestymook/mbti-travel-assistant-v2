"""
REST Health Check Integration Tests.

Focused integration tests for REST health check request and response handling.
Tests the complete REST health check flow including HTTP request generation,
response validation, and error handling.

Requirements covered: 2.1, 2.2
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from models.dual_health_models import EnhancedServerConfig, RESTHealthCheckResult
from services.rest_health_check_client import RESTHealthCheckClient


class TestRESTHealthIntegration:
    """Integration tests for REST health check handling."""

    @pytest.fixture
    def rest_client(self):
        """Create REST health check client for testing."""
        return RESTHealthCheckClient()

    @pytest.fixture
    def server_config(self):
        """Create server configuration for REST testing."""
        return EnhancedServerConfig(
            server_name="rest-test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=False,
            rest_enabled=True,
            rest_timeout_seconds=10,
            rest_retry_attempts=3,
            auth_headers={"Authorization": "Bearer test-token", "X-API-Key": "api-key-123"}
        )

    async def test_rest_health_request_generation(self, rest_client, server_config):
        """
        Test REST health check HTTP request generation.
        
        Requirements: 2.1
        """
        mock_response_data = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "server_metrics": {"uptime": 3600}
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify request was made correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            
            # Verify URL
            assert call_args[0][0] == server_config.rest_health_endpoint_url
            
            # Verify headers
            call_kwargs = call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"
            assert call_kwargs["headers"]["X-API-Key"] == "api-key-123"
            
            # Verify timeout
            assert call_kwargs["timeout"] == server_config.rest_timeout_seconds

    async def test_rest_health_response_validation_success(self, rest_client, server_config):
        """
        Test successful REST health check response validation.
        
        Requirements: 2.1, 2.2
        """
        # Mock comprehensive health response
        mock_response_data = {
            "status": "healthy",
            "timestamp": "2025-01-01T12:00:00Z",
            "server_metrics": {
                "uptime": 7200,
                "memory_usage": 0.65,
                "cpu_usage": 0.45,
                "active_connections": 25,
                "requests_per_minute": 150,
                "error_rate": 0.02
            },
            "circuit_breaker_states": {
                "mcp_tools": "CLOSED",
                "database": "CLOSED",
                "external_api": "HALF_OPEN",
                "cache": "CLOSED"
            },
            "system_health": {
                "disk_usage": 0.70,
                "network_latency": 45,
                "database_connections": 8,
                "cache_hit_rate": 0.85
            },
            "version": "1.2.3",
            "environment": "production"
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify response structure
            assert result.status_code == 200
            assert result.response_body == mock_response_data
            assert result.success is True

            # Verify response validation
            validation_result = rest_client.validate_rest_response(result)
            assert validation_result.is_valid is True
            assert validation_result.status == "healthy"
            assert validation_result.server_metrics["uptime"] == 7200
            assert validation_result.circuit_breaker_states["external_api"] == "HALF_OPEN"
            assert validation_result.system_health["cache_hit_rate"] == 0.85

    async def test_rest_health_response_validation_degraded(self, rest_client, server_config):
        """
        Test REST health check response validation for degraded status.
        
        Requirements: 2.2
        """
        # Mock degraded health response
        mock_response_data = {
            "status": "degraded",
            "timestamp": "2025-01-01T12:00:00Z",
            "server_metrics": {
                "uptime": 7200,
                "memory_usage": 0.85,  # High memory usage
                "cpu_usage": 0.75,     # High CPU usage
                "active_connections": 95,
                "requests_per_minute": 50,  # Low throughput
                "error_rate": 0.15          # High error rate
            },
            "circuit_breaker_states": {
                "mcp_tools": "CLOSED",
                "database": "HALF_OPEN",    # Database issues
                "external_api": "OPEN",     # External API down
                "cache": "CLOSED"
            },
            "system_health": {
                "disk_usage": 0.90,         # High disk usage
                "network_latency": 200,     # High latency
                "database_connections": 2,  # Low connections
                "cache_hit_rate": 0.45      # Low cache hit rate
            },
            "alerts": [
                "High memory usage detected",
                "External API circuit breaker open",
                "Database connection issues"
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify degraded status handling
            validation_result = rest_client.validate_rest_response(result)
            assert validation_result.is_valid is True
            assert validation_result.status == "degraded"
            assert len(validation_result.alerts) == 3
            assert "High memory usage detected" in validation_result.alerts

    async def test_rest_health_response_validation_unhealthy(self, rest_client, server_config):
        """
        Test REST health check response validation for unhealthy status.
        
        Requirements: 2.2
        """
        # Mock unhealthy health response
        mock_response_data = {
            "status": "unhealthy",
            "timestamp": "2025-01-01T12:00:00Z",
            "server_metrics": {
                "uptime": 300,              # Recently restarted
                "memory_usage": 0.95,       # Critical memory usage
                "cpu_usage": 0.90,          # Critical CPU usage
                "active_connections": 0,    # No connections
                "requests_per_minute": 0,   # No throughput
                "error_rate": 1.0           # All requests failing
            },
            "circuit_breaker_states": {
                "mcp_tools": "OPEN",        # All circuit breakers open
                "database": "OPEN",
                "external_api": "OPEN",
                "cache": "OPEN"
            },
            "system_health": {
                "disk_usage": 0.98,         # Critical disk usage
                "network_latency": 5000,    # Extreme latency
                "database_connections": 0,  # No database connections
                "cache_hit_rate": 0.0       # Cache not working
            },
            "errors": [
                "Database connection failed",
                "Cache service unavailable",
                "MCP tools not responding",
                "Critical resource exhaustion"
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 503
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify unhealthy status handling
            assert result.status_code == 503
            validation_result = rest_client.validate_rest_response(result)
            assert validation_result.status == "unhealthy"
            assert len(validation_result.errors) == 4
            assert "Database connection failed" in validation_result.errors

    async def test_rest_health_http_status_code_handling(self, rest_client, server_config):
        """
        Test handling of various HTTP status codes in REST health checks.
        
        Requirements: 2.1, 2.2
        """
        status_code_scenarios = [
            (200, True, "healthy"),
            (201, True, "healthy"),
            (202, True, "healthy"),
            (400, False, "unhealthy"),
            (401, False, "unhealthy"),
            (403, False, "unhealthy"),
            (404, False, "unhealthy"),
            (429, False, "degraded"),
            (500, False, "unhealthy"),
            (502, False, "unhealthy"),
            (503, False, "unhealthy"),
            (504, False, "unhealthy")
        ]

        for status_code, expected_success, expected_status in status_code_scenarios:
            mock_response_data = {
                "status": expected_status,
                "timestamp": "2025-01-01T12:00:00Z",
                "message": f"HTTP {status_code} response"
            }

            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value.status = status_code
                mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

                result = await rest_client.send_health_request(
                    server_config.rest_health_endpoint_url,
                    server_config.auth_headers,
                    server_config.rest_timeout_seconds
                )

                # Verify status code handling
                assert result.status_code == status_code
                assert result.success == expected_success

    async def test_rest_health_authentication_headers(self, rest_client, server_config):
        """
        Test that authentication headers are properly included in REST requests.
        
        Requirements: 2.1
        """
        mock_response_data = {"status": "healthy"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

            await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify authentication headers were included
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"
            assert call_kwargs["headers"]["X-API-Key"] == "api-key-123"

    async def test_rest_health_retry_logic_with_exponential_backoff(self, rest_client, server_config):
        """
        Test REST health check retry logic with exponential backoff.
        
        Requirements: 2.1
        """
        call_count = 0
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # First two calls fail
                mock_response = AsyncMock()
                mock_response.status = 503
                mock_response.json.return_value = {"status": "unhealthy", "error": "Service unavailable"}
                return mock_response
            else:
                # Third call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

        with patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect), \
             patch('asyncio.sleep') as mock_sleep:  # Mock sleep to speed up test

            result = await rest_client.perform_rest_health_check_with_retry(
                server_config
            )

            # Verify retry logic worked
            assert call_count == 3
            assert result.success is True
            assert result.status_code == 200
            
            # Verify exponential backoff was used
            assert mock_sleep.call_count == 2  # Two retries, so two sleeps
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] < sleep_calls[1]  # Exponential backoff

    async def test_rest_health_timeout_handling(self, rest_client, server_config):
        """
        Test REST health check timeout handling.
        
        Requirements: 2.1
        """
        import asyncio

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError("Request timeout")

            try:
                await rest_client.send_health_request(
                    server_config.rest_health_endpoint_url,
                    server_config.auth_headers,
                    1  # 1 second timeout
                )
                assert False, "Expected TimeoutError"
            except asyncio.TimeoutError:
                pass  # Expected

    async def test_rest_health_connection_error_handling(self, rest_client, server_config):
        """
        Test REST health check connection error handling.
        
        Requirements: 2.1
        """
        import aiohttp

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.side_effect = aiohttp.ClientConnectorError(
                connection_key=None, os_error=None
            )

            try:
                await rest_client.send_health_request(
                    server_config.rest_health_endpoint_url,
                    server_config.auth_headers,
                    server_config.rest_timeout_seconds
                )
                assert False, "Expected ClientConnectorError"
            except aiohttp.ClientConnectorError:
                pass  # Expected

    async def test_rest_health_invalid_json_response(self, rest_client, server_config):
        """
        Test handling of invalid JSON responses from REST health endpoint.
        
        Requirements: 2.2
        """
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.side_effect = json.JSONDecodeError(
                "Invalid JSON", "response", 0
            )

            try:
                await rest_client.send_health_request(
                    server_config.rest_health_endpoint_url,
                    server_config.auth_headers,
                    server_config.rest_timeout_seconds
                )
                assert False, "Expected JSONDecodeError"
            except json.JSONDecodeError:
                pass  # Expected

    async def test_rest_health_custom_endpoint_paths(self, rest_client):
        """
        Test REST health checks with custom endpoint paths.
        
        Requirements: 2.1
        """
        custom_endpoints = [
            "http://localhost:8080/health",
            "http://localhost:8080/api/v1/health",
            "http://localhost:8080/status",
            "http://localhost:8080/ping",
            "http://localhost:8080/healthcheck"
        ]

        mock_response_data = {"status": "healthy"}

        for endpoint in custom_endpoints:
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value.status = 200
                mock_get.return_value.__aenter__.return_value.json.return_value = mock_response_data

                result = await rest_client.send_health_request(
                    endpoint,
                    {},
                    10
                )

                # Verify request was made to correct endpoint
                mock_get.assert_called_once()
                assert mock_get.call_args[0][0] == endpoint
                assert result.success is True

    async def test_rest_health_response_time_measurement(self, rest_client, server_config):
        """
        Test that REST health check response times are accurately measured.
        
        Requirements: 2.2
        """
        import time

        # Mock a delay in the response
        async def mock_delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            return mock_response

        with patch('aiohttp.ClientSession.get', side_effect=mock_delayed_response):
            start_time = time.time()
            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )
            end_time = time.time()

            # Verify response time measurement
            actual_duration = (end_time - start_time) * 1000  # Convert to milliseconds
            assert result.response_time_ms >= 100  # At least 100ms due to sleep
            assert abs(result.response_time_ms - actual_duration) < 50  # Within 50ms tolerance

    async def test_rest_health_large_response_handling(self, rest_client, server_config):
        """
        Test handling of large REST health check responses.
        
        Requirements: 2.2
        """
        # Create a large response with many metrics
        large_response_data = {
            "status": "healthy",
            "timestamp": "2025-01-01T12:00:00Z",
            "server_metrics": {f"metric_{i}": i * 0.1 for i in range(1000)},
            "detailed_stats": {f"stat_{i}": f"value_{i}" for i in range(500)},
            "historical_data": [
                {"timestamp": f"2025-01-01T{hour:02d}:00:00Z", "value": hour * 10}
                for hour in range(24)
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = large_response_data

            result = await rest_client.send_health_request(
                server_config.rest_health_endpoint_url,
                server_config.auth_headers,
                server_config.rest_timeout_seconds
            )

            # Verify large response handling
            assert result.success is True
            assert len(result.response_body["server_metrics"]) == 1000
            assert len(result.response_body["detailed_stats"]) == 500
            assert len(result.response_body["historical_data"]) == 24