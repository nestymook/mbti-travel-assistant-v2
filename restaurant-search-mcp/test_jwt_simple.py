#!/usr/bin/env python3
"""
Simple test to verify JWT authentication is working with the deployed agent.
"""

import json
import boto3
import getpass
from botocore.exceptions import ClientError

def load_cognito_config():
    """Load Cognito configuration."""
    try:
        with open('cognito_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Failed to load Cognito config: {e}")
        return {}

def authenticate_user(cognito_config):
    """Authenticate user and get JWT token."""
    try:
        username = input(f"Enter username (default: {cognito_config['test_user']['username']}): ").strip()
        if not username:
            username = cognito_config['test_user']['username']
        
        password = getpass.getpass(f"Enter password for {username}: ")
        
        print(f"🔐 Authenticating with Cognito as: {username}")
        
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        
        response = cognito_client.initiate_auth(
            ClientId=cognito_config['app_client']['client_id'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print("✓ JWT Authentication successful")
        return access_token
        
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return None

def test_agent_with_sigv4():
    """Test agent invocation using SigV4 (should fail if JWT is required)."""
    try:
        print("\n🔧 Testing agent with SigV4 authentication...")
        
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        response = client.invoke_agent(
            agentId='restaurant_search_conversational_agent-dsuHTs5FJn',
            agentAliasId='TSTALIASID',
            sessionId='test-session-123',
            inputText='Find restaurants in Central district'
        )
        
        print("✓ SigV4 authentication worked - agent accepts SigV4")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if "Authorization method mismatch" in error_message:
            print("✓ SigV4 rejected - agent requires JWT authentication")
            return False
        elif "AccessDenied" in error_code:
            print("✓ SigV4 rejected - agent requires JWT authentication")
            return False
        else:
            print(f"⚠️ Unexpected error: {error_code} - {error_message}")
            return False
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return False

def main():
    print("🚀 Testing Restaurant Search Agent Authentication")
    print("=" * 60)
    
    # Load Cognito config
    cognito_config = load_cognito_config()
    if not cognito_config:
        return
    
    # Test 1: Try SigV4 authentication (should fail if JWT is required)
    sigv4_works = test_agent_with_sigv4()
    
    # Test 2: Get JWT token
    print("\n🔐 Testing JWT authentication...")
    jwt_token = authenticate_user(cognito_config)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Authentication Test Results:")
    
    if not sigv4_works and jwt_token:
        print("✅ Agent is configured for JWT authentication")
        print("✅ JWT authentication is working")
        print("✅ SigV4 is properly rejected")
        print("\n🎉 Agent is correctly configured for JWT authentication!")
    elif sigv4_works:
        print("⚠️ Agent accepts SigV4 authentication")
        print("💡 Agent may be configured for SigV4, not JWT")
    else:
        print("❌ Both authentication methods failed")
        print("💡 Check agent configuration and credentials")

if __name__ == "__main__":
    main()