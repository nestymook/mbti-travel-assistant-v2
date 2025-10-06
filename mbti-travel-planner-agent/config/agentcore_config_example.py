"""
AgentCore Configuration Usage Examples

This module demonstrates how to use the AgentCore environment-based
configuration system.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.agentcore_environment_config import (
    load_agentcore_environment_config,
    get_agentcore_config_manager,
    validate_agentcore_environment,
    EnvironmentConfig
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example: Basic configuration loading."""
    print("=" * 60)
    print("Example 1: Basic Configuration Loading")
    print("=" * 60)
    
    try:
        # Load configuration for current environment (auto-detected)
        config = load_agentcore_environment_config()
        
        print(f"✅ Loaded configuration for environment: {config.environment}")
        print(f"   AgentCore region: {config.agentcore.region}")
        print(f"   Search agent ARN: {config.agentcore.restaurant_search_agent_arn}")
        print(f"   Reasoning agent ARN: {config.agentcore.restaurant_reasoning_agent_arn}")
        print(f"   Cognito user pool: {config.cognito.user_pool_id}")
        print(f"   Debug mode: {config.debug_mode}")
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")


def example_specific_environment():
    """Example: Loading configuration for specific environment."""
    print("\n" + "=" * 60)
    print("Example 2: Specific Environment Configuration")
    print("=" * 60)
    
    environments = ['development', 'staging', 'production']
    
    for env in environments:
        try:
            config = load_agentcore_environment_config(environment=env)
            print(f"✅ {env.capitalize()}:")
            print(f"   Timeout: {config.agentcore.timeout_seconds}s")
            print(f"   Max retries: {config.agentcore.max_retries}")
            print(f"   Caching enabled: {config.performance.enable_caching}")
            print(f"   Metrics namespace: {config.monitoring.metrics_namespace}")
            
        except Exception as e:
            print(f"❌ {env.capitalize()}: {e}")


def example_configuration_validation():
    """Example: Configuration validation."""
    print("\n" + "=" * 60)
    print("Example 3: Configuration Validation")
    print("=" * 60)
    
    # Validate environment variables
    issues = validate_agentcore_environment()
    
    if issues:
        print("❌ Environment variable issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All environment variables are valid")
    
    # Validate loaded configuration
    try:
        config_manager = get_agentcore_config_manager()
        config = config_manager.load_config()
        
        config_issues = config_manager.validate_configuration(config)
        
        if config_issues:
            print("❌ Configuration issues found:")
            for issue in config_issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration is valid")
            
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")


def example_configuration_summary():
    """Example: Getting configuration summary."""
    print("\n" + "=" * 60)
    print("Example 4: Configuration Summary")
    print("=" * 60)
    
    try:
        config_manager = get_agentcore_config_manager()
        config = config_manager.load_config()
        summary = config_manager.get_configuration_summary()
        
        print("📋 Configuration Summary:")
        print(f"   Environment: {summary['environment']}")
        
        print("   AgentCore:")
        for key, value in summary['agentcore'].items():
            print(f"     {key}: {value}")
        
        print("   Cognito:")
        for key, value in summary['cognito'].items():
            if key == 'client_secret':
                print(f"     {key}: {'*' * len(str(value))}")  # Hide secret
            else:
                print(f"     {key}: {value}")
        
        print("   Performance:")
        for key, value in summary['performance'].items():
            print(f"     {key}: {value}")
        
        print("   Monitoring:")
        for key, value in summary['monitoring'].items():
            print(f"     {key}: {value}")
        
        print(f"   Debug mode: {summary['debug_mode']}")
        
    except Exception as e:
        print(f"❌ Failed to get configuration summary: {e}")


def example_environment_detection():
    """Example: Environment detection logic."""
    print("\n" + "=" * 60)
    print("Example 5: Environment Detection")
    print("=" * 60)
    
    config_manager = get_agentcore_config_manager()
    
    # Show current environment variables that affect detection
    env_vars = [
        'ENVIRONMENT',
        'AWS_ENVIRONMENT', 
        'DEPLOYMENT_STAGE',
        'LOCAL_DEVELOPMENT',
        'DEBUG',
        'STAGING',
        'PRODUCTION'
    ]
    
    print("🔍 Environment detection variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: (not set)")
    
    detected_env = config_manager.detect_environment()
    print(f"\n🎯 Detected environment: {detected_env}")


def example_custom_config_dir():
    """Example: Using custom configuration directory."""
    print("\n" + "=" * 60)
    print("Example 6: Custom Configuration Directory")
    print("=" * 60)
    
    # Example of using a custom config directory
    custom_config_dir = "/path/to/custom/config"
    
    print(f"📁 Using custom config directory: {custom_config_dir}")
    print("   (This would fail unless the directory exists)")
    
    try:
        # This would work if the custom directory existed
        config = load_agentcore_environment_config(config_dir=custom_config_dir)
        print(f"✅ Loaded config from custom directory")
    except Exception as e:
        print(f"❌ Expected failure: {e}")
    
    # Show default config directory
    default_config_dir = os.path.join(os.path.dirname(__file__))
    print(f"📁 Default config directory: {default_config_dir}")


def example_error_handling():
    """Example: Error handling scenarios."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)
    
    # Save original environment variables
    original_env = {}
    test_vars = ['COGNITO_USER_POOL_ID', 'COGNITO_CLIENT_ID', 'COGNITO_CLIENT_SECRET']
    
    for var in test_vars:
        original_env[var] = os.getenv(var)
    
    try:
        # Test with missing required variables
        print("🧪 Testing with missing Cognito configuration...")
        
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
        
        try:
            config = load_agentcore_environment_config()
            print("❌ Unexpected success - should have failed")
        except ValueError as e:
            print(f"✅ Expected error caught: {e}")
        
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    print("🔄 Environment variables restored")


def main():
    """Run all examples."""
    print("🚀 AgentCore Configuration System Examples")
    print("=" * 60)
    
    # Run all examples
    example_basic_usage()
    example_specific_environment()
    example_configuration_validation()
    example_configuration_summary()
    example_environment_detection()
    example_custom_config_dir()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("✨ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()