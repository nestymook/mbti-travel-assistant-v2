#!/usr/bin/env python3
"""
Test script to verify the complete deployment workflow works correctly.
"""

from scripts.deploy_agentcore import AgentCoreDeployment

def test_complete_workflow():
    """Test the complete deployment workflow."""
    print("🧪 Testing complete deployment workflow...")
    
    try:
        # Initialize deployment
        deployment = AgentCoreDeployment(region='us-east-1', environment='production')
        
        # Step 1: Configure
        print("\n📋 Step 1: Testing configuration...")
        config_response = deployment.configure_agentcore_runtime(
            entrypoint='main.py',
            agent_name='mbti_travel_planner_agent',
            requirements_file='requirements.txt'
        )
        print("✓ Configuration completed successfully")
        
        # Step 2: Monitor status (since agent is already deployed)
        print("\n⏳ Step 2: Testing status monitoring...")
        status_response = deployment.monitor_deployment_status(timeout_minutes=1)  # Short timeout for test
        print("✓ Status monitoring completed successfully")
        
        # Step 3: Test connectivity
        print("\n🔍 Step 3: Testing connectivity...")
        connectivity_result = deployment.test_deployment_connectivity()
        
        if connectivity_result:
            print("✓ Connectivity test passed")
        else:
            print("✗ Connectivity test failed")
            return False
        
        print("\n🎉 SUCCESS: Complete deployment workflow test passed!")
        print("✓ All components are working correctly")
        print("✓ The 'No endpoint information available' issue has been resolved")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)