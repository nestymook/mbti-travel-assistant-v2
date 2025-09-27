#!/usr/bin/env python3
"""
Deploy Restaurant Search Conversational Agent with BedrockAgentCoreApp EntryPoint

This script deploys the complete conversational agent that uses BedrockAgentCoreApp
entrypoint with Strands Agent integration for natural language restaurant search.
"""

import json
import os
import sys
import time
from typing import Dict, Any

import boto3
from bedrock_agentcore_starter_toolkit import Runtime


def deploy_conversational_agent():
    """Deploy the conversational agent with entrypoint integration."""
    
    print("🚀 Deploying Restaurant Search Conversational Agent")
    print("=" * 60)
    
    # Initialize AgentCore Runtime
    agentcore_runtime = Runtime()
    
    try:
        # Load Cognito configuration
        print("📋 Loading Cognito configuration...")
        
        if not os.path.exists("cognito_config.json"):
            print("✗ Cognito configuration not found. Please run setup_cognito.py first.")
            return False
        
        with open("cognito_config.json", 'r') as f:
            cognito_config = json.load(f)
        
        client_id = cognito_config['app_client']['client_id']
        discovery_url = cognito_config['discovery_url']
        
        print(f"✓ Client ID: {client_id}")
        print(f"✓ Discovery URL: {discovery_url}")
        
        # Create authentication configuration
        auth_config = {
            "customJWTAuthorizer": {
                "allowedClients": [client_id],
                "discoveryUrl": discovery_url,
            }
        }
        
        # Validate entrypoint file
        entrypoint = "main.py"
        if not os.path.exists(entrypoint):
            print(f"✗ Entrypoint file not found: {entrypoint}")
            return False
        
        print(f"✓ Entrypoint file: {entrypoint}")
        
        # Validate requirements file
        requirements_file = "requirements.txt"
        if not os.path.exists(requirements_file):
            print(f"✗ Requirements file not found: {requirements_file}")
            return False
        
        print(f"✓ Requirements file: {requirements_file}")
        
        # Configure AgentCore Runtime for entrypoint
        print("\n🔧 Configuring AgentCore Runtime...")
        
        config_response = agentcore_runtime.configure(
            entrypoint=entrypoint,
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file=requirements_file,
            region="us-east-1",
            authorizer_configuration=auth_config,
            protocol="ENTRYPOINT",  # Use ENTRYPOINT protocol instead of MCP
            agent_name="restaurant_search_conversational_agent"
        )
        
        print("✓ AgentCore Runtime configured successfully")
        print(f"Configuration: {config_response}")
        
        # Launch deployment
        print("\n🚀 Launching deployment...")
        
        launch_response = agentcore_runtime.launch()
        print("✓ Deployment launched successfully")
        print(f"Launch response: {launch_response}")
        
        # Monitor deployment status
        print("\n⏳ Monitoring deployment status...")
        
        timeout_minutes = 15
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while True:
            try:
                status_response = agentcore_runtime.status()
                
                if 'endpoint' in status_response:
                    endpoint_status = status_response['endpoint'].get('status', 'UNKNOWN')
                    print(f"Status: {endpoint_status}")
                    
                    if endpoint_status == 'READY':
                        print("🎉 Deployment is READY!")
                        
                        # Save deployment information
                        deployment_info = {
                            'agent_name': 'restaurant_search_conversational_agent',
                            'entrypoint': entrypoint,
                            'protocol': 'ENTRYPOINT',
                            'auth_config': auth_config,
                            'cognito_config': cognito_config,
                            'status': status_response,
                            'deployed_at': time.time()
                        }
                        
                        with open('conversational_agent_deployment.json', 'w') as f:
                            json.dump(deployment_info, f, indent=2, default=str)
                        
                        print("✓ Deployment information saved to conversational_agent_deployment.json")
                        
                        # Print usage information
                        print("\n📋 Deployment Summary:")
                        print("=" * 40)
                        print(f"Agent Name: restaurant_search_conversational_agent")
                        print(f"Protocol: ENTRYPOINT (BedrockAgentCoreApp)")
                        print(f"Authentication: JWT (Cognito)")
                        print(f"Status: {endpoint_status}")
                        
                        if 'url' in status_response.get('endpoint', {}):
                            endpoint_url = status_response['endpoint']['url']
                            print(f"Endpoint URL: {endpoint_url}")
                        
                        print("\n🎯 Usage:")
                        print("The conversational agent accepts natural language queries like:")
                        print("- 'Find restaurants in Central district'")
                        print("- 'Show me breakfast places in Tsim Sha Tsui'")
                        print("- 'What dinner restaurants are in Causeway Bay?'")
                        
                        print("\n🔐 Authentication:")
                        print("All requests require JWT authentication via Cognito.")
                        print("Use the test client scripts to interact with the agent.")
                        
                        return True
                        
                    elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                        print(f"💥 Deployment failed with status: {endpoint_status}")
                        print(f"Status details: {status_response}")
                        return False
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
                    print(f"Current status: {status_response}")
                    return False
                
                # Wait before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(30)
        
    except Exception as e:
        print(f"💥 Deployment failed: {e}")
        return False


def test_conversational_agent():
    """Test the deployed conversational agent."""
    
    print("\n🧪 Testing Conversational Agent...")
    
    try:
        # Load deployment info
        if not os.path.exists('conversational_agent_deployment.json'):
            print("✗ Deployment info not found. Deploy the agent first.")
            return False
        
        with open('conversational_agent_deployment.json', 'r') as f:
            deployment_info = json.load(f)
        
        # Check if agent is ready
        agentcore_runtime = Runtime()
        status_response = agentcore_runtime.status()
        
        endpoint_status = status_response.get('endpoint', {}).get('status', 'UNKNOWN')
        
        if endpoint_status != 'READY':
            print(f"✗ Agent not ready. Status: {endpoint_status}")
            return False
        
        print("✓ Agent is ready for testing")
        print("✓ Use test_agentcore_with_auth.py to test the conversational agent")
        
        return True
        
    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Restaurant Search Conversational Agent')
    parser.add_argument('--test-only', action='store_true', 
                       help='Only test existing deployment')
    
    args = parser.parse_args()
    
    if args.test_only:
        success = test_conversational_agent()
    else:
        success = deploy_conversational_agent()
        if success:
            test_conversational_agent()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())