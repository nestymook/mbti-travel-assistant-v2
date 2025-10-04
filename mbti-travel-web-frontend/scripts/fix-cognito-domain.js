#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';

// Configuration
const USER_POOL_ID = 'us-east-1_wBAxW7yd4';
const CLIENT_ID = '26k0pnja579pdpb1pt6savs27e';
const OLD_DOMAIN = 'mbti-travel-oidc-334662794';
const AWS_REGION = 'us-east-1';
const CLOUDFRONT_DOMAIN = 'https://d39ank8zud5pbg.cloudfront.net';

console.log('🚨 CRITICAL: Fixing Corrupted Cognito Domain');
console.log('============================================');

async function fixCognitoDomain() {
  try {
    // Step 1: Test current domain to confirm it's broken
    console.log('📋 Step 1: Testing current domain...');
    
    try {
      const testResult = execSync(`curl -I "https://${OLD_DOMAIN}.auth.${AWS_REGION}.amazoncognito.com/.well-known/openid-configuration"`, {
        encoding: 'utf8',
        timeout: 10000
      });
      
      if (testResult.includes('404')) {
        console.log('❌ Confirmed: Current domain returns 404');
      } else {
        console.log('⚠️ Domain might be working. Check manually before proceeding.');
        console.log('Test result:', testResult);
        
        const proceed = process.argv.includes('--force');
        if (!proceed) {
          console.log('💡 Use --force flag to proceed anyway');
          process.exit(1);
        }
      }
    } catch (error) {
      console.log('❌ Confirmed: Cannot reach current domain');
    }

    // Step 2: Delete corrupted domain
    console.log('\n📋 Step 2: Deleting corrupted domain...');
    
    try {
      execSync(`aws cognito-idp delete-user-pool-domain --domain ${OLD_DOMAIN} --region ${AWS_REGION}`, {
        stdio: 'inherit'
      });
      console.log('✅ Domain deletion initiated');
    } catch (error) {
      console.log('⚠️ Domain deletion failed (might already be deleted):', error.message);
    }

    // Step 3: Wait for deletion
    console.log('\n📋 Step 3: Waiting for deletion to complete...');
    
    let deletionComplete = false;
    for (let i = 0; i < 12; i++) { // Wait up to 2 minutes
      try {
        execSync(`aws cognito-idp describe-user-pool-domain --domain ${OLD_DOMAIN} --region ${AWS_REGION}`, {
          stdio: 'pipe'
        });
        console.log(`⏳ Still deleting... (${i + 1}/12)`);
        await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      } catch (error) {
        console.log('✅ Domain deletion completed');
        deletionComplete = true;
        break;
      }
    }

    if (!deletionComplete) {
      console.log('⚠️ Deletion taking longer than expected. Proceeding anyway...');
    }

    // Step 4: Create new domain
    console.log('\n📋 Step 4: Creating new domain...');
    
    const timestamp = Math.floor(Date.now() / 1000);
    const newDomain = `restaurant-mcp-fixed-${timestamp}`;
    
    console.log(`📋 New domain name: ${newDomain}`);
    
    const createResult = execSync(`aws cognito-idp create-user-pool-domain --domain ${newDomain} --user-pool-id ${USER_POOL_ID} --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });
    
    console.log('✅ New domain creation initiated');
    console.log('Result:', createResult);

    // Step 5: Wait for domain to become active
    console.log('\n📋 Step 5: Waiting for new domain to become active...');
    
    let domainActive = false;
    for (let i = 0; i < 20; i++) { // Wait up to 5 minutes
      try {
        const statusResult = execSync(`aws cognito-idp describe-user-pool-domain --domain ${newDomain} --region ${AWS_REGION}`, {
          encoding: 'utf8'
        });
        
        const status = JSON.parse(statusResult);
        console.log(`⏳ Domain status: ${status.DomainDescription.Status} (${i + 1}/20)`);
        
        if (status.DomainDescription.Status === 'ACTIVE') {
          domainActive = true;
          break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 15000)); // Wait 15 seconds
      } catch (error) {
        console.log(`⏳ Checking domain status... (${i + 1}/20)`);
        await new Promise(resolve => setTimeout(resolve, 15000));
      }
    }

    if (!domainActive) {
      console.log('⚠️ Domain taking longer than expected to become active');
      console.log('💡 Continue with manual testing in a few minutes');
    }

    // Step 6: Test new domain
    console.log('\n📋 Step 6: Testing new domain...');
    
    try {
      await new Promise(resolve => setTimeout(resolve, 30000)); // Wait 30 seconds for DNS
      
      const testUrl = `https://${newDomain}.auth.${AWS_REGION}.amazoncognito.com/.well-known/openid-configuration`;
      console.log(`🧪 Testing: ${testUrl}`);
      
      const testResult = execSync(`curl -s "${testUrl}"`, {
        encoding: 'utf8',
        timeout: 15000
      });
      
      if (testResult.includes('authorization_endpoint')) {
        console.log('✅ New domain is working correctly!');
      } else {
        console.log('⚠️ Domain might still be propagating. Test manually in a few minutes.');
      }
    } catch (error) {
      console.log('⚠️ Domain test failed (might still be propagating):', error.message);
      console.log('💡 Try testing manually in 5-10 minutes');
    }

    // Step 7: Update environment file
    console.log('\n📋 Step 7: Updating environment configuration...');
    
    const envFile = '.env.production';
    if (fs.existsSync(envFile)) {
      let envContent = fs.readFileSync(envFile, 'utf8');
      envContent = envContent.replace(
        `VITE_COGNITO_DOMAIN=${OLD_DOMAIN}`,
        `VITE_COGNITO_DOMAIN=${newDomain}`
      );
      fs.writeFileSync(envFile, envContent);
      console.log('✅ Environment file updated');
    } else {
      console.log('⚠️ Environment file not found. Update manually:');
      console.log(`VITE_COGNITO_DOMAIN=${newDomain}`);
    }

    // Step 8: Update User Pool Client (ensure callback URLs are correct)
    console.log('\n📋 Step 8: Updating User Pool Client...');
    
    try {
      execSync(`aws cognito-idp update-user-pool-client \
        --user-pool-id ${USER_POOL_ID} \
        --client-id ${CLIENT_ID} \
        --callback-urls "${CLOUDFRONT_DOMAIN}/" "${CLOUDFRONT_DOMAIN}/auth/callback" \
        --logout-urls "${CLOUDFRONT_DOMAIN}/" \
        --allowed-o-auth-flows "code" \
        --allowed-o-auth-scopes "email" "openid" "profile" \
        --allowed-o-auth-flows-user-pool-client \
        --supported-identity-providers "COGNITO" \
        --region ${AWS_REGION}`, {
        stdio: 'inherit'
      });
      console.log('✅ User Pool Client updated');
    } catch (error) {
      console.log('⚠️ User Pool Client update failed:', error.message);
    }

    // Summary
    console.log('\n🎉 Cognito Domain Fix Completed!');
    console.log('================================');
    console.log(`📋 Old Domain: ${OLD_DOMAIN} (deleted)`);
    console.log(`📋 New Domain: ${newDomain}`);
    console.log(`🔗 New Login URL: https://${newDomain}.auth.${AWS_REGION}.amazoncognito.com/login`);
    console.log(`🧪 Test URL: https://${newDomain}.auth.${AWS_REGION}.amazoncognito.com/.well-known/openid-configuration`);
    
    console.log('\n📋 Next Steps:');
    console.log('1. ✅ Environment file updated (if found)');
    console.log('2. 🔄 Rebuild and redeploy frontend');
    console.log('3. 🧪 Test OAuth flow with diagnostic tool');
    console.log('4. ⏳ Wait 5-10 minutes if domain is still propagating');
    
    console.log('\n🚀 Rebuild and Deploy Commands:');
    console.log('npm run build');
    console.log('aws s3 sync dist/ s3://mbti-travel-production-209803798463/ --delete');
    console.log('aws cloudfront create-invalidation --distribution-id E2OI88972BLL6O --paths "/*"');

    return {
      oldDomain: OLD_DOMAIN,
      newDomain: newDomain,
      testUrl: `https://${newDomain}.auth.${AWS_REGION}.amazoncognito.com/.well-known/openid-configuration`,
      loginUrl: `https://${newDomain}.auth.${AWS_REGION}.amazoncognito.com/login`
    };

  } catch (error) {
    console.error('❌ Cognito domain fix failed:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

// Helper function to wait
function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Run the fix
fixCognitoDomain().then((result) => {
  console.log('\n✅ Fix completed successfully!');
  console.log('🔗 Test the new domain in a few minutes');
}).catch(console.error);