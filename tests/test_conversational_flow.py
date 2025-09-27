#!/usr/bin/env python3
"""
End-to-End Conversational Flow Tests

Tests the complete conversational agent workflow from natural language
query to formatted response, including MCP tool integration.

Requirements: 12.1, 12.2, 13.1, 13.2
"""

import json
import asyncio
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.query_processor import QueryProcessor
from services.restaurant_service import RestaurantService
from services.district_service import DistrictService
from services.time_service import TimeService
from services.data_access import DataAccessClient
from models.restaurant_models import Restaurant, OperatingHours, Sentiment, RestaurantMetadata


class ConversationalFlowTester:
    """Test complete conversational flow from query to response."""
    
    def __init__(self):
        """Initialize the conversational flow tester."""
        self.query_processor = QueryProcessor()
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # Create sample restaurant data for testing
        self.sample_restaurants = self._create_sample_restaurants()
    
    def _create_sample_restaurants(self) -> List[Restaurant]:
        """Create sample restaurant data for testing.
        
        Returns:
            List of sample Restaurant objects.
        """
        restaurants = []
        
        # Central district breakfast place
        restaurants.append(Restaurant(
            id="rest_001",
            name="Central Breakfast Cafe",
            address="123 Central Street, Central",
            meal_type=["Western", "Cafe"],
            sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
            location_category="Cafe",
            district="Central district",
            price_range="$$",
            operating_hours=OperatingHours(
                mon_fri=["07:00 - 11:30"],
                sat_sun=["08:00 - 12:00"],
                public_holiday=["09:00 - 11:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="high",
                version="1.0",
                quality_score=95
            )
        ))
        
        # Tsim Sha Tsui dinner restaurant
        restaurants.append(Restaurant(
            id="rest_002",
            name="TST Dinner House",
            address="456 Nathan Road, Tsim Sha Tsui",
            meal_type=["Chinese", "Cantonese"],
            sentiment=Sentiment(likes=120, dislikes=15, neutral=10),
            location_category="Restaurant",
            district="Tsim Sha Tsui",
            price_range="$$$",
            operating_hours=OperatingHours(
                mon_fri=["18:00 - 23:00"],
                sat_sun=["17:30 - 23:30"],
                public_holiday=["18:00 - 22:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="high",
                version="1.0",
                quality_score=92
            )
        ))
        
        # Causeway Bay lunch place
        restaurants.append(Restaurant(
            id="rest_003",
            name="Causeway Lunch Spot",
            address="789 Hennessy Road, Causeway Bay",
            meal_type=["Japanese", "Sushi"],
            sentiment=Sentiment(likes=95, dislikes=8, neutral=7),
            location_category="Restaurant",
            district="Causeway Bay",
            price_range="$$",
            operating_hours=OperatingHours(
                mon_fri=["11:30 - 15:00", "18:00 - 22:00"],
                sat_sun=["11:30 - 22:00"],
                public_holiday=["12:00 - 21:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="high",
                version="1.0",
                quality_score=88
            )
        ))
        
        return restaurants
    
    def simulate_mcp_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> List[Restaurant]:
        """Simulate MCP tool call and return filtered restaurants.
        
        Args:
            tool_name: Name of the MCP tool to simulate.
            parameters: Parameters for the tool call.
            
        Returns:
            List of restaurants matching the criteria.
        """
        results = []
        
        if tool_name == "search_restaurants_by_district":
            districts = parameters.get('districts', [])
            for restaurant in self.sample_restaurants:
                if restaurant.district in districts:
                    results.append(restaurant)
        
        elif tool_name == "search_restaurants_by_meal_type":
            meal_types = parameters.get('meal_types', [])
            # Simple simulation - check if operating hours overlap with meal times
            for restaurant in self.sample_restaurants:
                if self._restaurant_serves_meal_type(restaurant, meal_types):
                    results.append(restaurant)
        
        elif tool_name == "search_restaurants_combined":
            districts = parameters.get('districts', [])
            meal_types = parameters.get('meal_types', [])
            
            for restaurant in self.sample_restaurants:
                district_match = not districts or restaurant.district in districts
                meal_match = not meal_types or self._restaurant_serves_meal_type(restaurant, meal_types)
                
                if district_match and meal_match:
                    results.append(restaurant)
        
        return results
    
    def _restaurant_serves_meal_type(self, restaurant: Restaurant, meal_types: List[str]) -> bool:
        """Check if restaurant serves any of the specified meal types.
        
        Args:
            restaurant: Restaurant object to check.
            meal_types: List of meal types to check for.
            
        Returns:
            True if restaurant serves any of the meal types.
        """
        # Simple simulation based on operating hours
        for meal_type in meal_types:
            if meal_type == "breakfast":
                # Check if any hours start before 11:30
                for hours in restaurant.operating_hours.mon_fri + restaurant.operating_hours.sat_sun:
                    if hours.startswith(("07:", "08:", "09:", "10:", "11:0", "11:1", "11:2")):
                        return True
            elif meal_type == "lunch":
                # Check if any hours overlap with 11:30-17:29
                for hours in restaurant.operating_hours.mon_fri + restaurant.operating_hours.sat_sun:
                    if "11:30" in hours or "12:" in hours or "13:" in hours or "14:" in hours or "15:" in hours:
                        return True
            elif meal_type == "dinner":
                # Check if any hours start after 17:30
                for hours in restaurant.operating_hours.mon_fri + restaurant.operating_hours.sat_sun:
                    if hours.startswith(("17:3", "17:4", "17:5", "18:", "19:", "20:", "21:", "22:")):
                        return True
        
        return False
    
    def test_conversational_query(self, query: str, expected_tool: str = None) -> Dict[str, Any]:
        """Test a complete conversational query workflow.
        
        Args:
            query: Natural language query to test.
            expected_tool: Expected MCP tool to be called (optional).
            
        Returns:
            Test result dictionary.
        """
        test_result = {
            'query': query,
            'success': False,
            'intent_extracted': False,
            'tool_called': False,
            'response_generated': False,
            'expected_tool': expected_tool,
            'actual_tool': None,
            'error': None,
            'response_preview': None
        }
        
        try:
            # Step 1: Extract intent from natural language query
            intent = self.query_processor.extract_intent(query)
            test_result['intent_extracted'] = True
            test_result['intent'] = {
                'type': intent.intent_type,
                'districts': intent.districts,
                'meal_types': intent.meal_types,
                'confidence': intent.confidence
            }
            
            # Step 2: Determine appropriate MCP tool and parameters
            tool_name, parameters = self._determine_mcp_tool_call(intent)
            test_result['actual_tool'] = tool_name
            
            if expected_tool and tool_name != expected_tool:
                test_result['error'] = f"Expected tool {expected_tool}, got {tool_name}"
                return test_result
            
            # Step 3: Simulate MCP tool call
            if tool_name:
                restaurants = self.simulate_mcp_tool_call(tool_name, parameters)
                test_result['tool_called'] = True
                test_result['results_count'] = len(restaurants)
                
                # Step 4: Format conversational response
                query_context = {
                    'original_query': query,
                    'districts': intent.districts,
                    'meal_types': intent.meal_types,
                    'tool_calls': [{'tool': tool_name, 'parameters': parameters}]
                }
                
                response = self.query_processor.format_conversational_response(
                    restaurants, query_context
                )
                
                test_result['response_generated'] = True
                test_result['response_preview'] = response.response_text[:200] + "..."
                test_result['success'] = True
            
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result
    
    def _determine_mcp_tool_call(self, intent) -> tuple:
        """Determine which MCP tool to call based on intent.
        
        Args:
            intent: QueryIntent object.
            
        Returns:
            Tuple of (tool_name, parameters).
        """
        if intent.intent_type == "district_search":
            return "search_restaurants_by_district", {"districts": intent.districts}
        elif intent.intent_type == "meal_search":
            return "search_restaurants_by_meal_type", {"meal_types": intent.meal_types}
        elif intent.intent_type == "combined_search":
            return "search_restaurants_combined", {
                "districts": intent.districts,
                "meal_types": intent.meal_types
            }
        else:
            return None, {}
    
    def run_conversational_tests(self) -> Dict[str, Any]:
        """Run comprehensive conversational flow tests.
        
        Returns:
            Test results summary.
        """
        print("🧪 Running End-to-End Conversational Flow Tests\n")
        
        # Define test cases with expected behaviors
        test_cases = [
            {
                'query': "Find restaurants in Central district",
                'expected_tool': "search_restaurants_by_district",
                'description': "District-only search"
            },
            {
                'query': "Breakfast places",
                'expected_tool': "search_restaurants_by_meal_type",
                'description': "Meal-type-only search"
            },
            {
                'query': "Dinner restaurants in Tsim Sha Tsui",
                'expected_tool': "search_restaurants_combined",
                'description': "Combined district and meal search"
            },
            {
                'query': "Good lunch spots in Causeway Bay",
                'expected_tool': "search_restaurants_combined",
                'description': "Natural language combined search"
            },
            {
                'query': "What's good in Central?",
                'expected_tool': "search_restaurants_by_district",
                'description': "Casual district inquiry"
            },
            {
                'query': "Morning places in TST",
                'expected_tool': "search_restaurants_combined",
                'description': "Informal meal time and district"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🔍 Test {i}/{len(test_cases)}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            
            result = self.test_conversational_query(
                test_case['query'], 
                test_case['expected_tool']
            )
            
            self.test_results['total_tests'] += 1
            
            if result['success']:
                self.test_results['passed_tests'] += 1
                print(f"✅ PASSED")
                print(f"   Intent: {result['intent']['type']}")
                print(f"   Tool: {result['actual_tool']}")
                print(f"   Results: {result.get('results_count', 0)} restaurants")
                if result.get('response_preview'):
                    print(f"   Response: {result['response_preview']}")
            else:
                self.test_results['failed_tests'] += 1
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
            self.test_results['test_details'].append(result)
            print()
        
        # Summary
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
        print(f"📊 Test Summary:")
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        return self.test_results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling scenarios.
        
        Returns:
            Error handling test results.
        """
        print("\n🚨 Testing Error Handling Scenarios\n")
        
        error_test_cases = [
            {
                'query': "restaurants in Invalid District",
                'description': "Invalid district name"
            },
            {
                'query': "unknown meal type places",
                'description': "Invalid meal type"
            },
            {
                'query': "",
                'description': "Empty query"
            },
            {
                'query': "asdfghjkl qwertyuiop",
                'description': "Nonsensical query"
            }
        ]
        
        error_results = {
            'total_error_tests': len(error_test_cases),
            'handled_gracefully': 0,
            'error_details': []
        }
        
        for i, test_case in enumerate(error_test_cases, 1):
            print(f"🔍 Error Test {i}/{len(error_test_cases)}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            
            try:
                result = self.test_conversational_query(test_case['query'])
                
                # Check if error was handled gracefully
                if result.get('response_generated') or result.get('intent_extracted'):
                    error_results['handled_gracefully'] += 1
                    print(f"✅ Handled gracefully")
                    if result.get('response_preview'):
                        print(f"   Response: {result['response_preview']}")
                else:
                    print(f"⚠️ Not handled gracefully")
                
                error_results['error_details'].append(result)
                
            except Exception as e:
                print(f"❌ Exception raised: {e}")
                error_results['error_details'].append({
                    'query': test_case['query'],
                    'exception': str(e)
                })
            
            print()
        
        graceful_rate = (error_results['handled_gracefully'] / error_results['total_error_tests']) * 100
        print(f"📊 Error Handling Summary:")
        print(f"Total Error Tests: {error_results['total_error_tests']}")
        print(f"Handled Gracefully: {error_results['handled_gracefully']}")
        print(f"Graceful Handling Rate: {graceful_rate:.1f}%")
        
        return error_results
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report.
        
        Returns:
            Test report as formatted string.
        """
        report = "# Conversational Flow Test Report\n\n"
        
        # Overall summary
        total_tests = self.test_results['total_tests']
        passed_tests = self.test_results['passed_tests']
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report += f"## Overall Results\n"
        report += f"- Total Tests: {total_tests}\n"
        report += f"- Passed: {passed_tests}\n"
        report += f"- Failed: {self.test_results['failed_tests']}\n"
        report += f"- Success Rate: {success_rate:.1f}%\n\n"
        
        # Detailed results
        report += "## Detailed Test Results\n\n"
        for i, result in enumerate(self.test_results['test_details'], 1):
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            report += f"### Test {i}: {result['query']}\n"
            report += f"**Status:** {status}\n"
            
            if result.get('intent'):
                intent = result['intent']
                report += f"**Intent Type:** {intent['type']}\n"
                report += f"**Districts:** {intent['districts']}\n"
                report += f"**Meal Types:** {intent['meal_types']}\n"
                report += f"**Confidence:** {intent['confidence']:.2f}\n"
            
            if result.get('actual_tool'):
                report += f"**MCP Tool:** {result['actual_tool']}\n"
            
            if result.get('results_count') is not None:
                report += f"**Results Count:** {result['results_count']}\n"
            
            if result.get('error'):
                report += f"**Error:** {result['error']}\n"
            
            report += "\n"
        
        return report


def main():
    """Main function to run conversational flow tests."""
    tester = ConversationalFlowTester()
    
    # Run main conversational tests
    results = tester.run_conversational_tests()
    
    # Run error handling tests
    error_results = tester.test_error_handling()
    
    # Generate and save report
    report = tester.generate_test_report()
    
    try:
        with open("conversational_flow_test_report.md", "w") as f:
            f.write(report)
        print(f"\n📄 Test report saved to: conversational_flow_test_report.md")
    except Exception as e:
        print(f"\n⚠️ Could not save test report: {e}")
    
    # Return success if most tests passed
    success_rate = (results['passed_tests'] / results['total_tests']) * 100
    return success_rate >= 80  # 80% success rate threshold


if __name__ == "__main__":
    print("🤖 Testing Complete Conversational Agent Flow\n")
    success = main()
    
    if success:
        print("\n🎉 Conversational flow tests completed successfully!")
        exit(0)
    else:
        print("\n⚠️ Some conversational flow tests failed!")
        exit(1)