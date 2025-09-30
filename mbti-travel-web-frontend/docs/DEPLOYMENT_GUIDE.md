# Deployment Guide

This document provides comprehensive instructions for deploying the MBTI Travel Web Frontend to various environments, including development, staging, and production.

## 📋 Table of Contents

- [Overview](#overview)
- [Environment Configuration](#environment-configuration)
- [Build Process](#build-process)
- [Deployment Options](#deployment-options)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Overview

The MBTI Travel Web Frontend is a Vue 3 + TypeScript single-page application (SPA) that can be deployed as static files to various hosting platforms. The deployment process includes:

- **Environment Configuration**: Setting up environment-specific variables
- **Build Optimization**: Creating optimized production bundles
- **Static Hosting**: Deploying to CDN or static hosting services
- **SSL/TLS**: Ensuring secure HTTPS connections
- **Monitoring**: Setting up performance and error monitoring

### Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Developer     │    │   CI/CD         │    │   Production    │
│   Environment   │    │   Pipeline      │    │   Environment   │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │ Local     │  │───▶│  │ GitHub    │  │───▶│  │ AWS S3 +  │  │
│  │ Dev       │  │    │  │ Actions   │  │    │  │ CloudFront│  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │ Testing   │  │    │  │ Build &   │  │    │  │ Custom    │  │
│  │ Suite     │  │    │  │ Deploy    │  │    │  │ Domain    │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Environment Configuration

### Environment Files

Create environment-specific configuration files:

#### Development (.env.development)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8080
VITE_API_TIMEOUT=100000

# Authentication (Development Cognito Pool)
VITE_COGNITO_USER_POOL_ID=us-east-1_dev123456
VITE_COGNITO_CLIENT_ID=dev-client-id-123
VITE_COGNITO_DOMAIN=https://dev-auth.auth.us-east-1.amazoncognito.com

# External Services
VITE_MBTI_TEST_URL=https://www.16personalities.com/free-personality-test

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG_MODE=true
VITE_ENABLE_MOCK_API=true

# Development Settings
VITE_LOG_LEVEL=debug
VITE_ENABLE_DEVTOOLS=true
```

#### Staging (.env.staging)
```env
# API Configuration
VITE_API_BASE_URL=https://staging-api.mbti-travel.com
VITE_API_TIMEOUT=60000

# Authentication (Staging Cognito Pool)
VITE_COGNITO_USER_POOL_ID=us-east-1_staging123
VITE_COGNITO_CLIENT_ID=staging-client-id-123
VITE_COGNITO_DOMAIN=https://staging-auth.auth.us-east-1.amazoncognito.com

# External Services
VITE_MBTI_TEST_URL=https://www.16personalities.com/free-personality-test

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_MOCK_API=false

# Staging Settings
VITE_LOG_LEVEL=info
VITE_ENABLE_DEVTOOLS=false
```

#### Production (.env.production)
```env
# API Configuration
VITE_API_BASE_URL=https://api.mbti-travel.com
VITE_API_TIMEOUT=60000

# Authentication (Production Cognito Pool)
VITE_COGNITO_USER_POOL_ID=us-east-1_prod123456
VITE_COGNITO_CLIENT_ID=prod-client-id-123
VITE_COGNITO_DOMAIN=https://auth.mbti-travel.com

# External Services
VITE_MBTI_TEST_URL=https://www.16personalities.com/free-personality-test

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_MOCK_API=false

# Production Settings
VITE_LOG_LEVEL=error
VITE_ENABLE_DEVTOOLS=false

# Performance
VITE_ENABLE_PWA=true
VITE_ENABLE_SERVICE_WORKER=true
```

### Environment Configuration Service

```typescript
// src/config/environment.ts
interface EnvironmentConfig {
  apiBaseUrl: string
  apiTimeout: number
  cognito: {
    userPoolId: string
    clientId: string
    domain: string
  }
  mbtiTestUrl: string
  features: {
    analytics: boolean
    debugMode: boolean
    mockApi: boolean
    pwa: boolean
    serviceWorker: boolean
  }
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error'
    enableDevtools: boolean
  }
}

export const environment: EnvironmentConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 60000,
  cognito: {
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
    clientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
    domain: import.meta.env.VITE_COGNITO_DOMAIN
  },
  mbtiTestUrl: import.meta.env.VITE_MBTI_TEST_URL,
  features: {
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    debugMode: import.meta.env.VITE_ENABLE_DEBUG_MODE === 'true',
    mockApi: import.meta.env.VITE_ENABLE_MOCK_API === 'true',
    pwa: import.meta.env.VITE_ENABLE_PWA === 'true',
    serviceWorker: import.meta.env.VITE_ENABLE_SERVICE_WORKER === 'true'
  },
  logging: {
    level: (import.meta.env.VITE_LOG_LEVEL as any) || 'info',
    enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true'
  }
}

// Validate required environment variables
const requiredEnvVars = [
  'VITE_API_BASE_URL',
  'VITE_COGNITO_USER_POOL_ID',
  'VITE_COGNITO_CLIENT_ID',
  'VITE_COGNITO_DOMAIN'
]

const missingEnvVars = requiredEnvVars.filter(
  varName => !import.meta.env[varName]
)

if (missingEnvVars.length > 0) {
  throw new Error(
    `Missing required environment variables: ${missingEnvVars.join(', ')}`
  )
}
```

## Build Process

### Build Scripts

Update `package.json` with comprehensive build scripts:

```json
{
  "scripts": {
    "dev": "vite --mode development",
    "dev:staging": "vite --mode staging",
    "build": "npm run type-check && vite build --mode production",
    "build:staging": "npm run type-check && vite build --mode staging",
    "build:development": "npm run type-check && vite build --mode development",
    "preview": "vite preview",
    "preview:staging": "vite preview --mode staging",
    "type-check": "vue-tsc --noEmit",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "test": "vitest run",
    "test:coverage": "vitest run --coverage",
    "deploy:staging": "npm run build:staging && node scripts/deploy.js staging",
    "deploy:production": "npm run build && node scripts/deploy.js production"
  }
}
```

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      vue(),
      // PWA plugin for production
      ...(env.VITE_ENABLE_PWA === 'true' ? [
        VitePWA({
          registerType: 'autoUpdate',
          workbox: {
            globPatterns: ['**/*.{js,css,html,ico,png,svg}']
          },
          manifest: {
            name: 'MBTI Travel Planner',
            short_name: 'MBTI Travel',
            description: 'Personalized Hong Kong travel itineraries based on MBTI personality types',
            theme_color: '#3498db',
            background_color: '#ffffff',
            display: 'standalone',
            icons: [
              {
                src: 'pwa-192x192.png',
                sizes: '192x192',
                type: 'image/png'
              },
              {
                src: 'pwa-512x512.png',
                sizes: '512x512',
                type: 'image/png'
              }
            ]
          }
        })
      ] : [])
    ],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    build: {
      target: 'esnext',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: mode !== 'production',
      minify: mode === 'production' ? 'terser' : false,
      terserOptions: mode === 'production' ? {
        compress: {
          drop_console: true,
          drop_debugger: true
        }
      } : undefined,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router', 'pinia'],
            ui: ['@headlessui/vue', '@heroicons/vue'],
            utils: ['axios', 'lodash-es']
          }
        }
      },
      chunkSizeWarningLimit: 1000
    },
    server: {
      port: 5173,
      host: true,
      proxy: mode === 'development' ? {
        '/api': {
          target: env.VITE_API_BASE_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      } : undefined
    },
    preview: {
      port: 4173,
      host: true
    },
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString())
    }
  }
})
```

### Build Optimization Script

```javascript
// scripts/build.js
const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const mode = process.argv[2] || 'production'

console.log(`🏗️  Building for ${mode} environment...`)

try {
  // Clean previous build
  if (fs.existsSync('dist')) {
    fs.rmSync('dist', { recursive: true })
    console.log('✅ Cleaned previous build')
  }

  // Type checking
  console.log('🔍 Running type check...')
  execSync('vue-tsc --noEmit', { stdio: 'inherit' })
  console.log('✅ Type check passed')

  // Linting
  console.log('🔍 Running linter...')
  execSync('eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts', { stdio: 'inherit' })
  console.log('✅ Linting passed')

  // Testing
  console.log('🧪 Running tests...')
  execSync('vitest run', { stdio: 'inherit' })
  console.log('✅ Tests passed')

  // Build
  console.log('📦 Building application...')
  execSync(`vite build --mode ${mode}`, { stdio: 'inherit' })
  console.log('✅ Build completed')

  // Generate build info
  const buildInfo = {
    version: process.env.npm_package_version,
    mode,
    buildTime: new Date().toISOString(),
    nodeVersion: process.version,
    gitCommit: execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim()
  }

  fs.writeFileSync(
    path.join('dist', 'build-info.json'),
    JSON.stringify(buildInfo, null, 2)
  )
  console.log('✅ Build info generated')

  console.log(`🎉 Build completed successfully for ${mode}!`)
} catch (error) {
  console.error('❌ Build failed:', error.message)
  process.exit(1)
}
```

## Deployment Options

### 1. AWS S3 + CloudFront (Recommended)

#### Setup Script

```javascript
// scripts/deploy.js
const AWS = require('aws-sdk')
const fs = require('fs')
const path = require('path')
const mime = require('mime-types')

const environment = process.argv[2] || 'staging'

const config = {
  staging: {
    bucketName: 'mbti-travel-staging',
    distributionId: 'E1234567890ABC',
    region: 'us-east-1'
  },
  production: {
    bucketName: 'mbti-travel-production',
    distributionId: 'E0987654321XYZ',
    region: 'us-east-1'
  }
}

const deployConfig = config[environment]
if (!deployConfig) {
  console.error(`❌ Unknown environment: ${environment}`)
  process.exit(1)
}

// Configure AWS
AWS.config.update({ region: deployConfig.region })
const s3 = new AWS.S3()
const cloudfront = new AWS.CloudFront()

async function uploadToS3() {
  console.log(`📤 Uploading to S3 bucket: ${deployConfig.bucketName}`)
  
  const distPath = path.join(__dirname, '..', 'dist')
  const files = getAllFiles(distPath)
  
  for (const file of files) {
    const relativePath = path.relative(distPath, file)
    const key = relativePath.replace(/\\/g, '/')
    
    const fileContent = fs.readFileSync(file)
    const contentType = mime.lookup(file) || 'application/octet-stream'
    
    const params = {
      Bucket: deployConfig.bucketName,
      Key: key,
      Body: fileContent,
      ContentType: contentType,
      CacheControl: getCacheControl(key),
      ACL: 'public-read'
    }
    
    await s3.upload(params).promise()
    console.log(`✅ Uploaded: ${key}`)
  }
}

async function invalidateCloudFront() {
  console.log(`🔄 Invalidating CloudFront distribution: ${deployConfig.distributionId}`)
  
  const params = {
    DistributionId: deployConfig.distributionId,
    InvalidationBatch: {
      CallerReference: Date.now().toString(),
      Paths: {
        Quantity: 1,
        Items: ['/*']
      }
    }
  }
  
  const result = await cloudfront.createInvalidation(params).promise()
  console.log(`✅ Invalidation created: ${result.Invalidation.Id}`)
}

function getAllFiles(dir) {
  const files = []
  const items = fs.readdirSync(dir)
  
  for (const item of items) {
    const fullPath = path.join(dir, item)
    if (fs.statSync(fullPath).isDirectory()) {
      files.push(...getAllFiles(fullPath))
    } else {
      files.push(fullPath)
    }
  }
  
  return files
}

function getCacheControl(key) {
  if (key.match(/\.(js|css)$/)) {
    return 'public, max-age=31536000' // 1 year
  } else if (key.match(/\.(png|jpg|jpeg|gif|svg|ico)$/)) {
    return 'public, max-age=2592000' // 30 days
  } else if (key === 'index.html') {
    return 'public, max-age=0, must-revalidate' // No cache
  } else {
    return 'public, max-age=86400' // 1 day
  }
}

async function deploy() {
  try {
    console.log(`🚀 Deploying to ${environment} environment...`)
    
    await uploadToS3()
    await invalidateCloudFront()
    
    console.log(`🎉 Deployment to ${environment} completed successfully!`)
    console.log(`🌐 URL: https://${deployConfig.bucketName}.s3-website-${deployConfig.region}.amazonaws.com`)
  } catch (error) {
    console.error('❌ Deployment failed:', error)
    process.exit(1)
  }
}

