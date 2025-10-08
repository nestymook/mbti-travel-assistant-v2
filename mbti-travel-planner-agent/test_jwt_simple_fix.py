#!/usr/bin/env python3
"""
Simple test to verify JWT token fix without full agent initialization.
"""

import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

def test_jwt_token_update_functions():
    """Test that JWT token update functions exist and work."""
    
    print("=" * 60)
    print("JWT TOKEN UPDATE FUNCTIONS TEST")
    print("=" * 60)
    
    try:
        # Import the functions directly
        from main import update_agentcore_jwt_token, update_tools_jwt_token
        
        print("✅ JWT token update functions imported successfully")
        
        # Test that functions are callable
        print(f"✅ update_agentcore_jwt_token is callable: {callable(update_agentcore_jwt_token)}")
        print(f"✅ update_tools_jwt_token is callable: {callable(update_tools_jwt_token)}")
        
        # Create a mock tool with runtime_client
        class MockRuntimeClient:
            def __init__(self):
                self.jwt_token = None
        
        class MockTool:
            def __init__(self):
                self.runtime_client = MockRuntimeClient()
        
        class MockNestedTool:
            def __init__(self):
                self._tool_obj = MockTool()
        
        class MockOriginalTool:
            def __init__(self):
                self.original_tool = MockTool()
        
        # Test update_tools_jwt_token with mock tools
        test_jwt_token = "test_jwt_token_12345"
        mock_tools = [MockTool(), MockNestedTool(), MockOriginalTool()]
        
        print(f"\n🔧 Testing update_tools_jwt_token with mock tools")
        print(f"Test JWT token: {test_jwt_token}")
        
        # Update JWT tokens
        updated_count = update_tools_jwt_token(test_jwt_token, mock_tools)
        
        print(f"✅ Tools updated: {updated_count}")
        
        # Verify tokens were set
        success_count = 0
        
        # Check direct runtime_client
        if mock_tools[0].runtime_client.jwt_token == test_jwt_token:
            success_count += 1
            print("  ✅ Direct runtime_client JWT token updated")
        else:
            print(f"  ❌ Direct runtime_client JWT token not updated: {mock_tools[0].runtime_client.jwt_token}")
        
        # Check nested _tool_obj
        if mock_tools[1]._tool_obj.runtime_client.jwt_token == test_jwt_token:
            success_count += 1
            print("  ✅ Nested _tool_obj JWT token updated")
        else:
            print(f"  ❌ Nested _tool_obj JWT token not updated: {mock_tools[1]._tool_obj.runtime_client.jwt_token}")
        
        # Check original_tool
        if mock_tools[2].original_tool.runtime_client.jwt_token == test_jwt_token:
            success_count += 1
            print("  ✅ Original_tool JWT token updated")
        else:
            print(f"  ❌ Original_tool JWT token not updated: {mock_tools[2].original_tool.runtime_client.jwt_token}")
        
        print(f"\n✅ Successfully updated: {success_count}/3 mock tools")
        
        if success_count == 3 and updated_count == 3:
            print("\n🎉 JWT TOKEN UPDATE FUNCTIONS ARE WORKING CORRECTLY!")
            return True
        else:
            print(f"\n❌ JWT TOKEN UPDATE FUNCTIONS NEED IMPROVEMENT")
            print(f"   Expected: 3 updates, Got: {updated_count}")
            print(f"   Expected: 3 successes, Got: {success_count}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jwt_token_update_functions()
    exit(0 if success else 1)