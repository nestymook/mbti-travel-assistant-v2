#!/usr/bin/env python3
"""
Fix AgentCore IAM Permissions Script

This script fixes the IAM permissions issue where the AgentCore health check service
fails with AccessDeniedException when trying to call bedrock-agentcore:GetAgentRuntime.

Error being fixed:
WARNING:services.agentcore_health_check_service.health_check:Failed to get agent runtime status: 
An error occurred (AccessDeniedException) when calling the GetAgentRuntime operation: 
User: arn:aws:sts::209803798463:assumed-role/AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2/BedrockAgentCore-8cdaf416-b4aa-4382-b66e-80fb3510bdde 
is not authorized to perform: bedrock-agentcore:GetAgentRuntime on resource: 
arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
"""

import json
import boto3
import logging
import sys
from typing import Dict, Any, List
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentCoreIAMFixer:
    """Fix IAM permissions for AgentCore health check service."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize the IAM fixer."""
        self.region_name = region_name
        self.account_id = "209803798463"
        self.agentcore_execution_role = "AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2"
        self.agent_runtime_arn = f"arn:aws:bedrock-agentcore:{region_name}:{self.account_id}:runtime/restaurant_search_agent-mN8bgq2Y1j"
        
        try:
            self.iam_client = boto3.client('iam', region_name=region_name)
            self.sts_client = boto3.client('sts', region_name=region_name)
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            sys.exit(1)
    
    def get_current_identity(self) -> Dict[str, Any]:
        """Get current AWS identity information."""
        try:
            identity = self.sts_client.get_caller_identity()
            logger.info(f"Current AWS identity: {identity.get('Arn')}")
            return identity
        except Exception as e:
            logger.error(f"Failed to get caller identity: {e}")
            raise
    
    def create_agentcore_policy_document(self) -> Dict[str, Any]:
        """Create the IAM policy document for AgentCore permissions."""
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AgentCoreHealthCheckPermissions",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:GetAgentRuntime",
                        "bedrock-agentcore:ListAgentRuntimes",
                        "bedrock-agentcore:DescribeAgentRuntime"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock-agentcore:{self.region_name}:{self.account_id}:runtime/*",
                        self.agent_runtime_arn
                    ]
                },
                {
                    "Sid": "BedrockAgentCoreGeneralPermissions",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:ListAgentRuntimes"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "BedrockModelAccessPermissions",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{self.region_name}::foundation-model/*"
                    ]
                }
            ]
        }
        
        logger.info("Created AgentCore IAM policy document")
        logger.debug(f"Policy document: {json.dumps(policy_document, indent=2)}")
        return policy_document
    
    def check_role_exists(self, role_name: str) -> bool:
        """Check if the IAM role exists."""
        try:
            self.iam_client.get_role(RoleName=role_name)
            logger.info(f"Role {role_name} exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                logger.warning(f"Role {role_name} does not exist")
                return False
            else:
                logger.error(f"Error checking role {role_name}: {e}")
                raise
    
    def list_role_policies(self, role_name: str) -> List[str]:
        """List inline policies attached to the role."""
        try:
            response = self.iam_client.list_role_policies(RoleName=role_name)
            policies = response.get('PolicyNames', [])
            logger.info(f"Role {role_name} has {len(policies)} inline policies: {policies}")
            return policies
        except ClientError as e:
            logger.error(f"Error listing policies for role {role_name}: {e}")
            raise
    
    def list_attached_role_policies(self, role_name: str) -> List[Dict[str, str]]:
        """List managed policies attached to the role."""
        try:
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            policies = response.get('AttachedPolicies', [])
            logger.info(f"Role {role_name} has {len(policies)} attached managed policies")
            for policy in policies:
                logger.info(f"  - {policy['PolicyName']} ({policy['PolicyArn']})")
            return policies
        except ClientError as e:
            logger.error(f"Error listing attached policies for role {role_name}: {e}")
            raise
    
    def create_or_update_inline_policy(self, role_name: str, policy_name: str, policy_document: Dict[str, Any]) -> bool:
        """Create or update an inline policy on the role."""
        try:
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            logger.info(f"Successfully created/updated inline policy {policy_name} on role {role_name}")
            return True
        except ClientError as e:
            logger.error(f"Error creating/updating policy {policy_name} on role {role_name}: {e}")
            return False
    
    def create_managed_policy(self, policy_name: str, policy_document: Dict[str, Any]) -> str:
        """Create a managed IAM policy."""
        try:
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="AgentCore health check permissions for bedrock-agentcore operations"
            )
            policy_arn = response['Policy']['Arn']
            logger.info(f"Successfully created managed policy {policy_name} with ARN: {policy_arn}")
            return policy_arn
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                # Policy already exists, get its ARN
                policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
                logger.info(f"Managed policy {policy_name} already exists with ARN: {policy_arn}")
                return policy_arn
            else:
                logger.error(f"Error creating managed policy {policy_name}: {e}")
                raise
    
    def attach_managed_policy_to_role(self, role_name: str, policy_arn: str) -> bool:
        """Attach a managed policy to the role."""
        try:
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Successfully attached policy {policy_arn} to role {role_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                logger.error(f"Role {role_name} or policy {policy_arn} does not exist")
            else:
                logger.error(f"Error attaching policy {policy_arn} to role {role_name}: {e}")
            return False
    
    def verify_permissions(self, role_name: str) -> bool:
        """Verify that the role has the required permissions."""
        try:
            # Check inline policies
            inline_policies = self.list_role_policies(role_name)
            
            # Check attached managed policies
            attached_policies = self.list_attached_role_policies(role_name)
            
            # For a complete verification, we would need to simulate the policy
            # This is a basic check to see if our policy was applied
            has_agentcore_policy = any('AgentCore' in policy for policy in inline_policies)
            has_bedrock_policy = any('Bedrock' in policy.get('PolicyName', '') for policy in attached_policies)
            
            if has_agentcore_policy or has_bedrock_policy:
                logger.info("Role appears to have AgentCore-related permissions")
                return True
            else:
                logger.warning("Role may not have the required AgentCore permissions")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying permissions for role {role_name}: {e}")
            return False
    
    def fix_iam_permissions(self, use_managed_policy: bool = False) -> bool:
        """Fix the IAM permissions for AgentCore health check service."""
        logger.info("Starting AgentCore IAM permissions fix...")
        
        # Get current identity
        identity = self.get_current_identity()
        
        # Check if the role exists
        if not self.check_role_exists(self.agentcore_execution_role):
            logger.error(f"AgentCore execution role {self.agentcore_execution_role} does not exist")
            logger.info("This role should be created automatically by AgentCore deployment")
            return False
        
        # Create the policy document
        policy_document = self.create_agentcore_policy_document()
        
        # Apply the policy
        if use_managed_policy:
            # Create managed policy approach
            policy_name = "AgentCoreHealthCheckPermissions"
            try:
                policy_arn = self.create_managed_policy(policy_name, policy_document)
                success = self.attach_managed_policy_to_role(self.agentcore_execution_role, policy_arn)
            except Exception as e:
                logger.error(f"Failed to create/attach managed policy: {e}")
                success = False
        else:
            # Create inline policy approach (recommended for role-specific permissions)
            policy_name = "AgentCoreHealthCheckInlinePolicy"
            success = self.create_or_update_inline_policy(
                self.agentcore_execution_role, 
                policy_name, 
                policy_document
            )
        
        if success:
            logger.info("Successfully applied IAM permissions fix")
            
            # Verify the permissions were applied
            if self.verify_permissions(self.agentcore_execution_role):
                logger.info("✅ IAM permissions fix completed successfully")
                logger.info("The AgentCore health check service should now be able to call GetAgentRuntime")
                return True
            else:
                logger.warning("⚠️ Permissions were applied but verification failed")
                return False
        else:
            logger.error("❌ Failed to apply IAM permissions fix")
            return False
    
    def save_policy_document(self, filename: str = "agentcore_iam_policy.json") -> None:
        """Save the policy document to a file for reference."""
        policy_document = self.create_agentcore_policy_document()
        
        try:
            with open(filename, 'w') as f:
                json.dump(policy_document, f, indent=2)
            logger.info(f"Policy document saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save policy document to {filename}: {e}")

def main():
    """Main function to fix AgentCore IAM permissions."""
    logger.info("🚀 Starting AgentCore IAM Permissions Fix")
    
    try:
        # Initialize the fixer
        fixer = AgentCoreIAMFixer()
        
        # Save policy document for reference
        fixer.save_policy_document()
        
        # Fix the permissions (using inline policy by default)
        success = fixer.fix_iam_permissions(use_managed_policy=False)
        
        if success:
            logger.info("🎉 AgentCore IAM permissions fix completed successfully!")
            logger.info("Next steps:")
            logger.info("1. Wait a few minutes for IAM changes to propagate")
            logger.info("2. Restart your AgentCore health check service")
            logger.info("3. Verify that the GetAgentRuntime calls now succeed")
            return 0
        else:
            logger.error("💥 AgentCore IAM permissions fix failed!")
            logger.info("Troubleshooting steps:")
            logger.info("1. Verify you have IAM permissions to modify the role")
            logger.info("2. Check that the AgentCore execution role exists")
            logger.info("3. Review the error messages above for specific issues")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Unexpected error during IAM fix: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())