deploy()
```

#### CloudFormation Template

```yaml
# infrastructure/cloudformation.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'MBTI Travel Web Frontend Infrastructure'

Parameters:
  Environment:
    Type: String
    AllowedValues: [staging, production]
    Default: staging
  DomainName:
    Type: String
    Description: 'Custom domain name (optional)'
    Default: ''

Conditions:
  HasCustomDomain: !Not [!Equals [!Ref DomainName, '']]
  IsProduction: !Equals [!Ref Environment, 'production']

Resources:
  # S3 Bucket for static hosting
  WebsiteBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'mbti-travel-${Environment}'
      WebsiteConfiguration:
        IndexDocument: index.html
        ErrorDocument: index.html
      PublicAccessBlockConfiguration:
        BlockPublicAcls: false
        BlockPublicPolicy: false
        IgnorePublicAcls: false
        RestrictPublicBuckets: false
      CorsConfiguration:
        CorsRules:
          - AllowedHeaders: ['*']
            AllowedMethods: [GET, HEAD]
            AllowedOrigins: ['*']
            MaxAge: 3600

  # S3 Bucket Policy
  WebsiteBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref WebsiteBucket
      PolicyDocument:
        Statement:
          - Sid: PublicReadGetObject
            Effect: Allow
            Principal: '*'
            Action: s3:GetObject
            Resource: !Sub '${WebsiteBucket}/*'

  # CloudFront Distribution
  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Aliases: !If
          - HasCustomDomain
          - [!Ref DomainName]
          - !Ref AWS::NoValue
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods: [GET, HEAD, OPTIONS]
          CachedMethods: [GET, HEAD]
          Compress: true
          ForwardedValues:
            QueryString: false
            Cookies:
              Forward: none
        DefaultRootObject: index.html
        Enabled: true
        HttpVersion: http2
        Origins:
          - Id: S3Origin
            DomainName: !GetAtt WebsiteBucket.RegionalDomainName
            S3OriginConfig:
              OriginAccessIdentity: ''
        PriceClass: !If [IsProduction, 'PriceClass_All', 'PriceClass_100']
        ViewerCertificate: !If
          - HasCustomDomain
          - AcmCertificateArn: !Ref SSLCertificate
            SslSupportMethod: sni-only
            MinimumProtocolVersion: TLSv1.2_2021
          - CloudFrontDefaultCertificate: true
        CustomErrorResponses:
          - ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /index.html
          - ErrorCode: 403
            ResponseCode: 200
            ResponsePagePath: /index.html

  # SSL Certificate (if custom domain)
  SSLCertificate:
    Type: AWS::CertificateManager::Certificate
    Condition: HasCustomDomain
    Properties:
      DomainName: !Ref DomainName
      ValidationMethod: DNS
      DomainValidationOptions:
        - DomainName: !Ref DomainName
          HostedZoneId: !Ref HostedZone

  # Route 53 Hosted Zone (if custom domain)
  HostedZone:
    Type: AWS::Route53::HostedZone
    Condition: HasCustomDomain
    Properties:
      Name: !Ref DomainName

  # Route 53 Record (if custom domain)
  DNSRecord:
    Type: AWS::Route53::RecordSet
    Condition: HasCustomDomain
    Properties:
      HostedZoneId: !Ref HostedZone
      Name: !Ref DomainName
      Type: A
      AliasTarget:
        DNSName: !GetAtt CloudFrontDistribution.DomainName
        HostedZoneId: Z2FDTNDATAQYW2 # CloudFront hosted zone ID

