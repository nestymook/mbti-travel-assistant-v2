#!/usr/bin/env node

/**
 * Create CloudFront Response Headers Policy for Security Headers
 * This is the recommended approach for adding security headers
 */

import { execSync } from 'child_process';

const DISTRIBUTION_ID = 'E2OI88972BLL6O';

async function main() {
  try {
    console.log('🔒 Creating CloudFront Response Headers Policy for security headers...');
    
    // Create the response headers policy
    const policyId = await createResponseHeadersPolicy();
    
    if (policyId) {
      console.log('✅ Response Headers Policy created successfully!');
      console.log(`📋 Policy ID: ${policyId}`);
      console.log('');
      console.log('🔄 To apply this policy to your CloudFront distribution:');
      console.log('1. Go to AWS CloudFront Console');
      console.log(`2. Select distribution: ${DISTRIBUTION_ID}`);
      console.log('3. Go to Behaviors tab');
      console.log('4. Edit the Default behavior');
      console.log('5. Scroll to Response headers policy');
      console.log(`6. Select: mbti-travel-security-headers`);
      console.log('7. Save changes');
      console.log('');
      console.log('⏱️  Changes will take 10-15 minutes to deploy globally');
    }
    
  } catch (error) {
    console.error('❌ Failed to create security headers policy:', error.message);
    process.exit(1);
  }
}

async function createResponseHeadersPolicy() {
  const policyConfig = {
    Name: 'mbti-travel-security-headers',
    Comment: 'Security headers for MBTI Travel application',
    SecurityHeadersConfig: {
      StrictTransportSecurity: {
        AccessControlMaxAgeSec: 31536000,
        IncludeSubdomains: true,
        Preload: true,
        Override: true
      },
      ContentTypeOptions: {
        Override: true
      },
      FrameOptions: {
        FrameOption: 'DENY',
        Override: true
      },
      XSSProtection: {
        ModeBlock: true,
        Protection: true,
        Override: true
      },
      ReferrerPolicy: {
        ReferrerPolicy: 'strict-origin-when-cross-origin',
        Override: true
      }
    },
    CustomHeadersConfig: {
      Quantity: 3,
      Items: [
        {
          Header: 'X-Download-Options',
          Value: 'noopen',
          Override: true
        },
        {
          Header: 'X-Permitted-Cross-Domain-Policies',
          Value: 'none',
          Override: true
        },
        {
          Header: 'Content-Security-Policy',
          Value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com; frame-ancestors 'none';",
          Override: true
        }
      ]
    }
  };

  try {
    // Write policy config to temporary file
    const configFile = '/tmp/response-headers-policy.json';
    import('fs').then(fs => {
      fs.writeFileSync(configFile, JSON.stringify(policyConfig, null, 2));
    });
    
    // Create the policy using AWS CLI
    const command = `aws cloudfront create-response-headers-policy --response-headers-policy-config file://${configFile} --region us-east-1`;
    
    console.log('📝 Creating response headers policy...');
    const result = execSync(command, { encoding: 'utf-8' });
    const response = JSON.parse(result);
    
    console.log('✅ Policy created successfully');
    return response.ResponseHeadersPolicy.Id;
    
  } catch (error) {
    if (error.message.includes('ResponseHeadersPolicyAlreadyExists')) {
      console.log('ℹ️  Response headers policy already exists');
      
      // Get existing policy ID
      try {
        const listCommand = 'aws cloudfront list-response-headers-policies --region us-east-1';
        const listResult = execSync(listCommand, { encoding: 'utf-8' });
        const policies = JSON.parse(listResult);
        
        const existingPolicy = policies.ResponseHeadersPolicyList.Items.find(
          policy => policy.ResponseHeadersPolicy.ResponseHeadersPolicyConfig.Name === 'mbti-travel-security-headers'
        );
        
        if (existingPolicy) {
          return existingPolicy.ResponseHeadersPolicy.Id;
        }
      } catch (listError) {
        console.error('Failed to get existing policy:', listError.message);
      }
    }
    throw error;
  }
}

// Run the script
main();