#!/usr/bin/env python3
"""
Check Specific AgentCore Runtime Deployment Status

This script checks the status of a specific deployed agent.
"""

import boto3
import json
from botocore.exceptions import ClientError


def check_agentcore_deployment_status():
    """Check the status of the deployed AgentCore agent."""
    print("🔍 Checking Specific AgentCore Deployment Status")
    print("=" * 50)
    
    # Agent information from .bedrock_agentcore.yaml
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_mcp_no_auth-QkpwVXBnQD"
    agent_id = "restaurant_search_mcp_no_auth-QkpwVXBnQD"
    region = "us-east-1"
    
    try:
        # Initialize Bedrock AgentCore client
        client = boto3.client('bedrock-agentcore', region_name=region)
        
        print(f"📋 Checking agent: {agent_id}")
        print(f"🏷️ Agent ARN: {agent_arn}")
        
        # Get agent runtime status
        response = client.get_agent_runtime(agentRuntimeId=agent_id)
        
        print("✓ Agent runtime found!")
        print(f"\n📊 Agent Status:")
        print(json.dumps(response, indent=2, default=str))
        
        # Parse status
        status = response.get('status', 'UNKNOWN')
        print(f"\n🎯 Current Status: {status}")
        
        if status == 'READY':
            print("✅ Agent is READY and operational!")
            
            # Show endpoint information
            if 'endpoint' in response:
                endpoint = response['endpoint']
                print(f"🔗 Endpoint URL: {endpoint.get('url', 'N/A')}")
            
            # Show configuration
            if 'protocolConfiguration' in response:
                protocol = response['protocolConfiguration']
                print(f"🔧 Protocol: {protocol.get('serverProtocol', 'N/A')}")
            
        elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            print("❌ Agent deployment FAILED")
            if 'failureReasons' in response:
                print(f"💥 Failure reasons: {response['failureReasons']}")
                
        elif status in ['CREATING', 'UPDATING']:
            print("⏳ Agent deployment is IN PROGRESS")
            
        else:
            print(f"⚠️ Unknown status: {status}")
        
        return response
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print("❌ Agent not found - may have been deleted or never deployed")
        elif error_code == 'AccessDeniedException':
            print("🔒 Access denied - check IAM permissions for bedrock-agentcore:GetAgentRuntime")
        else:
            print(f"💥 AWS Error: {e}")
        return None
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return None


def test_mcp_endpoint():
    """Test the MCP endpoint if available."""
    print("\n🧪 Testing MCP Endpoint Connectivity")
    print("=" * 40)
    
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_mcp_no_auth-QkpwVXBnQD"
    region = "us-east-1"
    
    # Construct MCP URL
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations"
    
    print(f"🔗 MCP URL: {mcp_url}")
    
    try:
        import requests
        
        # Simple connectivity test (without authentication for now)
        print("📡 Testing basic connectivity...")
        
        # This will likely fail without auth, but will tell us if the endpoint exists
        response = requests.get(mcp_url, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Endpoint is reachable (authentication required)")
        elif response.status_code == 200:
            print("✅ Endpoint is reachable and responding")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
    except ImportError:
        print("⚠️ requests library not available for connectivity test")


if __name__ == "__main__":
    result = check_agentcore_deployment_status()
    
    if result:
        status = result.get('status', 'UNKNOWN')
        if status == 'READY':
            print("\n🎉 SUCCESS: Your MCP server is deployed and ready!")
            test_mcp_endpoint()
        elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            print("\n💥 FAILED: Deployment encountered errors")
        elif status in ['CREATING', 'UPDATING']:
            print("\n⏳ IN PROGRESS: Deployment is still running")
        else:
            print(f"\n❓ UNKNOWN: Status is {status}")
    else:
        print("\n❌ DEPLOYMENT CHECK FAILED")