#!/usr/bin/env python3
"""
Gateway Connectivity and Endpoint Availability Test Script

This script tests gateway connectivity and endpoint availability for the
mbti-travel-planner-agent integration with agentcore-gateway-mcp-tools.

Features:
- Tests all gateway endpoints across environments
- Validates response formats and status codes
- Measures response times and availability
- Generates detailed connectivity reports
- Supports authentication testing
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

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.environment_loader import EnvironmentConfigLoader
from services.logging_service import get_logging_service
from services.error_handler import ErrorHandler


class GatewayConnectivityTester:
    """Test gateway connectivity and endpoint availability."""
    
    def __init__(self, environment: str = "production", verbose: bool = False):
        """
        Initialize the connectivity tester.
        
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
        self.logger = logging.getLogger("gateway_connectivity_test")
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.error_handler = ErrorHandler("connectivity_test")
        
        # Load environment configuration
        self.env_loader = EnvironmentConfigLoader()
        self.config = self._load_gateway_config()
        
        # Test results
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": environment,
            "tests": {},
            "summary": {}
        }
        
        self.logger.info(f"Initialized gateway connectivity tester for {environment}")
    
    def _load_gateway_config(self) -> Dict[str, Any]:
        """Load gateway configuration for the specified environment."""
        try:
            gateway_config_path = project_root / "config" / "environments" / "gateway.json"
            
            if not gateway_config_path.exists():
                raise FileNotFoundError(f"Gateway config not found: {gateway_config_path}")
            
            with open(gateway_config_path, 'r') as f:
                all_configs = json.load(f)
            
            if self.environment not in all_configs:
                raise ValueError(f"Environment '{self.environment}' not found in gateway config")
            
            config = all_configs[self.environment]
            self.logger.info(f"Loaded gateway config for {self.environment}: {config['base_url']}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load gateway config: {e}")
            raise
    
    async def test_basic_connectivity(self) -> Dict[str, Any]:
        """Test basic connectivity to the gateway."""
        test_name = "basic_connectivity"
        self.logger.info(f"Testing basic connectivity to {self.config['base_url']}")
        
        start_time = time.time()
        result = {
            "test_name": test_name,
            "endpoint": self.config['base_url'],
            "success": False,
            "response_time_ms": 0,
            "error": None,
            "details": {}
        }
        
        try:
            timeout = httpx.Timeout(self.config.get('timeout', 30))
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Test basic connectivity with a simple GET request
                response = await client.get(self.config['base_url'])
                
                result["response_time_ms"] = (time.time() - start_time) * 1000
                result["success"] = True
                result["details"] = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "response_size": len(response.content) if response.content else 0
                }
                
                self.logger.info(f"✓ Basic connectivity test passed: {response.status_code}")
                
        except httpx.TimeoutException:
            result["response_time_ms"] = (time.time() - start_time) * 1000
            result["error"] = f"Connection timeout after {self.config.get('timeout', 30)}s"
            self.logger.error(f"✗ Basic connectivity test failed: timeout")
            
        except Exception as e:
            result["response_time_ms"] = (time.time() - start_time) * 1000
            result["error"] = str(e)
            self.logger.error(f"✗ Basic connectivity test failed: {e}")
        
        self.test_results["tests"][test_name] = result
        return result
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health check endpoint."""
        test_name = "health_endpoint"
        health_url = f"{self.config['base_url']}{self.config.get('health_check_endpoint', '/health')}"
        
        self.logger.info(f"Testing health endpoint: {health_url}")
        
        start_time = time.time()
        result = {
            "test_name": test_name,
            "endpoint": health_url,
            "success": False,
            "response_time_ms": 0,
            "error": None,
            "details": {}
        }
        
        try:
            timeout = httpx.Timeout(self.config.get('timeout', 30))
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(health_url)
                
                result["response_time_ms"] = (time.time() - start_time) * 1000
                result["success"] = response.status_code == 200
                
                # Parse health response
                health_data = {}
                try:
                    if response.headers.get("content-type", "").startswith("application/json"):
                        health_data = response.json()
                except Exception:
                    pass
                
                result["details"] = {
                    "status_code": response.status_code,
                    "health_data": health_data,
                    "response_size": len(response.content) if response.content else 0
                }
                
                if result["success"]:
                    self.logger.info(f"✓ Health endpoint test passed: {response.status_code}")
                else:
                    self.logger.warning(f"⚠ Health endpoint returned {response.status_code}")
                
        except Exception as e:
            result["response_time_ms"] = (time.time() - start_time) * 1000
            result["error"] = str(e)
            self.logger.error(f"✗ Health endpoint test failed: {e}")
        
        self.test_results["tests"][test_name] = result
        return result
    
    async def test_restaurant_endpoints(self) -> Dict[str, Any]:
        """Test all restaurant API endpoints."""
        test_name = "restaurant_endpoints"
        self.logger.info("Testing restaurant API endpoints")
        
        endpoints_to_test = [
            {
                "name": "district_search",
                "path": self.config['endpoints']['restaurant_search_district'],
                "method": "POST",
                "payload": {"districts": ["Central district"]},
                "expected_status": [200, 400, 422]
            },
            {
                "name": "combined_search", 
                "path": self.config['endpoints']['restaurant_search_combined'],
                "method": "POST",
                "payload": {"districts": ["Central district"], "meal_types": ["lunch"]},
                "expected_status": [200, 400, 422]
            },
            {
                "name": "recommendation",
                "path": self.config['endpoints']['restaurant_recommend'],
                "method": "POST",
                "payload": {
                    "restaurants": [
                        {
                            "id": "test_001",
                            "name": "Test Restaurant",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ],
                    "ranking_method": "sentiment_likes"
                },
                "expected_status": [200, 400, 422]
            }
        ]
        
        endpoint_results = {}
        overall_success = True
        
        timeout = httpx.Timeout(self.config.get('timeout', 30))
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            for endpoint_config in endpoints_to_test:
                endpoint_name = endpoint_config["name"]
                endpoint_url = f"{self.config['base_url']}{endpoint_config['path']}"
                
                self.logger.info(f"Testing {endpoint_name}: {endpoint_url}")
                
                start_time = time.time()
                endpoint_result = {
                    "endpoint": endpoint_url,
                    "method": endpoint_config["method"],
                    "success": False,
                    "response_time_ms": 0,
                    "error": None,
                    "details": {}
                }
                
                try:
                    # Add authentication headers if required
                    headers = {"Content-Type": "application/json"}
                    if self.config.get('auth_required', False):
                        # For testing purposes, we'll test without auth first
                        # In production, you would add proper JWT tokens here
                        pass
                    
                    if endpoint_config["method"] == "POST":
                        response = await client.post(
                            endpoint_url,
                            json=endpoint_config["payload"],
                            headers=headers
                        )
                    else:
                        response = await client.get(endpoint_url, headers=headers)
                    
                    endpoint_result["response_time_ms"] = (time.time() - start_time) * 1000
                    endpoint_result["success"] = response.status_code in endpoint_config["expected_status"]
                    
                    # Parse response data
                    response_data = {}
                    try:
                        if response.headers.get("content-type", "").startswith("application/json"):
                            response_data = response.json()
                    except Exception:
                        pass
                    
                    endpoint_result["details"] = {
                        "status_code": response.status_code,
                        "response_data": response_data,
                        "response_size": len(response.content) if response.content else 0,
                        "expected_status": endpoint_config["expected_status"]
                    }
                    
                    if endpoint_result["success"]:
                        self.logger.info(f"✓ {endpoint_name} test passed: {response.status_code}")
                    else:
                        self.logger.warning(f"⚠ {endpoint_name} returned unexpected status: {response.status_code}")
                        overall_success = False
                    
                except Exception as e:
                    endpoint_result["response_time_ms"] = (time.time() - start_time) * 1000
                    endpoint_result["error"] = str(e)
                    self.logger.error(f"✗ {endpoint_name} test failed: {e}")
                    overall_success = False
                
                endpoint_results[endpoint_name] = endpoint_result
        
        result = {
            "test_name": test_name,
            "success": overall_success,
            "endpoints": endpoint_results,
            "total_endpoints": len(endpoints_to_test),
            "successful_endpoints": sum(1 for r in endpoint_results.values() if r["success"])
        }
        
        self.test_results["tests"][test_name] = result
        return result
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics by making multiple requests."""
        test_name = "performance_metrics"
        self.logger.info("Testing performance metrics")
        
        # Test configuration
        num_requests = 5
        endpoint_url = f"{self.config['base_url']}{self.config.get('health_check_endpoint', '/health')}"
        
        response_times = []
        successful_requests = 0
        errors = []
        
        timeout = httpx.Timeout(self.config.get('timeout', 30))
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            for i in range(num_requests):
                start_time = time.time()
                
                try:
                    response = await client.get(endpoint_url)
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    
                    self.logger.debug(f"Request {i+1}/{num_requests}: {response.status_code} ({response_time:.2f}ms)")
                    
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    errors.append(str(e))
                    self.logger.debug(f"Request {i+1}/{num_requests} failed: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        # Calculate statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        success_rate = (successful_requests / num_requests) * 100
        
        result = {
            "test_name": test_name,
            "endpoint": endpoint_url,
            "success": success_rate >= 80,  # Consider successful if 80%+ requests succeed
            "metrics": {
                "total_requests": num_requests,
                "successful_requests": successful_requests,
                "success_rate_percent": success_rate,
                "avg_response_time_ms": avg_response_time,
                "min_response_time_ms": min_response_time,
                "max_response_time_ms": max_response_time,
                "response_times": response_times,
                "errors": errors
            }
        }
        
        if result["success"]:
            self.logger.info(f"✓ Performance test passed: {success_rate:.1f}% success rate, {avg_response_time:.2f}ms avg")
        else:
            self.logger.warning(f"⚠ Performance test concerns: {success_rate:.1f}% success rate")
        
        self.test_results["tests"][test_name] = result
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all connectivity and availability tests."""
        self.logger.info(f"Starting gateway connectivity tests for {self.environment}")
        
        # Run all tests
        tests = [
            self.test_basic_connectivity(),
            self.test_health_endpoint(),
            self.test_restaurant_endpoints(),
            self.test_performance_metrics()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results and handle exceptions
        successful_tests = 0
        total_tests = len(tests)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_name = f"test_{i}"
                self.logger.error(f"Test {test_name} raised exception: {result}")
                self.test_results["tests"][test_name] = {
                    "test_name": test_name,
                    "success": False,
                    "error": str(result)
                }
            elif result.get("success", False):
                successful_tests += 1
        
        # Generate summary
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate_percent": (successful_tests / total_tests) * 100,
            "overall_success": successful_tests == total_tests,
            "environment": self.environment,
            "gateway_url": self.config['base_url'],
            "test_duration_seconds": time.time() - self._start_time if hasattr(self, '_start_time') else 0
        }
        
        # Log summary
        summary = self.test_results["summary"]
        if summary["overall_success"]:
            self.logger.info(f"✓ All tests passed ({successful_tests}/{total_tests})")
        else:
            self.logger.warning(f"⚠ Some tests failed ({successful_tests}/{total_tests})")
        
        return self.test_results
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """Save test results to a JSON file."""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"gateway_connectivity_test_{self.environment}_{timestamp}.json"
        
        output_path = project_root / "tests" / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"Test results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self) -> None:
        """Print a formatted summary of test results."""
        summary = self.test_results.get("summary", {})
        
        print("\n" + "="*60)
        print(f"GATEWAY CONNECTIVITY TEST SUMMARY")
        print("="*60)
        print(f"Environment: {summary.get('environment', 'Unknown')}")
        print(f"Gateway URL: {summary.get('gateway_url', 'Unknown')}")
        print(f"Test Time: {self.test_results.get('timestamp', 'Unknown')}")
        print(f"Duration: {summary.get('test_duration_seconds', 0):.2f} seconds")
        print()
        
        print(f"Overall Result: {'✓ PASS' if summary.get('overall_success') else '✗ FAIL'}")
        print(f"Success Rate: {summary.get('success_rate_percent', 0):.1f}% ({summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)})")
        print()
        
        print("Test Details:")
        print("-" * 40)
        
        for test_name, test_result in self.test_results.get("tests", {}).items():
            status = "✓ PASS" if test_result.get("success") else "✗ FAIL"
            response_time = test_result.get("response_time_ms", 0)
            error = test_result.get("error", "")
            
            print(f"{test_name:25} {status:8} {response_time:8.2f}ms")
            if error:
                print(f"{'':25} Error: {error}")
        
        print("\n" + "="*60)


async def main():
    """Main function to run gateway connectivity tests."""
    parser = argparse.ArgumentParser(description="Test gateway connectivity and endpoint availability")
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
    tester = GatewayConnectivityTester(
        environment=args.environment,
        verbose=args.verbose
    )
    
    tester._start_time = time.time()
    
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