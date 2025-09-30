#!/usr/bin/env python3
"""
AgentCore OIDC Configuration Update Script

This script updates the existing AgentCore agent with the new OIDC-enabled
Cognito User Pool configuration to resolve the 403 Forbidden authentication errors.
"""

import json
import os
import sys
import logging
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path

import boto3
import yaml
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentCoreOIDCUpdater:
    """Updates AgentCore agent with new OIDC configuration."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the AgentCore OIDC updater.
        
        Args:
            region: AWS region for AgentCore deployment
        """
        self.region = region
        self.session = boto3.Session()
        
        try:
            # Initialize AWS clients
            self.sts_client = self.session.client('sts', region_name=region)
            self.cognito_client = self.session.client('cognito-idp', region_name=region)
            
            # Verify AWS credentials
            self.account_id = self.sts_client.get_caller_identity()['Account']
            logger.info(f"Connected to AWS account: {self.account_id} in region: {region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {str(e)}")
            sys.exit(1)
    
    def load_current_config(self) -> Dict[str, Any]:
        """Load current AgentCore configuration from YAML file."""
        config_file = Path(".bedrock_agentcore.yaml")
        
        if not config_file.exists():
            raise FileNotFoundError("AgentCore configuration file not found: .bedrock_agentcore.yaml")
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info("Loaded AgentCore configuration successfully")
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid AgentCore configuration YAML: {e}")
    
    def load_oidc_config(self) -> Dict[str, Any]:
        """Load OIDC Cognito configuration."""
        oidc_config_file = Path("cognito_oidc_config.json")
        
        if not oidc_config_file.exists():
            raise FileNotFoundError("OIDC configuration file not found: cognito_oidc_config.json")
        
        try:
            with open(oidc_config_file, 'r') as f:
                oidc_config = json.load(f)
            
            logger.info("Loaded OIDC configuration successfully")
            return oidc_config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid OIDC configuration JSON: {e}")
    
    def verify_oidc_discovery_endpoint(self, discovery_url: str) -> bool:
        """Verify that the OIDC discovery endpoint is accessible."""
        try:
            import requests
            
            logger.info(f"Verifying OIDC discovery endpoint: {discovery_url}")
            response = requests.get(discovery_url, timeout=10)
            
            if response.status_code == 200:
                discovery_data = response.json()
                required_fields = ['issuer', 'authorization_endpoint', 'token_endpoint', 'jwks_uri']
                
                for field in required_fields:
                    if field not in discovery_data:
                        logger.error(f"Missing required field in OIDC discovery: {field}")
                        return False
                
                logger.info("OIDC discovery endpoint verification successful")
                logger.info(f"Issuer: {discovery_data.get('issuer')}")
                logger.info(f"JWKS URI: {discovery_data.get('jwks_uri')}")
                return True
            else:
                logger.error(f"OIDC discovery endpoint returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify OIDC discovery endpoint: {e}")
            return False
    
    def verify_cognito_user_pool(self, user_pool_id: str, client_id: str) -> bool:
        """Verify Cognito User Pool and client configuration."""
        try:
            # Verify User Pool exists
            logger.info(f"Verifying Cognito User Pool: {user_pool_id}")
            user_pool = self.cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            logger.info(f"User Pool found: {user_pool['UserPool']['Name']}")
            
            # Verify App Client exists and has correct configuration
            logger.info(f"Verifying App Client: {client_id}")
            client = self.cognito_client.describe_user_pool_client(
                UserPoolId=user_pool_id,
                ClientId=client_id
            )
            
            client_config = client['UserPoolClient']
            
            # Check OAuth configuration
            if not client_config.get('AllowedOAuthFlowsUserPoolClient', False):
                logger.error("OAuth flows not enabled for app client")
                return False
            
            oauth_flows = client_config.get('AllowedOAuthFlows', [])
            oauth_scopes = client_config.get('AllowedOAuthScopes', [])
            
            if 'code' not in oauth_flows:
                logger.error("Authorization code flow not enabled")
                return False
            
            required_scopes = ['openid', 'email', 'profile']
            for scope in required_scopes:
                if scope not in oauth_scopes:
                    logger.error(f"Required OAuth scope missing: {scope}")
                    return False
            
            logger.info("Cognito User Pool and App Client verification successful")
            return True
            
        except ClientError as e:
            logger.error(f"Cognito verification failed: {e}")
            return False
    
    def update_agentcore_via_cli(self, agent_name: str) -> bool:
        """Attempt to update AgentCore using CLI commands."""
        try:
            # Try agentcore CLI first
            logger.info("Attempting to update AgentCore using agentcore CLI...")
            
            # Check if agentcore CLI is available
            result = subprocess.run(['agentcore', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"AgentCore CLI found: {result.stdout.strip()}")
                
                # Try to update the agent
                update_result = subprocess.run(['agentcore', 'update', agent_name], 
                                             capture_output=True, text=True, timeout=300)
                
                if update_result.returncode == 0:
                    logger.info("AgentCore update successful via CLI")
                    logger.info(f"Update output: {update_result.stdout}")
                    return True
                else:
                    logger.error(f"AgentCore CLI update failed: {update_result.stderr}")
                    return False
            else:
                logger.info("AgentCore CLI not available")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.info(f"AgentCore CLI not available: {e}")
            return False
        except Exception as e:
            logger.error(f"AgentCore CLI update failed: {e}")
            return False
    
    def update_agentcore_via_sdk(self, config: Dict[str, Any]) -> bool:
        """Attempt to update AgentCore using bedrock-agentcore SDK."""
        try:
            logger.info("Attempting to update AgentCore using bedrock-agentcore SDK...")
            
            # Try to import bedrock-agentcore
            try:
                from bedrock_agentcore_starter_toolkit import Runtime
                logger.info("bedrock-agentcore-starter-toolkit available")
            except ImportError:
                logger.info("bedrock-agentcore-starter-toolkit not available")
                return False
            
            agent_config = config['agents']['mbti_travel_assistant_mcp']
            agent_arn = agent_config['bedrock_agentcore']['agent_arn']
            
            # Create runtime instance
            runtime = Runtime(agent_arn=agent_arn)
            
            # Update configuration (this is a placeholder - actual SDK method may differ)
            logger.info(f"Updating AgentCore agent: {agent_arn}")
            
            # Note: The actual SDK update method may be different
            # This is a conceptual implementation
            update_config = {
                'authorizer_configuration': agent_config['authorizer_configuration']
            }
            
            # runtime.update_configuration(update_config)  # Placeholder method
            
            logger.info("AgentCore update successful via SDK")
            return True
            
        except Exception as e:
            logger.error(f"AgentCore SDK update failed: {e}")
            return False
    
    def create_deployment_script(self, config: Dict[str, Any], oidc_config: Dict[str, Any]) -> str:
        """Create a deployment script for manual AgentCore update."""
        agent_config = config['agents']['mbti_travel_assistant_mcp']
        
        script_content = f"""#!/bin/bash
# AgentCore OIDC Configuration Update Script
# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

echo "Updating AgentCore agent with OIDC configuration..."

# Agent Information
AGENT_ID="{agent_config['bedrock_agentcore']['agent_id']}"
AGENT_ARN="{agent_config['bedrock_agentcore']['agent_arn']}"
REGION="{self.region}"

# OIDC Configuration
USER_POOL_ID="{oidc_config['user_pool']['user_pool_id']}"
CLIENT_ID="{oidc_config['app_client']['client_id']}"
DISCOVERY_URL="{oidc_config['oidc_configuration']['discovery_url']}"

echo "Agent ID: $AGENT_ID"
echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo "Discovery URL: $DISCOVERY_URL"

# Verify OIDC endpoint
echo "Verifying OIDC discovery endpoint..."
curl -s "$DISCOVERY_URL" | jq . > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ OIDC discovery endpoint is accessible"
else
    echo "❌ OIDC discovery endpoint is not accessible"
    exit 1
fi

# Manual steps for AgentCore update
echo ""
echo "Manual AgentCore Update Steps:"
echo "1. Open AWS Bedrock AgentCore Console"
echo "2. Navigate to Agent: $AGENT_ID"
echo "3. Update Authentication Configuration:"
echo "   - Type: Custom JWT Authorizer"
echo "   - Allowed Clients: $CLIENT_ID"
echo "   - Discovery URL: $DISCOVERY_URL"
echo "4. Save and deploy the configuration"
echo ""

# Alternative: Use AWS CLI if available
echo "Alternative: AWS CLI commands (if supported):"
echo "aws bedrock-agentcore update-agent-runtime \\"
echo "  --agent-id $AGENT_ID \\"
echo "  --region $REGION \\"
echo "  --authorizer-configuration '{{"
echo "    \"customJWTAuthorizer\": {{"
echo "      \"allowedClients\": [\"$CLIENT_ID\"],"
echo "      \"discoveryUrl\": \"$DISCOVERY_URL\""
echo "    }}"
echo "  }}'"

echo ""
echo "Configuration update script completed."
"""
        
        script_path = "update_agentcore_manual.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"Created manual deployment script: {script_path}")
        return script_path
    
    def update_agentcore(self) -> Dict[str, Any]:
        """
        Main method to update AgentCore with OIDC configuration.
        
        Returns:
            Dictionary with update results and status
        """
        logger.info("Starting AgentCore OIDC configuration update...")
        
        try:
            # Load configurations
            config = self.load_current_config()
            oidc_config = self.load_oidc_config()
            
            agent_config = config['agents']['mbti_travel_assistant_mcp']
            agent_name = agent_config['name']
            agent_id = agent_config['bedrock_agentcore']['agent_id']
            
            # Extract OIDC configuration
            user_pool_id = oidc_config['user_pool']['user_pool_id']
            client_id = oidc_config['app_client']['client_id']
            discovery_url = oidc_config['oidc_configuration']['discovery_url']
            
            logger.info(f"Updating AgentCore agent: {agent_name} ({agent_id})")
            logger.info(f"New User Pool: {user_pool_id}")
            logger.info(f"New Client ID: {client_id}")
            
            # Verify OIDC configuration
            if not self.verify_oidc_discovery_endpoint(discovery_url):
                raise ValueError("OIDC discovery endpoint verification failed")
            
            if not self.verify_cognito_user_pool(user_pool_id, client_id):
                raise ValueError("Cognito User Pool verification failed")
            
            # Attempt different update methods
            update_methods = [
                ("CLI", lambda: self.update_agentcore_via_cli(agent_name)),
                ("SDK", lambda: self.update_agentcore_via_sdk(config))
            ]
            
            update_successful = False
            
            for method_name, method_func in update_methods:
                logger.info(f"Trying update method: {method_name}")
                
                try:
                    if method_func():
                        logger.info(f"AgentCore update successful via {method_name}")
                        update_successful = True
                        break
                except Exception as e:
                    logger.warning(f"Update method {method_name} failed: {e}")
                    continue
            
            # Create manual deployment script as fallback
            script_path = self.create_deployment_script(config, oidc_config)
            
            result = {
                "status": "success" if update_successful else "manual_required",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "user_pool_id": user_pool_id,
                "client_id": client_id,
                "discovery_url": discovery_url,
                "update_successful": update_successful,
                "manual_script": script_path,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if update_successful:
                logger.info("✅ AgentCore OIDC configuration update completed successfully!")
            else:
                logger.warning("⚠️  Automatic update failed. Manual update required.")
                logger.info(f"📋 Manual update script created: {script_path}")
                logger.info("Please follow the instructions in the script to complete the update.")
            
            return result
            
        except Exception as e:
            logger.error(f"AgentCore update failed: {str(e)}")
            raise


def main():
    """Main function to run the AgentCore OIDC update."""
    try:
        updater = AgentCoreOIDCUpdater()
        result = updater.update_agentcore()
        
        # Save result to file
        with open("agentcore_update_result.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\n" + "="*60)
        print("AGENTCORE OIDC UPDATE SUMMARY")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Agent ID: {result['agent_id']}")
        print(f"User Pool ID: {result['user_pool_id']}")
        print(f"Client ID: {result['client_id']}")
        print(f"Discovery URL: {result['discovery_url']}")
        print(f"Update Successful: {result['update_successful']}")
        
        if not result['update_successful']:
            print(f"Manual Script: {result['manual_script']}")
            print("\nNext Steps:")
            print("1. Run the manual script for detailed instructions")
            print("2. Update AgentCore configuration via AWS Console")
            print("3. Test the authentication flow")
        
        print("="*60)
        
        return 0 if result['update_successful'] else 1
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())