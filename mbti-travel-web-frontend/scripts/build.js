#!/usr/bin/env node

/**
 * Advanced Build Script
 * Handles environment-specific builds with optimizations
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';

const args = process.argv.slice(2);
const mode = args.find(arg => arg.startsWith('--mode='))?.split('=')[1] || 'production';
const analyze = args.includes('--analyze');
const verbose = args.includes('--verbose');

console.log(`🚀 Building MBTI Travel Frontend for ${mode} environment...`);

// Validate environment
if (!existsSync(`.env.${mode}`)) {
  console.error(`❌ Environment file .env.${mode} not found`);
  process.exit(1);
}

// Create build info
const buildInfo = {
  mode,
  timestamp: new Date().toISOString(),
  version: process.env.npm_package_version || '1.0.0',
  nodeVersion: process.version,
  commit: getGitCommit(),
};

// Ensure dist directory exists
if (!existsSync('dist')) {
  mkdirSync('dist', { recursive: true });
}

// Write build info
writeFileSync('dist/build-info.json', JSON.stringify(buildInfo, null, 2));

try {
  // Clean previous build
  console.log('🧹 Cleaning previous build...');
  execSync('npm run clean', { stdio: verbose ? 'inherit' : 'pipe' });
  
  // Run validation
  console.log('✅ Running validation...');
  execSync('npm run validate', { stdio: verbose ? 'inherit' : 'pipe' });
  
  // Build application
  console.log('📦 Building application...');
  const buildCommand = `cross-env NODE_ENV=production vite build --mode ${mode}${analyze ? ' --analyze' : ''}`;
  execSync(buildCommand, { stdio: 'inherit' });
  
  // Generate additional assets
  if (mode === 'production') {
    console.log('🔧 Generating production assets...');
    generateServiceWorker();
    generateSecurityHeaders();
  }
  
  console.log('✨ Build completed successfully!');
  console.log(`📊 Build info written to dist/build-info.json`);
  
  if (analyze) {
    console.log('📈 Bundle analysis available at dist/stats.html');
  }
  
} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}

function getGitCommit() {
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch {
    return 'unknown';
  }
}

function generateServiceWorker() {
  const swContent = `
// Service Worker for MBTI Travel Frontend
const CACHE_NAME = 'mbti-travel-v${buildInfo.version}';
const urlsToCache = [
  '/',
  '/assets/styles/main.css',
  '/assets/fonts/inter-regular.woff2',
  '/assets/fonts/inter-medium.woff2',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
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
`;
  
  writeFileSync('dist/sw.js', swContent.trim());
}

function generateSecurityHeaders() {
  const headers = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.mbti-travel.example.com https://auth.mbti-travel.example.com;",
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  };
  
  writeFileSync('dist/_headers', Object.entries(headers)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n')
  );
}