#!/usr/bin/env python3
"""
Test Authentication Utilities

This module provides utilities for JWT authentication and HTTPS requests
to the MBTI Travel Planner Agent deployed on AgentCore.
"""

import json
import time
import hmac
import hashlib
import base64
import requests
import boto3
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AgentCoreTestClient:
    """Client for testing AgentCore deployed agents with JWT authentication."""
    
    def __init__(self, config_path: str = "config/cognito_config.json"):
        """Initialize the test client with Cognito configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.region = self.config['region']
        self.user_pool_id = self.config['user_pool']['user_pool_id']
        self.client_id = self.config['app_client']['client_id']
        self.client_secret = self.config['app_client']['client_secret']
        self.test_username = self.config['test_user']['username']
        self.test_password = "TestPass1234!"  # Known test password
        
        # AgentCore endpoint - this should be the deployed agent URL
        self.agent_endpoint = "https://bedrock-agentcore-runtime.us-east-1.amazonaws.com"
        self.agent_id = "mbti_travel_planner_agent-JPTzWT3IZp"
        
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
        self._jwt_token = None
        self._token_expiry = None
    
    def _calculate_secret_hash(self, username: str) -> str:
        """Calculate the SECRET_HASH required for Cognito authentication."""
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def _get_jwt_token(self) -> str:
        """Get a valid JWT token from Cognito."""
        # Check if we have a valid cached token
        if self._jwt_token and self._token_expiry and time.time() < self._token_expiry:
            return self._jwt_token
        
        try:
            secret_hash = self._calculate_secret_hash(self.test_username)
            
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': self.test_username,
                    'PASSWORD': self.test_password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            auth_result = response['AuthenticationResult']
            self._jwt_token = auth_result['IdToken']
            
            # Set expiry time (tokens typically last 1 hour, we'll refresh after 50 minutes)
            self._token_expiry = time.time() + (50 * 60)
            
            logger.info("Successfully obtained JWT token")
            return self._jwt_token
            
        except Exception as e:
            logger.error(f"Failed to get JWT token: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for AgentCore requests."""
        jwt_token = self._get_jwt_token()
        return {
            'Authorization': f'Bearer {jwt_token}',
            'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.test_username,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def invoke_agent(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Invoke the agent with a prompt via HTTPS."""
        if not session_id:
            session_id = f"test-session-{int(time.time())}"
        
        url = f"{self.agent_endpoint}/invoke-agent-runtime"
        headers = self._get_headers()
        
        payload = {
            "prompt": prompt,
            "sessionId": session_id,
            "enableTrace": True
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent invocation failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status via HTTPS."""
        url = f"{self.agent_endpoint}/agent-status"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent status check failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check via HTTPS."""
        url = f"{self.agent_endpoint}/health"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def search_restaurants(self, query: str, district: Optional[str] = None) -> Dict[str, Any]:
        """Search for restaurants via the agent."""
        prompt = f"Find restaurants"
        if district:
            prompt += f" in {district}"
        if query:
            prompt += f" that match: {query}"
        
        return self.invoke_agent(prompt)
    
    def get_restaurant_recommendations(self, personality_type: str, preferences: Optional[str] = None) -> Dict[str, Any]:
        """Get restaurant recommendations based on MBTI personality type."""
        prompt = f"Recommend restaurants for {personality_type} personality type"
        if preferences:
            prompt += f" with preferences: {preferences}"
        
        return self.invoke_agent(prompt)


def create_test_client() -> AgentCoreTestClient:
    """Create a test client instance."""
    return AgentCoreTestClient()


def test_jwt_authentication() -> bool:
    """Test JWT authentication functionality."""
    try:
        client = create_test_client()
        token = client._get_jwt_token()
        return token is not None and len(token) > 0
    except Exception as e:
        logger.error(f"JWT authentication test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the authentication
    logging.basicConfig(level=logging.INFO)
    
    print("Testing JWT authentication...")
    if test_jwt_authentication():
        print("✅ JWT authentication test passed")
    else:
        print("❌ JWT authentication test failed")
    
    # Test agent invocation
    try:
        client = create_test_client()
        result = client.invoke_agent("Hello, can you help me find restaurants?")
        print("✅ Agent invocation test passed")
        print(f"Response: {result}")
    except Exception as e:
        print(f"❌ Agent invocation test failed: {e}")