#!/usr/bin/env python3
"""
Test MCP Deployment by invoking the agent runtime
"""

import subprocess
import json
import time
import base64


def test_mcp_agent_invocation():
    """Test the MCP agent by invoking it."""
    print("🧪 Testing MCP Agent Deployment via Invocation")
    print("=" * 50)
    
    agent_id = "restaurant_search_mcp_no_auth-QkpwVXBnQD"
    
    # Create a simple MCP initialization request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        print(f"📋 Testing agent: {agent_id}")
        print(f"🔧 Sending MCP initialize request...")
        
        # Use AWS CLI to invoke the agent runtime
        agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{agent_id}"
        
        # Encode payload as base64
        payload_json = json.dumps(mcp_request)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()
        
        cmd = [
            "aws", "bedrock-agentcore", "invoke-agent-runtime",
            "--agent-runtime-arn", agent_arn,
            "--region", "us-east-1",
            "--payload", payload_b64,
            "response.json"
        ]
        
        print(f"Command: {' '.join(cmd[:6])}... [body omitted]")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Agent invocation successful!")
            
            try:
                # Read response from file
                with open("response.json", "r") as f:
                    response = json.load(f)
                print(f"\n📊 Response:")
                print(json.dumps(response, indent=2))
                
                # Check if it's a valid MCP response
                if 'jsonrpc' in response and response.get('jsonrpc') == '2.0':
                    print("\n🎉 Valid MCP response received!")
                    
                    if 'result' in response:
                        result_data = response['result']
                        if 'capabilities' in result_data:
                            print("✅ MCP server capabilities detected")
                        if 'serverInfo' in result_data:
                            server_info = result_data['serverInfo']
                            print(f"🔧 Server: {server_info.get('name', 'Unknown')} v{server_info.get('version', 'Unknown')}")
                    
                    return True
                else:
                    print("⚠️ Response doesn't appear to be valid MCP format")
                    return False
                    
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON")
                print(f"Raw response: {result.stdout}")
                return False
                
        else:
            print(f"❌ Agent invocation failed (exit code {result.returncode}):")
            print(f"STDERR: {result.stderr}")
            
            if "ResourceNotFoundException" in result.stderr:
                print("\n💡 Agent not found - deployment may have failed")
            elif "AccessDeniedException" in result.stderr:
                print("\n💡 Access denied - check IAM permissions")
            elif "ValidationException" in result.stderr:
                print("\n💡 Request validation failed")
            
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Request timed out - agent may be starting up")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return False


def test_mcp_tools_list():
    """Test listing MCP tools."""
    print("\n🔧 Testing MCP Tools List")
    print("=" * 30)
    
    agent_id = "restaurant_search_mcp_no_auth-QkpwVXBnQD"
    
    # MCP tools/list request
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{agent_id}"
        
        # Encode payload as base64
        payload_json = json.dumps(tools_request)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()
        
        cmd = [
            "aws", "bedrock-agentcore", "invoke-agent-runtime",
            "--agent-runtime-arn", agent_arn,
            "--region", "us-east-1",
            "--payload", payload_b64,
            "tools_response.json"
        ]
        
        print("🔧 Requesting available MCP tools...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            try:
                # Read response from file
                with open("tools_response.json", "r") as f:
                    response = json.load(f)
                
                if 'result' in response and 'tools' in response['result']:
                    tools = response['result']['tools']
                    print(f"✅ Found {len(tools)} MCP tools:")
                    
                    for i, tool in enumerate(tools, 1):
                        name = tool.get('name', 'Unknown')
                        description = tool.get('description', 'No description')
                        print(f"  {i}. {name}: {description}")
                    
                    return tools
                else:
                    print("⚠️ No tools found in response")
                    print(f"Response: {json.dumps(response, indent=2)}")
                    return []
                    
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                return []
        else:
            print(f"❌ Tools list request failed: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"💥 Error testing tools: {e}")
        return []


def main():
    """Main test function."""
    print("🚀 Restaurant Search MCP Deployment Test")
    print("=" * 45)
    
    # Test 1: Basic MCP initialization
    init_success = test_mcp_agent_invocation()
    
    if init_success:
        # Test 2: List available tools
        tools = test_mcp_tools_list()
        
        print(f"\n📊 Deployment Test Summary:")
        print(f"✅ MCP Initialization: SUCCESS")
        print(f"✅ Tools Available: {len(tools)} tools found")
        
        if len(tools) >= 3:  # We expect 3 restaurant search tools
            print("🎉 DEPLOYMENT STATUS: SUCCESS - All systems operational!")
            return True
        else:
            print("⚠️ DEPLOYMENT STATUS: PARTIAL - Some tools may be missing")
            return False
    else:
        print(f"\n📊 Deployment Test Summary:")
        print(f"❌ MCP Initialization: FAILED")
        print("💥 DEPLOYMENT STATUS: FAILED - Agent not responding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)