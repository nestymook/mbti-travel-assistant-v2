#!/usr/bin/env python3
"""
Create Test User using AWS CLI

This script creates the new test user using AWS CLI commands,
which might have different permission requirements.
"""

import json
import subprocess
import sys


def run_aws_cli_command(command):
    """Run AWS CLI command and return result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"AWS CLI command failed: {e}")
        print(f"Error output: {e.stderr}")
        return None


def create_test_user_with_cli():
    """Create test user using AWS CLI."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    user_pool_id = config['user_pool']['user_pool_id']
    new_username = "testing_user@test.com.hk"
    new_password = "TestPass123!"
    
    print(f"Creating test user: {new_username}")
    print(f"User Pool ID: {user_pool_id}")
    
    # Step 1: Try to create the user
    create_command = f'''aws cognito-idp admin-create-user \\
        --user-pool-id {user_pool_id} \\
        --username "{new_username}" \\
        --user-attributes Name=email,Value="{new_username}" Name=email_verified,Value=true \\
        --temporary-password "{new_password}" \\
        --message-action SUPPRESS \\
        --region us-east-1'''
    
    print("Creating user...")
    result = run_aws_cli_command(create_command)
    
    if result is None:
        print("Failed to create user, trying to set password for existing user...")
    else:
        print("✅ User created successfully")
    
    # Step 2: Set permanent password
    set_password_command = f'''aws cognito-idp admin-set-user-password \\
        --user-pool-id {user_pool_id} \\
        --username "{new_username}" \\
        --password "{new_password}" \\
        --permanent \\
        --region us-east-1'''
    
    print("Setting permanent password...")
    result = run_aws_cli_command(set_password_command)
    
    if result is None:
        print("❌ Failed to set password")
        return False
    else:
        print("✅ Password set successfully")
    
    # Step 3: Confirm user signup
    confirm_command = f'''aws cognito-idp admin-confirm-sign-up \\
        --user-pool-id {user_pool_id} \\
        --username "{new_username}" \\
        --region us-east-1'''
    
    print("Confirming user signup...")
    result = run_aws_cli_command(confirm_command)
    
    if result is None:
        print("⚠️ Failed to confirm signup, but user might already be confirmed")
    else:
        print("✅ User confirmed successfully")
    
    return True


def test_authentication():
    """Test authentication with the new user."""
    
    # Load configuration
    with open('cognito_config.json', 'r') as f:
        config = json.load(f)
    
    client_id = config['app_client']['client_id']
    username = config['test_user']['username']
    password = "TestPass123!"
    
    print(f"Testing authentication for: {username}")
    
    # Use AWS CLI to test authentication
    auth_command = f'''aws cognito-idp initiate-auth \\
        --client-id {client_id} \\
        --auth-flow USER_PASSWORD_AUTH \\
        --auth-parameters USERNAME="{username}",PASSWORD="{password}" \\
        --region us-east-1'''
    
    result = run_aws_cli_command(auth_command)
    
    if result:
        print("✅ Authentication test successful")
        
        # Parse the result to get token info
        try:
            auth_result = json.loads(result)
            access_token = auth_result['AuthenticationResult']['AccessToken']
            print(f"Access token length: {len(access_token)}")
        except Exception as e:
            print(f"Could not parse auth result: {e}")
        
        return True
    else:
        print("❌ Authentication test failed")
        return False


def main():
    """Main function."""
    print("🚀 Creating test user using AWS CLI")
    
    # Check if AWS CLI is available
    try:
        subprocess.run(['aws', '--version'], capture_output=True, check=True)
        print("✅ AWS CLI is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ AWS CLI is not available or not configured")
        return 1
    
    # Create the user
    success = create_test_user_with_cli()
    
    if success:
        print("\n🔍 Testing authentication...")
        auth_success = test_authentication()
        
        if auth_success:
            print("\n✅ Test user creation completed successfully!")
            print("Username: testing_user@test.com.hk")
            print("Password: TestPass123!")
            return 0
        else:
            print("\n⚠️ User created but authentication test failed")
            return 1
    else:
        print("\n❌ Failed to create test user")
        return 1


if __name__ == "__main__":
    sys.exit(main())