Outputs:
  WebsiteURL:
    Description: 'Website URL'
    Value: !If
      - HasCustomDomain
      - !Sub 'https://${DomainName}'
      - !Sub 'https://${CloudFrontDistribution.DomainName}'
  
  S3BucketName:
    Description: 'S3 Bucket Name'
    Value: !Ref WebsiteBucket
    
  CloudFrontDistributionId:
    Description: 'CloudFront Distribution ID'
    Value: !Ref CloudFrontDistribution
```

### 2. Netlify Deployment

```toml
# netlify.toml
[build]
  publish = "dist"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[context.staging]
  command = "npm run build:staging"

[context.production]
  command = "npm run build"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.css"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/index.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
```

### 3. Vercel Deployment

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/index.html",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=0, must-revalidate"
        }
      ]
    }
  ]
}
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  NODE_VERSION: '18'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run type check
        run: npm run type-check

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info

  build-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build for staging
        run: npm run build:staging
        env:
          VITE_API_BASE_URL: ${{ secrets.STAGING_API_BASE_URL }}
          VITE_COGNITO_USER_POOL_ID: ${{ secrets.STAGING_COGNITO_USER_POOL_ID }}
          VITE_COGNITO_CLIENT_ID: ${{ secrets.STAGING_COGNITO_CLIENT_ID }}
          VITE_COGNITO_DOMAIN: ${{ secrets.STAGING_COGNITO_DOMAIN }}

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: staging-build
          path: dist/

  deploy-staging:
    needs: build-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download build artifacts
        uses: actions/download-artifact@v3
        with:
          name: staging-build
          path: dist/

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://${{ secrets.STAGING_S3_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.STAGING_CLOUDFRONT_ID }} --paths "/*"

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()

  build-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build for production
        run: npm run build
        env:
          VITE_API_BASE_URL: ${{ secrets.PRODUCTION_API_BASE_URL }}
          VITE_COGNITO_USER_POOL_ID: ${{ secrets.PRODUCTION_COGNITO_USER_POOL_ID }}
          VITE_COGNITO_CLIENT_ID: ${{ secrets.PRODUCTION_COGNITO_CLIENT_ID }}
          VITE_COGNITO_DOMAIN: ${{ secrets.PRODUCTION_COGNITO_DOMAIN }}

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: production-build
          path: dist/

  deploy-production:
    needs: build-production
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download build artifacts
        uses: actions/download-artifact@v3
        with:
          name: production-build
          path: dist/

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://${{ secrets.PRODUCTION_S3_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.PRODUCTION_CLOUDFRONT_ID }} --paths "/*"

      - name: Run smoke tests
        run: |
          curl -f https://mbti-travel.com/health || exit 1

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

### Deployment Validation Script

```javascript
// scripts/validate-deployment.js
const axios = require('axios')

