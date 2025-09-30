#!/usr/bin/env node

import { execSync } from 'child_process';

// Configuration
const USER_POOL_ID = 'us-east-1_wBAxW7yd4';
const AWS_REGION = 'us-east-1';

console.log('🔧 Creating Test User for Direct Authentication');
console.log('===============================================');

async function createTestUser() {
  try {
    // Get user input for email and password
    const email = process.argv[2];
    const password = process.argv[3];
    
    if (!email || !password) {
      console.log('Usage: node create-test-user.js <email> <password>');
      console.log('Example: node create-test-user.js test@example.com TempPassword123!');
      process.exit(1);
    }
    
    console.log(`📋 Creating user: ${email}`);
    
    // Step 1: Create user
    console.log('📋 Step 1: Creating user in Cognito...');
    
    const createUserCommand = `aws cognito-idp admin-create-user \
      --user-pool-id ${USER_POOL_ID} \
      --username "${email}" \
      --user-attributes Name=email,Value="${email}" Name=email_verified,Value=true \
      --temporary-password "${password}" \
      --message-action SUPPRESS \
      --region ${AWS_REGION}`;

    try {
      execSync(createUserCommand, { stdio: 'inherit' });
      console.log('✅ User created successfully');
    } catch (error) {
      if (error.message.includes('UsernameExistsException')) {
        console.log('⚠️ User already exists, continuing...');
      } else {
        throw error;
      }
    }

    // Step 2: Set permanent password
    console.log('📋 Step 2: Setting permanent password...');
    
    const setPasswordCommand = `aws cognito-idp admin-set-user-password \
      --user-pool-id ${USER_POOL_ID} \
      --username "${email}" \
      --password "${password}" \
      --permanent \
      --region ${AWS_REGION}`;

    execSync(setPasswordCommand, { stdio: 'inherit' });
    console.log('✅ Password set successfully');

    // Step 3: Confirm user (mark as verified)
    console.log('📋 Step 3: Confirming user...');
    
    const confirmUserCommand = `aws cognito-idp admin-confirm-sign-up \
      --user-pool-id ${USER_POOL_ID} \
      --username "${email}" \
      --region ${AWS_REGION}`;

    try {
      execSync(confirmUserCommand, { stdio: 'inherit' });
      console.log('✅ User confirmed successfully');
    } catch (error) {
      if (error.message.includes('NotAuthorizedException')) {
        console.log('⚠️ User already confirmed');
      } else {
        console.log('⚠️ Confirmation failed, but user should still be usable');
      }
    }

    console.log('\n🎉 Test User Created Successfully!');
    console.log('==================================');
    console.log(`📧 Email: ${email}`);
    console.log(`🔑 Password: ${password}`);
    console.log('\n📋 You can now use these credentials to test the direct login:');
    console.log(`1. Go to: https://d39ank8zud5pbg.cloudfront.net/login`);
    console.log(`2. Enter email: ${email}`);
    console.log(`3. Enter password: ${password}`);
    console.log(`4. Click "Sign In"`);
    
    console.log('\n⚠️ Security Note:');
    console.log('This is a test user for development purposes only.');
    console.log('In production, users should sign up through proper registration flow.');

  } catch (error) {
    console.error('❌ Failed to create test user:', error.message);
    
    if (error.message.includes('InvalidParameterException')) {
      console.log('\n💡 Common issues:');
      console.log('- Password must meet complexity requirements (8+ chars, uppercase, lowercase, number, special char)');
      console.log('- Email must be a valid email format');
    }
    
    process.exit(1);
  }
}

// Additional function to list existing users
async function listUsers() {
  console.log('📋 Listing existing users...');
  
  try {
    const listCommand = `aws cognito-idp list-users --user-pool-id ${USER_POOL_ID} --region ${AWS_REGION}`;
    const result = execSync(listCommand, { encoding: 'utf8' });
    const users = JSON.parse(result);
    
    console.log(`Found ${users.Users.length} users:`);
    users.Users.forEach((user, index) => {
      const email = user.Attributes.find(attr => attr.Name === 'email')?.Value || 'No email';
      console.log(`${index + 1}. ${user.Username} (${email}) - Status: ${user.UserStatus}`);
    });
  } catch (error) {
    console.error('Failed to list users:', error.message);
  }
}

// Check command line arguments
if (process.argv.includes('--list')) {
  listUsers();
} else {
  createTestUser();
}