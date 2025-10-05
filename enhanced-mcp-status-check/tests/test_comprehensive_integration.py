"""
Comprehensive integration tests for enhanced MCP status check system.

This module contains end-to-end integration tests covering:
- Dual health check flow (MCP + REST)
- MCP tools/list request and response validation
- REST health check request and response handling
- Failure scenario tests (MCP fails, REST succeeds, etc.)
- Authentication integration tests for both protocols
- Performance tests for concurrent dual monitoring

Requirements covered: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 9.1, 9.2
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.mcp_health_check_client import MCPHealthCheckClient
from services.rest_health_check_client import RESTHealthCheckClient
from services.health_result_aggregator import HealthResultAggregator
from services.authentication_service import AuthenticationService


class TestComprehensiveIntegration:
    """Comprehensive integration tests for enhanced MCP status check system."""

    @pytest.fixture
    async def enhanced_service(self):
        """Create enhanced health check service for testing."""
        service = EnhancedHealthCheckService()
        await service.initialize()
        return service

    @pytest.fixture
    def sample_server_config(self):
        """Create sample server configuration for testing."""
        return EnhancedServerConfig(
            server_name="test-mcp-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=True,
            mcp_timeout_seconds=10,
            rest_timeout_seconds=8,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            jwt_token="test-jwt-token",
            auth_headers={"Authorization": "Bearer test-token"},
            mcp_priority_weight=0.6,
            rest_priority_weight=0.4,
            require_both_success=False
        )

    @pytest.fixture
    def auth_service(self):
        """Create authentication service for testing."""
        return AuthenticationService()

    async def test_end_to_end_dual_health_check_flow_success(self, enhanced_service, sample_server_config):
        """
        Test complete end-to-end dual health check flow with both MCP and REST succeeding.
        
        Requirements: 1.1, 2.1, 3.1
        """
        # Mock successful MCP response
        mock_mcp_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants",
                        "inputSchema": {"type": "object"}
                    },
                    {
                        "name": "recommend_restaurants", 
                        "description": "Recommend restaurants",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        }

        # Mock successful REST response
        mock_rest_response = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "server_metrics": {
                "uptime": 3600,
                "memory_usage": 0.5,
                "cpu_usage": 0.3
            },
            "circuit_breaker_states": {
                "mcp_tools": "CLOSED",
                "database": "CLOSED"
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP mock
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_mcp_response
            
            # Configure REST mock
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_rest_response

            # Execute dual health check
            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify result structure
            assert isinstance(result, DualHealthCheckResult)
            assert result.server_name == "test-mcp-server"
            assert result.overall_success is True
            assert result.overall_status == ServerStatus.HEALTHY

            # Verify MCP results
            assert result.mcp_success is True
            assert result.mcp_tools_count == 2
            assert result.mcp_response_time_ms > 0

            # Verify REST results
            assert result.rest_success is True
            assert result.rest_status_code == 200
            assert result.rest_response_time_ms > 0

            # Verify combined metrics
            assert result.health_score > 0.8
            assert "mcp" in result.available_paths
            assert "rest" in result.available_paths

    async def test_mcp_tools_list_request_validation(self, enhanced_service, sample_server_config):
        """
        Test MCP tools/list request generation and response validation.
        
        Requirements: 1.1, 1.2
        """
        # Mock MCP response with missing expected tool
        mock_mcp_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants",
                        "inputSchema": {"type": "object"}
                    }
                    # Missing "recommend_restaurants" tool
                ]
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = mock_mcp_response
            
            # Mock REST to succeed
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify MCP validation detected missing tool
            assert result.mcp_success is False
            assert "recommend_restaurants" in str(result.mcp_error_message)
            assert result.overall_status == ServerStatus.DEGRADED

    async def test_rest_health_check_request_response_handling(self, enhanced_service, sample_server_config):
        """
        Test REST health check request generation and response handling.
        
        Requirements: 2.1, 2.2
        """
        # Mock REST response with detailed health information
        mock_rest_response = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "server_metrics": {
                "uptime": 7200,
                "memory_usage": 0.7,
                "cpu_usage": 0.4,
                "active_connections": 15
            },
            "circuit_breaker_states": {
                "mcp_tools": "CLOSED",
                "database": "HALF_OPEN",
                "external_api": "OPEN"
            },
            "system_health": {
                "disk_usage": 0.6,
                "network_latency": 50
            }
        }

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock MCP to succeed
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            # Configure REST mock
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = mock_rest_response

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify REST response parsing
            assert result.rest_success is True
            assert result.rest_status_code == 200
            
            # Verify detailed REST data extraction
            rest_result = result.rest_result
            assert rest_result.server_metrics["uptime"] == 7200
            assert rest_result.circuit_breaker_states["database"] == "HALF_OPEN"
            assert rest_result.system_health["disk_usage"] == 0.6

    async def test_failure_scenario_mcp_fails_rest_succeeds(self, enhanced_service, sample_server_config):
        """
        Test failure scenario where MCP fails but REST succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP to fail
            mock_post.return_value.__aenter__.return_value.status = 500
            mock_post.return_value.__aenter__.return_value.json.side_effect = Exception("MCP server error")
            
            # Configure REST to succeed
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify failure handling
            assert result.mcp_success is False
            assert result.rest_success is True
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.overall_success is False
            
            # Verify available paths
            assert "rest" in result.available_paths
            assert "mcp" not in result.available_paths

    async def test_failure_scenario_rest_fails_mcp_succeeds(self, enhanced_service, sample_server_config):
        """
        Test failure scenario where REST fails but MCP succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP to succeed
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            # Configure REST to fail
            mock_get.return_value.__aenter__.return_value.status = 503
            mock_get.return_value.__aenter__.return_value.json.side_effect = Exception("REST endpoint unavailable")

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify failure handling
            assert result.mcp_success is True
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.overall_success is False
            
            # Verify available paths
            assert "mcp" in result.available_paths
            assert "rest" not in result.available_paths

    async def test_failure_scenario_both_fail(self, enhanced_service, sample_server_config):
        """
        Test failure scenario where both MCP and REST fail.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure both to fail
            mock_post.return_value.__aenter__.return_value.status = 500
            mock_post.return_value.__aenter__.return_value.json.side_effect = Exception("MCP server error")
            
            mock_get.return_value.__aenter__.return_value.status = 503
            mock_get.return_value.__aenter__.return_value.json.side_effect = Exception("REST endpoint unavailable")

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify complete failure handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert result.overall_success is False
            
            # Verify no available paths
            assert len(result.available_paths) == 0

    async def test_authentication_integration_mcp_jwt(self, enhanced_service, sample_server_config, auth_service):
        """
        Test JWT authentication integration for MCP requests.
        
        Requirements: 9.1, 9.2
        """
        # Mock JWT token validation
        with patch.object(auth_service, 'validate_jwt_token', return_value=True), \
             patch.object(auth_service, 'refresh_jwt_token', return_value="new-jwt-token"), \
             patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify authentication was handled
            assert result.mcp_success is True
            assert result.rest_success is True
            
            # Verify JWT token was included in MCP request
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert "Authorization" in call_kwargs.get("headers", {})

    async def test_authentication_integration_rest_bearer_token(self, enhanced_service, sample_server_config, auth_service):
        """
        Test Bearer token authentication integration for REST requests.
        
        Requirements: 9.1, 9.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify authentication was handled
            assert result.rest_success is True
            
            # Verify Bearer token was included in REST request
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert "Authorization" in call_kwargs.get("headers", {})
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"

    async def test_authentication_failure_scenarios(self, enhanced_service, sample_server_config):
        """
        Test authentication failure scenarios for both protocols.
        
        Requirements: 9.1, 9.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure authentication failures
            mock_post.return_value.__aenter__.return_value.status = 401
            mock_post.return_value.__aenter__.return_value.json.return_value = {"error": "Unauthorized"}
            
            mock_get.return_value.__aenter__.return_value.status = 401
            mock_get.return_value.__aenter__.return_value.json.return_value = {"error": "Invalid token"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify authentication failures are properly handled
            assert result.mcp_success is False
            assert result.rest_success is False
            assert "Unauthorized" in str(result.mcp_error_message) or "401" in str(result.mcp_error_message)
            assert "Invalid token" in str(result.rest_error_message) or "401" in str(result.rest_error_message)

    async def test_concurrent_dual_monitoring_performance(self, enhanced_service):
        """
        Test performance of concurrent dual monitoring across multiple servers.
        
        Requirements: 3.1, 3.2
        """
        # Create multiple server configurations
        server_configs = []
        for i in range(5):
            config = EnhancedServerConfig(
                server_name=f"test-server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health",
                mcp_enabled=True,
                rest_enabled=True
            )
            server_configs.append(config)

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            # Measure concurrent execution time
            start_time = time.time()
            results = await enhanced_service.check_multiple_servers_dual(server_configs)
            end_time = time.time()

            # Verify results
            assert len(results) == 5
            for result in results:
                assert result.mcp_success is True
                assert result.rest_success is True
                assert result.overall_success is True

            # Verify concurrent execution was faster than sequential
            execution_time = end_time - start_time
            assert execution_time < 2.0  # Should complete in under 2 seconds for 5 servers

    async def test_concurrent_monitoring_with_mixed_failures(self, enhanced_service):
        """
        Test concurrent monitoring with mixed success/failure scenarios.
        
        Requirements: 3.1, 3.2
        """
        # Create server configurations
        server_configs = []
        for i in range(3):
            config = EnhancedServerConfig(
                server_name=f"test-server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health",
                mcp_enabled=True,
                rest_enabled=True
            )
            server_configs.append(config)

        def mock_post_side_effect(*args, **kwargs):
            # First server succeeds, second fails, third succeeds
            url = kwargs.get('url', args[0] if args else '')
            if '8080' in url:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response
            elif '8081' in url:
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_response.json.side_effect = Exception("Server error")
                return mock_response
            else:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

        def mock_get_side_effect(*args, **kwargs):
            # All REST endpoints succeed
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            results = await enhanced_service.check_multiple_servers_dual(server_configs)

            # Verify mixed results
            assert len(results) == 3
            assert results[0].overall_success is True  # Both succeed
            assert results[1].overall_success is False  # MCP fails, REST succeeds -> DEGRADED
            assert results[2].overall_success is True  # Both succeed

            # Verify status distribution
            healthy_count = sum(1 for r in results if r.overall_status == ServerStatus.HEALTHY)
            degraded_count = sum(1 for r in results if r.overall_status == ServerStatus.DEGRADED)
            assert healthy_count == 2
            assert degraded_count == 1

    async def test_timeout_handling_integration(self, enhanced_service, sample_server_config):
        """
        Test timeout handling in dual health check integration.
        
        Requirements: 1.1, 2.1
        """
        # Set short timeouts for testing
        sample_server_config.mcp_timeout_seconds = 1
        sample_server_config.rest_timeout_seconds = 1

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure timeouts
            mock_post.return_value.__aenter__.side_effect = asyncio.TimeoutError("MCP timeout")
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError("REST timeout")

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify timeout handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert "timeout" in str(result.mcp_error_message).lower()
            assert "timeout" in str(result.rest_error_message).lower()

    async def test_retry_logic_integration(self, enhanced_service, sample_server_config):
        """
        Test retry logic integration for both MCP and REST requests.
        
        Requirements: 1.1, 2.1
        """
        # Configure retry attempts
        sample_server_config.mcp_retry_attempts = 2
        sample_server_config.rest_retry_attempts = 2

        call_count = {'mcp': 0, 'rest': 0}

        def mock_post_side_effect(*args, **kwargs):
            call_count['mcp'] += 1
            if call_count['mcp'] < 2:
                # First call fails
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_response.json.side_effect = Exception("Temporary error")
                return mock_response
            else:
                # Second call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
                }
                return mock_response

        def mock_get_side_effect(*args, **kwargs):
            call_count['rest'] += 1
            if call_count['rest'] < 2:
                # First call fails
                mock_response = AsyncMock()
                mock_response.status = 503
                mock_response.json.side_effect = Exception("Service unavailable")
                return mock_response
            else:
                # Second call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Verify retry logic worked
            assert result.mcp_success is True
            assert result.rest_success is True
            assert result.overall_success is True
            assert call_count['mcp'] == 2
            assert call_count['rest'] == 2

    async def test_data_serialization_integration(self, enhanced_service, sample_server_config):
        """
        Test data serialization and deserialization in integration flow.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            result = await enhanced_service.perform_dual_health_check(sample_server_config)

            # Test serialization to dictionary
            result_dict = result.to_dict()
            assert isinstance(result_dict, dict)
            assert result_dict["server_name"] == "test-mcp-server"
            assert result_dict["overall_success"] is True
            assert "mcp_result" in result_dict
            assert "rest_result" in result_dict

            # Test JSON serialization
            result_json = json.dumps(result_dict)
            assert isinstance(result_json, str)
            
            # Test deserialization
            deserialized = json.loads(result_json)
            assert deserialized["server_name"] == "test-mcp-server"
            assert deserialized["overall_success"] is True