const environment = process.argv[2] || 'staging'

const config = {
  staging: {
    url: 'https://staging.mbti-travel.com',
    expectedTitle: 'MBTI Travel Planner - Staging'
  },
  production: {
    url: 'https://mbti-travel.com',
    expectedTitle: 'MBTI Travel Planner'
  }
}

const deployConfig = config[environment]

async function validateDeployment() {
  console.log(`🔍 Validating ${environment} deployment...`)
  
  try {
    // Test main page
    const response = await axios.get(deployConfig.url, {
      timeout: 10000,
      headers: {
        'User-Agent': 'Deployment-Validator/1.0'
      }
    })
    
    if (response.status !== 200) {
      throw new Error(`Expected status 200, got ${response.status}`)
    }
    
    if (!response.data.includes(deployConfig.expectedTitle)) {
      throw new Error(`Expected title "${deployConfig.expectedTitle}" not found`)
    }
    
    console.log('✅ Main page validation passed')
    
    // Test API connectivity
    const apiResponse = await axios.get(`${deployConfig.url}/health`, {
      timeout: 5000
    })
    
    if (apiResponse.status !== 200) {
      console.warn('⚠️  API health check failed, but deployment is valid')
    } else {
      console.log('✅ API connectivity validation passed')
    }
    
    // Test static assets
    const assetsToTest = [
      '/assets/index.css',
      '/assets/index.js',
      '/favicon.ico'
    ]
    
    for (const asset of assetsToTest) {
      try {
        const assetResponse = await axios.head(`${deployConfig.url}${asset}`, {
          timeout: 5000
        })
        if (assetResponse.status === 200) {
          console.log(`✅ Asset ${asset} is accessible`)
        }
      } catch (error) {
        console.warn(`⚠️  Asset ${asset} may not be accessible:`, error.message)
      }
    }
    
    console.log(`🎉 ${environment} deployment validation completed successfully!`)
    
  } catch (error) {
    console.error(`❌ ${environment} deployment validation failed:`, error.message)
    process.exit(1)
  }
}

