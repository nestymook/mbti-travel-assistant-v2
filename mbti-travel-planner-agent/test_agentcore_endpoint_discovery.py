#!/usr/bin/env python3
"""
AgentCore Endpoint Discovery Test

This script tries different endpoint formats to find the correct
HTTPS API endpoint for JWT-authenticated AgentCore agents.
"""

import json
import logging
import sys
import time
import uuid
import hmac
import hashlib
import base64
import getpass
import requests
import boto3
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndpointDiscovery:
    """Discover the correct AgentCore HTTPS endpoint."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize endpoint discovery."""
        self.region_name = region_name
        self.agent_arn = 'arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/mbti_travel_planner_agent-JPTzWT3IZp'
        self.agent_id = self.agent_arn.split('/')[-1]
        
        # Load Cognito configuration
        try:
            with open('config/cognito_config.json', 'r') as f:
                self.cognito_config = json.load(f)
            logger.info("✅ Loaded Cognito configuration")
        except Exception as e:
            logger.error(f"❌ Failed to load Cognito config: {e}")
            raise
        
        # Initialize Cognito client
        self.cognito_client = boto3.client('cognito-idp', region_name=region_name)
        
        # Get OAuth2 token
        self.access_token = self.get_oauth2_token()
    
    def get_oauth2_token(self) -> Optional[str]:
        """Get OAuth2 access token from Cognito."""
        try:
            username = "test@mbti-travel.com"
            password = getpass.getpass(f"Enter password for {username}: ")
            
            if not password:
                logger.error("❌ Password cannot be empty")
                return None
            
            logger.info(f"🔐 Authenticating with Cognito as: {username}")
            
            # Calculate SECRET_HASH
            client_id = self.cognito_config['app_client']['client_id']
            client_secret = self.cognito_config['app_client']['client_secret']
            
            message = username + client_id
            dig = hmac.new(
                client_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            secret_hash = base64.b64encode(dig).decode()
            
            # Authenticate with Cognito
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.cognito_config['user_pool']['user_pool_id'],
                ClientId=client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            if 'AuthenticationResult' in response:
                access_token = response['AuthenticationResult']['AccessToken']
                logger.info("✅ Successfully obtained OAuth2 access token")
                return access_token
            else:
                logger.error("❌ No AuthenticationResult in Cognito response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get OAuth2 access token: {e}")
            return None
    
    def test_endpoint(self, endpoint: str, payload: Dict[str, Any], method: str = 'POST') -> Dict[str, Any]:
        """Test a specific endpoint with the given payload."""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': 'test@mbti-travel.com',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"🔍 Testing endpoint: {endpoint}")
            logger.info(f"Method: {method}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            if method.upper() == 'POST':
                response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            elif method.upper() == 'GET':
                response = requests.get(endpoint, headers=headers, params=payload, timeout=30)
            else:
                response = requests.request(method, endpoint, headers=headers, json=payload, timeout=30)
            
            result = {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'success': response.status_code < 400
            }
            
            try:
                result['response'] = response.json()
            except:
                result['response'] = response.text
            
            if result['success']:
                logger.info(f"✅ SUCCESS: {endpoint} returned {response.status_code}")
            else:
                logger.warning(f"❌ FAILED: {endpoint} returned {response.status_code}: {response.text}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ERROR testing {endpoint}: {e}")
            return {
                'endpoint': endpoint,
                'error': str(e),
                'success': False
            }
    
    def discover_endpoints(self) -> List[Dict[str, Any]]:
        """Try different endpoint formats to find the correct one."""
        if not self.access_token:
            logger.error("❌ No access token available")
            return []
        
        logger.info("🔍 Starting endpoint discovery...")
        
        # Generate session ID
        session_id = f"discovery_session_{uuid.uuid4().hex}_{int(time.time())}"
        if len(session_id) < 33:
            session_id = session_id + "_" + "x" * (33 - len(session_id))
        
        # Test different endpoint formats - focusing on the correct runtime endpoint
        base_urls = [
            f"https://bedrock-agentcore-runtime.{self.region_name}.amazonaws.com",
            f"https://bedrock-agentcore.{self.region_name}.amazonaws.com",
            f"https://agentcore.{self.region_name}.amazonaws.com"
        ]
        
        endpoint_patterns = [
            # Pattern 1: Correct AgentCore Runtime endpoint
            "/invoke-agent-runtime",
            
            # Pattern 2: Alternative patterns (for completeness)
            f"/agent-runtime/{self.agent_id}/invoke",
            f"/runtime/{self.agent_id}/invoke",
            f"/agents/{self.agent_id}/invoke",
            f"/v1/agent-runtime/{self.agent_id}/invoke"
        ]
        
        # Test payloads - using the correct format based on your sample
        payloads = [
            # Payload 1: Correct AgentCore Runtime format
            {
                "prompt": "Explain machine learning in simple terms",
                "sessionId": session_id,
                "enableTrace": True
            },
            
            # Payload 2: Alternative format without trace
            {
                "prompt": "Hello test",
                "sessionId": session_id,
                "enableTrace": False
            },
            
            # Payload 3: AWS SDK format (for comparison)
            {
                "agentRuntimeArn": self.agent_arn,
                "runtimeSessionId": session_id,
                "payload": json.dumps({"input": {"prompt": "Hello test"}}),
                "qualifier": "DEFAULT"
            },
            
            # Payload 4: Simple input format
            {
                "input": {"prompt": "Hello test"},
                "sessionId": session_id
            }
        ]
        
        results = []
        
        for base_url in base_urls:
            for pattern in endpoint_patterns:
                endpoint = base_url + pattern
                
                for i, payload in enumerate(payloads):
                    logger.info(f"\n📝 Testing: {endpoint} with payload format {i+1}")
                    result = self.test_endpoint(endpoint, payload)
                    result['payload_format'] = i + 1
                    results.append(result)
                    
                    # If we found a successful endpoint, try a few more payloads
                    if result['success']:
                        logger.info(f"🎉 Found working endpoint: {endpoint}")
                        break
                
                # If we found a working endpoint, no need to test more patterns for this base URL
                if any(r['success'] for r in results[-len(payloads):]):
                    break
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> None:
        """Analyze the endpoint discovery results."""
        logger.info("\n" + "="*60)
        logger.info("📊 ENDPOINT DISCOVERY RESULTS")
        logger.info("="*60)
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        logger.info(f"Total endpoints tested: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        
        if successful:
            logger.info("\n✅ WORKING ENDPOINTS:")
            for result in successful:
                logger.info(f"  - {result['endpoint']} (payload format {result['payload_format']})")
                logger.info(f"    Status: {result['status_code']}")
                logger.info(f"    Response: {str(result['response'])[:100]}...")
        
        if failed:
            logger.info("\n❌ FAILED ENDPOINTS (sample):")
            # Show first 5 failures
            for result in failed[:5]:
                logger.info(f"  - {result['endpoint']}: {result.get('status_code', 'ERROR')}")
        
        logger.info("="*60)

def main():
    """Main discovery function."""
    try:
        logger.info("🚀 Starting AgentCore endpoint discovery...")
        
        discovery = EndpointDiscovery()
        results = discovery.discover_endpoints()
        discovery.analyze_results(results)
        
        # Save results
        results_file = f"endpoint_discovery_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📄 Results saved to: {results_file}")
        
        # Check if we found any working endpoints
        successful = [r for r in results if r['success']]
        if successful:
            logger.info("🎉 Found working endpoint(s)!")
            return 0
        else:
            logger.error("💥 No working endpoints found!")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Discovery failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())