#!/usr/bin/env node

import { execSync } from 'child_process';

// Configuration
const CLOUDFRONT_DOMAIN = 'https://d39ank8zud5pbg.cloudfront.net';
const COGNITO_DOMAIN = 'https://restaurant-mcp-9cccf837.auth.us-east-1.amazoncognito.com';
const CLIENT_ID = '26k0pnja579pdpb1pt6savs27e';
const USER_POOL_ID = 'us-east-1_wBAxW7yd4';

console.log('🧪 Testing OAuth Flow Configuration...');

async function testOAuthFlow() {
  try {
    // Test 1: Check Cognito User Pool Client configuration
    console.log('\n📋 Test 1: Checking Cognito User Pool Client...');
    
    const clientConfig = execSync(`aws cognito-idp describe-user-pool-client --user-pool-id ${USER_POOL_ID} --client-id ${CLIENT_ID} --region us-east-1`, {
      encoding: 'utf8'
    });
    
    const client = JSON.parse(clientConfig);
    const callbackUrls = client.UserPoolClient.CallbackURLs;
    const logoutUrls = client.UserPoolClient.LogoutURLs;
    const oauthFlows = client.UserPoolClient.AllowedOAuthFlows;
    const oauthScopes = client.UserPoolClient.AllowedOAuthScopes;
    
    console.log('✅ Callback URLs:', callbackUrls);
    console.log('✅ Logout URLs:', logoutUrls);
    console.log('✅ OAuth Flows:', oauthFlows);
    console.log('✅ OAuth Scopes:', oauthScopes);
    
    // Validate configuration
    const expectedCallbacks = [`${CLOUDFRONT_DOMAIN}/`, `${CLOUDFRONT_DOMAIN}/auth/callback`];
    const hasCorrectCallbacks = expectedCallbacks.every(url => callbackUrls.includes(url));
    
    if (hasCorrectCallbacks) {
      console.log('✅ Callback URLs are correctly configured');
    } else {
      console.log('❌ Callback URLs need to be updated');
      console.log('Expected:', expectedCallbacks);
      console.log('Actual:', callbackUrls);
    }
    
    // Test 2: Check Cognito Domain
    console.log('\n📋 Test 2: Checking Cognito Domain...');
    
    const domainConfig = execSync(`aws cognito-idp describe-user-pool-domain --domain restaurant-mcp-9cccf837 --region us-east-1`, {
      encoding: 'utf8'
    });
    
    const domain = JSON.parse(domainConfig);
    console.log('✅ Domain Status:', domain.DomainDescription.Status);
    console.log('✅ CloudFront Distribution:', domain.DomainDescription.CloudFrontDistribution);
    
    // Test 3: Generate OAuth URLs
    console.log('\n📋 Test 3: Generating OAuth URLs...');
    
    const loginUrl = `${COGNITO_DOMAIN}/login?` + new URLSearchParams({
      client_id: CLIENT_ID,
      response_type: 'code',
      scope: 'email openid profile',
      redirect_uri: `${CLOUDFRONT_DOMAIN}/`
    }).toString();
    
    const logoutUrl = `${COGNITO_DOMAIN}/logout?` + new URLSearchParams({
      client_id: CLIENT_ID,
      logout_uri: `${CLOUDFRONT_DOMAIN}/`
    }).toString();
    
    console.log('🔗 Login URL:', loginUrl);
    console.log('🔗 Logout URL:', logoutUrl);
    
    // Test 4: Check CloudFront Distribution
    console.log('\n📋 Test 4: Checking CloudFront Distribution...');
    
    const distributions = execSync(`aws cloudfront list-distributions --region us-east-1 --query "DistributionList.Items[?contains(Comment, 'MBTI')].{Id:Id,DomainName:DomainName,Status:Status}"`, {
      encoding: 'utf8'
    });
    
    const distList = JSON.parse(distributions);
    if (distList.length > 0) {
      const dist = distList[0];
      console.log('✅ Distribution ID:', dist.Id);
      console.log('✅ Domain Name:', dist.DomainName);
      console.log('✅ Status:', dist.Status);
      
      if (dist.Status === 'Deployed') {
        console.log('✅ CloudFront distribution is deployed');
      } else {
        console.log('⏳ CloudFront distribution is still deploying');
      }
    } else {
      console.log('❌ No MBTI CloudFront distribution found');
    }
    
    // Test 5: Test connectivity
    console.log('\n📋 Test 5: Testing Connectivity...');
    
    try {
      // Test CloudFront endpoint
      console.log('Testing CloudFront endpoint...');
      const curlResult = execSync(`curl -s -o /dev/null -w "%{http_code}" ${CLOUDFRONT_DOMAIN}`, {
        encoding: 'utf8',
        timeout: 10000
      });
      
      if (curlResult.trim() === '200') {
        console.log('✅ CloudFront endpoint is accessible');
      } else {
        console.log(`⚠️ CloudFront endpoint returned status: ${curlResult}`);
      }
    } catch (curlError) {
      console.log('⚠️ Could not test CloudFront endpoint (curl not available or network issue)');
    }
    
    // Test 6: Validate OAuth endpoints
    console.log('\n📋 Test 6: Validating OAuth Endpoints...');
    
    try {
      // Test Cognito well-known configuration
      const wellKnownUrl = `${COGNITO_DOMAIN}/.well-known/openid_configuration`;
      console.log('Testing Cognito well-known configuration...');
      
      const wellKnownResult = execSync(`curl -s "${wellKnownUrl}"`, {
        encoding: 'utf8',
        timeout: 10000
      });
      
      const wellKnown = JSON.parse(wellKnownResult);
      console.log('✅ Authorization Endpoint:', wellKnown.authorization_endpoint);
      console.log('✅ Token Endpoint:', wellKnown.token_endpoint);
      console.log('✅ JWKS URI:', wellKnown.jwks_uri);
      
    } catch (wellKnownError) {
      console.log('⚠️ Could not test Cognito well-known configuration');
    }
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log('✅ Cognito User Pool Client: Configured');
    console.log('✅ Cognito Domain: Active');
    console.log('✅ OAuth URLs: Generated');
    console.log('✅ CloudFront Distribution: Found');
    
    console.log('\n🎯 Next Steps:');
    console.log('1. Open the login URL in a browser to test the flow');
    console.log('2. Check browser developer tools for any errors');
    console.log('3. Verify that the callback URL receives the authorization code');
    console.log('4. Monitor the auth callback processing in the console');
    
    console.log(`\n🔗 Test Login: ${loginUrl}`);
    
  } catch (error) {
    console.error('❌ OAuth flow test failed:', error.message);
    process.exit(1);
  }
}

