#!/usr/bin/env python3
"""
Test Deployed MBTI Travel Planner Agent - Restaurant MCP Functionality

This script tests the deployed AgentCore agent's restaurant search and reasoning
functionality through HTTP requests with JWT authentication.
"""

import requests
import json
import logging
import sys
import time
import uuid
import os
import base64
import hmac
import hashlib
import asyncio
import getpass
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from pathlib import Path
import urllib.parse
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JWTAuthenticator:
    """Handle JWT authentication with Cognito."""
    
    def __init__(self, cognito_config: dict):
        """Initialize JWT authenticator."""
        self.cognito_config = cognito_config
        self.region = cognito_config["region"]
        self.user_pool_id = cognito_config["user_pool"]["user_pool_id"]
        self.client_id = cognito_config["app_client"]["client_id"]
        self.client_secret = cognito_config["app_client"]["client_secret"]
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
        
    def calculate_secret_hash(self, username: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def authenticate_user(self, username: str, password: str) -> str:
        """Authenticate user and return JWT token."""
        try:
            secret_hash = self.calculate_secret_hash(username)
            
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            if 'AuthenticationResult' in response:
                return response['AuthenticationResult']['IdToken']
            else:
                raise Exception("Authentication failed - no token returned")
                
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

class DeployedAgentTester:
    """Test deployed AgentCore agent functionality via HTTP requests."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize the tester."""
        self.region_name = region_name
        
        # AgentCore HTTP endpoint (corrected)
        self.agent_base_url = "https://bedrock-agentcore.us-east-1.amazonaws.com"
        self.agent_id = "mbti_travel_planner_agent-JPTzWT3IZp"
        # URL encode the agent ARN
        self.agent_arn = urllib.parse.quote(f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{self.agent_id}", safe='')

        self.agent_endpoint = f"{self.agent_base_url}/runtimes/{self.agent_arn}/invocations?qualifier=DEFAULT"
        
        # Test user configuration (default user)
        self.default_username = "test@mbti-travel.com"
        
        # JWT token file
        self.jwt_token_file = Path("fresh_jwt.txt")
        
        # Load Cognito configuration
        self.cognito_config = self.load_cognito_config()
        
        # Initialize JWT authenticator
        self.jwt_auth = JWTAuthenticator(self.cognito_config)
        self.jwt_token = None
        
        logger.info(f"Initialized tester for agent: {self.agent_id}")
        logger.info(f"AgentCore endpoint: {self.agent_endpoint}")
        logger.info(f"Agent ID: {self.agent_id}")
    
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            config_file = Path("config/cognito_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("No cognito_config.json found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load Cognito config: {e}")
            return {}
    
    def calculate_secret_hash(self, username: str, client_id: str, client_secret: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        message = username + client_id
        dig = hmac.new(
            client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def authenticate_with_cognito(self, username: str = None, password: str = None) -> Optional[str]:
        """Authenticate with Cognito and get JWT token."""
        try:
            import boto3
            import getpass
            from botocore.exceptions import ClientError
            
            # Use default username if not provided
            if not username:
                username = self.default_username
            
            # Get password if not provided
            if not password:
                password = getpass.getpass(f"Enter password for {username}: ")
            
            logger.info(f"🔐 Authenticating with Cognito as: {username}")
            
            # Get client credentials
            client_id = self.cognito_config['app_client']['client_id']
            client_secret = self.cognito_config['app_client']['client_secret']
            
            # Calculate SECRET_HASH
            secret_hash = self.calculate_secret_hash(username, client_id, client_secret)
            
            cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
            
            # Prepare auth parameters with SECRET_HASH
            auth_parameters = {
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
            
            logger.info("🔑 Initiating authentication with SECRET_HASH...")
            
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_parameters
            )
            
            access_token = response['AuthenticationResult']['AccessToken']
            logger.info("✅ JWT Authentication successful")
            logger.info(f"Token length: {len(access_token)} characters")
            
            return access_token
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Cognito authentication failed: {error_code} - {error_message}")
            
            # Provide helpful error messages
            if error_code == 'NotAuthorizedException':
                logger.error("❌ Invalid username or password")
            elif error_code == 'UserNotFoundException':
                logger.error("❌ User not found")
            elif error_code == 'InvalidParameterException':
                logger.error("❌ Invalid parameters - check client configuration")
            else:
                logger.error(f"❌ Authentication error: {error_code}")
            
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def force_token_refresh(self) -> Optional[str]:
        """Force a fresh JWT token by removing the existing file and re-authenticating."""
        logger.info("🔄 Forcing JWT token refresh...")
        
        # Remove existing token file if it exists
        if self.jwt_token_file.exists():
            try:
                self.jwt_token_file.unlink()
                logger.info("🗑️ Removed existing JWT token file")
            except Exception as e:
                logger.warning(f"Could not remove existing token file: {e}")
        
        # Get fresh token
        return self.get_jwt_token()

    def validate_jwt_token(self, token: str) -> bool:
        """Validate if JWT token is properly formatted and not expired."""
        try:
            if not token or len(token) < 100:
                return False
            
            if not token.startswith('eyJ'):
                return False
            
            # Basic JWT structure validation (header.payload.signature)
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Try to decode the payload to check expiration
            import json
            import base64
            from datetime import datetime
            
            # Add padding if needed for base64 decoding
            payload = parts[1]
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            
            decoded_payload = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded_payload)
            
            # Check if token is expired
            if 'exp' in payload_data:
                exp_timestamp = payload_data['exp']
                current_timestamp = datetime.utcnow().timestamp()
                if current_timestamp >= exp_timestamp:
                    logger.warning("⚠️ JWT token has expired")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"JWT token validation failed: {e}")
            return False

    def get_jwt_token(self) -> Optional[str]:
        """Get a valid JWT token for authentication with per-request handling."""
        logger.info("🔐 Starting JWT token authentication process...")
        
        # Step 1: Try to load from file first (if exists)
        if self.jwt_token_file.exists():
            logger.info("📄 Found existing JWT token file, attempting to use it...")
            token = self.jwt_token_file.read_text().strip()
            
            if self.validate_jwt_token(token):
                logger.info("✅ JWT token from file is valid")
                return token
            else:
                logger.warning("⚠️ JWT token from file is invalid or expired")
        else:
            logger.info("📄 No existing JWT token file found")
        
        # Step 2: If file doesn't exist or token is invalid, authenticate with Cognito
        if not self.cognito_config:
            logger.error("❌ No Cognito configuration available")
            sys.exit(1)
        
        logger.info("🔐 Attempting Cognito authentication...")
        print("\n" + "="*60)
        print("🔐 JWT Authentication Required")
        print("="*60)
        print(f"Default user: {self.default_username}")
        print("Please enter your password to authenticate:")
        print("-"*60)
        
        # Authenticate with default user
        token = self.authenticate_with_cognito(username=self.default_username)
        
        if token:
            # Step 3: Save the new token to file (overwrite)
            try:
                self.jwt_token_file.parent.mkdir(parents=True, exist_ok=True)
                self.jwt_token_file.write_text(token)
                logger.info(f"✅ Fresh JWT token saved to {self.jwt_token_file}")
            except Exception as e:
                logger.warning(f"Could not save token: {e}")
            
            return token
        else:
            # Step 4: If authentication failed, exit the application
            logger.error("❌ Authentication failed. Exiting application.")
            sys.exit(1)
    
    def invoke_agent_with_auth(self, 
                              prompt: str,
                              runtime_session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the deployed AgentCore agent with JWT authentication via HTTP.
        
        Args:
            prompt: Input prompt for the agent
            runtime_session_id: Session ID (must be 33+ characters)
            
        Returns:
            Dictionary containing the agent response
        """
        try:
            # Get JWT token
            jwt_token = self.get_jwt_token()
            if not jwt_token:
                return {
                    'success': False,
                    'error': 'Could not obtain JWT token',
                    'session_id': runtime_session_id
                }
            
            # Generate session ID if not provided
            if not runtime_session_id:
                runtime_session_id = f"test_session_{uuid.uuid4().hex}_{int(time.time())}"
            
            # Ensure session ID is at least 33 characters
            if len(runtime_session_id) < 33:
                runtime_session_id = runtime_session_id + "_" + "x" * (33 - len(runtime_session_id))
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.default_username,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Prepare payload
            payload = {
                "prompt": prompt,
                "sessionId": runtime_session_id,
                "enableTrace": True
            }
            
            # AgentCore invoke endpoint (corrected)
            url = self.agent_endpoint
            
            logger.info(f"Invoking agent via HTTP: {url}")
            logger.info(f"Session ID: {runtime_session_id} (length: {len(runtime_session_id)})")
            logger.info(f"Prompt: {prompt[:100]}...")
            
            # Make the HTTP request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                # Handle streaming response
                response_text = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])  # Parse SSE data
                            if "completion" in chunk:
                                response_text += chunk["completion"]["bytes"].decode("utf-8")
                            elif "trace" in chunk:
                                logger.debug(f"Trace: {chunk['trace']}")
                        except json.JSONDecodeError:
                            continue
                
                logger.info("✅ Agent invocation successful")
                return {
                    'success': True,
                    'response': response_text,
                    'session_id': runtime_session_id,
                    'agent_id': self.agent_id
                }
            else:
                logger.error(f"❌ HTTP request failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'session_id': runtime_session_id,
                    'agent_id': self.agent_id
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP request error: {e}")
            return {
                'success': False,
                'error': f'Request error: {str(e)}',
                'error_type': 'RequestException',
                'session_id': runtime_session_id,
                'agent_id': self.agent_id
            }
        except Exception as e:
            logger.error(f"❌ Agent invocation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'session_id': runtime_session_id,
                'agent_id': self.agent_id
            }
    
    def test_basic_functionality(self) -> bool:
        """Test basic agent functionality."""
        logger.info("🔍 Testing basic agent functionality...")
        
        try:
            result = self.invoke_agent_with_auth(
                prompt="Hello! Can you help me plan a trip to Hong Kong?"
            )
            
            if result['success']:
                logger.info("✅ Basic functionality test passed")
                logger.info(f"Response preview: {str(result['response'])[:200]}...")
                return True
            else:
                logger.error(f"❌ Basic functionality test failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Basic functionality test error: {e}")
            return False
    
    def test_restaurant_search_functionality(self) -> bool:
        """Test restaurant search functionality."""
        logger.info("🔍 Testing restaurant search functionality...")
        
        try:
            result = self.invoke_agent_with_auth(
                prompt="Find restaurants in Central district for lunch. I'm looking for good dim sum places."
            )
            
            if result['success']:
                response_text = str(result['response'])
                
                # Check if response contains restaurant-related content
                restaurant_keywords = ['restaurant', 'dim sum', 'central', 'lunch', 'food', 'dining']
                found_keywords = [kw for kw in restaurant_keywords if kw.lower() in response_text.lower()]
                
                if found_keywords:
                    logger.info("✅ Restaurant search functionality test passed")
                    logger.info(f"Found keywords: {found_keywords}")
                    logger.info(f"Response preview: {response_text[:300]}...")
                    return True
                else:
                    logger.warning("⚠️ Restaurant search response doesn't contain expected keywords")
                    logger.info(f"Response: {response_text[:300]}...")
                    return False
            else:
                logger.error(f"❌ Restaurant search test failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restaurant search test error: {e}")
            return False
    
    def test_mbti_restaurant_reasoning(self) -> bool:
        """Test MBTI-based restaurant reasoning functionality."""
        logger.info("🔍 Testing MBTI restaurant reasoning functionality...")
        
        try:
            result = self.invoke_agent_with_auth(
                prompt="I'm an ENFP personality type. Can you recommend restaurants in Hong Kong that would suit my personality? I love trying new experiences and social dining."
            )
            
            if result['success']:
                response_text = str(result['response'])
                
                # Check if response contains MBTI and restaurant-related content
                mbti_keywords = ['ENFP', 'personality', 'social', 'experience', 'recommend']
                restaurant_keywords = ['restaurant', 'dining', 'hong kong', 'food']
                
                found_mbti = [kw for kw in mbti_keywords if kw.lower() in response_text.lower()]
                found_restaurant = [kw for kw in restaurant_keywords if kw.lower() in response_text.lower()]
                
                if found_mbti and found_restaurant:
                    logger.info("✅ MBTI restaurant reasoning test passed")
                    logger.info(f"Found MBTI keywords: {found_mbti}")
                    logger.info(f"Found restaurant keywords: {found_restaurant}")
                    logger.info(f"Response preview: {response_text[:300]}...")
                    return True
                else:
                    logger.warning("⚠️ MBTI reasoning response doesn't contain expected keywords")
                    logger.info(f"MBTI keywords found: {found_mbti}")
                    logger.info(f"Restaurant keywords found: {found_restaurant}")
                    logger.info(f"Response: {response_text[:300]}...")
                    return False
            else:
                logger.error(f"❌ MBTI reasoning test failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MBTI reasoning test error: {e}")
            return False
    
    def test_mcp_tool_integration(self) -> bool:
        """Test MCP tool integration by asking for specific restaurant data."""
        logger.info("🔍 Testing MCP tool integration...")
        
        try:
            result = self.invoke_agent_with_auth(
                prompt="Use your restaurant search tools to find specific restaurants in Admiralty district. I need detailed information about their operating hours and cuisine types."
            )
            
            if result['success']:
                response_text = str(result['response'])
                
                # Check if response shows tool usage or detailed restaurant data
                tool_keywords = ['search', 'tool', 'found', 'admiralty', 'hours', 'cuisine']
                found_keywords = [kw for kw in tool_keywords if kw.lower() in response_text.lower()]
                
                if found_keywords:
                    logger.info("✅ MCP tool integration test passed")
                    logger.info(f"Found tool-related keywords: {found_keywords}")
                    logger.info(f"Response preview: {response_text[:300]}...")
                    return True
                else:
                    logger.warning("⚠️ MCP tool integration response doesn't show clear tool usage")
                    logger.info(f"Response: {response_text[:300]}...")
                    return False
            else:
                logger.error(f"❌ MCP tool integration test failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MCP tool integration test error: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests."""
        logger.info("🔍 Testing error handling...")
        
        try:
            # Test with empty prompt
            result = self.invoke_agent_with_auth(prompt="")
            
            if result['success']:
                logger.info("✅ Error handling test passed - agent handled empty prompt gracefully")
                return True
            else:
                # Check if it's a graceful error
                error_msg = result.get('error', '').lower()
                if 'validation' in error_msg or 'invalid' in error_msg or 'empty' in error_msg:
                    logger.info("✅ Error handling test passed - appropriate error for empty prompt")
                    return True
                else:
                    logger.warning(f"⚠️ Unexpected error for empty prompt: {result['error']}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error handling test error: {e}")
            return False
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests of the deployed agent."""
        logger.info("🚀 Starting comprehensive tests of deployed MBTI Travel Planner Agent...")
        start_time = time.time()
        
        # Test results
        test_results = {
            'basic_functionality': False,
            'restaurant_search': False,
            'mbti_reasoning': False,
            'mcp_tool_integration': False,
            'error_handling': False,
            'overall_success': False
        }
        
        # Test 1: Basic functionality
        test_results['basic_functionality'] = self.test_basic_functionality()
        
        # Test 2: Restaurant search functionality
        test_results['restaurant_search'] = self.test_restaurant_search_functionality()
        
        # Test 3: MBTI restaurant reasoning
        test_results['mbti_reasoning'] = self.test_mbti_restaurant_reasoning()
        
        # Test 4: MCP tool integration
        test_results['mcp_tool_integration'] = self.test_mcp_tool_integration()
        
        # Test 5: Error handling
        test_results['error_handling'] = self.test_error_handling()
        
        # Calculate overall success
        passed_tests = sum(test_results.values())
        total_tests = len(test_results) - 1  # Exclude 'overall_success'
        test_results['overall_success'] = passed_tests >= (total_tests * 0.8)  # 80% pass rate
        
        duration = time.time() - start_time
        
        # Generate summary
        logger.info("=" * 60)
        logger.info("📊 DEPLOYED AGENT TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Basic Functionality: {'✅ PASS' if test_results['basic_functionality'] else '❌ FAIL'}")
        logger.info(f"Restaurant Search: {'✅ PASS' if test_results['restaurant_search'] else '❌ FAIL'}")
        logger.info(f"MBTI Reasoning: {'✅ PASS' if test_results['mbti_reasoning'] else '❌ FAIL'}")
        logger.info(f"MCP Tool Integration: {'✅ PASS' if test_results['mcp_tool_integration'] else '❌ FAIL'}")
        logger.info(f"Error Handling: {'✅ PASS' if test_results['error_handling'] else '❌ FAIL'}")
        logger.info("-" * 60)
        logger.info(f"Overall Result: {'✅ SUCCESS' if test_results['overall_success'] else '❌ NEEDS ATTENTION'}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Agent ARN: {self.agent_arn}")
        logger.info("=" * 60)
        
        return {
            'test_results': test_results,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'duration': duration,
            'agent_arn': self.agent_arn,
            'timestamp': datetime.utcnow().isoformat()
        }

async def main():
    """Main test function."""
    try:
        # Initialize tester
        tester = DeployedAgentTester()
        
        # Run comprehensive tests
        results = await tester.run_comprehensive_tests()
        
        # Save results to file
        results_file = f"deployed_agent_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Test results saved to: {results_file}")
        
        # Exit with appropriate code
        if results['test_results']['overall_success']:
            logger.info("🎉 Deployed agent tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Some deployed agent tests need attention!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test execution failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())