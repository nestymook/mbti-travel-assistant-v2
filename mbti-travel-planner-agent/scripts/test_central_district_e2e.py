#!/usr/bin/env python3
"""
Central District Search End-to-End Test Script

This script tests the complete Central district search functionality end-to-end,
including restaurant search, sentiment analysis, recommendations, and response
formatting. It simulates real user interactions and validates the complete workflow.

Features:
- Complete Central district restaurant search workflow
- Sentiment analysis and recommendation testing
- Response format validation
- Performance measurement
- User experience simulation
- Error scenario testing
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.gateway_http_client import GatewayHTTPClient, Environment
from services.central_district_workflow import CentralDistrictWorkflow
from services.logging_service import get_logging_service
from services.error_handler import ErrorHandler


class CentralDistrictE2ETester:
    """End-to-end tester for Central district search functionality."""
    
    def __init__(self, environment: str = "production", verbose: bool = False):
        """
        Initialize the E2E tester.
        
        Args:
            environment: Environment to test (development, staging, production)
            verbose: Enable verbose logging
        """
        self.environment = environment
        self.verbose = verbose
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("central_district_e2e_test")
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.error_handler = ErrorHandler("central_district_e2e_test")
        
        # Initialize environment
        env_enum = Environment.PRODUCTION
        if environment == "development":
            env_enum = Environment.DEVELOPMENT
        elif environment == "staging":
            env_enum = Environment.STAGING
        
        self.gateway_client = GatewayHTTPClient(environment=env_enum)
        self.workflow = CentralDistrictWorkflow(environment=env_enum)
        
        # Test results
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": environment,
            "test_scenarios": {},
            "performance_metrics": {},
            "summary": {}
        }
        
        self.logger.info(f"Initialized Central district E2E tester for {environment}")
    
    async def test_basic_search_workflow(self) -> Dict[str, Any]:
        """Test basic Central district search workflow."""
        scenario_name = "basic_search_workflow"
        self.logger.info("Testing basic Central district search workflow")
        
        start_time = time.time()
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "steps": {},
            "errors": [],
            "performance": {}
        }
        
        try:
            # Step 1: Search for restaurants in Central district
            step1_start = time.time()
            search_result = await self.gateway_client.search_restaurants_by_district(["Central district"])
            step1_time = (time.time() - step1_start) * 1000
            
            if search_result.get("success", False):
                restaurants = search_result.get("restaurants", [])
                result["steps"]["restaurant_search"] = {
                    "success": True,
                    "restaurant_count": len(restaurants),
                    "response_time_ms": step1_time,
                    "has_metadata": "metadata" in search_result
                }
                self.logger.info(f"✓ Step 1: Found {len(restaurants)} restaurants in Central district")
                
                if len(restaurants) > 0:
                    # Step 2: Analyze restaurant data structure
                    sample_restaurant = restaurants[0]
                    required_fields = ["id", "name", "sentiment"]
                    has_required_fields = all(field in sample_restaurant for field in required_fields)
                    
                    result["steps"]["data_structure"] = {
                        "success": has_required_fields,
                        "sample_restaurant_keys": list(sample_restaurant.keys()),
                        "has_sentiment_data": "sentiment" in sample_restaurant,
                        "sentiment_structure": sample_restaurant.get("sentiment", {}) if has_required_fields else {}
                    }
                    
                    if has_required_fields:
                        self.logger.info("✓ Step 2: Restaurant data structure is valid")
                        
                        # Step 3: Get recommendations
                        step3_start = time.time()
                        recommend_result = await self.gateway_client.recommend_restaurants(restaurants[:10])
                        step3_time = (time.time() - step3_start) * 1000
                        
                        if recommend_result.get("success", False):
                            result["steps"]["recommendation"] = {
                                "success": True,
                                "response_time_ms": step3_time,
                                "has_recommendation": "recommendation" in recommend_result,
                                "has_candidates": "candidates" in recommend_result,
                                "has_analysis": "analysis_summary" in recommend_result,
                                "ranking_method": recommend_result.get("ranking_method")
                            }
                            self.logger.info("✓ Step 3: Restaurant recommendations generated")
                            
                            # Step 4: Validate recommendation quality
                            recommendation = recommend_result.get("recommendation")
                            candidates = recommend_result.get("candidates", [])
                            
                            if recommendation and candidates:
                                result["steps"]["recommendation_quality"] = {
                                    "success": True,
                                    "recommended_restaurant": recommendation.get("name"),
                                    "candidate_count": len(candidates),
                                    "has_sentiment_analysis": "analysis_summary" in recommend_result
                                }
                                self.logger.info(f"✓ Step 4: Quality recommendation: {recommendation.get('name')}")
                            else:
                                result["success"] = False
                                result["errors"].append("Recommendation or candidates missing")
                                result["steps"]["recommendation_quality"] = {"success": False}
                        else:
                            result["success"] = False
                            result["errors"].append("Restaurant recommendation failed")
                            result["steps"]["recommendation"] = {"success": False}
                    else:
                        result["success"] = False
                        result["errors"].append("Restaurant data structure invalid")
                else:
                    result["success"] = False
                    result["errors"].append("No restaurants found in Central district")
                    result["steps"]["data_structure"] = {"success": False}
            else:
                result["success"] = False
                result["errors"].append("Restaurant search failed")
                result["steps"]["restaurant_search"] = {"success": False}
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Workflow error: {e}")
            self.logger.error(f"✗ Basic search workflow failed: {e}")
        
        # Calculate performance metrics
        total_time = (time.time() - start_time) * 1000
        result["performance"] = {
            "total_time_ms": total_time,
            "search_time_ms": result["steps"].get("restaurant_search", {}).get("response_time_ms", 0),
            "recommendation_time_ms": result["steps"].get("recommendation", {}).get("response_time_ms", 0)
        }
        
        self.test_results["test_scenarios"][scenario_name] = result
        return result
    
    async def test_complete_workflow_service(self) -> Dict[str, Any]:
        """Test the complete workflow using CentralDistrictWorkflow service."""
        scenario_name = "complete_workflow_service"
        self.logger.info("Testing complete workflow service")
        
        start_time = time.time()
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "steps": {},
            "errors": [],
            "performance": {}
        }
        
        try:
            # Execute complete workflow
            workflow_result = await self.workflow.execute_central_district_search()
            workflow_time = (time.time() - start_time) * 1000
            
            if workflow_result.get("success", False):
                result["steps"]["workflow_execution"] = {
                    "success": True,
                    "response_time_ms": workflow_time,
                    "has_restaurants": "restaurants" in workflow_result,
                    "has_recommendation": "recommendation" in workflow_result,
                    "has_summary": "summary" in workflow_result
                }
                
                # Validate workflow response structure
                expected_keys = ["success", "restaurants", "recommendation", "summary", "metadata"]
                has_expected_structure = all(key in workflow_result for key in expected_keys)
                
                result["steps"]["response_structure"] = {
                    "success": has_expected_structure,
                    "response_keys": list(workflow_result.keys()),
                    "missing_keys": [key for key in expected_keys if key not in workflow_result]
                }
                
                if has_expected_structure:
                    self.logger.info("✓ Complete workflow executed successfully")
                    
                    # Validate user-friendly formatting
                    summary = workflow_result.get("summary", {})
                    if isinstance(summary, dict) and "message" in summary:
                        result["steps"]["user_formatting"] = {
                            "success": True,
                            "has_user_message": True,
                            "message_length": len(summary.get("message", "")),
                            "has_statistics": "statistics" in summary
                        }
                        self.logger.info("✓ User-friendly formatting validated")
                    else:
                        result["success"] = False
                        result["errors"].append("User-friendly summary missing")
                        result["steps"]["user_formatting"] = {"success": False}
                else:
                    result["success"] = False
                    result["errors"].append("Workflow response structure invalid")
            else:
                result["success"] = False
                result["errors"].append("Complete workflow execution failed")
                result["steps"]["workflow_execution"] = {"success": False}
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Complete workflow error: {e}")
            self.logger.error(f"✗ Complete workflow service failed: {e}")
        
        result["performance"] = {
            "total_time_ms": (time.time() - start_time) * 1000
        }
        
        self.test_results["test_scenarios"][scenario_name] = result
        return result
    
    async def test_meal_type_filtering(self) -> Dict[str, Any]:
        """Test meal type filtering functionality."""
        scenario_name = "meal_type_filtering"
        self.logger.info("Testing meal type filtering")
        
        start_time = time.time()
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "steps": {},
            "errors": [],
            "performance": {}
        }
        
        try:
            meal_types_to_test = ["breakfast", "lunch", "dinner"]
            meal_type_results = {}
            
            for meal_type in meal_types_to_test:
                step_start = time.time()
                search_result = await self.gateway_client.search_restaurants_combined(
                    districts=["Central district"],
                    meal_types=[meal_type]
                )
                step_time = (time.time() - step_start) * 1000
                
                if search_result.get("success", False):
                    restaurants = search_result.get("restaurants", [])
                    meal_type_results[meal_type] = {
                        "success": True,
                        "restaurant_count": len(restaurants),
                        "response_time_ms": step_time
                    }
                    self.logger.info(f"✓ {meal_type}: Found {len(restaurants)} restaurants")
                else:
                    meal_type_results[meal_type] = {
                        "success": False,
                        "error": search_result.get("error", "Unknown error"),
                        "response_time_ms": step_time
                    }
                    self.logger.warning(f"⚠ {meal_type}: Search failed")
            
            # Validate that at least one meal type returned results
            successful_searches = sum(1 for r in meal_type_results.values() if r["success"])
            
            result["steps"]["meal_type_searches"] = {
                "success": successful_searches > 0,
                "results": meal_type_results,
                "successful_searches": successful_searches,
                "total_searches": len(meal_types_to_test)
            }
            
            if successful_searches == 0:
                result["success"] = False
                result["errors"].append("No meal type searches succeeded")
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Meal type filtering error: {e}")
            self.logger.error(f"✗ Meal type filtering failed: {e}")
        
        result["performance"] = {
            "total_time_ms": (time.time() - start_time) * 1000
        }
        
        self.test_results["test_scenarios"][scenario_name] = result
        return result
    
    async def test_error_scenarios(self) -> Dict[str, Any]:
        """Test error handling scenarios."""
        scenario_name = "error_scenarios"
        self.logger.info("Testing error handling scenarios")
        
        start_time = time.time()
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "steps": {},
            "errors": [],
            "performance": {}
        }
        
        try:
            error_scenarios = [
                {
                    "name": "empty_district_list",
                    "test": lambda: self.gateway_client.search_restaurants_by_district([]),
                    "expected_behavior": "graceful_error"
                },
                {
                    "name": "invalid_district",
                    "test": lambda: self.gateway_client.search_restaurants_by_district(["NonexistentDistrict"]),
                    "expected_behavior": "empty_results_or_error"
                },
                {
                    "name": "empty_restaurant_list_for_recommendation",
                    "test": lambda: self.gateway_client.recommend_restaurants([]),
                    "expected_behavior": "graceful_error"
                },
                {
                    "name": "invalid_meal_type",
                    "test": lambda: self.gateway_client.search_restaurants_combined(
                        districts=["Central district"], meal_types=["invalid_meal"]
                    ),
                    "expected_behavior": "empty_results_or_error"
                }
            ]
            
            error_test_results = {}
            
            for scenario in error_scenarios:
                scenario_name_inner = scenario["name"]
                step_start = time.time()
                
                try:
                    test_result = await scenario["test"]()
                    step_time = (time.time() - step_start) * 1000
                    
                    # Check if error was handled gracefully
                    if isinstance(test_result, dict):
                        has_success_field = "success" in test_result
                        has_error_field = "error" in test_result
                        graceful_handling = has_success_field and (
                            test_result.get("success") == False or 
                            len(test_result.get("restaurants", [])) == 0
                        )
                        
                        error_test_results[scenario_name_inner] = {
                            "success": graceful_handling,
                            "response_time_ms": step_time,
                            "has_success_field": has_success_field,
                            "has_error_field": has_error_field,
                            "result_success": test_result.get("success"),
                            "error_message": test_result.get("error")
                        }
                        
                        if graceful_handling:
                            self.logger.info(f"✓ {scenario_name_inner}: Error handled gracefully")
                        else:
                            self.logger.warning(f"⚠ {scenario_name_inner}: Error handling could be improved")
                    else:
                        error_test_results[scenario_name_inner] = {
                            "success": False,
                            "error": "Unexpected response format"
                        }
                
                except Exception as e:
                    step_time = (time.time() - step_start) * 1000
                    error_test_results[scenario_name_inner] = {
                        "success": False,
                        "response_time_ms": step_time,
                        "exception": str(e)
                    }
                    self.logger.warning(f"⚠ {scenario_name_inner}: Exception raised: {e}")
            
            # Evaluate overall error handling
            successful_error_handling = sum(1 for r in error_test_results.values() if r["success"])
            total_error_tests = len(error_scenarios)
            
            result["steps"]["error_handling"] = {
                "success": successful_error_handling >= total_error_tests * 0.75,  # 75% threshold
                "results": error_test_results,
                "successful_handling": successful_error_handling,
                "total_tests": total_error_tests,
                "success_rate": (successful_error_handling / total_error_tests) * 100
            }
            
            if result["steps"]["error_handling"]["success"]:
                self.logger.info(f"✓ Error handling: {successful_error_handling}/{total_error_tests} scenarios handled well")
            else:
                result["success"] = False
                result["errors"].append("Error handling needs improvement")
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Error scenario testing failed: {e}")
            self.logger.error(f"✗ Error scenario testing failed: {e}")
        
        result["performance"] = {
            "total_time_ms": (time.time() - start_time) * 1000
        }
        
        self.test_results["test_scenarios"][scenario_name] = result
        return result
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks for Central district search."""
        scenario_name = "performance_benchmarks"
        self.logger.info("Testing performance benchmarks")
        
        start_time = time.time()
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "steps": {},
            "errors": [],
            "performance": {}
        }
        
        try:
            # Performance test configuration
            num_iterations = 3
            search_times = []
            recommendation_times = []
            total_times = []
            
            for i in range(num_iterations):
                iteration_start = time.time()
                
                # Search phase
                search_start = time.time()
                search_result = await self.gateway_client.search_restaurants_by_district(["Central district"])
                search_time = (time.time() - search_start) * 1000
                search_times.append(search_time)
                
                if search_result.get("success", False) and search_result.get("restaurants"):
                    # Recommendation phase
                    recommend_start = time.time()
                    recommend_result = await self.gateway_client.recommend_restaurants(
                        search_result["restaurants"][:5]
                    )
                    recommend_time = (time.time() - recommend_start) * 1000
                    recommendation_times.append(recommend_time)
                else:
                    recommendation_times.append(0)
                
                total_time = (time.time() - iteration_start) * 1000
                total_times.append(total_time)
                
                self.logger.debug(f"Iteration {i+1}: {total_time:.2f}ms total")
                
                # Small delay between iterations
                await asyncio.sleep(0.5)
            
            # Calculate statistics
            def calculate_stats(times):
                if not times:
                    return {"avg": 0, "min": 0, "max": 0, "median": 0}
                
                times_sorted = sorted(times)
                return {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "median": times_sorted[len(times_sorted) // 2]
                }
            
            search_stats = calculate_stats(search_times)
            recommendation_stats = calculate_stats(recommendation_times)
            total_stats = calculate_stats(total_times)
            
            # Performance thresholds (in milliseconds)
            thresholds = {
                "search_max": 15000,      # 15 seconds
                "recommendation_max": 20000,  # 20 seconds
                "total_max": 30000        # 30 seconds
            }
            
            performance_checks = {
                "search_performance": search_stats["avg"] <= thresholds["search_max"],
                "recommendation_performance": recommendation_stats["avg"] <= thresholds["recommendation_max"],
                "total_performance": total_stats["avg"] <= thresholds["total_max"]
            }
            
            result["steps"]["performance_analysis"] = {
                "success": all(performance_checks.values()),
                "iterations": num_iterations,
                "search_stats": search_stats,
                "recommendation_stats": recommendation_stats,
                "total_stats": total_stats,
                "thresholds": thresholds,
                "performance_checks": performance_checks
            }
            
            if result["steps"]["performance_analysis"]["success"]:
                self.logger.info(f"✓ Performance benchmarks met: {total_stats['avg']:.2f}ms avg total time")
            else:
                result["success"] = False
                result["errors"].append("Performance benchmarks not met")
                self.logger.warning(f"⚠ Performance concerns: {total_stats['avg']:.2f}ms avg total time")
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Performance benchmark error: {e}")
            self.logger.error(f"✗ Performance benchmark testing failed: {e}")
        
        result["performance"] = {
            "total_time_ms": (time.time() - start_time) * 1000
        }
        
        self.test_results["test_scenarios"][scenario_name] = result
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Central district E2E tests."""
        self.logger.info(f"Starting Central district E2E tests for {self.environment}")
        start_time = time.time()
        
        # Run all test scenarios
        test_scenarios = [
            self.test_basic_search_workflow(),
            self.test_complete_workflow_service(),
            self.test_meal_type_filtering(),
            self.test_error_scenarios(),
            self.test_performance_benchmarks()
        ]
        
        results = await asyncio.gather(*test_scenarios, return_exceptions=True)
        
        # Process results
        successful_scenarios = 0
        total_scenarios = len(test_scenarios)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scenario_name = f"scenario_{i}"
                self.logger.error(f"Scenario {scenario_name} raised exception: {result}")
                self.test_results["test_scenarios"][scenario_name] = {
                    "scenario_name": scenario_name,
                    "success": False,
                    "error": str(result)
                }
            elif result.get("success", False):
                successful_scenarios += 1
        
        # Calculate performance metrics
        total_test_time = time.time() - start_time
        
        # Aggregate performance data
        all_response_times = []
        for scenario_result in self.test_results["test_scenarios"].values():
            if "performance" in scenario_result:
                total_time = scenario_result["performance"].get("total_time_ms", 0)
                if total_time > 0:
                    all_response_times.append(total_time)
        
        self.test_results["performance_metrics"] = {
            "total_test_duration_seconds": total_test_time,
            "average_scenario_time_ms": sum(all_response_times) / len(all_response_times) if all_response_times else 0,
            "fastest_scenario_ms": min(all_response_times) if all_response_times else 0,
            "slowest_scenario_ms": max(all_response_times) if all_response_times else 0
        }
        
        # Generate summary
        self.test_results["summary"] = {
            "total_scenarios": total_scenarios,
            "successful_scenarios": successful_scenarios,
            "success_rate_percent": (successful_scenarios / total_scenarios) * 100,
            "overall_success": successful_scenarios == total_scenarios,
            "environment": self.environment,
            "test_duration_seconds": total_test_time,
            "central_district_functionality": "WORKING" if successful_scenarios >= total_scenarios * 0.8 else "ISSUES"
        }
        
        # Log summary
        summary = self.test_results["summary"]
        if summary["overall_success"]:
            self.logger.info(f"✓ All E2E tests passed ({successful_scenarios}/{total_scenarios})")
            self.logger.info("✓ Central district functionality is WORKING")
        else:
            self.logger.warning(f"⚠ Some E2E tests failed ({successful_scenarios}/{total_scenarios})")
            if summary["central_district_functionality"] == "WORKING":
                self.logger.info("✓ Central district functionality is mostly WORKING")
            else:
                self.logger.warning("✗ Central district functionality has ISSUES")
        
        return self.test_results
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """Save test results to a JSON file."""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"central_district_e2e_test_{self.environment}_{timestamp}.json"
        
        output_path = project_root / "tests" / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"Test results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self) -> None:
        """Print a formatted summary of test results."""
        summary = self.test_results.get("summary", {})
        performance = self.test_results.get("performance_metrics", {})
        
        print("\n" + "="*70)
        print(f"CENTRAL DISTRICT E2E TEST SUMMARY")
        print("="*70)
        print(f"Environment: {summary.get('environment', 'Unknown')}")
        print(f"Test Time: {self.test_results.get('timestamp', 'Unknown')}")
        print(f"Duration: {summary.get('test_duration_seconds', 0):.2f} seconds")
        print()
        
        functionality_status = summary.get('central_district_functionality', 'UNKNOWN')
        status_symbol = "✓" if functionality_status == "WORKING" else "⚠" if "WORKING" in functionality_status else "✗"
        print(f"Central District Status: {status_symbol} {functionality_status}")
        print(f"Success Rate: {summary.get('success_rate_percent', 0):.1f}% ({summary.get('successful_scenarios', 0)}/{summary.get('total_scenarios', 0)})")
        print()
        
        print("Performance Metrics:")
        print(f"  Average Scenario Time: {performance.get('average_scenario_time_ms', 0):.2f}ms")
        print(f"  Fastest Scenario: {performance.get('fastest_scenario_ms', 0):.2f}ms")
        print(f"  Slowest Scenario: {performance.get('slowest_scenario_ms', 0):.2f}ms")
        print()
        
        print("Test Scenario Results:")
        print("-" * 50)
        
        for scenario_name, scenario_result in self.test_results.get("test_scenarios", {}).items():
            status = "✓ PASS" if scenario_result.get("success") else "✗ FAIL"
            scenario_time = scenario_result.get("performance", {}).get("total_time_ms", 0)
            
            print(f"{scenario_name:30} {status:8} {scenario_time:8.2f}ms")
            
            # Show step details for failed scenarios
            if not scenario_result.get("success"):
                errors = scenario_result.get("errors", [])
                for error in errors[:2]:  # Show first 2 errors
                    print(f"  Error: {error}")
        
        print("\n" + "="*70)


async def main():
    """Main function to run Central district E2E tests."""
    parser = argparse.ArgumentParser(description="Test Central district search functionality end-to-end")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Environment to test (default: production)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for test results (default: auto-generated)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress summary output"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = CentralDistrictE2ETester(
        environment=args.environment,
        verbose=args.verbose
    )
    
    try:
        # Run tests
        results = await tester.run_all_tests()
        
        # Save results
        output_file = tester.save_results(args.output)
        
        # Print summary unless quiet mode
        if not args.quiet:
            tester.print_summary()
        
        # Exit with appropriate code
        success = results.get("summary", {}).get("overall_success", False)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())