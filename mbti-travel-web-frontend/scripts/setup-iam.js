#!/usr/bin/env node

/**
 * IAM Setup Script for MBTI Travel Frontend Deployment
 * Sets up the necessary IAM permissions for deployment
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync } from 'fs';

const args = process.argv.slice(2);
const createUser = args.includes('--create-user');
const userName = args.find(arg => arg.startsWith('--user='))?.split('=')[1] || '';
const attachToRole = args.find(arg => arg.startsWith('--role='))?.split('=')[1] || '';
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');

console.log('🔐 Setting up IAM permissions for MBTI Travel Frontend deployment...');

async function main() {
  try {
    if (attachToRole) {
      await attachPolicyToRole();
    } else if (createUser) {
      await deployIAMStack();
    } else {
      await showCurrentPermissions();
    }
    
    console.log('✨ IAM setup completed successfully!');
    
  } catch (error) {
    console.error('❌ IAM setup failed:', error.message);
    if (verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

async function attachPolicyToRole() {
  console.log(`🔗 Attaching deployment policy to role: ${attachToRole}`);
  
  if (dryRun) {
    console.log('🔍 Dry run: Would attach policy to role');
    return;
  }
  
  // First, create the managed policy
  const policyDocument = readFileSync('infrastructure/iam-policies.json', 'utf8');
  const policyName = 'MBTITravelFrontendDeploymentPolicy';
  
  try {
    // Check if policy already exists
    const existingPolicy = execSync(`aws iam get-policy --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/${policyName}`, 
      { encoding: 'utf8', stdio: 'pipe' });
    console.log('✅ Policy already exists');
  } catch (error) {
    // Policy doesn't exist, create it
    console.log('📝 Creating managed policy...');
    const createPolicyCommand = `aws iam create-policy --policy-name ${policyName} --policy-document file://infrastructure/iam-policies.json --description "Policy for deploying MBTI Travel Frontend to AWS"`;
    execSync(createPolicyCommand, { stdio: verbose ? 'inherit' : 'pipe' });
    console.log('✅ Managed policy created');
  }
  
  // Attach policy to role
  const accountId = execSync('aws sts get-caller-identity --query Account --output text', { encoding: 'utf8' }).trim();
  const policyArn = `arn:aws:iam::${accountId}:policy/${policyName}`;
  
  const attachCommand = `aws iam attach-role-policy --role-name ${attachToRole} --policy-arn ${policyArn}`;
  execSync(attachCommand, { stdio: verbose ? 'inherit' : 'pipe' });
  console.log(`✅ Policy attached to role: ${attachToRole}`);
}

async function deployIAMStack() {
  console.log('🏗️  Deploying IAM CloudFormation stack...');
  
  const stackName = 'mbti-travel-frontend-iam';
  const parameters = [];
  
  if (createUser) {
    parameters.push({
      ParameterKey: 'CreateUser',
      ParameterValue: 'true'
    });
  }
  
  if (userName) {
    parameters.push({
      ParameterKey: 'UserName',
      ParameterValue: userName
    });
  }
  
  if (dryRun) {
    console.log('🔍 Dry run: Would deploy IAM stack with parameters:');
    console.log(JSON.stringify(parameters, null, 2));
    return;
  }
  
  // Write parameters to temporary file
  const parametersFile = 'temp-iam-parameters.json';
  writeFileSync(parametersFile, JSON.stringify(parameters));
  
  try {
    // Check if stack exists
    let stackExists = false;
    try {
      execSync(`aws cloudformation describe-stacks --stack-name ${stackName}`, { stdio: 'pipe' });
      stackExists = true;
    } catch (error) {
      // Stack doesn't exist
    }
    
    if (stackExists) {
      console.log('📝 Updating existing IAM stack...');
      const updateCommand = `aws cloudformation update-stack --stack-name ${stackName} --template-body file://infrastructure/iam-setup.yml --parameters file://${parametersFile} --capabilities CAPABILITY_NAMED_IAM`;
      execSync(updateCommand, { stdio: verbose ? 'inherit' : 'pipe' });
    } else {
      console.log('🆕 Creating new IAM stack...');
      const createCommand = `aws cloudformation create-stack --stack-name ${stackName} --template-body file://infrastructure/iam-setup.yml --parameters file://${parametersFile} --capabilities CAPABILITY_NAMED_IAM`;
      execSync(createCommand, { stdio: verbose ? 'inherit' : 'pipe' });
    }
    
    // Wait for stack completion
    console.log('⏳ Waiting for stack operation to complete...');
    const waitCommand = stackExists ? 
      `aws cloudformation wait stack-update-complete --stack-name ${stackName}` :
      `aws cloudformation wait stack-create-complete --stack-name ${stackName}`;
    
    execSync(waitCommand, { stdio: verbose ? 'inherit' : 'pipe', timeout: 600000 }); // 10 minutes timeout
    
    // Display stack outputs
    await displayStackOutputs(stackName);
    
  } finally {
    // Clean up temporary file
    try {
      const fs = await import('fs');
      if (fs.existsSync(parametersFile)) {
        fs.unlinkSync(parametersFile);
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  }
}

async function displayStackOutputs(stackName) {
  try {
    const command = `aws cloudformation describe-stacks --stack-name ${stackName} --query "Stacks[0].Outputs" --output table`;
    const outputs = execSync(command, { encoding: 'utf8' });
    
    console.log('\n📋 IAM Stack Outputs:');
    console.log(outputs);
    
    // Get specific outputs for easy access
    const outputsJson = execSync(`aws cloudformation describe-stacks --stack-name ${stackName} --query "Stacks[0].Outputs" --output json`, { encoding: 'utf8' });
    const parsedOutputs = JSON.parse(outputsJson);
    
    const accessKeyOutput = parsedOutputs.find(output => output.OutputKey === 'AccessKeyId');
    const secretKeyOutput = parsedOutputs.find(output => output.OutputKey === 'SecretAccessKey');
    const roleArnOutput = parsedOutputs.find(output => output.OutputKey === 'GitHubActionsRoleArn');
    
    if (accessKeyOutput && secretKeyOutput) {
      console.log('\n🔑 AWS Credentials for Deployment:');
      console.log(`AWS_ACCESS_KEY_ID=${accessKeyOutput.OutputValue}`);
      console.log(`AWS_SECRET_ACCESS_KEY=${secretKeyOutput.OutputValue}`);
      console.log('\n⚠️  Store these credentials securely! They will not be shown again.');
    }
    
    if (roleArnOutput) {
      console.log('\n🎭 GitHub Actions Role ARN:');
      console.log(roleArnOutput.OutputValue);
      console.log('\nUse this role ARN in your GitHub Actions workflow for OIDC authentication.');
    }
    
  } catch (error) {
    console.warn('⚠️  Failed to get stack outputs:', error.message);
  }
}

async function showCurrentPermissions() {
  console.log('🔍 Checking current AWS permissions...');
  
  try {
    // Get current identity
    const identity = execSync('aws sts get-caller-identity', { encoding: 'utf8' });
    const identityData = JSON.parse(identity);
    
    console.log('\n👤 Current AWS Identity:');
    console.log(`User/Role: ${identityData.Arn}`);
    console.log(`Account: ${identityData.Account}`);
    
    // Check if we have the required permissions by testing a few key actions
    const permissionTests = [
      {
        name: 'CloudFormation',
        command: 'aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --max-items 1',
        required: true
      },
      {
        name: 'S3',
        command: 'aws s3 ls --max-items 1',
        required: true
      },
      {
        name: 'CloudFront',
        command: 'aws cloudfront list-distributions --max-items 1',
        required: true
      },
      {
        name: 'IAM',
        command: 'aws iam list-roles --max-items 1',
        required: false
      }
    ];
    
    console.log('\n🧪 Permission Tests:');
    for (const test of permissionTests) {
      try {
        execSync(test.command, { stdio: 'pipe' });
        console.log(`✅ ${test.name}: Access granted`);
      } catch (error) {
        const status = test.required ? '❌' : '⚠️ ';
        console.log(`${status} ${test.name}: Access denied`);
        if (test.required) {
          console.log(`   Required for deployment. Run: node scripts/setup-iam.js --role=YourRoleName`);
        }
      }
    }
    
    console.log('\n📖 Next Steps:');
    console.log('1. If you see ❌ errors above, you need additional permissions');
    console.log('2. Option A: Attach policy to existing role:');
    console.log('   node scripts/setup-iam.js --role=YourRoleName');
    console.log('3. Option B: Create new IAM user with permissions:');
    console.log('   node scripts/setup-iam.js --create-user');
    console.log('4. Option C: Have your AWS admin attach the policy manually');
    console.log('   Policy file: infrastructure/iam-policies.json');
    
  } catch (error) {
    console.error('❌ Failed to check permissions:', error.message);
  }
}

// Run the setup
main();