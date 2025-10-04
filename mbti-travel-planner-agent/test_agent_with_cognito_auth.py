#!/usr/bin/env python3
"""
Test script for MBTI Travel Planner Agent with Cognito JWT authentication.

This script:
1. Authenticates with Cognito using the test user credentials
2. Gets a JWT token
3. Creates a base64 encoded test payload
4. Invokes the deployed AgentCore agent with the JWT token
"""

import json
import base64
import boto3
import subprocess
import sys
from pathlib import Path

# Cognito configuration from the other project
COGNITO_CONFIG = {
    "region": "us-east-1",
    "user_pool_id": "us-east-1_KePRX24Bn",
    "client_id": "1ofgeckef3po4i3us4j1m4chvd",
    "client_secret": "t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
    "test_user": {
        "username": "mbti-test-user@example.com",
        "password": "MBTITest123!"
    }
}

def get_cognito_jwt_token():
    """Authenticate with Cognito and get JWT token."""
    print("🔐 Authenticating with Cognito...")
    
    try:
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=COGNITO_CONFIG['region'])
        
        # Authenticate user
        response = cognito_client.admin_initiate_auth(
            UserPoolId=COGNITO_CONFIG['user_pool_id'],
            ClientId=COGNITO_CONFIG['client_id'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': COGNITO_CONFIG['test_user']['username'],
                'PASSWORD': COGNITO_CONFIG['test_user']['password']
            }
        )
        
        # Extract JWT token
        jwt_token = response['AuthenticationResult']['AccessToken']
        print(f"✅ Successfully authenticated with Cognito")
        print(f"🎫 JWT Token (first 50 chars): {jwt_token[:50]}...")
        
        return jwt_token
        
    except Exception as e:
        print(f"❌ Failed to authenticate with Cognito: {e}")
        return None

def create_test_payload():
    """Create a test payload for the agent."""
    payload = {
        "prompt": "Hello! Can you help me find restaurants in Central district for lunch? I have an ENFP personality type and I'm looking for places with good vibes and social atmosphere."
    }
    
    # Convert to JSON string
    json_str = json.dumps(payload)
    
    # Encode to base64
    b64_encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    print(f"📦 Created test payload: {json_str}")
    print(f"🔢 Base64 encoded payload: {b64_encoded[:50]}...")
    
    return b64_encoded

def invoke_agent_with_jwt(payload_b64, jwt_token):
    """Invoke the AgentCore agent with JWT authentication."""
    print("🚀 Invoking AgentCore agent with JWT authentication...")
    
    try:
        # Use the virtual environment's agentcore command
        venv_agentcore = Path(".venv/Scripts/agentcore.exe")
        if not venv_agentcore.exists():
            venv_agentcore = Path(".venv/bin/agentcore")  # Linux/Mac path
        
        if not venv_agentcore.exists():
            print("❌ AgentCore CLI not found in virtual environment")
            return None
        
        # Invoke agent with JWT bearer token
        cmd = [
            str(venv_agentcore),
            "invoke",
            "--bearer-token", jwt_token,
            payload_b64
        ]
        
        print(f"🔧 Running command: {' '.join(cmd[:3])} --bearer-token [JWT_TOKEN] [PAYLOAD]")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Agent invocation successful!")
            print("📋 Agent Response:")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)
            return result.stdout
        else:
            print(f"❌ Agent invocation failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Agent invocation timed out after 2 minutes")
        return None
    except Exception as e:
        print(f"❌ Error invoking agent: {e}")
        return None

def save_test_results(jwt_token, payload, response):
    """Save test results to file."""
    results = {
        "timestamp": "2025-10-03T19:45:00Z",
        "test_type": "cognito_jwt_authentication",
        "cognito_config": {
            "user_pool_id": COGNITO_CONFIG['user_pool_id'],
            "client_id": COGNITO_CONFIG['client_id'],
            "username": COGNITO_CONFIG['test_user']['username']
        },
        "jwt_token_present": jwt_token is not None,
        "jwt_token_length": len(jwt_token) if jwt_token else 0,
        "payload": payload,
        "response": response,
        "success": response is not None
    }
    
    # Save to tests/results directory
    results_dir = Path("tests/results")
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / "cognito_jwt_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Test results saved to: {results_file}")

def main():
    """Main test function."""
    print("🧪 MBTI Travel Planner Agent - Cognito JWT Authentication Test")
    print("=" * 70)
    
    # Step 1: Get JWT token from Cognito
    jwt_token = get_cognito_jwt_token()
    if not jwt_token:
        print("❌ Cannot proceed without JWT token")
        sys.exit(1)
    
    # Step 2: Create test payload
    payload_b64 = create_test_payload()
    
    # Step 3: Invoke agent with JWT
    response = invoke_agent_with_jwt(payload_b64, jwt_token)
    
    # Step 4: Save results
    save_test_results(jwt_token, payload_b64, response)
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    if response:
        print("🎉 TEST SUCCESSFUL!")
        print("✅ Cognito authentication: SUCCESS")
        print("✅ JWT token obtained: SUCCESS") 
        print("✅ Agent invocation: SUCCESS")
        print("✅ Response received: SUCCESS")
    else:
        print("❌ TEST FAILED!")
        print("❌ Agent invocation failed or timed out")
    
    print("=" * 70)

if __name__ == "__main__":
    main()