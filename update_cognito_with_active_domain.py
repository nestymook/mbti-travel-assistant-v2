#!/usr/bin/env python3
"""
Update Cognito configuration with the active custom domain
"""

import json


def update_cognito_config():
    """Update Cognito config with the active custom domain."""
    print("🔧 Updating Cognito Configuration with Active Custom Domain")
    print("=" * 55)
    
    try:
        # Load existing config
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        
        # Update with the active custom domain
        domain_prefix = "restaurant-mcp-9cccf837"
        new_discovery_url = f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration"
        
        print(f"📋 Current Discovery URL: {config.get('discovery_url', 'N/A')}")
        print(f"🔄 New Discovery URL: {new_discovery_url}")
        
        # Update configuration
        config['custom_domain'] = {
            'domain_prefix': domain_prefix,
            'domain_url': f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com",
            'discovery_url': new_discovery_url,
            'status': 'ACTIVE'
        }
        config['discovery_url'] = new_discovery_url
        
        # Save updated config
        with open('cognito_config.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print("✅ Configuration updated successfully!")
        print(f"Domain: {domain_prefix}")
        print(f"Status: ACTIVE")
        print(f"Discovery URL: {new_discovery_url}")
        
        return config
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return None


def test_new_discovery_url():
    """Test the new discovery URL."""
    import requests
    
    domain_prefix = "restaurant-mcp-9cccf837"
    new_url = f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration"
    
    print(f"\n🧪 Testing New Discovery URL:")
    print(f"URL: {new_url}")
    
    try:
        response = requests.get(new_url, timeout=10)
        if response.status_code == 200:
            print("✅ New discovery URL is accessible!")
            discovery_data = response.json()
            print(f"Issuer: {discovery_data.get('issuer', 'N/A')}")
            print(f"Authorization Endpoint: {discovery_data.get('authorization_endpoint', 'N/A')}")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    config = update_cognito_config()
    
    if config:
        success = test_new_discovery_url()
        
        if success:
            print(f"\n🎉 Ready for JWT Authentication Deployment!")
            print(f"Next step: python execute_deployment.py")
        else:
            print(f"\n⚠️ Domain is ACTIVE but URL not yet accessible")
            print(f"Wait a few more minutes for DNS propagation")
    else:
        print(f"\n❌ Configuration update failed")