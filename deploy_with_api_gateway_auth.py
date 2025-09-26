#!/usr/bin/env python3
"""
Deploy with API Gateway Lambda Authorizer instead of Cognito JWT
"""

from bedrock_agentcore_starter_toolkit import Runtime


def deploy_with_lambda_auth():
    """Deploy using Lambda authorizer instead of Cognito JWT."""
    print("🔐 Deploying with Lambda Authorizer (Alternative to Cognito JWT)")
    print("=" * 65)
    
    try:
        runtime = Runtime()
        
        # Configure with Lambda authorizer
        auth_config = {
            "customLambdaAuthorizer": {
                "lambdaArn": "arn:aws:lambda:us-east-1:209803798463:function:restaurant-mcp-auth",
                "authorizerResultTtlInSeconds": 300
            }
        }
        
        print("📋 Configuring with Lambda Authorizer...")
        config_response = runtime.configure(
            entrypoint="restaurant_mcp_server.py",
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region="us-east-1",
            authorizer_configuration=auth_config,
            protocol="MCP",
            agent_name="restaurant_search_mcp_lambda_auth"
        )
        
        print("✓ Configuration completed with Lambda authorizer")
        return config_response
        
    except Exception as e:
        print(f"❌ Lambda authorizer configuration failed: {e}")
        print("💡 This requires creating a Lambda authorizer function first")
        return None


if __name__ == "__main__":
    print("⚠️ This is an alternative approach requiring Lambda function setup")
    print("For now, recommend using no-auth deployment or fixing Cognito domain")