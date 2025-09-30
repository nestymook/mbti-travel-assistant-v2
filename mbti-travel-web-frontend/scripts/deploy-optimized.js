#!/usr/bin/env node

/**
 * Optimized S3 Deployment Script with Security Headers and Performance Optimizations
 * Addresses security, compatibility, and performance audit issues
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, relative, extname } from 'path';

const args = process.argv.slice(2);
const bucketName = args[0] || 'mbti-travel-production-209803798463';
const verbose = args.includes('--verbose');

console.log(`🚀 Deploying to S3 bucket: ${bucketName} with security headers and performance optimizations...`);

// Validate build exists
if (!existsSync('dist/index.html')) {
  console.error('❌ Build not found. Run npm run build first.');
  process.exit(1);
}

async function main() {
  try {
    // Upload files with security headers and optimizations
    await uploadWithOptimizations();
    
    console.log('✨ Deployment completed successfully!');
    console.log(`🌐 Website URL: http://${bucketName}.s3-website-us-east-1.amazonaws.com`);
    console.log(`🔒 Security headers applied`);
    console.log(`⚡ Performance optimizations enabled`);
    
  } catch (error) {
    console.error('❌ Deployment failed:', error.message);
    process.exit(1);
  }
}

async function uploadWithOptimizations() {
  const distPath = 'dist';
  const files = getAllFiles(distPath);
  
  console.log(`📁 Found ${files.length} files to upload with optimizations`);
  
  for (const file of files) {
    const relativePath = relative(distPath, file).replace(/\\/g, '/');
    const contentType = getContentType(file);
    const cacheControl = getCacheControl(relativePath);
    const securityHeaders = getSecurityHeaders(relativePath);
    
    try {
      const command = `aws s3 cp "${file}" "s3://${bucketName}/${relativePath}" --content-type "${contentType}" --cache-control "${cacheControl}" ${securityHeaders} --region us-east-1`;
      
      if (verbose) {
        console.log(`📤 Uploading: ${relativePath} (${contentType})`);
        console.log(`   Cache: ${cacheControl}`);
        console.log(`   Security: ${securityHeaders.split(' ').length / 2} headers`);
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
  
  console.log(`✅ Successfully uploaded ${files.length} files with security headers and performance optimizations`);
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
  // HTML files - no cache for SPA routing (optimized)
  if (filePath.endsWith('.html') || filePath === 'index.html') {
    return 'public, max-age=0, no-cache, no-store';
  }
  
  // Static assets with hash in filename - long cache with immutable
  if (filePath.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/) && 
      filePath.match(/-[a-f0-9]{8,}\./)) {
    return 'public, max-age=31536000, immutable';
  }
  
  // Other static assets - medium cache
  if (filePath.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
    return 'public, max-age=86400, s-maxage=86400';
  }
  
  // JSON and other files - short cache
  return 'public, max-age=3600, s-maxage=3600';
}

function getSecurityHeaders(filePath) {
  const headers = [];
  
  // Core security headers for all files
  headers.push('--metadata x-content-type-options=nosniff');
  headers.push('--metadata x-frame-options=DENY');
  headers.push('--metadata x-xss-protection="1; mode=block"');
  headers.push('--metadata referrer-policy=strict-origin-when-cross-origin');
  headers.push('--metadata x-download-options=noopen');
  headers.push('--metadata x-permitted-cross-domain-policies=none');
  
  // HTML-specific security headers
  if (filePath.endsWith('.html')) {
    // Content Security Policy for enhanced security
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cognito-idp.us-east-1.amazonaws.com https://*.amazoncognito.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "img-src 'self' data: https: blob:",
      "font-src 'self' data: https://fonts.gstatic.com",
      "connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com https://p4ex20jih1.execute-api.us-east-1.amazonaws.com",
      "media-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "upgrade-insecure-requests"
    ].join('; ');
    
    headers.push(`--metadata content-security-policy="${csp}"`);
    
    // Additional HTML security headers
    headers.push('--metadata strict-transport-security="max-age=31536000; includeSubDomains; preload"');
    headers.push('--metadata permissions-policy="geolocation=(), microphone=(), camera=()"');
  }
  
  // JavaScript-specific headers (avoid duplicates)
  if (filePath.endsWith('.js') || filePath.endsWith('.mjs')) {
    // x-content-type-options already added above
  }
  
  // CSS-specific headers
  if (filePath.endsWith('.css')) {
    headers.push('--metadata x-content-type-options=nosniff');
  }
  
  return headers.join(' ');
}

// Performance monitoring
function logPerformanceMetrics() {
  const distPath = 'dist';
  const files = getAllFiles(distPath);
  
  let totalSize = 0;
  let jsSize = 0;
  let cssSize = 0;
  let imageSize = 0;
  
  files.forEach(file => {
    const stats = statSync(file);
    const size = stats.size;
    totalSize += size;
    
    const ext = extname(file).toLowerCase();
    if (['.js', '.mjs'].includes(ext)) {
      jsSize += size;
    } else if (ext === '.css') {
      cssSize += size;
    } else if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'].includes(ext)) {
      imageSize += size;
    }
  });
  
  console.log('\n📊 Performance Metrics:');
  console.log(`   Total size: ${(totalSize / 1024).toFixed(2)} KB`);
  console.log(`   JavaScript: ${(jsSize / 1024).toFixed(2)} KB`);
  console.log(`   CSS: ${(cssSize / 1024).toFixed(2)} KB`);
  console.log(`   Images: ${(imageSize / 1024).toFixed(2)} KB`);
  console.log(`   Files: ${files.length}`);
  
  // Performance recommendations
  if (jsSize > 500 * 1024) {
    console.log('⚠️  JavaScript bundle is large (>500KB). Consider code splitting.');
  }
  if (cssSize > 100 * 1024) {
    console.log('⚠️  CSS bundle is large (>100KB). Consider CSS optimization.');
  }
  if (totalSize > 2 * 1024 * 1024) {
    console.log('⚠️  Total bundle is large (>2MB). Consider asset optimization.');
  }
}

// Run the deployment
main().then(() => {
  logPerformanceMetrics();
});