#!/usr/bin/env python3
"""
Manually update Cognito configuration with custom domain
"""

import json


def update_cognito_config_with_domain(domain_prefix):
    """Update the Cognito configuration with custom domain."""
    print(f"🔧 Updating Cognito Configuration with Custom Domain")
    print(f"Domain Prefix: {domain_prefix}")
    
    try:
        # Load existing config
        with open('cognito_config.json', 'r') as f:
            config = json.load(f)
        
        # Update with custom domain
        new_discovery_url = f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com/.well-known/openid_configuration"
        
        config['custom_domain'] = {
            'domain_prefix': domain_prefix,
            'domain_url': f"https://{domain_prefix}.auth.us-east-1.amazoncognito.com",
            'discovery_url': new_discovery_url
        }
        config['discovery_url'] = new_discovery_url
        
        # Save updated config
        with open('cognito_config.json', 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"✅ Configuration updated!")
        print(f"New Discovery URL: {new_discovery_url}")
        
        return config
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return None


if __name__ == "__main__":
    print("📋 Manual Configuration Update")
    print("After creating custom domain in AWS Console:")
    print("1. Run: python update_cognito_config_manual.py")
    print("2. Provide your domain prefix when prompted")
    print("3. Then run: python execute_deployment.py")
    
    # Example usage
    domain_prefix = input("Enter your Cognito domain prefix: ").strip()
    if domain_prefix:
        update_cognito_config_with_domain(domain_prefix)