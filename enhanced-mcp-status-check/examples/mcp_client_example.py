"""
Example usage of MCP Health Check Client

This example demonstrates how to use the MCP Health Check Client
to perform health checks on MCP servers.
"""

import asyncio
import json
from datetime import datetime

from models.dual_health_models import EnhancedServerConfig
from services.mcp_health_check_client import MCPHealthCheckClient


async def example_mcp_health_check():
    """Example of performing MCP health check."""
    
    # Configure server for health check
    server_config = EnhancedServerConfig(
        server_name="example-mcp-server",
        mcp_endpoint_url="http://localhost:8080/mcp",
        rest_health_endpoint_url="http://localhost:8080/health",
        mcp_enabled=True,
        mcp_timeout_seconds=10,
        mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
        mcp_retry_attempts=3,
        jwt_token="your-jwt-token-here",  # Optional
        auth_headers={"X-API-Key": "your-api-key"}  # Optional
    )
    
    # Perform health check
    async with MCPHealthCheckClient() as client:
        print(f"Performing MCP health check for {server_config.server_name}...")
        
        result = await client.perform_mcp_health_check(server_config)
        
        print(f"\nHealth Check Results:")
        print(f"Server: {result.server_name}")
        print(f"Success: {result.success}")
        print(f"Response Time: {result.response_time_ms:.2f}ms")
        print(f"Tools Count: {result.tools_count}")
        print(f"Expected Tools Found: {result.expected_tools_found}")
        print(f"Missing Tools: {result.missing_tools}")
        
        if result.connection_error:
            print(f"Connection Error: {result.connection_error}")
        
        if result.mcp_error:
            print(f"MCP Error: {result.mcp_error}")
        
        if result.validation_result:
            print(f"Validation Valid: {result.validation_result.is_valid}")
            print(f"Validation Errors: {result.validation_result.validation_errors}")
        
        # Print full result as JSON
        print(f"\nFull Result JSON:")
        print(result.to_json())


async def example_multiple_servers():
    """Example of checking multiple servers concurrently."""
    
    servers = [
        EnhancedServerConfig(
            server_name="restaurant-search-mcp",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/health",
            mcp_expected_tools=["search_restaurants_by_district"]
        ),
        EnhancedServerConfig(
            server_name="restaurant-reasoning-mcp",
            mcp_endpoint_url="http://localhost:8081/mcp",
            rest_health_endpoint_url="http://localhost:8081/health",
            mcp_expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"]
        ),
        EnhancedServerConfig(
            server_name="mbti-travel-assistant-mcp",
            mcp_endpoint_url="http://localhost:8082/mcp",
            rest_health_endpoint_url="http://localhost:8082/health",
            mcp_expected_tools=["get_mbti_recommendations"]
        )
    ]
    
    async with MCPHealthCheckClient() as client:
        print("Performing health checks for multiple servers...")
        
        results = await client.check_multiple_servers_mcp(
            server_configs=servers,
            max_concurrent=3
        )
        
        print(f"\nResults for {len(results)} servers:")
        for result in results:
            status = "✅ HEALTHY" if result.success else "❌ UNHEALTHY"
            print(f"{status} {result.server_name} ({result.response_time_ms:.2f}ms)")
            if not result.success and result.connection_error:
                print(f"   Error: {result.connection_error}")


async def example_custom_validation():
    """Example of custom tools validation."""
    
    async with MCPHealthCheckClient() as client:
        # Create a custom MCP request
        request = client.create_mcp_request("custom-request-id")
        print(f"Custom MCP Request:")
        print(request.to_json())
        
        # Example response validation
        sample_response_data = {
            "jsonrpc": "2.0",
            "id": "custom-request-id",
            "result": {
                "tools": [
                    {
                        "name": "search_restaurants",
                        "description": "Search for restaurants by criteria",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "district": {"type": "string"}
                            }
                        }
                    },
                    {
                        "name": "recommend_restaurants",
                        "description": "Get restaurant recommendations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "preferences": {"type": "object"}
                            }
                        }
                    }
                ]
            }
        }
        
        from models.dual_health_models import MCPToolsListResponse
        response = MCPToolsListResponse.from_dict(sample_response_data)
        
        # Validate with expected tools
        validation_result = client.validate_tools_list_response(
            response=response,
            expected_tools=["search_restaurants", "recommend_restaurants", "missing_tool"]
        )
        
        print(f"\nValidation Results:")
        print(f"Valid: {validation_result.is_valid}")
        print(f"Tools Count: {validation_result.tools_count}")
        print(f"Expected Tools Found: {validation_result.expected_tools_found}")
        print(f"Missing Tools: {validation_result.missing_tools}")
        print(f"Validation Errors: {validation_result.validation_errors}")


async def main():
    """Run all examples."""
    print("=== MCP Health Check Client Examples ===\n")
    
    try:
        print("1. Single Server Health Check:")
        await example_mcp_health_check()
        print("\n" + "="*50 + "\n")
        
        print("2. Multiple Servers Health Check:")
        await example_multiple_servers()
        print("\n" + "="*50 + "\n")
        
        print("3. Custom Validation Example:")
        await example_custom_validation()
        
    except Exception as e:
        print(f"Example failed with error: {e}")
        print("Note: These examples require actual MCP servers to be running.")
        print("For testing purposes, the servers are expected at localhost:8080-8082")


if __name__ == "__main__":
    asyncio.run(main())