"""
Comprehensive integration tests for the reasoning MCP server status check system.

This module tests the complete status check system including health checks,
circuit breakers, metrics tracking, and API endpoints working together for reasoning server.
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from aioresponses import aioresponses

from models.status_models import (
    ServerStatus,
    CircuitBreakerState,
    CircuitBreakerConfig,
    MCPStatusCheckConfig,
    HealthCheckResult
)
from services.health_check_service import HealthCheckService
from services.circuit_breaker import StatusCheckManager, get_reasoning_status_manager
from services.status_config_loader import StatusCheckConfigLoader, get_config_loader
from api.status_endpoints import ReasoningStatusEndpoints, ReasoningStatusConsoleIntegration


class TestReasoningStatusCheckSystemIntegration:
    """Integration tests for the complete reasoning status check system."""
    
    def create_test_config_file(self) -> str:
        """Create a temporary test configuration file for reasoning server."""
        config_data = {
            "status_check_system": {
                "enabled": True,
                "global_check_interval_seconds": 30,
                "global_timeout_seconds": 10,
                "max_concurrent_checks": 5,
                "cloudwatch_namespace": "MCP/ReasoningStatusCheck"
            },
            "circuit_breaker_defaults": {
                "failure_threshold": 3,
                "recovery_threshold": 2,
                "timeout_seconds": 5,
                "half_open_max_calls": 2
            },
            "servers": {
                "healthy-reasoning-server": {
                    "server_name": "healthy-reasoning-server",
                    "endpoint_url": "https://example.com/reasoning/healthy",
                    "enabled": True,
                    "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"],
                    "circuit_breaker": {
                        "failure_threshold": 3
                    }
                },
                "unhealthy-reasoning-server": {
                    "server_name": "unhealthy-reasoning-server",
                    "endpoint_url": "https://example.com/reasoning/unhealthy",
                    "enabled": True,
                    "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"],
                    "circuit_breaker": {
                        "failure_threshold": 2
                    }
                },
                "disabled-reasoning-server": {
                    "server_name": "disabled-reasoning-server",
                    "endpoint_url": "https://example.com/reasoning/disabled",
                    "enabled": False,
                    "expected_tools": ["recommend_restaurants", "analyze_restaurant_sentiment"]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            return f.name
    
    @pytest.fixture
    def config_file(self):
        """Configuration file fixture."""
        return self.create_test_config_file()
    
    @pytest.fixture
    def config_loader(self, config_file):
        """Configuration loader fixture."""
        return StatusCheckConfigLoader(config_file)
    
    @pytest.fixture
    def status_manager(self):
        """Status manager fixture."""
        return StatusCheckManager()
    
    @pytest.fixture
    def health_service(self):
        """Health check service fixture."""
        return HealthCheckService(timeout_seconds=5)
    
    @pytest.fixture
    def app(self):
        """FastAPI application fixture."""
        return FastAPI(title="Reasoning Status Check Integration Test")
    
    @pytest.fixture
    def status_endpoints(self, app, status_manager, config_loader):
        """Status endpoints fixture."""
        endpoints = ReasoningStatusEndpoints(app, status_manager)
        endpoints.config_loader = config_loader
        return endpoints
    
    @pytest.fixture
    def client(self, app, status_endpoints):
        """Test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def console_integration(self, status_manager):
        """Console integration fixture."""
        return ReasoningStatusConsoleIntegration(status_manager)
    
    @pytest.mark.asyncio
    async def test_complete_reasoning_system_setup(self, config_loader, status_manager):
        """Test setting up the complete reasoning status check system."""
        # Load server configurations
        server_configs = config_loader.get_server_configs()
        
        # Should have 3 reasoning servers configured, but only 2 enabled
        assert len(server_configs) == 3
        enabled_servers = config_loader.get_enabled_servers()
        assert len(enabled_servers) == 2
        assert "healthy-reasoning-server" in enabled_servers
        assert "unhealthy-reasoning-server" in enabled_servers
        assert "disabled-reasoning-server" not in enabled_servers
        
        # Verify expected tools for reasoning servers
        for server_name, config in server_configs.items():
            assert "recommend_restaurants" in config.expected_tools
            assert "analyze_restaurant_sentiment" in config.expected_tools
        
        # Add enabled servers to status manager
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Verify servers were added
        all_metrics = await status_manager.get_all_server_metrics()
        assert len(all_metrics) == 2
        assert "healthy-reasoning-server" in all_metrics
        assert "unhealthy-reasoning-server" in all_metrics
    
    @pytest.mark.asyncio
    async def test_reasoning_health_check_with_circuit_breaker_integration(self, config_loader, status_manager, health_service):
        """Test reasoning health checks integrated with circuit breaker functionality."""
        # Set up servers
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Mock successful and failing health checks with reasoning tools
        with aioresponses() as m:
            # Healthy reasoning server responds successfully with expected tools
            m.post(
                "https://example.com/reasoning/healthy",
                payload={
                    "jsonrpc": "2.0",
                    "id": "reasoning-health-check",
                    "result": {
                        "tools": [
                            {"name": "recommend_restaurants", "description": "Analyze restaurant sentiment data and provide intelligent recommendations"},
                            {"name": "analyze_restaurant_sentiment", "description": "Analyze sentiment data without providing recommendations"}
                        ]
                    }
                },
                status=200,
                repeat=True
            )
            
            # Unhealthy reasoning server fails
            m.post(
                "https://example.com/reasoning/unhealthy",
                status=500,
                repeat=True
            )
            
            async with health_service:
                # Perform multiple health checks to trigger circuit breaker
                enabled_configs = [config for config in server_configs.values() if config.enabled]
                
                for round_num in range(4):  # Enough to trigger circuit breaker
                    results = await health_service.check_multiple_servers(enabled_configs)
                    
                    # Record results in status manager
                    for result in results:
                        await status_manager.record_health_check_result(result)
                    
                    # Check results
                    healthy_result = next(r for r in results if r.server_name == "healthy-reasoning-server")
                    unhealthy_result = next(r for r in results if r.server_name == "unhealthy-reasoning-server")
                    
                    assert healthy_result.success is True
                    assert healthy_result.tools_count == 2  # Should have both reasoning tools
                    assert unhealthy_result.success is False
        
        # Check final circuit breaker states
        cb_states = await status_manager.get_all_circuit_breaker_states()
        assert cb_states["healthy-reasoning-server"] == CircuitBreakerState.CLOSED
        assert cb_states["unhealthy-reasoning-server"] == CircuitBreakerState.OPEN  # Should be open after failures
        
        # Check server availability
        assert await status_manager.is_server_available("healthy-reasoning-server") is True
        assert await status_manager.is_server_available("unhealthy-reasoning-server") is False
    
    @pytest.mark.asyncio
    async def test_reasoning_api_endpoints_integration(self, client, config_loader, status_manager):
        """Test reasoning API endpoints with real status data."""
        # Set up servers with test data
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Add some test health check results
        healthy_result = HealthCheckResult(
            server_name="healthy-reasoning-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=100.0,
            tools_count=2  # Both reasoning tools
        )
        
        unhealthy_result = HealthCheckResult(
            server_name="unhealthy-reasoning-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            error_message="Connection timeout"
        )
        
        await status_manager.record_health_check_result(healthy_result)
        await status_manager.record_health_check_result(unhealthy_result)
        
        # Test reasoning system health endpoint
        response = client.get("/status/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["success"] is True
        assert health_data["data"]["total_servers"] == 2
        assert health_data["data"]["server_type"] == "reasoning"
        
        # Test reasoning servers status endpoint
        response = client.get("/status/servers")
        assert response.status_code == 200
        servers_data = response.json()
        assert len(servers_data["data"]["servers"]) == 2
        
        # Verify reasoning tools are included in server status
        for server in servers_data["data"]["servers"]:
            assert "expected_tools" in server
            assert "recommend_restaurants" in server["expected_tools"]
            assert "analyze_restaurant_sentiment" in server["expected_tools"]
        
        # Test individual reasoning server status
        response = client.get("/status/servers/healthy-reasoning-server")
        assert response.status_code == 200
        server_data = response.json()
        assert server_data["data"]["server_name"] == "healthy-reasoning-server"
        assert server_data["data"]["status"] == "healthy"
        assert "recommend_restaurants" in server_data["data"]["expected_tools"]
        assert "analyze_restaurant_sentiment" in server_data["data"]["expected_tools"]
        
        # Test reasoning metrics endpoint
        response = client.get("/status/metrics")
        assert response.status_code == 200
        metrics_data = response.json()
        assert "aggregate_metrics" in metrics_data["data"]
        assert "server_metrics" in metrics_data["data"]
        assert metrics_data["data"]["server_type"] == "reasoning"
        
        # Test reasoning configuration endpoint
        response = client.get("/status/config")
        assert response.status_code == 200
        config_data = response.json()
        assert len(config_data["data"]["server_configs"]) == 3
        assert len(config_data["data"]["enabled_servers"]) == 2
        assert config_data["data"]["server_type"] == "reasoning"
    
    @pytest.mark.asyncio
    async def test_reasoning_circuit_breaker_control_via_api(self, client, config_loader, status_manager):
        """Test controlling reasoning circuit breakers via API endpoints."""
        # Set up servers
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Test opening reasoning circuit breaker
        request_data = {
            "action": "open",
            "server_names": ["healthy-reasoning-server"]
        }
        
        response = client.post("/status/circuit-breaker", json=request_data)
        assert response.status_code == 200
        
        # Verify circuit breaker is open
        cb_state = await status_manager.get_server_circuit_breaker_state("healthy-reasoning-server")
        assert cb_state == CircuitBreakerState.OPEN
        
        # Test closing reasoning circuit breaker
        request_data["action"] = "close"
        response = client.post("/status/circuit-breaker", json=request_data)
        assert response.status_code == 200
        
        # Verify circuit breaker is closed
        cb_state = await status_manager.get_server_circuit_breaker_state("healthy-reasoning-server")
        assert cb_state == CircuitBreakerState.CLOSED
        
        # Test reset reasoning circuit breaker
        request_data["action"] = "reset"
        response = client.post("/status/circuit-breaker", json=request_data)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_reasoning_console_integration_with_real_data(self, console_integration, config_loader, status_manager):
        """Test reasoning console integration with real status data."""
        # Set up servers with varied health states
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Create healthy reasoning server
        for i in range(3):
            result = HealthCheckResult(
                server_name="healthy-reasoning-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0 + i * 10,
                tools_count=2  # Both reasoning tools
            )
            await status_manager.record_health_check_result(result)
        
        # Create unhealthy reasoning server with failures
        for i in range(6):  # More than 5 consecutive failures
            result = HealthCheckResult(
                server_name="unhealthy-reasoning-server",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                error_message=f"Reasoning failure {i+1}"
            )
            await status_manager.record_health_check_result(result)
        
        # Force circuit breaker open for unhealthy reasoning server
        await status_manager.force_circuit_breaker_open("unhealthy-reasoning-server")
        
        # Get dashboard data
        dashboard_data = await console_integration.get_dashboard_data()
        
        # Verify dashboard structure
        assert "timestamp" in dashboard_data
        assert "system_health" in dashboard_data
        assert "servers" in dashboard_data
        assert "alerts" in dashboard_data
        assert dashboard_data["server_type"] == "reasoning"
        
        # Check system health
        system_health = dashboard_data["system_health"]
        assert system_health["total_servers"] == 2
        assert system_health["healthy_servers"] == 1
        assert system_health["unhealthy_servers"] == 1
        assert system_health["overall_health_percentage"] == 50.0
        assert system_health["server_type"] == "reasoning"
        
        # Check servers are sorted by status (unhealthy first)
        servers = dashboard_data["servers"]
        assert len(servers) == 2
        assert servers[0]["status"] == "unhealthy"  # Should be first
        assert servers[1]["status"] == "healthy"   # Should be second
        
        # Verify reasoning tools are included
        for server in servers:
            assert server["server_type"] == "reasoning"
            assert "recommend_restaurants" in server["expected_tools"]
            assert "analyze_restaurant_sentiment" in server["expected_tools"]
        
        # Check alerts
        alerts = dashboard_data["alerts"]
        assert len(alerts) > 0
        
        # Should have circuit breaker alert for reasoning server
        cb_alerts = [alert for alert in alerts if alert["type"] == "circuit_breaker_open"]
        assert len(cb_alerts) == 1
        assert cb_alerts[0]["server"] == "unhealthy-reasoning-server"
        assert cb_alerts[0]["severity"] == "critical"
        assert cb_alerts[0]["server_type"] == "reasoning"
        assert "Reasoning circuit breaker is OPEN" in cb_alerts[0]["message"]
    
    @pytest.mark.asyncio
    async def test_reasoning_manual_health_check_via_api(self, client, config_loader, status_manager):
        """Test triggering manual health checks for reasoning servers via API."""
        # Set up servers
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Mock health check responses
        with aioresponses() as m:
            m.post(
                "https://example.com/reasoning/healthy",
                payload={
                    "jsonrpc": "2.0",
                    "id": "reasoning-health-check",
                    "result": {
                        "tools": [
                            {"name": "recommend_restaurants", "description": "Reasoning tool 1"},
                            {"name": "analyze_restaurant_sentiment", "description": "Reasoning tool 2"}
                        ]
                    }
                },
                status=200
            )
            
            m.post(
                "https://example.com/reasoning/unhealthy",
                status=500
            )
            
            # Trigger manual health check
            request_data = {
                "server_names": ["healthy-reasoning-server", "unhealthy-reasoning-server"],
                "timeout_seconds": 10
            }
            
            with patch('api.status_endpoints.quick_health_check') as mock_health_check:
                # Mock the health check results
                mock_results = {
                    "healthy-reasoning-server": HealthCheckResult(
                        server_name="healthy-reasoning-server",
                        timestamp=datetime.now(),
                        success=True,
                        response_time_ms=150.0,
                        tools_count=2
                    ),
                    "unhealthy-reasoning-server": HealthCheckResult(
                        server_name="unhealthy-reasoning-server",
                        timestamp=datetime.now(),
                        success=False,
                        response_time_ms=5000.0,
                        error_message="HTTP 500"
                    )
                }
                mock_health_check.return_value = mock_results
                
                response = client.post("/status/health-check", json=request_data)
                assert response.status_code == 200
                
                data = response.json()
                assert data["success"] is True
                assert "Reasoning health check completed" in data["message"]
                assert "1/2 servers healthy" in data["message"]
                
                # Check results structure
                results = data["data"]["results"]
                assert len(results) == 2
                assert results["healthy-reasoning-server"]["success"] is True
                assert results["unhealthy-reasoning-server"]["success"] is False
                
                # Check summary
                summary = data["data"]["summary"]
                assert summary["total_servers"] == 2
                assert summary["healthy_servers"] == 1
                assert summary["unhealthy_servers"] == 1
    
    @pytest.mark.asyncio
    async def test_reasoning_circuit_breaker_recovery_cycle(self, config_loader, status_manager, health_service):
        """Test reasoning circuit breaker failure detection and manual recovery."""
        # Set up server with short timeout for testing
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_threshold=2,
            timeout_seconds=1,  # Short timeout for testing
            half_open_max_calls=2
        )
        
        await status_manager.add_server("test-reasoning-server", config)
        
        # Phase 1: Simulate failures to open circuit breaker
        for i in range(3):
            result = HealthCheckResult(
                server_name="test-reasoning-server",
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                error_message=f"Reasoning failure {i+1}"
            )
            await status_manager.record_health_check_result(result)
        
        # Circuit breaker should be open
        cb_state = await status_manager.get_server_circuit_breaker_state("test-reasoning-server")
        assert cb_state == CircuitBreakerState.OPEN
        assert await status_manager.is_server_available("test-reasoning-server") is False
        
        # Phase 2: Test manual circuit breaker control
        # Force circuit breaker to half-open for testing
        circuit_breaker = status_manager.circuit_breakers["test-reasoning-server"]
        await circuit_breaker._transition_to_half_open()
        
        cb_state = await status_manager.get_server_circuit_breaker_state("test-reasoning-server")
        assert cb_state == CircuitBreakerState.HALF_OPEN
        
        # Simulate successful health checks for recovery
        for i in range(2):  # recovery_threshold = 2
            result = HealthCheckResult(
                server_name="test-reasoning-server",
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0,
                tools_count=2  # Both reasoning tools
            )
            await status_manager.record_health_check_result(result)
        
        # Circuit breaker should be closed after recovery
        cb_state = await status_manager.get_server_circuit_breaker_state("test-reasoning-server")
        assert cb_state == CircuitBreakerState.CLOSED
        assert await status_manager.is_server_available("test-reasoning-server") is True
    
    @pytest.mark.asyncio
    async def test_reasoning_system_metrics_accuracy(self, config_loader, status_manager):
        """Test that reasoning system metrics are calculated accurately."""
        # Set up servers
        server_configs = config_loader.get_server_configs()
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
        
        # Add varied health check results
        test_data = [
            ("healthy-reasoning-server", True, 100.0, 2),
            ("healthy-reasoning-server", True, 120.0, 2),
            ("healthy-reasoning-server", True, 110.0, 2),
            ("unhealthy-reasoning-server", False, 5000.0, None),
            ("unhealthy-reasoning-server", False, 4500.0, None),
            ("unhealthy-reasoning-server", True, 200.0, 2),  # One success
        ]
        
        for server_name, success, response_time, tools_count in test_data:
            result = HealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=success,
                response_time_ms=response_time,
                tools_count=tools_count,
                error_message=None if success else "Reasoning test error"
            )
            await status_manager.record_health_check_result(result)
        
        # Get system health summary
        health_summary = await status_manager.get_system_health_summary()
        
        # Verify calculations
        assert health_summary["total_servers"] == 2
        assert health_summary["server_type"] == "reasoning"
        # Both servers have recent activity, so they should be considered healthy or degraded
        # The exact classification depends on the consecutive failures at the end
        assert health_summary["healthy_servers"] + health_summary["degraded_servers"] == 2
        
        # Get individual server metrics
        healthy_metrics = await status_manager.get_server_metrics("healthy-reasoning-server")
        unhealthy_metrics = await status_manager.get_server_metrics("unhealthy-reasoning-server")
        
        # Verify healthy reasoning server metrics
        assert healthy_metrics.total_requests == 3
        assert healthy_metrics.successful_requests == 3
        assert healthy_metrics.success_rate == 100.0
        assert abs(healthy_metrics.average_response_time_ms - 110.0) < 0.1  # (100+120+110)/3
        
        # Verify unhealthy reasoning server metrics
        assert unhealthy_metrics.total_requests == 3
        assert unhealthy_metrics.successful_requests == 1
        assert unhealthy_metrics.failed_requests == 2
        assert abs(unhealthy_metrics.success_rate - 33.33) < 0.1
        assert unhealthy_metrics.consecutive_failures == 0  # Last was success
        assert unhealthy_metrics.consecutive_successes == 1
        
        # Verify the server is considered healthy since last check was successful
        assert unhealthy_metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_reasoning_tools_validation(self, config_loader, status_manager, health_service):
        """Test that reasoning tools are properly validated in health checks."""
        # Set up server
        server_configs = config_loader.get_server_configs()
        config = server_configs["healthy-reasoning-server"]
        await status_manager.add_server(config.server_name, config.circuit_breaker)
        
        # Test with missing reasoning tools
        with aioresponses() as m:
            # Response missing analyze_restaurant_sentiment tool
            m.post(
                "https://example.com/reasoning/healthy",
                payload={
                    "jsonrpc": "2.0",
                    "id": "reasoning-health-check",
                    "result": {
                        "tools": [
                            {"name": "recommend_restaurants", "description": "Only one tool"}
                        ]
                    }
                },
                status=200
            )
            
            async with health_service:
                result = await health_service.check_server_health(config)
                
                # Should fail because missing expected reasoning tool
                assert result.success is False
                assert "Missing expected reasoning tools" in result.error_message
                assert "analyze_restaurant_sentiment" in result.error_message
        
        # Test with all expected reasoning tools
        with aioresponses() as m:
            # Response with both expected reasoning tools
            m.post(
                "https://example.com/reasoning/healthy",
                payload={
                    "jsonrpc": "2.0",
                    "id": "reasoning-health-check",
                    "result": {
                        "tools": [
                            {"name": "recommend_restaurants", "description": "Reasoning tool 1"},
                            {"name": "analyze_restaurant_sentiment", "description": "Reasoning tool 2"}
                        ]
                    }
                },
                status=200
            )
            
            async with health_service:
                result = await health_service.check_server_health(config)
                
                # Should succeed with both reasoning tools
                assert result.success is True
                assert result.tools_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])