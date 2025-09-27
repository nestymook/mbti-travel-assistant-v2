#!/usr/bin/env python3
"""
Debug Authentication Issues

This script helps debug authentication issues with Cognito.
"""

import json
import boto3
from botocore.exceptions import ClientError
from services.auth_service import CognitoAuthenticator, AuthenticationError


def debug_cognito_auth():
    """Debug Cognito authentication issues."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    client_id = config['app_client']['client_id']
    region = config['region']
    username = config['test_user']['email']
    password = "TestPass123!"
    
    print(f"Debugging authentication for:")
    print(f"  User Pool ID: {user_pool_id}")
    print(f"  Client ID: {client_id}")
    print(f"  Region: {region}")
    print(f"  Username: {username}")
    print()
    
    # Check user status first
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    try:
        print("1. Checking user status...")
        user_response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        
        print(f"   User Status: {user_response['UserStatus']}")
        print(f"   Enabled: {user_response.get('Enabled', 'Unknown')}")
        
        # Check user attributes
        attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
        print(f"   Email: {attributes.get('email', 'N/A')}")
        print(f"   Email Verified: {attributes.get('email_verified', 'N/A')}")
        
    except ClientError as e:
        print(f"   Error checking user: {e}")
        return False
    
    # Try simple authentication first
    try:
        print("\n2. Testing simple authentication...")
        
        # Try initiate auth without SRP first
        try:
            response = cognito_client.admin_initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            print("   ✅ ADMIN_NO_SRP_AUTH successful")
            return True
            
        except ClientError as e:
            print(f"   ❌ ADMIN_NO_SRP_AUTH failed: {e.response['Error']['Code']}")
    
    except Exception as e:
        print(f"   ❌ Simple auth failed: {e}")
    
    # Try SRP authentication
    try:
        print("\n3. Testing SRP authentication...")
        authenticator = CognitoAuthenticator(user_pool_id, client_id, region)
        
        # Try to authenticate
        tokens = authenticator.authenticate_user(username, password)
        print("   ✅ SRP authentication successful")
        print(f"   Access token length: {len(tokens.access_token)}")
        return True
        
    except AuthenticationError as e:
        print(f"   ❌ SRP authentication failed: {e.error_type} - {e.message}")
        print(f"   Details: {e.details}")
        print(f"   Suggested action: {e.suggested_action}")
        
    except Exception as e:
        print(f"   ❌ SRP authentication error: {e}")
    
    return False


if __name__ == "__main__":
    success = debug_cognito_auth()
    exit(0 if success else 1)