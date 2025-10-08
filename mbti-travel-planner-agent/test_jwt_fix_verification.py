#!/usr/bin/env python3
"""
Simple test to verify JWT token fix is working correctly.
"""

import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_jwt_token_update():
    """Test that JWT token update function works correctly."""
    
    print("=" * 60)
    print("JWT TOKEN UPDATE FIX VERIFICATION")
    print("=" * 60)
    
    try:
        # Import main components
        from main import (
            update_agentcore_jwt_token, 
            update_tools_jwt_token,
            agentcore_client, 
            agent,
            AGENT_AVAILABLE,
            AGENTCORE_AVAILABLE
        )
        
        print(f"✅ AgentCore Available: {AGENTCORE_AVAILABLE}")
        print(f"✅ Agent Available: {AGENT_AVAILABLE}")
        print(f"✅ AgentCore Client: {agentcore_client is not None}")
        print(f"✅ Agent: {agent is not None}")
        
        if agent:
            # Check different ways to access tools
            tools = None
            if hasattr(agent, 'tools'):
                tools = agent.tools
                print(f"✅ Agent has {len(agent.tools)} tools via .tools attribute")
            elif hasattr(agent, '_tools'):
                tools = agent._tools
                print(f"✅ Agent has {len(agent._tools)} tools via ._tools attribute")
            else:
                print("❌ Agent has no accessible tools attribute")
                # Try to inspect the agent object
                print(f"Agent type: {type(agent)}")
                print(f"Agent attributes: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
                return False
            
            if not tools:
                print("❌ No tools found in agent")
                return False
            
            # Check if tools have runtime_client
            tools_with_runtime_client = 0
            for i, tool in enumerate(tools):
                print(f"  Tool {i}: {type(tool).__name__}")
                print(f"    Attributes: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
                
                if hasattr(tool, 'runtime_client'):
                    tools_with_runtime_client += 1
                    print(f"    ✅ has runtime_client: {hasattr(tool.runtime_client, 'jwt_token')}")
                elif hasattr(tool, '_tool_obj') and hasattr(tool._tool_obj, 'runtime_client'):
                    tools_with_runtime_client += 1
                    print(f"    ✅ has nested runtime_client: {hasattr(tool._tool_obj.runtime_client, 'jwt_token')}")
                elif hasattr(tool, 'original_tool') and hasattr(tool.original_tool, 'runtime_client'):
                    tools_with_runtime_client += 1
                    print(f"    ✅ has original_tool.runtime_client: {hasattr(tool.original_tool.runtime_client, 'jwt_token')}")
                else:
                    print(f"    ❌ no runtime_client found")
            
            print(f"✅ Tools with runtime_client: {tools_with_runtime_client}")
            
            # Test JWT token update
            test_jwt_token = "test_jwt_token_12345"
            
            print(f"\n🔧 Testing JWT token update with: {test_jwt_token}")
            
            # Update JWT token
            update_agentcore_jwt_token(test_jwt_token)
            
            # Verify global client has the token
            if agentcore_client:
                print(f"✅ Global AgentCore client JWT token: {agentcore_client.jwt_token == test_jwt_token}")
            
            # Verify tools have the token
            tools_updated = 0
            for i, tool in enumerate(tools):
                if hasattr(tool, 'runtime_client') and hasattr(tool.runtime_client, 'jwt_token'):
                    if tool.runtime_client.jwt_token == test_jwt_token:
                        tools_updated += 1
                        print(f"  ✅ Tool {i} JWT token updated correctly")
                    else:
                        print(f"  ❌ Tool {i} JWT token not updated: {tool.runtime_client.jwt_token}")
                elif hasattr(tool, '_tool_obj') and hasattr(tool._tool_obj, 'runtime_client'):
                    if hasattr(tool._tool_obj.runtime_client, 'jwt_token'):
                        if tool._tool_obj.runtime_client.jwt_token == test_jwt_token:
                            tools_updated += 1
                            print(f"  ✅ Tool {i} (nested) JWT token updated correctly")
                        else:
                            print(f"  ❌ Tool {i} (nested) JWT token not updated: {tool._tool_obj.runtime_client.jwt_token}")
                elif hasattr(tool, 'original_tool') and hasattr(tool.original_tool, 'runtime_client'):
                    if hasattr(tool.original_tool.runtime_client, 'jwt_token'):
                        if tool.original_tool.runtime_client.jwt_token == test_jwt_token:
                            tools_updated += 1
                            print(f"  ✅ Tool {i} (original_tool) JWT token updated correctly")
                        else:
                            print(f"  ❌ Tool {i} (original_tool) JWT token not updated: {tool.original_tool.runtime_client.jwt_token}")
            
            print(f"✅ Tools successfully updated: {tools_updated}/{tools_with_runtime_client}")
            
            if tools_updated == tools_with_runtime_client and tools_updated > 0:
                print("\n🎉 JWT TOKEN UPDATE FIX IS WORKING CORRECTLY!")
                return True
            else:
                print("\n❌ JWT TOKEN UPDATE FIX NEEDS MORE WORK")
                return False
        else:
            print("❌ Agent has no tools to test")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jwt_token_update()
    exit(0 if success else 1)