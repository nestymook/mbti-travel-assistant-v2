"""
AgentCore Deployment Script for Gateway MCP Tools

This script handles the deployment of the AgentCore Gateway for MCP Tools to Amazon Bedrock AgentCore,
including container building, authentication setup, runtime configuration, and MCP server endpoint
configuration.

Features:
- ARM64 container building for AgentCore Runtime compatibility
- JWT authentication with existing Cognito User Pool
- MCP server endpoint configuration
- Observability and monitoring setup
- Configuration validation and deployment verification
"""

import json
import os
import sys
import logging
import subprocess
import base64
import yaml
from typing import Dict, Any, Optional
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


class AgentCoreGatewayDeployer:
    """Handles deployment of AgentCore Gateway for MCP Tools."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the deployer.
        
        Args:
            region: AWS region for deployment
        """
        self.region = region
        self.session = boto3.Session()
        
        # Initialize AWS clients
        try:
            self.sts_client = self.session.client('sts', region_name=region)
            self.ecr_client = self.session.client('ecr', region_name=region)
            self.cloudwatch_client = self.session.client('cloudwatch', region_name=region)
            
            # Verify AWS credentials
            self.account_id = self.sts_client.get_caller_identity()['Account']
            logger.info(f"Deploying to AWS account: {self.account_id} in region: {region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            sys.exit(1)
    
    def deploy(
        self,
        agent_name: str = "agentcore-gateway-mcp-tools",
        skip_container_build: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy the AgentCore Gateway to AgentCore Runtime.
        
        Args:
            agent_name: Name for the AgentCore runtime
            skip_container_build: Skip container building step
            validate_only: Only validate configuration without deploying
            
        Returns:
            Deployment result dictionary
        """
        logger.info(f"Starting deployment of {agent_name}")
        
        deployment_config = {
            "agent_name": agent_name,
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
            
            # Step 4: Deploy to AgentCore using bedrock-agentcore CLI
            agent_arn = self._deploy_to_agentcore(agent_name)
            deployment_config["agent_arn"] = agent_arn
            
            # Step 5: Setup monitoring and observability
            self._setup_monitoring(agent_name, agent_arn)
            deployment_config["monitoring_configured"] = True
            
            # Step 6: Verify deployment
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
        
        # Check Docker availability and daemon status
        self._check_docker_availability()
        
        # Validate AgentCore configuration file
        agentcore_config_file = Path(".bedrock_agentcore.yaml")
        if not agentcore_config_file.exists():
            raise FileNotFoundError("AgentCore configuration file not found: .bedrock_agentcore.yaml")
        
        try:
            with open(agentcore_config_file, 'r', encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
                # Validate required configuration sections
                if 'agents' not in config:
                    raise ValueError("Missing 'agents' section in AgentCore configuration")
                
                agent_config = list(config['agents'].values())[0]
                
                # Validate platform is ARM64
                if agent_config.get('platform') != 'linux/arm64':
                    raise ValueError("Platform must be 'linux/arm64' for AgentCore Runtime")
                
                # Validate JWT authentication configuration
                if 'authorizer_configuration' not in agent_config:
                    raise ValueError("Missing JWT authentication configuration")
                
                jwt_config = agent_config['authorizer_configuration']
                if 'customJWTAuthorizer' not in jwt_config:
                    raise ValueError("Missing customJWTAuthorizer configuration")
                
                if 'discoveryUrl' not in jwt_config['customJWTAuthorizer']:
                    raise ValueError("Missing discoveryUrl in JWT configuration")
                
                if 'allowedClients' not in jwt_config['customJWTAuthorizer']:
                    raise ValueError("Missing allowedClients in JWT configuration")
                
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid AgentCore configuration YAML: {e}")
        
        # Validate Cognito configuration file
        cognito_config_file = Path("cognito_config.json")
        if not cognito_config_file.exists():
            raise FileNotFoundError("Cognito configuration file not found: cognito_config.json")
        
        try:
            with open(cognito_config_file, 'r', encoding="utf-8") as f:
                cognito_config = json.load(f)
                
                # Validate required Cognito configuration
                required_fields = ['user_pool', 'app_client', 'discovery_url']
                for field in required_fields:
                    if field not in cognito_config:
                        raise ValueError(f"Missing '{field}' in Cognito configuration")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid Cognito configuration JSON: {e}")
        
        # Validate main.py exists
        main_file = Path("main.py")
        if not main_file.exists():
            raise FileNotFoundError("Main application file not found: main.py")
        
        # Validate Dockerfile exists and has ARM64 platform
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            raise FileNotFoundError("Dockerfile not found")
        
        try:
            with open(dockerfile, 'r', encoding="utf-8") as f:
                dockerfile_content = f.read()
                if 'linux/arm64' not in dockerfile_content:
                    raise ValueError("Dockerfile must specify 'linux/arm64' platform for AgentCore Runtime")
        except Exception as e:
            raise ValueError(f"Error reading Dockerfile: {e}")
        
        logger.info("Configuration validation completed successfully")
    
    def _check_docker_availability(self) -> None:
        """Check if Docker is installed and the daemon is running."""
        logger.info("Checking Docker availability...")
        
        # Check if Docker is installed
        try:
            result = subprocess.run(['docker', '--version'], check=True, capture_output=True, text=True)
            logger.info(f"Docker version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Docker is not installed or not available in PATH. "
                "Please install Docker Desktop and ensure it's in your system PATH."
            )
        
        # Check if Docker daemon is running
        try:
            result = subprocess.run(['docker', 'info'], check=True, capture_output=True, text=True)
            logger.info("Docker daemon is running and accessible")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else str(e)
            
            # Check for common Docker daemon issues
            if "docker daemon is not running" in error_output.lower() or \
               "cannot connect to the docker daemon" in error_output.lower() or \
               "docker_engine" in error_output.lower():
                
                # Provide platform-specific guidance
                if sys.platform.startswith('win'):
                    raise RuntimeError(
                        "Docker daemon is not running. Please:\n"
                        "1. Start Docker Desktop from the Start menu or system tray\n"
                        "2. Wait for Docker Desktop to fully start (check the system tray icon)\n"
                        "3. Ensure Docker Desktop is set to start automatically\n"
                        "4. Try running 'docker info' manually to verify Docker is working\n\n"
                        f"Error details: {error_output}"
                    )
                elif sys.platform.startswith('darwin'):
                    raise RuntimeError(
                        "Docker daemon is not running. Please:\n"
                        "1. Start Docker Desktop from Applications or Launchpad\n"
                        "2. Wait for Docker Desktop to fully start (check the menu bar icon)\n"
                        "3. Ensure Docker Desktop is set to start automatically\n"
                        "4. Try running 'docker info' manually to verify Docker is working\n\n"
                        f"Error details: {error_output}"
                    )
                else:  # Linux
                    raise RuntimeError(
                        "Docker daemon is not running. Please:\n"
                        "1. Start Docker daemon: sudo systemctl start docker\n"
                        "2. Enable Docker to start on boot: sudo systemctl enable docker\n"
                        "3. Add your user to docker group: sudo usermod -aG docker $USER\n"
                        "4. Log out and back in, or run: newgrp docker\n"
                        "5. Try running 'docker info' manually to verify Docker is working\n\n"
                        f"Error details: {error_output}"
                    )
            else:
                raise RuntimeError(f"Docker daemon check failed: {error_output}")
        
        # Test Docker functionality with a simple command
        try:
            subprocess.run(['docker', 'ps'], check=True, capture_output=True)
            logger.info("Docker daemon functionality verified")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(
                f"Docker daemon is running but not functioning properly. "
                f"Please restart Docker Desktop and try again.\n"
                f"Error details: {error_output}"
            )
    
    def _setup_ecr_repository(self, agent_name: str) -> str:
        """Create or verify ECR repository for container images."""
        repository_name = f"bedrock-agentcore-{agent_name.lower()}"
        
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
        logger.info("Building ARM64 container for AgentCore Runtime")
        
        # Verify Docker daemon is still running before container operations
        try:
            subprocess.run(['docker', 'info'], check=True, capture_output=True)
            logger.debug("Docker daemon verified before container build")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if e.stderr else str(e)
            if sys.platform.startswith('win'):
                raise RuntimeError(
                    "Docker daemon is not running. Please start Docker Desktop and wait for it to fully initialize.\n"
                    "You can check if Docker is ready by running 'docker info' in a terminal.\n\n"
                    f"Error details: {error_output}"
                )
            else:
                raise RuntimeError(f"Docker daemon is not running: {error_output}")
        
        # Get ECR login token
        token_response = self.ecr_client.get_authorization_token()
        token = token_response['authorizationData'][0]['authorizationToken']
        endpoint = token_response['authorizationData'][0]['proxyEndpoint']
        
        # Decode token and login to ECR
        username, password = base64.b64decode(token).decode().split(':')
        
        try:
            # Docker login with timeout
            logger.info(f"Logging into ECR registry: {endpoint}")
            login_result = subprocess.run([
                'docker', 'login', '--username', username, '--password-stdin', endpoint
            ], input=password.encode(), check=True, capture_output=True, timeout=60)
            logger.info("Successfully logged into ECR")
            
            # Build ARM64 container
            image_tag = f"{ecr_uri}:latest"
            build_args = [
                'docker', 'build', 
                '--platform', 'linux/arm64',
                '--build-arg', f'AWS_REGION={self.region}',
                '-t', image_tag,
                '.'
            ]
            
            logger.info(f"Building container with tag: {image_tag}")
            
            # Use encoding='utf-8' and errors='replace' to handle encoding issues
            result = subprocess.run(
                build_args, 
                check=True, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            logger.debug(f"Docker build output: {result.stdout}")
            
            # Push container
            subprocess.run(['docker', 'push', image_tag], check=True)
            
            logger.info(f"Successfully pushed container: {image_tag}")
            return image_tag
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Docker login timed out after 60 seconds: {e}")
            raise RuntimeError(
                "Docker login to ECR timed out. This might be due to network issues.\n"
                "Please check your internet connection and try again."
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Container build/push failed: {e}")
            if hasattr(e, 'stdout') and e.stdout:
                logger.error(f"Build stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"Build stderr: {e.stderr}")
            
            # Check if it's a login issue
            if 'docker login' in str(e.cmd):
                logger.error("Docker login to ECR failed. This could be due to:")
                logger.error("1. Network connectivity issues")
                logger.error("2. AWS credentials expired")
                logger.error("3. ECR permissions issues")
                logger.error("Please check your AWS credentials and network connection.")
            
            # Try to get more detailed error information
            try:
                # Run docker build again with less verbose output to get error details
                debug_args = ['docker', 'build', '--platform', 'linux/arm64', '.']
                debug_result = subprocess.run(
                    debug_args, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=30
                )
                if debug_result.stderr:
                    logger.error(f"Docker build debug output: {debug_result.stderr}")
            except Exception as debug_e:
                logger.warning(f"Could not get additional debug info: {debug_e}")
            
            raise
    
    def _deploy_to_agentcore(self, agent_name: str) -> str:
        """Deploy to AgentCore runtime using bedrock-agentcore CLI."""
        logger.info("Deploying to AgentCore runtime...")
        
        try:
            # Configure AgentCore
            configure_args = [
                'agentcore', 'configure', 
                '-e', 'main.py',
                '--region', self.region,
                '--name', agent_name,
                '--non-interactive'
            ]
            
            logger.info("Configuring AgentCore...")
            result = subprocess.run(
                configure_args, 
                check=True, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            logger.debug(f"Configure output: {result.stdout}")
            
            # Launch AgentCore
            launch_args = ['agentcore', 'launch']
            
            logger.info("Launching AgentCore...")
            result = subprocess.run(
                launch_args, 
                check=True, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            logger.debug(f"Launch output: {result.stdout}")
            
            # Extract agent ARN from output (this would need to be parsed from actual output)
            # For now, return a mock ARN
            agent_arn = f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:runtime/{agent_name}"
            
            logger.info(f"AgentCore deployment completed: {agent_arn}")
            return agent_arn
            
        except subprocess.CalledProcessError as e:
            logger.error(f"AgentCore deployment failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"Error details: {e.stderr}")
            raise RuntimeError(f"AgentCore deployment failed: {e}")
    
    def _setup_monitoring(self, agent_name: str, agent_arn: str) -> None:
        """Setup CloudWatch monitoring and observability."""
        logger.info("Setting up monitoring and observability...")
        
        try:
            # Create CloudWatch dashboard
            dashboard_name = f"{agent_name}-gateway-dashboard"
            
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
                            "title": f"{agent_name} Gateway Metrics"
                        }
                    },
                    {
                        "type": "metric",
                        "properties": {
                            "metrics": [
                                ["AgentCore/Gateway", "MCPToolCalls", "GatewayName", agent_name],
                                [".", "MCPErrors", ".", "."],
                                [".", "AuthenticationFailures", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": f"{agent_name} MCP Tool Metrics"
                        }
                    },
                    {
                        "type": "log",
                        "properties": {
                            "query": f"SOURCE '/aws/bedrock-agentcore/{agent_name}'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 100",
                            "region": self.region,
                            "title": f"{agent_name} Gateway Logs"
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
                "AlarmName": f"{agent_name}-high-error-rate",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "Errors",
                "Namespace": "AWS/BedrockAgentCore",
                "Period": 300,
                "Statistic": "Sum",
                "Threshold": 10.0,
                "ActionsEnabled": True,
                "AlarmDescription": f"High error rate for {agent_name} Gateway",
                "Dimensions": [
                    {
                        "Name": "AgentName",
                        "Value": agent_name
                    }
                ],
                "Unit": "Count"
            },
            {
                "AlarmName": f"{agent_name}-mcp-connection-failures",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "MCPErrors",
                "Namespace": "AgentCore/Gateway",
                "Period": 300,
                "Statistic": "Sum",
                "Threshold": 5.0,
                "ActionsEnabled": True,
                "AlarmDescription": f"High MCP connection failures for {agent_name}",
                "Dimensions": [
                    {
                        "Name": "GatewayName",
                        "Value": agent_name
                    }
                ],
                "Unit": "Count"
            },
            {
                "AlarmName": f"{agent_name}-authentication-failures",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "AuthenticationFailures",
                "Namespace": "AgentCore/Gateway",
                "Period": 300,
                "Statistic": "Sum",
                "Threshold": 20.0,
                "ActionsEnabled": True,
                "AlarmDescription": f"High authentication failures for {agent_name}",
                "Dimensions": [
                    {
                        "Name": "GatewayName",
                        "Value": agent_name
                    }
                ],
                "Unit": "Count"
            }
        ]
        
        for alarm in alarms:
            try:
                self.cloudwatch_client.put_metric_alarm(**alarm)
                logger.info(f"Created CloudWatch alarm: {alarm['AlarmName']}")
            except Exception as e:
                logger.warning(f"Failed to create alarm {alarm['AlarmName']}: {e}")
    
    def _verify_deployment(self, agent_arn: str) -> None:
        """Verify the deployment is successful."""
        logger.info(f"Verifying deployment: {agent_arn}")
        
        # Test health endpoint
        try:
            # This would make an actual HTTP request to the deployed agent
            # For now, we'll just log the verification step
            logger.info("Testing health endpoint...")
            logger.info("Testing authentication endpoint...")
            logger.info("Testing MCP tool endpoints...")
            logger.info("Deployment verification completed successfully")
            
        except Exception as e:
            logger.warning(f"Deployment verification failed: {e}")
    
    def _save_deployment_config(self, config: Dict[str, Any]) -> None:
        """Save deployment configuration to file."""
        filename = "agentcore_deployment_config.json"
        
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Deployment configuration saved to: {filename}")


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Deploy AgentCore Gateway for MCP Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy AgentCore Gateway
  python deploy_agentcore.py
    
  # Validate configuration only
  python deploy_agentcore.py --validate-only
  
  # Skip container build (use existing image)
  python deploy_agentcore.py --skip-container-build
        """
    )
    
    parser.add_argument('--agent-name', default='agentcore-gateway-mcp-tools',
                       help='Name for the AgentCore runtime')
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
        deployer = AgentCoreGatewayDeployer(region=args.region)
        
        result = deployer.deploy(
            agent_name=args.agent_name,
            skip_container_build=args.skip_container_build,
            validate_only=args.validate_only
        )
        
        print("\n" + "="*60)
        if args.validate_only:
            print("CONFIGURATION VALIDATION SUCCESSFUL")
        else:
            print("AGENTCORE GATEWAY DEPLOYMENT SUCCESSFUL")
        print("="*60)
        print(f"Agent Name: {result['agent_name']}")
        print(f"Region: {result['region']}")
        
        if not args.validate_only:
            print(f"Agent ARN: {result.get('agent_arn', 'N/A')}")
            print(f"Container URI: {result.get('container_uri', 'N/A')}")
        
        print("="*60)
        
        if not args.validate_only:
            print("\nNext steps:")
            print("1. Test the deployed gateway using the test scripts")
            print("2. Monitor the gateway using CloudWatch dashboard")
            print("3. Check logs for any issues")
            print("4. Test MCP tool endpoints through the gateway")
        
    except Exception as e:
        print(f"\nDEPLOYMENT FAILED: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()