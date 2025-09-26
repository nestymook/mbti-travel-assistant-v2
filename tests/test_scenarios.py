"""Comprehensive Test Scenarios for Restaurant Search MCP Server.

This module provides comprehensive test scenarios using existing district configuration
files and actual restaurant data. It covers various search combinations with real data
and includes edge case test data for error handling validation.

The scenarios are designed to validate all requirements and test the system with
realistic data patterns found in the config/districts/ and config/restaurants/ directories.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from tests.test_mcp_client import LocalMCPTestClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Test scenario definition."""
    name: str
    description: str
    tool_name: str
    arguments: Dict[str, Any]
    expected_success: bool
    validation_criteria: Optional[Dict[str, Any]] = None
    requirements: Optional[List[str]] = None


class ComprehensiveTestScenarios:
    """Comprehensive test scenarios using real config data."""
    
    def __init__(self, config_base_path: str = "config"):
        """Initialize test scenarios with config data.
        
        Args:
            config_base_path: Base path to config directory
        """
        self.config_base_path = config_base_path
        self.districts_config = self._load_district_config()
        self.available_districts = self._get_available_districts()
        self.available_restaurant_files = self._get_available_restaurant_files()
        
    def _load_district_config(self) -> Dict[str, Any]:
        """Load district configuration from config files.
        
        Returns:
            Combined district configuration data
        """
        config = {}
        districts_path = os.path.join(self.config_base_path, "districts")
        
        try:
            # Load master config
            master_config_path = os.path.join(districts_path, "master-config.json")
            if os.path.exists(master_config_path):
                with open(master_config_path, 'r', encoding='utf-8') as f:
                    config['master'] = json.load(f)
            
            # Load regional configs
            config['regions'] = {}
            for region_file in ['hong-kong-island.json', 'kowloon.json', 'new-territories.json', 'lantau.json']:
                region_path = os.path.join(districts_path, region_file)
                if os.path.exists(region_path):
                    with open(region_path, 'r', encoding='utf-8') as f:
                        region_name = region_file.replace('.json', '')
                        config['regions'][region_name] = json.load(f)
                        
        except Exception as e:
            logger.warning(f"Could not load district config: {e}")
            
        return config
    
    def _get_available_districts(self) -> List[str]:
        """Get list of available districts from config.
        
        Returns:
            List of district names
        """
        districts = []
        
        for region_name, region_data in self.districts_config.get('regions', {}).items():
            if 'districts' in region_data:
                for district in region_data['districts']:
                    if 'name' in district:
                        districts.append(district['name'])
        
        return sorted(districts)
    
    def _get_available_restaurant_files(self) -> Dict[str, List[str]]:
        """Get available restaurant data files by region.
        
        Returns:
            Dictionary mapping region to list of available district files
        """
        files = {}
        restaurants_path = os.path.join(self.config_base_path, "restaurants")
        
        if not os.path.exists(restaurants_path):
            return files
            
        for region_dir in os.listdir(restaurants_path):
            region_path = os.path.join(restaurants_path, region_dir)
            if os.path.isdir(region_path):
                files[region_dir] = []
                for file_name in os.listdir(region_path):
                    if file_name.endswith('.json'):
                        district_name = file_name.replace('.json', '').replace('-', ' ').title()
                        files[region_dir].append(district_name)
        
        return files
    
    def get_district_search_scenarios(self) -> List[TestScenario]:
        """Get comprehensive district search test scenarios.
        
        Returns:
            List of district search test scenarios
        """
        scenarios = []
        
        # Get some real districts for testing
        real_districts = self.available_districts[:10] if self.available_districts else [
            'Central district', 'Admiralty', 'Causeway Bay', 'Wan Chai', 'Sheung Wan'
        ]
        
        # Positive test cases with real data
        scenarios.extend([
            TestScenario(
                name="Single high-priority district",
                description="Search for restaurants in Central district (high priority area)",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["Central district"]},
                expected_success=True,
                validation_criteria={
                    "min_restaurants": 1,
                    "has_metadata": True,
                    "district_in_results": "Central district"
                },
                requirements=["1.1", "1.2", "9.1"]
            ),
            TestScenario(
                name="Multiple districts from same region",
                description="Search multiple districts from Hong Kong Island",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["Central district", "Admiralty", "Causeway Bay"]},
                expected_success=True,
                validation_criteria={
                    "min_restaurants": 1,
                    "has_metadata": True,
                    "districts_covered": ["Central district", "Admiralty", "Causeway Bay"]
                },
                requirements=["1.1", "1.3", "9.1"]
            ),
            TestScenario(
                name="Mixed priority districts",
                description="Search districts with different priority levels",
                tool_name="search_restaurants_by_district",
                arguments={"districts": real_districts[:5]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "response_structure": ["success", "data"]
                },
                requirements=["1.1", "1.3", "9.2"]
            ),
            TestScenario(
                name="All available districts",
                description="Search all configured districts",
                tool_name="search_restaurants_by_district",
                arguments={"districts": real_districts},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "response_structure": ["success", "data"]
                },
                requirements=["1.1", "1.3", "9.1", "9.2"]
            )
        ])
        
        # Negative test cases
        scenarios.extend([
            TestScenario(
                name="Non-existent district",
                description="Search for a district that doesn't exist in config",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["NonExistentDistrict"]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError",
                    "has_available_districts": True
                },
                requirements=["1.2", "9.4"]
            ),
            TestScenario(
                name="Mixed valid and invalid districts",
                description="Search with both valid and invalid district names",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["Central district", "InvalidDistrict", "FakePlace"]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError",
                    "has_available_districts": True
                },
                requirements=["1.2", "9.4"]
            ),
            TestScenario(
                name="Empty districts list",
                description="Search with empty districts list",
                tool_name="search_restaurants_by_district",
                arguments={"districts": []},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["1.2"]
            ),
            TestScenario(
                name="Invalid parameter type",
                description="Pass string instead of list for districts",
                tool_name="search_restaurants_by_district",
                arguments={"districts": "Central district"},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["1.2"]
            ),
            TestScenario(
                name="Districts with non-string items",
                description="Pass list with non-string items",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["Central district", 123, None]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["1.2"]
            )
        ])
        
        return scenarios
    
    def get_meal_type_search_scenarios(self) -> List[TestScenario]:
        """Get comprehensive meal type search test scenarios.
        
        Returns:
            List of meal type search test scenarios
        """
        scenarios = []
        
        # Positive test cases for meal types
        scenarios.extend([
            TestScenario(
                name="Breakfast search",
                description="Search restaurants open for breakfast (07:00-11:29)",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_periods_defined": True,
                    "breakfast_period": "07:00 - 11:29"
                },
                requirements=["2.1", "2.4", "2.5"]
            ),
            TestScenario(
                name="Lunch search",
                description="Search restaurants open for lunch (11:30-17:29)",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["lunch"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_periods_defined": True,
                    "lunch_period": "11:30 - 17:29"
                },
                requirements=["2.2", "2.4", "2.5"]
            ),
            TestScenario(
                name="Dinner search",
                description="Search restaurants open for dinner (17:30-22:30)",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["dinner"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_periods_defined": True,
                    "dinner_period": "17:30 - 22:30"
                },
                requirements=["2.3", "2.4", "2.5"]
            ),
            TestScenario(
                name="Multiple meal types",
                description="Search restaurants for breakfast and lunch",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast", "lunch"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_analysis": True
                },
                requirements=["2.1", "2.2", "2.6"]
            ),
            TestScenario(
                name="All meal types",
                description="Search restaurants for all meal types",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast", "lunch", "dinner"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_analysis": True
                },
                requirements=["2.1", "2.2", "2.3", "2.6"]
            ),
            TestScenario(
                name="Case insensitive meal types",
                description="Test case insensitivity for meal type names",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["BREAKFAST", "Lunch", "dinner"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True
                },
                requirements=["2.1", "2.2", "2.3"]
            )
        ])
        
        # Negative test cases for meal types
        scenarios.extend([
            TestScenario(
                name="Invalid meal type",
                description="Search with invalid meal type",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["brunch"]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError",
                    "valid_meal_types_listed": True
                },
                requirements=["2.7"]
            ),
            TestScenario(
                name="Mixed valid and invalid meal types",
                description="Search with both valid and invalid meal types",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast", "brunch", "snack"]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError",
                    "valid_meal_types_listed": True
                },
                requirements=["2.7"]
            ),
            TestScenario(
                name="Empty meal types list",
                description="Search with empty meal types list",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": []},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["2.7"]
            ),
            TestScenario(
                name="Invalid parameter type for meal types",
                description="Pass string instead of list for meal types",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": "breakfast"},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["2.7"]
            ),
            TestScenario(
                name="Meal types with non-string items",
                description="Pass list with non-string items",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast", 123, None]},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["2.7"]
            )
        ])
        
        return scenarios
    
    def get_combined_search_scenarios(self) -> List[TestScenario]:
        """Get comprehensive combined search test scenarios.
        
        Returns:
            List of combined search test scenarios
        """
        scenarios = []
        
        # Get some real districts for testing
        real_districts = self.available_districts[:5] if self.available_districts else [
            'Central district', 'Admiralty', 'Causeway Bay'
        ]
        
        # Positive test cases for combined search
        scenarios.extend([
            TestScenario(
                name="Districts only - single district",
                description="Combined search with only districts parameter (single)",
                tool_name="search_restaurants_combined",
                arguments={"districts": ["Central district"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "district_info": True
                },
                requirements=["6.2", "6.4"]
            ),
            TestScenario(
                name="Districts only - multiple districts",
                description="Combined search with only districts parameter (multiple)",
                tool_name="search_restaurants_combined",
                arguments={"districts": real_districts[:3]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "district_info": True
                },
                requirements=["6.2", "6.4"]
            ),
            TestScenario(
                name="Meal types only - single meal type",
                description="Combined search with only meal types parameter (single)",
                tool_name="search_restaurants_combined",
                arguments={"meal_types": ["lunch"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "meal_analysis": True
                },
                requirements=["6.3", "6.4"]
            ),
            TestScenario(
                name="Meal types only - multiple meal types",
                description="Combined search with only meal types parameter (multiple)",
                tool_name="search_restaurants_combined",
                arguments={"meal_types": ["breakfast", "dinner"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "meal_analysis": True
                },
                requirements=["6.3", "6.4"]
            ),
            TestScenario(
                name="Both parameters - restrictive search",
                description="Combined search with both districts and meal types (restrictive)",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": ["Central district", "Admiralty"],
                    "meal_types": ["lunch"]
                },
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "district_info": True,
                    "meal_analysis": True
                },
                requirements=["6.1", "6.4"]
            ),
            TestScenario(
                name="Both parameters - broad search",
                description="Combined search with multiple districts and meal types",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": real_districts[:3],
                    "meal_types": ["breakfast", "lunch", "dinner"]
                },
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined",
                    "district_info": True,
                    "meal_analysis": True
                },
                requirements=["6.1", "6.4"]
            ),
            TestScenario(
                name="Explicit None parameters",
                description="Combined search with explicit None for one parameter",
                tool_name="search_restaurants_combined",
                arguments={"districts": ["Central district"], "meal_types": None},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "search_type": "combined"
                },
                requirements=["6.2", "6.4"]
            )
        ])
        
        # Negative test cases for combined search
        scenarios.extend([
            TestScenario(
                name="No parameters provided",
                description="Combined search with no parameters",
                tool_name="search_restaurants_combined",
                arguments={},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Both parameters None",
                description="Combined search with both parameters explicitly None",
                tool_name="search_restaurants_combined",
                arguments={"districts": None, "meal_types": None},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Empty districts list",
                description="Combined search with empty districts list",
                tool_name="search_restaurants_combined",
                arguments={"districts": []},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Empty meal types list",
                description="Combined search with empty meal types list",
                tool_name="search_restaurants_combined",
                arguments={"meal_types": []},
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Invalid district with valid meal type",
                description="Combined search with invalid district and valid meal type",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": ["InvalidDistrict"],
                    "meal_types": ["breakfast"]
                },
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Valid district with invalid meal type",
                description="Combined search with valid district and invalid meal type",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": ["Central district"],
                    "meal_types": ["brunch"]
                },
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            ),
            TestScenario(
                name="Invalid parameter types",
                description="Combined search with invalid parameter types",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": "Central district",
                    "meal_types": "breakfast"
                },
                expected_success=False,
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["6.4"]
            )
        ])
        
        return scenarios
    
    def get_edge_case_scenarios(self) -> List[TestScenario]:
        """Get edge case test scenarios for error handling validation.
        
        Returns:
            List of edge case test scenarios
        """
        scenarios = []
        
        # Edge cases for data handling
        scenarios.extend([
            TestScenario(
                name="District with special characters",
                description="Search district with special characters in name",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["Central district"]},  # This has a space
                expected_success=True,
                validation_criteria={
                    "has_metadata": True
                },
                requirements=["9.5"]
            ),
            TestScenario(
                name="Case sensitivity in district names",
                description="Test case sensitivity in district names",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["central district", "ADMIRALTY"]},
                expected_success=False,  # Should be case sensitive
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["9.2"]
            ),
            TestScenario(
                name="Very long district list",
                description="Search with many districts to test performance",
                tool_name="search_restaurants_by_district",
                arguments={"districts": self.available_districts},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "response_time_reasonable": True
                },
                requirements=["1.3"]
            ),
            TestScenario(
                name="Unicode district names",
                description="Test handling of unicode characters in district names",
                tool_name="search_restaurants_by_district",
                arguments={"districts": ["中環", "金鐘"]},  # Chinese names
                expected_success=False,  # These aren't in our config
                validation_criteria={
                    "error_type": "ValidationError"
                },
                requirements=["9.4"]
            ),
            TestScenario(
                name="Meal type boundary conditions",
                description="Test meal types that might be on boundaries",
                tool_name="search_restaurants_by_meal_type",
                arguments={"meal_types": ["breakfast", "lunch", "dinner"]},
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "meal_analysis": True
                },
                requirements=["2.5", "2.6"]
            ),
            TestScenario(
                name="Combined search with maximum parameters",
                description="Combined search with maximum realistic parameters",
                tool_name="search_restaurants_combined",
                arguments={
                    "districts": self.available_districts[:10],
                    "meal_types": ["breakfast", "lunch", "dinner"]
                },
                expected_success=True,
                validation_criteria={
                    "has_metadata": True,
                    "response_time_reasonable": True
                },
                requirements=["6.1", "6.4"]
            )
        ])
        
        return scenarios
    
    def get_all_scenarios(self) -> List[TestScenario]:
        """Get all test scenarios.
        
        Returns:
            Complete list of all test scenarios
        """
        all_scenarios = []
        all_scenarios.extend(self.get_district_search_scenarios())
        all_scenarios.extend(self.get_meal_type_search_scenarios())
        all_scenarios.extend(self.get_combined_search_scenarios())
        all_scenarios.extend(self.get_edge_case_scenarios())
        
        return all_scenarios
    
    def print_scenario_summary(self) -> None:
        """Print a summary of all available test scenarios."""
        scenarios = self.get_all_scenarios()
        
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SCENARIOS SUMMARY")
        print("="*60)
        print(f"Total scenarios: {len(scenarios)}")
        print(f"Available districts: {len(self.available_districts)}")
        print(f"Available restaurant files: {sum(len(files) for files in self.available_restaurant_files.values())}")
        
        # Group by tool
        by_tool = {}
        for scenario in scenarios:
            tool = scenario.tool_name
            if tool not in by_tool:
                by_tool[tool] = []
            by_tool[tool].append(scenario)
        
        for tool_name, tool_scenarios in by_tool.items():
            print(f"\n{tool_name}: {len(tool_scenarios)} scenarios")
            positive = sum(1 for s in tool_scenarios if s.expected_success)
            negative = len(tool_scenarios) - positive
            print(f"  - Positive tests: {positive}")
            print(f"  - Negative tests: {negative}")
        
        # Show some sample districts
        if self.available_districts:
            print(f"\nSample districts: {', '.join(self.available_districts[:10])}")
            if len(self.available_districts) > 10:
                print(f"... and {len(self.available_districts) - 10} more")
        
        # Show restaurant file coverage
        print(f"\nRestaurant data coverage:")
        for region, files in self.available_restaurant_files.items():
            print(f"  - {region}: {len(files)} district files")


