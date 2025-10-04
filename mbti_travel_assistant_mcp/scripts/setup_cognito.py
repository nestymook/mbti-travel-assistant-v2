#!/usr/bin/env python3
"""
Cognito User Pool Setup Script for Restaurant Search MCP

This script creates and configures an Amazon Cognito User Pool with app client
for JWT authentication with the Restaurant Search MCP server deployed on
Bedrock AgentCore Runtime.

Requirements: 8.3, 8.4
"""

import json
import os
import sys
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError


class CognitoSetup:
    """Setup and configure Cognito User Pool for MCP authentication."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize Cognito setup client.
        
        Args:
            region: AWS region for Cognito resources.
        """
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        self.config_file = "cognito_config.json"
    
    def create_user_pool(self, pool_name: str = "restaurant-search-mcp-pool") -> Dict[str, Any]:
        """Create Cognito User Pool with appropriate configuration.
        
        Args:
            pool_name: Name for the Cognito User Pool.
            
        Returns:
            Dictionary containing user pool configuration.
        """
        try:
            # Create user pool with JWT token configuration
            response = self.cognito_client.create_user_pool(
                PoolName=pool_name,
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 8,
                        'RequireUppercase': True,
                        'RequireLowercase': True,
                        'RequireNumbers': True,
                        'RequireSymbols': False
                    }
                },
                AutoVerifiedAttributes=['email'],
                UsernameAttributes=['email'],
                UsernameConfiguration={
                    'CaseSensitive': False
                },
                Schema=[
                    {
                        'Name': 'email',
                        'AttributeDataType': 'String',
                        'Required': True,
                        'Mutable': True
                    }
                ],
                AccountRecoverySetting={
                    'RecoveryMechanisms': [
                        {
                            'Priority': 1,
                            'Name': 'verified_email'
                        }
                    ]
                }
            )
            
            user_pool_id = response['UserPool']['Id']
            print(f"✓ Created User Pool: {user_pool_id}")
            
            return {
                'user_pool_id': user_pool_id,
                'user_pool_arn': response['UserPool']['Arn'],
                'creation_date': response['UserPool']['CreationDate'].isoformat()
            }
            
        except ClientError as e:
            print(f"✗ Error creating user pool: {e}")
            raise
    
    def create_user_pool_client(self, user_pool_id: str, 
                               client_name: str = "restaurant-search-mcp-client") -> Dict[str, Any]:
        """Create User Pool App Client for JWT authentication.
        
        Args:
            user_pool_id: ID of the user pool.
            client_name: Name for the app client.
            
        Returns:
            Dictionary containing app client configuration.
        """
        try:
            response = self.cognito_client.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName=client_name,
                GenerateSecret=False,  # Public client for JWT tokens
                RefreshTokenValidity=30,  # 30 days
                AccessTokenValidity=60,   # 60 minutes
                IdTokenValidity=60,       # 60 minutes
                TokenValidityUnits={
                    'AccessToken': 'minutes',
                    'IdToken': 'minutes',
                    'RefreshToken': 'days'
                },
                ReadAttributes=['email'],
                WriteAttributes=['email'],
                ExplicitAuthFlows=[
                    'ALLOW_USER_PASSWORD_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH',
                    'ALLOW_USER_SRP_AUTH'
                ],
                SupportedIdentityProviders=['COGNITO'],
                PreventUserExistenceErrors='ENABLED'
            )
            
            client_id = response['UserPoolClient']['ClientId']
            print(f"✓ Created App Client: {client_id}")
            
            return {
                'client_id': client_id,
                'client_name': client_name
            }
            
        except ClientError as e:
            print(f"✗ Error creating app client: {e}")
            raise
    
    def create_test_user(self, user_pool_id: str, email: str, 
                        temporary_password: str = "TempPass123!") -> Dict[str, Any]:
        """Create a test user for authentication testing.
        
        Args:
            user_pool_id: ID of the user pool.
            email: Email address for the test user.
            temporary_password: Temporary password for the user.
            
        Returns:
            Dictionary containing user information.
        """
        try:
            # Create user
            response = self.cognito_client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        'Name': 'email_verified',
                        'Value': 'true'
                    }
                ],
                TemporaryPassword=temporary_password,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            
            print(f"✓ Created test user: {email}")
            
            # Set permanent password
            self.cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=temporary_password,
                Permanent=True
            )
            
            print(f"✓ Set permanent password for user: {email}")
            
            return {
                'username': email,
                'email': email,
                'status': response['User']['UserStatus']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException':
                print(f"✓ Test user already exists: {email}")
                return {
                    'username': email,
                    'email': email,
                    'status': 'EXISTS'
                }
            else:
                print(f"✗ Error creating test user: {e}")
                raise
    
    def get_discovery_url(self, user_pool_id: str) -> str:
        """Get the OIDC discovery URL for the user pool.
        
        Args:
            user_pool_id: ID of the user pool.
            
        Returns:
            OIDC discovery URL.
        """
        return f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    
    def save_configuration(self, config: Dict[str, Any]) -> None:
        """Save Cognito configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✓ Configuration saved to: {self.config_file}")
        except Exception as e:
            print(f"✗ Error saving configuration: {e}")
            raise
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load existing Cognito configuration from JSON file.
        
        Returns:
            Configuration dictionary.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            return {}
    
    def setup_complete_cognito(self, test_user_email: str = "test@example.com") -> Dict[str, Any]:
        """Complete Cognito setup process.
        
        Args:
            test_user_email: Email for test user creation.
            
        Returns:
            Complete configuration dictionary.
        """
        print("🚀 Starting Cognito User Pool setup...")
        
        # Check if configuration already exists
        existing_config = self.load_configuration()
        if existing_config:
            print("✓ Found existing configuration")
            return existing_config
        
        try:
            # Create user pool
            user_pool_config = self.create_user_pool()
            user_pool_id = user_pool_config['user_pool_id']
            
            # Create app client
            client_config = self.create_user_pool_client(user_pool_id)
            
            # Create test user
            user_config = self.create_test_user(user_pool_id, test_user_email)
            
            # Build complete configuration
            complete_config = {
                'region': self.region,
                'user_pool': user_pool_config,
                'app_client': client_config,
                'test_user': user_config,
                'discovery_url': self.get_discovery_url(user_pool_id),
                'setup_timestamp': boto3.Session().region_name
            }
            
            # Save configuration
            self.save_configuration(complete_config)
            
            print("\n🎉 Cognito setup completed successfully!")
            print(f"User Pool ID: {user_pool_id}")
            print(f"App Client ID: {client_config['client_id']}")
            print(f"Test User: {test_user_email}")
            print(f"Discovery URL: {complete_config['discovery_url']}")
            
            return complete_config
            
        except Exception as e:
            print(f"\n💥 Setup failed: {e}")
            raise


def main():
    """Main function to run Cognito setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Cognito User Pool for Restaurant Search MCP')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--email', default='test@example.com', help='Test user email (default: test@example.com)')
    parser.add_argument('--pool-name', default='restaurant-search-mcp-pool', help='User pool name')
    
    args = parser.parse_args()
    
    try:
        # Initialize setup
        cognito_setup = CognitoSetup(region=args.region)
        
        # Run complete setup
        config = cognito_setup.setup_complete_cognito(test_user_email=args.email)
        
        print("\n📋 Configuration Summary:")
        print(f"Region: {config['region']}")
        print(f"User Pool ID: {config['user_pool']['user_pool_id']}")
        print(f"App Client ID: {config['app_client']['client_id']}")
        print(f"Test User: {config['test_user']['email']}")
        print(f"Discovery URL: {config['discovery_url']}")
        print(f"Config File: cognito_config.json")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())