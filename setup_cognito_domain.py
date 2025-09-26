#!/usr/bin/env python3
"""
Set up Cognito Custom Domain for AgentCore JWT Authentication
"""

import boto3
import json
import time
from botocore.exceptions import ClientError


def setup_cognito_custom_domain():
    """Set up a custom domain for Cognito User Pool."""
    print("🌐 Setting up Cognito Custom Domain for AgentCore")
    print("=" * 50)
    
    # Load existing config
    try:
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        user_pool_id = config['user_pool']['user_pool_id']
    except:
        print("❌ Could not load Cognito configuration")
        return None
    
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Generate a unique domain name
    import uuid
    domain_name = f"restaurant-mcp-{str(uuid.uuid4())[:8]}"
    
    try:
        print(f"📋 Creating custom domain: {domain_name}")
        
        # Create domain
        response = cognito_client.create_user_pool_domain(
            Domain=domain_name,
            UserPoolId=user_pool_id
        )
        
        print(f"✓ Domain creation initiated")
        print(f"CloudFront Distribution: {response.get('CloudFrontDomain', 'N/A')}")
        
        # Wait for domain to be ready
        print("⏳ Waiting for domain to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                domain_response = cognito_client.describe_user_pool_domain(
                    Domain=domain_name
                )
                
                status = domain_response['DomainDescription']['Status']
                print(f"Domain Status: {status}")
                
                if status == 'ACTIVE':
                    print("✅ Domain is ACTIVE!")
                    break
                elif status == 'FAILED':
                    print("❌ Domain creation failed")
                    return None
                    
                time.sleep(10)
                
            except ClientError as e:
                if 'ResourceNotFoundException' in str(e):
                    print("⏳ Domain still being created...")
                    time.sleep(10)
                else:
                    print(f"❌ Error checking domain: {e}")
                    return None
        
        # Update configuration with new discovery URL
        new_discovery_url = f"https://{domain_name}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration"
        
        config['custom_domain'] = {
            'domain_name': domain_name,
            'discovery_url': new_discovery_url,
            'cloudfront_domain': response.get('CloudFrontDomain')
        }
        config['discovery_url'] = new_discovery_url
        
        # Save updated config
        with open('cognito_config.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"\n✅ Custom Domain Setup Complete!")
        print(f"Domain Name: {domain_name}")
        print(f"New Discovery URL: {new_discovery_url}")
        
        return config
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidParameterException':
            print(f"❌ Domain name already exists or invalid: {domain_name}")
            # Try with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            domain_name = f"restaurant-mcp-{timestamp}"
            print(f"🔄 Retrying with: {domain_name}")
            # Recursive call with new name would go here
        else:
            print(f"❌ Error creating domain: {e}")
        return None


def test_new_discovery_url(config):
    """Test the new discovery URL."""
    if not config or 'custom_domain' not in config:
        return False
    
    import requests
    
    new_url = config['custom_domain']['discovery_url']
    print(f"\n🧪 Testing New Discovery URL:")
    print(f"URL: {new_url}")
    
    try:
        response = requests.get(new_url, timeout=10)
        if response.status_code == 200:
            print("✅ New discovery URL is accessible!")
            discovery_data = response.json()
            print(f"Issuer: {discovery_data.get('issuer', 'N/A')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    config = setup_cognito_custom_domain()
    
    if config:
        success = test_new_discovery_url(config)
        
        if success:
            print(f"\n🎉 Ready for AgentCore JWT Deployment!")
            print(f"Next step: Run deployment with new discovery URL")
        else:
            print(f"\n⚠️ Custom domain created but not yet accessible")
            print(f"Wait a few minutes and try deployment again")
    else:
        print(f"\n❌ Custom domain setup failed")
        print(f"Try manual setup in AWS Console")