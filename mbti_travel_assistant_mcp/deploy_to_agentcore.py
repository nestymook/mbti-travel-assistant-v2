#!/usr/bin/env python3
"""
Deploy MBTI Travel Assistant MCP to Amazon Bedrock AgentCore Runtime

This script uses the bedrock-agentcore-starter-toolkit to deploy the containerized
MBTI Travel Assistant to AgentCore with proper authentication and configuration.
"""

import json
import logging
import sys
from pathlib import Path

try:
    from bedrock_agentcore_starter_toolkit import Runtime
    import boto3
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Please install: pip install bedrock-agentcore-starter-toolkit boto3")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def deploy_mbti_travel_assistant():
    """Deploy MBTI Travel Assistant MCP to AgentCore Runtime."""
    
    # Load deployment configuration
    config_file = Path("agentcore_deployment_config_production.json")
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    logger.info(f"Deploying {config['name']} to AgentCore Runtime")
    logger.info(f"Container URI: {config['container_uri']}")
    logger.info(f"Platform: {config['platform']}")
    
    try:
        # Initialize AgentCore Runtime
        runtime = Runtime()
        
        # Deploy configuration
        deployment_config = {
            "name": config["name"],
            "container_uri": config["container_uri"],
            "platform": config["platform"],
            "network_mode": config["network_mode"],
            "environment_variables": config["environment"],
            "authentication": config["authentication"],
            "observability": config["observability"],
            "resources": config.get("resources", {}),
            "scaling": config.get("scaling", {}),
            "health_check": config.get("health_check", {})
        }
        
        logger.info("Starting AgentCore deployment...")
        
        # Configure the runtime
        runtime.configure(
            entrypoint_path="main.py",
            container_uri=config["container_uri"],
            environment_variables=config["environment"]
        )
        
        # Launch the AgentCore runtime
        result = runtime.launch()
        
        if result and hasattr(result, 'agent_arn'):
            agent_arn = result.agent_arn
            logger.info(f"✅ Deployment successful!")
            logger.info(f"Agent ARN: {agent_arn}")
            
            # Save deployment result
            deployment_result = {
                "status": "success",
                "agent_arn": agent_arn,
                "agent_name": config["name"],
                "container_uri": config["container_uri"],
                "cognito_user_pool_id": config["environment"]["COGNITO_USER_POOL_ID"],
                "discovery_url": config["authentication"]["config"]["customJWTAuthorizer"]["discoveryUrl"],
                "search_mcp_endpoint": config["environment"]["SEARCH_MCP_ENDPOINT"],
                "reasoning_mcp_endpoint": config["environment"]["REASONING_MCP_ENDPOINT"],
                "model": config["environment"]["AGENT_MODEL"]
            }
            
            with open("deployment_result.json", 'w') as f:
                json.dump(deployment_result, f, indent=2)
            
            print("\n" + "="*60)
            print("🎉 MBTI TRAVEL ASSISTANT MCP DEPLOYMENT SUCCESSFUL! 🎉")
            print("="*60)
            print(f"Agent Name: {config['name']}")
            print(f"Agent ARN: {agent_arn}")
            print(f"Model: {config['environment']['AGENT_MODEL']}")
            print(f"Platform: {config['platform']}")
            print(f"Authentication: JWT (Cognito)")
            print(f"User Pool ID: {config['environment']['COGNITO_USER_POOL_ID']}")
            print(f"Search MCP: {config['environment']['SEARCH_MCP_ENDPOINT']}")
            print(f"Reasoning MCP: {config['environment']['REASONING_MCP_ENDPOINT']}")
            print("="*60)
            print("\nNext Steps:")
            print("1. Test the deployment using the test scripts")
            print("2. Monitor via CloudWatch dashboard")
            print("3. Check logs for any issues")
            print("4. Create test users in Cognito if needed")
            
            return True
            
        else:
            logger.error("❌ Deployment failed - no agent ARN returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        
        # Save error result
        error_result = {
            "status": "failed",
            "error": str(e),
            "agent_name": config["name"],
            "container_uri": config["container_uri"]
        }
        
        with open("deployment_result.json", 'w') as f:
            json.dump(error_result, f, indent=2)
        
        return False


def check_prerequisites():
    """Check if all prerequisites are met."""
    logger.info("Checking deployment prerequisites...")
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"✅ AWS credentials configured for account: {identity['Account']}")
    except Exception as e:
        logger.error(f"❌ AWS credentials not configured: {e}")
        return False
    
    # Check if container exists in ECR
    try:
        ecr = boto3.client('ecr', region_name='us-east-1')
        response = ecr.describe_images(
            repositoryName='mbti-travel-assistant-mcp',
            imageIds=[{'imageTag': 'latest'}]
        )
        if response['imageDetails']:
            logger.info("✅ Container image found in ECR")
        else:
            logger.error("❌ Container image not found in ECR")
            return False
    except Exception as e:
        logger.error(f"❌ Error checking ECR: {e}")
        return False
    
    # Check if configuration file exists
    config_file = Path("agentcore_deployment_config_production.json")
    if config_file.exists():
        logger.info("✅ Deployment configuration found")
    else:
        logger.error("❌ Deployment configuration not found")
        return False
    
    logger.info("✅ All prerequisites met")
    return True


if __name__ == "__main__":
    logger.info("Starting MBTI Travel Assistant MCP deployment to AgentCore")
    
    if not check_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)
    
    success = deploy_mbti_travel_assistant()
    
    if success:
        logger.info("🎉 Deployment completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Deployment failed!")
        sys.exit(1)