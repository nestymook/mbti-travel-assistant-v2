#!/usr/bin/env node

/**
 * Deployment Script
 * Handles deployment to different environments
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';

const args = process.argv.slice(2);
const environment = args[0] || 'staging';
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');

console.log(`🚀 Deploying MBTI Travel Frontend to ${environment}...`);

// Validate build exists
if (!existsSync('dist/index.html')) {
  console.error('❌ Build not found. Run npm run build first.');
  process.exit(1);
}

// Read build info
let buildInfo;
try {
  buildInfo = JSON.parse(readFileSync('dist/build-info.json', 'utf8'));
} catch {
  console.error('❌ Build info not found. Run npm run build first.');
  process.exit(1);
}

console.log(`📦 Deploying build ${buildInfo.version} (${buildInfo.commit.slice(0, 8)})`);

try {
  switch (environment) {
    case 'staging':
      deployToStaging();
      break;
    case 'production':
      deployToProduction();
      break;
    default:
      console.error(`❌ Unknown environment: ${environment}`);
      process.exit(1);
  }
  
  console.log('✨ Deployment completed successfully!');
  
} catch (error) {
  console.error('❌ Deployment failed:', error.message);
  process.exit(1);
}

function deployToStaging() {
  console.log('🔄 Deploying to staging environment...');
  
  // Example: Deploy to AWS S3 + CloudFront
  if (!dryRun) {
    execSync('aws s3 sync dist/ s3://staging-mbti-travel-frontend --delete', {
      stdio: verbose ? 'inherit' : 'pipe'
    });
    
    execSync('aws cloudfront create-invalidation --distribution-id E1234567890 --paths "/*"', {
      stdio: verbose ? 'inherit' : 'pipe'
    });
  } else {
    console.log('🔍 Dry run: Would sync to s3://staging-mbti-travel-frontend');
  }
}

function deployToProduction() {
  console.log('🔄 Deploying to production environment...');
  
  // Additional safety checks for production
  if (!process.env.PRODUCTION_DEPLOY_KEY) {
    console.error('❌ PRODUCTION_DEPLOY_KEY environment variable required');
    process.exit(1);
  }
  
  // Example: Deploy to AWS S3 + CloudFront
  if (!dryRun) {
    execSync('aws s3 sync dist/ s3://prod-mbti-travel-frontend --delete', {
      stdio: verbose ? 'inherit' : 'pipe'
    });
    
    execSync('aws cloudfront create-invalidation --distribution-id E0987654321 --paths "/*"', {
      stdio: verbose ? 'inherit' : 'pipe'
    });
  } else {
    console.log('🔍 Dry run: Would sync to s3://prod-mbti-travel-frontend');
  }
}