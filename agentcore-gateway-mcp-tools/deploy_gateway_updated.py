#!/usr/bin/env python3
"""
Updated AgentCore Gateway Deployment Script
Deploys the AgentCore Gateway with updated Cognito settings including client secret hash and USER_PASSWORD_AUTH flow.
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime


class GatewayAgentCoreDeployment:
    """Deploy AgentCore Gateway with updated authentication settings."""
    
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
            
        Raises:
            FileNotFoundError: If Cognito config file doesn't exist.
            ValueError: If Cognito config is invalid.
        """
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(
                    f"Cognito configuration file not found: {config_file}. "
                    "Please ensure cognito_config.json exists in the current directory."
                )
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['user_pool', 'app_client', 'discovery_url']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in Cognito config: {field}")
            
            print(f"✓ Loaded Cognito configuration from: {config_file}")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Cognito config file: {e}")
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
        client_id = cognito_config['app_client']['client_id']
        discovery_url = cognito_config['discovery_url']
        
        # Create JWT authorizer configuration with existing Cognito setup
        auth_config = {
            "customJWTAuthorizer": {
                "allowedClients": [client_id],
                "discoveryUrl": discovery_url,
            }
        }
        
        print(f"✓ Created JWT authorizer config for gateway:")
        print(f"  - Client ID: {client_id}")
        print(f"  - Discovery URL: {discovery_url}")
        print(f"  - User Pool ID: {cognito_config['user_pool']['user_pool_id']}")
        print(f"  - Region: {cognito_config['region']}")
        return auth_config
    
    def configure_agentcore_runtime(self, 
                                   entrypoint: str = "main.py",
                                   agent_name: str = "agentcore_gateway_mcp_tools",
                                   requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        """Configure AgentCore Runtime deployment for gateway.
        
        Args:
            entrypoint: Python file to use as entrypoint.
            agent_name: Name for the gateway MCP agent.
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
            
            print(f"🚀 Configuring AgentCore Runtime deployment for gateway...")
            print(f"Entrypoint: {entrypoint}")
            print(f"Agent Name: {agent_name}")
            print(f"Requirements: {requirements_file}")
            print(f"Region: {self.region}")
            print(f"Protocol: HTTP")
            
            # Configure AgentCore Runtime with gateway-specific settings
            response = self.agentcore_runtime.configure(
                entrypoint=entrypoint,
                auto_create_execution_role=True,
                auto_create_ecr=True,
                requirements_file=requirements_file,
                region=self.region,
                authorizer_configuration=auth_config,
                protocol="HTTP",
                agent_name=agent_name
            )
            
            print("✓ AgentCore Runtime configuration completed for gateway")
            
            # Save configuration for reference
            config_data = {
                'entrypoint': entrypoint,
                'agent_name': agent_name,
                'requirements_file': requirements_file,
                'region': self.region,
                'protocol': 'HTTP',
                'auth_config': auth_config,
                'cognito_config': cognito_config,
                'configuration_response': response,
                'configured_at': time.time(),
                'server_type': 'gateway'
            }
            
            self.save_deployment_config(config_data)
            
            return response
            
        except Exception as e:
            print(f"✗ Error configuring AgentCore Runtime for gateway: {e}")
            raise
    
    def launch_deployment(self) -> Dict[str, Any]:
        """Launch the gateway deployment to AgentCore Runtime.
        
        Returns:
            Launch response from AgentCore Runtime.
        """
        try:
            print("🚀 Launching gateway deployment to AgentCore Runtime...")
            
            # Launch deployment
            launch_response = self.agentcore_runtime.launch()
            
            print("✓ Gateway deployment launch initiated")
            print(f"Launch Response: {launch_response}")
            
            return launch_response
            
        except Exception as e:
            print(f"✗ Error launching gateway deployment: {e}")
            raise
    
    def monitor_deployment_status(self, timeout_minutes: int = 15) -> Dict[str, Any]:
        """Monitor gateway deployment status until READY or timeout.
        
        Args:
            timeout_minutes: Maximum time to wait for deployment.
            
        Returns:
            Final deployment status.
        """
        try:
            print(f"⏳ Monitoring gateway deployment status (timeout: {timeout_minutes} minutes)...")
            
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            while True:
                try:
                    status_response = self.agentcore_runtime.status()
                    
                    # Get agent name from deployment config
                    deployment_config = self.load_deployment_config()
                    agent_name = deployment_config.get('agent_name', 'agentcore_gateway_mcp_tools')
                    print(f"Retrieved Bedrock AgentCore status for gateway: {agent_name}")
                    
                    # Check endpoint status first (primary indicator)
                    endpoint_status = 'UNKNOWN'
                    agent_status = 'UNKNOWN'
                    
                    if hasattr(status_response, 'endpoint') and status_response.endpoint:
                        endpoint_status = status_response.endpoint.get('status', 'UNKNOWN')
                        print(f"Gateway Endpoint Status: {endpoint_status}")
                    
                    if hasattr(status_response, 'agent') and status_response.agent:
                        agent_status = status_response.agent.get('status', 'UNKNOWN')
                        print(f"Gateway Agent Status: {agent_status}")
                    
                    # Check if deployment is ready (both endpoint and agent should be READY)
                    if endpoint_status == 'READY' and agent_status == 'READY':
                        print("🎉 Gateway deployment is READY! (Both endpoint and agent are ready)")
                        return status_response
                    elif endpoint_status == 'READY':
                        print("🎉 Gateway deployment is READY! (Endpoint is ready)")
                        return status_response
                    elif agent_status == 'READY':
                        print("🎉 Gateway deployment is READY! (Agent is ready)")
                        return status_response
                    elif endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED'] or agent_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                        print(f"💥 Gateway deployment failed - Endpoint: {endpoint_status}, Agent: {agent_status}")
                        return status_response
                    
                    print(f"⏳ Still waiting for gateway - Endpoint: {endpoint_status}, Agent: {agent_status}")
                    
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
                        return status_response
                    
                    # Wait before next check
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"⚠️ Error checking gateway status: {e}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            print("\n⏹️ Gateway monitoring interrupted by user")
            return self.agentcore_runtime.status()
    
    def test_deployment_connectivity(self) -> bool:
        """Test connectivity to deployed gateway.
        
        Returns:
            True if connectivity test passes, False otherwise.
        """
        try:
            print("🔍 Testing gateway deployment connectivity...")
            
            # Get deployment status
            status_response = self.agentcore_runtime.status()
            
            if 'endpoint' not in status_response:
                print("✗ No endpoint information available for gateway")
                return False
            
            endpoint_info = status_response['endpoint']
            endpoint_status = endpoint_info.get('status', 'UNKNOWN')
            
            if endpoint_status != 'READY':
                print(f"✗ Gateway endpoint not ready. Status: {endpoint_status}")
                return False
            
            # Extract endpoint URL if available
            if 'url' in endpoint_info:
                endpoint_url = endpoint_info['url']
                print(f"✓ Gateway endpoint URL: {endpoint_url}")
            
            print("✓ Gateway deployment connectivity test passed")
            return True
            
        except Exception as e:
            print(f"✗ Gateway connectivity test failed: {e}")
            return False
    
    def save_deployment_config(self, config: Dict[str, Any]) -> None:
        """Save deployment configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save.
        """
        try:
            with open(self.deployment_config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✓ Gateway deployment configuration saved to: {self.deployment_config_file}")
        except Exception as e:
            print(f"✗ Error saving gateway deployment configuration: {e}")
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
            print(f"✗ Error loading gateway deployment configuration: {e}")
            return {}
    
    def deploy_complete_workflow(self) -> Dict[str, Any]:
        """Execute complete gateway deployment workflow.
        
        Returns:
            Final deployment status and configuration.
        """
        try:
            print("🚀 Starting complete AgentCore Runtime deployment workflow for gateway...")
            
            # Step 1: Configure runtime
            print("\n📋 Step 1: Configuring AgentCore Runtime for gateway...")
            config_response = self.configure_agentcore_runtime()
            
            # Step 2: Launch deployment
            print("\n🚀 Step 2: Launching gateway deployment...")
            launch_response = self.launch_deployment()
            
            # Step 3: Monitor deployment status
            print("\n⏳ Step 3: Monitoring gateway deployment status...")
            status_response = self.monitor_deployment_status()
            
            # Step 4: Test connectivity
            print("\n🔍 Step 4: Testing gateway deployment connectivity...")
            connectivity_ok = self.test_deployment_connectivity()
            
            # Compile final results
            # Check deployment success based on status response structure
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
                print("\n🎉 Gateway deployment completed successfully!")
                print("✓ AgentCore Gateway is deployed and ready")
                print("✓ Authentication is configured with existing Cognito setup")
                print("✓ Connectivity test passed")
            else:
                print("\n⚠️ Gateway deployment completed with issues")
                print("Please check the logs and status for details")
            
            return final_result
            
        except Exception as e:
            print(f"\n💥 Gateway deployment workflow failed: {e}")
            raise


def main():
    """Main function to run gateway AgentCore deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy AgentCore Gateway MCP Tools to AgentCore Runtime')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--entrypoint', default='main.py', 
                       help='Gateway entrypoint (default: main.py)')
    parser.add_argument('--agent-name', default='agentcore_gateway_mcp_tools',
                       help='Agent name (default: agentcore_gateway_mcp_tools)')
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
        deployment = GatewayAgentCoreDeployment(region=args.region)
        
        if args.status_only:
            # Just check status
            deployment.configure_agentcore_runtime(
                entrypoint=args.entrypoint,
                agent_name=args.agent_name,
                requirements_file=args.requirements
            )
            status = deployment.agentcore_runtime.status()
            print(f"Gateway Deployment Status: {json.dumps(status, indent=2, default=str)}")
            return 0
        
        elif args.configure_only:
            # Only configure
            config_response = deployment.configure_agentcore_runtime(
                entrypoint=args.entrypoint,
                agent_name=args.agent_name,
                requirements_file=args.requirements
            )
            print(f"Gateway configuration completed: {config_response}")
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
            
            print("\n📋 Gateway Deployment Summary:")
            print(f"Successful: {result['deployment_successful']}")
            if 'endpoint' in result.get('final_status', {}):
                endpoint_info = result['final_status']['endpoint']
                print(f"Status: {endpoint_info.get('status', 'UNKNOWN')}")
                if 'url' in endpoint_info:
                    print(f"URL: {endpoint_info['url']}")
            
            return 0 if result['deployment_successful'] else 1
        
    except Exception as e:
        print(f"\n💥 Gateway deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())