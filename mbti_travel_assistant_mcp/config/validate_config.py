#!/usr/bin/env python3
"""
Configuration validation script for MBTI Travel Assistant MCP

This script validates configuration settings for different environments
and provides detailed feedback on any configuration issues.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

from config_loader import ConfigLoader, ConfigurationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Configuration validator with comprehensive checks"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_environment(self, environment: str) -> bool:
        """Validate configuration for specific environment
        
        Args:
            environment: Environment name to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        logger.info(f"Validating configuration for environment: {environment}")
        
        try:
            settings = self.config_loader.load_environment_config(environment)
            
            # Validate MCP configuration
            self._validate_mcp_config(settings, environment)
            
            # Validate authentication configuration
            self._validate_auth_config(settings, environment)
            
            # Validate AgentCore configuration
            self._validate_agentcore_config(settings, environment)
            
            # Validate cache configuration
            self._validate_cache_config(settings, environment)
            
            # Validate logging configuration
            self._validate_logging_config(settings, environment)
            
            # Report results
            self._report_validation_results(environment)
            
            return len(self.validation_errors) == 0
            
        except ConfigurationError as e:
            logger.error(f"Configuration error for {environment}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating {environment}: {e}")
            return False
    
    def _validate_mcp_config(self, settings: Any, environment: str) -> None:
        """Validate MCP client configuration"""
        mcp_config = settings.mcp_client
        
        # Check required endpoints
        if not mcp_config.search_mcp_endpoint:
            self.validation_errors.append(f"{environment}: SEARCH_MCP_ENDPOINT is required")
        elif not self._is_valid_url(mcp_config.search_mcp_endpoint):
            self.validation_errors.append(f"{environment}: SEARCH_MCP_ENDPOINT is not a valid URL")
        
        if not mcp_config.reasoning_mcp_endpoint:
            self.validation_errors.append(f"{environment}: REASONING_MCP_ENDPOINT is required")
        elif not self._is_valid_url(mcp_config.reasoning_mcp_endpoint):
            self.validation_errors.append(f"{environment}: REASONING_MCP_ENDPOINT is not a valid URL")
        
        # Check timeout values
        if mcp_config.mcp_connection_timeout <= 0:
            self.validation_errors.append(f"{environment}: MCP_CONNECTION_TIMEOUT must be positive")
        elif mcp_config.mcp_connection_timeout < 10:
            self.validation_warnings.append(f"{environment}: MCP_CONNECTION_TIMEOUT is very low ({mcp_config.mcp_connection_timeout}s)")
        
        # Check retry attempts
        if mcp_config.mcp_retry_attempts < 1:
            self.validation_errors.append(f"{environment}: MCP_RETRY_ATTEMPTS must be at least 1")
        elif mcp_config.mcp_retry_attempts > 10:
            self.validation_warnings.append(f"{environment}: MCP_RETRY_ATTEMPTS is very high ({mcp_config.mcp_retry_attempts})")
    
    def _validate_auth_config(self, settings: Any, environment: str) -> None:
        """Validate authentication configuration"""
        auth_config = settings.authentication
        
        # Production environments require full auth config
        if environment == "production":
            if not auth_config.cognito_user_pool_id:
                self.validation_errors.append(f"{environment}: COGNITO_USER_POOL_ID is required for production")
            
            if not auth_config.jwt_audience:
                self.validation_warnings.append(f"{environment}: JWT_AUDIENCE should be set for production")
        
        # Check JWT algorithm
        valid_algorithms = ["RS256", "HS256", "ES256"]
        if auth_config.jwt_algorithm not in valid_algorithms:
            self.validation_errors.append(f"{environment}: JWT_ALGORITHM must be one of {valid_algorithms}")
        
        # Check token cache TTL
        if auth_config.token_cache_ttl <= 0:
            self.validation_errors.append(f"{environment}: TOKEN_CACHE_TTL must be positive")
        elif auth_config.token_cache_ttl < 60:
            self.validation_warnings.append(f"{environment}: TOKEN_CACHE_TTL is very low ({auth_config.token_cache_ttl}s)")
    
    def _validate_agentcore_config(self, settings: Any, environment: str) -> None:
        """Validate AgentCore runtime configuration"""
        agentcore_config = settings.agentcore
        
        # Check port
        if not (1024 <= agentcore_config.runtime_port <= 65535):
            self.validation_errors.append(f"{environment}: RUNTIME_PORT must be between 1024 and 65535")
        
        # Check model
        if not agentcore_config.agent_model:
            self.validation_errors.append(f"{environment}: AGENT_MODEL is required")
        elif not agentcore_config.agent_model.startswith("anthropic."):
            self.validation_warnings.append(f"{environment}: AGENT_MODEL should be an Anthropic model")
        
        # Check temperature
        if not (0.0 <= agentcore_config.agent_temperature <= 2.0):
            self.validation_errors.append(f"{environment}: AGENT_TEMPERATURE must be between 0.0 and 2.0")
        
        # Check max tokens
        if agentcore_config.agent_max_tokens <= 0:
            self.validation_errors.append(f"{environment}: AGENT_MAX_TOKENS must be positive")
        elif agentcore_config.agent_max_tokens > 8192:
            self.validation_warnings.append(f"{environment}: AGENT_MAX_TOKENS is very high ({agentcore_config.agent_max_tokens})")
    
    def _validate_cache_config(self, settings: Any, environment: str) -> None:
        """Validate cache configuration"""
        cache_config = settings.cache
        
        # Check TTL
        if cache_config.cache_ttl <= 0:
            self.validation_errors.append(f"{environment}: CACHE_TTL must be positive")
        elif cache_config.cache_ttl < 60:
            self.validation_warnings.append(f"{environment}: CACHE_TTL is very low ({cache_config.cache_ttl}s)")
        
        # Check Redis URL if provided
        if cache_config.redis_url and not self._is_valid_redis_url(cache_config.redis_url):
            self.validation_errors.append(f"{environment}: REDIS_URL is not valid")
    
    def _validate_logging_config(self, settings: Any, environment: str) -> None:
        """Validate logging configuration"""
        logging_config = settings.logging
        
        # Check log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if logging_config.log_level not in valid_levels:
            self.validation_errors.append(f"{environment}: LOG_LEVEL must be one of {valid_levels}")
        
        # Check log format
        valid_formats = ["json", "text"]
        if logging_config.log_format not in valid_formats:
            self.validation_errors.append(f"{environment}: LOG_FORMAT must be one of {valid_formats}")
        
        # Production should use INFO or higher
        if environment == "production" and logging_config.log_level == "DEBUG":
            self.validation_warnings.append(f"{environment}: DEBUG logging not recommended for production")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        return url.startswith(("http://", "https://")) and len(url) > 10
    
    def _is_valid_redis_url(self, url: str) -> bool:
        """Check if Redis URL is valid"""
        return url.startswith("redis://") and len(url) > 10
    
    def _report_validation_results(self, environment: str) -> None:
        """Report validation results"""
        if self.validation_errors:
            logger.error(f"Validation errors for {environment}:")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
        
        if self.validation_warnings:
            logger.warning(f"Validation warnings for {environment}:")
            for warning in self.validation_warnings:
                logger.warning(f"  - {warning}")
        
        if not self.validation_errors and not self.validation_warnings:
            logger.info(f"Configuration for {environment} is valid")


def main():
    """Main validation function"""
    environments = ["development", "staging", "production"]
    validator = ConfigValidator()
    
    all_valid = True
    
    for env in environments:
        print(f"\n{'='*50}")
        print(f"Validating {env.upper()} environment")
        print(f"{'='*50}")
        
        if not validator.validate_environment(env):
            all_valid = False
        
        # Reset validation state for next environment
        validator.validation_errors.clear()
        validator.validation_warnings.clear()
    
    print(f"\n{'='*50}")
    if all_valid:
        print("✅ All environment configurations are valid")
        sys.exit(0)
    else:
        print("❌ Some environment configurations have errors")
        sys.exit(1)


if __name__ == "__main__":
    main()