#!/usr/bin/env python3
"""
Diagnose Cognito Configuration Issues for AgentCore JWT Authentication
"""

import boto3
import json
import requests
from botocore.exceptions import ClientError


def diagnose_cognito_config():
    """Diagnose the current Cognito configuration."""
    print("🔍 Diagnosing Cognito Configuration for AgentCore JWT")
    print("=" * 55)
    
    try:
        # Load current config
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        
        user_pool_id = config['user_pool']['user_pool_id']
        client_id = config['app_client']['client_id']
        discovery_url = config['discovery_url']
        
        print(f"📋 Current Configuration:")
        print(f"User Pool ID: {user_pool_id}")
        print(f"Client ID: {client_id}")
        print(f"Discovery URL: {discovery_url}")
        
        # Test discovery URL accessibility
        print(f"\n🌐 Testing Discovery URL Accessibility:")
        try:
            response = requests.get(discovery_url, timeout=10)
            print(f"✓ Discovery URL is accessible (Status: {response.status_code})")
            
            if response.status_code == 200:
                discovery_data = response.json()
                print(f"✓ Discovery document is valid JSON")
                print(f"Issuer: {discovery_data.get('issuer', 'N/A')}")
                print(f"Authorization Endpoint: {discovery_data.get('authorization_endpoint', 'N/A')}")
                print(f"Token Endpoint: {discovery_data.get('token_endpoint', 'N/A')}")
                print(f"JWKS URI: {discovery_data.get('jwks_uri', 'N/A')}")
            else:
                print(f"⚠️ Discovery URL returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Discovery URL not accessible: {e}")
        
        # Check User Pool details via AWS API
        print(f"\n🔧 Checking User Pool via AWS API:")
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        
        try:
            pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            pool_info = pool_response['UserPool']
            
            print(f"✓ User Pool exists and is accessible")
            print(f"Pool Name: {pool_info.get('Name', 'N/A')}")
            print(f"Pool Status: {pool_info.get('Status', 'N/A')}")
            print(f"Domain: {pool_info.get('Domain', 'N/A')}")
            
            # Check if pool has a custom domain
            if 'Domain' in pool_info and pool_info['Domain']:
                custom_discovery_url = f"https://{pool_info['Domain']}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration"
                print(f"🔗 Custom Domain Discovery URL: {custom_discovery_url}")
            
        except ClientError as e:
            print(f"❌ Error accessing User Pool: {e}")
        
        # Check App Client details
        print(f"\n📱 Checking App Client via AWS API:")
        try:
            client_response = cognito_client.describe_user_pool_client(
                UserPoolId=user_pool_id,
                ClientId=client_id
            )
            client_info = client_response['UserPoolClient']
            
            print(f"✓ App Client exists and is accessible")
            print(f"Client Name: {client_info.get('ClientName', 'N/A')}")
            print(f"Explicit Auth Flows: {client_info.get('ExplicitAuthFlows', [])}")
            print(f"Supported Identity Providers: {client_info.get('SupportedIdentityProviders', [])}")
            
        except ClientError as e:
            print(f"❌ Error accessing App Client: {e}")
        
        return config
        
    except FileNotFoundError:
        print("❌ Cognito configuration file not found")
        return None
    except Exception as e:
        print(f"💥 Error diagnosing configuration: {e}")
        return None


def suggest_fixes():
    """Suggest potential fixes for the JWT authentication issue."""
    print(f"\n🛠️ Potential Fixes for JWT Authentication:")
    print("=" * 45)
    
    print("1. **URL Format Issue**:")
    print("   - AgentCore may require a specific URL format")
    print("   - Try removing trailing slashes or extra characters")
    
    print("\n2. **Custom Domain Requirement**:")
    print("   - AgentCore may require a custom Cognito domain")
    print("   - Set up a custom domain for your User Pool")
    
    print("\n3. **User Pool Configuration**:")
    print("   - Ensure User Pool is in ACTIVE status")
    print("   - Verify all required OAuth flows are enabled")
    
    print("\n4. **Regional Issues**:")
    print("   - Ensure User Pool and AgentCore are in same region (us-east-1)")
    print("   - Check if region-specific URL format is required")
    
    print("\n5. **Alternative Approaches**:")
    print("   - Deploy without authentication first (working)")
    print("   - Add JWT authentication later via AgentCore console")
    print("   - Use API Gateway authorizer instead")


def create_fixed_cognito_config():
    """Create a new Cognito configuration with potential fixes."""
    print(f"\n🔧 Creating Fixed Cognito Configuration:")
    print("=" * 40)
    
    try:
        # Try different URL formats
        user_pool_id = "us-east-1_wBAxW7yd4"  # From existing config
        
        # Standard format (current)
        standard_url = f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid_configuration"
        
        # Alternative formats to try
        alt_formats = [
            f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid-configuration",
            f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/openid_configuration/",
            f"https://{user_pool_id}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration",
        ]
        
        print("🧪 Testing Alternative URL Formats:")
        for i, url in enumerate(alt_formats, 1):
            print(f"{i}. {url}")
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✓ Accessible (Status: {response.status_code})")
                else:
                    print(f"   ❌ Status: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return alt_formats
        
    except Exception as e:
        print(f"💥 Error testing formats: {e}")
        return []


if __name__ == "__main__":
    # Diagnose current configuration
    config = diagnose_cognito_config()
    
    # Suggest fixes
    suggest_fixes()
    
    # Test alternative formats
    alt_urls = create_fixed_cognito_config()
    
    print(f"\n📋 Next Steps:")
    print("1. Try deploying without authentication (working)")
    print("2. Set up Cognito custom domain")
    print("3. Test alternative discovery URL formats")
    print("4. Contact AWS Support for AgentCore-specific requirements")