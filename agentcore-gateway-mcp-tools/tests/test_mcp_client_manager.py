"""
Unit tests for MCP Client Manager.

Tests connection management, retry logic, health monitoring, and error handling.
"""

import asyncio
import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import httpx
import pytest_httpx

from services.mcp_client_manager import (
    MCPClientManager,
    MCPConnectionPool,
    MCPServerConfig,
    MCPServerHealth,
    MCPServerStatus,
    get_mcp_client_manager,
    shutdown_mcp_client_manager
)


class TestMCPConnectionPool:
    """Test cases for MCP connection pool."""
    
    @pytest_asyncio.fixture
    async def connection_pool(self):
        """Create a connection pool for testing."""
        pool = MCPConnectionPool(max_connections=5, max_keepalive=2)
        yield pool
        await pool.close_all()
    
    @pytest.mark.asyncio
    async def test_get_client_creates_new_client(self, connection_pool):
        """Test that get_client creates a new HTTP client."""
        server_url = "http://test-server:8080"
        
        client = await connection_pool.get_client(server_url)
        
        assert isinstance(client, httpx.AsyncClient)
        assert client.base_url == server_url
        assert server_url in connection_pool._clients
    
    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self, connection_pool):
        """Test that get_client reuses existing HTTP client."""
        server_url = "http://test-server:8080"
        
        client1 = await connection_pool.get_client(server_url)
        client2 = await connection_pool.get_client(server_url)
        
        assert client1 is client2
        assert len(connection_pool._clients) == 1
    
    @pytest.mark.asyncio
    async def test_close_client_removes_specific_client(self, connection_pool):
        """Test that close_client removes a specific client."""
        server_url1 = "http://test-server1:8080"
        server_url2 = "http://test-server2:8080"
        
        await connection_pool.get_client(server_url1)
        await connection_pool.get_client(server_url2)
        
        assert len(connection_pool._clients) == 2
        
        await connection_pool.close_client(server_url1)
        
        assert len(connection_pool._clients) == 1
        assert server_url1 not in connection_pool._clients
        assert server_url2 in connection_pool._clients
    
    @pytest.mark.asyncio
    async def test_close_all_removes_all_clients(self, connection_pool):
        """Test that close_all removes all clients."""
        await connection_pool.get_client("http://server1:8080")
        await connection_pool.get_client("http://server2:8080")
        
        assert len(connection_pool._clients) == 2
        
        await connection_pool.close_all()
        
        assert len(connection_pool._clients) == 0