validateDeployment()
```

## Monitoring and Maintenance

### Performance Monitoring

```typescript
// src/utils/monitoring.ts
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  
  static getInstance(): PerformanceMonitor {
    if (!this.instance) {
      this.instance = new PerformanceMonitor()
    }
    return this.instance
  }
  
  /**
   * Track page load performance
   */
  trackPageLoad(pageName: string): void {
    if (typeof window === 'undefined') return
    
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    
    const metrics = {
      page: pageName,
      loadTime: navigation.loadEventEnd - navigation.loadEventStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      firstPaint: this.getFirstPaint(),
      firstContentfulPaint: this.getFirstContentfulPaint(),
      timestamp: new Date().toISOString()
    }
    
    this.sendMetrics('page_load', metrics)
  }
  
  /**
   * Track API call performance
   */
  trackApiCall(endpoint: string, duration: number, success: boolean): void {
    const metrics = {
      endpoint,
      duration,
      success,
      timestamp: new Date().toISOString()
    }
    
    this.sendMetrics('api_call', metrics)
  }
  
  /**
   * Track user interactions
   */
  trackUserInteraction(action: string, component: string): void {
    const metrics = {
      action,
      component,
      timestamp: new Date().toISOString()
    }
    
    this.sendMetrics('user_interaction', metrics)
  }
  
  private getFirstPaint(): number {
    const paintEntries = performance.getEntriesByType('paint')
    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint')
    return firstPaint ? firstPaint.startTime : 0
  }
  
  private getFirstContentfulPaint(): number {
    const paintEntries = performance.getEntriesByType('paint')
    const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint')
    return fcp ? fcp.startTime : 0
  }
  
  private sendMetrics(type: string, data: any): void {
    if (environment.features.analytics) {
      // Send to analytics service (e.g., Google Analytics, AWS CloudWatch)
      console.log(`[METRICS] ${type}:`, data)
    }
  }
}
```

### Error Tracking

```typescript
// src/utils/errorTracking.ts
export class ErrorTracker {
  private static instance: ErrorTracker
  
