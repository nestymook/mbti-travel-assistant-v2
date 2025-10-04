"""
AgentCore Deployment Script for MBTI Travel Planner Agent

This script handles the deployment of the MBTI Travel Assistant to Amazon Bedrock AgentCore,
including container building, authentication setup, runtime configuration, and environment-specific
deployment configurations.

Features:
- Environment-specific deployment (development, staging, production)
- ECR repository management and ARM64 container building
- AgentCore runtime deployment with observability
- Configuration validation and deployment verification
"""

import json
import os
import sys
import logging
import subprocess
import base64
import yaml
from typing import Dict, Any, Optional, List
import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Manages environment-specific configuration."""
    
    def __init__(self, environment: str, config_dir: str = "config/environments"):
        """
        Initialize environment configuration.
        
        Args:
            environment: Environment name (development, staging, production)
            config_dir: Directory containing environment configuration files
        """
        self.environment = environment
        self.config_dir = Path(config_dir)
        self.config = self._load_environment_config()
    
    def _load_environment_config(self) -> Dict[str, str]:
        """Load environment-specific configuration from .env file."""
        env_file = self.config_dir / f"{self.environment}.env"
        
        if not env_file.exists():
            raise FileNotFoundError(f"Environment configuration not found: {env_file}")
        
        config = {}
        with open(env_file, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        logger.info(f"Loaded {len(config)} configuration items for {self.environment}")
        return config
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value."""
        return self.config.get(key, default)
    