async def run_comprehensive_scenario_tests(server_url: str = "http://localhost:8080") -> Dict[str, Any]:
    """Run comprehensive scenario tests against MCP server.
    
    Args:
        server_url: URL of the MCP server to test
        
    Returns:
        Comprehensive test results
    """
    logger.info("Starting comprehensive scenario tests")
    
    # Initialize test scenarios and client
    scenarios = ComprehensiveTestScenarios()
    client = LocalMCPTestClient(server_url)
    
    # Get all test scenarios
    all_scenarios = scenarios.get_all_scenarios()
    
    # Test connection first
    connection_ok = await client.test_connection()
    if not connection_ok:
        return {
            'success': False,
            'error': 'Failed to connect to MCP server',
            'server_url': server_url
        }
    
    # Run all scenarios
    results = []
    for scenario in all_scenarios:
        logger.info(f"Running scenario: {scenario.name}")
        
        result = await client.call_tool(scenario.tool_name, scenario.arguments)
        
        if result:
            # Validate result matches expectation
            actual_success = result.get('success', False) and result.get('response', {}).get('success', False)
            expected_success = scenario.expected_success
            
            # Additional validation based on criteria
            validation_passed = True
            validation_details = {}
            
            if scenario.validation_criteria and actual_success:
                validation_details = _validate_response(result.get('response', {}), scenario.validation_criteria)
                validation_passed = validation_details.get('passed', True)
            
            test_result = {
                'scenario_name': scenario.name,
                'description': scenario.description,
                'tool_name': scenario.tool_name,
                'arguments': scenario.arguments,
                'expected_success': expected_success,
                'actual_success': actual_success,
                'validation_passed': validation_passed,
                'validation_details': validation_details,
                'passed': actual_success == expected_success and validation_passed,
                'response': result.get('response', {}),
                'error': result.get('error'),
                'requirements': scenario.requirements or []
            }
            
            results.append(test_result)
        else:
            logger.error(f"Scenario '{scenario.name}' failed - no result")
            results.append({
                'scenario_name': scenario.name,
                'description': scenario.description,
                'tool_name': scenario.tool_name,
                'arguments': scenario.arguments,
                'expected_success': scenario.expected_success,
                'actual_success': False,
                'validation_passed': False,
                'passed': False,
                'error': 'No result returned',
                'requirements': scenario.requirements or []
            })
    
    # Calculate summary statistics
    total_scenarios = len(results)
    passed_scenarios = sum(1 for r in results if r['passed'])
    failed_scenarios = total_scenarios - passed_scenarios
    
    # Group results by tool
    by_tool = {}
    for result in results:
        tool = result['tool_name']
        if tool not in by_tool:
            by_tool[tool] = {'total': 0, 'passed': 0, 'results': []}
        by_tool[tool]['total'] += 1
        if result['passed']:
            by_tool[tool]['passed'] += 1
        by_tool[tool]['results'].append(result)
    
    return {
        'success': True,
        'server_url': server_url,
        'scenario_summary': {
            'total_scenarios': total_scenarios,
            'passed_scenarios': passed_scenarios,
            'failed_scenarios': failed_scenarios,
            'success_rate': round((passed_scenarios / total_scenarios) * 100, 1) if total_scenarios > 0 else 0
        },
        'results_by_tool': by_tool,
        'all_results': results,
        'config_info': {
            'available_districts': len(scenarios.available_districts),
            'restaurant_files': sum(len(files) for files in scenarios.available_restaurant_files.values())
        }
    }