  static getInstance(): ErrorTracker {
    if (!this.instance) {
      this.instance = new ErrorTracker()
    }
    return this.instance
  }
  
  /**
   * Initialize error tracking
   */
  initialize(): void {
    if (typeof window === 'undefined') return
    
    // Global error handler
    window.addEventListener('error', (event) => {
      this.trackError({
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        type: 'javascript_error'
      })
    })
    
    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.trackError({
        message: event.reason?.message || 'Unhandled promise rejection',
        stack: event.reason?.stack,
        type: 'promise_rejection'
      })
    })
  }
  
  /**
   * Track custom errors
   */
  trackError(error: {
    message: string
    stack?: string
    type: string
    context?: any
  }): void {
    const errorData = {
      ...error,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      environment: import.meta.env.MODE
    }
    
    console.error('[ERROR TRACKER]', errorData)
    
    if (environment.features.analytics) {
      // Send to error tracking service (e.g., Sentry, Rollbar)
      this.sendToErrorService(errorData)
    }
  }
  
  private sendToErrorService(errorData: any): void {
    // Implementation depends on your error tracking service
    fetch('/api/errors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(errorData)
    }).catch(err => {
      console.error('Failed to send error to tracking service:', err)
    })
  }
}
```

### Health Check Endpoint

```typescript
// src/utils/healthCheck.ts
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  buildTime: string
  environment: string
  checks: {
    api: boolean
    auth: boolean
    storage: boolean
  }
}

