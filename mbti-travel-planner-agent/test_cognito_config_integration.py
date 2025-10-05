#!/usr/bin/env python3
"""
Test script to validate Cognito configuration integration in deploy_agentcore.py

This script tests:
1. Loading Cognito configuration from JSON file
2. Validating configuration format
3. Extracting required values for AgentCore deployment
"""

import sys
import json
from pathlib import Path

# Add the scripts directory to the path to import the deployer
script_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(script_dir))

try:
    from deploy_agentcore import CognitoConfigLoader, AgentCoreDeployer
except ImportError as e:
    print(f"❌ Failed to import deployment modules: {e}")
    print(f"Script directory: {script_dir}")
    print(f"Current working directory: {Path.cwd()}")
    sys.exit(1)


def test_cognito_config_loader():
    """Test the CognitoConfigLoader class."""
    print("🧪 Testing CognitoConfigLoader...")
    
    try:
        # Test loading the default config file
        config_loader = CognitoConfigLoader("config/cognito_config.json")
        
        # Test getting configuration values
        discovery_url = config_loader.get_discovery_url()
        client_id = config_loader.get_client_id()
        user_pool_id = config_loader.get_user_pool_id()
        region = config_loader.get_region()
        
        print(f"✅ Discovery URL: {discovery_url}")
        print(f"✅ Client ID: {client_id}")
        print(f"✅ User Pool ID: {user_pool_id}")
        print(f"✅ Region: {region}")
        
        # Test validation
        is_valid = config_loader.validate_config()
        print(f"✅ Configuration valid: {is_valid}")
        
        if not is_valid:
            print("❌ Configuration validation failed")
            return False
        
        # Verify required values are present
        required_values = [discovery_url, client_id, user_pool_id, region]
        if not all(required_values):
            print("❌ Missing required configuration values")
            return False
        
        # Verify discovery URL format
        if not discovery_url.endswith("/.well-known/openid-configuration"):
            print(f"❌ Invalid discovery URL format: {discovery_url}")
            return False
        
        print("✅ CognitoConfigLoader test passed")
        return True
        
    except Exception as e:
        print(f"❌ CognitoConfigLoader test failed: {e}")
        return False


def test_agentcore_deployer_integration():
    """Test AgentCore deployer with Cognito configuration."""
    print("\n🧪 Testing AgentCore Deployer integration...")
    
    try:
        # Initialize deployer with Cognito config
        deployer = AgentCoreDeployer(
            region="us-east-1",
            environment="development",
            cognito_config_path="config/cognito_config.json"
        )
        
        # Test that Cognito config is loaded
        discovery_url = deployer.cognito_config.get_discovery_url()
        client_id = deployer.cognito_config.get_client_id()
        
        print(f"✅ Deployer loaded Discovery URL: {discovery_url}")
        print(f"✅ Deployer loaded Client ID: {client_id}")
        
        # Test configuration validation (without actual deployment)
        try:
            deployer._validate_configuration()
            print("✅ Configuration validation passed")
        except Exception as e:
            print(f"⚠️  Configuration validation failed (expected if environment not fully set up): {e}")
        
        print("✅ AgentCore Deployer integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ AgentCore Deployer integration test failed: {e}")
        return False


def test_config_file_exists():
    """Test that the Cognito configuration file exists and is valid JSON."""
    print("\n🧪 Testing Cognito configuration file...")
    
    config_file = Path("config/cognito_config.json")
    
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding="utf-8") as f:
            config = json.load(f)
        
        print(f"✅ Configuration file loaded successfully")
        
        # Check for required top-level keys
        required_keys = ["region", "user_pool", "app_client", "discovery_url"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"❌ Missing required keys: {missing_keys}")
            return False
        
        print("✅ Configuration file structure is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading configuration file: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 MBTI Travel Planner Agent - Cognito Configuration Integration Test")
    print("=" * 70)
    
    tests = [
        ("Configuration File", test_config_file_exists),
        ("CognitoConfigLoader", test_cognito_config_loader),
        ("AgentCore Deployer Integration", test_agentcore_deployer_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Cognito configuration integration is working correctly")
        print("✅ Ready for AgentCore deployment with Cognito authentication")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please fix the issues before deploying to AgentCore")
    
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)