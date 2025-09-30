#!/usr/bin/env node

/**
 * Deployment Configuration Validation Script
 * Validates that all deployment configurations are properly set up
 */

import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

console.log('🔍 Validating deployment configuration...');

const errors = [];
const warnings = [];

// Check environment files
const envFiles = ['.env.development', '.env.staging', '.env.production', '.env.example'];
envFiles.forEach(file => {
  if (!existsSync(file)) {
    errors.push(`Missing environment file: ${file}`);
  } else {
    console.log(`✅ Found ${file}`);
  }
});

// Check build configuration files
const configFiles = [
  'vite.config.ts',
  'build.config.ts',
  'src/config/environment.ts',
  'scripts/build.js',
  'scripts/deploy.js'
];

configFiles.forEach(file => {
  if (!existsSync(file)) {
    errors.push(`Missing configuration file: ${file}`);
  } else {
    console.log(`✅ Found ${file}`);
  }
});

// Check Docker files
const dockerFiles = ['Dockerfile', 'Dockerfile.dev', 'docker-compose.yml', 'nginx.conf'];
dockerFiles.forEach(file => {
  if (!existsSync(file)) {
    warnings.push(`Missing Docker file: ${file}`);
  } else {
    console.log(`✅ Found ${file}`);
  }
});

// Check CI/CD configuration
const cicdFiles = ['.github/workflows/ci-cd.yml'];
cicdFiles.forEach(file => {
  if (!existsSync(file)) {
    warnings.push(`Missing CI/CD file: ${file}`);
  } else {
    console.log(`✅ Found ${file}`);
  }
});

// Check package.json scripts
try {
  const packageJson = JSON.parse(readFileSync('package.json', 'utf8'));
  const requiredScripts = [
    'build:staging',
    'build:production',
    'validate',
    'lint:check',
    'format:check',
    'ci:build',
    'ci:test'
  ];
  
  requiredScripts.forEach(script => {
    if (!packageJson.scripts[script]) {
      errors.push(`Missing package.json script: ${script}`);
    } else {
      console.log(`✅ Found script: ${script}`);
    }
  });
} catch (error) {
  errors.push('Could not read package.json');
}

// Check documentation
const docFiles = ['DEPLOYMENT.md'];
docFiles.forEach(file => {
  if (!existsSync(file)) {
    warnings.push(`Missing documentation: ${file}`);
  } else {
    console.log(`✅ Found ${file}`);
  }
});

// Report results
console.log('\n📊 Validation Results:');

if (errors.length > 0) {
  console.log('\n❌ Errors:');
  errors.forEach(error => console.log(`  - ${error}`));
}

if (warnings.length > 0) {
  console.log('\n⚠️  Warnings:');
  warnings.forEach(warning => console.log(`  - ${warning}`));
}

if (errors.length === 0 && warnings.length === 0) {
  console.log('✨ All deployment configuration files are present!');
} else if (errors.length === 0) {
  console.log('✅ Core deployment configuration is complete (with some optional warnings)');
} else {
  console.log('❌ Deployment configuration validation failed');
  process.exit(1);
}

console.log('\n🚀 Deployment configuration validation complete!');