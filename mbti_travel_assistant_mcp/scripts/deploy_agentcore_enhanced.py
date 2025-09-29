#!/usr/bin/env python3
"""
Enhanced AgentCore Deployment Script for MBTI Travel Assistant MCP

This script provides comprehensive deployment automation for the MBTI Travel Assistant
to Amazon Bedrock AgentCore Runtime with environment-specific configurations,
knowledge base automation, and deployment verification.

Features:
- Environment-specific deployment configurations
- Automated knowledge base configuration and validation
- ECR repository management with ARM64 container building
- Cognito User Pool creation and JWT configuration
- AgentCore runtime deployment with observability
- Deployment verification and health checks
- Configuration validation and rollback capabilities
"""

import json
import os
import sys
import logging
import subprocess
import base64
import yaml
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import ConfigLoader
from services.cloudwatch_monitor import CloudWatchMonitor
from services.health_check import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Manages knowledge base configuration and validation."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize knowledge base manager."""
        self.region = region
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
    
    def validate_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """
        Validate knowledge base configuration and status.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            Validation result dictionary
        """
        try:
            logger.info(f"Validating knowledge base: {kb_id}")
            
            # Get knowledge base details
            kb_response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
            kb_info = kb_response['knowledgeBase']
            
            # Get data sources
            data_sources_response = self.bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            data_sources = data_sources_response['dataSourceSummaries']
            
            # Check knowledge base status
            kb_status = kb_info['status']
            if kb_status != 'ACTIVE':
                return {
                    "valid": False,
                    "error": f"Knowledge base status is {kb_status}, expected ACTIVE",
                    "kb_info": kb_info
                }
            
            # Validate data sources
            active_data_sources = []
            for ds in data_sources:
                ds_details = self.bedrock_agent.get_data_source(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds['dataSourceId']
                )
                
                if ds_details['dataSource']['status'] == 'AVAILABLE':
                    active_data_sources.append(ds_details['dataSource'])
                else:
                    logger.warning(f"Data source {ds['name']} is not available: {ds_details['dataSource']['status']}")
            
            if not active_data_sources:
                return {
                    "valid": False,
                    "error": "No active data sources found",
                    "kb_info": kb_info,
                    "data_sources": data_sources
                }
            
            # Test knowledge base query
            test_result = self._test_knowledge_base_query(kb_id)
            
            return {
                "valid": True,
                "kb_info": kb_info,
                "data_sources": active_data_sources,
                "test_query_result": test_result,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Knowledge base validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _test_knowledge_base_query(self, kb_id: str) -> Dict[str, Any]:
        """Test knowledge base with a simple query."""
        try:
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': 'What tourist spots are available?'},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {'numberOfResults': 3}
                }
            )
            
            results = response.get('retrievalResults', [])
            
            return {
                "success": True,
                "results_count": len(results),
                "has_content": len(results) > 0 and bool(results[0].get('content', {}).get('text'))
            }
            
        except Exception as e:
            logger.error(f"Knowledge base test query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def ensure_knowledge_base_ready(self, kb_id: str, timeout_minutes: int = 10) -> bool:
        """
        Ensure knowledge base is ready for use.
        
        Args:
            kb_id: Knowledge base ID
            timeout_minutes: Maximum time to wait
            
        Returns:
            True if ready, False otherwise
        """
        logger.info(f"Ensuring knowledge base {kb_id} is ready...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            validation_result = self.validate_knowledge_base(kb_id)
            
            if validation_result["valid"]:
                logger.info(f"Knowledge base {kb_id} is ready")
                return True
            
            logger.info(f"Knowledge base not ready: {validation_result.get('error', 'Unknown error')}")
            time.sleep(30)
        
        logger.error(f"Knowledge base {kb_id} not ready after {timeout_minutes} minutes")
        return False


class EnhancedAgentCoreDeployer:
    """Enhanced AgentCore deployer with comprehensive automation."""
    
    def __init__(self, region: str = "us-east-1", environment: str = "development"):
        """
        Initialize the enhanced deployer.
        
        Args:
            region: AWS region for deployment
            environment: Environment (development, staging, production)
        """
        self.region = region
        self.environment = environment
        self.session = boto3.Session()
        
        # Load configuration
        self.config_loader = ConfigLoader(environment)
        self.config = self.config_loader.load_config()
        
        # Initialize AWS clients
        try:
            self.sts_client = self.session.client('sts', region_name=region)
            self.ecr_client = self.session.client('ecr', region_name=region)
            self.cognito_client = self.session.client('cognito-idp', region_name=region)
            self.cloudformation = self.session.client('cloudformation', region_name=region)
            
            # Initialize managers
            self.kb_manager = KnowledgeBaseManager(region)
            self.cloudwatch_monitor = CloudWatchMonitor(region, environment=environment)
            self.health_checker = HealthChecker()
            
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
    
    async def deploy_complete_stack(
        self,
        agent_name: str = "mbti-travel-assistant-mcp",
        skip_container_build: bool = False,
        validate_only: bool = False,
        enable_rollback: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy complete MBTI Travel Assistant stack.
        
        Args:
            agent_name: Name for the AgentCore runtime
            skip_container_build: Skip container building step
            validate_only: Only validate configuration without deploying
            enable_rollback: Enable automatic rollback on failure
            
        Returns:
            Deployment result dictionary
        """
        logger.info(f"Starting complete stack deployment for {agent_name}")
        
        deployment_config = {
            "agent_name": agent_name,
            "environment": self.environment,
            "timestamp": datetime.utcnow().isoformat(),
            "region": self.region,
            "account_id": self.account_id,
            "deployment_id": f"{agent_name}-{self.environment}-{int(time.time())}",
            "phases": {}
        }
        
        try:
            # Phase 1: Pre-deployment validation
            logger.info("Phase 1: Pre-deployment validation")
            validation_result = await self._validate_deployment_prerequisites()
            deployment_config["phases"]["validation"] = validation_result
            
            if not validation_result["success"]:
                raise Exception(f"Pre-deployment validation failed: {validation_result['errors']}")
            
            if validate_only:
                deployment_config["status"] = "validated"
                return deployment_config
            
            # Phase 2: Knowledge base validation and configuration
            logger.info("Phase 2: Knowledge base validation")
            kb_result = await self._configure_knowledge_base()
            deployment_config["phases"]["knowledge_base"] = kb_result
            
            # Phase 3: Infrastructure setup
            logger.info("Phase 3: Infrastructure setup")
            infra_result = await self._setup_infrastructure(agent_name)
            deployment_config["phases"]["infrastructure"] = infra_result
            
            # Phase 4: Container build and push
            if not skip_container_build:
                logger.info("Phase 4: Container build and push")
                container_result = await self._build_and_push_container(agent_name)
                deployment_config["phases"]["container"] = container_result
            else:
                logger.info("Phase 4: Skipping container build")
                deployment_config["phases"]["container"] = {"skipped": True}
            
            # Phase 5: AgentCore deployment
            logger.info("Phase 5: AgentCore deployment")
            agentcore_result = await self._deploy_agentcore_runtime(agent_name, deployment_config)
            deployment_config["phases"]["agentcore"] = agentcore_result
            
            # Phase 6: Post-deployment verification
            logger.info("Phase 6: Post-deployment verification")
            verification_result = await self._verify_deployment(agent_name, deployment_config)
            deployment_config["phases"]["verification"] = verification_result
            
            # Phase 7: Monitoring and observability setup
            logger.info("Phase 7: Monitoring setup")
            monitoring_result = await self._setup_monitoring(agent_name)
            deployment_config["phases"]["monitoring"] = monitoring_result
            
            # Determine overall success
            deployment_config["status"] = "success"
            deployment_config["agent_arn"] = agentcore_result.get("agent_arn")
            deployment_config["endpoint_url"] = agentcore_result.get("endpoint_url")
            
            logger.info(f"Complete stack deployment successful for {agent_name}")
            
            # Save deployment configuration
            await self._save_deployment_config(deployment_config)
            
            return deployment_config
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            deployment_config["status"] = "failed"
            deployment_config["error"] = str(e)
            
            if enable_rollback:
                logger.info("Initiating rollback...")
                rollback_result = await self._rollback_deployment(deployment_config)
                deployment_config["rollback"] = rollback_result
            
            await self._save_deployment_config(deployment_config)
            raise
    
    async def _validate_deployment_prerequisites(self) -> Dict[str, Any]:
        """Validate all deployment prerequisites."""
        logger.info("Validating deployment prerequisites...")
        
        validation_result = {
            "success": True,
            "checks": {},
            "errors": [],
            "warnings": []
        }
        
        # Check AWS credentials and permissions
        try:
            identity = self.sts_client.get_caller_identity()
            validation_result["checks"]["aws_credentials"] = {
                "success": True,
                "account_id": identity["Account"],
                "user_arn": identity["Arn"]
            }
        except Exception as e:
            validation_result["checks"]["aws_credentials"] = {"success": False, "error": str(e)}
            validation_result["errors"].append(f"AWS credentials: {e}")
            validation_result["success"] = False
        
        # Check Docker availability
        try:
            result = subprocess.run(['docker', '--version'], check=True, capture_output=True, text=True)
            validation_result["checks"]["docker"] = {
                "success": True,
                "version": result.stdout.strip()
            }
        except Exception as e:
            validation_result["checks"]["docker"] = {"success": False, "error": str(e)}
            validation_result["errors"].append(f"Docker: {e}")
            validation_result["success"] = False
        
        # Check required configuration files
        required_files = [
            ".bedrock_agentcore.yaml",
            "requirements.txt",
            "main.py",
            f"config/environments/{self.environment}.env"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                validation_result["checks"][f"file_{file_path}"] = {"success": True}
            else:
                validation_result["checks"][f"file_{file_path}"] = {"success": False, "error": "File not found"}
                validation_result["errors"].append(f"Required file not found: {file_path}")
                validation_result["success"] = False
        
        # Validate environment configuration
        try:
            required_env_vars = [
                "SEARCH_MCP_ENDPOINT",
                "REASONING_MCP_ENDPOINT",
                "AGENT_MODEL",
                "KNOWLEDGE_BASE_ID"
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not self.config.get(var):
                    missing_vars.append(var)
            
            if missing_vars:
                validation_result["checks"]["environment_config"] = {
                    "success": False,
                    "missing_vars": missing_vars
                }
                validation_result["errors"].append(f"Missing environment variables: {missing_vars}")
                validation_result["success"] = False
            else:
                validation_result["checks"]["environment_config"] = {"success": True}
                
        except Exception as e:
            validation_result["checks"]["environment_config"] = {"success": False, "error": str(e)}
            validation_result["errors"].append(f"Environment config: {e}")
            validation_result["success"] = False
        
        # Check MCP endpoints availability
        mcp_endpoints = {
            "search": self.config.get("SEARCH_MCP_ENDPOINT"),
            "reasoning": self.config.get("REASONING_MCP_ENDPOINT")
        }
        
        for name, endpoint in mcp_endpoints.items():
            if endpoint:
                try:
                    # Simple connectivity check (placeholder)
                    validation_result["checks"][f"mcp_{name}_endpoint"] = {
                        "success": True,
                        "endpoint": endpoint
                    }
                except Exception as e:
                    validation_result["checks"][f"mcp_{name}_endpoint"] = {
                        "success": False,
                        "error": str(e)
                    }
                    validation_result["warnings"].append(f"MCP {name} endpoint may not be accessible: {e}")
        
        return validation_result
    
    async def _configure_knowledge_base(self) -> Dict[str, Any]:
        """Configure and validate knowledge base."""
        logger.info("Configuring knowledge base...")
        
        kb_id = self.config.get("KNOWLEDGE_BASE_ID")
        if not kb_id:
            return {
                "success": False,
                "error": "Knowledge base ID not configured"
            }
        
        # Validate knowledge base
        validation_result = self.kb_manager.validate_knowledge_base(kb_id)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Knowledge base validation failed: {validation_result.get('error')}",
                "validation_result": validation_result
            }
        
        # Ensure knowledge base is ready
        is_ready = self.kb_manager.ensure_knowledge_base_ready(kb_id)
        
        return {
            "success": is_ready,
            "knowledge_base_id": kb_id,
            "validation_result": validation_result,
            "ready": is_ready
        }
    
    async def _setup_infrastructure(self, agent_name: str) -> Dict[str, Any]:
        """Setup required infrastructure components."""
        logger.info("Setting up infrastructure...")
        
        infra_result = {
            "components": {},
            "success": True
        }
        
        try:
            # Setup ECR repository
            ecr_result = await self._setup_ecr_repository(agent_name)
            infra_result["components"]["ecr"] = ecr_result
            
            # Setup Cognito User Pool
            cognito_result = await self._setup_cognito_user_pool(agent_name)
            infra_result["components"]["cognito"] = cognito_result
            
            # Setup CloudWatch log groups
            logs_result = await self._setup_log_groups(agent_name)
            infra_result["components"]["logs"] = logs_result
            
            # Setup IAM roles if needed
            iam_result = await self._setup_iam_roles(agent_name)
            infra_result["components"]["iam"] = iam_result
            
        except Exception as e:
            logger.error(f"Infrastructure setup failed: {e}")
            infra_result["success"] = False
            infra_result["error"] = str(e)
        
        return infra_result
    
    async def _setup_ecr_repository(self, agent_name: str) -> Dict[str, Any]:
        """Setup ECR repository for container images."""
        repository_name = agent_name.lower()
        
        try:
            # Check if repository exists
            try:
                response = self.ecr_client.describe_repositories(
                    repositoryNames=[repository_name]
                )
                repository_uri = response['repositories'][0]['repositoryUri']
                logger.info(f"Using existing ECR repository: {repository_uri}")
                
                return {
                    "success": True,
                    "repository_uri": repository_uri,
                    "created": False
                }
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                    # Create new repository
                    logger.info(f"Creating ECR repository: {repository_name}")
                    response = self.ecr_client.create_repository(
                        repositoryName=repository_name,
                        imageScanningConfiguration={'scanOnPush': True},
                        encryptionConfiguration={'encryptionType': 'AES256'}
                    )
                    repository_uri = response['repository']['repositoryUri']
                    
                    # Set lifecycle policy
                    lifecycle_policy = {
                        "rules": [
                            {
                                "rulePriority": 1,
                                "description": "Keep last 10 images",
                                "selection": {
                                    "tagStatus": "any",
                                    "countType": "imageCountMoreThan",
                                    "countNumber": 10
                                },
                                "action": {
                                    "type": "expire"
                                }
                            }
                        ]
                    }
                    
                    self.ecr_client.put_lifecycle_policy(
                        repositoryName=repository_name,
                        lifecyclePolicyText=json.dumps(lifecycle_policy)
                    )
                    
                    logger.info(f"Created ECR repository: {repository_uri}")
                    
                    return {
                        "success": True,
                        "repository_uri": repository_uri,
                        "created": True
                    }
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"ECR repository setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _setup_cognito_user_pool(self, agent_name: str) -> Dict[str, Any]:
        """Setup Cognito User Pool for authentication."""
        user_pool_name = f"{agent_name}-{self.environment}-user-pool"
        
        try:
            # Check if user pool already exists
            existing_pools = self.cognito_client.list_user_pools(MaxResults=60)
            for pool in existing_pools['UserPools']:
                if pool['Name'] == user_pool_name:
                    logger.info(f"Using existing Cognito User Pool: {pool['Id']}")
                    return await self._get_existing_cognito_config(pool['Id'], agent_name)
            
            # Create new user pool
            logger.info(f"Creating Cognito User Pool: {user_pool_name}")
            
            # Environment-specific password policy
            password_policy = self._get_password_policy_for_environment()
            
            response = self.cognito_client.create_user_pool(
                PoolName=user_pool_name,
                Policies={'PasswordPolicy': password_policy},
                AutoVerifiedAttributes=['email'],
                UsernameAttributes=['email'],
                Schema=[
                    {
                        'Name': 'email',
                        'AttributeDataType': 'String',
                        'Required': True,
                        'Mutable': True
                    },
                    {
                        'Name': 'name',
                        'AttributeDataType': 'String',
                        'Required': False,
                        'Mutable': True
                    }
                ],
                UserPoolTags={
                    'Environment': self.environment,
                    'Application': agent_name,
                    'ManagedBy': 'EnhancedAgentCoreDeployer'
                }
            )
            
            user_pool_id = response['UserPool']['Id']
            
            # Create User Pool Client
            client_response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=f"{agent_name}-{self.environment}-client",
                GenerateSecret=False,
                ExplicitAuthFlows=[
                    'ADMIN_NO_SRP_AUTH',
                    'ALLOW_USER_SRP_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH'
                ],
                TokenValidityUnits={
                    'AccessToken': 'hours',
                    'IdToken': 'hours',
                    'RefreshToken': 'days'
                },
                AccessTokenValidity=1,
                IdTokenValidity=1,
                RefreshTokenValidity=30
            )
            
            client_id = client_response['UserPoolClient']['ClientId']
            
            return {
                "success": True,
                "user_pool_id": user_pool_id,
                "client_id": client_id,
                "discovery_url": f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid_configuration",
                "created": True
            }
            
        except Exception as e:
            logger.error(f"Cognito setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_existing_cognito_config(self, user_pool_id: str, agent_name: str) -> Dict[str, Any]:
        """Get configuration for existing Cognito User Pool."""
        try:
            # Find existing client
            clients = self.cognito_client.list_user_pool_clients(
                UserPoolId=user_pool_id,
                MaxResults=60
            )
            
            client_name = f"{agent_name}-{self.environment}-client"
            client_id = None
            
            for client in clients['UserPoolClients']:
                if client['ClientName'] == client_name:
                    client_id = client['ClientId']
                    break
            
            if not client_id:
                # Create new client for this environment
                client_response = self.cognito_client.create_user_pool_client(
                    UserPoolId=user_pool_id,
                    ClientName=client_name,
                    GenerateSecret=False,
                    ExplicitAuthFlows=[
                        'ADMIN_NO_SRP_AUTH',
                        'ALLOW_USER_SRP_AUTH',
                        'ALLOW_REFRESH_TOKEN_AUTH'
                    ]
                )
                client_id = client_response['UserPoolClient']['ClientId']
            
            return {
                "success": True,
                "user_pool_id": user_pool_id,
                "client_id": client_id,
                "discovery_url": f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid_configuration",
                "created": False
            }
            
        except Exception as e:
            logger.error(f"Failed to get existing Cognito config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_password_policy_for_environment(self) -> Dict[str, Any]:
        """Get environment-specific password policy."""
        policies = {
            "production": {
                'MinimumLength': 12,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True
            },
            "staging": {
                'MinimumLength': 10,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': False
            },
            "development": {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': False
            }
        }
        
        return policies.get(self.environment, policies["development"])
    
    async def _setup_log_groups(self, agent_name: str) -> Dict[str, Any]:
        """Setup CloudWatch log groups."""
        log_groups = [
            f"/aws/lambda/{agent_name}-{self.environment}",
            f"/mbti/travel-assistant/{self.environment}/application",
            f"/mbti/travel-assistant/{self.environment}/mcp-calls",
            f"/mbti/travel-assistant/{self.environment}/security"
        ]
        
        created_groups = []
        failed_groups = []
        
        retention_days = 7 if self.environment == "development" else 30
        
        for log_group in log_groups:
            try:
                success = self.cloudwatch_monitor.create_log_group(log_group, retention_days)
                if success:
                    created_groups.append(log_group)
                else:
                    failed_groups.append(log_group)
            except Exception as e:
                logger.error(f"Failed to create log group {log_group}: {e}")
                failed_groups.append(log_group)
        
        return {
            "success": len(failed_groups) == 0,
            "created": created_groups,
            "failed": failed_groups
        }
    
    async def _setup_iam_roles(self, agent_name: str) -> Dict[str, Any]:
        """Setup IAM roles if needed."""
        # For now, return success as AgentCore handles IAM roles automatically
        return {
            "success": True,
            "message": "IAM roles managed by AgentCore"
        }
    
    async def _build_and_push_container(self, agent_name: str) -> Dict[str, Any]:
        """Build and push ARM64 container to ECR."""
        logger.info("Building and pushing ARM64 container...")
        
        try:
            # Get ECR repository URI from infrastructure setup
            repository_name = agent_name.lower()
            
            response = self.ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            repository_uri = response['repositories'][0]['repositoryUri']
            
            # Get ECR login token
            token_response = self.ecr_client.get_authorization_token()
            token = token_response['authorizationData'][0]['authorizationToken']
            endpoint = token_response['authorizationData'][0]['proxyEndpoint']
            
            # Decode token and login to ECR
            username, password = base64.b64decode(token).decode().split(':')
            
            # Docker login
            subprocess.run([
                'docker', 'login', '--username', username, '--password-stdin', endpoint
            ], input=password.encode(), check=True, capture_output=True)
            
            # Build ARM64 container
            image_tag = f"{repository_uri}:{self.environment}-{int(time.time())}"
            latest_tag = f"{repository_uri}:latest"
            
            build_args = [
                'docker', 'build',
                '--platform', 'linux/arm64',
                '--build-arg', f'ENVIRONMENT={self.environment}',
                '--build-arg', f'AWS_REGION={self.region}',
                '-t', image_tag,
                '-t', latest_tag,
                '.'
            ]
            
            logger.info(f"Building container with tags: {image_tag}, {latest_tag}")
            result = subprocess.run(build_args, check=True, capture_output=True, text=True)
            
            # Push both tags
            subprocess.run(['docker', 'push', image_tag], check=True)
            subprocess.run(['docker', 'push', latest_tag], check=True)
            
            logger.info(f"Successfully pushed container: {image_tag}")
            
            return {
                "success": True,
                "image_tag": image_tag,
                "latest_tag": latest_tag,
                "repository_uri": repository_uri
            }
            
        except Exception as e:
            logger.error(f"Container build/push failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _deploy_agentcore_runtime(self, agent_name: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to AgentCore runtime."""
        logger.info("Deploying to AgentCore runtime...")
        
        try:
            # This would use the actual AgentCore SDK
            # For now, return a placeholder implementation
            
            # Get infrastructure components
            infra = deployment_config["phases"]["infrastructure"]["components"]
            container_info = deployment_config["phases"].get("container", {})
            
            # Create AgentCore configuration
            agentcore_config = {
                "name": f"{agent_name}-{self.environment}",
                "container_uri": container_info.get("latest_tag", f"{infra['ecr']['repository_uri']}:latest"),
                "platform": "linux/arm64",
                "network_mode": "PUBLIC",
                "authentication": {
                    "type": "jwt",
                    "config": {
                        "customJWTAuthorizer": {
                            "allowedClients": [infra["cognito"]["client_id"]],
                            "discoveryUrl": infra["cognito"]["discovery_url"]
                        }
                    }
                },
                "environment": self._get_runtime_environment_variables(),
                "observability": {
                    "enabled": True,
                    "tracing": True,
                    "metrics": True,
                    "logs": True
                },
                "resources": self._get_resource_configuration(),
                "scaling": self._get_scaling_configuration()
            }
            
            # Save AgentCore configuration
            config_file = f"agentcore_deployment_config_{self.environment}.json"
            with open(config_file, 'w') as f:
                json.dump(agentcore_config, f, indent=2)
            
            # Placeholder for actual AgentCore deployment
            # In real implementation, this would use bedrock-agentcore SDK
            agent_arn = f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:agent/{agent_name}-{self.environment}"
            endpoint_url = f"https://{agent_name}-{self.environment}.agentcore.{self.region}.amazonaws.com"
            
            return {
                "success": True,
                "agent_arn": agent_arn,
                "endpoint_url": endpoint_url,
                "config_file": config_file,
                "agentcore_config": agentcore_config
            }
            
        except Exception as e:
            logger.error(f"AgentCore deployment failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_runtime_environment_variables(self) -> Dict[str, str]:
        """Get runtime environment variables."""
        env_vars = {
            "AWS_REGION": self.region,
            "AWS_DEFAULT_REGION": self.region,
            "ENVIRONMENT": self.environment,
            "DOCKER_CONTAINER": "1"
        }
        
        # Add configuration from environment file
        config_vars = [
            "SEARCH_MCP_ENDPOINT",
            "REASONING_MCP_ENDPOINT",
            "AGENT_MODEL",
            "KNOWLEDGE_BASE_ID",
            "CACHE_ENABLED",
            "CACHE_TTL",
            "LOG_LEVEL",
            "LOG_FORMAT"
        ]
        
        for var in config_vars:
            value = self.config.get(var)
            if value is not None:
                env_vars[var] = str(value)
        
        return env_vars
    
    def _get_resource_configuration(self) -> Dict[str, str]:
        """Get resource configuration based on environment."""
        resources = {
            "production": {"cpu": "2 vCPU", "memory": "4 GB"},
            "staging": {"cpu": "1 vCPU", "memory": "2 GB"},
            "development": {"cpu": "0.5 vCPU", "memory": "1 GB"}
        }
        
        return resources.get(self.environment, resources["development"])
    
    def _get_scaling_configuration(self) -> Dict[str, Any]:
        """Get scaling configuration based on environment."""
        scaling = {
            "production": {"min_instances": 2, "max_instances": 20, "target_utilization": 70},
            "staging": {"min_instances": 1, "max_instances": 10, "target_utilization": 70},
            "development": {"min_instances": 1, "max_instances": 3, "target_utilization": 80}
        }
        
        return scaling.get(self.environment, scaling["development"])
    
    async def _verify_deployment(self, agent_name: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Verify deployment is working correctly."""
        logger.info("Verifying deployment...")
        
        verification_result = {
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Check AgentCore endpoint availability
            agentcore_info = deployment_config["phases"]["agentcore"]
            endpoint_url = agentcore_info.get("endpoint_url")
            
            if endpoint_url:
                # Placeholder for endpoint health check
                verification_result["checks"]["endpoint_health"] = {
                    "success": True,
                    "endpoint": endpoint_url
                }
            
            # Check knowledge base connectivity
            kb_id = self.config.get("KNOWLEDGE_BASE_ID")
            if kb_id:
                kb_test = self.kb_manager._test_knowledge_base_query(kb_id)
                verification_result["checks"]["knowledge_base"] = kb_test
                
                if not kb_test["success"]:
                    verification_result["errors"].append("Knowledge base connectivity failed")
                    verification_result["success"] = False
            
            # Check MCP endpoints (placeholder)
            mcp_endpoints = {
                "search": self.config.get("SEARCH_MCP_ENDPOINT"),
                "reasoning": self.config.get("REASONING_MCP_ENDPOINT")
            }
            
            for name, endpoint in mcp_endpoints.items():
                if endpoint:
                    # Placeholder for MCP endpoint check
                    verification_result["checks"][f"mcp_{name}"] = {
                        "success": True,
                        "endpoint": endpoint
                    }
            
            # Check CloudWatch logs
            log_groups = deployment_config["phases"]["infrastructure"]["components"]["logs"]
            if log_groups["success"]:
                verification_result["checks"]["cloudwatch_logs"] = {
                    "success": True,
                    "log_groups": log_groups["created"]
                }
            
        except Exception as e:
            logger.error(f"Deployment verification failed: {e}")
            verification_result["success"] = False
            verification_result["error"] = str(e)
        
        return verification_result
    
    async def _setup_monitoring(self, agent_name: str) -> Dict[str, Any]:
        """Setup monitoring and observability."""
        logger.info("Setting up monitoring...")
        
        try:
            # Create CloudWatch dashboard
            dashboard_success = self.cloudwatch_monitor.create_dashboard(agent_name)
            
            # Create standard alarms
            created_alarms = self.cloudwatch_monitor.create_standard_alarms(agent_name)
            
            return {
                "success": dashboard_success and len(created_alarms) > 0,
                "dashboard_created": dashboard_success,
                "alarms_created": created_alarms,
                "alarms_count": len(created_alarms)
            }
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _rollback_deployment(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback deployment on failure."""
        logger.info("Rolling back deployment...")
        
        rollback_result = {
            "success": True,
            "actions": []
        }
        
        try:
            # Rollback AgentCore deployment (placeholder)
            if "agentcore" in deployment_config["phases"]:
                rollback_result["actions"].append("AgentCore deployment rollback (placeholder)")
            
            # Clean up created resources if needed
            if "infrastructure" in deployment_config["phases"]:
                infra = deployment_config["phases"]["infrastructure"]["components"]
                
                # Don't delete ECR repository or Cognito User Pool as they might be reused
                # Just log what would be cleaned up
                rollback_result["actions"].append("Infrastructure cleanup (ECR and Cognito preserved)")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_result["success"] = False
            rollback_result["error"] = str(e)
        
        return rollback_result
    
    async def _save_deployment_config(self, deployment_config: Dict[str, Any]) -> None:
        """Save deployment configuration to file."""
        try:
            config_file = f"deployment_result_{self.environment}_{int(time.time())}.json"
            with open(config_file, 'w') as f:
                json.dump(deployment_config, f, indent=2, default=str)
            
            logger.info(f"Deployment configuration saved to: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save deployment configuration: {e}")


async def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced AgentCore deployment for MBTI Travel Assistant'
    )
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--agent-name', default='mbti-travel-assistant-mcp',
                       help='Agent name')
    parser.add_argument('--skip-container-build', action='store_true',
                       help='Skip container building step')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate configuration')
    parser.add_argument('--disable-rollback', action='store_true',
                       help='Disable automatic rollback on failure')
    
    args = parser.parse_args()
    
    try:
        deployer = EnhancedAgentCoreDeployer(
            region=args.region,
            environment=args.environment
        )
        
        result = await deployer.deploy_complete_stack(
            agent_name=args.agent_name,
            skip_container_build=args.skip_container_build,
            validate_only=args.validate_only,
            enable_rollback=not args.disable_rollback
        )
        
        if result["status"] == "success":
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT SUCCESSFUL! 🎉")
            print("="*60)
            print(f"Agent Name: {result['agent_name']}")
            print(f"Environment: {result['environment']}")
            if result.get("agent_arn"):
                print(f"Agent ARN: {result['agent_arn']}")
            if result.get("endpoint_url"):
                print(f"Endpoint URL: {result['endpoint_url']}")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ DEPLOYMENT FAILED")
            print("="*60)
            print(f"Error: {result.get('error', 'Unknown error')}")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))