# MBTI Travel Frontend - Deployment Guide

This guide covers deployment configurations and processes for the MBTI Travel Web Frontend application.

## Table of Contents

- [Environment Configuration](#environment-configuration)
- [Build Process](#build-process)
- [Deployment Options](#deployment-options)
- [CI/CD Pipeline](#cicd-pipeline)
- [Docker Deployment](#docker-deployment)
- [Performance Optimization](#performance-optimization)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)

## Environment Configuration

### Environment Files

The application supports multiple environment configurations:

- `.env.development` - Local development
- `.env.staging` - Staging environment
- `.env.production` - Production environment
- `.env.example` - Template for environment variables

### Required Environment Variables

```bash
# API Configuration
VITE_API_BASE_URL=https://api.mbti-travel.example.com
VITE_API_TIMEOUT=30000

# Authentication Configuration
VITE_COGNITO_USER_POOL_ID=us-east-1_your_pool_id
VITE_COGNITO_CLIENT_ID=your_client_id
VITE_COGNITO_DOMAIN=auth.mbti-travel.example.com

# CDN Configuration (optional)
VITE_CDN_URL=https://cdn.mbti-travel.example.com

# Base URL for routing
VITE_BASE_URL=/
```

## Build Process

### Local Build

```bash
# Development build
npm run build

# Staging build
npm run build:staging

# Production build
npm run build:production

# Build with bundle analysis
npm run build:production -- --analyze
```

### Build Validation

The build process includes comprehensive validation:

```bash
# Run full validation pipeline
npm run validate

# Individual validation steps
npm run lint:check
npm run format:check
npm run type-check
npm run test:run
```

### Build Artifacts

After building, the following artifacts are generated:

- `dist/` - Built application files
- `dist/build-info.json` - Build metadata
- `dist/stats.html` - Bundle analysis (with --analyze flag)
- `dist/_headers` - Security headers configuration
- `dist/sw.js` - Service worker (production only)

## Deployment Options

### 1. Static Hosting (Recommended)

Deploy to static hosting services like AWS S3 + CloudFront:

```bash
# Deploy to staging
npm run deploy staging

# Deploy to production
npm run deploy production

# Dry run deployment
npm run deploy production --dry-run
```

### 2. Container Deployment

Deploy using Docker containers:

```bash
# Build production container
docker build -t mbti-travel-frontend .

# Run container
docker run -p 8080:8080 mbti-travel-frontend

# Using Docker Compose
docker-compose --profile prod up
```

### 3. CDN Integration

The application supports CDN integration for optimized asset delivery:

- Static assets are automatically versioned with hashes
- CDN URLs are configured via `VITE_CDN_URL` environment variable
- Responsive images with automatic format optimization
- Critical asset preloading

## CI/CD Pipeline

### GitHub Actions Workflow

The application includes a comprehensive CI/CD pipeline (`.github/workflows/ci-cd.yml`):

1. **Validation Stage**
   - Linting and formatting checks
   - Type checking
   - Unit tests with coverage

2. **E2E Testing Stage**
   - Playwright end-to-end tests
   - Cross-browser compatibility testing

3. **Build Stage**
   - Environment-specific builds
   - Bundle optimization and analysis

4. **Deployment Stage**
   - Automated deployment to staging/production
   - CloudFront cache invalidation
   - GitHub release creation

### Required Secrets

Configure the following secrets in your GitHub repository:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# Environment-specific variables
VITE_API_BASE_URL_STAGING
VITE_API_BASE_URL_PRODUCTION
VITE_COGNITO_USER_POOL_ID_STAGING
VITE_COGNITO_USER_POOL_ID_PRODUCTION
VITE_COGNITO_CLIENT_ID_STAGING
VITE_COGNITO_CLIENT_ID_PRODUCTION
VITE_COGNITO_DOMAIN_STAGING
VITE_COGNITO_DOMAIN_PRODUCTION
VITE_CDN_URL_STAGING
VITE_CDN_URL_PRODUCTION

# AWS Resources
S3_BUCKET_STAGING
S3_BUCKET_PRODUCTION
CLOUDFRONT_DISTRIBUTION_ID_STAGING
CLOUDFRONT_DISTRIBUTION_ID_PRODUCTION
```

## Docker Deployment

### Production Container

```dockerfile
# Build and run production container
docker build -t mbti-travel-frontend:latest .
docker run -d -p 8080:8080 --name mbti-travel mbti-travel-frontend:latest
```

### Development Container

```dockerfile
# Run development container with hot reload
docker-compose --profile dev up
```

### Container Features

- Multi-stage build for optimized image size
- Non-root user for security
- Health checks for container orchestration
- Nginx with performance optimizations
- Security headers configuration
- Gzip compression enabled

## Performance Optimization

### Build Optimizations

- **Code Splitting**: Automatic vendor and personality-specific chunk splitting
- **Tree Shaking**: Dead code elimination in production builds
- **Minification**: Terser minification with console removal
- **Asset Optimization**: Image optimization and WebP generation
- **Bundle Analysis**: Detailed bundle size analysis

### Runtime Optimizations

- **Lazy Loading**: Personality-specific components loaded on demand
- **Virtual Scrolling**: Efficient rendering of large lists
- **Debounced Inputs**: Optimized user input handling
- **CDN Integration**: Global asset distribution
- **Service Worker**: Offline caching for critical resources

### Performance Monitoring

```typescript
// Performance monitoring is enabled in development
if (import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true') {
  // Performance metrics collection
}
```

## Security Configuration

### Content Security Policy

```nginx
Content-Security-Policy: default-src 'self'; 
  script-src 'self' 'unsafe-inline'; 
  style-src 'self' 'unsafe-inline'; 
  img-src 'self' data: https:; 
  font-src 'self' data:; 
  connect-src 'self' https://api.mbti-travel.example.com https://auth.mbti-travel.example.com;
```

### Security Headers

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### HTTPS Configuration

- Force HTTPS in production
- HSTS headers for enhanced security
- Secure cookie configuration

## Monitoring and Logging

### Application Monitoring

- Build information available at `/build-info.json`
- Health check endpoint at `/health`
- Performance metrics collection
- Error boundary logging

### Infrastructure Monitoring

- Container health checks
- CloudWatch metrics integration
- CloudFront access logs
- S3 access logging

### Log Levels

Configure logging levels per environment:

- **Development**: `debug` - Detailed logging for development
- **Staging**: `warn` - Warnings and errors only
- **Production**: `error` - Errors only

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Clear cache and rebuild
   npm run clean
   npm ci
   npm run build
   ```

2. **Environment Variable Issues**
   ```bash
   # Validate environment configuration
   node -e "console.log(process.env)" | grep VITE_
   ```

3. **Docker Build Issues**
   ```bash
   # Build with verbose output
   docker build --no-cache --progress=plain -t mbti-travel-frontend .
   ```

4. **Deployment Issues**
   ```bash
   # Test deployment with dry run
   npm run deploy production --dry-run --verbose
   ```

### Performance Issues

1. **Bundle Size Analysis**
   ```bash
   npm run build:production -- --analyze
   # Open dist/stats.html to analyze bundle
   ```

2. **Runtime Performance**
   ```bash
   # Enable performance monitoring
   VITE_ENABLE_PERFORMANCE_MONITORING=true npm run dev
   ```

### Security Issues

1. **CSP Violations**
   - Check browser console for CSP violations
   - Update CSP headers in nginx.conf
   - Validate external resource domains

2. **Authentication Issues**
   - Verify Cognito configuration
   - Check JWT token validation
   - Validate CORS settings

## Best Practices

### Development

- Use environment-specific configurations
- Run validation before commits
- Test builds locally before deployment
- Monitor bundle size regularly

### Deployment

- Always deploy to staging first
- Use automated deployment pipelines
- Monitor deployment health checks
- Keep rollback procedures ready

### Security

- Regularly update dependencies
- Monitor security advisories
- Use HTTPS everywhere
- Implement proper CSP headers

### Performance

- Monitor Core Web Vitals
- Optimize images and assets
- Use CDN for global distribution
- Implement proper caching strategies

## Support

For deployment issues or questions:

1. Check the troubleshooting section above
2. Review build logs and error messages
3. Validate environment configuration
4. Contact the development team with specific error details

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: MBTI Travel Development Team