#!/usr/bin/env python3
"""
Simple deployment test for Restaurant Reasoning MCP Server
"""

import json
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_deployment_info():
    """Test deployment information from config file"""
    print("🔍 Testing Restaurant Reasoning MCP Server Deployment")
    print("=" * 60)
    
    try:
        # Load deployment config
        config_file = Path("agentcore_deployment_config.json")
        if not config_file.exists():
            print("❌ Deployment config file not found")
            return False
            
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Extract key information
        agent_name = config.get("agent_name", "Unknown")
        region = config.get("region", "Unknown")
        
        final_result = config.get("final_deployment_result", {})
        final_status = final_result.get("final_status", "")
        
        print(f"📋 Agent Name: {agent_name}")
        print(f"🌍 Region: {region}")
        print(f"🔧 Server Type: {config.get('server_type', 'Unknown')}")
        
        # Extract agent ARN and status
        if "agent_arn=" in final_status:
            agent_arn_start = final_status.find("agent_arn='") + len("agent_arn='")
            agent_arn_end = final_status.find("'", agent_arn_start)
            agent_arn = final_status[agent_arn_start:agent_arn_end]
            print(f"🎯 Agent ARN: {agent_arn}")
        
        # Check if deployment was successful
        if "'status': 'READY'" in final_status:
            print("✅ Agent Status: READY")
            deployment_success = True
        else:
            print("⚠️ Agent Status: Unknown")
            deployment_success = False
            
        # Check authentication config
        auth_config = config.get("auth_config", {})
        if auth_config:
            print("🔐 Authentication: Configured (JWT)")
            jwt_config = auth_config.get("customJWTAuthorizer", {})
            if jwt_config.get("discoveryUrl"):
                print(f"🔑 Discovery URL: {jwt_config['discoveryUrl']}")
        else:
            print("🔓 Authentication: Not configured")
        
        # Check Cognito config
        cognito_config = config.get("cognito_config", {})
        if cognito_config:
            user_pool_id = cognito_config.get("user_pool", {}).get("user_pool_id")
            client_id = cognito_config.get("app_client", {}).get("client_id")
            test_user = cognito_config.get("test_user", {}).get("username")
            
            print(f"👤 User Pool ID: {user_pool_id}")
            print(f"📱 Client ID: {client_id}")
            print(f"🧪 Test User: {test_user}")
        
        print("\n" + "=" * 60)
        
        if deployment_success:
            print("🎉 Deployment Status: SUCCESS")
            print("✅ Restaurant Reasoning MCP Server is deployed and ready!")
            print("\n💡 Next Steps:")
            print("   1. Test MCP tools with authentication")
            print("   2. Verify reasoning capabilities")
            print("   3. Run integration tests")
            return True
        else:
            print("⚠️ Deployment Status: NEEDS VERIFICATION")
            print("🔍 Please check AWS console for detailed status")
            return False
            
    except Exception as e:
        print(f"❌ Error testing deployment: {e}")
        return False

def test_local_imports():
    """Test that local modules can be imported"""
    print("\n🔍 Testing Local Module Imports")
    print("-" * 40)
    
    try:
        # Test core service imports
        from services.restaurant_reasoning_service import RestaurantReasoningService
        print("✅ RestaurantReasoningService imported successfully")
        
        from services.recommendation_service import RecommendationAlgorithm
        print("✅ RecommendationAlgorithm imported successfully")
        
        from services.sentiment_service import SentimentAnalysisService
        print("✅ SentimentAnalysisService imported successfully")
        
        from models.restaurant_models import Restaurant, Sentiment
        print("✅ Restaurant models imported successfully")
        
        # Test MCP server import
        import restaurant_reasoning_mcp_server
        print("✅ MCP server module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Restaurant Reasoning MCP Server - Deployment Test")
    print("=" * 60)
    
    # Test deployment info
    deployment_ok = test_deployment_info()
    
    # Test local imports
    imports_ok = test_local_imports()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Deployment Info: {'✅ PASS' if deployment_ok else '❌ FAIL'}")
    print(f"   Module Imports:  {'✅ PASS' if imports_ok else '❌ FAIL'}")
    
    if deployment_ok and imports_ok:
        print("\n🎉 All tests passed! Deployment is ready for testing.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)