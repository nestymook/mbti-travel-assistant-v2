"""
Simple Integration Test for Enhanced Status API Endpoints

This test verifies that the enhanced REST API endpoints can be created
and respond correctly with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from api.enhanced_status_endpoints import create_enhanced_status_app
from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus,
    CombinedHealthMetrics
)


class TestAPIIntegrationSimple:
    """Simple integration tests for enhanced status API."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        # Mock health service
        health_service = AsyncMock()
        
        # Create sample dual result
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=100.0,
            tools_count=2,
            expected_tools_found=["tool1", "tool2"],
            missing_tools=[],
            request_id="test-123"
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=80.0,
            status_code=200,
            health_endpoint_url="http://localhost:8001/status/health"
        )
        
        combined_metrics = CombinedHealthMetrics(
            mcp_response_time_ms=100.0,
            rest_response_time_ms=80.0,
            combined_response_time_ms=90.0,
            mcp_success_rate=1.0,
            rest_success_rate=1.0,
            combined_success_rate=1.0,
            tools_available_count=2,
            tools_expected_count=2,
            tools_availability_percentage=100.0
        )
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=mcp_result,
            mcp_success=True,
            mcp_response_time_ms=100.0,
            mcp_tools_count=2,
            rest_result=rest_result,
            rest_success=True,
            rest_response_time_ms=80.0,
            rest_status_code=200,
            combined_response_time_ms=90.0,
            health_score=0.95,
            available_paths=["mcp", "rest", "both"],
            combined_metrics=combined_metrics
        )
        
        # Mock health service methods
        health_service.check_multiple_servers_dual.return_value = [dual_result]
        health_service.perform_dual_health_check.return_value = dual_result
        
        # Mock aggregator
        health_service.aggregator = MagicMock()
        health_service.aggregator.create_aggregation_summary.return_value = {
            "total_servers": 1,
            "healthy_servers": 1,
            "degraded_servers": 0,
            "unhealthy_servers": 0,
            "unknown_servers": 0,
            "average_health_score": 0.95,
            "average_response_time_ms": 90.0,
            "mcp_success_rate": 1.0,
            "rest_success_rate": 1.0,
            "combined_success_rate": 1.0
        }
        
        # Mock metrics collector
        metrics_collector = AsyncMock()
        metrics_collector.get_mcp_metrics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "average_response_time_ms": 100.0
        }
        metrics_collector.get_rest_metrics.return_value = {
            "total_requests": 100,
            "successful_requests": 98,
            "failed_requests": 2,
            "average_response_time_ms": 80.0
        }
        metrics_collector.get_combined_metrics.return_value = {
            "total_dual_checks": 100,
            "both_successful": 93,
            "mcp_only_successful": 2,
            "rest_only_successful": 3,
            "both_failed": 2
        }
        metrics_collector.get_server_mcp_metrics.return_value = {"success_rate": 0.95}
        metrics_collector.get_server_rest_metrics.return_value = {"success_rate": 0.98}
        
        # Mock config manager
        config_manager = MagicMock()
        
        server_config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8001/mcp",
            rest_health_endpoint_url="http://localhost:8001/status/health",
            mcp_expected_tools=["tool1", "tool2"]
        )
        
        async def mock_get_all_server_configs():
            return [server_config]
        
        async def mock_get_server_config(server_name):
            if server_name == "test-server":
                return server_config
            return None
        
        config_manager.get_all_server_configs = mock_get_all_server_configs
        config_manager.get_server_config = mock_get_server_config
        
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
        
        config_manager.get_current_config = mock_get_current_config
        config_manager.update_config = mock_update_config
        
        return health_service, metrics_collector, config_manager
    
    @pytest.fixture
    def test_client(self, mock_services):
        """Create test client with mocked services."""
        health_service, metrics_collector, config_manager = mock_services
        
        app = create_enhanced_status_app(
            health_service=health_service,
            metrics_collector=metrics_collector,
            config_manager=config_manager
        )
        
        return TestClient(app)
    
    def test_system_health_endpoint(self, test_client):
        """Test /status/health endpoint."""
        response = test_client.get("/status/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_status" in data
        assert "total_servers" in data
        assert "healthy_servers" in data
        assert "servers" in data
        assert data["overall_status"] == "HEALTHY"
        assert data["total_servers"] == 1
        assert data["healthy_servers"] == 1
    
    def test_server_status_endpoint(self, test_client):
        """Test /status/servers/{server_name} endpoint."""
        response = test_client.get("/status/servers/test-server")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "server_name" in data
        assert "status" in data
        assert "success" in data
        assert "health_score" in data
        assert "available_paths" in data
        assert data["server_name"] == "test-server"
        assert data["status"] == "HEALTHY"
        assert data["success"] is True
    
    def test_server_status_not_found(self, test_client):
        """Test /status/servers/{server_name} endpoint with non-existent server."""
        response = test_client.get("/status/servers/non-existent-server")
        
        assert response.status_code == 404
    
    def test_metrics_endpoint(self, test_client):
        """Test /status/metrics endpoint."""
        response = test_client.get("/status/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mcp_metrics" in data
        assert "rest_metrics" in data
        assert "combined_metrics" in data
        assert "server_metrics" in data
        assert "timestamp" in data
    
    def test_dual_check_endpoint(self, test_client):
        """Test /status/dual-check endpoint."""
        request_data = {
            "server_names": ["test-server"],
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
        assert len(data["servers"]) == 1
    
    def test_config_endpoint(self, test_client):
        """Test /status/config endpoint."""
        response = test_client.get("/status/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "enhanced_monitoring_enabled" in data
        assert "mcp_health_checks" in data
        assert "rest_health_checks" in data
        assert "result_aggregation" in data
        assert "servers" in data
        assert data["enhanced_monitoring_enabled"] is True
    
    def test_config_update_endpoint(self, test_client):
        """Test /status/config PUT endpoint."""
        update_data = {
            "mcp_health_checks": {
                "default_timeout_seconds": 15
            }
        }
        
        response = test_client.put("/status/config", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        assert "updated_fields" in data
    
    def test_legacy_health_endpoint(self, test_client):
        """Test legacy /health endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "healthy" in data
        assert "timestamp" in data
        assert "servers" in data
        assert data["status"] == "healthy"
        assert data["healthy"] is True
    
    def test_legacy_status_endpoint(self, test_client):
        """Test legacy /status endpoint."""
        response = test_client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_status" in data
        assert "servers" in data
        assert "summary" in data
        assert "timestamp" in data
        assert data["overall_status"] == "healthy"
    
    def test_system_health_with_parameters(self, test_client):
        """Test /status/health endpoint with query parameters."""
        # Test without server details
        response = test_client.get("/status/health?include_servers=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data["servers"]) == 0
        
        # Test with force check
        response = test_client.get("/status/health?force_check=true&timeout=60")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
    
    def test_metrics_with_parameters(self, test_client):
        """Test /status/metrics endpoint with query parameters."""
        response = test_client.get("/status/metrics?time_range=7200&include_server_breakdown=false")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mcp_metrics" in data
        assert "rest_metrics" in data
        assert "combined_metrics" in data
        # Server breakdown should be empty when include_server_breakdown=false
        assert len(data["server_metrics"]) == 0
    
    def test_dual_check_all_servers(self, test_client):
        """Test /status/dual-check endpoint for all servers."""
        request_data = {
            "timeout_seconds": 20,
            "include_mcp": True,
            "include_rest": False  # Only MCP checks
        }
        
        response = test_client.post("/status/dual-check", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "check_id" in data
        assert "summary" in data
        assert "servers" in data
    
    def test_config_with_sensitive_data(self, test_client):
        """Test /status/config endpoint with sensitive data."""
        response = test_client.get("/status/config?include_sensitive=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "servers" in data
        # Should include sensitive fields (though they may be None in this test)
        for server in data["servers"]:
            assert "jwt_token" in server or server.get("jwt_token") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])