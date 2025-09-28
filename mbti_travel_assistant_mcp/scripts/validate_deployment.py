#!/usr/bin/env python3
"""
Deployment validation script for MBTI Travel Assistant MCP.

This script validates deployment configurations, prerequisites, and
deployed agent health across different environments.
"""

import json
import os
import sys
import logging
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validates deployment configurations and deployed agent health."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the deployment validator.
        
        Args:
            region: AWS region for validation
        """
        self.region = region
        self.session = boto3.Session()
        
        try:
            self.sts_client = self.session.client('sts', region_name=region)
            self.ecr_client = self.session.client('ecr', region_name=region)
            self.cognito_client = self.session.client('cognito-idp', region_name=region)
            self.cloudwatch_client = self.session.client('cloudwatch', region_name=region)
            
            self.account_id = self.sts_client.get_caller_identity()['Account']
            logger.info(f"Validating in AWS account: {self.account_id} in region: {region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            sys.exit(1)
    
    def validate_prerequisites(self) -> Dict[str, Any]:
        """Validate deployment prerequisites."""
        logger.info("Validating deployment prerequisites...")
        
        results = {
            "aws_credentials": False,
            "docker": False,
            "bedrock_access": False,
            "agentcore_permissions": False,
            "configuration_files": False,
            "environment_configs": False
        }
        
        # Check AWS credentials
        try:
            self.sts_client.get_caller_identity()
            results["aws_credentials"] = True
            logger.info("✓ AWS credentials valid")
        except Exception as e:
            logger.error(f"✗ AWS credentials invalid: {e}")
        
        # Check Docker
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            results["docker"] = True
            logger.info("✓ Docker available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("✗ Docker not available")
        
        # Check Bedrock access
        try:
            bedrock_client = self.session.client('bedrock', region_name=self.region)
            bedrock_client.list_foundation_models()
            results["bedrock_access"] = True
            logger.info("✓ Bedrock access available")
        except Exception as e:
            logger.error(f"✗ Bedrock access failed: {e}")
        
        # Check AgentCore permissions (placeholder)
        try:
            # This would check actual AgentCore permissions
            # For now, we'll assume they're available if other AWS services work
            results["agentcore_permissions"] = results["aws_credentials"]
            if results["agentcore_permissions"]:
                logger.info("✓ AgentCore permissions assumed available")
            else:
                logger.error("✗ AgentCore permissions not available")
        except Exception as e:
            logger.error(f"✗ AgentCore permissions check failed: {e}")
        
        # Check configuration files
        config_files = [
            ".bedrock_agentcore.yaml",
            "config/environments/development.env",
            "config/environments/staging.env",
            "config/environments/production.env",
            "Dockerfile",
            "requirements.txt"
        ]
        
        missing_files = []
        for file_path in config_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if not missing_files:
            results["configuration_files"] = True
            logger.info("✓ All configuration files present")
        else:
            logger.error(f"✗ Missing configuration files: {missing_files}")
        
        # Validate environment configurations
        env_validation = self._validate_environment_configs()
        results["environment_configs"] = env_validation["valid"]
        
        if env_validation["valid"]:
            logger.info("✓ Environment configurations valid")
        else:
            logger.error(f"✗ Environment configuration errors: {env_validation['errors']}")
        
        return results
    
    def _validate_environment_configs(self) -> Dict[str, Any]:
        """Validate environment configuration files."""
        environments = ["development", "staging", "production"]
        required_vars = [
            "ENVIRONMENT",
            "AWS_REGION",
            "SEARCH_MCP_ENDPOINT",
            "REASONING_MCP_ENDPOINT",
            "AGENT_MODEL"
        ]
        
        errors = []
        valid = True
        
        for env in environments:
            env_file = Path(f"config/environments/{env}.env")
            
            if not env_file.exists():
                errors.append(f"Missing environment file: {env_file}")
                valid = False
                continue
            
            # Parse environment file
            env_vars = {}
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            except Exception as e:
                errors.append(f"Failed to parse {env_file}: {e}")
                valid = False
                continue
            
            # Check required variables
            for var in required_vars:
                if var not in env_vars or not env_vars[var]:
                    errors.append(f"Missing or empty variable {var} in {env}")
                    valid = False
            
            # Validate MCP endpoints
            for endpoint_var in ["SEARCH_MCP_ENDPOINT", "REASONING_MCP_ENDPOINT"]:
                endpoint = env_vars.get(endpoint_var, "")
                if endpoint and not (endpoint.startswith("http://") or endpoint.startswith("https://")):
                    errors.append(f"Invalid URL format for {endpoint_var} in {env}: {endpoint}")
                    valid = False
        
        return {"valid": valid, "errors": errors}
    
    def validate_deployment(self, environment: str) -> Dict[str, Any]:
        """Validate a specific deployment."""
        logger.info(f"Validating {environment} deployment...")
        
        results = {
            "environment": environment,
            "deployment_config": False,
            "ecr_repository": False,
            "container_image": False,
            "cognito_user_pool": False,
            "agent_runtime": False,
            "monitoring": False,
            "health_check": False
        }
        
        # Check deployment configuration
        config_file = Path(f"agentcore_deployment_config_{environment}.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                results["deployment_config"] = True
                results["config"] = config
                logger.info(f"✓ Deployment configuration found for {environment}")
                
                # Validate ECR repository
                if "ecr_repository" in config:
                    ecr_valid = self._validate_ecr_repository(config["ecr_repository"])
                    results["ecr_repository"] = ecr_valid
                
                # Validate container image
                if "container_uri" in config:
                    image_valid = self._validate_container_image(config["container_uri"])
                    results["container_image"] = image_valid
                
                # Validate Cognito User Pool
                if "cognito_user_pool_id" in config:
                    cognito_valid = self._validate_cognito_user_pool(config["cognito_user_pool_id"])
                    results["cognito_user_pool"] = cognito_valid
                elif "cognito_config" in config and "user_pool_id" in config["cognito_config"]:
                    cognito_valid = self._validate_cognito_user_pool(config["cognito_config"]["user_pool_id"])
                    results["cognito_user_pool"] = cognito_valid
                
                # Validate agent runtime (placeholder)
                if "agent_arn" in config:
                    runtime_valid = self._validate_agent_runtime(config["agent_arn"])
                    results["agent_runtime"] = runtime_valid
                
                # Validate monitoring setup
                monitoring_valid = self._validate_monitoring(config.get("agent_name", ""), environment)
                results["monitoring"] = monitoring_valid
                
            except Exception as e:
                logger.error(f"✗ Failed to validate deployment configuration: {e}")
        else:
            logger.error(f"✗ No deployment configuration found for {environment}")
        
        return results
    
    def _validate_ecr_repository(self, ecr_uri: str) -> bool:
        """Validate ECR repository exists."""
        try:
            repository_name = ecr_uri.split('/')[-1].split(':')[0]
            self.ecr_client.describe_repositories(repositoryNames=[repository_name])
            logger.info(f"✓ ECR repository exists: {repository_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                logger.error(f"✗ ECR repository not found: {repository_name}")
            else:
                logger.error(f"✗ ECR repository validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ ECR repository validation error: {e}")
            return False
    
    def _validate_container_image(self, container_uri: str) -> bool:
        """Validate container image exists in ECR."""
        try:
            parts = container_uri.split('/')
            repository_name = parts[-1].split(':')[0]
            tag = parts[-1].split(':')[1] if ':' in parts[-1] else 'latest'
            
            response = self.ecr_client.describe_images(
                repositoryName=repository_name,
                imageIds=[{'imageTag': tag}]
            )
            
            if response['imageDetails']:
                logger.info(f"✓ Container image exists: {container_uri}")
                return True
            else:
                logger.error(f"✗ Container image not found: {container_uri}")
                return False
                
        except ClientError as e:
            logger.error(f"✗ Container image validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Container image validation error: {e}")
            return False
    
    def _validate_cognito_user_pool(self, user_pool_id: str) -> bool:
        """Validate Cognito User Pool exists and is configured."""
        try:
            response = self.cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            
            if response['UserPool']:
                logger.info(f"✓ Cognito User Pool exists: {user_pool_id}")
                
                # Check for clients
                clients = self.cognito_client.list_user_pool_clients(
                    UserPoolId=user_pool_id,
                    MaxResults=10
                )
                
                if clients['UserPoolClients']:
                    logger.info(f"✓ Cognito User Pool has {len(clients['UserPoolClients'])} client(s)")
                    return True
                else:
                    logger.warning(f"⚠ Cognito User Pool has no clients: {user_pool_id}")
                    return False
            else:
                logger.error(f"✗ Cognito User Pool not found: {user_pool_id}")
                return False
                
        except ClientError as e:
            logger.error(f"✗ Cognito User Pool validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Cognito User Pool validation error: {e}")
            return False
    
    def _validate_agent_runtime(self, agent_arn: str) -> bool:
        """Validate AgentCore runtime (placeholder implementation)."""
        # TODO: Implement actual AgentCore runtime validation
        # This would use the AgentCore SDK to check runtime status
        
        logger.info(f"✓ Agent runtime validation (mock): {agent_arn}")
        return True
    
    def _validate_monitoring(self, agent_name: str, environment: str) -> bool:
        """Validate monitoring setup."""
        try:
            dashboard_name = f"{agent_name}-{environment}-dashboard"
            
            # Check CloudWatch dashboard
            try:
                self.cloudwatch_client.get_dashboard(DashboardName=dashboard_name)
                logger.info(f"✓ CloudWatch dashboard exists: {dashboard_name}")
                dashboard_exists = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFound':
                    logger.warning(f"⚠ CloudWatch dashboard not found: {dashboard_name}")
                    dashboard_exists = False
                else:
                    raise
            
            # Check CloudWatch alarms
            alarm_prefix = f"{agent_name}-{environment}-"
            alarms = self.cloudwatch_client.describe_alarms(
                AlarmNamePrefix=alarm_prefix,
                MaxRecords=100
            )
            
            if alarms['MetricAlarms']:
                logger.info(f"✓ Found {len(alarms['MetricAlarms'])} CloudWatch alarms")
                alarms_exist = True
            else:
                logger.warning(f"⚠ No CloudWatch alarms found with prefix: {alarm_prefix}")
                alarms_exist = False
            
            return dashboard_exists or alarms_exist
            
        except Exception as e:
            logger.error(f"✗ Monitoring validation failed: {e}")
            return False
    
    def validate_health_check(self, agent_endpoint: str) -> bool:
        """Validate agent health check endpoint."""
        try:
            health_url = f"{agent_endpoint}/health"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ Health check passed: {health_url}")
                return True
            else:
                logger.error(f"✗ Health check failed: {health_url} (status: {response.status_code})")
                return False
                
        except requests.RequestException as e:
            logger.error(f"✗ Health check request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Health check error: {e}")
            return False
    
    def generate_validation_report(self, validations: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("="*60)
        report.append("DEPLOYMENT VALIDATION REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.utcnow().isoformat()}Z")
        report.append(f"AWS Account: {self.account_id}")
        report.append(f"Region: {self.region}")
        report.append("")
        
        # Prerequisites section
        if "prerequisites" in validations:
            report.append("PREREQUISITES:")
            prereqs = validations["prerequisites"]
            for check, passed in prereqs.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                report.append(f"  {check.replace('_', ' ').title()}: {status}")
            report.append("")
        
        # Environment deployments section
        for env in ["development", "staging", "production"]:
            if env in validations:
                report.append(f"{env.upper()} DEPLOYMENT:")
                deployment = validations[env]
                
                for check, passed in deployment.items():
                    if check in ["environment", "config"]:
                        continue
                    
                    status = "✓ PASS" if passed else "✗ FAIL"
                    report.append(f"  {check.replace('_', ' ').title()}: {status}")
                report.append("")
        
        # Summary section
        report.append("SUMMARY:")
        
        total_checks = 0
        passed_checks = 0
        
        for section, checks in validations.items():
            if isinstance(checks, dict):
                for check, passed in checks.items():
                    if isinstance(passed, bool):
                        total_checks += 1
                        if passed:
                            passed_checks += 1
        
        report.append(f"  Total Checks: {total_checks}")
        report.append(f"  Passed: {passed_checks}")
        report.append(f"  Failed: {total_checks - passed_checks}")
        report.append(f"  Success Rate: {(passed_checks/total_checks*100):.1f}%" if total_checks > 0 else "  Success Rate: N/A")
        
        report.append("="*60)
        
        return "\n".join(report)


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate MBTI Travel Assistant deployment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate prerequisites only
  python validate_deployment.py --prerequisites-only
  
  # Validate specific environment
  python validate_deployment.py --environment staging
  
  # Validate all environments
  python validate_deployment.py --all
  
  # Generate detailed report
  python validate_deployment.py --all --report validation_report.txt
        """
    )
    
    parser.add_argument('--environment', '-e',
                       choices=['development', 'staging', 'production'],
                       help='Validate specific environment')
    parser.add_argument('--all', action='store_true',
                       help='Validate all environments')
    parser.add_argument('--prerequisites-only', action='store_true',
                       help='Only validate prerequisites')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region for validation')
    parser.add_argument('--report', '-r',
                       help='Generate validation report to file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        validator = DeploymentValidator(region=args.region)
        validations = {}
        
        # Validate prerequisites
        validations["prerequisites"] = validator.validate_prerequisites()
        
        if args.prerequisites_only:
            # Only show prerequisites validation
            prereqs = validations["prerequisites"]
            all_passed = all(prereqs.values())
            
            print("\nPrerequisites Validation:")
            for check, passed in prereqs.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {check.replace('_', ' ').title()}: {status}")
            
            if all_passed:
                print("\n✓ All prerequisites validation passed!")
                sys.exit(0)
            else:
                print("\n✗ Some prerequisites validation failed!")
                sys.exit(1)
        
        # Validate specific environment or all environments
        environments_to_validate = []
        
        if args.environment:
            environments_to_validate = [args.environment]
        elif args.all:
            environments_to_validate = ["development", "staging", "production"]
        else:
            # Default to development if no specific environment requested
            environments_to_validate = ["development"]
        
        for env in environments_to_validate:
            validations[env] = validator.validate_deployment(env)
        
        # Generate and display report
        report = validator.generate_validation_report(validations)
        
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"Validation report saved to: {args.report}")
        else:
            print(report)
        
        # Determine exit code based on validation results
        all_passed = True
        for section, checks in validations.items():
            if isinstance(checks, dict):
                for check, passed in checks.items():
                    if isinstance(passed, bool) and not passed:
                        all_passed = False
                        break
        
        if all_passed:
            print("\n✓ All validations passed!")
            sys.exit(0)
        else:
            print("\n✗ Some validations failed!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()