class AgentCoreDeployer:
    """Handles deployment of MBTI Travel Assistant to AgentCore."""
    
    def __init__(self, region: str = "us-east-1", environment: str = "development"):
        """
        Initialize the deployer.
        
        Args:
            region: AWS region for deployment
            environment: Environment (development, staging, production)
        """
        self.region = region
        self.environment = environment
        self.session = boto3.Session()
        
        # Load environment configuration
        self.env_config = EnvironmentConfig(environment)
        
        # Initialize AWS clients
        try:
            self.sts_client = self.session.client('sts', region_name=region)
            self.ecr_client = self.session.client('ecr', region_name=region)
            self.cloudwatch_client = self.session.client('cloudwatch', region_name=region)
            
            # Verify AWS credentials
            self.account_id = self.sts_client.get_caller_identity()['Account']
            logger.info(f"Deploying to AWS account: {self.account_id} in region: {region}")
            logger.info(f"Environment: {environment}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            sys.exit(1)
    
    def deploy(
        self,
        agent_name: str = "mbti-travel-planner-agent",
        skip_container_build: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy the MBTI Travel Assistant to AgentCore.
        
        Args:
            agent_name: Name for the AgentCore runtime
            skip_container_build: Skip container building step
            validate_only: Only validate configuration without deploying
            
        Returns:
            Deployment result dictionary
        """
        logger.info(f"Starting deployment of {agent_name} to {self.environment}")
        
        deployment_config = {
            "agent_name": agent_name,
            "environment": self.environment,
            "timestamp": datetime.datetime.now(datetime.UTC),
            "region": self.region,
            "account_id": self.account_id,
        }
        
        try:
            # Step 1: Validate configuration
            self._validate_configuration()
            deployment_config["configuration_valid"] = True
            
            if validate_only:
                logger.info("Configuration validation completed successfully")
                deployment_config["status"] = "validated"
                self._save_deployment_config(deployment_config)
                return deployment_config
            
            # Step 2: Create or verify ECR repository
            ecr_uri = self._setup_ecr_repository(agent_name)
            deployment_config["ecr_repository"] = ecr_uri
            
            # Step 3: Build and push container (if not skipped)
            if not skip_container_build:
                container_uri = self._build_and_push_container(agent_name, ecr_uri)
                deployment_config["container_uri"] = container_uri
            else:
                container_uri = f"{ecr_uri}:latest"
                deployment_config["container_uri"] = container_uri
                logger.info(f"Skipping container build, using: {container_uri}")
            
            # Step 5: Create AgentCore configuration
            agentcore_config = self._create_agentcore_config(
                agent_name,
                container_uri,
            )
            deployment_config["agentcore_config"] = agentcore_config
            
            # Step 6: Deploy to AgentCore
            agent_arn = self._deploy_to_agentcore(agentcore_config)
            deployment_config["agent_arn"] = agent_arn
            
            # Step 7: Setup monitoring and observability
            self._setup_monitoring(agent_name, agent_arn)
            deployment_config["monitoring_configured"] = True
            
            # Step 8: Verify deployment
            self._verify_deployment(agent_arn)
            deployment_config["status"] = "success"
            
            logger.info(f"Successfully deployed {agent_name}")
            logger.info(f"Agent ARN: {agent_arn}")
            
            # Save deployment configuration
            self._save_deployment_config(deployment_config)
            
            return deployment_config
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            deployment_config["status"] = "failed"
            deployment_config["error"] = str(e)
            self._save_deployment_config(deployment_config)
            raise
    
    def _validate_configuration(self) -> None:
        """Validate deployment configuration and prerequisites."""
        logger.info("Validating deployment configuration...")
        
        # Check required environment variables
        required_vars = [
            "AGENT_MODEL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not self.env_config.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        # Check Docker availability
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Docker is not available. Please install Docker.")
        
        # Validate AgentCore configuration file
        agentcore_config_file = Path(".bedrock_agentcore.yaml")
        if not agentcore_config_file.exists():
            raise FileNotFoundError("AgentCore configuration file not found: .bedrock_agentcore.yaml")
        
        try:
            with open(agentcore_config_file, 'r', encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid AgentCore configuration YAML: {e}")
        
        logger.info("Configuration validation completed successfully")
    
    def _setup_ecr_repository(self, agent_name: str) -> str:
        """Create or verify ECR repository for container images."""
        repository_name = agent_name.lower()
        
        try:
            # Check if repository exists
            response = self.ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            repository_uri = response['repositories'][0]['repositoryUri']
            logger.info(f"Using existing ECR repository: {repository_uri}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                # Create new repository
                logger.info(f"Creating ECR repository: {repository_name}")
                response = self.ecr_client.create_repository(
                    repositoryName=repository_name,
                    imageScanningConfiguration={'scanOnPush': True}
                )
                repository_uri = response['repository']['repositoryUri']
                logger.info(f"Created ECR repository: {repository_uri}")
            else:
                raise
        
        return repository_uri
    
    def _build_and_push_container(self, agent_name: str, ecr_uri: str) -> str:
        """Build ARM64 container and push to ECR."""
        logger.info("Building ARM64 container for AgentCore")
        
        # Get ECR login token
        token_response = self.ecr_client.get_authorization_token()
        token = token_response['authorizationData'][0]['authorizationToken']
        endpoint = token_response['authorizationData'][0]['proxyEndpoint']
        
        # Decode token and login to ECR
        username, password = base64.b64decode(token).decode().split(':')
        
        try:
            # Docker login
            subprocess.run([
                'docker', 'login', '--username', username, '--password-stdin', endpoint
            ], input=password.encode(), check=True, capture_output=True)
            
            # Build ARM64 container with environment-specific tag
            image_tag = f"{ecr_uri}:{self.environment}-latest"
            build_args = [
                'docker', 'build', 
                '--platform', 'linux/arm64',
                '--build-arg', f'ENVIRONMENT={self.environment}',
                '--build-arg', f'AWS_REGION={self.region}',
                '-t', image_tag,
                '.'
            ]
            
            logger.info(f"Building container with tag: {image_tag}")
            result = subprocess.run(build_args, check=True, capture_output=True, text=True)
            logger.debug(f"Docker build output: {result.stdout}")
            
            # Also tag as latest for the environment
            latest_tag = f"{ecr_uri}:latest"
            subprocess.run(['docker', 'tag', image_tag, latest_tag], check=True)
            
            # Push both tags
            subprocess.run(['docker', 'push', image_tag], check=True)
            subprocess.run(['docker', 'push', latest_tag], check=True)
            
            logger.info(f"Successfully pushed container: {image_tag}")
            return image_tag
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Container build/push failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"Error details: {e.stderr}")
            raise
    
    def _setup_monitoring(self, agent_name: str, agent_arn: str) -> None:
        """Setup CloudWatch monitoring and observability."""
        logger.info("Setting up monitoring and observability...")
        
        try:
            # Create CloudWatch dashboard
            dashboard_name = f"{agent_name}-{self.environment}-dashboard"
            
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "properties": {
                            "metrics": [
                                ["AWS/BedrockAgentCore", "Invocations", "AgentName", agent_name],
                                [".", "Errors", ".", "."],
                                [".", "Duration", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": f"{agent_name} Metrics"
                        }
                    },
                    {
                        "type": "log",
                        "properties": {
                            "query": f"SOURCE '/aws/bedrock-agentcore/{agent_name}'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 100",
                            "region": self.region,
                            "title": f"{agent_name} Logs"
                        }
                    }
                ]
            }
            
            self.cloudwatch_client.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            logger.info(f"Created CloudWatch dashboard: {dashboard_name}")
            
            # Create CloudWatch alarms
            self._create_cloudwatch_alarms(agent_name)
            
        except Exception as e:
            logger.warning(f"Failed to setup monitoring: {e}")
    
    def _create_cloudwatch_alarms(self, agent_name: str) -> None:
        """Create CloudWatch alarms for monitoring."""
        alarms = [
            {
                "AlarmName": f"{agent_name}-{self.environment}-high-error-rate",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "Errors",
                "Namespace": "AWS/BedrockAgentCore",
                "Period": 300,
                "Statistic": "Sum",
                "Threshold": 10.0,
                "ActionsEnabled": True,
                "AlarmDescription": f"High error rate for {agent_name}",
                "Dimensions": [
                    {
                        "Name": "AgentName",
                        "Value": agent_name
                    }
                ],
                "Unit": "Count"
            },
            {
                "AlarmName": f"{agent_name}-{self.environment}-high-duration",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "Duration",
                "Namespace": "AWS/BedrockAgentCore",
                "Period": 300,
                "Statistic": "Average",
                "Threshold": 30000.0,  # 30 seconds
                "ActionsEnabled": True,
                "AlarmDescription": f"High response time for {agent_name}",
                "Dimensions": [
                    {
                        "Name": "AgentName",
                        "Value": agent_name
                    }
                ],
                "Unit": "Milliseconds"
            }
        ]
        
        for alarm in alarms:
            try:
                self.cloudwatch_client.put_metric_alarm(**alarm)
                logger.info(f"Created CloudWatch alarm: {alarm['AlarmName']}")
            except Exception as e:
                logger.warning(f"Failed to create alarm {alarm['AlarmName']}: {e}")
    
    def _create_agentcore_config(
        self,
        agent_name: str,
        container_uri: str
    ) -> Dict[str, Any]:
        """Create AgentCore deployment configuration with environment-specific settings."""
                
        # Base configuration
        config = {
            "name": f"{agent_name}-{self.environment}",
            "container_uri": container_uri,
            "platform": "linux/arm64",
            "network_mode": "PUBLIC",
            "authentication": {
                "type": "jwt",
                "config": {
                    "customJWTAuthorizer": {
                        "allowedClients": []
                    }
                }
            },
            "environment": {
                "AWS_REGION": self.region,
                "AWS_DEFAULT_REGION": self.region,
                "ENVIRONMENT": self.environment,
                "DOCKER_CONTAINER": "1"
            },
            "observability": {
                "enabled": True,
                "tracing": True,
                "metrics": True,
                "logs": True
            }
        }
        
        # Add environment-specific configuration
        env_vars = {
            "AGENT_MODEL": self.env_config.get("AGENT_MODEL"),
            "AGENT_TEMPERATURE": self.env_config.get("AGENT_TEMPERATURE", "0.1"),
            "AGENT_MAX_TOKENS": self.env_config.get("AGENT_MAX_TOKENS", "4096"),
        }
        
        # Add non-null environment variables
        for key, value in env_vars.items():
            if value is not None:
                config["environment"][key] = value
        
        # Environment-specific resource configuration
        if self.environment == "production":
            config["resources"] = {
                "cpu": "2 vCPU",
                "memory": "4 GB"
            }
            config["scaling"] = {
                "min_instances": 2,
                "max_instances": 20,
                "target_utilization": 70
            }
        elif self.environment == "staging":
            config["resources"] = {
                "cpu": "1 vCPU",
                "memory": "2 GB"
            }
            config["scaling"] = {
                "min_instances": 1,
                "max_instances": 10,
                "target_utilization": 70
            }
        else:  # development
            config["resources"] = {
                "cpu": "0.5 vCPU",
                "memory": "1 GB"
            }
            config["scaling"] = {
                "min_instances": 1,
                "max_instances": 3,
                "target_utilization": 80
            }
        
        # Health check configuration
        config["health_check"] = {
            "path": "/health",
            "interval": 30,
            "timeout": 5,
            "retries": 3
        }
        
        # Save configuration
        config_filename = f"agentcore_deployment_config_{self.environment}.json"
        with open(config_filename, 'w', encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created AgentCore configuration: {config_filename}")
        return config
    
    def _deploy_to_agentcore(self, config: Dict[str, Any]) -> str:
        """Deploy to AgentCore runtime (placeholder implementation)."""
        """agentcore configure -e my_agent.py --region us-west-2 --agent-name mbti-travel-planner-agent"""
        deploy_args = [
            'agentcore', 'configure', 
            '-e', f'main.py',
            '--region', f'us-east-1',
            '--agent-name', f'mbti-travel-planner-agent'
        ]
        
        # Check Docker availability
        try:
            subprocess.run(deploy_args, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("main.py is not available. Please check.")

        logger.info("Deploying to AgentCore runtime...")
        
        # Placeholder implementation
        # In actual implementation, this would use:
        # from bedrock_agentcore_starter_toolkit import AgentCoreDeployer
        # deployer = AgentCoreDeployer()
        # result = deployer.deploy(config)
        
        # For now, return a mock ARN
        mock_agent_arn = f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:agent/{config['name']}"
        
        logger.info(f"AgentCore deployment completed (mock): {mock_agent_arn}")
        return mock_agent_arn
    
    def _verify_deployment(self, agent_arn: str) -> None:
        """Verify the deployment is successful."""
        # TODO: Implement actual deployment verification
        # This would check the agent status and health
        
        logger.info(f"Verifying deployment: {agent_arn}")
        logger.info("Deployment verification completed (mock)")
    
    def _save_deployment_config(self, config: Dict[str, Any]) -> None:
        """Save deployment configuration to file."""
        filename = f"deployment_execution_summary.json"
        
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Deployment configuration saved to: {filename}")


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Deploy MBTI Travel Assistant to AgentCore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to development environment
  python deploy_agentcore.py --environment development
    
  # Validate configuration only
  python deploy_agentcore.py --environment staging --validate-only
  
  # Skip container build (use existing image)
  python deploy_agentcore.py --environment production --skip-container-build
        """
    )
    
    parser.add_argument('--agent-name', default='mbti_travel_planner_agent',
                       help='Name for the AgentCore runtime')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region for deployment')
    parser.add_argument('--skip-container-build', action='store_true',
                       help='Skip container building step')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate configuration without deploying')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        deployer = AgentCoreDeployer(region=args.region, environment=args.environment)
        
        result = deployer.deploy(
            agent_name=args.agent_name,
            skip_container_build=args.skip_container_build,
            validate_only=args.validate_only
        )
        
        print("\n" + "="*60)
        if args.validate_only:
            print("CONFIGURATION VALIDATION SUCCESSFUL")
        else:
            print("DEPLOYMENT SUCCESSFUL")
        print("="*60)
        print(f"Agent Name: {result['agent_name']}")
        print(f"Environment: {result['environment']}")
        print(f"Region: {result['region']}")
        
        if not args.validate_only:
            print(f"Agent ARN: {result.get('agent_arn', 'N/A')}")
            print(f"Container URI: {result.get('container_uri', 'N/A')}")
        
        print("="*60)
        
        if not args.validate_only:
            print("\nNext steps:")
            print("1. Test the deployed agent using the test scripts")
            print("2. Monitor the agent using CloudWatch dashboard")
            print("3. Check logs for any issues")
        
    except Exception as e:
        print(f"\nDEPLOYMENT FAILED: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()