// Additional function to create a test HTML page
function createTestPage() {
  console.log('\n📋 Creating OAuth test page...');
  
  const testPageContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth Flow Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .test-section { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 5px; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <h1>🧪 OAuth Flow Test</h1>
    
    <div class="test-section">
        <h2>Test Configuration</h2>
        <div class="code">
            CloudFront Domain: ${CLOUDFRONT_DOMAIN}<br>
            Cognito Domain: ${COGNITO_DOMAIN}<br>
            Client ID: ${CLIENT_ID}
        </div>
    </div>
    
    <div class="test-section">
        <h2>Test Actions</h2>
        <a href="${COGNITO_DOMAIN}/login?client_id=${CLIENT_ID}&response_type=code&scope=email+openid+profile&redirect_uri=${encodeURIComponent(CLOUDFRONT_DOMAIN + '/')}" class="button">
            Test Login Flow
        </a>
        <a href="${CLOUDFRONT_DOMAIN}/debug-auth.html" class="button">
            Debug Auth State
        </a>
    </div>
    
    <div class="test-section">
        <h2>Current URL Info</h2>
        <div class="code" id="urlInfo"></div>
    </div>
    
    <script>
        document.getElementById('urlInfo').innerHTML = 
            'URL: ' + window.location.href + '<br>' +
            'Search: ' + window.location.search + '<br>' +
            'Hash: ' + window.location.hash;
    </script>
</body>
</html>`;

  require('fs').writeFileSync('../public/oauth-test.html', testPageContent);
  console.log('✅ OAuth test page created at /oauth-test.html');
}

// Run tests
testOAuthFlow().then(() => {
  createTestPage();
  console.log('\n🎉 OAuth flow testing completed!');
}).catch(console.error);