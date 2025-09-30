#!/usr/bin/env node

/**
 * S3 Deployment Script with Proper MIME Types
 * Fixes the MIME type issue that prevents JavaScript modules from loading
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, relative, extname } from 'path';

const args = process.argv.slice(2);
const bucketName = args[0] || 'mbti-travel-production-209803798463';
const verbose = args.includes('--verbose');

console.log(`🚀 Deploying to S3 bucket: ${bucketName} with proper MIME types...`);

// Validate build exists
if (!existsSync('dist/index.html')) {
  console.error('❌ Build not found. Run npm run build first.');
  process.exit(1);
}

async function main() {
  try {
    // Upload files with correct MIME types
    await uploadWithMimeTypes();
    
    console.log('✨ Deployment completed successfully!');
    console.log(`🌐 Website URL: http://${bucketName}.s3-website-us-east-1.amazonaws.com`);
    
  } catch (error) {
    console.error('❌ Deployment failed:', error.message);
    process.exit(1);
  }
}

async function uploadWithMimeTypes() {
  const distPath = 'dist';
  const files = getAllFiles(distPath);
  
  console.log(`📁 Found ${files.length} files to upload with proper MIME types`);
  
  for (const file of files) {
    const relativePath = relative(distPath, file).replace(/\\/g, '/');
    const contentType = getContentType(file);
    const cacheControl = getCacheControl(relativePath);
    
    try {
      const securityHeaders = getSecurityHeaders(relativePath);
      const command = `aws s3 cp "${file}" "s3://${bucketName}/${relativePath}" --content-type "${contentType}" --cache-control "${cacheControl}" ${securityHeaders} --region us-east-1`;
      
      if (verbose) {
        console.log(`📤 Uploading: ${relativePath} (${contentType})`);
      } else {
        process.stdout.write('.');
      }
      
      execSync(command, { stdio: verbose ? 'inherit' : 'pipe' });
      
    } catch (error) {
      throw new Error(`Failed to upload ${relativePath}: ${error.message}`);
    }
  }
  
  if (!verbose) {
    console.log(''); // New line after dots
  }
  
  console.log(`✅ Successfully uploaded ${files.length} files with correct MIME types`);
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
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.mjs': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
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
    '.txt': 'text/plain; charset=utf-8',
    '.xml': 'application/xml; charset=utf-8',
    '.pdf': 'application/pdf',
    '.map': 'application/json; charset=utf-8'
  };
  
  return contentTypes[ext] || 'application/octet-stream';
}

function getCacheControl(filePath) {
  // HTML files - no cache (for SPA routing) - remove must-revalidate for performance
  if (filePath.endsWith('.html') || filePath === 'index.html') {
    return 'public, max-age=0, no-cache';
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

function getSecurityHeaders(filePath) {
  const headers = [];
  
  // Add security headers for all files
  headers.push('--metadata x-content-type-options=nosniff');
  headers.push('--metadata x-frame-options=DENY');
  headers.push('--metadata x-xss-protection="1; mode=block"');
  headers.push('--metadata referrer-policy=strict-origin-when-cross-origin');
  
  // Add CSP header for HTML files
  if (filePath.endsWith('.html')) {
    const csp = "default-src self; script-src self unsafe-inline unsafe-eval https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com; style-src self unsafe-inline; img-src self data: https:; font-src self data:; connect-src self https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com; frame-ancestors none;";
    headers.push(`--metadata content-security-policy="${csp}"`);
  }
  
  return headers.join(' ');
}

// Run the deployment
main();