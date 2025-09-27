#!/usr/bin/env python3
"""
Test AgentCore Runtime with proper JWT authentication.

This script tests the deployed MCP server by first obtaining a JWT token
from Cognito and then using it to authenticate with the AgentCore Runtime.
"""

import json
import os
import sys
import time
import base64
from typing import Dict, Any, Optional

import boto3
import requests
from botocore.exceptions import ClientError


class AuthenticatedAgentCoreTester:
    """Test AgentCore Runtime with JWT authentication."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize authenticated tester.
        
        Args:
            region: AWS region where agent is deployed.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Agent information from deployment
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_mcp-JZdACMALGo"
        self.agent_id = "restaurant_search_mcp-JZdACMALGo"
        
        # Load Cognito configuration
        self.cognito_config = self.load_cognito_config()
        
        # Initialize clients
        self.cognito_client = self.session.client('cognito-idp', region_name=region)
        self.agentcore_client = self.session.client('bedrock-agentcore', region_name=region)
        
        print(f"✓ Clients initialized for region: {region}")
    
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
    
    def authenticate_with_cognito(self, username: str, password: str) -> str:
        """Authenticate with Cognito and get JWT token.
        
        Args:
            username: Cognito username (email).
            password: User password.
            
        Returns:
            JWT access token.
        """
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
            
            print(f"✓ Authentication successful")
            print(f"Access token length: {len(access_token)}")
            
            # Decode and display token info (for debugging)
            try:
                # JWT tokens have 3 parts separated by dots
                header, payload, signature = access_token.split('.')
                
                # Add padding if needed for base64 decoding
                payload += '=' * (4 - len(payload) % 4)
                decoded_payload = base64.b64decode(payload)
                token_data = json.loads(decoded_payload)
                
                print(f"Token client_id: {token_data.get('client_id', 'N/A')}")
                print(f"Token username: {token_data.get('username', 'N/A')}")
                print(f"Token expires: {token_data.get('exp', 'N/A')}")
                
            except Exception as e:
                print(f"⚠️ Could not decode token for debugging: {e}")
            
            return access_token
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"✗ Cognito authentication failed: {error_code} - {error_message}")
            raise
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            raise
    
    def invoke_agent_with_jwt(self, prompt: str, jwt_token: str, session_id: str = None) -> Dict[str, Any]:
        """Invoke the agent with JWT authentication.
        
        Args:
            prompt: The prompt to send to the agent.
            jwt_token: JWT access token from Cognito.
            session_id: Optional session ID for conversation continuity.
            
        Returns:
            Dictionary containing the response and metadata.
        """
        try:
            print(f"🚀 Invoking agent with JWT auth...")
            print(f"Prompt: {prompt[:100]}...")
            
            # Prepare invoke parameters
            invoke_params = {
                'agentRuntimeArn': self.agent_arn,
                'payload': json.dumps({'prompt': prompt})
            }
            
            # Add session ID if provided
            if session_id:
                invoke_params['runtimeSessionId'] = session_id
                print(f"Using session ID: {session_id}")
            
            # Create a new session with custom headers for JWT
            # Note: We need to use the requests library to add custom headers
            # since boto3 doesn't support custom authorization headers easily
            
            # Get the endpoint URL for AgentCore
            endpoint_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com"
            
            # Prepare the request
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Use the AgentCore REST API directly
            api_url = f"{endpoint_url}/runtime/{self.agent_id}/invoke"
            
            payload_data = {
                'prompt': prompt
            }
            
            if session_id:
                payload_data['sessionId'] = session_id
            
            print(f"Making request to: {api_url}")
            
            # Make the request
            response = requests.post(
                api_url,
                headers=headers,
                json=payload_data,
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✓ Agent invocation successful")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response_data': response_data,
                    'headers': dict(response.headers)
                }
            else:
                print(f"✗ Agent invocation failed: {response.status_code}")
                print(f"Response text: {response.text}")
                
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text,
                    'headers': dict(response.headers)
                }
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Request error: {e}")
            return {
                'success': False,
                'error': f"Request error: {str(e)}"
            }
        except Exception as e:
            print(f"✗ Error invoking agent: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_with_authentication(self, username: str, password: str) -> Dict[str, Any]:
        """Test the agent with proper authentication flow."""
        try:
            print("🚀 Starting authenticated agent test...")
            
            # Step 1: Authenticate with Cognito
            jwt_token = self.authenticate_with_cognito(username, password)
            
            # Step 2: Test simple greeting
            print("\n🧪 Testing simple greeting with JWT...")
            greeting_result = self.invoke_agent_with_jwt(
                "Hello! Can you help me find restaurants?", 
                jwt_token
            )
            
            # Step 3: Test restaurant search
            print("\n🧪 Testing restaurant search with JWT...")
            search_result = self.invoke_agent_with_jwt(
                "Please search for restaurants in Central district using the search_restaurants_by_district tool.",
                jwt_token
            )
            
            # Step 4: Test conversational request
            print("\n🧪 Testing conversational request with JWT...")
            conversational_result = self.invoke_agent_with_jwt(
                "I'm looking for good breakfast places in Hong Kong. Can you help me find some in Central district?",
                jwt_token
            )
            
            # Compile results
            test_results = {
                'authentication_successful': True,
                'jwt_token_length': len(jwt_token),
                'tests': {
                    'greeting': greeting_result,
                    'restaurant_search': search_result,
                    'conversational': conversational_result
                }
            }
            
            # Calculate success metrics
            successful_tests = sum(1 for test in test_results['tests'].values() 
                                 if test.get('success', False))
            total_tests = len(test_results['tests'])
            
            test_results['successful_tests'] = successful_tests
            test_results['total_tests'] = total_tests
            test_results['overall_success'] = successful_tests > 0
            
            # Print summary
            print(f"\n📊 Authentication Test Results:")
            print(f"Authentication: ✓ SUCCESS")
            print(f"Successful API calls: {successful_tests}/{total_tests}")
            
            for test_name, result in test_results['tests'].items():
                success = result.get('success', False)
                status_icon = "✓" if success else "✗"
                print(f"{status_icon} {test_name}: {'SUCCESS' if success else 'FAILED'}")
                if not success and 'error' in result:
                    print(f"   Error: {result['error']}")
            
            return test_results
            
        except Exception as e:
            print(f"✗ Authentication test failed: {e}")
            return {
                'authentication_successful': False,
                'error': str(e),
                'overall_success': False
            }
    
    def run_comprehensive_authenticated_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests with authentication."""
        print("🚀 Starting comprehensive authenticated AgentCore tests...")
        
        # Get test user credentials from Cognito config
        test_user = self.cognito_config.get('test_user', {})
        username = test_user.get('username') or test_user.get('email')
        
        if not username:
            print("✗ No test user found in Cognito configuration")
            return {
                'overall_success': False,
                'error': 'No test user configured'
            }
        
        # For security, we'll prompt for password or use environment variable
        password = os.getenv('COGNITO_TEST_PASSWORD')
        if not password:
            print(f"Please provide password for test user: {username}")
            print("You can set COGNITO_TEST_PASSWORD environment variable to avoid prompting")
            try:
                import getpass
                password = getpass.getpass("Password: ")
            except Exception:
                print("✗ Could not get password")
                return {
                    'overall_success': False,
                    'error': 'Password required for authentication'
                }
        
        # Run authenticated tests
        results = self.test_with_authentication(username, password)
        
        # Save results
        try:
            with open('agentcore_authenticated_test_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n✓ Test results saved to: agentcore_authenticated_test_results.json")
        except Exception as e:
            print(f"✗ Failed to save test results: {e}")
        
        return results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AgentCore Runtime with JWT authentication')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--username', help='Cognito username (email)')
    parser.add_argument('--password', help='Cognito password (or set COGNITO_TEST_PASSWORD env var)')
    
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = AuthenticatedAgentCoreTester(region=args.region)
        
        if args.username and args.password:
            # Use provided credentials
            results = tester.test_with_authentication(args.username, args.password)
        else:
            # Use comprehensive test flow
            results = tester.run_comprehensive_authenticated_tests()
        
        return 0 if results.get('overall_success', False) else 1
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())