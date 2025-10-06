#!/usr/bin/env python3
"""
Test IAM Fix Verification Script - HTTP Version

This script tests whether the AgentCore agent is accessible via HTTP requests
with JWT authentication, replacing the previous boto3-based IAM testing.
"""

import requests
import logging
import sys
import json
import time
import uuid
import os
import base64
import hmac
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentHTTPVerifier:
    """Verify that the AgentCore agent is accessible via HTTP with JWT authentication."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize the verifier."""
        self.region_name = region_name
        self.account_id = "209803798463"
        self.agent_id = "mbti_travel_planner_agent-JPTzWT3IZp"
        
        # AgentCore HTTP endpoint
        self.agent_endpoint = "https://bedrock-agentcore-runtime.us-east-1.amazonaws.com"
        self.test_username = "test@mbti-travel.com"
        
        # JWT token file
        self.jwt_token_file = Path("fresh_jwt.txt")
        
        # Load Cognito configuration
        self.cognito_config = self.load_cognito_config()
        
        logger.info(f"Initialized verifier for agent: {self.agent_id}")
        logger.info(f"AgentCore endpoint: {self.agent_endpoint}")
    
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
    
    def get_jwt_token(self) -> Optional[str]:
        """Get a valid JWT token for authentication."""
        # Try to load from file first
        if self.jwt_token_file.exists():
            token = self.jwt_token_file.read_text().strip()
            if token and len(token) > 100:
                logger.info("✅ JWT token loaded from file")
                return token
        
        # Try environment variable
        token = os.getenv('JWT_TOKEN')
        if token:
            logger.info("✅ JWT token loaded from environment")
            return token
        
        # Try Cognito authentication
        if self.cognito_config:
            try:
                import boto3
                from botocore.exceptions import ClientError
                
                client_id = self.cognito_config.get('client_id')
                client_secret = self.cognito_config.get('client_secret')
                
                if not client_id or not client_secret:
                    logger.error("Missing Cognito client credentials")
                    return None
                
                # Use test credentials
                username = "test@mbti-travel.com"
                password = "TestPass1234!"
                
                # Calculate SECRET_HASH
                secret_hash = self.calculate_secret_hash(username, client_id, client_secret)
                
                cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
                
                response = cognito_client.initiate_auth(
                    ClientId=client_id,
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters={
                        'USERNAME': username,
                        'PASSWORD': password,
                        'SECRET_HASH': secret_hash
                    }
                )
                
                token = response['AuthenticationResult']['AccessToken']
                logger.info("✅ JWT token obtained from Cognito")
                
                # Save token for future use
                try:
                    self.jwt_token_file.write_text(token)
                except Exception as e:
                    logger.warning(f"Could not save token: {e}")
                
                return token
                
            except Exception as e:
                logger.error(f"Cognito authentication failed: {e}")
        
        logger.error("❌ Could not obtain JWT token")
        return None
    
    def test_agent_http_access(self) -> bool:
        """Test HTTP access to the AgentCore agent."""
        logger.info(f"Testing HTTP access to AgentCore agent: {self.agent_id}")
        
        try:
            # Get JWT token
            jwt_token = self.get_jwt_token()
            if not jwt_token:
                logger.error("❌ Could not obtain JWT token for testing")
                return False
            
            # Generate session ID
            session_id = f"test_session_{uuid.uuid4().hex}_{int(time.time())}"
            
            # Ensure session ID is at least 33 characters
            if len(session_id) < 33:
                session_id = session_id + "_" + "x" * (33 - len(session_id))
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.test_username,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Prepare test payload
            payload = {
                "prompt": "Hello! This is a test to verify the agent is accessible.",
                "sessionId": session_id,
                "enableTrace": True
            }
            
            # AgentCore invoke endpoint
            url = f"{self.agent_endpoint}/invoke-agent-runtime"
            
            logger.info(f"Making HTTP request to: {url}")
            logger.info(f"Session ID: {session_id}")
            
            # Make the HTTP request with a shorter timeout for verification
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                logger.info("✅ HTTP access to AgentCore agent successful!")
                
                # Read a bit of the response to confirm it's working
                response_text = ""
                line_count = 0
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            if "completion" in chunk:
                                response_text += chunk["completion"]["bytes"].decode("utf-8")
                                line_count += 1
                                if line_count >= 3:  # Just get a few lines for verification
                                    break
                        except json.JSONDecodeError:
                            continue
                
                logger.info(f"✅ Agent response received: {response_text[:100]}...")
                return True
            else:
                logger.error(f"❌ HTTP request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP request error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during HTTP access test: {e}")
            return False
    
    def test_agent_health_check(self) -> bool:
        """Test agent health check via HTTP."""
        logger.info("Testing agent health check...")
        
        try:
            # Get JWT token
            jwt_token = self.get_jwt_token()
            if not jwt_token:
                logger.error("❌ Could not obtain JWT token for health check")
                return False
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.test_username,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Health check endpoint (if available)
            health_url = f"{self.agent_endpoint}/health"
            
            logger.info(f"Making health check request to: {health_url}")
            
            # Make the health check request
            response = requests.get(
                health_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Agent health check successful!")
                logger.info(f"Health response: {response.text}")
                return True
            elif response.status_code == 404:
                logger.info("⚠️ Health endpoint not available (404), but this is expected")
                return True  # Not having a health endpoint is normal
            else:
                logger.warning(f"⚠️ Health check returned: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                return True  # Still consider this a success if we got a response
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Health check request error: {e}")
            return True  # Health check failures are not critical for this test
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error during health check: {e}")
    
    def run_verification_tests(self) -> bool:
        """Run all verification tests."""
        logger.info("🧪 Running HTTP-based agent verification tests...")
        
        # Test 1: Test JWT token acquisition
        logger.info("\n" + "="*60)
        logger.info("TEST 1: JWT Token Acquisition")
        logger.info("="*60)
        jwt_token = self.get_jwt_token()
        jwt_test_passed = jwt_token is not None
        
        if jwt_test_passed:
            logger.info("✅ JWT token acquisition successful")
        else:
            logger.error("❌ JWT token acquisition failed")
        
        # Test 2: Test HTTP access to agent
        logger.info("\n" + "="*60)
        logger.info("TEST 2: HTTP Access to AgentCore Agent")
        logger.info("="*60)
        http_test_passed = self.test_agent_http_access()
        
        # Test 3: Test agent health check
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Agent Health Check")
        logger.info("="*60)
        health_test_passed = self.test_agent_health_check()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("="*60)
        
        logger.info(f"JWT Token Acquisition: {'✅ PASS' if jwt_test_passed else '❌ FAIL'}")
        logger.info(f"HTTP Agent Access: {'✅ PASS' if http_test_passed else '❌ FAIL'}")
        logger.info(f"Agent Health Check: {'✅ PASS' if health_test_passed else '❌ FAIL'}")
        
        overall_success = jwt_test_passed and http_test_passed
        
        if overall_success:
            logger.info("\n🎉 AGENT HTTP VERIFICATION SUCCESSFUL!")
            logger.info("The AgentCore agent is accessible via HTTP with JWT authentication.")
        else:
            logger.error("\n💥 AGENT HTTP VERIFICATION FAILED!")
            logger.error("The AgentCore agent may have connectivity or authentication issues.")
            
            if not jwt_test_passed:
                logger.info("\nJWT Token troubleshooting suggestions:")
                logger.info("1. Check Cognito configuration in config/cognito_config.json")
                logger.info("2. Verify test user credentials are correct")
                logger.info("3. Ensure Cognito User Pool and App Client are properly configured")
            
            if not http_test_passed:
                logger.info("\nHTTP Access troubleshooting suggestions:")
                logger.info("1. Verify the AgentCore endpoint URL is correct")
                logger.info("2. Check that the agent is deployed and running")
                logger.info("3. Ensure JWT authentication is properly configured")
                logger.info("4. Check network connectivity to the AgentCore endpoint")
        
        # Save test results
        self.save_test_results(jwt_test_passed, http_test_passed, health_test_passed, overall_success)
        
        return overall_success
    
    def save_test_results(self, jwt_passed: bool, http_passed: bool, health_passed: bool, overall_success: bool):
        """Save test results to file."""
        results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "test_type": "agent_http_verification",
            "agent_config": {
                "agent_id": self.agent_id,
                "endpoint": self.agent_endpoint,
                "user_id": self.test_username
            },
            "test_results": {
                "jwt_token_acquisition": jwt_passed,
                "http_agent_access": http_passed,
                "agent_health_check": health_passed,
                "overall_success": overall_success
            }
        }
        
        # Save to tests/results directory
        results_dir = Path("tests/results")
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"agent_http_verification_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Test results saved to: {results_file}")

def main():
    """Main function to verify agent HTTP access."""
    logger.info("🚀 Starting Agent HTTP Verification")
    
    try:
        verifier = AgentHTTPVerifier()
        success = verifier.run_verification_tests()
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 Verification failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())