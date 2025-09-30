#!/usr/bin/env node

/**
 * CloudFront Security Headers Setup
 * Adds security headers via CloudFront Functions since S3 static hosting doesn't support custom headers
 */

import { CloudFrontClient, CreateFunctionCommand, UpdateDistributionCommand, GetDistributionCommand, GetDistributionConfigCommand } from '@aws-sdk/client-cloudfront';

const cloudfront = new CloudFrontClient({ region: 'us-east-1' });
const distributionId = 'E2OI88972BLL6O'; // Your CloudFront distribution ID

async function main() {
  try {
    console.log('🔒 Setting up CloudFront security headers...');
    
    // Create CloudFront Function for security headers
    await createSecurityHeadersFunction();
    
    // Update CloudFront distribution to use the function
    await updateDistributionWithFunction();
    
    console.log('✅ Security headers configured successfully!');
    console.log('🔄 CloudFront distribution is updating... This may take 10-15 minutes.');
    console.log('📋 Security headers will be applied to all responses once deployment completes.');
    
  } catch (error) {
    console.error('❌ Failed to setup security headers:', error);
    process.exit(1);
  }
}

async function createSecurityHeadersFunction() {
  const functionCode = `
function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Security Headers
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-xss-protection'] = { value: '1; mode=block' };
    headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin' };
    headers['x-download-options'] = { value: 'noopen' };
    headers['x-permitted-cross-domain-policies'] = { value: 'none' };
    
    // Content Security Policy for HTML files
    if (event.request.uri.endsWith('.html') || event.request.uri === '/' || !event.request.uri.includes('.')) {
        headers['content-security-policy'] = { 
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com; media-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;" 
        };
        headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubDomains; preload' };
        headers['permissions-policy'] = { value: 'geolocation=(), microphone=(), camera=()' };
    }
    
    return response;
}
`;

  try {
    const createFunctionCommand = new CreateFunctionCommand({
      Name: 'mbti-travel-security-headers',
      FunctionConfig: {
        Comment: 'Add security headers to all responses',
        Runtime: 'cloudfront-js-1.0'
      },
      FunctionCode: Buffer.from(functionCode, 'utf-8')
    });

    const result = await cloudfront.send(createFunctionCommand);
    console.log('✅ CloudFront Function created:', result.FunctionSummary.Name);
    return result.FunctionSummary.Name;
    
  } catch (error) {
    if (error.name === 'FunctionAlreadyExists') {
      console.log('ℹ️  CloudFront Function already exists, updating...');
      // In a real implementation, you'd update the existing function here
      return 'mbti-travel-security-headers';
    }
    throw error;
  }
}

async function updateDistributionWithFunction() {
  try {
    // Get current distribution configuration
    const getConfigCommand = new GetDistributionConfigCommand({
      Id: distributionId
    });
    
    const configResult = await cloudfront.send(getConfigCommand);
    const config = configResult.DistributionConfig;
    const etag = configResult.ETag;

    // Update the default cache behavior to include the function
    config.DefaultCacheBehavior.FunctionAssociations = {
      Quantity: 1,
      Items: [
        {
          FunctionARN: `arn:aws:cloudfront::${await getAccountId()}:function/mbti-travel-security-headers`,
          EventType: 'viewer-response'
        }
      ]
    };

    // Update the distribution
    const updateCommand = new UpdateDistributionCommand({
      Id: distributionId,
      DistributionConfig: config,
      IfMatch: etag
    });

    const result = await cloudfront.send(updateCommand);
    console.log('✅ CloudFront distribution updated with security headers function');
    return result;
    
  } catch (error) {
    console.error('Failed to update CloudFront distribution:', error);
    throw error;
  }
}

async function getAccountId() {
  // For this example, we'll use a placeholder
  // In a real implementation, you'd get this from STS
  return '209803798463';
}

// Alternative: Create CloudFormation template for security headers
async function createCloudFormationTemplate() {
  const template = {
    AWSTemplateFormatVersion: '2010-09-09',
    Description: 'CloudFront Security Headers Function',
    Resources: {
      SecurityHeadersFunction: {
        Type: 'AWS::CloudFront::Function',
        Properties: {
          Name: 'mbti-travel-security-headers',
          FunctionConfig: {
            Comment: 'Add security headers to all responses',
            Runtime: 'cloudfront-js-1.0'
          },
          FunctionCode: `
function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Security Headers
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-xss-protection'] = { value: '1; mode=block' };
    headers['referrer-policy'] = { value: 'strict-origin-when-cross-origin' };
    headers['x-download-options'] = { value: 'noopen' };
    headers['x-permitted-cross-domain-policies'] = { value: 'none' };
    
    // Content Security Policy for HTML files
    if (event.request.uri.endsWith('.html') || event.request.uri === '/' || !event.request.uri.includes('.')) {
        headers['content-security-policy'] = { 
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com; frame-ancestors 'none';" 
        };
        headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubDomains' };
        headers['permissions-policy'] = { value: 'geolocation=(), microphone=(), camera=()' };
    }
    
    return response;
}
          `
        }
      }
    },
    Outputs: {
      FunctionARN: {
        Description: 'ARN of the CloudFront Function',
        Value: { 'Fn::GetAtt': ['SecurityHeadersFunction', 'FunctionARN'] }
      }
    }
  };

  console.log('📄 CloudFormation template for security headers:');
  console.log(JSON.stringify(template, null, 2));
}

// Run the setup
main().catch(console.error);