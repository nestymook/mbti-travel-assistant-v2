#!/usr/bin/env python3
"""
Check AgentCore Runtime Deployment Status

This script checks the current status of the Restaurant Search MCP deployment.
"""

import json
from bedrock_agentcore_starter_toolkit import Runtime


def check_deployment_status():
    """Check the current deployment status."""
    print("🔍 Checking Restaurant Search MCP Deployment Status")
    print("=" * 50)
    
    try:
        # Initialize Runtime
        runtime = Runtime()
        
        # Try to get status
        print("📊 Retrieving deployment status...")
        status_response = runtime.status()
        
        print("✓ Status retrieved successfully")
        print(f"\n📋 Current Status:")
        print(json.dumps(status_response, indent=2, default=str))
        
        # Parse status
        if 'endpoint' in status_response:
            endpoint = status_response['endpoint']
            status = endpoint.get('status', 'UNKNOWN')
            
            print(f"\n🎯 Deployment Status: {status}")
            
            if status == 'READY':
                print("✅ Deployment is READY and operational!")
                if 'url' in endpoint:
                    print(f"🔗 Endpoint URL: {endpoint['url']}")
                if 'arn' in endpoint:
                    print(f"🏷️ Agent ARN: {endpoint['arn']}")
            elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                print("❌ Deployment has FAILED")
            elif status in ['CREATING', 'UPDATING']:
                print("⏳ Deployment is IN PROGRESS")
            else:
                print(f"⚠️ Unknown status: {status}")
        else:
            print("❓ No endpoint information available")
        
        return status_response
        
    except Exception as e:
        print(f"💥 Error checking status: {e}")
        print("\nThis might mean:")
        print("- No deployment has been configured yet")
        print("- The deployment was not successful")
        print("- AgentCore Runtime is not available in this region")
        return None


if __name__ == "__main__":
    result = check_deployment_status()
    
    if result:
        endpoint_status = result.get('endpoint', {}).get('status', 'UNKNOWN')
        if endpoint_status == 'READY':
            print("\n🎉 SUCCESS: Your MCP server is deployed and ready!")
        elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            print("\n💥 FAILED: Deployment encountered errors")
        elif endpoint_status in ['CREATING', 'UPDATING']:
            print("\n⏳ IN PROGRESS: Deployment is still running")
        else:
            print(f"\n❓ UNKNOWN: Status is {endpoint_status}")
    else:
        print("\n❌ NO DEPLOYMENT: No active deployment found")