#!/usr/bin/env python3
"""
Update Test User Password

This script updates the test user password to allow authentication testing.
"""

import json
import boto3
from botocore.exceptions import ClientError


def update_test_user_password():
    """Update test user password to enable authentication."""
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    username = config['test_user']['email']
    region = config['region']
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    try:
        # Set permanent password for the user
        new_password = "TestPass123!"
        
        print(f"Updating password for user: {username}")
        
        # Set permanent password (admin operation)
        response = cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=new_password,
            Permanent=True
        )
        
        print("✅ Password updated successfully")
        
        # Update the config file with new password info
        config['test_user']['status'] = 'CONFIRMED'
        config['test_user']['password_updated'] = True
        
        with open('cognito_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration updated")
        print(f"New password: {new_password}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Failed to update password: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = update_test_user_password()
    exit(0 if success else 1)