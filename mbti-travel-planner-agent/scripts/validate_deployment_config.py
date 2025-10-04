#!/usr/bin/env python3
"""
Deployment Configuration Validation Script

This script validates the deployment configuration for the MBTI Travel Planner Agent
with HTTP Gateway Integration. It checks environment variables, configuration files,
and gateway connectivity.

Usage:
    python scripts/validate_deployment_config.py [environment]

Examples:
    python scripts/validate_deployment_config.py development
    python scripts/validate_deployment_config.py production
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import httpx
    from config.gateway_config import get_gateway_config, GatewayConfig
    from config.environment_loader import load_environment_config
    from services.gateway_http_client import GatewayHTTPClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates deployment configuration for the MBTI Travel Planner Agent."""
    
    def __init__(self, environment: str = None):
        """Initialize the configuration validator.
        
        Args:
            environment: Target environment (development, staging, production)
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config: Optional[GatewayConfig] = None
        
    def validate_all(self) -> bool:
        """Run all validation checks.
        
        Returns:
            True if all validations pass, False otherwise
        """
        logger.info(f"Validating configuration for {self.environment} environment...")
        
        # Run all validation checks
        self.validate_environment()
        self.validate_required_files()
        self.validate_environment_variables()
        self.validate_gateway_config()
        
        # Run async validations
        asyncio.run(self.validate_gateway_connectivity())
        
        # Report results
        self.report_results()
        
        return len(self.errors) == 0
    
    def validate_environment(self):
        """Validate the environment setting."""
        valid_environments = ['development', 'staging', 'production']
        
        if self.environment not in valid_environments:
            self.errors.append(f"Invalid environment '{self.environment}'. Must be one of: {valid_environments}")
        else:
            logger.info(f"✓ Environment '{self.environment}' is valid")
    
    def validate_required_files(self):
        """Validate that required configuration files exist."""
        required_files = [
            'config/environments/gateway.json',
            f'config/environments/{self.environment}.env',
            'requirements.txt',
            '.bedrock_agentcore.yaml'
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                self.errors.append(f"Required file missing: {file_path}")
            else:
                logger.info(f"✓ Found required file: {file_path}")
    
    def validate_environment_variables(self):
        """Validate environment variables."""
        # Load environment configuration
        try:
            load_environment_config(self.environment)
            logger.info("✓ Environment configuration loaded successfully")
        except Exception as e:
            self.errors.append(f"Failed to load environment configuration: {e}")
            return
        
        # Check required variables
        required_vars = ['AWS_REGION']
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Required environment variable missing: {var}")
            else:
                logger.info(f"✓ Found required variable: {var}")
        
        # Check model configuration
        model = os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')
        if not model.startswith('amazon.nova-pro'):
            self.warnings.append(f"Agent model '{model}' is not Nova Pro. Consider using amazon.nova-pro-v1:0")
        else:
            logger.info(f"✓ Using Nova Pro model: {model}")
        
        # Validate numeric configurations
        numeric_configs = {
            'GATEWAY_TIMEOUT': (1, 300),
            'GATEWAY_MAX_RETRIES': (0, 10),
            'AGENT_MAX_TOKENS': (100, 8192),
            'AGENT_TIMEOUT': (10, 3600),
            'HEALTH_CHECK_INTERVAL': (60, 3600)
        }
        
        for var, (min_val, max_val) in numeric_configs.items():
            value = os.getenv(var)
            if value:
                try:
                    num_value = int(value)
                    if not (min_val <= num_value <= max_val):
                        self.warnings.append(f"{var}={num_value} is outside recommended range [{min_val}, {max_val}]")
                    else:
                        logger.info(f"✓ {var}={num_value} is within valid range")
                except ValueError:
                    self.errors.append(f"{var}='{value}' is not a valid integer")
        
        # Check authentication configuration
        auth_required = os.getenv('GATEWAY_AUTH_REQUIRED', 'false').lower() == 'true'
        auth_token = os.getenv('GATEWAY_AUTH_TOKEN')
        
        if auth_required and not auth_token:
            if self.environment in ['staging', 'production']:
                self.errors.append("GATEWAY_AUTH_TOKEN is required when GATEWAY_AUTH_REQUIRED=true")
            else:
                self.warnings.append("GATEWAY_AUTH_TOKEN not set but authentication is required")
        elif auth_required and auth_token:
            logger.info("✓ Gateway authentication is properly configured")
    
    def validate_gateway_config(self):
        """Validate gateway configuration."""
        try:
            self.config = get_gateway_config(self.environment)
            logger.info(f"✓ Gateway configuration loaded for {self.environment}")
            logger.info(f"  Base URL: {self.config.base_url}")
            logger.info(f"  Timeout: {self.config.timeout}s")
            logger.info(f"  Max Retries: {self.config.max_retries}")
            logger.info(f"  Auth Required: {self.config.auth_required}")
        except Exception as e:
            self.errors.append(f"Failed to load gateway configuration: {e}")
            return
        
        # Validate URL format
        if not self.config.base_url.startswith(('http://', 'https://')):
            self.errors.append(f"Invalid gateway URL format: {self.config.base_url}")
        
        # Check HTTPS for production
        if self.environment == 'production' and not self.config.base_url.startswith('https://'):
            self.errors.append("Production environment must use HTTPS gateway URL")
        
        # Validate timeout values
        if self.config.timeout < 10:
            self.warnings.append(f"Gateway timeout ({self.config.timeout}s) is very low")
        elif self.config.timeout > 120:
            self.warnings.append(f"Gateway timeout ({self.config.timeout}s) is very high")
    
    async def validate_gateway_connectivity(self):
        """Validate connectivity to the gateway service."""
        if not self.config:
            self.errors.append("Cannot test connectivity: gateway configuration not loaded")
            return
        
        try:
            # Create HTTP client for testing
            auth_token = os.getenv('GATEWAY_AUTH_TOKEN') if self.config.auth_required else None
            
            client = GatewayHTTPClient(
                environment=self.environment,
                base_url=self.config.base_url,
                timeout=min(self.config.timeout, 30),  # Use shorter timeout for validation
                auth_token=auth_token
            )
            
            # Test health endpoint
            try:
                health_response = await client.check_health()
                if health_response.get('status') == 'healthy':
                    logger.info("✓ Gateway health check passed")
                else:
                    self.warnings.append(f"Gateway health check returned: {health_response}")
            except Exception as e:
                self.warnings.append(f"Gateway health check failed: {e}")
            
            # Test basic connectivity (without authentication if not required)
            if not self.config.auth_required:
                try:
                    # Try to get tool metadata (should work without auth)
                    async with httpx.AsyncClient(timeout=10) as http_client:
                        response = await http_client.get(f"{self.config.base_url}/api/v1/tools/metadata")
                        if response.status_code == 200:
                            logger.info("✓ Gateway API endpoints are accessible")
                        else:
                            self.warnings.append(f"Gateway API returned status {response.status_code}")
                except Exception as e:
                    self.warnings.append(f"Gateway API connectivity test failed: {e}")
            
        except Exception as e:
            self.errors.append(f"Failed to create gateway client for testing: {e}")
    
    def report_results(self):
        """Report validation results."""
        print("\n" + "="*60)
        print(f"CONFIGURATION VALIDATION RESULTS - {self.environment.upper()}")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed! Configuration is ready for deployment.")
        else:
            if self.errors:
                print(f"\n❌ ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
        
        print("\n" + "="*60)
        
        if self.errors:
            print("❌ Configuration validation FAILED. Please fix the errors above.")
            return False
        elif self.warnings:
            print("⚠️  Configuration validation passed with warnings. Review warnings above.")
            return True
        else:
            print("✅ Configuration validation PASSED. Ready for deployment!")
            return True

def main():
    """Main function."""
    # Parse command line arguments
    environment = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Create and run validator
    validator = ConfigValidator(environment)
    success = validator.validate_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()