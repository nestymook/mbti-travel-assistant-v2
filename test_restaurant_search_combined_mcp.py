#!/usr/bin/env python3
"""
Test script for the search_restaurants_combined MCP tool from restaurant-search-mcp server.

This script tests the combined search functionality that allows filtering by both
districts and meal types, or either one independently.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantSearchMCPTester:
    """Test class for restaurant search MCP tools."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["restaurant-search-mcp/restaurant_mcp_server.py"],
            env={"REQUIRE_AUTHENTICATION": "false", "PYTHONPATH": "restaurant-search-mcp"}
        )
    
    async def test_search_restaurants_combined(self):
        """Test the search_restaurants_combined MCP tool with various scenarios."""
        
        test_cases = [
            {
                "name": "Search by districts only",
                "params": {
                    "districts": ["Central district", "Admiralty"]
                },
                "description": "Should return restaurants from Central district and Admiralty"
            },
            {
                "name": "Search by meal types only", 
                "params": {
                    "meal_types": ["breakfast", "lunch"]
                },
                "description": "Should return restaurants serving breakfast or lunch"
            },
            {
                "name": "Search by both districts and meal types",
                "params": {
                    "districts": ["Central district"],
                    "meal_types": ["lunch"]
                },
                "description": "Should return restaurants in Central district that serve lunch"
            },
            {
                "name": "Search with multiple districts and meal types",
                "params": {
                    "districts": ["Central district", "Causeway Bay", "Admiralty"],
                    "meal_types": ["breakfast", "lunch", "dinner"]
                },
                "description": "Should return restaurants matching any district and any meal type"
            },
            {
                "name": "Search with single district",
                "params": {
                    "districts": ["Tsim Sha Tsui"]
                },
                "description": "Should return all restaurants in Tsim Sha Tsui"
            },
            {
                "name": "Search with single meal type",
                "params": {
                    "meal_types": ["dinner"]
                },
                "description": "Should return all restaurants serving dinner"
            },
            {
                "name": "Empty search (no parameters)",
                "params": {},
                "description": "Should return error or all restaurants"
            },
            {
                "name": "Invalid district",
                "params": {
                    "districts": ["NonExistentDistrict"]
                },
                "description": "Should handle invalid district gracefully"
            },
            {
                "name": "Invalid meal type",
                "params": {
                    "meal_types": ["invalid_meal"]
                },
                "description": "Should handle invalid meal type gracefully"
            }
        ]
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                logger.info(f"Available tools: {[tool.name for tool in tools.tools]}")
                
                # Check if search_restaurants_combined is available
                combined_tool = None
                for tool in tools.tools:
                    if tool.name == "search_restaurants_combined":
                        combined_tool = tool
                        break
                
                if not combined_tool:
                    logger.error("search_restaurants_combined tool not found!")
                    return False
                
                logger.info(f"Found tool: {combined_tool.name}")
                logger.info(f"Tool description: {combined_tool.description}")
                
                # Run test cases
                results = []
                for i, test_case in enumerate(test_cases, 1):
                    logger.info(f"\n--- Test Case {i}: {test_case['name']} ---")
                    logger.info(f"Description: {test_case['description']}")
                    logger.info(f"Parameters: {json.dumps(test_case['params'], indent=2)}")
                    
                    try:
                        result = await session.call_tool(
                            "search_restaurants_combined",
                            test_case['params']
                        )
                        
                        # Parse the result
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0].text if result.content else "No content"
                            try:
                                parsed_result = json.loads(content)
                                success = parsed_result.get('success', False)
                                restaurant_count = len(parsed_result.get('restaurants', []))
                                
                                logger.info(f"✅ Success: {success}")
                                logger.info(f"📊 Restaurant count: {restaurant_count}")
                                
                                if restaurant_count > 0:
                                    # Show first few restaurants as examples
                                    restaurants = parsed_result.get('restaurants', [])
                                    logger.info("📍 Sample restaurants:")
                                    for j, restaurant in enumerate(restaurants[:3]):
                                        name = restaurant.get('name', 'Unknown')
                                        district = restaurant.get('district', 'Unknown')
                                        meal_types = restaurant.get('meal_type', [])
                                        logger.info(f"  {j+1}. {name} ({district}) - {meal_types}")
                                    
                                    if restaurant_count > 3:
                                        logger.info(f"  ... and {restaurant_count - 3} more restaurants")
                                
                                results.append({
                                    'test_case': test_case['name'],
                                    'success': success,
                                    'restaurant_count': restaurant_count,
                                    'params': test_case['params']
                                })
                                
                            except json.JSONDecodeError:
                                logger.error(f"❌ Failed to parse JSON response: {content}")
                                results.append({
                                    'test_case': test_case['name'],
                                    'success': False,
                                    'error': 'JSON parse error',
                                    'params': test_case['params']
                                })
                        else:
                            logger.error("❌ No content in result")
                            results.append({
                                'test_case': test_case['name'],
                                'success': False,
                                'error': 'No content',
                                'params': test_case['params']
                            })
                            
                    except Exception as e:
                        logger.error(f"❌ Test failed with error: {e}")
                        results.append({
                            'test_case': test_case['name'],
                            'success': False,
                            'error': str(e),
                            'params': test_case['params']
                        })
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("TEST SUMMARY")
                logger.info("="*60)
                
                successful_tests = [r for r in results if r['success']]
                failed_tests = [r for r in results if not r['success']]
                
                logger.info(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
                logger.info(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
                
                if successful_tests:
                    logger.info("\n📊 Successful test results:")
                    for result in successful_tests:
                        count = result.get('restaurant_count', 0)
                        logger.info(f"  • {result['test_case']}: {count} restaurants")
                
                if failed_tests:
                    logger.info("\n❌ Failed test details:")
                    for result in failed_tests:
                        error = result.get('error', 'Unknown error')
                        logger.info(f"  • {result['test_case']}: {error}")
                
                return len(failed_tests) == 0

    async def test_tool_schema(self):
        """Test the tool schema and parameters."""
        logger.info("\n" + "="*60)
        logger.info("TESTING TOOL SCHEMA")
        logger.info("="*60)
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                
                for tool in tools.tools:
                    if tool.name == "search_restaurants_combined":
                        logger.info(f"Tool Name: {tool.name}")
                        logger.info(f"Description: {tool.description}")
                        
                        if hasattr(tool, 'inputSchema'):
                            schema = tool.inputSchema
                            logger.info(f"Input Schema: {json.dumps(schema, indent=2)}")
                            
                            # Validate schema structure
                            if 'properties' in schema:
                                properties = schema['properties']
                                logger.info("✅ Schema has properties")
                                
                                if 'districts' in properties:
                                    logger.info("✅ 'districts' parameter found")
                                    districts_schema = properties['districts']
                                    logger.info(f"   Districts schema: {districts_schema}")
                                
                                if 'meal_types' in properties:
                                    logger.info("✅ 'meal_types' parameter found")
                                    meal_types_schema = properties['meal_types']
                                    logger.info(f"   Meal types schema: {meal_types_schema}")
                            
                        return True
                        
        return False

    async def run_all_tests(self):
        """Run all tests for the search_restaurants_combined tool."""
        logger.info("🚀 Starting Restaurant Search Combined MCP Tool Tests")
        logger.info("="*60)
        
        try:
            # Test tool schema
            schema_success = await self.test_tool_schema()
            if not schema_success:
                logger.error("❌ Schema test failed")
                return False
            
            # Test functionality
            functionality_success = await self.test_search_restaurants_combined()
            if not functionality_success:
                logger.error("❌ Functionality tests failed")
                return False
            
            logger.info("\n🎉 All tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test function."""
    tester = RestaurantSearchMCPTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ All tests passed! The search_restaurants_combined tool is working correctly.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)