#!/usr/bin/env python3
"""
Update Gateway Deployment with Auto-Update Flag
"""

import json
from bedrock_agentcore_starter_toolkit import Runtime

def update_gateway_deployment():
    """Update the existing gateway deployment with new settings."""
    print("🔄 Updating AgentCore Gateway deployment...")
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    runtime = Runtime()
    
    # Configure with updated settings
    auth_config = {
        'customJWTAuthorizer': {
            'allowedClients': [config['app_client']['client_id']],
            'discoveryUrl': config['discovery_url']
        }
    }
    
    print("✓ Configuring with updated Cognito settings...")
    print(f"  - Client ID: {config['app_client']['client_id']}")
    print(f"  - Discovery URL: {config['discovery_url']}")
    
    runtime.configure(
        entrypoint='main.py',
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file='requirements.txt',
        region='us-east-1',
        authorizer_configuration=auth_config,
        protocol='HTTP',
        agent_name='agentcore_gateway_mcp_tools'
    )
    
    # Launch with auto-update
    print("🚀 Launching with auto-update flag...")
    result = runtime.launch(auto_update_on_conflict=True)
    print("✅ Launch completed successfully")
    
    # Check status
    print("📊 Checking deployment status...")
    status = runtime.status()
    
    if hasattr(status, 'agent') and status.agent:
        agent_status = status.agent.get('status', 'UNKNOWN')
        print(f"✓ Agent Status: {agent_status}")
    
    if hasattr(status, 'endpoint') and status.endpoint:
        endpoint_status = status.endpoint.get('status', 'UNKNOWN')
        print(f"✓ Endpoint Status: {endpoint_status}")
    
    print("🎉 Gateway deployment update completed!")
    return result

if __name__ == "__main__":
    update_gateway_deployment()