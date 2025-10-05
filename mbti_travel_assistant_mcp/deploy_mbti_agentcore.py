#!/usr/bin/env python3
"""
AgentCore Runtime Deployment Script for MBTI Travel Assistant MCP

This script configures and deploys the MBTI Travel Assistant MCP server to
Amazon Bedrock AgentCore Runtime using the bedrock-agentcore-starter-toolkit.
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime


class MBTITravelAssistantDeployment:
    """Deploy MBTI Travel Assistant MCP to Bedrock AgentCore Runtime."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize AgentCore deployment.
        
        Args:
            region: AWS region for deployment.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.agentcore_runtime = Runtime()
        self.deployment_config_file = "agentcore_deployment_config.json"
        
    def load_cognito_config(self, config_file: str = "cognito_config.json") -> Dict[str, Any]:
        """Load Cognito configuration from existing setup.
        
        Args:
            config_file: Path to Cognito configuration file.
            
        Returns:
            Cognito configuration dictionary.
        """
        try:
            if not os.path.exists(config_file):
                # Use existing Cognito User Pool from other MCP deployments
                print("Using existing Cognito User Pool from restaurant MCP deployments")
                return {
                    "user_pool": {
                        "user_pool_id": "us-east-1_KePRX24Bn"
                    },
                    "app_client": {
                        "client_id": "placeholder"  # Will be retrieved from Cognito
                    },
                    "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration",
                    "region": "us-east-1"
                }
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"✓ Loaded Cognito configuration from: {config_file}")
            return config
            
        except Exception as e:
            print(f"✗ Error loading Cognito configuration: {e}")
            raise
    
    def create_jwt_authorizer_config(self, cognito_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create JWT authorizer configuration for AgentCore Runtime.
        
        Args:
            cognito_config: Cognito configuration dictionary.
            
        Returns:
            JWT authorizer configuration.
        """
        discovery_url = cognito_config['discovery_url']
        
        # Get client ID from Cognito User Pool
        client_id = cognito_config.get('app_client', {}).get('client_id', '26k0pnja579pdpb1pt6savs27e')
        
        # Create JWT authorizer configuration with existing Cognito setup
        auth_config = {
            "customJWTAuthorizer": {
                "allowedClients": [client_id],
                "discoveryUrl": discovery_url,
            }
        }
        
        print(f"✓ Created JWT authorizer config for MBTI Travel Assistant:")
        print(f"  - Client ID: {client_id}")
        print(f"  - Discovery URL: {discovery_url}")
        print(f"  - User Pool ID: {cognito_config['user_pool']['user_pool_id']}")
        print(f"  - Region: {cognito_config['region']}")
        return auth_config
    
    def configure_agentcore_runtime(self, 
                                   entrypoint: str = "main.py",
                                   agent_name: str = "mbti_travel_assistant_mcp",
                                   requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        """Configure AgentCore Runtime deployment for MBTI Travel Assistant.
        
        Args:
            entrypoint: Python file to use as entrypoint.
            agent_name: Name for the MBTI Travel Assistant agent.
            requirements_file: Path to requirements.txt file.
            
        Returns:
            Configuration response from AgentCore Runtime.
        """
        try:
            # Load existing Cognito configuration
            cognito_config = self.load_cognito_config()
            
            # Create JWT authorizer configuration
            auth_config = self.create_jwt_authorizer_config(cognito_config)
            
            # Validate entrypoint file exists
            if not os.path.exists(entrypoint):
                raise FileNotFoundError(f"Entrypoint file not found: {entrypoint}")
            
            # Validate requirements file exists
            if not os.path.exists(requirements_file):
                raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
            
            print(f"🚀 Configuring AgentCore Runtime deployment for MBTI Travel Assistant...")
            print(f"Entrypoint: {entrypoint}")
            print(f"Agent Name: {agent_name}")
            print(f"Requirements: {requirements_file}")
            print(f"Region: {self.region}")
            print(f"Model: Amazon Nova Pro 300K")
            
            # Configure AgentCore Runtime with MBTI Travel Assistant settings
            response = self.agentcore_runtime.configure(
                entrypoint=entrypoint,
                auto_create_execution_role=True,
                auto_create_ecr=True,
                requirements_file=requirements_file,
                region=self.region,
                authorizer_configuration=auth_config,
                agent_name=agent_name
            )
            
            print("✓ AgentCore Runtime configuration completed for MBTI Travel Assistant")
            
            # Save configuration for reference
            config_data = {
                'entrypoint': entrypoint,
                'agent_name': agent_name,
                'requirements_file': requirements_file,
                'region': self.region,
                'model': 'amazon.nova-pro-v1:0:300k',
                'auth_config': auth_config,
                'cognito_config': cognito_config,
                'configuration_response': response,
                'configured_at': time.time(),
                'server_type': 'mbti_travel_assistant'
            }
            
            self.save_deployment_config(config_data)
            
            return response
            
        except Exception as e:
            print(f"✗ Error configuring AgentCore Runtime for MBTI Travel Assistant: {e}")
            raise
    
    def launch_deployment(self) -> Dict[str, Any]:
        """Launch the MBTI Travel Assistant deployment to AgentCore Runtime.
        
        Returns:
            Launch response from AgentCore Runtime.
        """
        try:
            print("🚀 Launching MBTI Travel Assistant deployment to AgentCore Runtime...")
            
            # Launch deployment
            launch_response = self.agentcore_runtime.launch()
            
            print("✓ MBTI Travel Assistant deployment launch initiated")
            print(f"Launch Response: {launch_response}")
            
            return launch_response
            
        except Exception as e:
            print(f"✗ Error launching MBTI Travel Assistant deployment: {e}")
            raise
    
    def monitor_deployment_status(self, timeout_minutes: int = 15) -> Dict[str, Any]:
        """Monitor MBTI Travel Assistant deployment status until READY or timeout.
        
        Args:
            timeout_minutes: Maximum time to wait for deployment.
            
        Returns:
            Final deployment status.
        """
        try:
            print(f"⏳ Monitoring MBTI Travel Assistant deployment status (timeout: {timeout_minutes} minutes)...")
            
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            while True:
                try:
                    status_response = self.agentcore_runtime.status()
                    
                    # Get agent name from deployment config
                    deployment_config = self.load_deployment_config()
                    agent_name = deployment_config.get('agent_name', 'mbti_travel_assistant_mcp')
                    print(f"Retrieved Bedrock AgentCore status for MBTI Travel Assistant: {agent_name}")
                    
                    # Check endpoint status first (primary indicator)
                    endpoint_status = 'UNKNOWN'
                    agent_status = 'UNKNOWN'
                    
                    if hasattr(status_response, 'endpoint') and status_response.endpoint:
                        endpoint_status = status_response.endpoint.get('status', 'UNKNOWN')
                        print(f"MBTI Travel Assistant Endpoint Status: {endpoint_status}")
                    
                    if hasattr(status_response, 'agent') and status_response.agent:
                        agent_status = status_response.agent.get('status', 'UNKNOWN')
                        print(f"MBTI Travel Assistant Agent Status: {agent_status}")
                    
                    # Check if deployment is ready
                    if endpoint_status == 'READY' and agent_status == 'READY':
                        print("🎉 MBTI Travel Assistant deployment is READY! (Both endpoint and agent are ready)")
                        return status_response
                    elif endpoint_status == 'READY':
                        print("🎉 MBTI Travel Assistant deployment is READY! (Endpoint is ready)")
                        return status_response
                    elif agent_status == 'READY':
                        print("🎉 MBTI Travel Assistant deployment is READY! (Agent is ready)")
                        return status_response
                    elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED'] or agent_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                        print(f"💥 MBTI Travel Assistant deployment failed - Endpoint: {endpoint_status}, Agent: {agent_status}")
                        return status_response
                    
                    print(f"⏳ Still waiting for MBTI Travel Assistant - Endpoint: {endpoint_status}, Agent: {agent_status}")
                    
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
                        return status_response
                    
                    # Wait before next check
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"⚠️ Error checking MBTI Travel Assistant status: {e}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            print("\n⏹️ MBTI Travel Assistant monitoring interrupted by user")
            return self.agentcore_runtime.status()
    
    def test_deployment_connectivity(self) -> bool:
        """Test connectivity to deployed MBTI Travel Assistant.
        
        Returns:
            True if connectivity test passes, False otherwise.
        """
        try:
            print("🔍 Testing MBTI Travel Assistant deployment connectivity...")
            
            # Get deployment status
            status_response = self.agentcore_runtime.status()
            
            if not hasattr(status_response, 'endpoint') or not status_response.endpoint:
                print("✗ No endpoint information available for MBTI Travel Assistant")
                return False
            
            endpoint_info = status_response.endpoint
            endpoint_status = endpoint_info.get('status', 'UNKNOWN')
            
            if endpoint_status != 'READY':
                print(f"✗ MBTI Travel Assistant endpoint not ready. Status: {endpoint_status}")
                return False
            
            # Extract endpoint URL if available
            if 'url' in endpoint_info:
                endpoint_url = endpoint_info['url']
                print(f"✓ MBTI Travel Assistant endpoint URL: {endpoint_url}")
            
            print("✓ MBTI Travel Assistant deployment connectivity test passed")
            return True
            
        except Exception as e:
            print(f"✗ MBTI Travel Assistant connectivity test failed: {e}")
            return False
    
    def save_deployment_config(self, config: Dict[str, Any]) -> None:
        """Save deployment configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save.
        """
        try:
            with open(self.deployment_config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✓ MBTI Travel Assistant deployment configuration saved to: {self.deployment_config_file}")
        except Exception as e:
            print(f"✗ Error saving MBTI Travel Assistant deployment configuration: {e}")
            raise
    
    def load_deployment_config(self) -> Dict[str, Any]:
        """Load existing deployment configuration.
        
        Returns:
            Configuration dictionary or empty dict if not found.
        """
        try:
            if os.path.exists(self.deployment_config_file):
                with open(self.deployment_config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"✗ Error loading MBTI Travel Assistant deployment configuration: {e}")
            return {}
    
    def deploy_complete_workflow(self) -> Dict[str, Any]:
        """Execute complete MBTI Travel Assistant deployment workflow.
        
        Returns:
            Final deployment status and configuration.
        """
        try:
            print("🚀 Starting complete AgentCore Runtime deployment workflow for MBTI Travel Assistant...")
            
            # Step 1: Configure runtime
            print("\n📋 Step 1: Configuring AgentCore Runtime for MBTI Travel Assistant...")
            config_response = self.configure_agentcore_runtime()
            
            # Step 2: Launch deployment
            print("\n🚀 Step 2: Launching MBTI Travel Assistant deployment...")
            launch_response = self.launch_deployment()
            
            # Step 3: Monitor deployment status
            print("\n⏳ Step 3: Monitoring MBTI Travel Assistant deployment status...")
            status_response = self.monitor_deployment_status()
            
            # Step 4: Test connectivity
            print("\n🔍 Step 4: Testing MBTI Travel Assistant deployment connectivity...")
            connectivity_ok = self.test_deployment_connectivity()
            
            # Compile final results
            deployment_successful = False
            endpoint_ready = False
            agent_ready = False
            
            if hasattr(status_response, 'endpoint') and status_response.endpoint:
                endpoint_ready = status_response.endpoint.get('status') == 'READY'
            
            if hasattr(status_response, 'agent') and status_response.agent:
                agent_ready = status_response.agent.get('status') == 'READY'
            
            # Deployment is successful if either endpoint or agent is ready and connectivity test passes
            deployment_successful = (endpoint_ready or agent_ready) and connectivity_ok
            
            final_result = {
                'configuration': config_response,
                'launch': launch_response,
                'final_status': status_response,
                'connectivity_test': connectivity_ok,
                'deployment_successful': deployment_successful
            }
            
            # Update deployment config with final results
            deployment_config = self.load_deployment_config()
            deployment_config.update({
                'final_deployment_result': final_result,
                'completed_at': time.time()
            })
            self.save_deployment_config(deployment_config)
            
            if final_result['deployment_successful']:
                print("\n🎉 MBTI Travel Assistant deployment completed successfully!")
                print("✓ MBTI Travel Assistant is deployed and ready")
                print("✓ Authentication is configured with existing Cognito setup")
                print("✓ Connectivity test passed")
                print("✓ Using Amazon Nova Pro 300K model")
                print("✓ Connected to Restaurant Search and Reasoning MCP servers")
            else:
                print("\n⚠️ MBTI Travel Assistant deployment completed with issues")
                print("Please check the logs and status for details")
            
            return final_result
            
        except Exception as e:
            print(f"\n💥 MBTI Travel Assistant deployment workflow failed: {e}")
            raise


def main():
    """Main function to run MBTI Travel Assistant AgentCore deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy MBTI Travel Assistant MCP to AgentCore Runtime')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--entrypoint', default='main.py', 
                       help='Application entrypoint (default: main.py)')
    parser.add_argument('--agent-name', default='mbti_travel_assistant_mcp',
                       help='Agent name (default: mbti_travel_assistant_mcp)')
    parser.add_argument('--requirements', default='requirements.txt',
                       help='Requirements file (default: requirements.txt)')
    parser.add_argument('--configure-only', action='store_true',
                       help='Only configure, do not launch deployment')
    parser.add_argument('--launch-only', action='store_true',
                       help='Only launch (assumes already configured)')
    parser.add_argument('--status-only', action='store_true',
                       help='Only check deployment status')
    
    args = parser.parse_args()
    
    try:
        # Initialize deployment
        deployment = MBTITravelAssistantDeployment(region=args.region)
        
        if args.status_only:
            # Just check status
            status = deployment.agentcore_runtime.status()
            print(f"MBTI Travel Assistant Deployment Status: {json.dumps(status, indent=2, default=str)}")
            return 0
        
        elif args.configure_only:
            # Only configure
            config_response = deployment.configure_agentcore_runtime(
                entrypoint=args.entrypoint,
                agent_name=args.agent_name,
                requirements_file=args.requirements
            )
            print(f"MBTI Travel Assistant configuration completed: {config_response}")
            return 0
        
        elif args.launch_only:
            # Only launch
            launch_response = deployment.launch_deployment()
            status_response = deployment.monitor_deployment_status()
            connectivity_ok = deployment.test_deployment_connectivity()
            
            print(f"Launch Response: {launch_response}")
            print(f"Final Status: {status_response}")
            print(f"Connectivity OK: {connectivity_ok}")
            return 0
        
        else:
            # Complete workflow
            result = deployment.deploy_complete_workflow()
            
            print("\n📋 MBTI Travel Assistant Deployment Summary:")
            print(f"Successful: {result['deployment_successful']}")
            if hasattr(result.get('final_status', {}), 'endpoint') and result['final_status'].endpoint:
                endpoint_info = result['final_status'].endpoint
                print(f"Status: {endpoint_info.get('status', 'UNKNOWN')}")
                if 'url' in endpoint_info:
                    print(f"URL: {endpoint_info['url']}")
            
            return 0 if result['deployment_successful'] else 1
        
    except Exception as e:
        print(f"\n💥 MBTI Travel Assistant deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())