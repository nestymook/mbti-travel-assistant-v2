"""
AgentCore Configuration Validation Utility

This module provides utilities for validating AgentCore configuration
and environment setup.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.agentcore_environment_config import (
    get_agentcore_config_manager,
    validate_agentcore_environment,
    EnvironmentConfig
)

logger = logging.getLogger(__name__)


class AgentCoreConfigValidator:
    """Validates AgentCore configuration and environment setup."""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize validator.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__))
        self.config_manager = get_agentcore_config_manager(config_dir)
    
    def validate_environment_files(self) -> Dict[str, List[str]]:
        """
        Validate that environment files exist and are readable.
        
        Returns:
            Dictionary mapping environment names to list of issues
        """
        results = {}
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            issues = []
            
            # Check for environment file
            env_file_paths = [
                os.path.join(self.config_dir, "environments", f"agentcore_{env}.env"),
                os.path.join(self.config_dir, "environments", f"{env}.env"),
                f".env.agentcore.{env}",
                f".env.{env}",
                f"agentcore_{env}.env",
                f"{env}.env"
            ]
            
            file_found = False
            for env_file in env_file_paths:
                if os.path.exists(env_file):
                    file_found = True
                    
                    # Check if file is readable
                    try:
                        with open(env_file, 'r') as f:
                            content = f.read()
                            if not content.strip():
                                issues.append(f"Environment file is empty: {env_file}")
                    except Exception as e:
                        issues.append(f"Cannot read environment file {env_file}: {str(e)}")
                    
                    break
            
            if not file_found:
                issues.append(f"No environment file found for {env}")
            
            results[env] = issues
        
        return results
    
    def validate_configuration_for_environment(self, environment: str) -> List[str]:
        """
        Validate configuration for a specific environment.
        
        Args:
            environment: Environment name
            
        Returns:
            List of validation issues
        """
        issues = []
        
        try:
            # Load configuration
            config = self.config_manager.load_config(environment)
            
            # Validate configuration
            config_issues = self.config_manager.validate_configuration(config)
            issues.extend(config_issues)
            
            # Additional validation
            issues.extend(self._validate_agent_arns(config))
            issues.extend(self._validate_cognito_config(config))
            issues.extend(self._validate_performance_config(config))
            
        except Exception as e:
            issues.append(f"Failed to load configuration: {str(e)}")
        
        return issues
    
    def _validate_agent_arns(self, config: EnvironmentConfig) -> List[str]:
        """Validate agent ARNs."""
        issues = []
        
        # Check ARN format
        search_arn = config.agentcore.restaurant_search_agent_arn
        reasoning_arn = config.agentcore.restaurant_reasoning_agent_arn
        
        if not self._is_valid_agentcore_arn(search_arn):
            issues.append(f"Invalid restaurant search agent ARN format: {search_arn}")
        
        if not self._is_valid_agentcore_arn(reasoning_arn):
            issues.append(f"Invalid restaurant reasoning agent ARN format: {reasoning_arn}")
        
        # Check if ARNs are different
        if search_arn == reasoning_arn:
            issues.append("Restaurant search and reasoning agent ARNs should be different")
        
        return issues
    
    def _validate_cognito_config(self, config: EnvironmentConfig) -> List[str]:
        """Validate Cognito configuration."""
        issues = []
        
        cognito = config.cognito
        
        # Check user pool ID format
        if not cognito.user_pool_id.startswith('us-east-1_'):
            issues.append(f"User pool ID should start with region prefix: {cognito.user_pool_id}")
        
        # Check client ID length (should be 26 characters)
        if len(cognito.client_id) != 26:
            issues.append(f"Client ID should be 26 characters long, got {len(cognito.client_id)}")
        
        # Check client secret length (should be 51 characters)
        if len(cognito.client_secret) != 51:
            issues.append(f"Client secret should be 51 characters long, got {len(cognito.client_secret)}")
        
        # Check discovery URL format
        if cognito.discovery_url:
            if not cognito.discovery_url.endswith('/.well-known/openid-configuration'):
                issues.append("Discovery URL should end with /.well-known/openid-configuration")
            
            if 'cognito-idp' not in cognito.discovery_url:
                issues.append("Discovery URL should use cognito-idp domain")
        
        return issues
    
    def _validate_performance_config(self, config: EnvironmentConfig) -> List[str]:
        """Validate performance configuration."""
        issues = []
        
        perf = config.performance
        
        # Check reasonable cache TTL
        if perf.cache_ttl_seconds > 3600:  # 1 hour
            issues.append(f"Cache TTL seems too high: {perf.cache_ttl_seconds} seconds")
        
        # Check connection pool settings
        if perf.max_connections > 200:
            issues.append(f"Max connections seems too high: {perf.max_connections}")
        
        if perf.max_connections_per_host > perf.max_connections // 2:
            issues.append("Max connections per host should be less than half of total max connections")
        
        return issues
    
    def _is_valid_agentcore_arn(self, arn: str) -> bool:
        """Validate AgentCore ARN format."""
        try:
            parts = arn.split(':')
            return (
                len(parts) >= 6 and
                parts[0] == 'arn' and
                parts[1] == 'aws' and
                parts[2] == 'bedrock-agentcore' and
                parts[3] == 'us-east-1' and
                parts[4] == '209803798463' and
                parts[5].startswith('runtime/')
            )
        except Exception:
            return False
    
    def validate_all_environments(self) -> Dict[str, Any]:
        """
        Validate all environments and return comprehensive report.
        
        Returns:
            Dictionary with validation results
        """
        report = {
            "environment_files": self.validate_environment_files(),
            "environment_variables": validate_agentcore_environment(),
            "configurations": {}
        }
        
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            report["configurations"][env] = self.validate_configuration_for_environment(env)
        
        return report
    
    def print_validation_report(self, report: Dict[str, Any] = None) -> None:
        """Print a formatted validation report."""
        if report is None:
            report = self.validate_all_environments()
        
        print("=" * 60)
        print("AgentCore Configuration Validation Report")
        print("=" * 60)
        
        # Environment files
        print("\n📁 Environment Files:")
        for env, issues in report["environment_files"].items():
            if issues:
                print(f"  ❌ {env}: {', '.join(issues)}")
            else:
                print(f"  ✅ {env}: OK")
        
        # Environment variables
        print("\n🔧 Environment Variables:")
        if report["environment_variables"]:
            for issue in report["environment_variables"]:
                print(f"  ❌ {issue}")
        else:
            print("  ✅ All environment variables valid")
        
        # Configuration validation
        print("\n⚙️  Configuration Validation:")
        for env, issues in report["configurations"].items():
            if issues:
                print(f"  ❌ {env}:")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print(f"  ✅ {env}: OK")
        
        # Summary
        total_issues = (
            sum(len(issues) for issues in report["environment_files"].values()) +
            len(report["environment_variables"]) +
            sum(len(issues) for issues in report["configurations"].values())
        )
        
        print(f"\n📊 Summary:")
        if total_issues == 0:
            print("  🎉 All validations passed!")
        else:
            print(f"  ⚠️  Found {total_issues} issue(s) that need attention")
        
        print("=" * 60)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate AgentCore configuration")
    parser.add_argument(
        "--environment", 
        choices=['development', 'staging', 'production'],
        help="Validate specific environment only"
    )
    parser.add_argument(
        "--config-dir",
        help="Configuration directory path"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    
    # Create validator
    validator = AgentCoreConfigValidator(args.config_dir)
    
    if args.environment:
        # Validate specific environment
        issues = validator.validate_configuration_for_environment(args.environment)
        
        if issues:
            print(f"❌ {args.environment} configuration issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print(f"✅ {args.environment} configuration is valid")
    else:
        # Validate all environments
        report = validator.validate_all_environments()
        validator.print_validation_report(report)
        
        # Exit with error code if issues found
        total_issues = (
            sum(len(issues) for issues in report["environment_files"].values()) +
            len(report["environment_variables"]) +
            sum(len(issues) for issues in report["configurations"].values())
        )
        
        if total_issues > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()