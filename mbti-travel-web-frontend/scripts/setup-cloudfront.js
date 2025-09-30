#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';

// Configuration
const BUCKET_NAME = 'mbti-travel-production-209803798463';
const DISTRIBUTION_COMMENT = 'MBTI Travel Frontend Distribution';
const AWS_REGION = 'us-east-1';

console.log('🚀 Setting up CloudFront distribution for HTTPS access...');

async function setupCloudFront() {
  try {
    // Step 1: Create CloudFront distribution configuration
    const distributionConfig = {
      CallerReference: `mbti-travel-${Date.now()}`,
      Comment: DISTRIBUTION_COMMENT,
      DefaultCacheBehavior: {
        TargetOriginId: 'S3-mbti-travel-origin',
        ViewerProtocolPolicy: 'redirect-to-https',
        TrustedSigners: {
          Enabled: false,
          Quantity: 0
        },
        ForwardedValues: {
          QueryString: false,
          Cookies: {
            Forward: 'none'
          }
        },
        MinTTL: 0,
        DefaultTTL: 86400,
        MaxTTL: 31536000,
        Compress: true,
        AllowedMethods: {
          Quantity: 7,
          Items: ['GET', 'HEAD', 'OPTIONS', 'PUT', 'POST', 'PATCH', 'DELETE'],
          CachedMethods: {
            Quantity: 2,
            Items: ['GET', 'HEAD']
          }
        }
      },
      Origins: {
        Quantity: 1,
        Items: [
          {
            Id: 'S3-mbti-travel-origin',
            DomainName: `${BUCKET_NAME}.s3-website-${AWS_REGION}.amazonaws.com`,
            CustomOriginConfig: {
              HTTPPort: 80,
              HTTPSPort: 443,
              OriginProtocolPolicy: 'http-only'
            }
          }
        ]
      },
      Enabled: true,
      DefaultRootObject: 'index.html',
      CustomErrorResponses: {
        Quantity: 1,
        Items: [
          {
            ErrorCode: 404,
            ResponsePagePath: '/index.html',
            ResponseCode: '200',
            ErrorCachingMinTTL: 300
          }
        ]
      },
      PriceClass: 'PriceClass_100'
    };

    // Write distribution config to file
    fs.writeFileSync('cloudfront-config.json', JSON.stringify({
      DistributionConfig: distributionConfig
    }, null, 2));

    console.log('📋 Creating CloudFront distribution...');
    
    // Create the distribution
    const createResult = execSync(`aws cloudfront create-distribution --cli-input-json file://cloudfront-config.json --region ${AWS_REGION}`, {
      encoding: 'utf8'
    });

    const distribution = JSON.parse(createResult);
    const distributionId = distribution.Distribution.Id;
    const domainName = distribution.Distribution.DomainName;

    console.log(`✅ CloudFront distribution created!`);
    console.log(`📋 Distribution ID: ${distributionId}`);
    console.log(`🌐 Domain Name: ${domainName}`);
    console.log(`🔗 HTTPS URL: https://${domainName}`);

    // Clean up
    fs.unlinkSync('cloudfront-config.json');

    // Wait for distribution to deploy
    console.log('⏳ Waiting for distribution to deploy (this may take 10-15 minutes)...');
    console.log('💡 You can check status with: aws cloudfront get-distribution --id ' + distributionId);

    return {
      distributionId,
      domainName,
      httpsUrl: `https://${domainName}`
    };

  } catch (error) {
    console.error('❌ CloudFront setup failed:', error.message);
    
    // Clean up on error
    if (fs.existsSync('cloudfront-config.json')) {
      fs.unlinkSync('cloudfront-config.json');
    }
    
    process.exit(1);
  }
}

setupCloudFront().then((result) => {
  console.log('\n🎉 CloudFront setup completed!');
  console.log('\n📋 Next steps:');
  console.log('1. Wait for distribution to deploy (10-15 minutes)');
  console.log('2. Update Cognito User Pool Client with HTTPS URL');
  console.log('3. Update frontend environment configuration');
  console.log(`\n🔗 Your HTTPS URL: ${result.httpsUrl}`);
}).catch(console.error);