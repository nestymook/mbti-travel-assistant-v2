"""Test Runner for Local MCP Server Testing.

This script provides a convenient way to run all local MCP server tests,
including basic client tests and comprehensive scenario tests. It can be
used to validate the restaurant search MCP server functionality locally.
"""

import asyncio
import sys
import time
import logging
from typing import Dict, Any

from tests.test_mcp_client import run_local_tests, print_test_summary
from tests.test_scenarios import run_comprehensive_scenario_tests, ComprehensiveTestScenarios


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_all_tests(server_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Run all local MCP server tests.
    
    Args:
        server_url: URL of the local MCP server
        
    Returns:
        Combined test results
    """
    logger.info(f"Starting comprehensive test suite for {server_url}")
    start_time = time.time()
    
    results = {
        'server_url': server_url,
        'start_time': start_time,
        'basic_tests': None,
        'scenario_tests': None,
        'overall_success': False,
        'total_duration': 0
    }
    
    try:
        # Run basic MCP client tests
        logger.info("Running basic MCP client tests...")
        basic_results = await run_local_tests(server_url)
        results['basic_tests'] = basic_results
        
        if not basic_results.get('success'):
            logger.error("Basic tests failed, skipping scenario tests")
            return results
        
        # Run comprehensive scenario tests
        logger.info("Running comprehensive scenario tests...")
        scenario_results = await run_comprehensive_scenario_tests(server_url)
        results['scenario_tests'] = scenario_results
        
        # Calculate overall success
        basic_success = basic_results.get('success', False) and basic_results.get('test_summary', {}).get('failed_tests', 1) == 0
        scenario_success = scenario_results.get('success', False) and scenario_results.get('scenario_summary', {}).get('failed_scenarios', 1) == 0
        
        results['overall_success'] = basic_success and scenario_success
        
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}")
        results['error'] = str(e)
    
    finally:
        end_time = time.time()
        results['total_duration'] = round(end_time - start_time, 2)
    
    return results


def print_combined_results(results: Dict[str, Any]) -> None:
    """Print combined test results in a formatted way.
    
    Args:
        results: Combined test results from run_all_tests
    """
    print("\n" + "="*80)
    print("RESTAURANT SEARCH MCP SERVER - COMPLETE TEST RESULTS")
    print("="*80)
    print(f"Server URL: {results['server_url']}")
    print(f"Total Duration: {results['total_duration']} seconds")
    
    if results.get('error'):
        print(f"❌ Test suite failed with error: {results['error']}")
        return
    
    # Basic tests summary
    basic_tests = results.get('basic_tests')
    if basic_tests:
        print(f"\n📋 BASIC MCP CLIENT TESTS")
        print("-" * 40)
        if basic_tests.get('success'):
            summary = basic_tests.get('test_summary', {})
            print(f"Tools Found: {basic_tests.get('tools_found', 0)}")
            print(f"Available Tools: {', '.join(basic_tests.get('available_tools', []))}")
            print(f"Tests: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} passed ({summary.get('success_rate', 0)}%)")
            
            if summary.get('failed_tests', 0) > 0:
                print("❌ Some basic tests failed")
            else:
                print("✅ All basic tests passed")
        else:
            print("❌ Basic tests failed to run")
    
    # Scenario tests summary
    scenario_tests = results.get('scenario_tests')
    if scenario_tests:
        print(f"\n🎯 COMPREHENSIVE SCENARIO TESTS")
        print("-" * 40)
        if scenario_tests.get('success'):
            summary = scenario_tests.get('scenario_summary', {})
            config_info = scenario_tests.get('config_info', {})
            
            print(f"Config Data: {config_info.get('available_districts', 0)} districts, {config_info.get('restaurant_files', 0)} restaurant files")
            print(f"Scenarios: {summary.get('passed_scenarios', 0)}/{summary.get('total_scenarios', 0)} passed ({summary.get('success_rate', 0)}%)")
            
            # Show results by tool
            for tool_name, tool_data in scenario_tests.get('results_by_tool', {}).items():
                tool_display_name = tool_name.replace('search_restaurants_', '').replace('_', ' ').title()
                print(f"  {tool_display_name}: {tool_data['passed']}/{tool_data['total']} passed")
            
            if summary.get('failed_scenarios', 0) > 0:
                print("❌ Some scenario tests failed")
            else:
                print("✅ All scenario tests passed")
        else:
            print("❌ Scenario tests failed to run")
    
    # Overall result
    print(f"\n🏆 OVERALL RESULT")
    print("-" * 40)
    if results.get('overall_success'):
        print("✅ ALL TESTS PASSED! MCP server is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Check the details above.")
        
        # Show what failed
        failures = []
        if basic_tests and (not basic_tests.get('success') or basic_tests.get('test_summary', {}).get('failed_tests', 0) > 0):
            failures.append("Basic MCP client tests")
        if scenario_tests and (not scenario_tests.get('success') or scenario_tests.get('scenario_summary', {}).get('failed_scenarios', 0) > 0):
            failures.append("Comprehensive scenario tests")
        
        if failures:
            print(f"Failed test categories: {', '.join(failures)}")
    
    print("\n" + "="*80)


def show_test_info() -> None:
    """Show information about available tests and configuration."""
    print("🧪 RESTAURANT SEARCH MCP SERVER TEST SUITE")
    print("="*50)
    print("This test suite validates the Restaurant Search MCP server functionality")
    print("using real configuration data and comprehensive test scenarios.")
    print()
    
    # Show configuration info
    try:
        scenarios = ComprehensiveTestScenarios()
        print(f"📊 TEST CONFIGURATION:")
        print(f"  - Available districts: {len(scenarios.available_districts)}")
        print(f"  - Restaurant data files: {sum(len(files) for files in scenarios.available_restaurant_files.values())}")
        print(f"  - Total test scenarios: {len(scenarios.get_all_scenarios())}")
        
        # Show sample districts
        if scenarios.available_districts:
            sample_districts = scenarios.available_districts[:5]
            print(f"  - Sample districts: {', '.join(sample_districts)}")
            if len(scenarios.available_districts) > 5:
                print(f"    ... and {len(scenarios.available_districts) - 5} more")
        
        print()
    except Exception as e:
        logger.warning(f"Could not load test configuration info: {e}")
    
    print("🚀 USAGE:")
    print("  python tests/run_local_tests.py [server_url]")
    print("  Default server URL: http://localhost:8080")
    print()
    print("📋 TEST CATEGORIES:")
    print("  1. Basic MCP Client Tests - Tool listing and invocation")
    print("  2. District Search Tests - Various district search scenarios")
    print("  3. Meal Type Search Tests - Operating hours analysis")
    print("  4. Combined Search Tests - Mixed criteria searches")
    print("  5. Edge Case Tests - Error handling and boundary conditions")
    print()
    print("⚠️  PREREQUISITES:")
    print("  - Restaurant MCP server must be running locally")
    print("  - Start with: python restaurant_mcp_server.py")
    print("  - Config data must be available in config/ directory")
    print()


def main():
    """Main entry point for the test runner."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_test_info()
            return
        server_url = sys.argv[1]
    else:
        server_url = "http://localhost:8080"
    
    # Show test information
    show_test_info()
    
    print(f"🎯 Testing MCP server at: {server_url}")
    print("Starting test suite...")
    print()
    
    # Run all tests
    try:
        results = asyncio.run(run_all_tests(server_url))
        print_combined_results(results)
        
        # Exit with appropriate code
        if results.get('overall_success'):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()