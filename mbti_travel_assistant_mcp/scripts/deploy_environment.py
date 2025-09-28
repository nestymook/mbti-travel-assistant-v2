#!/usr/bin/env python3
"""
Environment-specific deployment automation script for MBTI Travel Assistant MCP.

This script provides simplified deployment commands for different environments
with pre-configured settings and validation.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentDeployer:
    """Handles environment-specific deployments with pre-configured settings."""
    
    def __init__(self):
        """Initialize the environment deployer."""
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.deploy_script = self.script_dir / "deploy_agentcore.py"
        
        if not self.deploy_script.exists():
            raise FileNotFoundError(f"Deployment script not found: {self.deploy_script}")
    
    def deploy_development(self, **kwargs) -> Dict[str, Any]:
        """Deploy to development environment."""
        logger.info("Deploying to development environment...")
        
        args = [
            sys.executable, str(self.deploy_script),
            "--environment", "development",
            "--region", "us-east-1"
        ]
        
        # Add optional arguments
        if kwargs.get("validate_only"):
            args.append("--validate-only")
        if kwargs.get("skip_container_build"):
            args.append("--skip-container-build")
        if kwargs.get("verbose"):
            args.append("--verbose")
        if kwargs.get("cognito_user_pool_id"):
            args.extend(["--cognito-user-pool-id", kwargs["cognito_user_pool_id"]])
        
        return self._run_deployment(args)
    
    def deploy_staging(self, **kwargs) -> Dict[str, Any]:
        """Deploy to staging environment."""
        logger.info("Deploying to staging environment...")
        
        # Staging requires validation first
        if not kwargs.get("skip_validation"):
            logger.info("Running pre-deployment validation...")
            validation_result = self._validate_environment("staging")
            if not validation_result:
                raise RuntimeError("Staging environment validation failed")
        
        args = [
            sys.executable, str(self.deploy_script),
            "--environment", "staging",
            "--region", "us-east-1"
        ]
        
        # Add optional arguments
        if kwargs.get("validate_only"):
            args.append("--validate-only")
        if kwargs.get("skip_container_build"):
            args.append("--skip-container-build")
        if kwargs.get("verbose"):
            args.append("--verbose")
        if kwargs.get("cognito_user_pool_id"):
            args.extend(["--cognito-user-pool-id", kwargs["cognito_user_pool_id"]])
        
        return self._run_deployment(args)
    
    def deploy_production(self, **kwargs) -> Dict[str, Any]:
        """Deploy to production environment with additional safety checks."""
        logger.info("Deploying to production environment...")
        
        # Production requires explicit confirmation
        if not kwargs.get("force") and not kwargs.get("validate_only"):
            confirmation = input("Are you sure you want to deploy to PRODUCTION? (yes/no): ")
            if confirmation.lower() != "yes":
                logger.info("Production deployment cancelled by user")
                return {"status": "cancelled"}
        
        # Production requires validation first
        if not kwargs.get("skip_validation"):
            logger.info("Running pre-deployment validation...")
            validation_result = self._validate_environment("production")
            if not validation_result:
                raise RuntimeError("Production environment validation failed")
        
        args = [
            sys.executable, str(self.deploy_script),
            "--environment", "production",
            "--region", "us-east-1"
        ]
        
        # Add optional arguments
        if kwargs.get("validate_only"):
            args.append("--validate-only")
        if kwargs.get("skip_container_build"):
            args.append("--skip-container-build")
        if kwargs.get("verbose"):
            args.append("--verbose")
        if kwargs.get("cognito_user_pool_id"):
            args.extend(["--cognito-user-pool-id", kwargs["cognito_user_pool_id"]])
        
        return self._run_deployment(args)
    
    def _validate_environment(self, environment: str) -> bool:
        """Validate environment configuration before deployment."""
        try:
            args = [
                sys.executable, str(self.deploy_script),
                "--environment", environment,
                "--validate-only"
            ]
            
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            logger.info(f"Environment validation successful for {environment}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Environment validation failed for {environment}: {e}")
            if e.stderr:
                logger.error(f"Validation error details: {e.stderr}")
            return False
    
    def _run_deployment(self, args: list) -> Dict[str, Any]:
        """Run the deployment script with given arguments."""
        try:
            # Change to project root directory
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            logger.info(f"Running deployment command: {' '.join(args)}")
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            
            logger.info("Deployment completed successfully")
            if result.stdout:
                print(result.stdout)
            
            return {"status": "success", "output": result.stdout}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment failed with exit code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            
            return {
                "status": "failed",
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr
            }
        
        finally:
            os.chdir(original_cwd)
    
    def list_deployments(self) -> Dict[str, Any]:
        """List existing deployments across environments."""
        logger.info("Listing existing deployments...")
        
        deployments = {}
        
        for environment in ["development", "staging", "production"]:
            config_file = self.project_root / f"agentcore_deployment_config_{environment}.json"
            
            if config_file.exists():
                try:
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    deployments[environment] = {
                        "agent_name": config.get("agent_name"),
                        "agent_arn": config.get("agent_arn"),
                        "timestamp": config.get("timestamp"),
                        "status": config.get("status"),
                        "container_uri": config.get("container_uri")
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to read deployment config for {environment}: {e}")
                    deployments[environment] = {"status": "unknown", "error": str(e)}
            else:
                deployments[environment] = {"status": "not_deployed"}
        
        return deployments
    
    def cleanup_environment(self, environment: str) -> Dict[str, Any]:
        """Clean up resources for a specific environment."""
        logger.info(f"Cleaning up {environment} environment...")
        
        # This would implement cleanup logic for:
        # - AgentCore runtime deletion
        # - ECR image cleanup
        # - CloudWatch dashboard/alarm cleanup
        # - Cognito User Pool cleanup (optional)
        
        logger.warning("Cleanup functionality not yet implemented")
        return {"status": "not_implemented"}


def main():
    """Main function for environment deployment automation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Environment-specific deployment automation for MBTI Travel Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to development
  python deploy_environment.py dev
  
  # Deploy to staging with validation
  python deploy_environment.py staging --validate-only
  
  # Deploy to production (requires confirmation)
  python deploy_environment.py prod --force
  
  # List all deployments
  python deploy_environment.py list
        """
    )
    
    parser.add_argument('command', 
                       choices=['dev', 'development', 'staging', 'stage', 'prod', 'production', 'list', 'cleanup'],
                       help='Deployment command')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate configuration without deploying')
    parser.add_argument('--skip-container-build', action='store_true',
                       help='Skip container building step')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip pre-deployment validation')
    parser.add_argument('--force', action='store_true',
                       help='Force deployment without confirmation (production only)')
    parser.add_argument('--cognito-user-pool-id',
                       help='Existing Cognito User Pool ID')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--cleanup-env',
                       choices=['development', 'staging', 'production'],
                       help='Environment to cleanup (for cleanup command)')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        deployer = EnvironmentDeployer()
        
        # Map command aliases
        command_map = {
            'dev': 'development',
            'stage': 'staging',
            'prod': 'production'
        }
        
        command = command_map.get(args.command, args.command)
        
        if command == 'list':
            deployments = deployer.list_deployments()
            
            print("\n" + "="*60)
            print("DEPLOYMENT STATUS")
            print("="*60)
            
            for env, info in deployments.items():
                print(f"\n{env.upper()}:")
                if info.get("status") == "not_deployed":
                    print("  Status: Not deployed")
                elif info.get("status") == "unknown":
                    print(f"  Status: Unknown ({info.get('error', 'N/A')})")
                else:
                    print(f"  Status: {info.get('status', 'N/A')}")
                    print(f"  Agent Name: {info.get('agent_name', 'N/A')}")
                    print(f"  Agent ARN: {info.get('agent_arn', 'N/A')}")
                    print(f"  Timestamp: {info.get('timestamp', 'N/A')}")
            
            print("="*60)
            
        elif command == 'cleanup':
            if not args.cleanup_env:
                print("Error: --cleanup-env is required for cleanup command")
                sys.exit(1)
            
            result = deployer.cleanup_environment(args.cleanup_env)
            print(f"Cleanup result: {result}")
            
        elif command in ['development', 'staging', 'production']:
            # Prepare deployment arguments
            deploy_kwargs = {
                'validate_only': args.validate_only,
                'skip_container_build': args.skip_container_build,
                'skip_validation': args.skip_validation,
                'force': args.force,
                'verbose': args.verbose,
                'cognito_user_pool_id': args.cognito_user_pool_id
            }
            
            # Call appropriate deployment method
            if command == 'development':
                result = deployer.deploy_development(**deploy_kwargs)
            elif command == 'staging':
                result = deployer.deploy_staging(**deploy_kwargs)
            elif command == 'production':
                result = deployer.deploy_production(**deploy_kwargs)
            
            if result.get("status") == "failed":
                sys.exit(1)
            elif result.get("status") == "cancelled":
                print("Deployment cancelled")
                sys.exit(0)
        
    except Exception as e:
        logger.error(f"Deployment automation failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()