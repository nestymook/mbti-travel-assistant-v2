#!/usr/bin/env node

/**
 * Simple S3 Deployment Script (No CloudFront)
 * Works with limited AWS permissions
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';

const args = process.argv.slice(2);
const environment = args[0] || 'staging';
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');

// Environment configuration
const config = {
  staging: {
    stackName: 'mbti-travel-frontend-simple-staging',
    region: 'us-east-1'
  },
  production: {
    stackName: 'mbti-travel-frontend-simple-production',
    region: 'us-east-1'
  }
};

const deployConfig = config[environment];
if (!deployConfig) {
  console.error(`❌ Unknown environment: ${environment}`);
  process.exit(1);
}

console.log(`🚀 Deploying MBTI Travel Frontend (Simple S3) to ${environment}...`);

async function main() {
  try {
    // Deploy infrastructure first
    await deployInfrastructure();
    
    // Get stack outputs
    const stackOutputs = await getStackOutputs();
    
    if (!stackOutputs.S3BucketName) {
      console.error('❌ S3 bucket name not found in stack outputs');
      process.exit(1);
    }
    
    // Upload files to S3
    await uploadToS3(stackOutputs.S3BucketName);
    
    console.log('✨ Deployment completed successfully!');
    console.log(`🌐 Website URL: ${stackOutputs.WebsiteURL}`);
    
  } catch (error) {
    console.error('❌ Deployment failed:', error.message);
    if (verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

async function deployInfrastructure() {
  console.log('🏗️  Deploying S3 infrastructure...');
  
  // Check if stack exists
  let stackExists = false;
  try {
    execSync(`aws cloudformation describe-stacks --stack-name ${deployConfig.stackName} --region ${deployConfig.region}`, { stdio: 'pipe' });
    stackExists = true;
  } catch (error) {
    // Stack doesn't exist
  }
  
  const parameters = [
    {
      ParameterKey: 'Environment',
      ParameterValue: environment
    }
  ];
  
  // Write parameters to temporary file
  const parametersFile = 'temp-simple-parameters.json';
  writeFileSync(parametersFile, JSON.stringify(parameters));
  
  try {
    if (stackExists) {
      console.log('📝 Updating existing infrastructure stack...');
      try {
        const updateCommand = `aws cloudformation update-stack --stack-name ${deployConfig.stackName} --template-body file://infrastructure/simple-s3-cloudformation.yml --parameters file://${parametersFile} --region ${deployConfig.region}`;
        execSync(updateCommand, { stdio: verbose ? 'inherit' : 'pipe' });
        
        console.log('⏳ Waiting for stack update to complete...');
        execSync(`aws cloudformation wait stack-update-complete --stack-name ${deployConfig.stackName} --region ${deployConfig.region}`, { 
          stdio: verbose ? 'inherit' : 'pipe',
          timeout: 600000 
        });
      } catch (error) {
        if (error.message.includes('No updates are to be performed')) {
          console.log('✅ No infrastructure changes needed');
        } else {
          throw error;
        }
      }
    } else {
      console.log('🆕 Creating new infrastructure stack...');
      const createCommand = `aws cloudformation create-stack --stack-name ${deployConfig.stackName} --template-body file://infrastructure/simple-s3-cloudformation.yml --parameters file://${parametersFile} --region ${deployConfig.region}`;
      execSync(createCommand, { stdio: verbose ? 'inherit' : 'pipe' });
      
      console.log('⏳ Waiting for stack creation to complete...');
      execSync(`aws cloudformation wait stack-create-complete --stack-name ${deployConfig.stackName} --region ${deployConfig.region}`, { 
        stdio: verbose ? 'inherit' : 'pipe',
        timeout: 600000 
      });
    }
    
    console.log('✅ Infrastructure deployment completed');
    
  } finally {
    // Clean up temporary file
    if (existsSync(parametersFile)) {
      const fs = await import('fs');
      fs.unlinkSync(parametersFile);
    }
  }
}

async function getStackOutputs() {
  console.log(`🔍 Getting stack outputs for ${deployConfig.stackName}...`);
  
  try {
    const command = `aws cloudformation describe-stacks --stack-name ${deployConfig.stackName} --region ${deployConfig.region} --query "Stacks[0].Outputs" --output json`;
    const result = execSync(command, { encoding: 'utf8' });
    const outputs = JSON.parse(result);
    
    const outputMap = {};
    outputs.forEach(output => {
      outputMap[output.OutputKey] = output.OutputValue;
    });
    
    return outputMap;
  } catch (error) {
    throw new Error(`Failed to get stack outputs: ${error.message}`);
  }
}

async function uploadToS3(bucketName) {
  console.log(`📤 Uploading to S3 bucket: ${bucketName}`);
  
  if (!existsSync('dist/index.html')) {
    throw new Error('Build not found. Run npm run build:staging first.');
  }
  
  if (dryRun) {
    console.log('🔍 Dry run: Would upload files to S3');
    return;
  }
  
  try {
    // Sync files to S3 with proper content types and cache headers
    const syncCommand = `aws s3 sync dist/ s3://${bucketName}/ --delete --region ${deployConfig.region}`;
    execSync(syncCommand, { stdio: verbose ? 'inherit' : 'pipe' });
    
    // Set specific content types and cache headers for different file types
    const fileTypes = [
      { pattern: '*.html', contentType: 'text/html', cacheControl: 'no-cache, no-store, must-revalidate' },
      { pattern: '*.css', contentType: 'text/css', cacheControl: 'public, max-age=31536000' },
      { pattern: '*.js', contentType: 'application/javascript', cacheControl: 'public, max-age=31536000' },
      { pattern: '*.json', contentType: 'application/json', cacheControl: 'public, max-age=3600' },
      { pattern: '*.png', contentType: 'image/png', cacheControl: 'public, max-age=31536000' },
      { pattern: '*.jpg', contentType: 'image/jpeg', cacheControl: 'public, max-age=31536000' },
      { pattern: '*.svg', contentType: 'image/svg+xml', cacheControl: 'public, max-age=31536000' },
      { pattern: '*.ico', contentType: 'image/x-icon', cacheControl: 'public, max-age=31536000' }
    ];
    
    for (const fileType of fileTypes) {
      try {
        const metadataCommand = `aws s3 cp s3://${bucketName}/ s3://${bucketName}/ --recursive --exclude "*" --include "${fileType.pattern}" --metadata-directive REPLACE --content-type "${fileType.contentType}" --cache-control "${fileType.cacheControl}" --region ${deployConfig.region}`;
        execSync(metadataCommand, { stdio: verbose ? 'inherit' : 'pipe' });
      } catch (error) {
        console.warn(`⚠️  Failed to set metadata for ${fileType.pattern}:`, error.message);
      }
    }
    
    console.log('✅ Files uploaded successfully');
    
  } catch (error) {
    throw new Error(`Failed to upload to S3: ${error.message}`);
  }
}

// Run the deployment
main();