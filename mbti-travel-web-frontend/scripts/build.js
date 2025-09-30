#!/usr/bin/env node

/**
 * AWS-Optimized Build Script
 * Handles environment-specific builds with AWS CloudFront optimizations
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'fs';
import { join } from 'path';

const args = process.argv.slice(2);
const mode = args.find(arg => arg.startsWith('--mode='))?.split('=')[1] || 'production';
const analyze = args.includes('--analyze');
const verbose = args.includes('--verbose');
const skipValidation = args.includes('--skip-validation');

console.log(`🚀 Building MBTI Travel Frontend for ${mode} environment...`);

// Create build info early
const buildInfo = {
  mode,
  timestamp: new Date().toISOString(),
  version: getPackageVersion(),
  nodeVersion: process.version,
  commit: getGitCommit(),
  branch: getGitBranch(),
  environment: process.env.NODE_ENV || 'production'
};

try {
  // Clean previous build
  console.log('🧹 Cleaning previous build...');
  if (existsSync('dist')) {
    rmSync('dist', { recursive: true });
  }
  mkdirSync('dist', { recursive: true });
  
  // Build info will be written after the build
  
  // Run validation unless skipped
  if (!skipValidation) {
    console.log('✅ Running validation...');
    execSync('npm run validate', { stdio: verbose ? 'inherit' : 'pipe' });
  }
  
  // Build application
  console.log('📦 Building application...');
  const buildCommand = `npx vite build --mode ${mode}${analyze ? ' --analyze' : ''}`;
  execSync(buildCommand, { 
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'production' }
  });
  
  // Generate AWS-specific assets
  console.log('🔧 Generating AWS-optimized assets...');
  
  // Write build info
  writeFileSync('dist/build-info.json', JSON.stringify(buildInfo, null, 2));
  
  generateHealthCheck();
  generateSecurityHeaders();
  generateRobotsTxt(mode);
  generateSitemap(mode);
  
  // Generate service worker for production
  if (mode === 'production') {
    generateServiceWorker();
  }
  
  // Validate build output
  validateBuildOutput();
  
  console.log('✨ Build completed successfully!');
  console.log(`📊 Build info: dist/build-info.json`);
  
  if (analyze) {
    console.log('📈 Bundle analysis: dist/stats.html');
  }
  
  // Display build summary
  displayBuildSummary();
  
} catch (error) {
  console.error('❌ Build failed:', error.message);
  if (verbose) {
    console.error(error.stack);
  }
  process.exit(1);
}

function getPackageVersion() {
  try {
    const packageJson = JSON.parse(readFileSync('package.json', 'utf8'));
    return packageJson.version;
  } catch {
    return '1.0.0';
  }
}

function getGitCommit() {
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
}

function getGitBranch() {
  try {
    return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
}

function generateHealthCheck() {
  const healthCheck = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: buildInfo.version,
    environment: buildInfo.mode,
    commit: buildInfo.commit.slice(0, 8)
  };
  
  writeFileSync('dist/health', JSON.stringify(healthCheck, null, 2));
}

function generateSecurityHeaders() {
  // CloudFront-compatible headers format
  const headers = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com;

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.js
  Cache-Control: public, max-age=31536000, immutable

/*.css
  Cache-Control: public, max-age=31536000, immutable

/index.html
  Cache-Control: public, max-age=0, must-revalidate

/health
  Cache-Control: no-cache, no-store, must-revalidate`;
  
  writeFileSync('dist/_headers', headers);
}

function generateRobotsTxt(mode) {
  const isProduction = mode === 'production';
  
  const robots = isProduction ? 
    `User-agent: *
Allow: /

Sitemap: https://mbti-travel.com/sitemap.xml` :
    `User-agent: *
Disallow: /`;

  writeFileSync('dist/robots.txt', robots);
}

function generateSitemap(mode) {
  const isProduction = mode === 'production';
  const baseUrl = isProduction ? 'https://mbti-travel.com' : 'https://staging.mbti-travel.com';
  const currentDate = new Date().toISOString().split('T')[0];
  
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${baseUrl}/</loc>
    <lastmod>${currentDate}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${baseUrl}/personality-test</loc>
    <lastmod>${currentDate}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>${baseUrl}/itinerary</loc>
    <lastmod>${currentDate}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>`;

  writeFileSync('dist/sitemap.xml', sitemap);
}

function generateServiceWorker() {
  const swContent = `// Service Worker for MBTI Travel Frontend
const CACHE_NAME = 'mbti-travel-v${buildInfo.version}';
const urlsToCache = [
  '/',
  '/health',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  // Skip caching for API calls
  if (event.request.url.includes('/api/')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});`;
  
  writeFileSync('dist/sw.js', swContent);
}

function validateBuildOutput() {
  const requiredFiles = [
    'index.html',
    'build-info.json',
    'health',
    '_headers',
    'robots.txt',
    'sitemap.xml'
  ];
  
  for (const file of requiredFiles) {
    if (!existsSync(join('dist', file))) {
      throw new Error(`Required file missing: ${file}`);
    }
  }
  
  // Validate index.html
  const indexHtml = readFileSync('dist/index.html', 'utf8');
  if (!indexHtml.includes('<div id="app">')) {
    throw new Error('index.html missing app container');
  }
}

function displayBuildSummary() {
  try {
    console.log('\n📋 Build Summary:');
    console.log(`   Version: ${buildInfo.version}`);
    console.log(`   Mode: ${buildInfo.mode}`);
    console.log(`   Commit: ${buildInfo.commit.slice(0, 8)}`);
    console.log(`   Branch: ${buildInfo.branch}`);
    console.log(`   Build Time: ${buildInfo.timestamp}`);
    
    // Get build size
    try {
      const sizeOutput = execSync('du -sh dist/', { encoding: 'utf8' });
      const size = sizeOutput.split('\t')[0];
      console.log(`   Total Size: ${size}`);
    } catch {
      console.log('   Total Size: Unable to calculate');
    }
    
    console.log('\n🎯 Ready for AWS deployment!');
    
  } catch (error) {
    console.warn('⚠️  Could not display build summary:', error.message);
  }
}