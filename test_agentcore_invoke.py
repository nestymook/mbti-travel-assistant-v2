#!/usr/bin/env python3
"""
Test AgentCore Runtime using direct invoke API.

This script tests the deployed MCP server by directly calling the
invoke_agent_runtime API.
"""

import json
import os
import sys
import time
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError


class AgentCoreInvokeTester:
    """Test AgentCore Runtime using invoke API."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize invoke tester.
        
        Args:
            region: AWS region where agent is deployed.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Agent information from deployment
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_mcp-JZdACMALGo"
        self.agent_id = "restaurant_search_mcp-JZdACMALGo"
        
        # Initialize AgentCore client
        try:
            self.agentcore_client = self.session.client('bedrock-agentcore', region_name=region)
            print(f"✓ AgentCore client initialized for region: {region}")
        except Exception as e:
            print(f"✗ Failed to initialize AgentCore client: {e}")
            raise
    
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            with open('cognito_config.json', 'r') as f:
                config = json.load(f)
            print(f"✓ Loaded Cognito configuration")
            return config
        except Exception as e:
            print(f"✗ Error loading Cognito config: {e}")
            return {}
    
    def invoke_agent_with_prompt(self, prompt: str, session_id: str = None) -> Dict[str, Any]:
        """Invoke the agent with a prompt.
        
        Args:
            prompt: The prompt to send to the agent.
            session_id: Optional session ID for conversation continuity.
            
        Returns:
            Dictionary containing the response and metadata.
        """
        try:
            print(f"🚀 Invoking agent with prompt: {prompt[:100]}...")
            
            # Prepare invoke parameters
            invoke_params = {
                'agentRuntimeArn': self.agent_arn,
                'payload': json.dumps({'prompt': prompt})
            }
            
            # Add session ID if provided
            if session_id:
                invoke_params['runtimeSessionId'] = session_id
                print(f"Using session ID: {session_id}")
            
            # Invoke the agent
            response = self.agentcore_client.invoke_agent_runtime(**invoke_params)
            
            print(f"✓ Agent invocation successful")
            print(f"Response keys: {list(response.keys())}")
            
            # Extract response content
            response_data = {
                'success': True,
                'response_metadata': response.get('ResponseMetadata', {}),
                'session_id': response.get('agentRuntimeSessionId'),
                'raw_response': response
            }
            
            # Check if there's a completion field
            if 'completion' in response:
                response_data['completion'] = response['completion']
                print(f"✓ Completion received: {len(str(response['completion']))} characters")
            
            # Check for streaming response
            if 'body' in response:
                print("✓ Streaming response detected")
                response_data['has_streaming_body'] = True
                
                # Try to read the streaming response
                try:
                    body_content = []
                    for event in response['body']:
                        if 'chunk' in event:
                            chunk = event['chunk']
                            if 'bytes' in chunk:
                                chunk_data = chunk['bytes'].decode('utf-8')
                                body_content.append(chunk_data)
                                print(f"Received chunk: {len(chunk_data)} bytes")
                        elif 'trace' in event:
                            print(f"Trace event: {event['trace']}")
                    
                    response_data['body_content'] = ''.join(body_content)
                    print(f"✓ Total streaming content: {len(response_data['body_content'])} characters")
                    
                except Exception as e:
                    print(f"⚠️ Error reading streaming response: {e}")
                    response_data['streaming_error'] = str(e)
            
            return response_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ AWS API Error: {error_code} - {error_message}")
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_message,
                'error': f"{error_code}: {error_message}"
            }
        except Exception as e:
            print(f"✗ Error invoking agent: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_simple_greeting(self) -> Dict[str, Any]:
        """Test simple greeting to verify basic connectivity."""
        try:
            print("\n🧪 Testing simple greeting...")
            
            prompt = "Hello! Can you help me?"
            result = self.invoke_agent_with_prompt(prompt)
            
            test_result = {
                'test_name': 'simple_greeting',
                'prompt': prompt,
                'success': result.get('success', False),
                'result': result
            }
            
            if result.get('success'):
                print("✓ Simple greeting test completed successfully")
            else:
                print(f"✗ Simple greeting test failed: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            print(f"✗ Simple greeting test error: {e}")
            return {
                'test_name': 'simple_greeting',
                'success': False,
                'error': str(e)
            }
    
    def test_restaurant_search_district(self) -> Dict[str, Any]:
        """Test restaurant search by district."""
        try:
            print("\n🧪 Testing restaurant search by district...")
            
            prompt = "Please search for restaurants in Central district using the search_restaurants_by_district tool with districts parameter set to ['Central district']."
            result = self.invoke_agent_with_prompt(prompt)
            
            test_result = {
                'test_name': 'restaurant_search_district',
                'prompt': prompt,
                'success': result.get('success', False),
                'result': result
            }
            
            if result.get('success'):
                print("✓ Restaurant search by district test completed successfully")
            else:
                print(f"✗ Restaurant search by district test failed: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            print(f"✗ Restaurant search by district test error: {e}")
            return {
                'test_name': 'restaurant_search_district',
                'success': False,
                'error': str(e)
            }
    
    def test_restaurant_search_meal_type(self) -> Dict[str, Any]:
        """Test restaurant search by meal type."""
        try:
            print("\n🧪 Testing restaurant search by meal type...")
            
            prompt = "Find restaurants that serve breakfast using the search_restaurants_by_meal_type tool with meal_types parameter set to ['breakfast']."
            result = self.invoke_agent_with_prompt(prompt)
            
            test_result = {
                'test_name': 'restaurant_search_meal_type',
                'prompt': prompt,
                'success': result.get('success', False),
                'result': result
            }
            
            if result.get('success'):
                print("✓ Restaurant search by meal type test completed successfully")
            else:
                print(f"✗ Restaurant search by meal type test failed: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            print(f"✗ Restaurant search by meal type test error: {e}")
            return {
                'test_name': 'restaurant_search_meal_type',
                'success': False,
                'error': str(e)
            }
    
    def test_combined_search(self) -> Dict[str, Any]:
        """Test combined restaurant search."""
        try:
            print("\n🧪 Testing combined restaurant search...")
            
            prompt = "Search for restaurants in Central district that serve dinner using the search_restaurants_combined tool with districts=['Central district'] and meal_types=['dinner']."
            result = self.invoke_agent_with_prompt(prompt)
            
            test_result = {
                'test_name': 'combined_search',
                'prompt': prompt,
                'success': result.get('success', False),
                'result': result
            }
            
            if result.get('success'):
                print("✓ Combined search test completed successfully")
            else:
                print(f"✗ Combined search test failed: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            print(f"✗ Combined search test error: {e}")
            return {
                'test_name': 'combined_search',
                'success': False,
                'error': str(e)
            }
    
    def test_conversational_request(self) -> Dict[str, Any]:
        """Test conversational restaurant request."""
        try:
            print("\n🧪 Testing conversational restaurant request...")
            
            prompt = "I'm visiting Hong Kong and looking for good breakfast places in Central district. Can you help me find some restaurants?"
            result = self.invoke_agent_with_prompt(prompt)
            
            test_result = {
                'test_name': 'conversational_request',
                'prompt': prompt,
                'success': result.get('success', False),
                'result': result
            }
            
            if result.get('success'):
                print("✓ Conversational request test completed successfully")
            else:
                print(f"✗ Conversational request test failed: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            print(f"✗ Conversational request test error: {e}")
            return {
                'test_name': 'conversational_request',
                'success': False,
                'error': str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("🚀 Starting comprehensive AgentCore invoke tests...")
        print(f"Agent ARN: {self.agent_arn}")
        
        # Run tests
        test_results = []
        
        # Test 1: Simple greeting
        result1 = self.test_simple_greeting()
        test_results.append(result1)
        
        # Test 2: District search
        result2 = self.test_restaurant_search_district()
        test_results.append(result2)
        
        # Test 3: Meal type search
        result3 = self.test_restaurant_search_meal_type()
        test_results.append(result3)
        
        # Test 4: Combined search
        result4 = self.test_combined_search()
        test_results.append(result4)
        
        # Test 5: Conversational request
        result5 = self.test_conversational_request()
        test_results.append(result5)
        
        # Calculate results
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        total_tests = len(test_results)
        overall_success = successful_tests > 0  # At least one test should pass
        
        # Compile final results
        final_results = {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'success_rate': f"{successful_tests}/{total_tests} ({(successful_tests/total_tests)*100:.1f}%)",
            'agent_arn': self.agent_arn,
            'tests': test_results,
            'timestamp': time.time()
        }
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"Overall Success: {overall_success}")
        print(f"Success Rate: {final_results['success_rate']}")
        print(f"Agent ARN: {self.agent_arn}")
        
        for i, result in enumerate(test_results, 1):
            test_name = result.get('test_name', f'test_{i}')
            success = result.get('success', False)
            status_icon = "✓" if success else "✗"
            print(f"{status_icon} Test {i} ({test_name}): {'PASSED' if success else 'FAILED'}")
            if not success and 'error' in result:
                print(f"   Error: {result['error']}")
        
        # Save results
        try:
            with open('agentcore_invoke_test_results.json', 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            print(f"\n✓ Test results saved to: agentcore_invoke_test_results.json")
        except Exception as e:
            print(f"✗ Failed to save test results: {e}")
        
        return final_results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AgentCore Runtime using invoke API')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--test', choices=['greeting', 'district', 'meal_type', 'combined', 'conversational', 'all'],
                       default='all', help='Specific test to run (default: all)')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = AgentCoreInvokeTester(region=args.region)
        
        if args.test == 'all':
            # Run comprehensive tests
            results = tester.run_comprehensive_tests()
            return 0 if results['overall_success'] else 1
        
        else:
            # Run specific test
            test_methods = {
                'greeting': tester.test_simple_greeting,
                'district': tester.test_restaurant_search_district,
                'meal_type': tester.test_restaurant_search_meal_type,
                'combined': tester.test_combined_search,
                'conversational': tester.test_conversational_request
            }
            
            if args.test in test_methods:
                result = test_methods[args.test]()
                print(f"\nTest Result: {json.dumps(result, indent=2, default=str)}")
                return 0 if result.get('success', False) else 1
            else:
                print(f"Unknown test: {args.test}")
                return 1
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())