#!/usr/bin/env python3
"""
Simple test for search_restaurants_combined MCP tool.
"""

import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_combined_search():
    """Test the search_restaurants_combined tool with a simple example."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["restaurant-search-mcp/restaurant_mcp_server.py"],
        env={"REQUIRE_AUTHENTICATION": "false", "PYTHONPATH": "restaurant-search-mcp"}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                logger.info("🔍 Testing search_restaurants_combined tool...")
                
                # Test 1: Search by district only
                logger.info("\n--- Test 1: Search by district (Central district) ---")
                result1 = await session.call_tool(
                    "search_restaurants_combined",
                    {"districts": ["Central district"]}
                )
                
                if result1.content:
                    content1 = result1.content[0].text
                    data1 = json.loads(content1)
                    logger.info(f"✅ Found {len(data1.get('restaurants', []))} restaurants in Central district")
                    
                    # Show first restaurant as example
                    if data1.get('restaurants'):
                        first_restaurant = data1['restaurants'][0]
                        logger.info(f"   Example: {first_restaurant.get('name')} - {first_restaurant.get('meal_type', [])}")
                
                # Test 2: Search by meal type only
                logger.info("\n--- Test 2: Search by meal type (lunch) ---")
                result2 = await session.call_tool(
                    "search_restaurants_combined",
                    {"meal_types": ["lunch"]}
                )
                
                if result2.content:
                    content2 = result2.content[0].text
                    data2 = json.loads(content2)
                    logger.info(f"✅ Found {len(data2.get('restaurants', []))} restaurants serving lunch")
                
                # Test 3: Search by both district and meal type
                logger.info("\n--- Test 3: Search by district AND meal type ---")
                result3 = await session.call_tool(
                    "search_restaurants_combined",
                    {
                        "districts": ["Central district"],
                        "meal_types": ["lunch"]
                    }
                )
                
                if result3.content:
                    content3 = result3.content[0].text
                    data3 = json.loads(content3)
                    restaurants = data3.get('restaurants', [])
                    logger.info(f"✅ Found {len(restaurants)} restaurants in Central district serving lunch")
                    
                    # Show details of found restaurants
                    for i, restaurant in enumerate(restaurants[:5]):  # Show first 5
                        name = restaurant.get('name', 'Unknown')
                        district = restaurant.get('district', 'Unknown')
                        meal_types = restaurant.get('meal_type', [])
                        address = restaurant.get('address', 'No address')
                        logger.info(f"   {i+1}. {name}")
                        logger.info(f"      District: {district}")
                        logger.info(f"      Meal types: {meal_types}")
                        logger.info(f"      Address: {address}")
                    
                    if len(restaurants) > 5:
                        logger.info(f"   ... and {len(restaurants) - 5} more restaurants")
                
                logger.info("\n🎉 All tests completed successfully!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the simple test."""
    logger.info("🚀 Starting Simple Combined Search Test")
    logger.info("="*50)
    
    success = await test_combined_search()
    
    if success:
        logger.info("\n✅ Test completed successfully!")
        return 0
    else:
        logger.error("\n❌ Test failed!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)