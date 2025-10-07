#!/usr/bin/env python3
"""
Simple test script to verify the restaurant reasoning MCP server can start.
"""

import sys
import os
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ FastMCP import successful")
    except ImportError as e:
        print(f"✗ FastMCP import failed: {e}")
        return False
    
    try:
        from services.restaurant_reasoning_service import RestaurantReasoningService
        print("✓ RestaurantReasoningService import successful")
    except ImportError as e:
        print(f"✗ RestaurantReasoningService import failed: {e}")
        return False
    
    try:
        from services.auth_middleware import AuthenticationMiddleware, AuthenticationConfig, AuthenticationHelper
        print("✓ Auth middleware imports successful")
    except ImportError as e:
        print(f"✗ Auth middleware imports failed: {e}")
        return False
    
    try:
        from models.restaurant_models import Restaurant, Sentiment, RecommendationResult, SentimentAnalysis
        print("✓ Restaurant models imports successful")
    except ImportError as e:
        print(f"✗ Restaurant models imports failed: {e}")
        return False
    
    try:
        from models.validation_models import ValidationResult, ValidationError
        print("✓ Validation models imports successful")
    except ImportError as e:
        print(f"✗ Validation models imports failed: {e}")
        return False
    
    return True

def test_server_creation():
    """Test that the MCP server can be created."""
    print("\nTesting server creation...")
    
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("test-reasoning-mcp")
        print("✓ FastMCP server creation successful")
        return True
    except Exception as e:
        print(f"✗ FastMCP server creation failed: {e}")
        traceback.print_exc()
        return False

def test_config_loading():
    """Test that configuration can be loaded."""
    print("\nTesting configuration loading...")
    
    try:
        import json
        config_path = os.path.join(os.path.dirname(__file__), 'cognito_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            print("✓ Cognito configuration loaded successfully")
        else:
            print("⚠ Cognito configuration file not found (this is okay for testing)")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Restaurant Reasoning MCP Server Startup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test server creation
    if not test_server_creation():
        all_passed = False
    
    # Test config loading
    if not test_config_loading():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Server should be able to start.")
    else:
        print("✗ Some tests failed. Check the errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())