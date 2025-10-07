#!/usr/bin/env python3
"""
Test script to verify district name normalization in the restaurant search MCP server.
"""

import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_district_normalization():
    """Test that district name normalization works correctly."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["restaurant-search-mcp/restaurant_mcp_server.py"],
        env={"REQUIRE_AUTHENTICATION": "false", "PYTHONPATH": "restaurant-search-mcp"}
    )
    
    # Test cases with various district name formats
    test_cases = [
        {
            "name": "Central (should normalize to Central district)",
            "districts": ["Central"],
            "expected_normalized": ["Central district"]
        },
        {
            "name": "Central district (should stay the same)",
            "districts": ["Central district"],
            "expected_normalized": ["Central district"]
        },
        {
            "name": "central (lowercase, should normalize)",
            "districts": ["central"],
            "expected_normalized": ["Central district"]
        },
        {
            "name": "Western (should normalize to Western district)",
            "districts": ["Western"],
            "expected_normalized": ["Western district"]
        },
        {
            "name": "western (lowercase, should normalize)",
            "districts": ["western"],
            "expected_normalized": ["Western district"]
        },
        {
            "name": "Multiple districts with mixed formats",
            "districts": ["Central", "Western", "Admiralty"],
            "expected_normalized": ["Central district", "Western district", "Admiralty"]
        },
        {
            "name": "Case variations",
            "districts": ["CENTRAL", "western", "Admiralty"],
            "expected_normalized": ["Central district", "Western district", "Admiralty"]
        }
    ]
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                logger.info("🧪 Testing District Name Normalization")
                logger.info("="*60)
                
                success_count = 0
                total_tests = len(test_cases)
                
                for i, test_case in enumerate(test_cases, 1):
                    logger.info(f"\n--- Test {i}: {test_case['name']} ---")
                    logger.info(f"Input districts: {test_case['districts']}")
                    logger.info(f"Expected normalized: {test_case['expected_normalized']}")
                    
                    try:
                        # Test with search_restaurants_by_district
                        result = await session.call_tool(
                            "search_restaurants_by_district",
                            {"districts": test_case['districts']}
                        )
                        
                        if result.content:
                            content = result.content[0].text
                            data = json.loads(content)
                            
                            if data.get('success'):
                                # Check if normalized districts are in the metadata
                                search_criteria = data.get('metadata', {}).get('search_criteria', {})
                                original_districts = search_criteria.get('districts', [])
                                normalized_districts = search_criteria.get('normalized_districts', [])
                                
                                logger.info(f"✅ Original districts in response: {original_districts}")
                                logger.info(f"✅ Normalized districts in response: {normalized_districts}")
                                
                                # Check if normalization worked as expected
                                if normalized_districts == test_case['expected_normalized']:
                                    logger.info(f"✅ Normalization SUCCESS: Got expected result")
                                    success_count += 1
                                else:
                                    logger.error(f"❌ Normalization FAILED: Expected {test_case['expected_normalized']}, got {normalized_districts}")
                                
                                # Show restaurant count
                                restaurant_count = len(data.get('restaurants', []))
                                logger.info(f"📊 Found {restaurant_count} restaurants")
                                
                                # Show first restaurant as example if any found
                                if restaurant_count > 0:
                                    first_restaurant = data['restaurants'][0]
                                    logger.info(f"   Example: {first_restaurant.get('name')} in {first_restaurant.get('district', 'Unknown district')}")
                            else:
                                error_msg = data.get('error', {}).get('message', 'Unknown error')
                                logger.error(f"❌ Search failed: {error_msg}")
                        else:
                            logger.error("❌ No content returned from tool")
                            
                    except Exception as e:
                        logger.error(f"❌ Test failed with exception: {e}")
                
                # Test with combined search as well
                logger.info(f"\n--- Testing Combined Search Normalization ---")
                try:
                    result = await session.call_tool(
                        "search_restaurants_combined",
                        {"districts": ["Central", "western"]}
                    )
                    
                    if result.content:
                        content = result.content[0].text
                        data = json.loads(content)
                        
                        if data.get('success'):
                            search_criteria = data.get('metadata', {}).get('search_criteria', {})
                            original_districts = search_criteria.get('districts', [])
                            normalized_districts = search_criteria.get('normalized_districts', [])
                            
                            logger.info(f"✅ Combined search - Original: {original_districts}")
                            logger.info(f"✅ Combined search - Normalized: {normalized_districts}")
                            
                            expected = ["Central district", "Western district"]
                            if normalized_districts == expected:
                                logger.info(f"✅ Combined search normalization SUCCESS")
                                success_count += 1
                            else:
                                logger.error(f"❌ Combined search normalization FAILED")
                            
                            total_tests += 1
                        else:
                            logger.error(f"❌ Combined search failed")
                except Exception as e:
                    logger.error(f"❌ Combined search test failed: {e}")
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("NORMALIZATION TEST SUMMARY")
                logger.info("="*60)
                logger.info(f"✅ Successful tests: {success_count}/{total_tests}")
                logger.info(f"❌ Failed tests: {total_tests - success_count}/{total_tests}")
                
                if success_count == total_tests:
                    logger.info("🎉 All normalization tests passed!")
                    return True
                else:
                    logger.error("❌ Some normalization tests failed!")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the normalization tests."""
    logger.info("🚀 Starting District Name Normalization Tests")
    
    success = await test_district_normalization()
    
    if success:
        logger.info("\n✅ All tests passed! District normalization is working correctly.")
        return 0
    else:
        logger.error("\n❌ Some tests failed! Check the logs above.")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)