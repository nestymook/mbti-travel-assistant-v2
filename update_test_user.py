#!/usr/bin/env python3
"""
Update Test User

This script creates a new test user "testing_user@test.com.hk" in Cognito
and updates the configuration.
"""

import json
import boto3
from botocore.exceptions import ClientError


def create_new_test_user():
    """Create new test user and update configuration."""
    
    # Load Cognito configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    region = config['region']
    
    # New test user details
    new_username = "testing_user@test.com.hk"
    new_password = "TestPass123!"
    
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name=region)
    
    try:
        print(f"Creating new test user: {new_username}")
        
        # Check if user already exists
        try:
            existing_user = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=new_username
            )
            print(f"User {new_username} already exists, updating password...")
            
            # Update existing user password
            cognito_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=new_username,
                Password=new_password,
                Permanent=True
            )
            
            # Confirm the user if not already confirmed
            user_status = existing_user['UserStatus']
            if user_status != 'CONFIRMED':
                cognito_client.admin_confirm_sign_up(
                    UserPoolId=user_pool_id,
                    Username=new_username
                )
                print(f"✅ User confirmed")
            
            print(f"✅ Existing user updated")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                # User doesn't exist, create new one
                print(f"Creating new user: {new_username}")
                
                # Create user
                cognito_client.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=new_username,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': new_username
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        }
                    ],
                    TemporaryPassword=new_password,
                    MessageAction='SUPPRESS'  # Don't send welcome email
                )
                
                print(f"✅ User created")
                
                # Set permanent password
                cognito_client.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username=new_username,
                    Password=new_password,
                    Permanent=True
                )
                
                print(f"✅ Permanent password set")
                
                # Confirm the user
                cognito_client.admin_confirm_sign_up(
                    UserPoolId=user_pool_id,
                    Username=new_username
                )
                
                print(f"✅ User confirmed")
            else:
                raise
        
        # Test authentication with new user
        print(f"Testing authentication for new user...")
        
        client_id = config['app_client']['client_id']
        
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': new_username,
                'PASSWORD': new_password
            }
        )
        
        print(f"✅ Authentication test successful")
        
        # Update configuration file
        config['test_user'] = {
            'username': new_username,
            'email': new_username,
            'status': 'CONFIRMED',
            'password_updated': True,
            'created_at': '2025-09-27'
        }
        
        # Keep the old user info as backup
        if 'previous_test_user' not in config:
            config['previous_test_user'] = {
                'username': 'nestymook@gmail.com',
                'email': 'nestymook@gmail.com',
                'note': 'Previous test user, kept for reference'
            }
        
        # Save updated configuration
        with open('cognito_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration updated")
        print(f"New test user: {new_username}")
        print(f"Password: {new_password}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Failed to create/update test user: {error_code} - {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_test_user():
    """Verify the test user can authenticate."""
    try:
        # Load updated configuration
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        
        username = config['test_user']['username']
        password = "TestPass123!"
        client_id = config['app_client']['client_id']
        region = config['region']
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp', region_name=region)
        
        print(f"Verifying authentication for: {username}")
        
        # Test authentication
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Extract token info
        auth_result = response['AuthenticationResult']
        access_token = auth_result['AccessToken']
        
        print(f"✅ Verification successful")
        print(f"Access token length: {len(access_token)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Updating test user to testing_user@test.com.hk")
    
    # Create/update test user
    success = create_new_test_user()
    
    if success:
        print("\n🔍 Verifying new test user...")
        verify_success = verify_test_user()
        
        if verify_success:
            print("\n✅ Test user update completed successfully!")
            print("You can now use testing_user@test.com.hk with password TestPass123!")
        else:
            print("\n⚠️ Test user created but verification failed")
            success = False
    
    exit(0 if success else 1)