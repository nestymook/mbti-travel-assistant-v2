"""Local MCP Client for Testing Restaurant Search MCP Server.

This module provides a comprehensive test client for the Restaurant Search MCP server
using MCP ClientSession and streamable_http transport. It tests all three MCP tools
with various scenarios using existing config data.

The client connects to the local FastMCP server running on localhost:8080 and
validates tool functionality, error handling, and response formats.
"""

import asyncio
import json
import logging
import time
from datetime import timedelta
from typing import Dict, List, Any, Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalMCPTestClient:
    """Local MCP test client for restaurant search server."""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        """Initialize the test client.
        
        Args:
            server_url: URL of the local MCP server
        """
        self.server_url = server_url
        self.timeout = timedelta(seconds=30)
        
    async def test_connection(self) -> bool:
        """Test basic connection to MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Testing connection to {self.server_url}")
            
            async with streamablehttp_client(
                self.server_url, 
                timeout=self.timeout
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    logger.info("Connection test successful")
                    return True
                    
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """List available MCP tools.
        
        Returns:
            List of tool definitions or None if failed
        """
        try:
            logger.info("Listing available MCP tools")
            
            async with streamablehttp_client(
                self.server_url, 
                timeout=self.timeout
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    
                    logger.info(f"Found {len(tools.tools)} tools:")
                    for tool in tools.tools:
                        logger.info(f"  - {tool.name}: {tool.description}")
                    
                    return [
                        {
                            'name': tool.name,
                            'description': tool.description,
                            'inputSchema': tool.inputSchema
                        }
                        for tool in tools.tools
                    ]
                    
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a specific MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response or None if failed
        """
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            
            async with streamablehttp_client(
                self.server_url, 
                timeout=self.timeout
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(
                        name=tool_name,
                        arguments=arguments
                    )
                    
                    # Parse the JSON response
                    response_data = json.loads(result.content[0].text)
                    logger.info(f"Tool '{tool_name}' completed successfully")
                    
                    return {
                        'success': True,
                        'tool_name': tool_name,
                        'arguments': arguments,
                        'response': response_data,
                        'is_error': result.isError if hasattr(result, 'isError') else False
                    }
                    
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            return {
                'success': False,
                'tool_name': tool_name,
                'arguments': arguments,
                'error': str(e)
            }
    
    async def test_search_by_district(self) -> List[Dict[str, Any]]:
        """Test search_restaurants_by_district tool with various scenarios.
        
        Returns:
            List of test results
        """
        logger.info("Testing search_restaurants_by_district tool")
        
        test_cases = [
            {
                'name': 'Single valid district',
                'arguments': {'districts': ['Central district']},
                'expected_success': True
            },
            {
                'name': 'Multiple valid districts',
                'arguments': {'districts': ['Central district', 'Admiralty', 'Causeway Bay']},
                'expected_success': True
            },
            {
                'name': 'Invalid district',
                'arguments': {'districts': ['NonExistentDistrict']},
                'expected_success': False
            },
            {
                'name': 'Mixed valid and invalid districts',
                'arguments': {'districts': ['Central district', 'InvalidDistrict']},
                'expected_success': False
            },
            {
                'name': 'Empty districts list',
                'arguments': {'districts': []},
                'expected_success': False
            },
            {
                'name': 'Non-list districts parameter',
                'arguments': {'districts': 'Central district'},
                'expected_success': False
            },
            {
                'name': 'Districts with non-string items',
                'arguments': {'districts': ['Central district', 123]},
                'expected_success': False
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"Running test: {test_case['name']}")
            
            result = await self.call_tool(
                'search_restaurants_by_district',
                test_case['arguments']
            )
            
            if result:
                # Validate result matches expectation
                actual_success = result.get('success', False) and result.get('response', {}).get('success', False)
                expected_success = test_case['expected_success']
                
                test_result = {
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': expected_success,
                    'actual_success': actual_success,
                    'passed': actual_success == expected_success,
                    'response': result.get('response', {}),
                    'error': result.get('error')
                }
                
                if test_result['passed']:
                    logger.info(f"✓ Test '{test_case['name']}' passed")
                else:
                    logger.warning(f"✗ Test '{test_case['name']}' failed")
                    
                results.append(test_result)
            else:
                logger.error(f"✗ Test '{test_case['name']}' failed - no result")
                results.append({
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': test_case['expected_success'],
                    'actual_success': False,
                    'passed': False,
                    'error': 'No result returned'
                })
        
        return results
    
    async def test_search_by_meal_type(self) -> List[Dict[str, Any]]:
        """Test search_restaurants_by_meal_type tool with various scenarios.
        
        Returns:
            List of test results
        """
        logger.info("Testing search_restaurants_by_meal_type tool")
        
        test_cases = [
            {
                'name': 'Single valid meal type - breakfast',
                'arguments': {'meal_types': ['breakfast']},
                'expected_success': True
            },
            {
                'name': 'Single valid meal type - lunch',
                'arguments': {'meal_types': ['lunch']},
                'expected_success': True
            },
            {
                'name': 'Single valid meal type - dinner',
                'arguments': {'meal_types': ['dinner']},
                'expected_success': True
            },
            {
                'name': 'Multiple valid meal types',
                'arguments': {'meal_types': ['breakfast', 'lunch', 'dinner']},
                'expected_success': True
            },
            {
                'name': 'Invalid meal type',
                'arguments': {'meal_types': ['brunch']},
                'expected_success': False
            },
            {
                'name': 'Mixed valid and invalid meal types',
                'arguments': {'meal_types': ['breakfast', 'brunch']},
                'expected_success': False
            },
            {
                'name': 'Empty meal types list',
                'arguments': {'meal_types': []},
                'expected_success': False
            },
            {
                'name': 'Non-list meal types parameter',
                'arguments': {'meal_types': 'breakfast'},
                'expected_success': False
            },
            {
                'name': 'Meal types with non-string items',
                'arguments': {'meal_types': ['breakfast', 123]},
                'expected_success': False
            },
            {
                'name': 'Case sensitivity test',
                'arguments': {'meal_types': ['BREAKFAST', 'Lunch']},
                'expected_success': True  # Should handle case insensitivity
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"Running test: {test_case['name']}")
            
            result = await self.call_tool(
                'search_restaurants_by_meal_type',
                test_case['arguments']
            )
            
            if result:
                # Validate result matches expectation
                actual_success = result.get('success', False) and result.get('response', {}).get('success', False)
                expected_success = test_case['expected_success']
                
                test_result = {
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': expected_success,
                    'actual_success': actual_success,
                    'passed': actual_success == expected_success,
                    'response': result.get('response', {}),
                    'error': result.get('error')
                }
                
                if test_result['passed']:
                    logger.info(f"✓ Test '{test_case['name']}' passed")
                else:
                    logger.warning(f"✗ Test '{test_case['name']}' failed")
                    
                results.append(test_result)
            else:
                logger.error(f"✗ Test '{test_case['name']}' failed - no result")
                results.append({
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': test_case['expected_success'],
                    'actual_success': False,
                    'passed': False,
                    'error': 'No result returned'
                })
        
        return results
    
    async def test_search_combined(self) -> List[Dict[str, Any]]:
        """Test search_restaurants_combined tool with various scenarios.
        
        Returns:
            List of test results
        """
        logger.info("Testing search_restaurants_combined tool")
        
        test_cases = [
            {
                'name': 'Districts only',
                'arguments': {'districts': ['Central district', 'Admiralty']},
                'expected_success': True
            },
            {
                'name': 'Meal types only',
                'arguments': {'meal_types': ['breakfast', 'lunch']},
                'expected_success': True
            },
            {
                'name': 'Both districts and meal types',
                'arguments': {
                    'districts': ['Central district', 'Causeway Bay'],
                    'meal_types': ['lunch', 'dinner']
                },
                'expected_success': True
            },
            {
                'name': 'Neither parameter provided',
                'arguments': {},
                'expected_success': False
            },
            {
                'name': 'Both parameters None',
                'arguments': {'districts': None, 'meal_types': None},
                'expected_success': False
            },
            {
                'name': 'Empty districts list',
                'arguments': {'districts': []},
                'expected_success': False
            },
            {
                'name': 'Empty meal types list',
                'arguments': {'meal_types': []},
                'expected_success': False
            },
            {
                'name': 'Invalid district with valid meal type',
                'arguments': {
                    'districts': ['InvalidDistrict'],
                    'meal_types': ['breakfast']
                },
                'expected_success': False
            },
            {
                'name': 'Valid district with invalid meal type',
                'arguments': {
                    'districts': ['Central district'],
                    'meal_types': ['brunch']
                },
                'expected_success': False
            },
            {
                'name': 'Non-list districts parameter',
                'arguments': {'districts': 'Central district'},
                'expected_success': False
            },
            {
                'name': 'Non-list meal types parameter',
                'arguments': {'meal_types': 'breakfast'},
                'expected_success': False
            }
        ]
        
        results = []
        for test_case in test_cases:
            logger.info(f"Running test: {test_case['name']}")
            
            result = await self.call_tool(
                'search_restaurants_combined',
                test_case['arguments']
            )
            
            if result:
                # Validate result matches expectation
                actual_success = result.get('success', False) and result.get('response', {}).get('success', False)
                expected_success = test_case['expected_success']
                
                test_result = {
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': expected_success,
                    'actual_success': actual_success,
                    'passed': actual_success == expected_success,
                    'response': result.get('response', {}),
                    'error': result.get('error')
                }
                
                if test_result['passed']:
                    logger.info(f"✓ Test '{test_case['name']}' passed")
                else:
                    logger.warning(f"✗ Test '{test_case['name']}' failed")
                    
                results.append(test_result)
            else:
                logger.error(f"✗ Test '{test_case['name']}' failed - no result")
                results.append({
                    'test_name': test_case['name'],
                    'arguments': test_case['arguments'],
                    'expected_success': test_case['expected_success'],
                    'actual_success': False,
                    'passed': False,
                    'error': 'No result returned'
                })
        
        return results
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite for all MCP tools.
        
        Returns:
            Complete test results summary
        """
        logger.info("Starting comprehensive MCP test suite")
        start_time = time.time()
        
        # Test connection first
        connection_ok = await self.test_connection()
        if not connection_ok:
            return {
                'success': False,
                'error': 'Failed to connect to MCP server',
                'server_url': self.server_url
            }
        
        # List available tools
        tools = await self.list_tools()
        if not tools:
            return {
                'success': False,
                'error': 'Failed to list MCP tools',
                'server_url': self.server_url
            }
        
        # Run all test suites
        district_tests = await self.test_search_by_district()
        meal_type_tests = await self.test_search_by_meal_type()
        combined_tests = await self.test_search_combined()
        
        # Calculate summary statistics
        all_tests = district_tests + meal_type_tests + combined_tests
        total_tests = len(all_tests)
        passed_tests = sum(1 for test in all_tests if test['passed'])
        failed_tests = total_tests - passed_tests
        
        end_time = time.time()
        duration = end_time - start_time
        
        summary = {
            'success': True,
            'server_url': self.server_url,
            'duration_seconds': round(duration, 2),
            'tools_found': len(tools),
            'available_tools': [tool['name'] for tool in tools],
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
            },
            'test_results': {
                'district_search_tests': {
                    'total': len(district_tests),
                    'passed': sum(1 for test in district_tests if test['passed']),
                    'results': district_tests
                },
                'meal_type_search_tests': {
                    'total': len(meal_type_tests),
                    'passed': sum(1 for test in meal_type_tests if test['passed']),
                    'results': meal_type_tests
                },
                'combined_search_tests': {
                    'total': len(combined_tests),
                    'passed': sum(1 for test in combined_tests if test['passed']),
                    'results': combined_tests
                }
            }
        }
        
        logger.info(f"Test suite completed in {duration:.2f} seconds")
        logger.info(f"Results: {passed_tests}/{total_tests} tests passed ({summary['test_summary']['success_rate']}%)")
        
        return summary


# Helper functions for running tests
async def run_local_tests(server_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Run local MCP tests against the specified server.
    
    Args:
        server_url: URL of the local MCP server
        
    Returns:
        Complete test results
    """
    client = LocalMCPTestClient(server_url)
    return await client.run_comprehensive_tests()


def print_test_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of test results.
    
    Args:
        results: Test results from run_comprehensive_tests
    """
    if not results.get('success'):
        print(f"❌ Test suite failed: {results.get('error', 'Unknown error')}")
        return
    
    print("\n" + "="*60)
    print("MCP SERVER TEST RESULTS")
    print("="*60)
    print(f"Server URL: {results['server_url']}")
    print(f"Duration: {results['duration_seconds']} seconds")
    print(f"Tools Found: {results['tools_found']}")
    print(f"Available Tools: {', '.join(results['available_tools'])}")
    
    summary = results['test_summary']
    print(f"\nOverall Results: {summary['passed_tests']}/{summary['total_tests']} tests passed ({summary['success_rate']}%)")
    
    # Print detailed results for each test category
    for category, data in results['test_results'].items():
        category_name = category.replace('_', ' ').title()
        print(f"\n{category_name}: {data['passed']}/{data['total']} passed")
        
        for test in data['results']:
            status = "✓" if test['passed'] else "✗"
            print(f"  {status} {test['test_name']}")
            if not test['passed'] and test.get('error'):
                print(f"    Error: {test['error']}")


if __name__ == "__main__":
    """Run the test suite when executed directly."""
    import sys
    
    # Allow custom server URL from command line
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    print(f"Testing MCP server at {server_url}")
    print("Make sure the restaurant MCP server is running locally!")
    print("Start it with: python restaurant_mcp_server.py")
    print()
    
    # Run the tests
    results = asyncio.run(run_local_tests(server_url))
    
    # Print results
    print_test_summary(results)
    
    # Exit with appropriate code
    if results.get('success') and results.get('test_summary', {}).get('failed_tests', 1) == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)