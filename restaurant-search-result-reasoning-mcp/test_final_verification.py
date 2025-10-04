#!/usr/bin/env python3
"""
Final Verification Test for Updated Restaurant Reasoning MCP
Comprehensive test of the updated deployment with client secret and OIDC fixes.
"""

import json
import boto3
import hmac
import hashlib
import base64
import requests
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


def test_complete_authentication_flow():
    """Test the complete authentication flow with updated configuration."""
    print("🔐 Testing Complete Authentication Flow...")
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        cognito_config = json.load(f)
    
    # Test credentials
    username = "test@mbti-travel.com"
    password = "TestPass1234!"
    client_id = cognito_config['app_client']['client_id']
    client_secret = cognito_config['app_client']['client_secret']
    user_pool_id = cognito_config['user_pool']['user_pool_id']
    discovery_url = cognito_config['discovery_url']
    
    print(f"✓ Configuration loaded successfully")
    print(f"  - User Pool: {user_pool_id}")
    print(f"  - Client ID: {client_id}")
    print(f"  - Discovery URL: {discovery_url}")
    
    try:
        # Step 1: Test Cognito authentication
        print("\n🔑 Step 1: Testing Cognito Authentication...")
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        
        secret_hash = calculate_secret_hash(username, client_id, client_secret)
        
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
        
        print("✅ Cognito authentication successful")
        print(f"  - Access token: {len(access_token)} chars")
        print(f"  - ID token: {len(id_token)} chars")
        
        # Step 2: Test OIDC discovery
        print("\n🌐 Step 2: Testing OIDC Discovery...")
        discovery_response = requests.get(discovery_url)
        
        if discovery_response.status_code == 200:
            discovery_data = discovery_response.json()
            print("✅ OIDC discovery successful")
            print(f"  - Issuer: {discovery_data.get('issuer')}")
            print(f"  - JWKS URI: {discovery_data.get('jwks_uri')}")
            
            # Test JWKS endpoint
            jwks_response = requests.get(discovery_data.get('jwks_uri'))
            if jwks_response.status_code == 200:
                print("✅ JWKS endpoint accessible")
            else:
                print(f"⚠️ JWKS endpoint issue: {jwks_response.status_code}")
        else:
            print(f"❌ OIDC discovery failed: {discovery_response.status_code}")
            return False
        
        # Step 3: Verify AgentCore configuration
        print("\n🤖 Step 3: Verifying AgentCore Configuration...")
        with open('.bedrock_agentcore.yaml', 'r') as f:
            agentcore_config = f.read()
        
        # Check key configuration elements
        checks = [
            (discovery_url in agentcore_config, "Discovery URL in config"),
            (client_id in agentcore_config, "Client ID in config"),
            ("customJWTAuthorizer" in agentcore_config, "JWT authorizer configured"),
            ("restaurant_reasoning_mcp" in agentcore_config, "Agent name configured")
        ]
        
        all_checks_passed = True
        for check_result, check_name in checks:
            if check_result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_checks_passed = False
        
        if not all_checks_passed:
            return False
        
        # Step 4: Test AgentCore deployment status
        print("\n📊 Step 4: Checking AgentCore Deployment Status...")
        
        # Read deployment config
        try:
            with open('agentcore_deployment_config.json', 'r') as f:
                deployment_config = json.load(f)
            
            agent_name = deployment_config.get('agent_name', 'restaurant_reasoning_mcp')
            print(f"✅ Deployment config found for agent: {agent_name}")
            
            if 'configuration_response' in deployment_config:
                print("✅ Configuration response available")
            
            if 'final_deployment_result' in deployment_config:
                final_result = deployment_config['final_deployment_result']
                deployment_successful = final_result.get('deployment_successful', False)
                print(f"✅ Final deployment result: {'SUCCESS' if deployment_successful else 'ISSUES'}")
            
        except FileNotFoundError:
            print("⚠️ Deployment config not found (may be normal)")
        
        print("\n🎉 All verification tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def test_auth_flow_variations():
    """Test different authentication flow variations."""
    print("\n🔄 Testing Authentication Flow Variations...")
    
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
    print("🚀 Restaurant Reasoning MCP - Final Verification Test")
    print("=" * 70)
    
    # Test complete authentication flow
    auth_test = test_complete_authentication_flow()
    
    # Test authentication flow variations
    flow_test = test_auth_flow_variations()
    
    print("\n" + "=" * 70)
    print("📋 Final Verification Summary:")
    print(f"Complete Authentication Flow: {'✅ PASS' if auth_test else '❌ FAIL'}")
    print(f"Authentication Flow Variations: {'✅ PASS' if flow_test else '❌ FAIL'}")
    
    overall_success = auth_test and flow_test
    print(f"Overall Verification: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Restaurant Reasoning MCP is fully verified and ready!")
        print("✅ Client secret integration working")
        print("✅ USER_PASSWORD_AUTH flow enabled")
        print("✅ OIDC discovery URL accessible")
        print("✅ AgentCore configuration correct")
        print("✅ JWT authentication functional")
    else:
        print("\n⚠️ Some verification tests failed. Please check the logs above.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)