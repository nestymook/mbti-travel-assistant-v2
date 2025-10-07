#!/usr/bin/env python3
"""
Test to check what districts and meal types are available in the restaurant data.
"""

import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_available_data():
    """Test what districts and meal types are available."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["restaurant-search-mcp/restaurant_mcp_server.py"],
        env={"REQUIRE_AUTHENTICATION": "false", "PYTHONPATH": "restaurant-search-mcp"}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                logger.info("🔍 Testing available districts and meal types...")
                
                # Test some common district names
                test_districts = [
                    "Central",
                    "Central district", 
                    "Admiralty",
                    "Causeway Bay",
                    "Tsim Sha Tsui",
                    "Wan Chai"
                ]
                
                logger.info("\n--- Testing District Names ---")
                for district in test_districts:
                    try:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"districts": [district]}
                        )
                        
                        if result.content:
                            content = result.content[0].text
                            data = json.loads(content)
                            
                            if data.get('success'):
                                count = len(data.get('restaurants', []))
                                logger.info(f"✅ '{district}': {count} restaurants")
                                
                                # Show first restaurant as example
                                if count > 0:
                                    first_restaurant = data['restaurants'][0]
                                    logger.info(f"   Example: {first_restaurant.get('name')} - {first_restaurant.get('mealType', [])}")
                            else:
                                error = data.get('error', {}).get('message', 'Unknown error')
                                logger.info(f"❌ '{district}': {error}")
                    except Exception as e:
                        logger.info(f"❌ '{district}': Error - {e}")
                
                # Test meal types
                test_meal_types = ["breakfast", "lunch", "dinner"]
                
                logger.info("\n--- Testing Meal Types ---")
                for meal_type in test_meal_types:
                    try:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"meal_types": [meal_type]}
                        )
                        
                        if result.content:
                            content = result.content[0].text
                            data = json.loads(content)
                            
                            if data.get('success'):
                                count = len(data.get('restaurants', []))
                                logger.info(f"✅ '{meal_type}': {count} restaurants")
                            else:
                                error = data.get('error', {}).get('message', 'Unknown error')
                                logger.info(f"❌ '{meal_type}': {error}")
                    except Exception as e:
                        logger.info(f"❌ '{meal_type}': Error - {e}")
                
                # Try to find a working district and show detailed restaurant info
                logger.info("\n--- Finding Working District ---")
                for district in test_districts:
                    try:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            {"districts": [district]}
                        )
                        
                        if result.content:
                            content = result.content[0].text
                            data = json.loads(content)
                            
                            if data.get('success') and len(data.get('restaurants', [])) > 0:
                                restaurants = data['restaurants']
                                logger.info(f"\n🎉 Found {len(restaurants)} restaurants in '{district}'!")
                                
                                # Show detailed info for first few restaurants
                                for i, restaurant in enumerate(restaurants[:3]):
                                    logger.info(f"\n  Restaurant {i+1}:")
                                    logger.info(f"    Name: {restaurant.get('name')}")
                                    logger.info(f"    District: {restaurant.get('district')}")
                                    logger.info(f"    Meal Types: {restaurant.get('mealType', [])}")
                                    logger.info(f"    Address: {restaurant.get('address', 'N/A')}")
                                    logger.info(f"    Price Range: {restaurant.get('priceRange', 'N/A')}")
                                    
                                    sentiment = restaurant.get('sentiment', {})
                                    likes = sentiment.get('likes', 0)
                                    dislikes = sentiment.get('dislikes', 0)
                                    neutral = sentiment.get('neutral', 0)
                                    logger.info(f"    Sentiment: {likes} likes, {dislikes} dislikes, {neutral} neutral")
                                
                                return True
                    except Exception as e:
                        continue
                
                logger.info("❌ No working districts found with restaurant data")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    logger.info("🚀 Testing Available Districts and Meal Types")
    logger.info("="*60)
    
    success = await test_available_data()
    
    if success:
        logger.info("\n✅ Found working restaurant data!")
        return 0
    else:
        logger.error("\n❌ No restaurant data found!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)