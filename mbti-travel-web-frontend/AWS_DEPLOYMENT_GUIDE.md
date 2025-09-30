# AWS Deployment Guide

This guide provides step-by-step instructions for deploying the MBTI Travel Web Frontend to AWS using S3, CloudFront, and automated CI/CD pipelines.

## 📋 Prerequisites

### AWS Account Setup
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Node.js 20.19.0 or later
- Git repository with GitHub Actions enabled

### Required AWS Permissions
Your AWS user/role needs the following permissions:
- `CloudFormationFullAccess`
- `S3FullAccess`
- `CloudFrontFullAccess`
- `IAMFullAccess` (for creating service roles)
- `Route53FullAccess` (if using custom domain)

## 🏗️ Infrastructure Overview

The deployment creates the following AWS resources:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   CloudFront    │    │   S3 Bucket     │
│   Actions       │───▶│   Distribution  │───▶│   Static Files  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Route 53      │    │   SSL/TLS       │    │   IAM Roles     │
│   DNS (Optional)│    │   Certificate   │    │   & Policies    │
│                 │    │   (Optional)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start Deployment

### 1. Clone and Setup
```bash
git clone <your-repo>
cd mbti-travel-web-frontend
npm install
```

### 2. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)
```

### 3. Deploy Infrastructure (Staging)
```bash
# Deploy staging infrastructure
npm run deploy:infrastructure:staging

# Build and deploy application
npm run build:staging
npm run deploy:staging
```

### 4. Deploy Infrastructure (Production)
```bash
# Deploy production infrastructure
npm run deploy:infrastructure:production

# Build and deploy application
npm run build:production
npm run deploy:production
```

## 📝 Detailed Setup Instructions

### Step 1: Environment Configuration

Create environment-specific configuration files:

#### Staging Environment (.env.staging)
```env
VITE_API_BASE_URL=https://staging-api.mbti-travel.com
VITE_COGNITO_USER_POOL_ID=us-east-1_staging123
VITE_COGNITO_CLIENT_ID=staging-client-id-123
VITE_COGNITO_DOMAIN=https://staging-auth.auth.us-east-1.amazoncognito.com
```

#### Production Environment (.env.production)
```env
VITE_API_BASE_URL=https://api.mbti-travel.com
VITE_COGNITO_USER_POOL_ID=us-east-1_prod123456
VITE_COGNITO_CLIENT_ID=prod-client-id-123
VITE_COGNITO_DOMAIN=https://auth.mbti-travel.com
```

### Step 2: Infrastructure Deployment

#### Deploy Staging Infrastructure
```bash
# Deploy CloudFormation stack for staging
npm run deploy:infrastructure:staging

# With custom domain (optional)
node scripts/deploy-infrastructure.js staging --domain=staging.mbti-travel.com --cert=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012
```

#### Deploy Production Infrastructure
```bash
# Deploy CloudFormation stack for production
npm run deploy:infrastructure:production

# With custom domain (optional)
node scripts/deploy-infrastructure.js production --domain=mbti-travel.com --cert=arn:aws:acm:us-east-1:123456789012:certificate/87654321-4321-4321-4321-210987654321
```

### Step 3: Application Deployment

#### Build and Deploy Staging
```bash
# Build staging application
npm run build:staging

# Deploy to staging
npm run deploy:staging

# Dry run (test without deploying)
npm run deploy:staging:dry-run
```

#### Build and Deploy Production
```bash
# Build production application
npm run build:production

# Deploy to production
npm run deploy:production

# Dry run (test without deploying)
npm run deploy:production:dry-run
```

## 🔧 GitHub Actions Setup

### Required Secrets

Configure the following secrets in your GitHub repository settings:

#### AWS Credentials
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

#### Environment Variables - Staging
```
VITE_API_BASE_URL_STAGING=https://staging-api.mbti-travel.com
VITE_COGNITO_USER_POOL_ID_STAGING=us-east-1_staging123
VITE_COGNITO_CLIENT_ID_STAGING=staging-client-id-123
VITE_COGNITO_DOMAIN_STAGING=https://staging-auth.auth.us-east-1.amazoncognito.com
VITE_CDN_URL_STAGING=https://staging-cdn.mbti-travel.com
```

#### Environment Variables - Production
```
VITE_API_BASE_URL_PRODUCTION=https://api.mbti-travel.com
VITE_COGNITO_USER_POOL_ID_PRODUCTION=us-east-1_prod123456
VITE_COGNITO_CLIENT_ID_PRODUCTION=prod-client-id-123
VITE_COGNITO_DOMAIN_PRODUCTION=https://auth.mbti-travel.com
VITE_CDN_URL_PRODUCTION=https://cdn.mbti-travel.com
```

### Deployment Workflow

The GitHub Actions workflow automatically:

1. **On Push to `develop` branch:**
   - Runs tests and validation
   - Builds staging application
   - Deploys infrastructure (if needed)
   - Deploys to staging environment
   - Validates deployment

2. **On Push to `main` branch:**
   - Runs tests and validation
   - Builds production application
   - Deploys infrastructure (if needed)
   - Deploys to production environment
   - Runs smoke tests
   - Creates GitHub release

## 🔍 Monitoring and Validation

### Health Check Endpoints

After deployment, the following endpoints are available:

- **Health Check:** `https://your-domain.com/health`
- **Build Info:** `https://your-domain.com/build-info.json`

