"""
Failure Scenarios Integration Tests.

Comprehensive integration tests for various failure scenarios in dual health checking.
Tests combinations of MCP and REST failures, partial failures, and recovery scenarios.

Requirements covered: 3.1, 3.2
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, List

from models.dual_health_models import (
    DualHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus
)
from services.enhanced_health_check_service import EnhancedHealthCheckService


class TestFailureScenariosIntegration:
    """Integration tests for failure scenarios in dual health checking."""

    @pytest.fixture
    async def enhanced_service(self):
        """Create enhanced health check service for testing."""
        service = EnhancedHealthCheckService()
        await service.initialize()
        return service

    @pytest.fixture
    def server_config(self):
        """Create server configuration for testing."""
        return EnhancedServerConfig(
            server_name="failure-test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health",
            mcp_enabled=True,
            rest_enabled=True,
            mcp_timeout_seconds=5,
            rest_timeout_seconds=5,
            mcp_retry_attempts=2,
            rest_retry_attempts=2,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            require_both_success=False
        )

    async def test_mcp_timeout_rest_success_scenario(self, enhanced_service, server_config):
        """
        Test scenario where MCP request times out but REST succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP to timeout
            mock_post.return_value.__aenter__.side_effect = asyncio.TimeoutError("MCP timeout")
            
            # Configure REST to succeed
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "status": "healthy",
                "server_metrics": {"uptime": 3600}
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify failure handling
            assert result.mcp_success is False
            assert result.rest_success is True
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.overall_success is False
            assert "timeout" in str(result.mcp_error_message).lower()
            assert "rest" in result.available_paths
            assert "mcp" not in result.available_paths

    async def test_rest_timeout_mcp_success_scenario(self, enhanced_service, server_config):
        """
        Test scenario where REST request times out but MCP succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP to succeed
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {
                    "tools": [
                        {"name": "search_restaurants"},
                        {"name": "recommend_restaurants"}
                    ]
                }
            }
            
            # Configure REST to timeout
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError("REST timeout")

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify failure handling
            assert result.mcp_success is True
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.overall_success is False
            assert "timeout" in str(result.rest_error_message).lower()
            assert "mcp" in result.available_paths
            assert "rest" not in result.available_paths

    async def test_both_timeout_scenario(self, enhanced_service, server_config):
        """
        Test scenario where both MCP and REST requests timeout.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure both to timeout
            mock_post.return_value.__aenter__.side_effect = asyncio.TimeoutError("MCP timeout")
            mock_get.return_value.__aenter__.side_effect = asyncio.TimeoutError("REST timeout")

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify complete failure handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert result.overall_success is False
            assert len(result.available_paths) == 0

    async def test_mcp_authentication_failure_rest_success(self, enhanced_service, server_config):
        """
        Test scenario where MCP authentication fails but REST succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP authentication failure
            mock_post.return_value.__aenter__.return_value.status = 401
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "error": "Unauthorized: Invalid JWT token"
            }
            
            # Configure REST to succeed
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "status": "healthy"
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify authentication failure handling
            assert result.mcp_success is False
            assert result.rest_success is True
            assert result.overall_status == ServerStatus.DEGRADED
            assert "unauthorized" in str(result.mcp_error_message).lower() or "401" in str(result.mcp_error_message)

    async def test_rest_authentication_failure_mcp_success(self, enhanced_service, server_config):
        """
        Test scenario where REST authentication fails but MCP succeeds.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP to succeed
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {
                    "tools": [
                        {"name": "search_restaurants"},
                        {"name": "recommend_restaurants"}
                    ]
                }
            }
            
            # Configure REST authentication failure
            mock_get.return_value.__aenter__.return_value.status = 403
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "error": "Forbidden: Invalid API key"
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify authentication failure handling
            assert result.mcp_success is True
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.DEGRADED
            assert "forbidden" in str(result.rest_error_message).lower() or "403" in str(result.rest_error_message)

    async def test_mcp_server_error_rest_degraded(self, enhanced_service, server_config):
        """
        Test scenario where MCP has server error and REST reports degraded status.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP server error
            mock_post.return_value.__aenter__.return_value.status = 500
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "error": "Internal server error: Database connection failed"
            }
            
            # Configure REST to report degraded status
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "status": "degraded",
                "alerts": ["Database connection issues", "High memory usage"],
                "circuit_breaker_states": {
                    "database": "OPEN",
                    "mcp_tools": "HALF_OPEN"
                }
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify combined failure handling
            assert result.mcp_success is False
            assert result.rest_success is True  # REST succeeded but reported degraded
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.overall_success is False

    async def test_intermittent_failure_recovery(self, enhanced_service, server_config):
        """
        Test scenario with intermittent failures and recovery.
        
        Requirements: 3.1, 3.2
        """
        call_counts = {'mcp': 0, 'rest': 0}

        def mock_post_side_effect(*args, **kwargs):
            call_counts['mcp'] += 1
            if call_counts['mcp'] % 2 == 1:
                # Odd calls fail
                mock_response = AsyncMock()
                mock_response.status = 503
                mock_response.json.return_value = {"error": "Service temporarily unavailable"}
                return mock_response
            else:
                # Even calls succeed
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {
                        "tools": [
                            {"name": "search_restaurants"},
                            {"name": "recommend_restaurants"}
                        ]
                    }
                }
                return mock_response

        def mock_get_side_effect(*args, **kwargs):
            call_counts['rest'] += 1
            if call_counts['rest'] % 3 == 1:
                # Every third call fails
                mock_response = AsyncMock()
                mock_response.status = 502
                mock_response.json.return_value = {"error": "Bad gateway"}
                return mock_response
            else:
                # Other calls succeed
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            # Perform multiple health checks to test intermittent failures
            results = []
            for i in range(6):
                result = await enhanced_service.perform_dual_health_check(server_config)
                results.append(result)

            # Verify intermittent failure patterns
            mcp_successes = sum(1 for r in results if r.mcp_success)
            rest_successes = sum(1 for r in results if r.rest_success)
            
            # MCP should succeed on even calls (2, 4, 6) = 3 successes
            assert mcp_successes == 3
            # REST should fail on calls 1 and 4 = 4 successes
            assert rest_successes == 4

    async def test_cascading_failure_scenario(self, enhanced_service, server_config):
        """
        Test cascading failure scenario where one failure leads to another.
        
        Requirements: 3.1, 3.2
        """
        call_sequence = []

        def mock_post_side_effect(*args, **kwargs):
            call_sequence.append('mcp')
            # MCP fails due to database issues
            mock_response = AsyncMock()
            mock_response.status = 503
            mock_response.json.return_value = {
                "error": "Service unavailable: Database connection pool exhausted"
            }
            return mock_response

        def mock_get_side_effect(*args, **kwargs):
            call_sequence.append('rest')
            # REST also fails due to same database issues
            mock_response = AsyncMock()
            mock_response.status = 503
            mock_response.json.return_value = {
                "status": "unhealthy",
                "errors": ["Database connection failed", "Circuit breaker open"]
            }
            return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify cascading failure handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert "database" in str(result.mcp_error_message).lower()
            assert "database" in str(result.rest_error_message).lower()

    async def test_partial_tool_availability_scenario(self, enhanced_service, server_config):
        """
        Test scenario where MCP server has partial tool availability.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP with only partial tools available
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {
                    "tools": [
                        {"name": "search_restaurants"}
                        # Missing "recommend_restaurants"
                    ]
                }
            }
            
            # Configure REST to succeed
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "status": "healthy"
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify partial tool availability handling
            assert result.mcp_success is False  # Missing expected tool
            assert result.rest_success is True
            assert result.overall_status == ServerStatus.DEGRADED
            assert result.mcp_tools_count == 1

    async def test_network_partition_scenario(self, enhanced_service, server_config):
        """
        Test network partition scenario where connections are refused.
        
        Requirements: 3.1, 3.2
        """
        import aiohttp

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure network connection errors
            mock_post.return_value.__aenter__.side_effect = aiohttp.ClientConnectorError(
                connection_key=None, os_error=ConnectionRefusedError("Connection refused")
            )
            mock_get.return_value.__aenter__.side_effect = aiohttp.ClientConnectorError(
                connection_key=None, os_error=ConnectionRefusedError("Connection refused")
            )

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify network partition handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert "connection" in str(result.mcp_error_message).lower()
            assert "connection" in str(result.rest_error_message).lower()

    async def test_resource_exhaustion_scenario(self, enhanced_service, server_config):
        """
        Test resource exhaustion scenario affecting both monitoring paths.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure MCP resource exhaustion
            mock_post.return_value.__aenter__.return_value.status = 429
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "error": "Too many requests: Rate limit exceeded"
            }
            
            # Configure REST resource exhaustion
            mock_get.return_value.__aenter__.return_value.status = 503
            mock_get.return_value.__aenter__.return_value.json.return_value = {
                "status": "unhealthy",
                "errors": ["Memory exhausted", "CPU overload", "Connection pool full"]
            }

            result = await enhanced_service.perform_dual_health_check(server_config)

            # Verify resource exhaustion handling
            assert result.mcp_success is False
            assert result.rest_success is False
            assert result.overall_status == ServerStatus.UNHEALTHY
            assert "rate limit" in str(result.mcp_error_message).lower() or "429" in str(result.mcp_error_message)

    async def test_gradual_degradation_scenario(self, enhanced_service, server_config):
        """
        Test gradual degradation scenario over multiple health checks.
        
        Requirements: 3.1, 3.2
        """
        degradation_stages = [
            # Stage 1: Both healthy
            {
                'mcp_status': 200,
                'mcp_response': {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
                },
                'rest_status': 200,
                'rest_response': {"status": "healthy", "server_metrics": {"cpu_usage": 0.3}}
            },
            # Stage 2: REST starts showing stress
            {
                'mcp_status': 200,
                'mcp_response': {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
                },
                'rest_status': 200,
                'rest_response': {"status": "degraded", "server_metrics": {"cpu_usage": 0.7}, "alerts": ["High CPU usage"]}
            },
            # Stage 3: MCP starts having issues
            {
                'mcp_status': 200,
                'mcp_response': {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}  # Missing one tool
                },
                'rest_status': 200,
                'rest_response': {"status": "degraded", "server_metrics": {"cpu_usage": 0.8}}
            },
            # Stage 4: Both severely degraded
            {
                'mcp_status': 503,
                'mcp_response': {"error": "Service temporarily unavailable"},
                'rest_status': 503,
                'rest_response': {"status": "unhealthy", "errors": ["Service overloaded"]}
            }
        ]

        results = []
        for stage in degradation_stages:
            with patch('aiohttp.ClientSession.post') as mock_post, \
                 patch('aiohttp.ClientSession.get') as mock_get:
                
                mock_post.return_value.__aenter__.return_value.status = stage['mcp_status']
                mock_post.return_value.__aenter__.return_value.json.return_value = stage['mcp_response']
                
                mock_get.return_value.__aenter__.return_value.status = stage['rest_status']
                mock_get.return_value.__aenter__.return_value.json.return_value = stage['rest_response']

                result = await enhanced_service.perform_dual_health_check(server_config)
                results.append(result)

        # Verify gradual degradation pattern
        assert results[0].overall_status == ServerStatus.HEALTHY
        assert results[1].overall_status == ServerStatus.DEGRADED
        assert results[2].overall_status == ServerStatus.DEGRADED
        assert results[3].overall_status == ServerStatus.UNHEALTHY

        # Verify health scores decrease over time
        health_scores = [r.health_score for r in results]
        assert health_scores[0] > health_scores[1] > health_scores[2] > health_scores[3]

    async def test_recovery_after_failure_scenario(self, enhanced_service, server_config):
        """
        Test recovery scenario after complete failure.
        
        Requirements: 3.1, 3.2
        """
        # First check: Complete failure
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_post.return_value.__aenter__.return_value.status = 500
            mock_post.return_value.__aenter__.return_value.json.return_value = {"error": "Internal server error"}
            
            mock_get.return_value.__aenter__.return_value.status = 503
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "unhealthy"}

            failure_result = await enhanced_service.perform_dual_health_check(server_config)

        # Second check: Partial recovery
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "degraded"}

            recovery_result = await enhanced_service.perform_dual_health_check(server_config)

        # Third check: Full recovery
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}, {"name": "recommend_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            healthy_result = await enhanced_service.perform_dual_health_check(server_config)

        # Verify recovery pattern
        assert failure_result.overall_status == ServerStatus.UNHEALTHY
        assert recovery_result.overall_status == ServerStatus.DEGRADED
        assert healthy_result.overall_status == ServerStatus.HEALTHY

        # Verify health scores improve over time
        assert failure_result.health_score < recovery_result.health_score < healthy_result.health_score