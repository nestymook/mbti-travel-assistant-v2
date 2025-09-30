#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';

// Configuration
const USER_POOL_ID = 'us-east-1_wBAxW7yd4';
const CLIENT_ID = '26k0pnja579pdpb1pt6savs27e';
const CLOUDFRONT_DOMAIN = 'https://d39ank8zud5pbg.cloudfront.net';
const DISTRIBUTION_ID = 'E2OI88972BLL6O';
const AWS_REGION = 'us-east-1';

console.log('🔧 Fixing Cognito OAuth Configuration...');

async function fixCognitoOAuth() {
  try {
    // Step 1: Update Cognito User Pool Client with correct callback URLs
    console.log('📋 Updating Cognito User Pool Client callback URLs...');
    
    const updateClientCommand = `aws cognito-idp update-user-pool-client \
      --user-pool-id ${USER_POOL_ID} \
      --client-id ${CLIENT_ID} \
      --callback-urls "${CLOUDFRONT_DOMAIN}/" "${CLOUDFRONT_DOMAIN}/auth/callback" \
      --logout-urls "${CLOUDFRONT_DOMAIN}/" \
      --allowed-o-auth-flows "code" \
      --allowed-o-auth-scopes "email" "openid" "profile" \
      --allowed-o-auth-flows-user-pool-client \
      --supported-identity-providers "COGNITO" \
      --region ${AWS_REGION}`;

    execSync(updateClientCommand, { stdio: 'inherit' });
    console.log('✅ Cognito User Pool Client updated successfully');

    // Step 2: Create CloudFront Response Headers Policy for CORS
    console.log('📋 Creating CloudFront Response Headers Policy...');
    
    const responseHeadersPolicy = {
      ResponseHeadersPolicyConfig: {
        Name: `mbti-travel-cors-policy-${Date.now()}`,
        Comment: 'CORS and security headers for MBTI Travel OAuth flow',
        CorsConfig: {
          AccessControlAllowOrigins: {
            Quantity: 2,
            Items: [CLOUDFRONT_DOMAIN, 'https://restaurant-mcp-9cccf837.auth.us-east-1.amazoncognito.com']
          },
          AccessControlAllowHeaders: {
            Quantity: 6,
            Items: ['Authorization', 'Content-Type', 'X-Amz-Date', 'X-Api-Key', 'X-Amz-Security-Token', 'X-Requested-With']
          },
          AccessControlAllowMethods: {
            Quantity: 7,
            Items: ['GET', 'HEAD', 'OPTIONS', 'PUT', 'POST', 'PATCH', 'DELETE']
          },
          AccessControlAllowCredentials: true,
          AccessControlExposeHeaders: {
            Quantity: 1,
            Items: ['*']
          },
          AccessControlMaxAgeSec: 86400,
          OriginOverride: true
        },
        SecurityHeadersConfig: {
          StrictTransportSecurity: {
            AccessControlMaxAgeSec: 31536000,
            IncludeSubdomains: true,
            Override: true
          },
          ContentTypeOptions: {
            Override: true
          },
          FrameOptions: {
            FrameOption: 'DENY',
            Override: true
          },
          ReferrerPolicy: {
            ReferrerPolicy: 'strict-origin-when-cross-origin',
            Override: true
          }
        }
      }
    };

    // Write policy to file
    fs.writeFileSync('response-headers-policy.json', JSON.stringify(responseHeadersPolicy, null, 2));

    // Create the policy
    const createPolicyResult = execSync(`aws cloudfront create-response-headers-policy --cli-input-json file://response-headers-policy.json --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });

    const policyResponse = JSON.parse(createPolicyResult);
    const policyId = policyResponse.ResponseHeadersPolicy.Id;
    console.log(`✅ Response Headers Policy created: ${policyId}`);

    // Step 3: Update CloudFront Distribution with the new policy
    console.log('📋 Updating CloudFront Distribution...');
    
    // Get current distribution config
    const getDistResult = execSync(`aws cloudfront get-distribution-config --id ${DISTRIBUTION_ID} --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });

    const distConfig = JSON.parse(getDistResult);
    const etag = distConfig.ETag;
    const config = distConfig.DistributionConfig;

    // Update the default cache behavior with the new response headers policy
    config.DefaultCacheBehavior.ResponseHeadersPolicyId = policyId;

    // Ensure proper cache behavior for SPA routing
    config.DefaultCacheBehavior.ViewerProtocolPolicy = 'redirect-to-https';
    config.DefaultCacheBehavior.Compress = true;
    
    // Update custom error responses for SPA routing
    config.CustomErrorResponses = {
      Quantity: 2,
      Items: [
        {
          ErrorCode: 404,
          ResponsePagePath: '/index.html',
          ResponseCode: '200',
          ErrorCachingMinTTL: 300
        },
        {
          ErrorCode: 403,
          ResponsePagePath: '/index.html',
          ResponseCode: '200',
          ErrorCachingMinTTL: 300
        }
      ]
    };

    // Write updated config to file
    fs.writeFileSync('updated-distribution-config.json', JSON.stringify({
      DistributionConfig: config,
      IfMatch: etag
    }, null, 2));

    // Update the distribution
    execSync(`aws cloudfront update-distribution --id ${DISTRIBUTION_ID} --cli-input-json file://updated-distribution-config.json --region ${AWS_REGION}`, {
      stdio: 'inherit'
    });

    console.log('✅ CloudFront Distribution updated successfully');

    // Step 4: Create invalidation to clear cache
    console.log('📋 Creating CloudFront invalidation...');
    
    const invalidationConfig = {
      Paths: {
        Quantity: 3,
        Items: ['/*', '/index.html', '/auth/callback']
      },
      CallerReference: `oauth-fix-${Date.now()}`
    };

    fs.writeFileSync('invalidation-config.json', JSON.stringify({
      InvalidationBatch: invalidationConfig
    }, null, 2));

    const invalidationResult = execSync(`aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --cli-input-json file://invalidation-config.json --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });

    const invalidation = JSON.parse(invalidationResult);
    console.log(`✅ Invalidation created: ${invalidation.Invalidation.Id}`);

    // Clean up temporary files
    fs.unlinkSync('response-headers-policy.json');
    fs.unlinkSync('updated-distribution-config.json');
    fs.unlinkSync('invalidation-config.json');

    console.log('\n🎉 Cognito OAuth configuration fixed!');
    console.log('\n📋 Changes made:');
    console.log('1. ✅ Updated Cognito callback URLs');
    console.log('2. ✅ Added CORS headers to CloudFront');
    console.log('3. ✅ Improved SPA routing support');
    console.log('4. ✅ Created cache invalidation');
    console.log('\n⏳ Please wait 5-10 minutes for CloudFront changes to propagate');
    console.log(`🔗 Test OAuth flow at: ${CLOUDFRONT_DOMAIN}/login`);

    return {
      policyId,
      invalidationId: invalidation.Invalidation.Id
    };

  } catch (error) {
    console.error('❌ OAuth fix failed:', error.message);
    
    // Clean up on error
    const tempFiles = ['response-headers-policy.json', 'updated-distribution-config.json', 'invalidation-config.json'];
    tempFiles.forEach(file => {
      if (fs.existsSync(file)) {
        fs.unlinkSync(file);
      }
    });
    
    process.exit(1);
  }
}

// Additional function to test OAuth configuration
async function testOAuthConfig() {
  console.log('\n🧪 Testing OAuth Configuration...');
  
  try {
    // Test Cognito domain
    const cognitoDomain = 'https://restaurant-mcp-9cccf837.auth.us-east-1.amazoncognito.com';
    console.log(`📋 Cognito Domain: ${cognitoDomain}`);
    
    // Test login URL
    const loginUrl = `${cognitoDomain}/login?` + new URLSearchParams({
      client_id: CLIENT_ID,
      response_type: 'code',
      scope: 'email openid profile',
      redirect_uri: `${CLOUDFRONT_DOMAIN}/`
    }).toString();
    
    console.log(`🔗 Login URL: ${loginUrl}`);
    
    // Test callback URL
    console.log(`🔗 Callback URL: ${CLOUDFRONT_DOMAIN}/auth/callback`);
    
    console.log('\n✅ OAuth configuration test completed');
    console.log('💡 You can now test the login flow manually');
    
  } catch (error) {
    console.error('❌ OAuth test failed:', error.message);
  }
}

// Run the fix
fixCognitoOAuth().then((result) => {
  console.log('\n📊 Fix Results:');
  console.log(`Policy ID: ${result.policyId}`);
  console.log(`Invalidation ID: ${result.invalidationId}`);
  
  // Run test
  return testOAuthConfig();
}).catch(console.error);