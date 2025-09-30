#!/usr/bin/env node

/**
 * AWS Infrastructure Deployment Script
 * Deploys CloudFormation stack for MBTI Travel Frontend
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';

const args = process.argv.slice(2);
const environment = args[0] || 'staging';
const domainName = args.find(arg => arg.startsWith('--domain='))?.split('=')[1] || '';
const certificateArn = args.find(arg => arg.startsWith('--cert='))?.split('=')[1] || '';
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');

// Environment configuration
const config = {
  staging: {
    stackName: 'mbti-travel-frontend-staging',
    region: 'us-east-1'
  },
  production: {
    stackName: 'mbti-travel-frontend-production',
    region: 'us-east-1'
  }
};

const deployConfig = config[environment];
if (!deployConfig) {
  console.error(`❌ Unknown environment: ${environment}`);
  process.exit(1);
}

console.log(`🏗️  Deploying infrastructure for ${environment} environment...`);

async function main() {
  try {
    // Validate CloudFormation template
    await validateTemplate();
    
    // Check if stack exists
    const stackExists = await checkStackExists();
    
    if (stackExists) {
      console.log(`📝 Updating existing stack: ${deployConfig.stackName}`);
      await updateStack();
    } else {
      console.log(`🆕 Creating new stack: ${deployConfig.stackName}`);
      await createStack();
    }
    
    // Wait for stack completion
    await waitForStackCompletion();
    
    // Display stack outputs
    await displayStackOutputs();
    
    console.log('✨ Infrastructure deployment completed successfully!');
    
  } catch (error) {
    console.error('❌ Infrastructure deployment failed:', error.message);
    if (verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

async function validateTemplate() {
  console.log('🔍 Validating CloudFormation template...');
  
  if (!existsSync('infrastructure/cloudformation.yml')) {
    throw new Error('CloudFormation template not found at infrastructure/cloudformation.yml');
  }
  
  try {
    const command = `aws cloudformation validate-template --template-body file://infrastructure/cloudformation.yml --region ${deployConfig.region}`;
    execSync(command, { stdio: verbose ? 'inherit' : 'pipe' });
    console.log('✅ Template validation passed');
  } catch (error) {
    throw new Error(`Template validation failed: ${error.message}`);
  }
}

async function checkStackExists() {
  try {
    const command = `aws cloudformation describe-stacks --stack-name ${deployConfig.stackName} --region ${deployConfig.region}`;
    execSync(command, { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
}

async function createStack() {
  const parameters = buildParameters();
  const tags = buildTags();
  
  if (dryRun) {
    console.log('🔍 Dry run: Would create stack with parameters:');
    console.log(JSON.stringify(parameters, null, 2));
    return;
  }
  
  // Write parameters and tags to temporary files to avoid command line issues
  const fs = await import('fs');
  const parametersFile = 'temp-parameters.json';
  const tagsFile = 'temp-tags.json';
  
  fs.writeFileSync(parametersFile, JSON.stringify(parameters));
  fs.writeFileSync(tagsFile, JSON.stringify(tags));
  
  try {
    const command = `aws cloudformation create-stack --stack-name ${deployConfig.stackName} --template-body file://infrastructure/cloudformation.yml --parameters file://${parametersFile} --tags file://${tagsFile} --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --region ${deployConfig.region}`;
    
    execSync(command, { stdio: verbose ? 'inherit' : 'pipe' });
    console.log('✅ Stack creation initiated');
  } finally {
    // Clean up temporary files
    if (fs.existsSync(parametersFile)) fs.unlinkSync(parametersFile);
    if (fs.existsSync(tagsFile)) fs.unlinkSync(tagsFile);
  }
}

async function updateStack() {
  const parameters = buildParameters();
  const tags = buildTags();
  
  if (dryRun) {
    console.log('🔍 Dry run: Would update stack with parameters:');
    console.log(JSON.stringify(parameters, null, 2));
    return;
  }
  
  // Write parameters and tags to temporary files to avoid command line issues
  const fs = await import('fs');
  const parametersFile = 'temp-parameters.json';
  const tagsFile = 'temp-tags.json';
  
  fs.writeFileSync(parametersFile, JSON.stringify(parameters));
  fs.writeFileSync(tagsFile, JSON.stringify(tags));
  
  try {
    const command = `aws cloudformation update-stack --stack-name ${deployConfig.stackName} --template-body file://infrastructure/cloudformation.yml --parameters file://${parametersFile} --tags file://${tagsFile} --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --region ${deployConfig.region}`;
    
    execSync(command, { stdio: verbose ? 'inherit' : 'pipe' });
    console.log('✅ Stack update initiated');
  } catch (error) {
    if (error.message.includes('No updates are to be performed')) {
      console.log('✅ No changes detected in stack');
      return;
    }
    throw error;
  } finally {
    // Clean up temporary files
    if (fs.existsSync(parametersFile)) fs.unlinkSync(parametersFile);
    if (fs.existsSync(tagsFile)) fs.unlinkSync(tagsFile);
  }
}

async function waitForStackCompletion() {
  if (dryRun) {
    return;
  }
  
  console.log('⏳ Waiting for stack operation to complete...');
  
  const command = `aws cloudformation wait stack-update-complete --stack-name ${deployConfig.stackName} --region ${deployConfig.region} || aws cloudformation wait stack-create-complete --stack-name ${deployConfig.stackName} --region ${deployConfig.region}`;
  
  try {
    execSync(command, { stdio: verbose ? 'inherit' : 'pipe', timeout: 1800000 }); // 30 minutes timeout
    console.log('✅ Stack operation completed successfully');
  } catch (error) {
    // Check stack status for better error reporting
    await checkStackStatus();
    throw new Error('Stack operation failed or timed out');
  }
}

async function checkStackStatus() {
  try {
    const command = `aws cloudformation describe-stacks --stack-name ${deployConfig.stackName} --region ${deployConfig.region} --query "Stacks[0].StackStatus" --output text`;
    const status = execSync(command, { encoding: 'utf8' }).trim();
    console.error(`❌ Stack status: ${status}`);
    
    if (status.includes('FAILED')) {
      // Get stack events for debugging
      const eventsCommand = `aws cloudformation describe-stack-events --stack-name ${deployConfig.stackName} --region ${deployConfig.region} --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED'].{Resource:LogicalResourceId,Reason:ResourceStatusReason}" --output table`;
      const events = execSync(eventsCommand, { encoding: 'utf8' });
      console.error('Failed resources:');
      console.error(events);
    }
  } catch (error) {
    console.error('Failed to get stack status');
  }
}

async function displayStackOutputs() {
  if (dryRun) {
    return;
  }
  
  try {
    const command = `aws cloudformation describe-stacks --stack-name ${deployConfig.stackName} --region ${deployConfig.region} --query "Stacks[0].Outputs" --output table`;
    const outputs = execSync(command, { encoding: 'utf8' });
    
    console.log('\n📋 Stack Outputs:');
    console.log(outputs);
  } catch (error) {
    console.warn('⚠️  Failed to get stack outputs:', error.message);
  }
}

function buildParameters() {
  const parameters = [
    {
      ParameterKey: 'Environment',
      ParameterValue: environment
    }
  ];
  
  if (domainName) {
    parameters.push({
      ParameterKey: 'DomainName',
      ParameterValue: domainName
    });
  }
  
  if (certificateArn) {
    parameters.push({
      ParameterKey: 'CertificateArn',
      ParameterValue: certificateArn
    });
  }
  
  return parameters;
}

function buildTags() {
  return [
    {
      Key: 'Project',
      Value: 'MBTI-Travel-Frontend'
    },
    {
      Key: 'Environment',
      Value: environment
    },
    {
      Key: 'ManagedBy',
      Value: 'CloudFormation'
    },
    {
      Key: 'CreatedBy',
      Value: process.env.USER || process.env.USERNAME || 'unknown'
    },
    {
      Key: 'CreatedAt',
      Value: new Date().toISOString()
    }
  ];
}

// Run the deployment
main();