#!/usr/bin/env python3
"""
Configuration initialization script for MBTI Travel Assistant MCP

This script initializes configuration files and validates the setup
for different deployment environments.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigInitializer:
    """Configuration initializer for MBTI Travel Assistant"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.environments_dir = config_dir / "environments"
        
    def initialize_configuration(self) -> bool:
        """Initialize all configuration files and directories
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create directories
            self._create_directories()
            
            # Validate configuration files
            self._validate_config_files()
            
            # Create default .env file if it doesn't exist
            self._create_default_env_file()
            
            # Validate JSON configuration files
            self._validate_json_configs()
            
            logger.info("Configuration initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration initialization failed: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Create necessary configuration directories"""
        directories = [
            self.config_dir,
            self.environments_dir,
            self.config_dir.parent / "logs",
            self.config_dir.parent / "data",
            self.config_dir.parent / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def _validate_config_files(self) -> None:
        """Validate that all required configuration files exist"""
        required_files = [
            self.environments_dir / "development.env",
            self.environments_dir / "staging.env", 
            self.environments_dir / "production.env",
            self.config_dir / "cognito_config.json",
            self.config_dir / "mcp_endpoints.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            raise FileNotFoundError(f"Missing required configuration files: {missing_files}")
        
        logger.info("All required configuration files found")
    
    def _create_default_env_file(self) -> None:
        """Create default .env file if it doesn't exist"""
        env_file = self.config_dir.parent / ".env"
        
        if not env_file.exists():
            default_env_content = """# MBTI Travel Assistant MCP - Default Environment Configuration
# Copy this file and customize for your environment

# Environment (development, staging, production)
ENVIRONMENT=development

# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Debug Settings
DEBUG=true
LOG_LEVEL=INFO

# Override any settings from environment-specific files here
"""
            
            with open(env_file, 'w') as f:
                f.write(default_env_content)
            
            logger.info(f"Created default .env file: {env_file}")
    
    def _validate_json_configs(self) -> None:
        """Validate JSON configuration files"""
        json_files = [
            self.config_dir / "cognito_config.json",
            self.config_dir / "mcp_endpoints.json"
        ]
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    json.load(f)
                logger.debug(f"Validated JSON file: {json_file}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {json_file}: {e}")
            except Exception as e:
                raise Exception(f"Error reading {json_file}: {e}")
        
        logger.info("All JSON configuration files are valid")
    
    def create_environment_template(self, environment: str) -> str:
        """Create environment configuration template
        
        Args:
            environment: Environment name
            
        Returns:
            Environment configuration template content
        """
        template = f"""# {environment.title()} Environment Configuration
# MBTI Travel Assistant MCP - {environment.title()} Settings

# Application Environment
ENVIRONMENT={environment}
AWS_REGION=us-east-1

# MCP Client Configuration
SEARCH_MCP_ENDPOINT=https://{environment}-search-mcp.agentcore.aws
REASONING_MCP_ENDPOINT=https://{environment}-reasoning-mcp.agentcore.aws
MCP_CONNECTION_TIMEOUT=30
MCP_RETRY_ATTEMPTS=3

# Authentication Configuration ({environment.title()})
COGNITO_USER_POOL_ID=us-east-1_{environment}123456
COGNITO_REGION=us-east-1
JWT_ALGORITHM=RS256
JWT_AUDIENCE=mbti-travel-assistant-{environment}
TOKEN_CACHE_TTL=600

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=1800

# AgentCore Runtime Configuration
RUNTIME_PORT=8080
AGENT_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=4096

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
TRACING_ENABLED=true
METRICS_ENABLED=true

# {environment.title()}-specific settings
DEBUG=false
MOCK_MCP_SERVERS=false
"""
        return template
    
    def update_cognito_config(self, environment: str, config_updates: Dict[str, Any]) -> None:
        """Update Cognito configuration for specific environment
        
        Args:
            environment: Environment name
            config_updates: Configuration updates to apply
        """
        cognito_config_file = self.config_dir / "cognito_config.json"
        
        try:
            with open(cognito_config_file, 'r') as f:
                config = json.load(f)
            
            if environment not in config:
                config[environment] = {}
            
            # Apply updates
            config[environment].update(config_updates)
            
            # Write back to file
            with open(cognito_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Updated Cognito configuration for {environment}")
            
        except Exception as e:
            logger.error(f"Failed to update Cognito configuration: {e}")
            raise
    
    def update_mcp_endpoints(self, environment: str, endpoint_updates: Dict[str, Any]) -> None:
        """Update MCP endpoints configuration for specific environment
        
        Args:
            environment: Environment name
            endpoint_updates: Endpoint configuration updates to apply
        """
        mcp_config_file = self.config_dir / "mcp_endpoints.json"
        
        try:
            with open(mcp_config_file, 'r') as f:
                config = json.load(f)
            
            if environment not in config:
                config[environment] = {}
            
            # Apply updates
            config[environment].update(endpoint_updates)
            
            # Write back to file
            with open(mcp_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Updated MCP endpoints configuration for {environment}")
            
        except Exception as e:
            logger.error(f"Failed to update MCP endpoints configuration: {e}")
            raise


def main():
    """Main initialization function"""
    config_dir = Path(__file__).parent
    initializer = ConfigInitializer(config_dir)
    
    print("Initializing MBTI Travel Assistant MCP configuration...")
    
    if initializer.initialize_configuration():
        print("✅ Configuration initialization completed successfully")
        print("\nNext steps:")
        print("1. Review and customize environment-specific .env files")
        print("2. Update Cognito configuration with your User Pool details")
        print("3. Update MCP endpoints with your actual server URLs")
        print("4. Run 'python validate_config.py' to validate your configuration")
        sys.exit(0)
    else:
        print("❌ Configuration initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()