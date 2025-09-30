#!/usr/bin/env python3

import json
import subprocess
import sys

# Configuration
DISTRIBUTION_ID = "E2OI88972BLL6O"
RESPONSE_HEADERS_POLICY_ID = "ba9fc5c6-76d2-4437-8ec4-7c07d48997d7"

def run_aws_command(command):
    """Run AWS CLI command and return JSON result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from command: {command}")
        print(f"Output: {result.stdout}")
        sys.exit(1)

def main():
    print("🔧 Updating CloudFront Distribution with CORS headers...")
    
    # Get current distribution configuration
    print("📋 Getting current distribution configuration...")
    get_config_cmd = f"aws cloudfront get-distribution-config --id {DISTRIBUTION_ID} --region us-east-1"
    config_data = run_aws_command(get_config_cmd)
    
    etag = config_data["ETag"]
    dist_config = config_data["DistributionConfig"]
    
    print(f"✅ Current ETag: {etag}")
    
    # Update the default cache behavior with response headers policy
    print("📋 Updating default cache behavior...")
    dist_config["DefaultCacheBehavior"]["ResponseHeadersPolicyId"] = RESPONSE_HEADERS_POLICY_ID
    
    # Ensure proper SPA routing support
    dist_config["CustomErrorResponses"] = {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 403,
                "ResponsePagePath": "/index.html", 
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    }
    
    # Ensure HTTPS redirect
    dist_config["DefaultCacheBehavior"]["ViewerProtocolPolicy"] = "redirect-to-https"
    
    # Enable compression
    dist_config["DefaultCacheBehavior"]["Compress"] = True
    
    # Create update configuration
    update_config = {
        "DistributionConfig": dist_config,
        "IfMatch": etag
    }
    
    # Write configuration to file
    with open("updated-distribution-config.json", "w") as f:
        json.dump(update_config, f, indent=2)
    
    print("📋 Updating CloudFront distribution...")
    
    # Update the distribution
    update_cmd = f"aws cloudfront update-distribution --id {DISTRIBUTION_ID} --cli-input-json file://updated-distribution-config.json --region us-east-1"
    update_result = run_aws_command(update_cmd)
    
    print("✅ CloudFront distribution updated successfully!")
    print(f"📋 Distribution Status: {update_result['Distribution']['Status']}")
    
    # Create invalidation
    print("📋 Creating CloudFront invalidation...")
    
    invalidation_config = {
        "InvalidationBatch": {
            "Paths": {
                "Quantity": 3,
                "Items": ["/*", "/index.html", "/auth/callback"]
            },
            "CallerReference": f"oauth-fix-{int(__import__('time').time())}"
        }
    }
    
    with open("invalidation-config.json", "w") as f:
        json.dump(invalidation_config, f, indent=2)
    
    invalidation_cmd = f"aws cloudfront create-invalidation --distribution-id {DISTRIBUTION_ID} --cli-input-json file://invalidation-config.json --region us-east-1"
    invalidation_result = run_aws_command(invalidation_cmd)
    
    print(f"✅ Invalidation created: {invalidation_result['Invalidation']['Id']}")
    
    # Clean up temporary files
    import os
    for file in ["updated-distribution-config.json", "invalidation-config.json"]:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n🎉 CloudFront configuration updated successfully!")
    print("\n📋 Changes made:")
    print("1. ✅ Added CORS response headers policy")
    print("2. ✅ Improved SPA routing support (404/403 -> index.html)")
    print("3. ✅ Enabled HTTPS redirect")
    print("4. ✅ Enabled compression")
    print("5. ✅ Created cache invalidation")
    
    print("\n⏳ Please wait 5-10 minutes for changes to propagate")
    print("🔗 Test OAuth flow at: https://d39ank8zud5pbg.cloudfront.net/login")

if __name__ == "__main__":
    main()