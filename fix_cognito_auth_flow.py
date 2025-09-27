#!/usr/bin/env python3
"""
Fix Cognito App Client Authentication Flow

This script updates the Cognito app client to enable USER_PASSWORD_AUTH flow
for testing purposes.
"""

import json
import boto3
from botocore.exceptions import ClientError


def fix_cognito_auth_flow():
    """Enable USER_PASSWORD_AUTH flow for the app client."""
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    client_id = config['app_client']['client_id']
    region = config['region']
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    try:
        print(f"Updating app client: {client_id}")
        print(f"User Pool: {user_pool_id}")
        
        # Update app client to enable USER_PASSWORD_AUTH
        response = cognito_client.update_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_SRP_AUTH'
            ],
            RefreshTokenValidity=30,
            AccessTokenValidity=60,
            IdTokenValidity=60,
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            }
        )
        
        print("✅ App client updated successfully")
        print("✅ USER_PASSWORD_AUTH flow enabled")
        
        # Verify the update
        client_info = cognito_client.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )
        
        auth_flows = client_info['UserPoolClient']['ExplicitAuthFlows']
        print(f"Current auth flows: {auth_flows}")
        
        if 'ALLOW_USER_PASSWORD_AUTH' in auth_flows:
            print("✅ USER_PASSWORD_AUTH confirmed enabled")
            return True
        else:
            print("❌ USER_PASSWORD_AUTH not found in auth flows")
            return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Failed to update app client: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = fix_cognito_auth_flow()
    exit(0 if success else 1)