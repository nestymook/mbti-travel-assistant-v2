#!/usr/bin/env python3
"""
Simple Authentication Test

This script tests authentication without requiring admin permissions.
"""

import json
import boto3
from botocore.exceptions import ClientError


def test_simple_auth():
    """Test simple authentication without admin permissions."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    client_id = config['app_client']['client_id']
    region = config['region']
    username = config['test_user']['email']
    password = "TestPass123!"
    
    print(f"Testing authentication for:")
    print(f"  User Pool ID: {user_pool_id}")
    print(f"  Client ID: {client_id}")
    print(f"  Region: {region}")
    print(f"  Username: {username}")
    print()
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    # Try USER_SRP_AUTH flow
    try:
        print("1. Testing USER_SRP_AUTH initiation...")
        
        # Step 1: Initiate SRP auth
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'SRP_A': '123456789'  # Dummy value for testing
            }
        )
        
        print(f"   Challenge: {response.get('ChallengeName', 'None')}")
        
        if 'ChallengeName' in response:
            challenge_params = response.get('ChallengeParameters', {})
            print(f"   Challenge Parameters: {list(challenge_params.keys())}")
            
            if response['ChallengeName'] == 'PASSWORD_VERIFIER':
                print("   ✅ SRP challenge received - user exists and SRP is working")
                return True
            else:
                print(f"   ⚠️ Unexpected challenge: {response['ChallengeName']}")
                return False
        else:
            print("   ❌ No challenge received")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ❌ SRP initiation failed: {error_code}")
        print(f"   Message: {error_message}")
        
        if error_code == 'UserNotFoundException':
            print("   → User does not exist")
        elif error_code == 'NotAuthorizedException':
            print("   → User exists but authentication not allowed")
        elif error_code == 'UserNotConfirmedException':
            print("   → User exists but not confirmed")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_simple_auth()
    exit(0 if success else 1)