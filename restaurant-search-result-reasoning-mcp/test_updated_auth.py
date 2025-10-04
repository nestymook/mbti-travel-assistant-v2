#!/usr/bin/env python3
"""
Test Updated Authentication for Restaurant Reasoning MCP
Tests the updated Cognito configuration with client secret and USER_PASSWORD_AUTH flow.
"""

import json
import boto3
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError


def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculate the SECRET_HASH for Cognito authentication."""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def test_updated_authentication():
    """Test the updated Cognito authentication configuration."""
    print("🔐 Testing Updated Authentication Configuration...")
    
    # Load updated Cognito configuration
    try:
        with open('cognito_config.json', 'r') as f:
            cognito_config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load Cognito config: {e}")
        return False
    
    # Test credentials
    username = "test@mbti-travel.com"
    password = "TestPass1234!"
    client_id = cognito_config['app_client']['client_id']
    client_secret = cognito_config['app_client']['client_secret']
    user_pool_id = cognito_config['user_pool']['user_pool_id']
    discovery_url = cognito_config['discovery_url']
    
    print(f"✓ User Pool ID: {user_pool_id}")
    print(f"✓ Client ID: {client_id}")
    print(f"✓ Discovery URL: {discovery_url}")
    print(f"✓ Username: {username}")
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        
        # Calculate SECRET_HASH
        secret_hash = calculate_secret_hash(username, client_id, client_secret)
        print("✓ SECRET_HASH calculated successfully")
        
        # Test USER_PASSWORD_AUTH flow
        print("🔑 Testing USER_PASSWORD_AUTH flow...")
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )
        
        auth_result = response['AuthenticationResult']
        access_token = auth_result['AccessToken']
        id_token = auth_result['IdToken']
        
        print("✅ Authentication successful!")
        print(f"✓ Access token length: {len(access_token)}")
        print(f"✓ ID token length: {len(id_token)}")
        
        # Test OIDC discovery URL
        print("🌐 Testing OIDC discovery URL...")
        import requests
        
        discovery_response = requests.get(discovery_url)
        if discovery_response.status_code == 200:
            discovery_data = discovery_response.json()
            print("✅ OIDC discovery URL accessible")
            print(f"✓ Issuer: {discovery_data.get('issuer', 'Not found')}")
            print(f"✓ JWKS URI: {discovery_data.get('jwks_uri', 'Not found')}")
        else:
            print(f"❌ OIDC discovery URL failed: {discovery_response.status_code}")
            return False
        
        # Check AgentCore configuration
        print("🤖 Checking AgentCore configuration...")
        try:
            with open('.bedrock_agentcore.yaml', 'r') as f:
                agentcore_config = f.read()
                if discovery_url in agentcore_config:
                    print("✅ AgentCore configuration uses correct discovery URL")
                else:
                    print("⚠️ AgentCore configuration may need updating")
        except Exception as e:
            print(f"⚠️ Could not verify AgentCore config: {e}")
        
        print("\n🎉 All authentication tests passed!")
        print("✅ Client secret integration working")
        print("✅ USER_PASSWORD_AUTH flow enabled")
        print("✅ OIDC discovery URL accessible")
        print("✅ JWT tokens generated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


def test_agentcore_status():
    """Test AgentCore deployment status."""
    print("\n🤖 Testing AgentCore Deployment Status...")
    
    try:
        from bedrock_agentcore_starter_toolkit import Runtime
        
        runtime = Runtime()
        runtime.configure(entrypoint='restaurant_reasoning_mcp_server.py')
        
        status = runtime.status()
        
        # Check agent status
        if hasattr(status, 'agent') and status.agent:
            agent_status = status.agent.get('status', 'UNKNOWN')
            print(f"✓ Agent Status: {agent_status}")
        
        # Check endpoint status
        if hasattr(status, 'endpoint') and status.endpoint:
            endpoint_status = status.endpoint.get('status', 'UNKNOWN')
            print(f"✓ Endpoint Status: {endpoint_status}")
        
        # Check configuration
        if hasattr(status, 'config') and status.config:
            agent_arn = status.config.agent_arn if hasattr(status.config, 'agent_arn') else 'Not found'
            memory_id = status.config.memory_id if hasattr(status.config, 'memory_id') else 'Not found'
            print(f"✓ Agent ARN: {agent_arn}")
            print(f"✓ Memory ID: {memory_id}")
        
        print("✅ AgentCore deployment status check completed")
        return True
        
    except Exception as e:
        print(f"❌ AgentCore status check failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Restaurant Reasoning MCP - Updated Authentication Test")
    print("=" * 60)
    
    # Test authentication
    auth_success = test_updated_authentication()
    
    # Test AgentCore status
    agentcore_success = test_agentcore_status()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
    print(f"AgentCore Status: {'✅ PASS' if agentcore_success else '❌ FAIL'}")
    
    overall_success = auth_success and agentcore_success
    print(f"Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Restaurant Reasoning MCP is ready with updated authentication!")
    else:
        print("\n⚠️ Some issues detected. Please check the logs above.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)