class TestMCPClientManager:
    """Test cases for MCP Client Manager."""
    
    @pytest_asyncio.fixture
    async def client_manager(self):
        """Create an MCP client manager for testing."""
        manager = MCPClientManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('services.mcp_client_manager.get_settings') as mock:
            settings = MagicMock()
            settings.mcp.search_server_url = "http://search-server:8080"
            settings.mcp.reasoning_server_url = "http://reasoning-server:8080"
            settings.mcp.connection_timeout = 30
            settings.mcp.max_retries = 3
            settings.mcp.retry_delay = 1.0
            mock.return_value = settings
            yield settings
    
    def test_setup_servers_configures_default_servers(self, mock_settings):
        """Test that _setup_servers configures default MCP servers."""
        manager = MCPClientManager()
        
        assert "restaurant-search" in manager.servers
        assert "restaurant-reasoning" in manager.servers
        
        search_config = manager.servers["restaurant-search"]
        assert search_config.name == "restaurant-search"
        assert search_config.url == "http://search-server:8080"
        assert "search_restaurants_by_district" in search_config.tools
        assert "search_restaurants_by_meal_type" in search_config.tools
        assert "search_restaurants_combined" in search_config.tools
        
        reasoning_config = manager.servers["restaurant-reasoning"]
        assert reasoning_config.name == "restaurant-reasoning"
        assert reasoning_config.url == "http://reasoning-server:8080"
        assert "recommend_restaurants" in reasoning_config.tools
        assert "analyze_restaurant_sentiment" in reasoning_config.tools
    
    @pytest.mark.asyncio
    async def test_start_initializes_health_monitoring(self, mock_settings):
        """Test that start() initializes health monitoring."""
        manager = MCPClientManager()
        
        with patch.object(manager, 'check_all_servers_health', new_callable=AsyncMock) as mock_health:
            await manager.start()
            
            assert manager._health_check_task is not None
            assert not manager._health_check_task.done()
            mock_health.assert_called_once()
            
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stop_cleans_up_resources(self, mock_settings):
        """Test that stop() cleans up all resources."""
        manager = MCPClientManager()
        await manager.start()
        
        # Verify resources are initialized
        assert manager._health_check_task is not None
        assert not manager._health_check_task.done()
        
        await manager.stop()
        
        # Verify resources are cleaned up
        assert manager._health_check_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_success(self, client_manager, httpx_mock):
        """Test successful MCP tool call."""
        # Mock successful response
        httpx_mock.add_response(
            method="POST",
            url="http://search-server:8080/invoke",
            json={"success": True, "data": {"restaurants": []}},
            status_code=200
        )
        
        result = await client_manager.call_mcp_tool(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_district",
            parameters={"districts": ["Central district"]}
        )
        
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_with_user_context(self, client_manager, httpx_mock):
        """Test MCP tool call with user context and authentication."""
        # Mock successful response
        httpx_mock.add_response(
            method="POST",
            url="http://search-server:8080/invoke",
            json={"success": True, "data": {"restaurants": []}},
            status_code=200
        )
        
        user_context = {
            "user_id": "test-user",
            "token": "test-token"
        }
        
        result = await client_manager.call_mcp_tool(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_district",
            parameters={"districts": ["Central district"]},
            user_context=user_context
        )
        
        assert result["success"] is True
        
        # Verify request was made with correct headers
        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_unknown_server(self, client_manager):
        """Test MCP tool call with unknown server raises ValueError."""
        with pytest.raises(ValueError, match="Unknown MCP server: unknown-server"):
            await client_manager.call_mcp_tool(
                server_name="unknown-server",
                tool_name="some_tool",
                parameters={}
            )
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_unknown_tool(self, client_manager):
        """Test MCP tool call with unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Tool 'unknown_tool' not available"):
            await client_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="unknown_tool",
                parameters={}
            )
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_http_error_retry(self, client_manager, httpx_mock):
        """Test MCP tool call retries on HTTP errors."""
        # Mock server error responses
        for _ in range(3):  # Will retry 3 times
            httpx_mock.add_response(
                method="POST",
                url="http://search-server:8080/invoke",
                status_code=500,
                text="Internal Server Error"
            )
        
        with pytest.raises(httpx.RequestError, match="MCP server returned HTTP 500"):
            await client_manager.call_mcp_tool(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_district",
                parameters={"districts": ["Central district"]}
            )
        
        # Verify all retry attempts were made
        assert len(httpx_mock.get_requests()) == 3
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_timeout_retry(self, client_manager):
        """Test MCP tool call retries on timeout."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_get_client.return_value = mock_client
            
            with pytest.raises(httpx.TimeoutException):
                await client_manager.call_mcp_tool(
                    server_name="restaurant-search",
                    tool_name="search_restaurants_by_district",
                    parameters={"districts": ["Central district"]}
                )
            
            # Verify retry attempts were made
            assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_check_server_health_success(self, client_manager, httpx_mock):
        """Test successful server health check."""
        httpx_mock.add_response(
            method="GET",
            url="http://search-server:8080/health",
            json={"status": "healthy"},
            status_code=200
        )
        
        health = await client_manager.check_server_health("restaurant-search")
        
        assert health.status == MCPServerStatus.HEALTHY
        assert health.response_time is not None
        assert health.response_time > 0
        assert health.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_check_server_health_failure(self, client_manager, httpx_mock):
        """Test server health check failure."""
        httpx_mock.add_response(
            method="GET",
            url="http://search-server:8080/health",
            status_code=503,
            text="Service Unavailable"
        )
        
        health = await client_manager.check_server_health("restaurant-search")
        
        assert health.status == MCPServerStatus.UNHEALTHY
        assert health.error_message == "HTTP 503"
        assert health.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_check_server_health_connection_error(self, client_manager):
        """Test server health check with connection error."""
        with patch.object(client_manager.connection_pool, 'get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            mock_get_client.return_value = mock_client
            
            health = await client_manager.check_server_health("restaurant-search")
            
            assert health.status == MCPServerStatus.UNHEALTHY
            assert "Connection failed" in health.error_message
            assert health.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_check_all_servers_health(self, client_manager, httpx_mock):
        """Test checking health of all servers."""
        # Mock health responses for both servers
        httpx_mock.add_response(
            method="GET",
            url="http://search-server:8080/health",
            json={"status": "healthy"},
            status_code=200
        )
        httpx_mock.add_response(
            method="GET",
            url="http://reasoning-server:8080/health",
            json={"status": "healthy"},
            status_code=200
        )
        
        health_results = await client_manager.check_all_servers_health()
        
        assert len(health_results) == 2
        assert "restaurant-search" in health_results
        assert "restaurant-reasoning" in health_results
        assert health_results["restaurant-search"].status == MCPServerStatus.HEALTHY
        assert health_results["restaurant-reasoning"].status == MCPServerStatus.HEALTHY
    
    def test_get_available_tools_all_servers(self, client_manager):
        """Test getting available tools for all servers."""
        tools = client_manager.get_available_tools()
        
        assert "restaurant-search" in tools
        assert "restaurant-reasoning" in tools
        assert "search_restaurants_by_district" in tools["restaurant-search"]
        assert "recommend_restaurants" in tools["restaurant-reasoning"]
    
    def test_get_available_tools_specific_server(self, client_manager):
        """Test getting available tools for a specific server."""
        tools = client_manager.get_available_tools("restaurant-search")
        
        assert len(tools) == 1
        assert "restaurant-search" in tools
        assert "search_restaurants_by_district" in tools["restaurant-search"]
    
    def test_get_available_tools_unknown_server(self, client_manager):
        """Test getting available tools for unknown server returns empty dict."""
        tools = client_manager.get_available_tools("unknown-server")
        
        assert tools == {}
    
    def test_is_server_healthy(self, client_manager):
        """Test checking if a server is healthy."""
        # Initially unknown status
        assert not client_manager.is_server_healthy("restaurant-search")
        
        # Set healthy status
        client_manager.health_status["restaurant-search"] = MCPServerHealth(
            status=MCPServerStatus.HEALTHY,
            last_check=time.time()
        )
        
        assert client_manager.is_server_healthy("restaurant-search")
        
        # Set unhealthy status
        client_manager.health_status["restaurant-search"] = MCPServerHealth(
            status=MCPServerStatus.UNHEALTHY,
            last_check=time.time()
        )
        
        assert not client_manager.is_server_healthy("restaurant-search")
    
    def test_get_healthy_servers(self, client_manager):
        """Test getting list of healthy servers."""
        # Set mixed health statuses
        client_manager.health_status["restaurant-search"] = MCPServerHealth(
            status=MCPServerStatus.HEALTHY,
            last_check=time.time()
        )
        client_manager.health_status["restaurant-reasoning"] = MCPServerHealth(
            status=MCPServerStatus.UNHEALTHY,
            last_check=time.time()
        )
        
        healthy_servers = client_manager.get_healthy_servers()
        
        assert len(healthy_servers) == 1
        assert "restaurant-search" in healthy_servers
        assert "restaurant-reasoning" not in healthy_servers


class TestGlobalMCPClientManager:
    """Test cases for global MCP client manager functions."""
    
    @pytest.mark.asyncio
    async def test_get_mcp_client_manager_singleton(self):
        """Test that get_mcp_client_manager returns singleton instance."""
        with patch('services.mcp_client_manager.MCPClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            manager1 = await get_mcp_client_manager()
            manager2 = await get_mcp_client_manager()
            
            assert manager1 is manager2
            mock_manager_class.assert_called_once()
            mock_manager.start.assert_called_once()
            
            await shutdown_mcp_client_manager()
    
    @pytest.mark.asyncio
    async def test_shutdown_mcp_client_manager(self):
        """Test that shutdown_mcp_client_manager properly cleans up."""
        with patch('services.mcp_client_manager.MCPClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            # Get manager instance
            await get_mcp_client_manager()
            
            # Shutdown manager
            await shutdown_mcp_client_manager()
            
            mock_manager.stop.assert_called_once()
            
            # Verify new instance is created after shutdown
            await get_mcp_client_manager()
            assert mock_manager_class.call_count == 2


@pytest.mark.asyncio
async def test_mcp_server_config_dataclass():
    """Test MCPServerConfig dataclass functionality."""
    config = MCPServerConfig(
        name="test-server",
        url="http://test:8080",
        timeout=60,
        max_retries=5,
        tools=["tool1", "tool2"]
    )
    
    assert config.name == "test-server"
    assert config.url == "http://test:8080"
    assert config.timeout == 60
    assert config.max_retries == 5
    assert config.tools == ["tool1", "tool2"]
    assert config.health_check_path == "/health"  # default value


@pytest.mark.asyncio
async def test_mcp_server_health_dataclass():
    """Test MCPServerHealth dataclass functionality."""
    health = MCPServerHealth(
        status=MCPServerStatus.HEALTHY,
        last_check=time.time(),
        response_time=0.123,
        consecutive_failures=0
    )
    
    assert health.status == MCPServerStatus.HEALTHY
    assert health.response_time == 0.123
    assert health.consecutive_failures == 0
    assert health.error_message is None  # default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])