#!/usr/bin/env node

/**
 * AWS Cognito User Pool Setup Script
 * Creates a Cognito User Pool and App Client for MBTI Travel application
 */

import { execSync } from 'child_process';
import { writeFileSync, readFileSync, existsSync } from 'fs';

const REGION = 'us-east-1';
const USER_POOL_NAME = 'mbti-travel-user-pool';
const APP_CLIENT_NAME = 'mbti-travel-web-client';

console.log('🚀 Setting up AWS Cognito User Pool for MBTI Travel...');

async function main() {
  try {
    // Check AWS CLI access
    console.log('✅ Checking AWS CLI access...');
    execSync('aws sts get-caller-identity', { stdio: 'pipe' });
    
    // Create User Pool
    console.log('📝 Creating Cognito User Pool...');
    const userPoolResult = execSync(`aws cognito-idp create-user-pool \\
      --pool-name "${USER_POOL_NAME}" \\
      --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=true}" \\
      --auto-verified-attributes email \\
      --username-attributes email \\
      --verification-message-template "DefaultEmailOption=CONFIRM_WITH_CODE" \\
      --admin-create-user-config "AllowAdminCreateUserOnly=false" \\
      --region ${REGION} \\
      --output json`, { encoding: 'utf8' });
    
    const userPool = JSON.parse(userPoolResult);
    const userPoolId = userPool.UserPool.Id;
    console.log(`✅ User Pool created: ${userPoolId}`);
    
    // Create App Client
    console.log('📱 Creating App Client...');
    const appClientResult = execSync(`aws cognito-idp create-user-pool-client \\
      --user-pool-id "${userPoolId}" \\
      --client-name "${APP_CLIENT_NAME}" \\
      --no-generate-secret \\
      --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_USER_SRP_AUTH \\
      --supported-identity-providers COGNITO \\
      --callback-urls "http://localhost:5173/login" "http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com/login" \\
      --logout-urls "http://localhost:5173/" "http://mbti-travel-production-209803798463.s3-website-us-east-1.amazonaws.com/" \\
      --region ${REGION} \\
      --output json`, { encoding: 'utf8' });
    
    const appClient = JSON.parse(appClientResult);
    const clientId = appClient.UserPoolClient.ClientId;
    console.log(`✅ App Client created: ${clientId}`);
    
    // Update environment files
    console.log('📄 Updating environment configuration...');
    updateEnvironmentFile('.env.production', userPoolId, clientId);
    updateEnvironmentFile('.env.development', userPoolId, clientId);
    
    // Create a test user
    console.log('👤 Creating test user...');
    try {
      execSync(`aws cognito-idp admin-create-user \\
        --user-pool-id "${userPoolId}" \\
        --username "test@mbti-travel.com" \\
        --user-attributes Name=email,Value=test@mbti-travel.com Name=name,Value="Test User" \\
        --temporary-password "TempPass123!" \\
        --message-action SUPPRESS \\
        --region ${REGION}`, { stdio: 'pipe' });
      
      // Set permanent password
      execSync(`aws cognito-idp admin-set-user-password \\
        --user-pool-id "${userPoolId}" \\
        --username "test@mbti-travel.com" \\
        --password "TestPass123!" \\
        --permanent \\
        --region ${REGION}`, { stdio: 'pipe' });
      
      console.log('✅ Test user created: test@mbti-travel.com / TestPass123!');
    } catch (error) {
      console.log('⚠️  Test user creation failed (may already exist)');
    }
    
    // Save configuration
    const config = {
      userPoolId,
      clientId,
      region: REGION,
      testUser: {
        email: 'test@mbti-travel.com',
        password: 'TestPass123!'
      }
    };
    
    writeFileSync('cognito-config.json', JSON.stringify(config, null, 2));
    
    console.log('\\n🎉 Cognito setup completed successfully!');
    console.log('\\n📋 Configuration:');
    console.log(`   User Pool ID: ${userPoolId}`);
    console.log(`   Client ID: ${clientId}`);
    console.log(`   Region: ${REGION}`);
    console.log('\\n🧪 Test Credentials:');
    console.log('   Email: test@mbti-travel.com');
    console.log('   Password: TestPass123!');
    console.log('\\n📁 Configuration saved to: cognito-config.json');
    console.log('\\n🔄 Please rebuild and redeploy the application to use Cognito authentication.');
    
  } catch (error) {
    console.error('❌ Cognito setup failed:', error.message);
    process.exit(1);
  }
}

function updateEnvironmentFile(filename, userPoolId, clientId) {
  if (!existsSync(filename)) {
    console.log(`⚠️  ${filename} not found, skipping...`);
    return;
  }
  
  let content = readFileSync(filename, 'utf8');
  
  // Update Cognito configuration
  content = content.replace(
    /VITE_COGNITO_USER_POOL_ID=.*/,
    `VITE_COGNITO_USER_POOL_ID=${userPoolId}`
  );
  content = content.replace(
    /VITE_COGNITO_CLIENT_ID=.*/,
    `VITE_COGNITO_CLIENT_ID=${clientId}`
  );
  
  // Remove the domain line as we're not using hosted UI
  content = content.replace(/VITE_COGNITO_DOMAIN=.*\\n?/, '');
  
  writeFileSync(filename, content);
  console.log(`✅ Updated ${filename}`);
}

// Run the setup
main();