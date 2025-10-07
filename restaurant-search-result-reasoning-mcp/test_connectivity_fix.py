#!/usr/bin/env python3
"""
Test script to verify the connectivity test fix for Restaurant Search Result Reasoning MCP Server.
"""

from scripts.deploy_agentcore import AgentCoreDeployment

def test_connectivity():
    """Test the fixed connectivity test method."""
    print("🧪 Testing connectivity test fix for Restaurant Search Result Reasoning MCP...")
    
    try:
        # Initialize deployment
        deployment = AgentCoreDeployment(region='us-east-1')
        
        # Configure the runtime
        deployment.configure_agentcore_runtime(
            entrypoint='main.py',
            agent_name='restaurant_search_result_reasoning_mcp',
            requirements_file='requirements.txt'
        )
        
        # Test connectivity
        connectivity_result = deployment.test_deployment_connectivity()
        
        if connectivity_result:
            print("\n🎉 SUCCESS: Connectivity test passed!")
            print("✓ The deployment script fix is working correctly")
            print("✓ Agent and endpoint status are properly detected")
            return True
        else:
            print("\n❌ FAILED: Connectivity test failed")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_connectivity()
    exit(0 if success else 1)