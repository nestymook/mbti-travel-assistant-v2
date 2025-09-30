#!/usr/bin/env python3
"""
Create Cognito User Pool with OIDC Configuration for AgentCore
"""

import boto3
import json
import time
from datetime import datetime

def create_oidc_cognito_setup():
    """Create a new Cognito User Pool with proper OIDC configuration"""
    
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    print("🚀 Creating new Cognito User Pool with OIDC configuration...")
    
    # Create User Pool with OIDC-compatible settings
    user_pool_response = cognito.create_user_pool(
        PoolName='mbti-travel-oidc-pool',
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True,
                'TemporaryPasswordValidityDays': 7
            }
        },
        LambdaConfig={},
        AutoVerifiedAttributes=['email'],
        UsernameAttributes=['email'],
        SmsVerificationMessage='Your verification code is {####}',
        EmailVerificationMessage='Your verification code is {####}',
        EmailVerificationSubject='Your verification code',
        VerificationMessageTemplate={
            'SmsMessage': 'Your verification code is {####}',
            'EmailMessage': 'Your verification code is {####}',
            'EmailSubject': 'Your verification code',
            'DefaultEmailOption': 'CONFIRM_WITH_CODE'
        },
        MfaConfiguration='OFF',
        DeviceConfiguration={
            'ChallengeRequiredOnNewDevice': False,
            'DeviceOnlyRememberedOnUserPrompt': False
        },
        EmailConfiguration={
            'EmailSendingAccount': 'COGNITO_DEFAULT'
        },
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': False,
            'InviteMessageTemplate': {
                'SMSMessage': 'Your username is {username} and temporary password is {####}',
                'EmailMessage': 'Your username is {username} and temporary password is {####}',
                'EmailSubject': 'Your temporary password'
            }
        },
        UserPoolTags={
            'Project': 'MBTI-Travel-Assistant',
            'Environment': 'Production',
            'Purpose': 'OIDC-Authentication'
        },
        AccountRecoverySetting={
            'RecoveryMechanisms': [
                {
                    'Priority': 1,
                    'Name': 'verified_email'
                }
            ]
        }
    )
    
    user_pool_id = user_pool_response['UserPool']['Id']
    user_pool_arn = user_pool_response['UserPool']['Arn']
    
    print(f"✅ Created User Pool: {user_pool_id}")
    
    # Create User Pool Client with OIDC OAuth flows
    client_response = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='mbti-travel-oidc-client',
        GenerateSecret=False,  # Public client for SPA
        RefreshTokenValidity=30,  # 30 days
        AccessTokenValidity=60,   # 60 minutes
        IdTokenValidity=60,       # 60 minutes
        TokenValidityUnits={
            'AccessToken': 'minutes',
            'IdToken': 'minutes',
            'RefreshToken': 'days'
        },
        ReadAttributes=[
            'email',
            'email_verified',
            'name',
            'preferred_username'
        ],
        WriteAttributes=[
            'email',
            'name',
            'preferred_username'
        ],
        ExplicitAuthFlows=[
            'ALLOW_USER_SRP_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH',
            'ALLOW_USER_PASSWORD_AUTH'
        ],
        SupportedIdentityProviders=['COGNITO'],
        CallbackURLs=[
            'https://d39ank8zud5pbg.cloudfront.net/',
            'https://d39ank8zud5pbg.cloudfront.net/auth/callback',
            'http://localhost:3000/',
            'http://localhost:3000/auth/callback'
        ],
        LogoutURLs=[
            'https://d39ank8zud5pbg.cloudfront.net/',
            'http://localhost:3000/'
        ],
        AllowedOAuthFlows=['code', 'implicit'],
        AllowedOAuthScopes=['openid', 'email', 'profile'],
        AllowedOAuthFlowsUserPoolClient=True,
        PreventUserExistenceErrors='ENABLED',
        EnableTokenRevocation=True,
        EnablePropagateAdditionalUserContextData=False
    )
    
    client_id = client_response['UserPoolClient']['ClientId']
    
    print(f"✅ Created User Pool Client: {client_id}")
    
    # Create User Pool Domain
    timestamp = str(int(time.time()))
    domain_prefix = f"mbti-travel-oidc-{timestamp}"
    
    try:
        domain_response = cognito.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        
        print(f"✅ Created User Pool Domain: {domain_prefix}")
        
        # Wait for domain to be active
        print("⏳ Waiting for domain to become active...")
        time.sleep(10)
        
        domain_url = f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com"
        
    except Exception as e:
        print(f"❌ Failed to create domain: {e}")
        domain_url = None
        domain_prefix = None
    
    # Create a test user
    try:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username='mbti-test-user@example.com',
            UserAttributes=[
                {'Name': 'email', 'Value': 'mbti-test-user@example.com'},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': 'MBTI Test User'}
            ],
            TemporaryPassword='TempPass123!',
            MessageAction='SUPPRESS'
        )
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username='mbti-test-user@example.com',
            Password='MBTITest123!',
            Permanent=True
        )
        
        print("✅ Created test user: mbti-test-user@example.com / MBTITest123!")
        
    except Exception as e:
        print(f"⚠️ Failed to create test user: {e}")
    
    # Generate configuration
    config = {
        "region": "us-east-1",
        "user_pool": {
            "user_pool_id": user_pool_id,
            "user_pool_arn": user_pool_arn,
            "creation_date": datetime.now().isoformat()
        },
        "app_client": {
            "client_id": client_id,
            "client_name": "mbti-travel-oidc-client"
        },
        "test_user": {
            "username": "mbti-test-user@example.com",
            "email": "mbti-test-user@example.com",
            "password": "MBTITest123!",
            "status": "CONFIRMED"
        },
        "oidc_configuration": {
            "discovery_url": f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid-configuration",
            "jwks_uri": f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json",
            "issuer": f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}",
            "authorization_endpoint": f"{domain_url}/oauth2/authorize" if domain_url else None,
            "token_endpoint": f"{domain_url}/oauth2/token" if domain_url else None,
            "userinfo_endpoint": f"{domain_url}/oauth2/userInfo" if domain_url else None
        },
        "custom_domain": {
            "domain_prefix": domain_prefix,
            "domain_url": domain_url,
            "status": "ACTIVE" if domain_url else "FAILED"
        },
        "setup_timestamp": datetime.now().isoformat(),
        "oauth_flows": ["code", "implicit"],
        "oauth_scopes": ["openid", "email", "profile"]
    }
    
    # Save configuration
    with open('cognito_oidc_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n🎉 OIDC Cognito Setup Complete!")
    print(f"📋 Configuration saved to: cognito_oidc_config.json")
    print(f"\n📊 Summary:")
    print(f"  User Pool ID: {user_pool_id}")
    print(f"  Client ID: {client_id}")
    print(f"  Domain: {domain_prefix}")
    print(f"  OIDC Discovery: https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid-configuration")
    print(f"  JWKS URI: https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json")
    
    if domain_url:
        print(f"  Authorization URL: {domain_url}/oauth2/authorize")
        print(f"  Token URL: {domain_url}/oauth2/token")
    
    print(f"\n🔐 Test User:")
    print(f"  Email: mbti-test-user@example.com")
    print(f"  Password: MBTITest123!")
    
    return config

if __name__ == "__main__":
    create_oidc_cognito_setup()