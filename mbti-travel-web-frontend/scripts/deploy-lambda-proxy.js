#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import archiver from 'archiver';

// Configuration
const AWS_REGION = 'us-east-1';
const LAMBDA_FUNCTION_NAME = 'mbti-travel-api-proxy';
const LAMBDA_ROLE_NAME = 'mbti-travel-lambda-proxy-role';
const API_GATEWAY_NAME = 'mbti-travel-proxy-api';

console.log('🚀 Deploying Lambda proxy for MBTI Travel API...');

async function createZipFile() {
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream('lambda-proxy.zip');
    const archive = archiver('zip', { zlib: { level: 9 } });

    output.on('close', () => {
      console.log(`✅ Lambda package created: ${archive.pointer()} bytes`);
      resolve();
    });

    archive.on('error', (err) => {
      reject(err);
    });

    archive.pipe(output);
    archive.file('lambda-proxy/index.js', { name: 'index.js' });
    archive.finalize();
  });
}

async function deployLambda() {
  try {
    // Step 1: Create IAM role for Lambda
    console.log('🔐 Creating IAM role for Lambda...');
    
    const trustPolicy = {
      Version: '2012-10-17',
      Statement: [
        {
          Effect: 'Allow',
          Principal: { Service: 'lambda.amazonaws.com' },
          Action: 'sts:AssumeRole'
        }
      ]
    };

    // Write trust policy to file
    fs.writeFileSync('trust-policy.json', JSON.stringify(trustPolicy, null, 2));
    
    try {
      execSync(`aws iam create-role --role-name ${LAMBDA_ROLE_NAME} --assume-role-policy-document file://trust-policy.json --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ IAM role created');
    } catch (error) {
      if (error.message.includes('EntityAlreadyExists')) {
        console.log('✅ IAM role already exists');
      } else {
        throw error;
      }
    }

    // Attach basic Lambda execution policy
    try {
      execSync(`aws iam attach-role-policy --role-name ${LAMBDA_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
    } catch (error) {
      // Policy might already be attached
    }

    // Wait for IAM role to propagate
    console.log('⏳ Waiting for IAM role to propagate...');
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Step 2: Create Lambda package
    console.log('📦 Creating Lambda deployment package...');
    await createZipFile();

    // Step 3: Deploy Lambda function
    console.log('🚀 Deploying Lambda function...');
    
    const accountId = execSync('aws sts get-caller-identity --query Account --output text', { encoding: 'utf8' }).trim();
    const roleArn = `arn:aws:iam::${accountId}:role/${LAMBDA_ROLE_NAME}`;

    try {
      // Try to create the function
      execSync(`aws lambda create-function --function-name ${LAMBDA_FUNCTION_NAME} --runtime nodejs18.x --role ${roleArn} --handler index.handler --zip-file fileb://lambda-proxy.zip --timeout 180 --memory-size 256 --region ${AWS_REGION}`, {
        stdio: 'inherit'
      });
      console.log('✅ Lambda function created');
    } catch (error) {
      if (error.message.includes('ResourceConflictException')) {
        // Function exists, update it
        console.log('📝 Updating existing Lambda function...');
        execSync(`aws lambda update-function-code --function-name ${LAMBDA_FUNCTION_NAME} --zip-file fileb://lambda-proxy.zip --region ${AWS_REGION}`, {
          stdio: 'inherit'
        });
        console.log('✅ Lambda function updated');
      } else {
        throw error;
      }
    }

    // Step 4: Create API Gateway
    console.log('🌐 Creating API Gateway...');
    
    let apiId;
    try {
      const createApiResult = execSync(`aws apigateway create-rest-api --name ${API_GATEWAY_NAME} --region ${AWS_REGION}`, {
        encoding: 'utf8'
      });
      const apiData = JSON.parse(createApiResult);
      apiId = apiData.id;
      console.log(`✅ API Gateway created: ${apiId}`);
    } catch (error) {
      if (error.message.includes('TooManyRequestsException')) {
        // Get existing API
        const existingApis = execSync(`aws apigateway get-rest-apis --region ${AWS_REGION}`, { encoding: 'utf8' });
        const apis = JSON.parse(existingApis);
        const existingApi = apis.items.find(api => api.name === API_GATEWAY_NAME);
        if (existingApi) {
          apiId = existingApi.id;
          console.log(`✅ Using existing API Gateway: ${apiId}`);
        } else {
          throw error;
        }
      } else {
        throw error;
      }
    }

    // Get root resource ID
    const resourcesResult = execSync(`aws apigateway get-resources --rest-api-id ${apiId} --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });
    const resources = JSON.parse(resourcesResult);
    const rootResource = resources.items.find(item => item.path === '/');
    const rootResourceId = rootResource.id;

    // Create generate-itinerary resource
    let resourceId;
    try {
      const createResourceResult = execSync(`aws apigateway create-resource --rest-api-id ${apiId} --parent-id ${rootResourceId} --path-part generate-itinerary --region ${AWS_REGION}`, {
        encoding: 'utf8'
      });
      const resourceData = JSON.parse(createResourceResult);
      resourceId = resourceData.id;
      console.log('✅ API resource created');
    } catch (error) {
      // Resource might already exist
      const updatedResources = execSync(`aws apigateway get-resources --rest-api-id ${apiId} --region ${AWS_REGION}`, {
        encoding: 'utf8'
      });
      const updatedResourcesData = JSON.parse(updatedResources);
      const existingResource = updatedResourcesData.items.find(item => item.pathPart === 'generate-itinerary');
      if (existingResource) {
        resourceId = existingResource.id;
        console.log('✅ Using existing API resource');
      } else {
        throw error;
      }
    }

    // Create POST method
    try {
      execSync(`aws apigateway put-method --rest-api-id ${apiId} --resource-id ${resourceId} --http-method POST --authorization-type NONE --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ POST method created');
    } catch (error) {
      // Method might already exist
    }

    // Create OPTIONS method for CORS
    try {
      execSync(`aws apigateway put-method --rest-api-id ${apiId} --resource-id ${resourceId} --http-method OPTIONS --authorization-type NONE --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ OPTIONS method created');
    } catch (error) {
      // Method might already exist
    }

    // Set up Lambda integration
    const lambdaArn = `arn:aws:lambda:${AWS_REGION}:${accountId}:function:${LAMBDA_FUNCTION_NAME}`;
    const integrationUri = `arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations`;

    try {
      execSync(`aws apigateway put-integration --rest-api-id ${apiId} --resource-id ${resourceId} --http-method POST --type AWS_PROXY --integration-http-method POST --uri ${integrationUri} --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ Lambda integration created');
    } catch (error) {
      // Integration might already exist
    }

    // Set up OPTIONS integration for CORS
    try {
      execSync(`aws apigateway put-integration --rest-api-id ${apiId} --resource-id ${resourceId} --http-method OPTIONS --type MOCK --request-templates '{"application/json": "{\\"statusCode\\": 200}"}' --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ OPTIONS integration created');
    } catch (error) {
      // Integration might already exist
    }

    // Add Lambda permission for API Gateway
    try {
      execSync(`aws lambda add-permission --function-name ${LAMBDA_FUNCTION_NAME} --statement-id api-gateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${AWS_REGION}:${accountId}:${apiId}/*/*" --region ${AWS_REGION}`, {
        stdio: 'pipe'
      });
      console.log('✅ Lambda permission added');
    } catch (error) {
      // Permission might already exist
    }

    // Deploy API
    console.log('🚀 Deploying API Gateway...');
    execSync(`aws apigateway create-deployment --rest-api-id ${apiId} --stage-name prod --region ${AWS_REGION}`, {
      stdio: 'inherit'
    });

    // Clean up
    fs.unlinkSync('lambda-proxy.zip');
    if (fs.existsSync('trust-policy.json')) {
      fs.unlinkSync('trust-policy.json');
    }

    console.log('✅ Deployment completed successfully!');
    console.log('');
    console.log('📋 Deployment Summary:');
    console.log(`🔗 API Gateway URL: https://${apiId}.execute-api.${AWS_REGION}.amazonaws.com/prod/generate-itinerary`);
    console.log(`⚡ Lambda Function: ${LAMBDA_FUNCTION_NAME}`);
    console.log(`🔐 IAM Role: ${LAMBDA_ROLE_NAME}`);
    console.log('');
    console.log('🔧 Next step: Update frontend .env.production with the API Gateway URL');

    return `https://${apiId}.execute-api.${AWS_REGION}.amazonaws.com/prod`;

  } catch (error) {
    console.error('❌ Deployment failed:', error.message);
    process.exit(1);
  }
}

// Check if archiver is available
try {
  await import('archiver');
} catch (error) {
  console.log('📦 Installing required dependencies...');
  execSync('npm install archiver', { stdio: 'inherit' });
}

deployLambda().then((apiUrl) => {
  console.log(`\n🎉 Ready to test! API URL: ${apiUrl}`);
}).catch(console.error);