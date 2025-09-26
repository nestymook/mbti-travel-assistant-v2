#!/usr/bin/env python3
"""
Deploy AgentCore Runtime without JWT Authentication

This script deploys the Restaurant Search MCP server without JWT authentication
to test if the basic deployment works.
"""

import json
import time
from bedrock_agentcore_starter_toolkit import Runtime


def deploy_without_auth():
    """Deploy MCP server without JWT authentication."""
    print("🚀 Deploying Restaurant Search MCP without JWT Authentication")
    print("=" * 60)
    
    try:
        # Initialize AgentCore Runtime
        runtime = Runtime()
        
        # Configure without authentication
        print("📋 Configuring AgentCore Runtime (no auth)...")
        config_response = runtime.configure(
            entrypoint="restaurant_mcp_server.py",
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region="us-east-1",
            protocol="MCP",
            agent_name="restaurant_search_mcp_no_auth"
        )
        
        print("✓ Configuration completed")
        print(f"Response: {config_response}")
        
        # Launch deployment
        print("\n🚀 Launching deployment...")
        launch_response = runtime.launch()
        
        print("✓ Launch initiated")
        print(f"Response: {launch_response}")
        
        # Monitor status
        print("\n⏳ Monitoring deployment status...")
        start_time = time.time()
        
        while True:
            try:
                status_response = runtime.status()
                
                if 'endpoint' in status_response:
                    endpoint_status = status_response['endpoint'].get('status', 'UNKNOWN')
                    print(f"Status: {endpoint_status}")
                    
                    if endpoint_status == 'READY':
                        print("🎉 Deployment is READY!")
                        break
                    elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                        print(f"💥 Deployment failed with status: {endpoint_status}")
                        break
                
                # Check timeout (15 minutes)
                elapsed = time.time() - start_time
                if elapsed > 900:
                    print("⏰ Timeout reached (15 minutes)")
                    break
                
                time.sleep(30)
                
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(30)
        
        # Final status
        final_status = runtime.status()
        print(f"\n📊 Final Status: {json.dumps(final_status, indent=2, default=str)}")
        
        return final_status
        
    except Exception as e:
        print(f"💥 Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = deploy_without_auth()
    if result and hasattr(result, 'endpoint') and result.endpoint.get('status') == 'READY':
        print("\n✅ Deployment successful!")
    elif result and hasattr(result, 'agent') and result.agent.get('status') == 'READY':
        print("\n✅ Deployment successful!")
    else:
        print("\n❌ Deployment failed!")