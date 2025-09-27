#!/usr/bin/env python3
"""
Direct test of deployed AgentCore Runtime using boto3 client.

This script tests the deployed MCP server by directly calling the
AgentCore Runtime API using boto3, bypassing the toolkit configuration issues.
"""

import json
import os
import sys
import time
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError


class DirectAgentCoreTester:
    """Test AgentCore Runtime directly using boto3."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize direct tester.
        
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
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent runtime status."""
        try:
            print("🔍 Checking agent runtime status...")
            
            response = self.agentcore_client.get_agent_runtime(
                agentRuntimeArn=self.agent_arn
            )
            
            status = response.get('status', 'UNKNOWN')
            print(f"Agent Status: {status}")
            
            return {
                'status': status,
                'ready': status == 'READY',
                'response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ AWS API Error: {error_code} - {error_message}")
            return {'ready': False, 'error': f"{error_code}: {error_message}"}
        except Exception as e:
            print(f"✗ Error getting agent status: {e}")
            return {'ready': False, 'error': str(e)}
    
    def get_endpoint_status(self) -> Dict[str, Any]:
        """Get agent runtime endpoint status."""
        try:
            print("🔍 Checking agent runtime endpoint status...")
            
            response = self.agentcore_client.get_agent_runtime_endpoint(
                agentRuntimeArn=self.agent_arn,
                name="DEFAULT"
            )
            
            status = response.get('status', 'UNKNOWN')
            print(f"Endpoint Status: {status}")
            
            return {
                'status': status,
                'ready': status == 'READY',
                'response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ AWS API Error: {error_code} - {error_message}")
            return {'ready': False, 'error': f"{error_code}: {error_message}"}
        except Exception as e:
            print(f"✗ Error getting endpoint status: {e}")
            return {'ready': False, 'error': str(e)}
    
    def create_session(self) -> str:
        """Create a new agent session."""
        try:
            print("🔄 Creating agent session...")
            
            response = self.agentcore_client.create_agent_runtime_session(
                agentRuntimeArn=self.agent_arn
            )
            
            session_id = response.get('agentRuntimeSessionId')
            print(f"✓ Session created: {session_id}")
            
            return session_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ AWS API Error creating session: {error_code} - {error_message}")
            raise
        except Exception as e:
            print(f"✗ Error creating session: {e}")
            raise
    
    def invoke_agent(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """Invoke the agent with a prompt."""
        try:
            print(f"🚀 Invoking agent with prompt: {prompt[:100]}...")
            
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_arn,
                agentRuntimeSessionId=session_id,
                inputText=prompt
            )
            
            print(f"✓ Agent invocation successful")
            return {
                'success': True,
                'response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ AWS API Error invoking agent: {error_code} - {error_message}")
            return {
                'success': False,
                'error': f"{error_code}: {error_message}"
            }
        except Exception as e:
            print(f"✗ Error invoking agent: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_restaurant_search_by_district(self, session_id: str) -> Dict[str, Any]:
        """Test restaurant search by district."""
        try:
            print("\n🧪 Testing restaurant search by district...")
            
            prompt = "Please search for restaurants in Central district and Admiralty using the search_restaurants_by_district tool."
            
            result = self.invoke_agent(session_id, prompt)
            
            if result['success']:
                print("✓ District search test completed")
            else:
                print(f"✗ District search test failed: {result.get('error', 'Unknown error')}")
            
            return {
                'test_name': 'search_by_district',
                'success': result['success'],
                'prompt': prompt,
                'result': result
            }
            
        except Exception as e:
            print(f"✗ District search test error: {e}")
            return {
                'test_name': 'search_by_district',
                'success': False,
                'error': str(e)
            }
    
    def test_restaurant_search_by_meal_type(self, session_id: str) -> Dict[str, Any]:
        """Test restaurant search by meal type."""
        try:
            print("\n🧪 Testing restaurant search by meal type...")
            
            prompt = "Find restaurants that serve breakfast and lunch using the search_restaurants_by_meal_type tool."
            
            result = self.invoke_agent(session_id, prompt)
            
            if result['success']:
                print("✓ Meal type search test completed")
            else:
                print(f"✗ Meal type search test failed: {result.get('error', 'Unknown error')}")
            
            return {
                'test_name': 'search_by_meal_type',
                'success': result['success'],
                'prompt': prompt,
                'result': result
            }
            
        except Exception as e:
            print(f"✗ Meal type search test error: {e}")
            return {
                'test_name': 'search_by_meal_type',
                'success': False,
                'error': str(e)
            }
    
    def test_combined_search(self, session_id: str) -> Dict[str, Any]:
        """Test combined restaurant search."""
        try:
            print("\n🧪 Testing combined restaurant search...")
            
            prompt = "Search for restaurants in Central district that serve dinner using the search_restaurants_combined tool."
            
            result = self.invoke_agent(session_id, prompt)
            
            if result['success']:
                print("✓ Combined search test completed")
            else:
                print(f"✗ Combined search test failed: {result.get('error', 'Unknown error')}")
            
            return {
                'test_name': 'combined_search',
                'success': result['success'],
                'prompt': prompt,
                'result': result
            }
            
        except Exception as e:
            print(f"✗ Combined search test error: {e}")
            return {
                'test_name': 'combined_search',
                'success': False,
                'error': str(e)
            }
    
    def test_conversational_prompt(self, session_id: str) -> Dict[str, Any]:
        """Test conversational prompt."""
        try:
            print("\n🧪 Testing conversational prompt...")
            
            prompt = "Hello! I'm visiting Hong Kong and looking for good restaurants. Can you help me find some places in Central district that serve breakfast?"
            
            result = self.invoke_agent(session_id, prompt)
            
            if result['success']:
                print("✓ Conversational prompt test completed")
            else:
                print(f"✗ Conversational prompt test failed: {result.get('error', 'Unknown error')}")
            
            return {
                'test_name': 'conversational_prompt',
                'success': result['success'],
                'prompt': prompt,
                'result': result
            }
            
        except Exception as e:
            print(f"✗ Conversational prompt test error: {e}")
            return {
                'test_name': 'conversational_prompt',
                'success': False,
                'error': str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("🚀 Starting comprehensive AgentCore Runtime tests...")
        
        # Check agent status
        agent_status = self.get_agent_status()
        if not agent_status.get('ready', False):
            print("✗ Agent not ready for testing")
            return {
                'overall_success': False,
                'agent_status': agent_status,
                'tests': []
            }
        
        # Check endpoint status
        endpoint_status = self.get_endpoint_status()
        if not endpoint_status.get('ready', False):
            print("✗ Endpoint not ready for testing")
            return {
                'overall_success': False,
                'agent_status': agent_status,
                'endpoint_status': endpoint_status,
                'tests': []
            }
        
        print("✓ Agent and endpoint are ready for testing")
        
        # Create session
        try:
            session_id = self.create_session()
        except Exception as e:
            print(f"✗ Failed to create session: {e}")
            return {
                'overall_success': False,
                'agent_status': agent_status,
                'endpoint_status': endpoint_status,
                'session_error': str(e),
                'tests': []
            }
        
        # Run tests
        test_results = []
        
        # Test 1: District search
        result1 = self.test_restaurant_search_by_district(session_id)
        test_results.append(result1)
        
        # Test 2: Meal type search
        result2 = self.test_restaurant_search_by_meal_type(session_id)
        test_results.append(result2)
        
        # Test 3: Combined search
        result3 = self.test_combined_search(session_id)
        test_results.append(result3)
        
        # Test 4: Conversational prompt
        result4 = self.test_conversational_prompt(session_id)
        test_results.append(result4)
        
        # Calculate results
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        total_tests = len(test_results)
        overall_success = successful_tests == total_tests
        
        # Compile final results
        final_results = {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'success_rate': f"{successful_tests}/{total_tests} ({(successful_tests/total_tests)*100:.1f}%)",
            'agent_status': agent_status,
            'endpoint_status': endpoint_status,
            'session_id': session_id,
            'tests': test_results,
            'timestamp': time.time()
        }
        
        # Print summary
        print(f"\n📊 Test Results Summary:")
        print(f"Overall Success: {overall_success}")
        print(f"Success Rate: {final_results['success_rate']}")
        print(f"Session ID: {session_id}")
        
        for i, result in enumerate(test_results, 1):
            test_name = result.get('test_name', f'test_{i}')
            success = result.get('success', False)
            status_icon = "✓" if success else "✗"
            print(f"{status_icon} Test {i} ({test_name}): {'PASSED' if success else 'FAILED'}")
            if not success and 'error' in result:
                print(f"   Error: {result['error']}")
        
        # Save results
        try:
            with open('agentcore_direct_test_results.json', 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            print(f"\n✓ Test results saved to: agentcore_direct_test_results.json")
        except Exception as e:
            print(f"✗ Failed to save test results: {e}")
        
        return final_results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AgentCore Runtime directly')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--status-only', action='store_true', help='Only check status')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = DirectAgentCoreTester(region=args.region)
        
        if args.status_only:
            # Just check status
            agent_status = tester.get_agent_status()
            endpoint_status = tester.get_endpoint_status()
            
            print(f"\nAgent Status: {json.dumps(agent_status, indent=2, default=str)}")
            print(f"\nEndpoint Status: {json.dumps(endpoint_status, indent=2, default=str)}")
            
            ready = agent_status.get('ready', False) and endpoint_status.get('ready', False)
            return 0 if ready else 1
        
        else:
            # Run comprehensive tests
            results = tester.run_comprehensive_tests()
            return 0 if results['overall_success'] else 1
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())