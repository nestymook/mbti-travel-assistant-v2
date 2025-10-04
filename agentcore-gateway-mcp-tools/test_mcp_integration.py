"""
Integration test for MCP Client Manager with health monitoring.
"""

import asyncio
import time
from unittest.mock import patch, AsyncMock
from services.mcp_client_manager import MCPClientManager, MCPServerStatus


async def test_health_monitoring():
    """Test health monitoring functionality."""
    print("Testing health monitoring...")
    
    manager = MCPClientManager()
    
    # Mock the HTTP client to simulate server responses
    with patch.object(manager.connection_pool, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Test successful health check
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        # Add a small delay to simulate network time
        async def mock_get(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms delay
            return mock_response
        
        mock_client.get = mock_get
        
        health = await manager.check_server_health("restaurant-search")
        
        assert health.status == MCPServerStatus.HEALTHY
        assert health.response_time is not None
        assert health.response_time > 0
        assert health.consecutive_failures == 0
        print("✓ Successful health check works correctly")
        
        # Test failed health check
        mock_response.status_code = 503
        
        async def mock_get_failed(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms delay
            return mock_response
        
        mock_client.get = mock_get_failed
        
        health = await manager.check_server_health("restaurant-search")
        
        assert health.status == MCPServerStatus.UNHEALTHY
        assert health.error_message == "HTTP 503"
        assert health.consecutive_failures == 1
        print("✓ Failed health check works correctly")
        
        # Test connection error
        async def mock_get_error(*args, **kwargs):
            raise Exception("Connection failed")
        
        mock_client.get = mock_get_error
        health = await manager.check_server_health("restaurant-search")
        
        assert health.status == MCPServerStatus.UNHEALTHY
        assert "Connection failed" in health.error_message
        assert health.consecutive_failures == 2
        print("✓ Connection error handling works correctly")


async def test_mcp_tool_call_validation():
    """Test MCP tool call validation."""
    print("\nTesting MCP tool call validation...")
    
    manager = MCPClientManager()
    
    # Test unknown server
    try:
        await manager.call_mcp_tool("unknown-server", "some_tool", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown MCP server" in str(e)
        print("✓ Unknown server validation works")
    
    # Test unknown tool
    try:
        await manager.call_mcp_tool("restaurant-search", "unknown_tool", {})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Tool 'unknown_tool' not available" in str(e)
        print("✓ Unknown tool validation works")


async def test_server_status_tracking():
    """Test server status tracking."""
    print("\nTesting server status tracking...")
    
    manager = MCPClientManager()
    
    # Initially no servers are healthy
    assert len(manager.get_healthy_servers()) == 0
    assert not manager.is_server_healthy("restaurant-search")
    
    # Manually set a server as healthy
    manager.health_status["restaurant-search"].status = MCPServerStatus.HEALTHY
    manager.health_status["restaurant-search"].last_check = time.time()
    
    assert manager.is_server_healthy("restaurant-search")
    healthy_servers = manager.get_healthy_servers()
    assert "restaurant-search" in healthy_servers
    assert len(healthy_servers) == 1
    print("✓ Server status tracking works correctly")


async def test_all_servers_health_check():
    """Test checking all servers health."""
    print("\nTesting all servers health check...")
    
    manager = MCPClientManager()
    
    with patch.object(manager.connection_pool, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        # Mock successful responses for both servers
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_get_all(*args, **kwargs):
            await asyncio.sleep(0.001)  # 1ms delay
            return mock_response
        
        mock_client.get = mock_get_all
        
        health_results = await manager.check_all_servers_health()
        
        assert len(health_results) == 2
        assert "restaurant-search" in health_results
        assert "restaurant-reasoning" in health_results
        
        for server_name, health in health_results.items():
            assert health.status == MCPServerStatus.HEALTHY
            assert health.response_time is not None
        
        print("✓ All servers health check works correctly")


async def main():
    """Run all integration tests."""
    print("Running MCP Client Manager Integration Tests")
    print("=" * 60)
    
    try:
        await test_health_monitoring()
        await test_mcp_tool_call_validation()
        await test_server_status_tracking()
        await test_all_servers_health_check()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())