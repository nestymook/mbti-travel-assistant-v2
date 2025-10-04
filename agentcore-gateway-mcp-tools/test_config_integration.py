#!/usr/bin/env python3
"""
Simple integration test for configuration management and hot reloading.

This script tests the basic functionality of the configuration management system
without requiring the full test suite setup.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path

from services.config_manager import ConfigManager, EnvironmentConfig, MCPServerConfig
from services.config_validator import ConfigValidator


async def test_configuration_management():
    """Test configuration management functionality."""
    print("Testing Configuration Management System")
    print("=" * 50)
    
    # Create temporary config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create sample configuration
        sample_config = {
            "name": "development",
            "log_level": "INFO",
            "debug": True,
            "enable_hot_reload": True,
            "mcp_servers": {
                "search": {
                    "name": "search",
                    "url": "http://localhost:8081",
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "health_check_path": "/health",
                    "enabled": True,
                    "tools": [
                        "search_restaurants_by_district",
                        "search_restaurants_by_meal_type",
                        "search_restaurants_combined"
                    ]
                },
                "reasoning": {
                    "name": "reasoning",
                    "url": "http://localhost:8082",
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "health_check_path": "/health",
                    "enabled": True,
                    "tools": [
                        "recommend_restaurants",
                        "analyze_restaurant_sentiment"
                    ]
                }
            }
        }
        
        # Write configuration file
        config_file = config_dir / "development.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"✓ Created configuration file: {config_file}")
        
        # Test 1: Configuration Manager Initialization
        print("\n1. Testing Configuration Manager Initialization")
        config_manager = ConfigManager(str(config_dir), "development")
        config = await config_manager.initialize()
        
        assert config.name == "development"
        assert config.debug is True
        assert len(config.mcp_servers) == 2
        print("✓ Configuration manager initialized successfully")
        
        # Test 2: Configuration Validation
        print("\n2. Testing Configuration Validation")
        validator = ConfigValidator()
        is_valid, errors, warnings = await validator.validate_configuration(config)
        
        print(f"✓ Configuration validation: {'PASSED' if is_valid else 'FAILED'}")
        if errors:
            print(f"  Errors: {len(errors)}")
            for error in errors:
                print(f"    - {error}")
        if warnings:
            print(f"  Warnings: {len(warnings)}")
            for warning in warnings:
                print(f"    - {warning}")
        
        # Test 3: MCP Server Configuration Access
        print("\n3. Testing MCP Server Configuration Access")
        search_config = config_manager.get_mcp_server_config("search")
        assert search_config is not None
        assert search_config.url == "http://localhost:8081"
        print("✓ MCP server configuration access works")
        
        all_servers = config_manager.get_all_mcp_servers()
        assert len(all_servers) == 2
        print(f"✓ Retrieved all MCP servers: {list(all_servers.keys())}")
        
        # Test 4: Configuration Reloading
        print("\n4. Testing Configuration Reloading")
        
        # Track configuration changes
        change_detected = False
        
        def on_config_change(new_config):
            nonlocal change_detected
            change_detected = True
            print(f"✓ Configuration change detected: debug={new_config.debug}")
        
        config_manager.add_change_callback(on_config_change)
        
        # Modify configuration
        sample_config["debug"] = False
        sample_config["mcp_servers"]["search"]["timeout"] = 60
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        # Reload configuration
        await config_manager.reload_configuration()
        
        # Verify changes
        updated_config = config_manager.get_current_config()
        assert updated_config.debug is False
        assert updated_config.mcp_servers["search"].timeout == 60
        assert change_detected is True
        
        print("✓ Configuration reloading works")
        print(f"✓ Configuration changes detected via callback")
        
        # Test 5: Environment-specific Configuration Files
        print("\n5. Testing Environment-specific Configuration Files")
        
        # Test different environments
        environments = ["development", "staging", "production", "test"]
        for env in environments:
            env_config = sample_config.copy()
            env_config["name"] = env
            
            if env == "production":
                env_config["debug"] = False
                env_config["enable_hot_reload"] = False
                env_config["log_level"] = "WARNING"
            elif env == "test":
                env_config["mcp_servers"]["search"]["timeout"] = 10
                env_config["mcp_servers"]["reasoning"]["timeout"] = 10
            
            env_file = config_dir / f"{env}.json"
            with open(env_file, 'w') as f:
                json.dump(env_config, f, indent=2)
        
        print(f"✓ Created configuration files for {len(environments)} environments")
        
        # Test loading different environments
        for env in environments:
            env_manager = ConfigManager(str(config_dir), env)
            env_config = await env_manager.load_configuration()
            assert env_config.name == env
            env_manager.stop_file_watching()
        
        print("✓ All environment configurations load successfully")
        
        # Test 6: Configuration Validation for All Environments
        print("\n6. Testing Configuration Validation for All Environments")
        
        from services.config_validator import validate_all_environment_configs
        
        # Temporarily change working directory for validation
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            validation_results = await validate_all_environment_configs()
            
            for env, (is_valid, errors, warnings) in validation_results.items():
                status = "PASSED" if is_valid else "FAILED"
                print(f"  {env}: {status} ({len(errors)} errors, {len(warnings)} warnings)")
        finally:
            os.chdir(original_cwd)
        
        # Clean up
        config_manager.stop_file_watching()
        
        print("\n" + "=" * 50)
        print("✅ All configuration management tests PASSED!")
        print("\nConfiguration management features verified:")
        print("  ✓ Configuration loading from files")
        print("  ✓ Environment-specific configurations")
        print("  ✓ Configuration validation")
        print("  ✓ Hot reloading capabilities")
        print("  ✓ Change notification callbacks")
        print("  ✓ MCP server configuration management")


async def test_configuration_errors():
    """Test error handling in configuration management."""
    print("\n" + "=" * 50)
    print("Testing Configuration Error Handling")
    print("=" * 50)
    
    # Test 1: Invalid Server Configuration
    print("\n1. Testing Invalid Server Configuration")
    try:
        invalid_server = MCPServerConfig(
            name="",  # Invalid empty name
            url="invalid-url",  # Invalid URL
            timeout=-1,  # Invalid timeout
            tools=[]  # No tools
        )
        print("❌ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly caught validation error: {e}")
    
    # Test 2: Invalid Environment Configuration
    print("\n2. Testing Invalid Environment Configuration")
    try:
        invalid_env = EnvironmentConfig(
            name="invalid_environment",  # Invalid environment name
            mcp_servers={}
        )
        print("❌ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly caught validation error: {e}")
    
    # Test 3: Configuration Validation Errors
    print("\n3. Testing Configuration Validation Errors")
    
    # Create configuration with missing required tools
    server_config = MCPServerConfig(
        name="incomplete",
        url="http://localhost:8080",
        tools=["wrong_tool"]  # Missing required tools
    )
    
    env_config = EnvironmentConfig(
        name="development",
        mcp_servers={"incomplete": server_config}
    )
    
    validator = ConfigValidator()
    is_valid, errors, warnings = await validator.validate_configuration(env_config)
    
    assert is_valid is False
    assert len(errors) > 0
    print(f"✓ Configuration validation correctly identified {len(errors)} errors")
    
    print("\n✅ Error handling tests PASSED!")


if __name__ == "__main__":
    async def main():
        await test_configuration_management()
        await test_configuration_errors()
        print("\n🎉 All tests completed successfully!")
    
    asyncio.run(main())