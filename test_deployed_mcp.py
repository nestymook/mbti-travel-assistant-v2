#!/usr/bin/env python3
"""
Test script for deployed Restaurant Search MCP server on AgentCore Runtime.

This script tests the deployed MCP server using the bedrock-agentcore-starter-toolkit
to invoke the MCP tools with proper authentication.
"""

import json
import os
import sys
import time
from typing import Dict, Any, List

import boto3
from bedrock_agentcore_starter_toolkit import Runtime


class DeployedMCPTester:
    """Test deployed Restaurant Search MCP server."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize MCP tester.
        
        Args:
            region: AWS region where agent is deployed.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.runtime = Runtime()
        
        # Configure runtime to connect to existing deployment
        self._configure_runtime()
    
    def _configure_runtime(self):
        """Configure runtime to connect to existing deployment."""
        try:
            # Load Cognito configuration
            cognito_config = self.load_cognito_config()
            
            # Create JWT authorizer configuration
            auth_config = {
                "customJWTAuthorizer": {
                    "allowedClients": [cognito_config['app_client']['client_id']],
                    "discoveryUrl": cognito_config['discovery_url']
                }
            }
            
            # Configure runtime to connect to existing agent
            self.runtime.configure(
                entrypoint="restaurant_mcp_server.py",
                agent_name="restaurant_search_mcp",
                region=self.region,
                authorizer_configuration=auth_config,
                protocol="MCP",
                auto_create_execution_role=False,  # Don't create new role, use existing
                auto_create_ecr=False  # Don't create new ECR, use existing
            )
            
            print("✓ Runtime configured to connect to existing deployment")
            
        except Exception as e:
            print(f"Warning: Could not configure runtime: {e}")
        
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            with open('cognito_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading Cognito config: {e}")
            return {}
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        try:
            print("🔍 Checking deployment status...")
            status = self.runtime.status()
            
            # Extract key information
            agent_status = getattr(status, 'agent', {}).get('status', 'UNKNOWN')
            endpoint_status = getattr(status, 'endpoint', {}).get('status', 'UNKNOWN')
            
            print(f"Agent Status: {agent_status}")
            print(f"Endpoint Status: {endpoint_status}")
            
            return {
                'agent_status': agent_status,
                'endpoint_status': endpoint_status,
                'ready': agent_status == 'READY' and endpoint_status == 'READY'
            }
            
        except Exception as e:
            print(f"Error getting deployment status: {e}")
            return {'ready': False, 'error': str(e)}
    
    def test_mcp_tool_search_by_district(self) -> Dict[str, Any]:
        """Test search_restaurants_by_district MCP tool."""
        try:
            print("\n🧪 Testing search_restaurants_by_district...")
            
            # Test with valid districts
            test_payload = {
                "prompt": "Search for restaurants in Central district and Admiralty using the search_restaurants_by_district tool",
                "tool_calls": [
                    {
                        "tool_name": "search_restaurants_by_district",
                        "parameters": {
                            "districts": ["Central district", "Admiralty"]
                        }
                    }
                ]
            }
            
            print(f"Invoking with payload: {json.dumps(test_payload, indent=2)}")
            
            # Invoke the deployed agent
            response = self.runtime.invoke(test_payload)
            
            print(f"✓ Response received: {type(response)}")
            print(f"Response content: {response}")
            
            return {
                'success': True,
                'response': response,
                'test_case': 'search_by_district'
            }
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'search_by_district'
            }
    
    def test_mcp_tool_search_by_meal_type(self) -> Dict[str, Any]:
        """Test search_restaurants_by_meal_type MCP tool."""
        try:
            print("\n🧪 Testing search_restaurants_by_meal_type...")
            
            # Test with valid meal types
            test_payload = {
                "prompt": "Find restaurants that serve breakfast and lunch using the search_restaurants_by_meal_type tool",
                "tool_calls": [
                    {
                        "tool_name": "search_restaurants_by_meal_type",
                        "parameters": {
                            "meal_types": ["breakfast", "lunch"]
                        }
                    }
                ]
            }
            
            print(f"Invoking with payload: {json.dumps(test_payload, indent=2)}")
            
            # Invoke the deployed agent
            response = self.runtime.invoke(test_payload)
            
            print(f"✓ Response received: {type(response)}")
            print(f"Response content: {response}")
            
            return {
                'success': True,
                'response': response,
                'test_case': 'search_by_meal_type'
            }
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'search_by_meal_type'
            }
    
    def test_mcp_tool_combined_search(self) -> Dict[str, Any]:
        """Test search_restaurants_combined MCP tool."""
        try:
            print("\n🧪 Testing search_restaurants_combined...")
            
            # Test with both districts and meal types
            test_payload = {
                "prompt": "Search for restaurants in Central district that serve dinner using the search_restaurants_combined tool",
                "tool_calls": [
                    {
                        "tool_name": "search_restaurants_combined",
                        "parameters": {
                            "districts": ["Central district"],
                            "meal_types": ["dinner"]
                        }
                    }
                ]
            }
            
            print(f"Invoking with payload: {json.dumps(test_payload, indent=2)}")
            
            # Invoke the deployed agent
            response = self.runtime.invoke(test_payload)
            
            print(f"✓ Response received: {type(response)}")
            print(f"Response content: {response}")
            
            return {
                'success': True,
                'response': response,
                'test_case': 'combined_search'
            }
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'combined_search'
            }
    
    def test_simple_prompt(self) -> Dict[str, Any]:
        """Test with a simple conversational prompt."""
        try:
            print("\n🧪 Testing simple conversational prompt...")
            
            # Test with natural language prompt
            test_payload = {
                "prompt": "Hello! Can you help me find some good restaurants in Hong Kong? I'm looking for places in Central district that serve breakfast."
            }
            
            print(f"Invoking with payload: {json.dumps(test_payload, indent=2)}")
            
            # Invoke the deployed agent
            response = self.runtime.invoke(test_payload)
            
            print(f"✓ Response received: {type(response)}")
            print(f"Response content: {response}")
            
            return {
                'success': True,
                'response': response,
                'test_case': 'simple_prompt'
            }
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'simple_prompt'
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid parameters."""
        try:
            print("\n🧪 Testing error handling...")
            
            # Test with invalid district
            test_payload = {
                "prompt": "Search for restaurants in an invalid district using the search_restaurants_by_district tool",
                "tool_calls": [
                    {
                        "tool_name": "search_restaurants_by_district",
                        "parameters": {
                            "districts": ["NonExistentDistrict"]
                        }
                    }
                ]
            }
            
            print(f"Invoking with payload: {json.dumps(test_payload, indent=2)}")
            
            # Invoke the deployed agent
            response = self.runtime.invoke(test_payload)
            
            print(f"✓ Response received: {type(response)}")
            print(f"Response content: {response}")
            
            return {
                'success': True,
                'response': response,
                'test_case': 'error_handling'
            }
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'error_handling'
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("🚀 Starting comprehensive MCP server tests...")
        
        # Check deployment status first
        status = self.get_deployment_status()
        if not status.get('ready', False):
            print("✗ Deployment not ready for testing")
            return {
                'overall_success': False,
                'deployment_status': status,
                'tests': []
            }
        
        print("✓ Deployment is ready for testing")
        
        # Run all tests
        test_results = []
        
        # Test 1: District search
        result1 = self.test_mcp_tool_search_by_district()
        test_results.append(result1)
        
        # Test 2: Meal type search
        result2 = self.test_mcp_tool_search_by_meal_type()
        test_results.append(result2)
        
        # Test 3: Combined search
        result3 = self.test_mcp_tool_combined_search()
        test_results.append(result3)
        
        # Test 4: Simple prompt
        result4 = self.test_simple_prompt()
        test_results.append(result4)
        
        # Test 5: Error handling
        result5 = self.test_error_handling()
        test_results.append(result5)
        
        # Calculate overall success
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        total_tests = len(test_results)
        overall_success = successful_tests == total_tests
        
        # Compile results
        final_results = {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'success_rate': f"{successful_tests}/{total_tests} ({(successful_tests/total_tests)*100:.1f}%)",
            'deployment_status': status,
            'tests': test_results,
            'timestamp': time.time()
        }
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"Overall Success: {overall_success}")
        print(f"Success Rate: {final_results['success_rate']}")
        
        for i, result in enumerate(test_results, 1):
            test_case = result.get('test_case', f'test_{i}')
            success = result.get('success', False)
            status_icon = "✓" if success else "✗"
            print(f"{status_icon} Test {i} ({test_case}): {'PASSED' if success else 'FAILED'}")
            if not success and 'error' in result:
                print(f"   Error: {result['error']}")
        
        # Save results to file
        try:
            with open('deployed_mcp_test_results.json', 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            print(f"\n✓ Test results saved to: deployed_mcp_test_results.json")
        except Exception as e:
            print(f"✗ Failed to save test results: {e}")
        
        return final_results


def main():
    """Main function to run MCP tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test deployed Restaurant Search MCP server')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--test', choices=['district', 'meal_type', 'combined', 'simple', 'error', 'all'],
                       default='all', help='Specific test to run (default: all)')
    parser.add_argument('--status-only', action='store_true', help='Only check deployment status')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = DeployedMCPTester(region=args.region)
        
        if args.status_only:
            # Just check status
            status = tester.get_deployment_status()
            print(f"Deployment Status: {json.dumps(status, indent=2)}")
            return 0 if status.get('ready', False) else 1
        
        elif args.test == 'all':
            # Run comprehensive tests
            results = tester.run_comprehensive_tests()
            return 0 if results['overall_success'] else 1
        
        else:
            # Run specific test
            test_methods = {
                'district': tester.test_mcp_tool_search_by_district,
                'meal_type': tester.test_mcp_tool_search_by_meal_type,
                'combined': tester.test_mcp_tool_combined_search,
                'simple': tester.test_simple_prompt,
                'error': tester.test_error_handling
            }
            
            if args.test in test_methods:
                result = test_methods[args.test]()
                print(f"Test Result: {json.dumps(result, indent=2, default=str)}")
                return 0 if result.get('success', False) else 1
            else:
                print(f"Unknown test: {args.test}")
                return 1
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())