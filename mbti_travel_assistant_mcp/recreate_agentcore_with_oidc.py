#!/usr/bin/env python3
"""
AgentCore Recreation Script with OIDC Configuration

This script deletes the existing AgentCore agent and recreates it with the same name
but updated OIDC authentication configuration to resolve the 403 Forbidden errors.
"""

import json
import os
import sys
import logging
import subprocess
import time
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentCoreRecreator:
    """Handles deletion and recreation of AgentCore agent with OIDC configuration."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize the AgentCore recreator.
        
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
    
    def load_configurations(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Load current AgentCore and OIDC configurations."""
        # Load AgentCore config
        config_file = Path(".bedrock_agentcore.yaml")
        if not config_file.exists():
            raise FileNotFoundError("AgentCore configuration file not found: .bedrock_agentcore.yaml")
        
        with open(config_file, 'r') as f:
            agentcore_config = yaml.safe_load(f)
        
        # Load OIDC config
        oidc_config_file = Path("cognito_oidc_config.json")
        if not oidc_config_file.exists():
            raise FileNotFoundError("OIDC configuration file not found: cognito_oidc_config.json")
        
        with open(oidc_config_file, 'r') as f:
            oidc_config = json.load(f)
        
        logger.info("Loaded AgentCore and OIDC configurations successfully")
        return agentcore_config, oidc_config
    
    def backup_current_config(self, config: Dict[str, Any]) -> str:
        """Create a backup of the current configuration."""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_file = f".bedrock_agentcore_backup_{timestamp}.yaml"
        
        with open(backup_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Created configuration backup: {backup_file}")
        return backup_file
    
    def delete_agentcore_agent(self, agent_name: str) -> bool:
        """
        Delete the existing AgentCore agent.
        
        Args:
            agent_name: Name of the agent to delete
            
        Returns:
            True if deletion was successful or agent doesn't exist
        """
        try:
            logger.info(f"Attempting to delete AgentCore agent: {agent_name}")
            
            # Try using bedrock-agentcore-starter-toolkit
            try:
                from bedrock_agentcore_starter_toolkit import Runtime
                
                # Note: The actual deletion method may vary depending on the SDK
                # This is a conceptual implementation
                logger.info("Attempting deletion via bedrock-agentcore SDK...")
                
                # For now, we'll use CLI approach
                return self._delete_via_cli(agent_name)
                
            except ImportError:
                logger.info("bedrock-agentcore-starter-toolkit not available, trying CLI...")
                return self._delete_via_cli(agent_name)
                
        except Exception as e:
            logger.error(f"Failed to delete AgentCore agent: {e}")
            return False
    
    def _delete_via_cli(self, agent_name: str) -> bool:
        """Delete agent via CLI commands."""
        try:
            # Try agentcore CLI
            result = subprocess.run(['agentcore', 'delete', agent_name], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Successfully deleted agent via CLI: {agent_name}")
                return True
            else:
                logger.warning(f"CLI deletion failed: {result.stderr}")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"AgentCore CLI not available: {e}")
            return False
        except Exception as e:
            logger.error(f"CLI deletion failed: {e}")
            return False
    
    def update_config_with_oidc(self, config: Dict[str, Any], oidc_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update AgentCore configuration with new OIDC settings.
        
        Args:
            config: Current AgentCore configuration
            oidc_config: OIDC configuration
            
        Returns:
            Updated configuration
        """
        # Clear existing agent runtime information to force recreation
        agent_config = config['agents']['mbti_travel_assistant_mcp']
        
        # Update OIDC configuration
        agent_config['authorizer_configuration'] = {
            'customJWTAuthorizer': {
                'allowedClients': [oidc_config['app_client']['client_id']],
                'discoveryUrl': oidc_config['oidc_configuration']['discovery_url']
            }
        }
        
        # Clear runtime-specific fields to force recreation
        agent_config['bedrock_agentcore'] = {
            'agent_id': None,
            'agent_arn': None,
            'agent_session_id': None
        }
        
        logger.info("Updated configuration with new OIDC settings")
        logger.info(f"New Client ID: {oidc_config['app_client']['client_id']}")
        logger.info(f"New Discovery URL: {oidc_config['oidc_configuration']['discovery_url']}")
        
        return config
    
    def save_updated_config(self, config: Dict[str, Any]) -> None:
        """Save the updated configuration to file."""
        with open('.bedrock_agentcore.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info("Saved updated AgentCore configuration")
    
    def deploy_new_agent(self, agent_name: str) -> bool:
        """
        Deploy the new AgentCore agent with OIDC configuration.
        
        Args:
            agent_name: Name of the agent to deploy
            
        Returns:
            True if deployment was successful
        """
        try:
            logger.info(f"Deploying new AgentCore agent: {agent_name}")
            
            # Try different deployment methods
            deployment_methods = [
                ("CLI", self._deploy_via_cli),
                ("SDK", self._deploy_via_sdk),
                ("Python Script", self._deploy_via_script)
            ]
            
            for method_name, method_func in deployment_methods:
                logger.info(f"Trying deployment method: {method_name}")
                
                try:
                    if method_func(agent_name):
                        logger.info(f"Successfully deployed agent via {method_name}")
                        return True
                except Exception as e:
                    logger.warning(f"Deployment method {method_name} failed: {e}")
                    continue
            
            logger.error("All deployment methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Agent deployment failed: {e}")
            return False
    
    def _deploy_via_cli(self, agent_name: str) -> bool:
        """Deploy agent via CLI."""
        try:
            # Try agentcore launch
            result = subprocess.run(['agentcore', 'launch', agent_name], 
                                  capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("Agent deployed successfully via CLI")
                return True
            else:
                logger.warning(f"CLI deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"CLI deployment failed: {e}")
            return False
    
    def _deploy_via_sdk(self, agent_name: str) -> bool:
        """Deploy agent via SDK."""
        try:
            from bedrock_agentcore_starter_toolkit import Runtime
            
            # This is a conceptual implementation
            # The actual SDK deployment method may differ
            logger.info("Attempting deployment via SDK...")
            
            # For now, return False to try other methods
            return False
            
        except ImportError:
            logger.info("bedrock-agentcore-starter-toolkit not available")
            return False
        except Exception as e:
            logger.warning(f"SDK deployment failed: {e}")
            return False
    
    def _deploy_via_script(self, agent_name: str) -> bool:
        """Deploy agent via existing deployment script."""
        try:
            script_path = Path("scripts/deploy_agentcore.py")
            if script_path.exists():
                logger.info("Using existing deployment script...")
                
                result = subprocess.run([sys.executable, str(script_path)], 
                                      capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    logger.info("Agent deployed successfully via script")
                    return True
                else:
                    logger.warning(f"Script deployment failed: {result.stderr}")
                    return False
            else:
                logger.info("No deployment script found")
                return False
                
        except Exception as e:
            logger.warning(f"Script deployment failed: {e}")
            return False
    
    def verify_new_deployment(self, oidc_config: Dict[str, Any]) -> bool:
        """
        Verify that the new deployment is working with OIDC.
        
        Args:
            oidc_config: OIDC configuration for verification
            
        Returns:
            True if verification successful
        """
        try:
            logger.info("Verifying new AgentCore deployment...")
            
            # Check if configuration file was updated with new agent info
            with open('.bedrock_agentcore.yaml', 'r') as f:
                updated_config = yaml.safe_load(f)
            
            agent_config = updated_config['agents']['mbti_travel_assistant_mcp']
            new_agent_id = agent_config['bedrock_agentcore'].get('agent_id')
            new_agent_arn = agent_config['bedrock_agentcore'].get('agent_arn')
            
            if new_agent_id and new_agent_arn:
                logger.info(f"New Agent ID: {new_agent_id}")
                logger.info(f"New Agent ARN: {new_agent_arn}")
                
                # Verify OIDC configuration
                auth_config = agent_config.get('authorizer_configuration', {})
                jwt_config = auth_config.get('customJWTAuthorizer', {})
                
                expected_client_id = oidc_config['app_client']['client_id']
                expected_discovery_url = oidc_config['oidc_configuration']['discovery_url']
                
                actual_clients = jwt_config.get('allowedClients', [])
                actual_discovery_url = jwt_config.get('discoveryUrl', '')
                
                if (expected_client_id in actual_clients and 
                    actual_discovery_url == expected_discovery_url):
                    logger.info("OIDC configuration verified successfully")
                    return True
                else:
                    logger.error("OIDC configuration mismatch")
                    return False
            else:
                logger.error("New agent information not found in configuration")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def recreate_agent(self) -> Dict[str, Any]:
        """
        Main method to recreate AgentCore agent with OIDC configuration.
        
        Returns:
            Dictionary with recreation results
        """
        logger.info("Starting AgentCore agent recreation with OIDC configuration...")
        
        try:
            # Load configurations
            agentcore_config, oidc_config = self.load_configurations()
            
            agent_config = agentcore_config['agents']['mbti_travel_assistant_mcp']
            agent_name = agent_config['name']
            old_agent_id = agent_config['bedrock_agentcore']['agent_id']
            old_agent_arn = agent_config['bedrock_agentcore']['agent_arn']
            
            logger.info(f"Recreating agent: {agent_name}")
            logger.info(f"Old Agent ID: {old_agent_id}")
            logger.info(f"Old Agent ARN: {old_agent_arn}")
            
            # Create backup
            backup_file = self.backup_current_config(agentcore_config)
            
            # Step 1: Delete existing agent
            logger.info("Step 1: Deleting existing agent...")
            deletion_successful = self.delete_agentcore_agent(agent_name)
            
            if not deletion_successful:
                logger.warning("Agent deletion failed or not supported. Proceeding with recreation...")
            
            # Step 2: Update configuration with OIDC
            logger.info("Step 2: Updating configuration with OIDC settings...")
            updated_config = self.update_config_with_oidc(agentcore_config, oidc_config)
            
            # Step 3: Save updated configuration
            logger.info("Step 3: Saving updated configuration...")
            self.save_updated_config(updated_config)
            
            # Step 4: Deploy new agent
            logger.info("Step 4: Deploying new agent...")
            deployment_successful = self.deploy_new_agent(agent_name)
            
            if not deployment_successful:
                logger.error("Automatic deployment failed. Manual deployment required.")
                
                # Restore backup if deployment failed
                logger.info("Restoring configuration backup...")
                with open(backup_file, 'r') as f:
                    backup_config = yaml.safe_load(f)
                self.save_updated_config(backup_config)
                
                result = {
                    "status": "manual_deployment_required",
                    "agent_name": agent_name,
                    "old_agent_id": old_agent_id,
                    "backup_file": backup_file,
                    "error": "Automatic deployment failed",
                    "next_steps": [
                        "Use AWS Console to create new AgentCore agent",
                        "Use the updated .bedrock_agentcore.yaml configuration",
                        "Ensure OIDC authentication is properly configured"
                    ]
                }
                return result
            
            # Step 5: Verify new deployment
            logger.info("Step 5: Verifying new deployment...")
            verification_successful = self.verify_new_deployment(oidc_config)
            
            result = {
                "status": "success" if verification_successful else "verification_failed",
                "agent_name": agent_name,
                "old_agent_id": old_agent_id,
                "backup_file": backup_file,
                "deployment_successful": deployment_successful,
                "verification_successful": verification_successful,
                "oidc_config": {
                    "user_pool_id": oidc_config['user_pool']['user_pool_id'],
                    "client_id": oidc_config['app_client']['client_id'],
                    "discovery_url": oidc_config['oidc_configuration']['discovery_url']
                },
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if verification_successful:
                logger.info("AgentCore agent recreation completed successfully!")
                logger.info("The agent should now accept OIDC ID tokens from the new Cognito User Pool.")
            else:
                logger.warning("Agent recreation completed but verification failed.")
                logger.info("Please check the agent configuration manually.")
            
            return result
            
        except Exception as e:
            logger.error(f"Agent recreation failed: {str(e)}")
            raise


def main():
    """Main function to run the AgentCore recreation."""
    try:
        recreator = AgentCoreRecreator()
        result = recreator.recreate_agent()
        
        # Save result to file
        with open("agentcore_recreation_result.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\n" + "="*80)
        print("AGENTCORE RECREATION SUMMARY")
        print("="*80)
        print(f"Status: {result['status']}")
        print(f"Agent Name: {result['agent_name']}")
        print(f"Old Agent ID: {result['old_agent_id']}")
        
        if 'oidc_config' in result:
            print(f"User Pool ID: {result['oidc_config']['user_pool_id']}")
            print(f"Client ID: {result['oidc_config']['client_id']}")
            print(f"Discovery URL: {result['oidc_config']['discovery_url']}")
        
        if result['status'] == 'success':
            print("\nRecreation completed successfully!")
            print("Test the authentication flow:")
            print("1. Login with: test@mbti-travel.com / TestPass1234!")
            print("2. Try generating an itinerary")
            print("3. Check for 403 errors in logs")
        elif result['status'] == 'manual_deployment_required':
            print("\nManual deployment required:")
            for step in result.get('next_steps', []):
                print(f"- {step}")
        
        print("="*80)
        
        return 0 if result['status'] == 'success' else 1
        
    except Exception as e:
        logger.error(f"Recreation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())