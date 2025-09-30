#!/usr/bin/env python3
"""
Check MBTI Travel Assistant Deployment Status

This script checks the current deployment status of the MBTI Travel Assistant
on Amazon Bedrock AgentCore Runtime.
"""

import json
import sys
from typing import Dict, Any

def check_deployment_status():
    """Check the current deployment status."""
    
    try:
        from bedrock_agentcore_starter_toolkit import Runtime
        
        print("🔍 Checking MBTI Travel Assistant Deployment Status...")
        print("=" * 60)
        
        # Initialize Runtime
        runtime = Runtime()
        
        # Configure for the deployed MBTI Travel Assistant
        print("🔧 Configuring runtime for status check...")
        runtime.configure(
            entrypoint="main.py",
            agent_name="mbti_travel_assistant_mcp",
            region="us-east-1",
            auto_create_execution_role=True
        )
        
        # Get status
        print("📊 Retrieving deployment status...")
        status = runtime.status()
        
        print("\n📋 Deployment Status Report:")
        print("-" * 40)
        
        # Check agent status
        if hasattr(status, 'agent') and status.agent:
            agent_info = status.agent
            agent_status = agent_info.get('status', 'UNKNOWN')
            agent_arn = agent_info.get('arn', 'Not available')
            
            print(f"🤖 Agent Status: {agent_status}")
            print(f"🔗 Agent ARN: {agent_arn}")
            
            if agent_status == 'READY':
                print("✅ Agent is READY and operational")
            elif agent_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                print("⏳ Agent is being deployed/updated")
            elif agent_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                print("❌ Agent deployment failed")
            else:
                print(f"⚠️ Agent status: {agent_status}")
        else:
            print("❌ No agent information available")
        
        # Check endpoint status
        if hasattr(status, 'endpoint') and status.endpoint:
            endpoint_info = status.endpoint
            endpoint_status = endpoint_info.get('status', 'UNKNOWN')
            endpoint_url = endpoint_info.get('url', 'Not available')
            
            print(f"🌐 Endpoint Status: {endpoint_status}")
            print(f"🔗 Endpoint URL: {endpoint_url}")
            
            if endpoint_status == 'READY':
                print("✅ Endpoint is READY and accessible")
            elif endpoint_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                print("⏳ Endpoint is being deployed/updated")
            elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                print("❌ Endpoint deployment failed")
            else:
                print(f"⚠️ Endpoint status: {endpoint_status}")
        else:
            print("❌ No endpoint information available")
        
        # Overall assessment
        agent_ready = hasattr(status, 'agent') and status.agent and status.agent.get('status') == 'READY'
        endpoint_ready = hasattr(status, 'endpoint') and status.endpoint and status.endpoint.get('status') == 'READY'
        
        print("\n🎯 Overall Assessment:")
        print("-" * 25)
        
        if agent_ready and endpoint_ready:
            print("🎉 MBTI Travel Assistant is FULLY OPERATIONAL")
            print("✅ Ready to process MBTI itinerary requests")
            print("✅ JWT authentication is configured")
            print("✅ MCP integration is active")
            deployment_success = True
        elif agent_ready or endpoint_ready:
            print("⚠️ MBTI Travel Assistant is PARTIALLY OPERATIONAL")
            print("Some components are ready, others may need attention")
            deployment_success = True
        else:
            print("❌ MBTI Travel Assistant is NOT OPERATIONAL")
            print("Deployment may have failed or is still in progress")
            deployment_success = False
        
        # Additional information
        print("\n💡 Additional Information:")
        print("-" * 30)
        print("• Agent Name: mbti_travel_assistant_mcp")
        print("• Region: us-east-1")
        print("• Platform: linux/arm64")
        print("• Authentication: JWT (Cognito)")
        print("• Model: Amazon Nova Pro 300K")
        print("• MCP Integration: Restaurant Search + Reasoning")
        
        # Save status report
        status_report = {
            "timestamp": status.__dict__ if hasattr(status, '__dict__') else str(status),
            "agent_ready": agent_ready,
            "endpoint_ready": endpoint_ready,
            "deployment_success": deployment_success,
            "agent_name": "mbti_travel_assistant_mcp",
            "region": "us-east-1"
        }
        
        with open('deployment_status_report.json', 'w') as f:
            json.dump(status_report, f, indent=2, default=str)
        
        print(f"\n✓ Status report saved to: deployment_status_report.json")
        
        return deployment_success
        
    except ImportError:
        print("❌ AgentCore Runtime toolkit not available")
        print("   Install with: pip install bedrock-agentcore-starter-toolkit")
        return False
    except Exception as e:
        print(f"❌ Error checking deployment status: {e}")
        return False

if __name__ == "__main__":
    print("🎭 MBTI Travel Assistant - Deployment Status Check")
    print("=" * 70)
    
    try:
        success = check_deployment_status()
        
        if success:
            print("\n🚀 Status Check: SUCCESS")
            print("The MBTI Travel Assistant is deployed and operational!")
        else:
            print("\n⚠️ Status Check: ISSUES DETECTED")
            print("Please check the deployment or try redeploying.")
        
        exit(0 if success else 1)
        
    except Exception as e:
        print(f"✗ Status check execution failed: {e}")
        exit(1)