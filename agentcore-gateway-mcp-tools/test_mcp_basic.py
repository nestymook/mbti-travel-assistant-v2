"""
Basic test for MCP Client Manager functionality.
"""

import asyncio
from services.mcp_client_manager import MCPClientManager, MCPServerStatus, MCPConnectionPool


async def test_connection_pool():
    """Test connection pool basic functionality."""
    print("Testing MCPConnectionPool...")
    
    pool = MCPConnectionPool(max_connections=5, max_keepalive=2)
    
    # Test creating clients
    client1 = await pool.get_client("http://test-server:8080")
    client2 = await pool.get_client("http://test-server:8080")
    
    # Should reuse the same client
    assert client1 is client2
    print("✓ Connection pool reuses clients correctly")
    
    # Test different server
    client3 = await pool.get_client("http://other-server:8080")
    assert client3 is not client1
    print("✓ Connection pool creates different clients for different servers")
    
    # Cleanup
    await pool.close_all()
    print("✓ Connection pool cleanup successful")


async def test_mcp_client_manager():
    """Test MCP client manager basic functionality."""
    print("\nTesting MCPClientManager...")
    
    manager = MCPClientManager()
    
    # Test server configuration
    assert "restaurant-search" in manager.servers
    assert "restaurant-reasoning" in manager.servers
    print("✓ MCP servers configured correctly")
    
    # Test available tools
    tools = manager.get_available_tools()
    assert "search_restaurants_by_district" in tools["restaurant-search"]
    assert "recommend_restaurants" in tools["restaurant-reasoning"]
    print("✓ Available tools configured correctly")
    
    # Test health status initialization
    assert len(manager.health_status) == 2
    for server_name in manager.servers:
        assert server_name in manager.health_status
        assert manager.health_status[server_name].status == MCPServerStatus.UNKNOWN
    print("✓ Health status initialized correctly")
    
    # Test server health check methods
    assert not manager.is_server_healthy("restaurant-search")  # Initially unknown
    healthy_servers = manager.get_healthy_servers()
    assert len(healthy_servers) == 0  # None are healthy initially
    print("✓ Health check methods work correctly")
    
    print("✓ MCP client manager basic functionality verified")


async def test_retry_logic():
    """Test that retry logic is properly configured."""
    print("\nTesting retry configuration...")
    
    manager = MCPClientManager()
    
    # Test that tenacity is properly imported and configured
    from tenacity import retry
    assert hasattr(manager.call_mcp_tool, '__wrapped__')  # Decorated with retry
    print("✓ Retry logic is properly configured")


async def main():
    """Run all basic tests."""
    print("Running MCP Client Manager Basic Tests")
    print("=" * 50)
    
    try:
        await test_connection_pool()
        await test_mcp_client_manager()
        await test_retry_logic()
        
        print("\n" + "=" * 50)
        print("✅ All basic tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())