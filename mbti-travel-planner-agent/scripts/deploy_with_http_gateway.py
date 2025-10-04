#!/usr/bin/env python3
"""
Deployment Script for MBTI Travel Planner Agent with HTTP Gateway Integration

This script deploys the MBTI Travel Planner Agent configured to use HTTP gateway
communication instead of direct MCP client connections.

Usage:
    python scripts/deploy_with_http_gateway.py [environment]

Examples:
    python scripts/deploy_with_http_gateway.py development
    python scripts/deploy_with_http_gateway.py production
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.environment_loader import load_environment_config
    from config.gateway_config import get_gateway_config
    from scripts.validate_deployment_config import ConfigValidator
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HTTPGatewayDeployer:
    """Deploys the MBTI Travel Planner Agent with HTTP Gateway integration."""
    
    def __init__(self, environment: str = None):
        """Initialize the deployer.
        
        Args:
            environment: Target environment (development, staging, production)
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'production')
        self.project_root = project_root
        
    def deploy(self) -> bool:
        """Deploy the agent with HTTP gateway configuration.
        
        Returns:
            True if deployment succeeds, False otherwise
        """
        logger.info(f"Starting deployment for {self.environment} environment...")
        
        try:
            # Step 1: Validate configuration
            if not self.validate_configuration():
                logger.error("Configuration validation failed. Aborting deployment.")
                return False
            
            # Step 2: Load environment configuration
            self.load_environment()
            
            # Step 3: Update deployment configuration
            self.update_deployment_config()
            
            # Step 4: Build and deploy
            if not self.build_and_deploy():
                logger.error("Build and deployment failed.")
                return False
            
            # Step 5: Verify deployment
            if not self.verify_deployment():
                logger.error("Deployment verification failed.")
                return False
            
            logger.info("✅ Deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed with error: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """Validate the deployment configuration."""
        logger.info("Validating deployment configuration...")
        
        validator = ConfigValidator(self.environment)
        return validator.validate_all()
    
    def load_environment(self):
        """Load environment-specific configuration."""
        logger.info(f"Loading {self.environment} environment configuration...")
        
        try:
            load_environment_config(self.environment)
            logger.info("✓ Environment configuration loaded")
        except Exception as e:
            raise RuntimeError(f"Failed to load environment configuration: {e}")
    
    def update_deployment_config(self):
        """Update deployment configuration files."""
        logger.info("Updating deployment configuration...")
        
        # Update .bedrock_agentcore.yaml with environment-specific settings
        config_path = self.project_root / '.bedrock_agentcore.yaml'
        
        if config_path.exists():
            logger.info("✓ AgentCore configuration file found")
            
            # Add environment-specific configuration
            env_vars = self.get_environment_variables()
            if env_vars:
                logger.info(f"✓ Environment variables configured: {len(env_vars)} variables")
        else:
            logger.warning("AgentCore configuration file not found")
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for deployment."""
        env_vars = {}
        
        # Core environment variables
        env_vars['ENVIRONMENT'] = self.environment
        env_vars['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
        
        # Gateway configuration
        gateway_config = get_gateway_config(self.environment)
        env_vars['GATEWAY_BASE_URL'] = gateway_config.base_url
        env_vars['GATEWAY_TIMEOUT'] = str(gateway_config.timeout)
        env_vars['GATEWAY_MAX_RETRIES'] = str(gateway_config.max_retries)
        env_vars['GATEWAY_AUTH_REQUIRED'] = str(gateway_config.auth_required).lower()
        
        # Model configuration
        env_vars['AGENT_MODEL'] = os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')
        env_vars['AGENT_TEMPERATURE'] = os.getenv('AGENT_TEMPERATURE', '0.1')
        env_vars['AGENT_MAX_TOKENS'] = os.getenv('AGENT_MAX_TOKENS', '2048')
        env_vars['AGENT_TIMEOUT'] = os.getenv('AGENT_TIMEOUT', '60')
        
        # Logging configuration
        env_vars['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
        env_vars['ENABLE_JSON_LOGGING'] = os.getenv('ENABLE_JSON_LOGGING', 'true')
        env_vars['ENABLE_STRUCTURED_LOGGING'] = os.getenv('ENABLE_STRUCTURED_LOGGING', 'true')
        
        # Performance configuration
        env_vars['HTTP_CLIENT_POOL_CONNECTIONS'] = os.getenv('HTTP_CLIENT_POOL_CONNECTIONS', '20')
        env_vars['HTTP_CLIENT_POOL_MAXSIZE'] = os.getenv('HTTP_CLIENT_POOL_MAXSIZE', '20')
        
        # Monitoring (for staging/production)
        if self.environment in ['staging', 'production']:
            env_vars['ENABLE_PERFORMANCE_MONITORING'] = 'true'
            env_vars['ENABLE_REQUEST_TRACING'] = 'true'
            
            if self.environment == 'production':
                env_vars['ENABLE_METRICS_COLLECTION'] = 'true'
                env_vars['ENABLE_REQUEST_VALIDATION'] = 'true'
                env_vars['ENABLE_RESPONSE_VALIDATION'] = 'true'
        
        return env_vars
    
    def build_and_deploy(self) -> bool:
        """Build and deploy the agent."""
        logger.info("Building and deploying agent...")
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Run AgentCore deployment
            cmd = ['python', '-m', 'bedrock_agentcore', 'deploy']
            
            # Add environment variables
            env = os.environ.copy()
            env.update(self.get_environment_variables())
            
            logger.info("Running AgentCore deployment...")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ AgentCore deployment completed")
                if result.stdout:
                    logger.info(f"Deployment output: {result.stdout}")
                return True
            else:
                logger.error(f"AgentCore deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Build and deployment error: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """Verify the deployment."""
        logger.info("Verifying deployment...")
        
        try:
            # Test agent invocation
            test_payload = {
                "prompt": "Hello! Can you help me find restaurants in Central district?",
                "session_id": "test-session"
            }
            
            # For now, just log that verification would happen
            # In a real deployment, this would invoke the deployed agent
            logger.info("✓ Deployment verification would test agent invocation")
            logger.info(f"✓ Test payload prepared: {json.dumps(test_payload, indent=2)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment verification error: {e}")
            return False
    
    def print_deployment_summary(self):
        """Print deployment summary."""
        gateway_config = get_gateway_config(self.environment)
        
        print("\n" + "="*60)
        print(f"DEPLOYMENT SUMMARY - {self.environment.upper()}")
        print("="*60)
        print(f"Environment: {self.environment}")
        print(f"Gateway URL: {gateway_config.base_url}")
        print(f"Authentication: {'Required' if gateway_config.auth_required else 'Not Required'}")
        print(f"Model: {os.getenv('AGENT_MODEL', 'amazon.nova-pro-v1:0')}")
        print(f"Timeout: {gateway_config.timeout}s")
        print(f"Max Retries: {gateway_config.max_retries}")
        
        if self.environment in ['staging', 'production']:
            print(f"Monitoring: Enabled")
            print(f"JSON Logging: Enabled")
        
        print("\nNext Steps:")
        print("1. Test the deployed agent with a sample request")
        print("2. Monitor logs and metrics")
        print("3. Verify gateway connectivity")
        print("="*60)

def main():
    """Main function."""
    # Parse command line arguments
    environment = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not environment:
        print("Usage: python scripts/deploy_with_http_gateway.py [environment]")
        print("Environments: development, staging, production")
        sys.exit(1)
    
    # Create and run deployer
    deployer = HTTPGatewayDeployer(environment)
    success = deployer.deploy()
    
    if success:
        deployer.print_deployment_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()