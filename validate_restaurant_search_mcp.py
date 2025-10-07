#!/usr/bin/env python3
"""
Quick validation script for restaurant-search-mcp server.
"""

import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_mcp_server():
    """Validate that the restaurant-search-mcp server is working."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["restaurant-search-mcp/restaurant_mcp_server.py"],
        env={"REQUIRE_AUTHENTICATION": "false", "PYTHONPATH": "restaurant-search-mcp"}
    )
    
    try:
        logger.info("🔍 Connecting to restaurant-search-mcp server...")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                logger.info("✅ Successfully connected to MCP server")
                
                # List available tools
                tools = await session.list_tools()
                logger.info(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
                
                # Check for expected tools
                expected_tools = [
                    "search_restaurants_by_district",
                    "search_restaurants_by_meal_type", 
                    "search_restaurants_combined"
                ]
                
                found_tools = [tool.name for tool in tools.tools]
                
                for expected_tool in expected_tools:
                    if expected_tool in found_tools:
                        logger.info(f"✅ Found expected tool: {expected_tool}")
                    else:
                        logger.error(f"❌ Missing expected tool: {expected_tool}")
                
                # Test the combined search tool specifically
                if "search_restaurants_combined" in found_tools:
                    logger.info("\n🧪 Testing search_restaurants_combined tool...")
                    
                    # Simple test
                    result = await session.call_tool(
                        "search_restaurants_combined",
                        {"districts": ["Central district"]}
                    )
                    
                    if result.content:
                        content = result.content[0].text
                        data = json.loads(content)
                        
                        if data.get('success'):
                            restaurant_count = len(data.get('restaurants', []))
                            logger.info(f"✅ Tool test successful: Found {restaurant_count} restaurants")
                            return True
                        else:
                            logger.error(f"❌ Tool returned error: {data.get('error', 'Unknown error')}")
                            return False
                    else:
                        logger.error("❌ No content returned from tool")
                        return False
                else:
                    logger.error("❌ search_restaurants_combined tool not found")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run validation."""
    logger.info("🚀 Validating Restaurant Search MCP Server")
    logger.info("="*50)
    
    success = await validate_mcp_server()
    
    if success:
        logger.info("\n✅ Validation successful! Server is ready for testing.")
        return 0
    else:
        logger.error("\n❌ Validation failed!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)