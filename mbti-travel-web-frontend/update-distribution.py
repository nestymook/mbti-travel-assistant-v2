#!/usr/bin/env python3

import json
import subprocess
import sys

DISTRIBUTION_ID = "E2OI88972BLL6O"
POLICY_ID = "95f6d017-12cd-4179-a155-54a664b42dc8"

def run_command(cmd):
    """Run AWS CLI command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Command failed: {e}")
        return None

def main():
    print("🔄 Updating CloudFront distribution with security headers policy...")
    
    # Get current distribution config
    print("📋 Getting current distribution configuration...")
    config_cmd = f"aws cloudfront get-distribution-config --id {DISTRIBUTION_ID} --region us-east-1"
    config_result = run_command(config_cmd)
    
    if not config_result:
        print("❌ Failed to get distribution config")
        sys.exit(1)
    
    try:
        config_data = json.loads(config_result)
        distribution_config = config_data['DistributionConfig']
        etag = config_data['ETag']
        
        # Add response headers policy to default cache behavior
        distribution_config['DefaultCacheBehavior']['ResponseHeadersPolicyId'] = POLICY_ID
        
        # Write updated config to file
        with open('updated-distribution-config.json', 'w') as f:
            json.dump(distribution_config, f, indent=2)
        
        print("✅ Configuration updated with security headers policy")
        
        # Update the distribution
        print("🚀 Updating CloudFront distribution...")
        update_cmd = f"aws cloudfront update-distribution --id {DISTRIBUTION_ID} --distribution-config file://updated-distribution-config.json --if-match {etag} --region us-east-1"
        
        update_result = run_command(update_cmd)
        
        if update_result:
            print("✅ CloudFront distribution updated successfully!")
            print("🔒 Security headers policy applied")
            print("⏱️  Changes will take 10-15 minutes to deploy globally")
            print("")
            print("🎯 Security headers that will be added:")
            print("   - X-Content-Type-Options: nosniff")
            print("   - X-Frame-Options: DENY")
            print("   - X-XSS-Protection: 1; mode=block")
            print("   - Referrer-Policy: strict-origin-when-cross-origin")
            print("   - Content-Security-Policy: (comprehensive policy)")
            print("   - Strict-Transport-Security: max-age=31536000")
            print("   - X-Download-Options: noopen")
            print("   - X-Permitted-Cross-Domain-Policies: none")
        else:
            print("❌ Failed to update distribution")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()