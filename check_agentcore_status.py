#!/usr/bin/env python3
"""
Check AgentCore Status using AWS CLI approach
"""

import subprocess
import json


def check_agentcore_status_cli():
    """Check AgentCore status using AWS CLI."""
    print("🔍 Checking AgentCore Deployment Status via AWS CLI")
    print("=" * 55)
    
    agent_id = "restaurant_search_mcp_no_auth-QkpwVXBnQD"
    
    try:
        # Try to get agent runtime info using AWS CLI
        cmd = [
            "aws", "bedrock-agentcore", "get-agent-runtime",
            "--agent-runtime-id", agent_id,
            "--region", "us-east-1"
        ]
        
        print(f"📋 Checking agent: {agent_id}")
        print(f"🔧 Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse JSON response
            response = json.loads(result.stdout)
            print("✅ Agent runtime found!")
            
            status = response.get('status', 'UNKNOWN')
            print(f"\n🎯 Current Status: {status}")
            
            if status == 'READY':
                print("🎉 Agent is READY and operational!")
                
                # Show key information
                if 'agentRuntimeArn' in response:
                    print(f"🏷️ Agent ARN: {response['agentRuntimeArn']}")
                
                if 'protocolConfiguration' in response:
                    protocol = response['protocolConfiguration']
                    print(f"🔧 Protocol: {protocol.get('serverProtocol', 'N/A')}")
                
                # Show endpoint if available
                endpoint_url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{agent_id}/invocations"
                print(f"🔗 MCP Endpoint: {endpoint_url}")
                
            elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                print("❌ Agent deployment FAILED")
                
            elif status in ['CREATING', 'UPDATING']:
                print("⏳ Agent deployment is IN PROGRESS")
            
            print(f"\n📊 Full Response:")
            print(json.dumps(response, indent=2, default=str))
            
            return response
            
        else:
            print(f"❌ AWS CLI Error (exit code {result.returncode}):")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
            if "ResourceNotFoundException" in result.stderr:
                print("\n💡 This likely means the agent was not successfully deployed")
            elif "AccessDeniedException" in result.stderr:
                print("\n💡 Check IAM permissions for bedrock-agentcore:GetAgentRuntime")
            
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return None
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install AWS CLI.")
        return None
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return None


def list_agent_runtimes():
    """List all agent runtimes to see what's available."""
    print("\n📋 Listing All Agent Runtimes")
    print("=" * 35)
    
    try:
        cmd = ["aws", "bedrock-agentcore", "list-agent-runtimes", "--region", "us-east-1"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            
            if 'agentRuntimeSummaries' in response:
                summaries = response['agentRuntimeSummaries']
                
                if summaries:
                    print(f"✅ Found {len(summaries)} agent runtime(s):")
                    
                    for i, summary in enumerate(summaries, 1):
                        print(f"\n{i}. Agent: {summary.get('agentRuntimeName', 'N/A')}")
                        print(f"   ID: {summary.get('agentRuntimeId', 'N/A')}")
                        print(f"   Status: {summary.get('status', 'N/A')}")
                        print(f"   Created: {summary.get('creationTime', 'N/A')}")
                else:
                    print("📭 No agent runtimes found")
            else:
                print("❓ Unexpected response format")
                
        else:
            print(f"❌ Failed to list agents: {result.stderr}")
            
    except Exception as e:
        print(f"💥 Error listing agents: {e}")


if __name__ == "__main__":
    # Check specific agent
    result = check_agentcore_status_cli()
    
    # List all agents for context
    list_agent_runtimes()
    
    if result:
        status = result.get('status', 'UNKNOWN')
        if status == 'READY':
            print("\n🎉 DEPLOYMENT STATUS: SUCCESS - MCP server is ready!")
        elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            print("\n💥 DEPLOYMENT STATUS: FAILED")
        elif status in ['CREATING', 'UPDATING']:
            print("\n⏳ DEPLOYMENT STATUS: IN PROGRESS")
        else:
            print(f"\n❓ DEPLOYMENT STATUS: {status}")
    else:
        print("\n❌ DEPLOYMENT STATUS: UNKNOWN OR FAILED")