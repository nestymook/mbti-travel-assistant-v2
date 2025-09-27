#!/usr/bin/env python3
"""
Final AgentCore Runtime test with JWT authentication support.

This script tests the deployed MCP server using proper JWT authentication
from Cognito and direct API calls to the AgentCore Runtime.
"""

import json
import os
import sys
import time
import base64
from typing import Dict, Any

import boto3
import requests
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime


class FinalAgentCoreTester:
    """Final comprehensive test of AgentCore Runtime."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize final tester.
        
        Args:
            region: AWS region where agent is deployed.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Agent information from deployment
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_mcp-JZdACMALGo"
        
        # Load Cognito configuration
        self.cognito_config = self.load_cognito_config()
        
        # Initialize clients
        self.cognito_client = self.session.client('cognito-idp', region_name=region)
        self.agentcore_client = self.session.client('bedrock-agentcore', region_name=region)
        
        # Initialize Runtime with proper configuration
        self.runtime = Runtime()
        self._configure_runtime()
        
        print(f"✓ Final tester initialized for region: {region}")
        print(f"✓ Agent ARN: {self.agent_arn}")
    
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            with open('cognito_config.json', 'r') as f:
                config = json.load(f)
            print(f"✓ Loaded Cognito configuration")
            return config
        except Exception as e:
            print(f"✗ Error loading Cognito config: {e}")
            raise
    
    def _configure_runtime(self):
        """Configure runtime to connect to existing deployment."""
        try:
            # Create JWT authorizer configuration
            auth_config = {
                "customJWTAuthorizer": {
                    "allowedClients": [self.cognito_config['app_client']['client_id']],
                    "discoveryUrl": self.cognito_config['discovery_url']
                }
            }
            
            # Configure runtime to connect to existing agent
            self.runtime.configure(
                entrypoint="restaurant_mcp_server.py",
                agent_name="restaurant_search_mcp",
                region=self.region,
                authorizer_configuration=auth_config,
                protocol="MCP",
                auto_create_execution_role=True,
                auto_create_ecr=True
            )
            
            print("✓ Runtime configured successfully")
            
        except Exception as e:
            print(f"Warning: Could not configure runtime: {e}")
    
    def authenticate_with_cognito(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with Cognito and get JWT tokens."""
        try:
            print(f"🔐 Authenticating with Cognito as: {username}")
            
            client_id = self.cognito_config['app_client']['client_id']
            
            # Initiate authentication
            response = self.cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            id_token = auth_result['IdToken']
            refresh_token = auth_result.get('RefreshToken')
            
            print(f"✓ Authentication successful")
            print(f"Access token length: {len(access_token)}")
            
            # Decode token for debugging
            try:
                header, payload, signature = access_token.split('.')
                payload += '=' * (4 - len(payload) % 4)
                decoded_payload = base64.b64decode(payload)
                token_data = json.loads(decoded_payload)
                
                print(f"Token client_id: {token_data.get('client_id', 'N/A')}")
                print(f"Token username: {token_data.get('username', 'N/A')}")
                print(f"Token expires: {token_data.get('exp', 'N/A')}")
                
            except Exception as e:
                print(f"⚠️ Could not decode token: {e}")
            
            return {
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ Cognito authentication failed: {error_code} - {error_message}")
            raise
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            raise
    
    def invoke_agent_with_jwt(self, prompt: str, jwt_tokens: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """Invoke AgentCore Runtime with JWT authentication."""
        try:
            print(f"🚀 Invoking AgentCore with JWT authentication...")
            print(f"Prompt: {prompt[:100]}...")
            
            # Extract the agent ID from ARN
            agent_id = self.agent_arn.split('/')[-1]
            
            # Use the bedrock-agentcore client with custom headers
            # Since the toolkit doesn't support JWT directly, we'll use requests
            
            # Get the AgentCore endpoint URL
            # The actual endpoint format for AgentCore Runtime
            endpoint_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com"
            
            # Prepare the request
            headers = {
                'Authorization': f"Bearer {jwt_tokens['access_token']}",
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'AgentCore-Test-Client/1.0'
            }
            
            # Prepare the payload
            payload = {
                'prompt': prompt
            }
            
            if session_id:
                payload['sessionId'] = session_id
            
            # Try different API endpoint formats
            api_endpoints = [
                f"{endpoint_url}/runtime/{agent_id}/invoke",
                f"{endpoint_url}/agent-runtime/{agent_id}/invoke",
                f"{endpoint_url}/v1/runtime/{agent_id}/invoke",
                f"{endpoint_url}/invoke"
            ]
            
            last_error = None
            
            for api_url in api_endpoints:
                try:
                    print(f"Trying endpoint: {api_url}")
                    
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    print(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        print(f"✓ Agent invocation successful")
                        
                        return {
                            'success': True,
                            'status_code': response.status_code,
                            'response_data': response_data,
                            'endpoint_used': api_url
                        }
                    elif response.status_code == 404:
                        print(f"Endpoint not found, trying next...")
                        continue
                    else:
                        print(f"Error response: {response.text}")
                        last_error = {
                            'status_code': response.status_code,
                            'error': response.text,
                            'endpoint': api_url
                        }
                        
                except requests.exceptions.RequestException as e:
                    print(f"Request error for {api_url}: {e}")
                    last_error = {
                        'error': f"Request error: {str(e)}",
                        'endpoint': api_url
                    }
                    continue
            
            # If we get here, all endpoints failed
            return {
                'success': False,
                'error': 'All API endpoints failed',
                'last_error': last_error
            }
            
        except Exception as e:
            print(f"✗ Error invoking agent with JWT: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def invoke_agent_with_boto3_jwt(self, prompt: str, jwt_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Try to invoke agent using boto3 with custom JWT headers."""
        try:
            print(f"🚀 Trying boto3 approach with JWT...")
            
            # Create a custom session with JWT token
            # This is a workaround since boto3 doesn't natively support JWT for AgentCore
            
            # We'll use the agentcore client but try to add custom headers
            # This might not work directly, but let's try
            
            payload_data = json.dumps({'prompt': prompt})
            
            # Try using the invoke_agent_runtime method with custom authentication
            # Note: This will likely still fail with the same auth error, but we'll try
            
            try:
                response = self.agentcore_client.invoke_agent_runtime(
                    agentRuntimeArn=self.agent_arn,
                    payload=payload_data
                )
                
                return {
                    'success': True,
                    'response': response,
                    'method': 'boto3_direct'
                }
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                if 'Authorization method mismatch' in error_message:
                    print(f"✗ Expected auth error: {error_message}")
                    return {
                        'success': False,
                        'error': 'JWT authentication required but boto3 uses SigV4',
                        'error_code': error_code,
                        'method': 'boto3_direct'
                    }
                else:
                    raise
                    
        except Exception as e:
            print(f"✗ Boto3 JWT approach failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'method': 'boto3_direct'
            }
    
    def test_runtime_invoke_with_jwt(self, jwt_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Test runtime invoke with JWT authentication."""
        try:
            print("\n🧪 Testing runtime invoke with JWT...")
            
            prompt = "Hello! Can you help me find restaurants?"
            
            # Try JWT-based invocation
            jwt_result = self.invoke_agent_with_jwt(prompt, jwt_tokens)
            
            if jwt_result.get('success'):
                print(f"✓ JWT invocation successful")
                return {
                    'success': True,
                    'response': jwt_result,
                    'test_case': 'jwt_invoke',
                    'method': 'jwt_direct'
                }
            
            # Also try boto3 approach to show the difference
            boto3_result = self.invoke_agent_with_boto3_jwt(prompt, jwt_tokens)
            
            return {
                'success': jwt_result.get('success', False),
                'jwt_result': jwt_result,
                'boto3_result': boto3_result,
                'test_case': 'jwt_invoke',
                'method': 'combined'
            }
            
        except Exception as e:
            print(f"✗ JWT invoke test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'jwt_invoke'
            }
    
    def test_restaurant_search_tools_with_jwt(self, jwt_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Test restaurant search MCP tools with JWT authentication."""
        try:
            print("\n🧪 Testing restaurant search tools with JWT...")
            
            # Test district search
            prompt = "Please search for restaurants in Central district using the search_restaurants_by_district tool with districts parameter set to ['Central district']."
            
            print(f"Testing district search...")
            result = self.invoke_agent_with_jwt(prompt, jwt_tokens)
            
            return {
                'success': result.get('success', False),
                'response': result,
                'test_case': 'restaurant_search_jwt',
                'prompt': prompt
            }
            
        except Exception as e:
            print(f"✗ Restaurant search tools test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'restaurant_search_jwt'
            }
    
    def test_conversational_interaction_with_jwt(self, jwt_tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Test conversational interaction with JWT authentication."""
        try:
            print("\n🧪 Testing conversational interaction with JWT...")
            
            # Test conversational request
            prompt = "I'm visiting Hong Kong and looking for good breakfast places. Can you help me find some restaurants in Central district that serve breakfast?"
            
            print(f"Testing conversational request...")
            result = self.invoke_agent_with_jwt(prompt, jwt_tokens)
            
            return {
                'success': result.get('success', False),
                'response': result,
                'test_case': 'conversational_jwt',
                'prompt': prompt
            }
            
        except Exception as e:
            print(f"✗ Conversational interaction test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_case': 'conversational_jwt'
            }
    
    def check_deployment_status(self) -> Dict[str, Any]:
        """Check deployment status."""
        try:
            print("🔍 Checking deployment status...")
            
            status = self.runtime.status()
            
            # Extract status information
            agent_status = getattr(status, 'agent', {}).get('status', 'UNKNOWN')
            endpoint_status = getattr(status, 'endpoint', {}).get('status', 'UNKNOWN')
            
            print(f"Agent Status: {agent_status}")
            print(f"Endpoint Status: {endpoint_status}")
            
            return {
                'agent_status': agent_status,
                'endpoint_status': endpoint_status,
                'ready': agent_status == 'READY' and endpoint_status == 'READY',
                'status_response': status
            }
            
        except Exception as e:
            print(f"✗ Error checking deployment status: {e}")
            return {
                'ready': False,
                'error': str(e)
            }
    
    def run_comprehensive_final_tests(self) -> Dict[str, Any]:
        """Run comprehensive final test suite with JWT authentication."""
        print("🚀 Starting comprehensive final AgentCore tests with JWT authentication...")
        
        # Check deployment status first
        status_result = self.check_deployment_status()
        if not status_result.get('ready', False):
            print("⚠️ Deployment may not be fully ready, but continuing with tests...")
        
        # Get test user credentials
        test_user = self.cognito_config.get('test_user', {})
        username = test_user.get('username') or test_user.get('email')
        
        if not username:
            return {
                'overall_success': False,
                'error': 'No test user configured',
                'deployment_status': status_result
            }
        
        # Authenticate with Cognito
        try:
            password = os.getenv('COGNITO_TEST_PASSWORD', 'TestPass123!')
            jwt_tokens = self.authenticate_with_cognito(username, password)
            print(f"✓ JWT authentication successful")
        except Exception as e:
            print(f"✗ JWT authentication failed: {e}")
            return {
                'overall_success': False,
                'error': f'Authentication failed: {str(e)}',
                'deployment_status': status_result
            }
        
        # Run tests with JWT authentication
        test_results = []
        
        # Test 1: Simple invoke with JWT
        result1 = self.test_runtime_invoke_with_jwt(jwt_tokens)
        test_results.append(result1)
        
        # Test 2: Restaurant search tools with JWT
        result2 = self.test_restaurant_search_tools_with_jwt(jwt_tokens)
        test_results.append(result2)
        
        # Test 3: Conversational interaction with JWT
        result3 = self.test_conversational_interaction_with_jwt(jwt_tokens)
        test_results.append(result3)
        
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
            'authentication': {
                'method': 'JWT (Cognito)',
                'username': username,
                'success': True,
                'token_length': len(jwt_tokens['access_token'])
            },
            'deployment_status': status_result,
            'tests': test_results,
            'timestamp': time.time(),
            'region': self.region,
            'agent_arn': self.agent_arn,
            'cognito_config': {
                'user_pool_id': self.cognito_config['user_pool']['user_pool_id'],
                'client_id': self.cognito_config['app_client']['client_id']
            }
        }
        
        # Print summary
        print(f"\n📊 Final Test Results Summary:")
        print(f"Overall Success: {overall_success}")
        print(f"Success Rate: {final_results['success_rate']}")
        print(f"Deployment Ready: {status_result.get('ready', False)}")
        print(f"JWT Authentication: ✓ SUCCESS")
        print(f"Test User: {username}")
        
        for i, result in enumerate(test_results, 1):
            test_case = result.get('test_case', f'test_{i}')
            success = result.get('success', False)
            status_icon = "✓" if success else "✗"
            print(f"{status_icon} Test {i} ({test_case}): {'PASSED' if success else 'FAILED'}")
            if not success and 'error' in result:
                print(f"   Error: {result['error']}")
            elif success and 'endpoint_used' in result.get('response', {}):
                print(f"   Endpoint: {result['response']['endpoint_used']}")
        
        # Additional information
        if not overall_success:
            print(f"\n💡 Note: JWT authentication is working correctly.")
            print(f"   The AgentCore Runtime requires proper JWT tokens, not AWS SigV4.")
            print(f"   API endpoint discovery may need adjustment for direct HTTP calls.")
        
        # Save results
        try:
            with open('agentcore_final_jwt_test_results.json', 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            print(f"\n✓ Final test results saved to: agentcore_final_jwt_test_results.json")
        except Exception as e:
            print(f"✗ Failed to save test results: {e}")
        
        return final_results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Final comprehensive AgentCore Runtime test')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--status-only', action='store_true', help='Only check deployment status')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = FinalAgentCoreTester(region=args.region)
        
        if args.status_only:
            # Just check status
            status = tester.check_deployment_status()
            print(f"\nDeployment Status: {json.dumps(status, indent=2, default=str)}")
            return 0 if status.get('ready', False) else 1
        
        else:
            # Run comprehensive tests
            results = tester.run_comprehensive_final_tests()
            return 0 if results['overall_success'] else 1
        
    except Exception as e:
        print(f"Final test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())