def _validate_response(response: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Validate response against criteria.
    
    Args:
        response: Response to validate
        criteria: Validation criteria
        
    Returns:
        Validation results
    """
    validation_results = {'passed': True, 'details': []}
    
    for criterion, expected_value in criteria.items():
        if criterion == "min_restaurants":
            actual_count = response.get('data', {}).get('count', 0)
            passed = actual_count >= expected_value
            validation_results['details'].append({
                'criterion': criterion,
                'expected': f">= {expected_value}",
                'actual': actual_count,
                'passed': passed
            })
            if not passed:
                validation_results['passed'] = False
                
        elif criterion == "has_metadata":
            has_metadata = 'metadata' in response.get('data', {})
            validation_results['details'].append({
                'criterion': criterion,
                'expected': True,
                'actual': has_metadata,
                'passed': has_metadata
            })
            if not has_metadata:
                validation_results['passed'] = False
                
        elif criterion == "error_type":
            actual_error_type = response.get('error', {}).get('type', '')
            passed = actual_error_type == expected_value
            validation_results['details'].append({
                'criterion': criterion,
                'expected': expected_value,
                'actual': actual_error_type,
                'passed': passed
            })
            if not passed:
                validation_results['passed'] = False
    
    return validation_results


if __name__ == "__main__":
    """Run comprehensive scenario tests when executed directly."""
    import sys
    import asyncio
    
    # Allow custom server URL from command line
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Show scenario summary first
    scenarios = ComprehensiveTestScenarios()
    scenarios.print_scenario_summary()
    
    print(f"\nTesting MCP server at {server_url}")
    print("Make sure the restaurant MCP server is running locally!")
    print("Start it with: python restaurant_mcp_server.py")
    print()
    
    # Run the comprehensive tests
    results = asyncio.run(run_comprehensive_scenario_tests(server_url))
    
    # Print results summary
    if results.get('success'):
        summary = results['scenario_summary']
        print(f"\n{'='*60}")
        print("COMPREHENSIVE SCENARIO TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total scenarios: {summary['total_scenarios']}")
        print(f"Passed: {summary['passed_scenarios']}")
        print(f"Failed: {summary['failed_scenarios']}")
        print(f"Success rate: {summary['success_rate']}%")
        
        # Show results by tool
        for tool_name, tool_data in results['results_by_tool'].items():
            print(f"\n{tool_name}: {tool_data['passed']}/{tool_data['total']} passed")
            
            # Show failed scenarios
            failed_scenarios = [r for r in tool_data['results'] if not r['passed']]
            if failed_scenarios:
                print(f"  Failed scenarios:")
                for scenario in failed_scenarios[:5]:  # Show first 5 failures
                    print(f"    ✗ {scenario['scenario_name']}")
                    if scenario.get('error'):
                        print(f"      Error: {scenario['error']}")
        
        # Exit with appropriate code
        if summary['failed_scenarios'] == 0:
            print("\n🎉 All scenarios passed!")
            sys.exit(0)
        else:
            print(f"\n❌ {summary['failed_scenarios']} scenarios failed!")
            sys.exit(1)
    else:
        print(f"❌ Test suite failed: {results.get('error', 'Unknown error')}")
        sys.exit(1)