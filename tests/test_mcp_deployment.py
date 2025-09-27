#!/usr/bin/env python3
"""
Test MCP Deployment by invoking the agent runtime

Follows program guidelines:
- Test payloads are base64 encoded in /tests/payload/
- Test requests are stored in /tests/request/
- Test responses are saved to /tests/response/
- Test results are saved to /tests/results/
"""

import subprocess
import json
import time
import base64
import os


def load_base64_payload(payload_file: str) -> str:
    """Load base64 encoded payload from file."""
    payload_path = os.path.join("tests/payload", payload_file)
    with open(payload_path, 'r') as f:
        return f.read().strip()

def save_response(response_file: str, response_data) -> None:
    """Save response data to response directory."""
    os.makedirs("tests/response", exist_ok=True)
    response_path = os.path.join("tests/response", response_file)
    with open(response_path, 'w') as f:
        if isinstance(response_data, str):
            f.write(response_data)
        else:
            json.dump(response_data, f, indent=2, default=str)

def test_mcp_agent_invocation():
    """Test the MCP agent by invoking it."""
    print("🧪 Testing MCP Agent Deployment via Invocation")
    print("=" * 50)
    
    agent_id = "restaurant_search_mcp_no_auth-QkpwVXBnQD"
    
    try:
        print(f"📋 Testing agent: {agent_id}")
        print(f"🔧 Sending MCP initialize request...")
        
        # Use AWS CLI to invoke the agent runtime
        agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{agent_id}"
        
        # Load base64 payload from file
        payload_b64 = load_base64_payload("mcp_initialize_request.b64")
        
        response_file = "mcp_initialize_response.json"
        cmd = [
            "aws", "bedrock-agentcore", "invoke-agent-runtime",
            "--agent-runtime-arn", agent_arn,
            "--region", "us-east-1",
            "--payload", payload_b64,
            os.path.join("tests/response", response_file)
        ]
        
        print(f"Command: {' '.join(cmd[:6])}... [body omitted]")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Agent invocation successful!")
            
            try:
                # Read response from file
                response_path = os.path.join("tests/response", response_file)
                with open(response_path, "r") as f:
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
    
    try:
        agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{agent_id}"
        
        # Load base64 payload from file
        payload_b64 = load_base64_payload("mcp_tools_list_request.b64")
        
        response_file = "mcp_tools_list_response.json"
        cmd = [
            "aws", "bedrock-agentcore", "invoke-agent-runtime",
            "--agent-runtime-arn", agent_arn,
            "--region", "us-east-1",
            "--payload", payload_b64,
            os.path.join("tests/response", response_file)
        ]
        
        print("🔧 Requesting available MCP tools...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            try:
                # Read response from file
                response_path = os.path.join("tests/response", response_file)
                with open(response_path, "r") as f:
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
    
    # Ensure results directory exists
    os.makedirs("tests/results", exist_ok=True)
    
    # Test 1: Basic MCP initialization
    init_success = test_mcp_agent_invocation()
    
    if init_success:
        # Test 2: List available tools
        tools = test_mcp_tools_list()
        
        # Save test results
        test_results = {
            "mcp_initialization": "SUCCESS" if init_success else "FAILED",
            "tools_found": len(tools),
            "tools_list": tools,
            "deployment_status": "SUCCESS" if len(tools) >= 3 else "PARTIAL",
            "timestamp": time.time()
        }
        
        results_file = os.path.join("tests/results", "mcp_deployment_test_results.json")
        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📊 Deployment Test Summary:")
        print(f"✅ MCP Initialization: SUCCESS")
        print(f"✅ Tools Available: {len(tools)} tools found")
        print(f"💾 Results saved to: {results_file}")
        
        if len(tools) >= 3:  # We expect 3 restaurant search tools
            print("🎉 DEPLOYMENT STATUS: SUCCESS - All systems operational!")
            return True
        else:
            print("⚠️ DEPLOYMENT STATUS: PARTIAL - Some tools may be missing")
            return False
    else:
        # Save failure results
        test_results = {
            "mcp_initialization": "FAILED",
            "tools_found": 0,
            "tools_list": [],
            "deployment_status": "FAILED",
            "timestamp": time.time()
        }
        
        results_file = os.path.join("tests/results", "mcp_deployment_test_results.json")
        with open(results_file, "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📊 Deployment Test Summary:")
        print(f"❌ MCP Initialization: FAILED")
        print(f"💾 Results saved to: {results_file}")
        print("💥 DEPLOYMENT STATUS: FAILED - Agent not responding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)