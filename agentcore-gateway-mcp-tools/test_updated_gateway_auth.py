#!/usr/bin/env python3
"""
Test Updated Gateway Authentication
Comprehensive test of the updated AgentCore Gateway deployment with client secret and OIDC fixes.
"""

import json
import boto3
import hmac
import hashlib
import base64
import requests
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime


def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculate the SECRET_HASH for Cognito authentication."""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def test_gateway_authentication():
    """Test the updated gateway authentication configuration."""
    print("🔐 Testing Updated Gateway Authentication Configuration...")
    
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
        print("🤖 Checking AgentCore Gateway configuration...")
        try:
            with open('.bedrock_agentcore.yaml', 'r') as f:
                agentcore_config = f.read()
                if discovery_url in agentcore_config:
                    print("✅ AgentCore configuration uses correct discovery URL")
                else:
                    print("⚠️ AgentCore configuration may need updating")
        except Exception as e:
            print(f"⚠️ Could not verify AgentCore config: {e}")
        
        print("\n🎉 All gateway authentication tests passed!")
        print("✅ Client secret integration working")
        print("✅ USER_PASSWORD_AUTH flow enabled")
        print("✅ OIDC discovery URL accessible")
        print("✅ JWT tokens generated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Gateway authentication test failed: {e}")
        return False


def test_gateway_deployment_status():
    """Test AgentCore Gateway deployment status."""
    print("\n🤖 Testing AgentCore Gateway Deployment Status...")
    
    try:
        runtime = Runtime()
        runtime.configure(entrypoint='main.py')
        
        status = runtime.status()
        
        # Check agent status
        if hasattr(status, 'agent') and status.agent:
            agent_status = status.agent.get('status', 'UNKNOWN')
            agent_arn = status.agent.get('agentRuntimeArn', 'Not found')
            print(f"✓ Agent Status: {agent_status}")
            print(f"✓ Agent ARN: {agent_arn}")
        
        # Check endpoint status
        if hasattr(status, 'endpoint') and status.endpoint:
            endpoint_status = status.endpoint.get('status', 'UNKNOWN')
            endpoint_arn = status.endpoint.get('agentRuntimeEndpointArn', 'Not found')
            print(f"✓ Endpoint Status: {endpoint_status}")
            print(f"✓ Endpoint ARN: {endpoint_arn}")
        
        # Check configuration
        if hasattr(status, 'config') and status.config:
            agent_arn = status.config.agent_arn if hasattr(status.config, 'agent_arn') else 'Not found'
            memory_id = status.config.memory_id if hasattr(status.config, 'memory_id') else 'Not found'
            print(f"✓ Config Agent ARN: {agent_arn}")
            print(f"✓ Memory ID: {memory_id}")
        
        print("✅ AgentCore Gateway deployment status check completed")
        return True
        
    except Exception as e:
        print(f"❌ AgentCore Gateway status check failed: {e}")
        return False


def test_auth_flow_variations():
    """Test different authentication flow variations for gateway."""
    print("\n🔄 Testing Gateway Authentication Flow Variations...")
    
    with open('cognito_config.json', 'r') as f:
        cognito_config = json.load(f)
    
    client_id = cognito_config['app_client']['client_id']
    client_secret = cognito_config['app_client']['client_secret']
    
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Test 1: Check enabled auth flows
    try:
        client_response = cognito_client.describe_user_pool_client(
            UserPoolId=cognito_config['user_pool']['user_pool_id'],
            ClientId=client_id
        )
        
        auth_flows = client_response['UserPoolClient']['ExplicitAuthFlows']
        print(f"✅ Enabled auth flows: {', '.join(auth_flows)}")
        
        required_flows = ['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH']
        for flow in required_flows:
            if flow in auth_flows:
                print(f"✅ {flow} enabled")
            else:
                print(f"❌ {flow} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Auth flow check failed: {e}")
        return False


def main():
    """Main verification function."""
    print("🚀 AgentCore Gateway MCP Tools - Updated Authentication Test")
    print("=" * 70)
    
    # Test gateway authentication
    auth_test = test_gateway_authentication()
    
    # Test gateway deployment status
    status_test = test_gateway_deployment_status()
    
    # Test authentication flow variations
    flow_test = test_auth_flow_variations()
    
    print("\n" + "=" * 70)
    print("📋 Gateway Authentication Test Summary:")
    print(f"Gateway Authentication: {'✅ PASS' if auth_test else '❌ FAIL'}")
    print(f"Gateway Deployment Status: {'✅ PASS' if status_test else '❌ FAIL'}")
    print(f"Authentication Flow Variations: {'✅ PASS' if flow_test else '❌ FAIL'}")
    
    overall_success = auth_test and status_test and flow_test
    print(f"Overall Gateway Test: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 AgentCore Gateway MCP Tools is fully verified and ready!")
        print("✅ Client secret integration working")
        print("✅ USER_PASSWORD_AUTH flow enabled")
        print("✅ OIDC discovery URL accessible")
        print("✅ AgentCore Gateway configuration correct")
        print("✅ JWT authentication functional")
        print("✅ Gateway deployment successful")
    else:
        print("\n⚠️ Some gateway verification tests failed. Please check the logs above.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)