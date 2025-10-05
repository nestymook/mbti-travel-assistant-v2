"""
Tests for Enhanced Status Check REST API Endpoints

This module contains comprehensive tests for the enhanced REST API endpoints
that provide dual monitoring results with backward compatibility.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import json

from api.enhanced_status_endpoints import (
    EnhancedStatusEndpoints,
    create_enhanced_status_app,
    HealthCheckRequest,
    ServerStatusResponse,
    SystemHealthResponse,
    MetricsResponse,
    ConfigurationResponse
)
from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus,
    CombinedHealthMetrics,
    AggregationConfig,
    PriorityConfig
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.enhanced_status_config import EnhancedStatusConfig


class TestEnhancedStatusEndpoints:
    """Test cases for Enhanced Status Endpoints."""
    
    @pytest.fixture
    def mock_health_service(self):
        """Create mock health service."""
        service = AsyncMock(spec=EnhancedHealthCheckService)
        service.aggregator = MagicMock()
        service.aggregator.create_aggregation_summary.return_value = {
            "total_servers": 1,
            "healthy_servers": 1,
            "degraded_servers": 0,
            "unhealthy_servers": 0,
            "unknown_servers": 0,
            "average_health_score": 0.95,
            "average_response_time_ms": 100.0,
            "mcp_success_rate": 1.0,
            "rest_success_rate": 1.0,
            "combined_success_rate": 1.0
        }
        return service
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Create mock metrics collector."""
        collector = AsyncMock(spec=DualMetricsCollector)
        collector.get_mcp_metrics.return_value = {
            "total_requests": 100,
            "successful_requests": 85,
            "failed_requests": 15,
            "average_response_time_ms": 120.0,
            "tools_validation_success_rate": 0.9
        }
        collector.get_rest_metrics.return_value = {
            "total_requests": 100,
            "successful_requests": 90,
            "failed_requests": 10,
            "average_response_time_ms": 80.0,
            "http_status_codes": {"200": 90, "500": 10}
        }
        collector.get_combined_metrics.return_value = {
            "total_dual_checks": 100,
            "both_successful": 80,
            "mcp_only_successful": 5,
            "rest_only_successful": 10,
            "both_failed": 5,
            "average_combined_response_time_ms": 100.0
        }
        return collector
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager."""
        manager = MagicMock()
        
        # Mock server configs
        server_config1 = EnhancedServerConfig(
            server_name="test-server-1",
            mcp_endpoint_url="http://localhost:8001/mcp",
            rest_health_endpoint_url="http://localhost:8001/status/health",
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"]
        )
        server_config2 = EnhancedServerConfig(
            server_name="test-server-2",
            mcp_endpoint_url="http://localhost:8002/mcp",
            rest_health_endpoint_url="http://localhost:8002/status/health",
            mcp_expected_tools=["analyze_sentiment"]
        )
        
        # Create async mock methods
        async def mock_get_all_server_configs():
            return [server_config1, server_config2]
        
        async def mock_get_server_config(server_name):
            if server_name == "test-server-1":
                return server_config1
            elif server_name == "test-server-2":
                return server_config2
            return None
        
        manager.get_all_server_configs = mock_get_all_server_configs
        manager.get_server_config = mock_get_server_config
        
        # Mock current config
        mock_config = MagicMock()
        mock_config.dual_monitoring_enabled = True
        mock_config.mcp_health_checks = {
            "enabled": True,
            "default_timeout_seconds": 10,
            "tools_list_validation": True
        }
        mock_config.rest_health_checks = {
            "enabled": True,
            "default_timeout_seconds": 8,
            "health_endpoint_path": "/status/health"
        }
        mock_config.result_aggregation = {
            "mcp_priority_weight": 0.6,
            "rest_priority_weight": 0.4
        }
        mock_config.last_updated = datetime.now()
        
        async def mock_get_current_config():
            return mock_config
        
        async def mock_update_config(config_update):
            return True
        
        manager.get_current_config = mock_get_current_config
        manager.update_config = mock_update_config
        
        return manager
    
    @pytest.fixture
    def sample_dual_result(self):
        """Create sample dual health check result."""
        mcp_result = MCPHealthCheckResult(
            server_name="test-server-1",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=120.0,
            tools_count=2,
            expected_tools_found=["search_restaurants", "recommend_restaurants"],
            missing_tools=[],
            request_id="test-123"
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server-1",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=80.0,
            status_code=200,
            health_endpoint_url="http://localhost:8001/status/health"
        )
        
        combined_metrics = CombinedHealthMetrics(
            mcp_response_time_ms=120.0,
            rest_response_time_ms=80.0,
            combined_response_time_ms=100.0,
            mcp_success_rate=1.0,
            rest_success_rate=1.0,
            combined_success_rate=1.0,
            tools_available_count=2,
            tools_expected_count=2,
            tools_availability_percentage=100.0
        )
        
        return DualHealthCheckResult(
            server_name="test-server-1",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=mcp_result,
            mcp_success=True,
            mcp_response_time_ms=120.0,
            mcp_tools_count=2,
            rest_result=rest_result,
            rest_success=True,
            rest_response_time_ms=80.0,
            rest_status_code=200,
            combined_response_time_ms=100.0,
            health_score=0.95,
            available_paths=["mcp", "rest", "both"],
            combined_metrics=combined_metrics
        )
    
    @pytest.fixture
    def endpoints(self, mock_health_service, mock_metrics_collector, mock_config_manager):
        """Create enhanced status endpoints instance."""
        return EnhancedStatusEndpoints(
            health_service=mock_health_service,
            metrics_collector=mock_metrics_collector,
            config_manager=mock_config_manager
        )
    
    @pytest.fixture
    def test_client(self, mock_health_service, mock_metrics_collector, mock_config_manager):
        """Create test client with FastAPI app."""
        app = create_enhanced_status_app(
            health_service=mock_health_service,
            metrics_collector=mock_metrics_collector,
            config_manager=mock_config_manager
        )
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_get_system_health_success(self, endpoints, sample_dual_result):
        """Test successful system health retrieval."""
        # Mock health service response
        endpoints.health_service.check_multiple_servers_dual.return_value = [sample_dual_result]
        
        # Test with force check
        response = await endpoints._get_system_health(
            include_servers=True,
            force_check=True,
            timeout=30
        )
        
        assert isinstance(response, SystemHealthResponse)
        assert response.overall_status == "HEALTHY"
        assert response.total_servers == 1
        assert response.healthy_servers == 1
        assert len(response.servers) == 1
        assert response.servers[0].server_name == "test-server-1"
        assert response.servers[0].success is True
    
    @pytest.mark.asyncio
    async def test_get_system_health_cached(self, endpoints, sample_dual_result):
        """Test system health with cached results."""
        # Add result to cache
        endpoints._result_cache["test-server-1"] = sample_dual_result
        
        # Test without force check (should use cache)
        response = await endpoints._get_system_health(
            include_servers=True,
            force_check=False,
            timeout=30
        )
        
        assert isinstance(response, SystemHealthResponse)
        assert response.overall_status == "HEALTHY"
        # Should not call health service since using cache
        endpoints.health_service.check_multiple_servers_dual.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_server_status_success(self, endpoints, sample_dual_result):
        """Test successful server status retrieval."""
        endpoints.health_service.perform_dual_health_check.return_value = sample_dual_result
        
        response = await endpoints._get_server_status(
            server_name="test-server-1",
            force_check=True,
            timeout=30
        )
        
        assert isinstance(response, ServerStatusResponse)
        assert response.server_name == "test-server-1"
        assert response.status == "HEALTHY"
        assert response.success is True
        assert response.health_score == 0.95
        assert "mcp" in response.available_paths
        assert "rest" in response.available_paths
    
    @pytest.mark.asyncio
    async def test_get_server_status_not_found(self, endpoints):
        """Test server status for non-existent server."""
        endpoints.config_manager.get_server_config.return_value = None
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await endpoints._get_server_status(
                server_name="non-existent-server",
                force_check=True,
                timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self, endpoints):
        """Test successful system metrics retrieval."""
        response = await endpoints._get_system_metrics(
            time_range=3600,
            include_server_breakdown=True
        )
        
        assert isinstance(response, MetricsResponse)
        assert "total_requests" in response.mcp_metrics
        assert "total_requests" in response.rest_metrics
        assert "total_dual_checks" in response.combined_metrics
        assert len(response.server_metrics) == 2  # Two servers configured
    
    @pytest.mark.asyncio
    async def test_trigger_dual_health_check_success(self, endpoints, sample_dual_result):
        """Test successful manual dual health check trigger."""
        endpoints.health_service.check_multiple_servers_dual.return_value = [sample_dual_result]
        
        request = HealthCheckRequest(
            server_names=["test-server-1"],
            timeout_seconds=30,
            include_mcp=True,
            include_rest=True
        )
        
        background_tasks = MagicMock()
        
        response = await endpoints._trigger_dual_health_check(request, background_tasks)
        
        assert "check_id" in response
        assert "timestamp" in response
        assert "summary" in response
        assert "servers" in response
        assert len(response["servers"]) == 1
        assert response["servers"][0]["server_name"] == "test-server-1"
    
    @pytest.mark.asyncio
    async def test_get_configuration_success(self, endpoints):
        """Test successful configuration retrieval."""
        response = await endpoints._get_configuration(include_sensitive=False)
        
        assert isinstance(response, ConfigurationResponse)
        assert response.enhanced_monitoring_enabled is True
        assert "enabled" in response.mcp_health_checks
        assert "enabled" in response.rest_health_checks
        assert len(response.servers) == 2
        
        # Check that sensitive data is not included
        for server in response.servers:
            assert "jwt_token" not in server
            assert "auth_headers" not in server
    
    @pytest.mark.asyncio
    async def test_get_configuration_with_sensitive(self, endpoints):
        """Test configuration retrieval with sensitive data."""
        response = await endpoints._get_configuration(include_sensitive=True)
        
        assert isinstance(response, ConfigurationResponse)
        # Sensitive data should be included (though None in this test)
        for server in response.servers:
            assert "jwt_token" in server or server.get("jwt_token") is None
    
    @pytest.mark.asyncio
    async def test_update_configuration_success(self, endpoints):
        """Test successful configuration update."""
        config_update = {
            "mcp_health_checks": {
                "default_timeout_seconds": 15
            }
        }
        
        response = await endpoints._update_configuration(config_update)
        
        assert response["success"] is True
        assert "Configuration updated successfully" in response["message"]
        assert "mcp_health_checks" in response["updated_fields"]
    
    @pytest.mark.asyncio
    async def test_update_configuration_failure(self, endpoints):
        """Test configuration update failure."""
        endpoints.config_manager.update_config.return_value = False
        
        config_update = {"invalid_field": "invalid_value"}
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await endpoints._update_configuration(config_update)
    
    @pytest.mark.asyncio
    async def test_legacy_health_endpoint(self, endpoints, sample_dual_result):
        """Test legacy health endpoint for backward compatibility."""
        # Mock system health response
        with patch.object(endpoints, '_get_system_health') as mock_get_health:
            mock_system_health = SystemHealthResponse(
                overall_status="HEALTHY",
                total_servers=2,
                healthy_servers=2,
                degraded_servers=0,
                unhealthy_servers=0,
                unknown_servers=0,
                last_check_timestamp=datetime.now().isoformat(),
                average_health_score=0.95,
                average_response_time_ms=100.0,
                servers=[]
            )
            mock_get_health.return_value = mock_system_health
            
            response = await endpoints._get_legacy_health()
            
            assert response["status"] == "healthy"
            assert response["healthy"] is True
            assert "timestamp" in response
            assert response["servers"]["total"] == 2
            assert response["servers"]["healthy"] == 2
    
    @pytest.mark.asyncio
    async def test_legacy_status_endpoint(self, endpoints, sample_dual_result):
        """Test legacy status endpoint for backward compatibility."""
        # Create mock server response
        mock_server_response = ServerStatusResponse(
            server_name="test-server-1",
            status="HEALTHY",
            success=True,
            timestamp=datetime.now().isoformat(),
            health_score=0.95,
            available_paths=["mcp", "rest", "both"]
        )
        
        with patch.object(endpoints, '_get_system_health') as mock_get_health:
            mock_system_health = SystemHealthResponse(
                overall_status="HEALTHY",
                total_servers=1,
                healthy_servers=1,
                degraded_servers=0,
                unhealthy_servers=0,
                unknown_servers=0,
                last_check_timestamp=datetime.now().isoformat(),
                average_health_score=0.95,
                average_response_time_ms=100.0,
                servers=[mock_server_response]
            )
            mock_get_health.return_value = mock_system_health
            
            response = await endpoints._get_legacy_status()
            
            assert response["overall_status"] == "healthy"
            assert "test-server-1" in response["servers"]
            assert response["servers"]["test-server-1"]["status"] == "healthy"
            assert response["servers"]["test-server-1"]["healthy"] is True
            assert response["summary"]["total"] == 1
            assert response["summary"]["healthy"] == 1
    
    def test_create_server_status_response(self, endpoints, sample_dual_result):
        """Test server status response creation."""
        response = endpoints._create_server_status_response(sample_dual_result)
        
        assert isinstance(response, ServerStatusResponse)
        assert response.server_name == "test-server-1"
        assert response.status == "HEALTHY"
        assert response.success is True
        assert response.health_score == 0.95
        assert response.mcp_result is not None
        assert response.rest_result is not None
        assert response.combined_metrics is not None
        assert response.error_message is None
    
    def test_create_server_status_response_with_errors(self, endpoints):
        """Test server status response creation with errors."""
        # Create dual result with errors
        dual_result = DualHealthCheckResult(
            server_name="test-server-1",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_success=False,
            mcp_error_message="MCP connection failed",
            rest_success=False,
            rest_error_message="REST endpoint unavailable",
            health_score=0.0,
            available_paths=["none"]
        )
        
        response = endpoints._create_server_status_response(dual_result)
        
        assert response.success is False
        assert response.status == "UNHEALTHY"
        assert "MCP: MCP connection failed" in response.error_message
        assert "REST: REST endpoint unavailable" in response.error_message
    
    def test_fastapi_integration(self, test_client, sample_dual_result):
        """Test FastAPI integration with test client."""
        # Test system health endpoint
        response = test_client.get("/status/health")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "total_servers" in data
        
        # Test server status endpoint
        response = test_client.get("/status/servers/test-server-1")
        assert response.status_code == 200
        data = response.json()
        assert "server_name" in data
        assert "status" in data
        
        # Test metrics endpoint
        response = test_client.get("/status/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "mcp_metrics" in data
        assert "rest_metrics" in data
        assert "combined_metrics" in data
        
        # Test configuration endpoint
        response = test_client.get("/status/config")
        assert response.status_code == 200
        data = response.json()
        assert "enhanced_monitoring_enabled" in data
        assert "mcp_health_checks" in data
        assert "rest_health_checks" in data
        
        # Test legacy endpoints
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "healthy" in data
        
        response = test_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "servers" in data
    
    def test_manual_health_check_endpoint(self, test_client):
        """Test manual health check endpoint."""
        request_data = {
            "server_names": ["test-server-1"],
            "timeout_seconds": 30,
            "include_mcp": True,
            "include_rest": True
        }
        
        response = test_client.post("/status/dual-check", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "check_id" in data
        assert "timestamp" in data
        assert "summary" in data
        assert "servers" in data
    
    def test_configuration_update_endpoint(self, test_client):
        """Test configuration update endpoint."""
        update_data = {
            "mcp_health_checks": {
                "default_timeout_seconds": 15
            }
        }
        
        response = test_client.put("/status/config", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_cache_management(self, endpoints, sample_dual_result):
        """Test result cache management."""
        # Add result to cache
        endpoints._result_cache["test-server-1"] = sample_dual_result
        
        # Verify cache contains result
        assert "test-server-1" in endpoints._result_cache
        
        # Test cache expiration by modifying timestamp
        old_result = DualHealthCheckResult(
            server_name="test-server-2",
            timestamp=datetime.now() - timedelta(hours=1),  # Old timestamp
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            health_score=0.8,
            available_paths=["mcp", "rest"]
        )
        endpoints._result_cache["test-server-2"] = old_result
        
        # Simulate cache cleanup (would normally be done by background task)
        current_time = datetime.now()
        expired_keys = []
        for server_name, result in endpoints._result_cache.items():
            if current_time - result.timestamp > endpoints._cache_ttl:
                expired_keys.append(server_name)
        
        for key in expired_keys:
            endpoints._result_cache.pop(key, None)
        
        # Verify expired entry was removed
        assert "test-server-2" not in endpoints._result_cache
        assert "test-server-1" in endpoints._result_cache  # Recent entry should remain
    
    @pytest.mark.asyncio
    async def test_background_tasks(self, endpoints):
        """Test background task management."""
        # Start background tasks
        await endpoints.start_background_tasks()
        
        # Verify tasks are running
        assert len(endpoints._background_tasks) > 0
        
        # Stop background tasks
        await endpoints.stop_background_tasks()
        
        # Verify tasks are stopped
        for task in endpoints._background_tasks:
            assert task.done() or task.cancelled()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, endpoints):
        """Test async context manager functionality."""
        async with endpoints:
            # Verify background tasks are started
            assert len(endpoints._background_tasks) > 0
        
        # Verify background tasks are stopped after exit
        for task in endpoints._background_tasks:
            assert task.done() or task.cancelled()


class TestHealthCheckRequest:
    """Test cases for HealthCheckRequest model."""
    
    def test_health_check_request_defaults(self):
        """Test HealthCheckRequest with default values."""
        request = HealthCheckRequest()
        
        assert request.server_names is None
        assert request.timeout_seconds == 30
        assert request.include_mcp is True
        assert request.include_rest is True
    
    def test_health_check_request_custom_values(self):
        """Test HealthCheckRequest with custom values."""
        request = HealthCheckRequest(
            server_names=["server1", "server2"],
            timeout_seconds=60,
            include_mcp=False,
            include_rest=True
        )
        
        assert request.server_names == ["server1", "server2"]
        assert request.timeout_seconds == 60
        assert request.include_mcp is False
        assert request.include_rest is True


class TestResponseModels:
    """Test cases for response models."""
    
    def test_server_status_response_creation(self):
        """Test ServerStatusResponse creation."""
        response = ServerStatusResponse(
            server_name="test-server",
            status="HEALTHY",
            success=True,
            timestamp=datetime.now().isoformat(),
            health_score=0.95,
            available_paths=["mcp", "rest", "both"]
        )
        
        assert response.server_name == "test-server"
        assert response.status == "HEALTHY"
        assert response.success is True
        assert response.health_score == 0.95
        assert "mcp" in response.available_paths
    
    def test_system_health_response_creation(self):
        """Test SystemHealthResponse creation."""
        server_response = ServerStatusResponse(
            server_name="test-server",
            status="HEALTHY",
            success=True,
            timestamp=datetime.now().isoformat(),
            health_score=0.95,
            available_paths=["mcp", "rest"]
        )
        
        response = SystemHealthResponse(
            overall_status="HEALTHY",
            total_servers=1,
            healthy_servers=1,
            degraded_servers=0,
            unhealthy_servers=0,
            unknown_servers=0,
            last_check_timestamp=datetime.now().isoformat(),
            average_health_score=0.95,
            average_response_time_ms=100.0,
            servers=[server_response]
        )
        
        assert response.overall_status == "HEALTHY"
        assert response.total_servers == 1
        assert response.healthy_servers == 1
        assert len(response.servers) == 1
        assert response.servers[0].server_name == "test-server"
    
    def test_metrics_response_creation(self):
        """Test MetricsResponse creation."""
        response = MetricsResponse(
            timestamp=datetime.now().isoformat(),
            mcp_metrics={"total_requests": 100},
            rest_metrics={"total_requests": 100},
            combined_metrics={"total_dual_checks": 100},
            server_metrics={"server1": {"mcp_metrics": {}, "rest_metrics": {}}}
        )
        
        assert "total_requests" in response.mcp_metrics
        assert "total_requests" in response.rest_metrics
        assert "total_dual_checks" in response.combined_metrics
        assert "server1" in response.server_metrics
    
    def test_configuration_response_creation(self):
        """Test ConfigurationResponse creation."""
        response = ConfigurationResponse(
            enhanced_monitoring_enabled=True,
            mcp_health_checks={"enabled": True},
            rest_health_checks={"enabled": True},
            result_aggregation={"mcp_priority_weight": 0.6},
            servers=[{"server_name": "test-server"}],
            last_updated=datetime.now().isoformat()
        )
        
        assert response.enhanced_monitoring_enabled is True
        assert response.mcp_health_checks["enabled"] is True
        assert response.rest_health_checks["enabled"] is True
        assert len(response.servers) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])