#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates environment configuration for the MBTI Travel Planner Agent
and provides detailed feedback on configuration issues.
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.environment_loader import (
    EnvironmentConfigLoader,
    GatewayEnvironmentConfig,
    load_environment_config,
    validate_current_environment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment_config(environment: str = None, config_dir: str = None) -> bool:
    """
    Validate configuration for a specific environment.
    
    Args:
        environment: Environment name to validate
        config_dir: Directory containing environment files
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        print(f"\n{'='*60}")
        print(f"VALIDATING CONFIGURATION")
        print(f"{'='*60}")
        
        # Load configuration
        loader = EnvironmentConfigLoader(config_dir)
        
        if environment:
            print(f"Environment: {environment} (specified)")
        else:
            environment = loader.detect_environment()
            print(f"Environment: {environment} (auto-detected)")
        
        print(f"Config directory: {loader.config_dir}")
        
        # Load and validate configuration
        config = loader.load_config(environment)
        
        print(f"\n{'='*60}")
        print(f"CONFIGURATION SUMMARY")
        print(f"{'='*60}")
        
        print(f"Environment: {config.environment}")
        print(f"Gateway URL: {config.base_url}")
        print(f"Gateway Timeout: {config.timeout}s")
        print(f"Gateway Max Retries: {config.max_retries}")
        print(f"Gateway Auth Required: {config.auth_required}")
        print(f"Agent Model: {config.agent_model}")
        print(f"Agent Temperature: {config.agent_temperature}")
        print(f"Agent Max Tokens: {config.agent_max_tokens}")
        print(f"Agent Timeout: {config.agent_timeout}s")
        print(f"AWS Region: {config.aws_region}")
        
        print(f"\n{'='*60}")
        print(f"VALIDATION RESULT")
        print(f"{'='*60}")
        print("✅ Configuration is VALID")
        
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"VALIDATION RESULT")
        print(f"{'='*60}")
        print(f"❌ Configuration is INVALID")
        print(f"Error: {str(e)}")
        
        return False


def validate_environment_variables() -> bool:
    """
    Validate current environment variables.
    
    Returns:
        True if environment variables are valid, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"VALIDATING ENVIRONMENT VARIABLES")
    print(f"{'='*60}")
    
    issues = validate_current_environment()
    
    if not issues:
        print("✅ All environment variables are VALID")
        return True
    else:
        print("❌ Environment variable validation FAILED")
        print("\nIssues found:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False


def test_all_environments(config_dir: str = None) -> Dict[str, bool]:
    """
    Test configuration for all environments.
    
    Args:
        config_dir: Directory containing environment files
        
    Returns:
        Dictionary mapping environment names to validation results
    """
    environments = ['development', 'staging', 'production']
    results = {}
    
    print(f"\n{'='*60}")
    print(f"TESTING ALL ENVIRONMENTS")
    print(f"{'='*60}")
    
    for env in environments:
        print(f"\n--- Testing {env.upper()} environment ---")
        try:
            loader = EnvironmentConfigLoader(config_dir)
            config = loader.load_config(env)
            results[env] = True
            print(f"✅ {env}: VALID")
            print(f"   Gateway: {config.base_url}")
            print(f"   Auth: {'Required' if config.auth_required else 'Not required'}")
        except Exception as e:
            results[env] = False
            print(f"❌ {env}: INVALID - {str(e)}")
    
    return results


def show_environment_detection() -> None:
    """Show how environment detection works."""
    print(f"\n{'='*60}")
    print(f"ENVIRONMENT DETECTION")
    print(f"{'='*60}")
    
    loader = EnvironmentConfigLoader()
    detected_env = loader.detect_environment()
    
    print(f"Detected environment: {detected_env}")
    print("\nEnvironment detection order:")
    print("1. ENVIRONMENT variable")
    print("2. AWS_ENVIRONMENT variable")
    print("3. DEPLOYMENT_STAGE variable")
    print("4. Local development indicators")
    print("5. Staging indicators")
    print("6. Production indicators")
    print("7. Default to development")
    
    print("\nCurrent environment variables:")
    env_vars = [
        'ENVIRONMENT',
        'AWS_ENVIRONMENT',
        'DEPLOYMENT_STAGE',
        'LOCAL_DEVELOPMENT',
        'DEBUG',
        'STAGING',
        'PRODUCTION'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}={value}")
        else:
            print(f"  {var}=(not set)")


def show_configuration_help() -> None:
    """Show configuration help and examples."""
    print(f"\n{'='*60}")
    print(f"CONFIGURATION HELP")
    print(f"{'='*60}")
    
    print("\nEnvironment Files:")
    print("  config/environments/development.env")
    print("  config/environments/staging.env")
    print("  config/environments/production.env")
    
    print("\nRequired Environment Variables:")
    print("  ENVIRONMENT - Environment name (development/staging/production)")
    print("  GATEWAY_BASE_URL - Gateway endpoint URL")
    print("  AGENT_MODEL - AI model to use")
    print("  AWS_REGION - AWS region")
    
    print("\nOptional Environment Variables (with defaults):")
    print("  GATEWAY_TIMEOUT=30 - Request timeout in seconds")
    print("  GATEWAY_MAX_RETRIES=3 - Maximum retry attempts")
    print("  GATEWAY_AUTH_REQUIRED=true - Whether authentication is required")
    print("  AGENT_TEMPERATURE=0.1 - Model temperature")
    print("  AGENT_MAX_TOKENS=2048 - Maximum tokens")
    print("  AGENT_TIMEOUT=60 - Agent timeout in seconds")
    
    print("\nExample usage:")
    print("  export ENVIRONMENT=development")
    print("  python validate_config.py")
    print("  python validate_config.py --environment production")
    print("  python validate_config.py --test-all")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate MBTI Travel Planner Agent configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--environment', '-e',
        help='Environment to validate (development/staging/production)'
    )
    
    parser.add_argument(
        '--config-dir', '-c',
        help='Directory containing environment files'
    )
    
    parser.add_argument(
        '--test-all', '-a',
        action='store_true',
        help='Test all environments'
    )
    
    parser.add_argument(
        '--check-env-vars', '-v',
        action='store_true',
        help='Check current environment variables'
    )
    
    parser.add_argument(
        '--show-detection', '-d',
        action='store_true',
        help='Show environment detection process'
    )
    
    parser.add_argument(
        '--help-config',
        action='store_true',
        help='Show configuration help'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = True
    
    try:
        if args.help_config:
            show_configuration_help()
        elif args.show_detection:
            show_environment_detection()
        elif args.check_env_vars:
            success = validate_environment_variables()
        elif args.test_all:
            results = test_all_environments(args.config_dir)
            success = all(results.values())
            
            print(f"\n{'='*60}")
            print(f"OVERALL RESULTS")
            print(f"{'='*60}")
            for env, result in results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{env}: {status}")
        else:
            success = validate_environment_config(args.environment, args.config_dir)
        
        if success:
            print(f"\n🎉 All validations PASSED!")
            sys.exit(0)
        else:
            print(f"\n💥 Some validations FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()