### Validation Commands

```bash
# Validate staging deployment
npm run validate:deployment staging

# Validate production deployment
npm run validate:deployment production
```

### Manual Testing

```bash
# Test staging
curl -f https://staging.mbti-travel.com/health
curl -f https://staging.mbti-travel.com/

# Test production
curl -f https://mbti-travel.com/health
curl -f https://mbti-travel.com/
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. CloudFormation Stack Creation Failed
```bash
# Check stack events
aws cloudformation describe-stack-events --stack-name mbti-travel-frontend-staging

# Delete failed stack and retry
aws cloudformation delete-stack --stack-name mbti-travel-frontend-staging
npm run deploy:infrastructure:staging
```

#### 2. S3 Deployment Failed
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check S3 bucket exists
aws s3 ls s3://mbti-travel-frontend-staging-123456789012

# Manual sync
aws s3 sync dist/ s3://mbti-travel-frontend-staging-123456789012 --delete
```

#### 3. CloudFront Invalidation Issues
```bash
# Check distribution status
aws cloudfront get-distribution --id E1234567890ABC

# Manual invalidation
aws cloudfront create-invalidation --distribution-id E1234567890ABC --paths "/*"
```

#### 4. Build Failures
```bash
# Clean and rebuild
npm run clean
npm ci
npm run build:staging

# Check environment variables
node -e "console.log(process.env)" | grep VITE_
```

### Debug Commands

```bash
# Verbose deployment
node scripts/deploy.js staging --verbose --dry-run

# Check stack outputs
aws cloudformation describe-stacks --stack-name mbti-travel-frontend-staging --query "Stacks[0].Outputs"

# List S3 bucket contents
aws s3 ls s3://mbti-travel-frontend-staging-123456789012/ --recursive

# Check CloudFront distribution
aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='MBTI Travel Frontend - staging']"
```

## 🔒 Security Considerations

### Content Security Policy
The application includes strict CSP headers:
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.amazonaws.com https://*.amazoncognito.com;
```

### HTTPS Enforcement
- All traffic is redirected to HTTPS
- HSTS headers are enabled
- Secure cookie configuration

### Access Control
- S3 bucket is configured with CloudFront Origin Access Identity
- IAM roles follow least privilege principle
- GitHub Actions uses OIDC for secure AWS access

## 📊 Performance Optimization

### CloudFront Caching
- Static assets: 1 year cache
- HTML files: No cache (for SPA routing)
- API calls: No cache

### Build Optimizations
- Code splitting by personality types
- Tree shaking for unused code
- Asset optimization and compression
- Bundle analysis available

### Monitoring
- Health check endpoints
- Build information tracking
- Performance metrics collection
- Error boundary logging

## 🔄 Rollback Procedures

### Quick Rollback
```bash
# Rollback to previous version (if available)
aws s3 sync s3://mbti-travel-frontend-staging-123456789012-backup/ s3://mbti-travel-frontend-staging-123456789012/ --delete
aws cloudfront create-invalidation --distribution-id E1234567890ABC --paths "/*"
```

### GitHub Release Rollback
1. Go to GitHub Releases
2. Find the previous working release
3. Re-run the deployment workflow for that commit

### Infrastructure Rollback
```bash
# Rollback CloudFormation stack
aws cloudformation cancel-update-stack --stack-name mbti-travel-frontend-staging

# Or update to previous template version
aws cloudformation update-stack --stack-name mbti-travel-frontend-staging --template-body file://previous-template.yml
```

## 📞 Support

### Getting Help
1. Check this deployment guide
2. Review AWS CloudFormation events
3. Check GitHub Actions logs
4. Validate environment configuration
5. Contact the development team

### Useful Resources
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Last Updated:** December 2024  
**Version:** 1.0.0  
**Maintainer:** MBTI Travel Development Team