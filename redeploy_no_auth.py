#!/usr/bin/env python3
"""
Redeploy Restaurant Search MCP without Authentication
"""

from bedrock_agentcore_starter_toolkit import Runtime
import time
import json


def redeploy_no_auth():
    """Redeploy without authentication."""
    print("🚀 Redeploying Restaurant Search MCP (No Authentication)")
    print("=" * 60)
    
    try:
        # Initialize runtime
        runtime = Runtime()
        
        # Configure without authentication
        print("📋 Configuring AgentCore Runtime...")
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
        
        # Launch deployment
        print("\n🚀 Launching deployment...")
        launch_response = runtime.launch()
        
        print("✓ Launch initiated")
        
        # Monitor status
        print("\n⏳ Monitoring deployment status...")
        start_time = time.time()
        
        while True:
            try:
                status_response = runtime.status()
                
                if hasattr(status_response, 'agent') and status_response.agent:
                    agent_status = status_response.agent.get('status', 'UNKNOWN')
                    print(f"Agent Status: {agent_status}")
                    
                    if agent_status == 'READY':
                        print("🎉 Agent is READY!")
                        break
                    elif agent_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                        print(f"💥 Agent failed with status: {agent_status}")
                        break
                
                # Check timeout (10 minutes)
                elapsed = time.time() - start_time
                if elapsed > 600:
                    print("⏰ Timeout reached (10 minutes)")
                    break
                
                time.sleep(30)
                
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(30)
        
        # Get final status
        final_status = runtime.status()
        print(f"\n📊 Final Status:")
        
        # Print status details
        if hasattr(final_status, 'agent'):
            agent = final_status.agent
            print(f"Agent Status: {agent.get('status', 'UNKNOWN')}")
            print(f"Agent ARN: {agent.get('agentRuntimeArn', 'N/A')}")
            
        if hasattr(final_status, 'endpoint'):
            endpoint = final_status.endpoint
            print(f"Endpoint Status: {endpoint.get('status', 'UNKNOWN')}")
            print(f"Endpoint ARN: {endpoint.get('agentRuntimeEndpointArn', 'N/A')}")
        
        return final_status
        
    except Exception as e:
        print(f"💥 Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = redeploy_no_auth()
    
    if result:
        # Check if deployment was successful
        success = False
        
        if hasattr(result, 'agent') and result.agent.get('status') == 'READY':
            success = True
        if hasattr(result, 'endpoint') and result.endpoint.get('status') == 'READY':
            success = True
            
        if success:
            print("\n✅ Redeployment successful!")
        else:
            print("\n⚠️ Redeployment completed with issues")
    else:
        print("\n❌ Redeployment failed!")