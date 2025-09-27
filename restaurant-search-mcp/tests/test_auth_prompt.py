#!/usr/bin/env python3
"""
Test authentication with password prompting.

This script demonstrates the updated authentication flow that prompts for passwords
instead of using hardcoded values.
"""

import json
import getpass
import boto3
from botocore.exceptions import ClientError


def test_auth_with_prompt():
    """Test authentication with password prompting."""
    
    print("🔐 Restaurant Search MCP - Authentication Test")
    print("=" * 50)
    
    try:
        # Load Cognito configuration
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        
        user_pool_id = config['user_pool']['user_pool_id']
        client_id = config['app_client']['client_id']
        region = config['region']
        
        print(f"User Pool ID: {user_pool_id}")
        print(f"Client ID: {client_id}")
        print(f"Region: {region}")
        
        # Prompt for credentials
        username = input("Enter Cognito username (default: testing_user@test.com.hk): ").strip()
        if not username:
            username = "testing_user@test.com.hk"
        
        password = getpass.getpass(f"Enter password for {username}: ")
        
        print(f"\n🔐 Authenticating with Cognito as: {username}")
        
        # Test authentication
        cognito_client = boto3.client('cognito-idp', region_name=region)
        
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        
        print("✅ Authentication successful!")
        print(f"Access token length: {len(access_token)}")
        
        # Decode token info (basic info only)
        import base64
        
        # Get token payload (middle part)
        token_parts = access_token.split('.')
        if len(token_parts) >= 2:
            # Add padding if needed
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            try:
                decoded = base64.b64decode(payload)
                token_info = json.loads(decoded)
                
                print(f"Token client_id: {token_info.get('client_id', 'N/A')}")
                print(f"Token username: {token_info.get('username', 'N/A')}")
                print(f"Token expires: {token_info.get('exp', 'N/A')}")
                
            except Exception as e:
                print(f"Could not decode token info: {e}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ Authentication failed: {error_code}")
        print(f"Error: {error_message}")
        
        if error_code == 'NotAuthorizedException':
            print("\n💡 Possible issues:")
            print("  - Incorrect username or password")
            print("  - User account may be disabled")
            print("  - Check if user exists in Cognito User Pool")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    success = test_auth_with_prompt()
    
    if success:
        print("\n🎉 Authentication test completed successfully!")
        print("You can now use the other test scripts with password prompting.")
    else:
        print("\n❌ Authentication test failed.")
        print("Please check your credentials and try again.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())