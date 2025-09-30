#!/usr/bin/env node

/**
 * AWS Deployment Script for MBTI Travel Frontend
 * Handles deployment to different environments with proper AWS integration
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, relative, extname } from 'path';
import { createHash } from 'crypto';

const args = process.argv.slice(2);
const environment = args[0] || 'staging';
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');
const skipInvalidation = args.includes('--skip-invalidation');

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

console.log(`📦 Deploying build ${buildInfo.version} (${buildInfo.commit?.slice(0, 8) || 'unknown'})`);

async function main() {
  try {
    // Get stack outputs
    const stackOutputs = await getStackOutputs();
    
    if (!stackOutputs.S3BucketName || !stackOutputs.CloudFrontDistributionId) {
      console.error('❌ Required stack outputs not found. Deploy infrastructure first.');
      process.exit(1);
    }
    
    console.log(`📤 Uploading to S3 bucket: ${stackOutputs.S3BucketName}`);
    
    // Upload files to S3
    await uploadToS3(stackOutputs.S3BucketName);
    
    // Invalidate CloudFront cache
    if (!skipInvalidation) {
      await invalidateCloudFront(stackOutputs.CloudFrontDistributionId);
    }
    
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
  const distPath = 'dist';
  const files = getAllFiles(distPath);
  
  console.log(`📁 Found ${files.length} files to upload`);
  
  if (dryRun) {
    console.log('🔍 Dry run: Would upload the following files:');
    files.forEach(file => {
      const relativePath = relative(distPath, file);
      console.log(`  - ${relativePath}`);
    });
    return;
  }
  
  // Upload files with proper content types and cache headers
  for (const file of files) {
    const relativePath = relative(distPath, file).replace(/\\/g, '/');
    const contentType = getContentType(file);
    const cacheControl = getCacheControl(relativePath);
    
    try {
      const command = `aws s3 cp "${file}" "s3://${bucketName}/${relativePath}" --content-type "${contentType}" --cache-control "${cacheControl}" --region ${deployConfig.region}`;
      
      if (verbose) {
        console.log(`📤 Uploading: ${relativePath}`);
      }
      
      execSync(command, { stdio: verbose ? 'inherit' : 'pipe' });
      
      if (!verbose) {
        process.stdout.write('.');
      }
    } catch (error) {
      throw new Error(`Failed to upload ${relativePath}: ${error.message}`);
    }
  }
  
  if (!verbose) {
    console.log(''); // New line after dots
  }
  
  console.log(`✅ Successfully uploaded ${files.length} files`);
  
  // Clean up old files (remove files that no longer exist)
  await cleanupOldFiles(bucketName, files.map(f => relative(distPath, f).replace(/\\/g, '/')));
}

async function cleanupOldFiles(bucketName, currentFiles) {
  try {
    console.log('🧹 Cleaning up old files...');
    
    const command = `aws s3 ls "s3://${bucketName}/" --recursive --region ${deployConfig.region}`;
    const result = execSync(command, { encoding: 'utf8' });
    
    const s3Files = result.split('\n')
      .filter(line => line.trim())
      .map(line => line.split(/\s+/).slice(3).join(' '))
      .filter(file => file);
    
    const filesToDelete = s3Files.filter(s3File => !currentFiles.includes(s3File));
    
    if (filesToDelete.length > 0) {
      console.log(`🗑️  Deleting ${filesToDelete.length} old files`);
      
      for (const file of filesToDelete) {
        if (!dryRun) {
          const deleteCommand = `aws s3 rm "s3://${bucketName}/${file}" --region ${deployConfig.region}`;
          execSync(deleteCommand, { stdio: verbose ? 'inherit' : 'pipe' });
        }
        
        if (verbose) {
          console.log(`🗑️  Deleted: ${file}`);
        }
      }
    } else {
      console.log('✅ No old files to clean up');
    }
  } catch (error) {
    console.warn('⚠️  Failed to clean up old files:', error.message);
  }
}

async function invalidateCloudFront(distributionId) {
  console.log(`🔄 Invalidating CloudFront distribution: ${distributionId}`);
  
  if (dryRun) {
    console.log('🔍 Dry run: Would invalidate CloudFront cache');
    return;
  }
  
  try {
    const invalidationId = Date.now().toString();
    const command = `aws cloudfront create-invalidation --distribution-id ${distributionId} --paths "/*" --region ${deployConfig.region}`;
    
    const result = execSync(command, { encoding: 'utf8' });
    const invalidation = JSON.parse(result);
    
    console.log(`✅ Invalidation created: ${invalidation.Invalidation.Id}`);
    console.log('⏳ Cache invalidation may take 5-15 minutes to complete');
  } catch (error) {
    throw new Error(`Failed to invalidate CloudFront: ${error.message}`);
  }
}

function getAllFiles(dir) {
  const files = [];
  const items = readdirSync(dir);
  
  for (const item of items) {
    const fullPath = join(dir, item);
    if (statSync(fullPath).isDirectory()) {
      files.push(...getAllFiles(fullPath));
    } else {
      files.push(fullPath);
    }
  }
  
  return files;
}

function getContentType(filePath) {
  const ext = extname(filePath).toLowerCase();
  const contentTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.txt': 'text/plain',
    '.xml': 'application/xml',
    '.pdf': 'application/pdf'
  };
  
  return contentTypes[ext] || 'application/octet-stream';
}

function getCacheControl(filePath) {
  // HTML files - no cache (for SPA routing)
  if (filePath.endsWith('.html') || filePath === 'index.html') {
    return 'public, max-age=0, must-revalidate';
  }
  
  // Static assets with hash in filename - long cache
  if (filePath.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/) && 
      filePath.match(/-[a-f0-9]{8,}\./)) {
    return 'public, max-age=31536000, immutable';
  }
  
  // Other static assets - medium cache
  if (filePath.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
    return 'public, max-age=86400';
  }
  
  // JSON and other files - short cache
  return 'public, max-age=3600';
}

// Run the deployment
main();