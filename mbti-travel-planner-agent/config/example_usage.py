#!/usr/bin/env python3
"""
Example Usage of Environment Configuration System

This script demonstrates how to use the environment configuration system
in the MBTI Travel Planner Agent.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.environment_loader import (
    load_environment_config,
    validate_current_environment,
    get_config_loader
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example of basic configuration usage."""
    print("=" * 60)
    print("BASIC CONFIGURATION USAGE")
    print("=" * 60)
    
    # Load configuration for current environment (auto-detected)
    config = load_environment_config()
    
    print(f"Environment: {config.environment}")
    print(f"Gateway URL: {config.base_url}")
    print(f"Gateway Timeout: {config.timeout}s")
    print(f"Auth Required: {config.auth_required}")
    print(f"Agent Model: {config.agent_model}")
    print(f"AWS Region: {config.aws_region}")


def example_specific_environment():
    """Example of loading configuration for specific environments."""
    print("\n" + "=" * 60)
    print("SPECIFIC ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    environments = ['development', 'staging', 'production']
    
    # Save original environment variables
    original_env_vars = {}
    env_vars_to_clear = ['ENVIRONMENT', 'GATEWAY_AUTH_REQUIRED', 'GATEWAY_TIMEOUT', 'GATEWAY_MAX_RETRIES']
    for var in env_vars_to_clear:
        original_env_vars[var] = os.getenv(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        for env in environments:
            print(f"\n--- {env.upper()} Environment ---")
            try:
                config = load_environment_config(env)
                print(f"Gateway URL: {config.base_url}")
                print(f"Timeout: {config.timeout}s")
                print(f"Max Retries: {config.max_retries}")
                print(f"Auth Required: {config.auth_required}")
            except Exception as e:
                print(f"Error loading {env}: {e}")
    finally:
        # Restore original environment variables
        for var, value in original_env_vars.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def example_validation():
    """Example of configuration validation."""
    print("\n" + "=" * 60)
    print("CONFIGURATION VALIDATION")
    print("=" * 60)
    
    # Validate current environment variables
    issues = validate_current_environment()
    
    if not issues:
        print("✅ All environment variables are valid")
    else:
        print("❌ Environment variable issues found:")
        for issue in issues:
            print(f"  - {issue}")


def example_environment_detection():
    """Example of environment detection."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT DETECTION")
    print("=" * 60)
    
    loader = get_config_loader()
    detected_env = loader.detect_environment()
    
    print(f"Detected environment: {detected_env}")
    
    # Show current environment variables that affect detection
    env_vars = [
        'ENVIRONMENT', 'AWS_ENVIRONMENT', 'DEPLOYMENT_STAGE',
        'LOCAL_DEVELOPMENT', 'DEBUG', 'STAGING', 'PRODUCTION'
    ]
    
    print("\nEnvironment variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}={value}")


def example_configuration_summary():
    """Example of getting configuration summary."""
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    
    loader = get_config_loader()
    config = loader.load_config()
    summary = loader.get_environment_summary()
    
    print(f"Environment: {summary['environment']}")
    print(f"Gateway Configuration:")
    for key, value in summary['gateway'].items():
        print(f"  {key}: {value}")
    
    print(f"Agent Configuration:")
    for key, value in summary['agent'].items():
        print(f"  {key}: {value}")
    
    print(f"AWS Configuration:")
    for key, value in summary['aws'].items():
        print(f"  {key}: {value}")


def example_with_environment_override():
    """Example of overriding configuration with environment variables."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT VARIABLE OVERRIDE")
    print("=" * 60)
    
    # Set environment variable to override default
    os.environ['GATEWAY_TIMEOUT'] = '120'
    os.environ['AGENT_TEMPERATURE'] = '0.5'
    
    try:
        config = load_environment_config('development')
        print(f"Gateway Timeout: {config.timeout}s (overridden)")
        print(f"Agent Temperature: {config.agent_temperature} (overridden)")
        print(f"Gateway URL: {config.base_url} (from defaults)")
    finally:
        # Clean up
        if 'GATEWAY_TIMEOUT' in os.environ:
            del os.environ['GATEWAY_TIMEOUT']
        if 'AGENT_TEMPERATURE' in os.environ:
            del os.environ['AGENT_TEMPERATURE']


def example_error_handling():
    """Example of error handling."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING")
    print("=" * 60)
    
    # Try to load configuration with invalid values
    os.environ['GATEWAY_TIMEOUT'] = 'invalid'
    
    try:
        config = load_environment_config('development')
        print("Configuration loaded successfully")
    except ValueError as e:
        print(f"✅ Caught expected validation error: {e}")
    finally:
        # Clean up
        if 'GATEWAY_TIMEOUT' in os.environ:
            del os.environ['GATEWAY_TIMEOUT']
    
    # Try to load configuration with missing required value
    original_env = os.getenv('ENVIRONMENT')
    if 'ENVIRONMENT' in os.environ:
        del os.environ['ENVIRONMENT']
    
    try:
        # This should work because it will default to development
        config = load_environment_config()
        print(f"✅ Auto-detected environment: {config.environment}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Restore original environment
        if original_env:
            os.environ['ENVIRONMENT'] = original_env


def main():
    """Run all examples."""
    print("MBTI Travel Planner Agent - Configuration System Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_specific_environment()
        example_validation()
        example_environment_detection()
        example_configuration_summary()
        example_with_environment_override()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n💥 Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()