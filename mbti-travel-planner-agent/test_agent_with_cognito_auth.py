#!/usr/bin/env python3
"""
Test script for MBTI Travel Planner Agent with Cognito JWT authentication via HTTP.

This script:
1. Authenticates with Cognito using the test user credentials
2. Gets a JWT token
3. Makes HTTP requests to the deployed AgentCore agent with JWT authentication
"""

import json
import base64
import requests
import hmac
import hashlib
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

# Cognito configuration
COGNITO_CONFIG = {
    "region": "us-east-1",
    "user_pool_id": "us-east-1_KePRX24Bn",
    "client_id": "1ofgeckef3po4i3us4j1m4chvd",
    "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
    "test_user": {
        "username": "test@mbti-travel.com",
        "password": "TestPass1234!"
    }
}

# AgentCore configuration
AGENTCORE_CONFIG = {
    "endpoint": "https://bedrock-agentcore-runtime.us-east-1.amazonaws.com",
    "agent_id": "mbti_travel_planner_agent-JPTzWT3IZp",
    "user_id": "test@mbti-travel.com"
}

def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculate SECRET_HASH for Cognito authentication."""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def get_cognito_jwt_token():
    """Authenticate with Cognito and get JWT token via HTTP."""
    print("🔐 Authenticating with Cognito...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=COGNITO_CONFIG['region'])
        
        # Calculate SECRET_HASH
        secret_hash = calculate_secret_hash(
            COGNITO_CONFIG['test_user']['username'],
            COGNITO_CONFIG['client_id'],
            COGNITO_CONFIG['client_secret']
        )
        
        # Authenticate user with SECRET_HASH
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_CONFIG['client_id'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': COGNITO_CONFIG['test_user']['username'],
                'PASSWORD': COGNITO_CONFIG['test_user']['password'],
                'SECRET_HASH': secret_hash
            }
        )
        
        # Extract JWT token
        jwt_token = response['AuthenticationResult']['AccessToken']
        print(f"✅ Successfully authenticated with Cognito")
        print(f"🎫 JWT Token (first 50 chars): {jwt_token[:50]}...")
        
        # Save token for future use
        try:
            with open("fresh_jwt.txt", "w") as f:
                f.write(jwt_token)
            print("💾 JWT token saved to fresh_jwt.txt")
        except Exception as e:
            print(f"⚠️ Could not save JWT token: {e}")
        
        return jwt_token
        
    except Exception as e:
        print(f"❌ Failed to authenticate with Cognito: {e}")
        return None

def invoke_agent_with_jwt(prompt: str, jwt_token: str) -> Optional[str]:
    """Invoke the AgentCore agent with JWT authentication via HTTP."""
    print("🚀 Invoking AgentCore agent with JWT authentication via HTTP...")
    
    try:
        # Generate session ID
        session_id = f"test_session_{uuid.uuid4().hex}_{int(time.time())}"
        
        # Ensure session ID is at least 33 characters
        if len(session_id) < 33:
            session_id = session_id + "_" + "x" * (33 - len(session_id))
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': AGENTCORE_CONFIG['user_id'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Prepare payload
        payload = {
            "prompt": prompt,
            "sessionId": session_id,
            "enableTrace": True
        }
        
        # AgentCore invoke endpoint
        url = f"{AGENTCORE_CONFIG['endpoint']}/invoke-agent-runtime"
        
        print(f"🌐 Making HTTP request to: {url}")
        print(f"📝 Session ID: {session_id}")
        print(f"💬 Prompt: {prompt[:100]}...")
        
        # Make the HTTP request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ HTTP request successful!")
            
            # Handle streaming response
            response_text = ""
            print("📋 Agent Response:")
            print("-" * 60)
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])  # Parse SSE data
                        if "completion" in chunk:
                            text = chunk["completion"]["bytes"].decode("utf-8")
                            response_text += text
                            print(text, end="")
                        elif "trace" in chunk:
                            print(f"\n[TRACE] {chunk['trace']}")
                    except json.JSONDecodeError:
                        continue
            
            print("\n" + "-" * 60)
            return response_text
        else:
            print(f"❌ HTTP request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Agent invocation failed: {e}")
        return None
def save_test_results(jwt_token, prompt, response):
    """Save test results to file."""
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_type": "cognito_jwt_authentication_http",
        "cognito_config": {
            "user_pool_id": COGNITO_CONFIG['user_pool_id'],
            "client_id": COGNITO_CONFIG['client_id'],
            "username": COGNITO_CONFIG['test_user']['username']
        },
        "agentcore_config": {
            "endpoint": AGENTCORE_CONFIG['endpoint'],
            "agent_id": AGENTCORE_CONFIG['agent_id'],
            "user_id": AGENTCORE_CONFIG['user_id']
        },
        "jwt_token_present": jwt_token is not None,
        "jwt_token_length": len(jwt_token) if jwt_token else 0,
        "prompt": prompt,
        "response": response,
        "success": response is not None
    }
    
    # Save to tests/results directory
    results_dir = Path("tests/results")
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"cognito_jwt_http_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Test results saved to: {results_file}")

def main():
    """Main test function."""
    print("🧪 MBTI Travel Planner Agent - Cognito JWT Authentication Test (HTTP)")
    print("=" * 70)
    
    # Step 1: Get JWT token from Cognito
    jwt_token = get_cognito_jwt_token()
    if not jwt_token:
        print("❌ Cannot proceed without JWT token")
        sys.exit(1)
    
    # Step 2: Test prompt
    test_prompt = "Hello! Can you help me find restaurants in Central district for lunch? I have an ENFP personality type and I'm looking for places with good vibes and social atmosphere."
    
    # Step 3: Invoke agent with JWT via HTTP
    response = invoke_agent_with_jwt(test_prompt, jwt_token)
    
    # Step 4: Save results
    save_test_results(jwt_token, test_prompt, response)
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    if response:
        print("🎉 TEST SUCCESSFUL!")
        print("✅ Cognito authentication: SUCCESS")
        print("✅ JWT token obtained: SUCCESS") 
        print("✅ HTTP agent invocation: SUCCESS")
        print("✅ Response received: SUCCESS")
        print(f"📊 Response length: {len(response)} characters")
    else:
        print("❌ TEST FAILED!")
        print("❌ HTTP agent invocation failed")
    
    print("=" * 70)

if __name__ == "__main__":
    main()