#!/usr/bin/env python3
"""
Test the remote MCP client authentication functionality.
"""

import asyncio
import json
import sys
import os

# Add the tests directory to the path
sys.path.append('tests')
from test_remote_client import RemoteMCPClient, RemoteCognitoAuthenticator


def test_cognito_authenticator():
    """Test the Cognito authenticator initialization and configuration loading."""
    try:
        print("🔐 Testing Cognito authenticator initialization...")
        
        # Test configuration loading
        authenticator = RemoteCognitoAuthenticator()
        print("✓ Cognito authenticator initialized successfully")
        
        # Test configuration access
        config = authenticator.config
        print(f"✓ Configuration loaded:")
        print(f"  - Region: {config['region']}")
        print(f"  - User Pool ID: {config['user_pool']['user_pool_id']}")
        print(f"  - Client ID: {config['app_client']['client_id']}")
        
        # Test test user credentials
        username, password = authenticator.get_test_user_credentials()
        print(f"✓ Test user credentials:")
        print(f"  - Username: {username}")
        print(f"  - Password: {'*' * len(password)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cognito authenticator test failed: {e}")
        return False


def test_agentcore_runtime_client():
    """Test the AgentCore Runtime client URL construction."""
    try:
        print("\n🌐 Testing AgentCore Runtime client...")
        
        # Import the AgentCore Runtime client
        from test_remote_client import AgentCoreRuntimeClient
        
        # Test with sample ARN
        sample_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/test-agent"
        client = AgentCoreRuntimeClient(sample_arn, "us-east-1")
        
        # Test URL construction
        mcp_url = client.construct_mcp_url()
        print(f"✓ MCP URL constructed: {mcp_url}")
        
        # Test auth headers
        sample_token = "sample.jwt.token"
        headers = client.create_auth_headers(sample_token)
        print(f"✓ Auth headers created:")
        for key, value in headers.items():
            if key.lower() == 'authorization':
                print(f"  - {key}: Bearer ***")
            else:
                print(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ AgentCore Runtime client test failed: {e}")
        return False


async def test_remote_mcp_client_init():
    """Test the remote MCP client initialization."""
    try:
        print("\n🔧 Testing Remote MCP client initialization...")
        
        # Test with sample ARN
        sample_arn = "arn:aws:bedrock-agentcore:us-east-1:123456789012:agent/test-agent"
        client = RemoteMCPClient(sample_arn, "us-east-1")
        
        print("✓ Remote MCP client initialized successfully")
        print(f"✓ Agent ARN: {sample_arn}")
        print(f"✓ Region: us-east-1")
        print(f"✓ Bearer token: {'Set' if client.bearer_token else 'Not set'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Remote MCP client initialization failed: {e}")
        return False


def test_authentication_error_handling():
    """Test authentication error handling."""
    try:
        print("\n⚠️ Testing authentication error handling...")
        
        authenticator = RemoteCognitoAuthenticator()
        
        # Test with invalid credentials (should fail gracefully)
        try:
            result = authenticator.authenticate_user("invalid@example.com", "wrongpassword")
            print("✗ Expected authentication to fail with invalid credentials")
            return False
        except ValueError as e:
            print(f"✓ Authentication correctly failed: {e}")
        except Exception as e:
            print(f"✓ Authentication failed with expected error: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Remote MCP Client Authentication")
    print("=" * 60)
    
    tests = [
        ("Cognito Authenticator", test_cognito_authenticator),
        ("AgentCore Runtime Client", test_agentcore_runtime_client),
        ("Remote MCP Client Init", test_remote_mcp_client_init),
        ("Authentication Error Handling", test_authentication_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)