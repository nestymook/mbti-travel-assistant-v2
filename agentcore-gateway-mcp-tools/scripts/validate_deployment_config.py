#!/usr/bin/env python3
"""
Deployment Configuration Validation Script

This script validates the AgentCore Gateway deployment configuration
to ensure all required files and settings are properly configured.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List


def validate_agentcore_config() -> List[str]:
    """Validate .bedrock_agentcore.yaml configuration."""
    errors = []
    config_file = Path(".bedrock_agentcore.yaml")
    
    if not config_file.exists():
        errors.append("Missing .bedrock_agentcore.yaml configuration file")
        return errors
    
    try:
        with open(config_file, 'r', encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Check required top-level keys
        if 'agents' not in config:
            errors.append("Missing 'agents' section in AgentCore configuration")
            return errors
        
        # Get first agent configuration
        agent_name = list(config['agents'].keys())[0]
        agent_config = config['agents'][agent_name]
        
        # Validate platform
        if agent_config.get('platform') != 'linux/arm64':
            errors.append("Platform must be 'linux/arm64' for AgentCore Runtime")
        
        # Validate entrypoint
        if agent_config.get('entrypoint') != 'main.py':
            errors.append("Entrypoint must be 'main.py'")
        
        # Validate JWT authentication
        if 'authorizer_configuration' not in agent_config:
            errors.append("Missing JWT authentication configuration")
        else:
            auth_config = agent_config['authorizer_configuration']
            if 'customJWTAuthorizer' not in auth_config:
                errors.append("Missing customJWTAuthorizer configuration")
            else:
                jwt_config = auth_config['customJWTAuthorizer']
                if 'discoveryUrl' not in jwt_config:
                    errors.append("Missing discoveryUrl in JWT configuration")
                if 'allowedClients' not in jwt_config:
                    errors.append("Missing allowedClients in JWT configuration")
                elif not jwt_config['allowedClients']:
                    errors.append("allowedClients list is empty")
        
        # Validate environment variables
        if 'environment_variables' not in agent_config:
            errors.append("Missing environment_variables configuration")
        else:
            env_vars = agent_config['environment_variables']
            required_env_vars = [
                'RESTAURANT_SEARCH_MCP_URL',
                'RESTAURANT_REASONING_MCP_URL',
                'COGNITO_USER_POOL_ID',
                'COGNITO_CLIENT_ID',
                'COGNITO_DISCOVERY_URL'
            ]
            
            for var in required_env_vars:
                if var not in env_vars:
                    errors.append(f"Missing required environment variable: {var}")
        
        print("✓ AgentCore configuration validation passed")
        
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML in AgentCore configuration: {e}")
    except Exception as e:
        errors.append(f"Error reading AgentCore configuration: {e}")
    
    return errors


def validate_cognito_config() -> List[str]:
    """Validate cognito_config.json configuration."""
    errors = []
    config_file = Path("cognito_config.json")
    
    if not config_file.exists():
        errors.append("Missing cognito_config.json configuration file")
        return errors
    
    try:
        with open(config_file, 'r', encoding="utf-8") as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ['user_pool', 'app_client', 'discovery_url']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing '{field}' in Cognito configuration")
        
        # Validate user pool configuration
        if 'user_pool' in config:
            user_pool = config['user_pool']
            if 'user_pool_id' not in user_pool:
                errors.append("Missing 'user_pool_id' in user_pool configuration")
            elif user_pool['user_pool_id'] != 'us-east-1_KePRX24Bn':
                errors.append("Incorrect user_pool_id, should be 'us-east-1_KePRX24Bn'")
        
        # Validate app client configuration
        if 'app_client' in config:
            app_client = config['app_client']
            if 'client_id' not in app_client:
                errors.append("Missing 'client_id' in app_client configuration")
            elif app_client['client_id'] != '1ofgeckef3po4i3us4j1m4chvd':
                errors.append("Incorrect client_id, should be '1ofgeckef3po4i3us4j1m4chvd'")
        
        # Validate discovery URL
        if 'discovery_url' in config:
            expected_url = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration"
            if config['discovery_url'] != expected_url:
                errors.append(f"Incorrect discovery_url, should be '{expected_url}'")
        
        print("✓ Cognito configuration validation passed")
        
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in Cognito configuration: {e}")
    except Exception as e:
        errors.append(f"Error reading Cognito configuration: {e}")
    
    return errors


def validate_dockerfile() -> List[str]:
    """Validate Dockerfile configuration."""
    errors = []
    dockerfile = Path("Dockerfile")
    
    if not dockerfile.exists():
        errors.append("Missing Dockerfile")
        return errors
    
    try:
        with open(dockerfile, 'r', encoding="utf-8") as f:
            content = f.read()
        
        # Check for ARM64 platform
        if '--platform=linux/arm64' not in content:
            errors.append("Dockerfile must specify '--platform=linux/arm64' for AgentCore Runtime")
        
        # Check for required environment variables
        required_env_vars = ['AWS_REGION', 'AWS_DEFAULT_REGION', 'DOCKER_CONTAINER']
        for var in required_env_vars:
            if f'ENV {var}=' not in content:
                errors.append(f"Missing environment variable in Dockerfile: {var}")
        
        # Check for health check
        if 'HEALTHCHECK' not in content:
            errors.append("Missing HEALTHCHECK instruction in Dockerfile")
        
        # Check for non-root user
        if 'USER ' not in content:
            errors.append("Missing USER instruction in Dockerfile (should run as non-root)")
        
        # Check for correct port exposure
        if 'EXPOSE 8080' not in content:
            errors.append("Missing or incorrect EXPOSE instruction (should be 8080)")
        
        print("✓ Dockerfile validation passed")
        
    except Exception as e:
        errors.append(f"Error reading Dockerfile: {e}")
    
    return errors


def validate_main_file() -> List[str]:
    """Validate main.py exists."""
    errors = []
    main_file = Path("main.py")
    
    if not main_file.exists():
        errors.append("Missing main.py application file")
    else:
        print("✓ Main application file exists")
    
    return errors


def validate_requirements() -> List[str]:
    """Validate requirements.txt exists."""
    errors = []
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        errors.append("Missing requirements.txt file")
    else:
        print("✓ Requirements file exists")
    
    return errors


def main():
    """Run all validation checks."""
    print("Validating AgentCore Gateway deployment configuration...")
    print("=" * 60)
    
    all_errors = []
    
    # Run all validation checks
    all_errors.extend(validate_agentcore_config())
    all_errors.extend(validate_cognito_config())
    all_errors.extend(validate_dockerfile())
    all_errors.extend(validate_main_file())
    all_errors.extend(validate_requirements())
    
    print("=" * 60)
    
    if all_errors:
        print("❌ VALIDATION FAILED")
        print("\nErrors found:")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
        print(f"\nTotal errors: {len(all_errors)}")
        sys.exit(1)
    else:
        print("✅ ALL VALIDATION CHECKS PASSED")
        print("\nDeployment configuration is valid and ready for deployment.")
        print("\nNext steps:")
        print("1. Run: python scripts/deploy_agentcore.py --validate-only")
        print("2. Run: python scripts/deploy_agentcore.py")
        sys.exit(0)


if __name__ == "__main__":
    main()