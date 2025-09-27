#!/usr/bin/env python3
"""
Test JWT authorizer configuration for AgentCore deployment.
"""

import json
import os
from deploy_agentcore import AgentCoreDeployment


def test_jwt_authorizer_config():
    """Test JWT authorizer configuration creation."""
    try:
        # Initialize deployment
        deployment = AgentCoreDeployment(region="us-east-1")
        
        # Load Cognito configuration
        cognito_config = deployment.load_cognito_config()
        print("✓ Loaded Cognito configuration:")
        print(f"  - User Pool ID: {cognito_config['user_pool']['user_pool_id']}")
        print(f"  - Client ID: {cognito_config['app_client']['client_id']}")
        print(f"  - Discovery URL: {cognito_config['discovery_url']}")
        
        # Create JWT authorizer config
        auth_config = deployment.create_jwt_authorizer_config(cognito_config)
        print("\n✓ Created JWT authorizer configuration:")
        print(json.dumps(auth_config, indent=2))
        
        # Validate configuration structure
        assert "customJWTAuthorizer" in auth_config
        assert "allowedClients" in auth_config["customJWTAuthorizer"]
        assert "discoveryUrl" in auth_config["customJWTAuthorizer"]
        
        # Validate values
        expected_client_id = cognito_config['app_client']['client_id']
        expected_discovery_url = cognito_config['discovery_url']
        
        assert auth_config["customJWTAuthorizer"]["allowedClients"] == [expected_client_id]
        assert auth_config["customJWTAuthorizer"]["discoveryUrl"] == expected_discovery_url
        
        print("\n✅ JWT authorizer configuration validation passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ JWT authorizer configuration test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_jwt_authorizer_config()
    exit(0 if success else 1)