export async function performHealthCheck(): Promise<HealthStatus> {
  const checks = {
    api: await checkApiHealth(),
    auth: await checkAuthHealth(),
    storage: await checkStorageHealth()
  }
  
  const allHealthy = Object.values(checks).every(check => check)
  const someHealthy = Object.values(checks).some(check => check)
  
  let status: HealthStatus['status']
  if (allHealthy) {
    status = 'healthy'
  } else if (someHealthy) {
    status = 'degraded'
  } else {
    status = 'unhealthy'
  }
  
  return {
    status,
    version: __APP_VERSION__,
    buildTime: __BUILD_TIME__,
    environment: import.meta.env.MODE,
    checks
  }
}

async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${environment.apiBaseUrl}/health`, {
      method: 'GET',
      timeout: 5000
    })
    return response.ok
  } catch {
    return false
  }
}

async function checkAuthHealth(): Promise<boolean> {
  try {
    // Check if Cognito is accessible
    const response = await fetch(`${environment.cognito.domain}/.well-known/openid_configuration`, {
      method: 'GET',
      timeout: 5000
    })
    return response.ok
  } catch {
    return false
  }
}

async function checkStorageHealth(): Promise<boolean> {
  try {
    // Check if localStorage is available
    localStorage.setItem('health-check', 'test')
    localStorage.removeItem('health-check')
    return true
  } catch {
    return false
  }
}
```

## Troubleshooting

### Common Deployment Issues

#### 1. Build Failures

**Problem**: TypeScript compilation errors
**Solution**:
```bash
# Check TypeScript configuration
npx tsc --noEmit --skipLibCheck

# Update dependencies
npm update

# Clear cache
rm -rf node_modules package-lock.json
npm install
```

#### 2. Environment Variable Issues

**Problem**: Missing or incorrect environment variables
**Solution**:
```bash
# Validate environment variables
node -e "
const env = require('dotenv').config();
const required = ['VITE_API_BASE_URL', 'VITE_COGNITO_USER_POOL_ID'];
const missing = required.filter(key => !process.env[key]);
if (missing.length) {
  console.error('Missing env vars:', missing);
  process.exit(1);
}
console.log('All required env vars present');
"
```

#### 3. CORS Issues

**Problem**: Cross-origin requests blocked
**Solution**: Ensure API backend includes proper CORS headers:
```javascript
// Expected CORS configuration
const corsConfig = {
  origin: ['https://mbti-travel.com', 'https://staging.mbti-travel.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}
```

#### 4. CloudFront Caching Issues

**Problem**: Old content served after deployment
**Solution**:
```bash
# Create CloudFront invalidation
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id E1234567890ABC \
  --id I1234567890ABC
```

#### 5. SSL Certificate Issues

**Problem**: SSL certificate validation failures
**Solution**:
```bash
# Check certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012

# Validate DNS records
dig CNAME _validation.example.com
```

### Rollback Procedures

#### Quick Rollback Script

```bash
#!/bin/bash
# scripts/rollback.sh

ENVIRONMENT=$1
PREVIOUS_VERSION=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$PREVIOUS_VERSION" ]; then
  echo "Usage: ./rollback.sh <environment> <previous_version>"
  exit 1
fi

echo "🔄 Rolling back $ENVIRONMENT to version $PREVIOUS_VERSION..."

# Download previous build from S3
aws s3 sync s3://mbti-travel-builds/$PREVIOUS_VERSION/ ./rollback-build/

# Deploy previous build
aws s3 sync ./rollback-build/ s3://mbti-travel-$ENVIRONMENT/ --delete

# Invalidate CloudFront
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name mbti-travel-$ENVIRONMENT \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "✅ Rollback completed successfully!"
```

---

This comprehensive deployment guide provides all the necessary information and scripts for successfully deploying the MBTI Travel Web Frontend to various environments with proper monitoring, error handling, and maintenance procedures.