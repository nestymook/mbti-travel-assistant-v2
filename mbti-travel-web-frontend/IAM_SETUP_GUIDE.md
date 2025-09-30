# IAM Setup Guide for MBTI Travel Frontend Deployment

This guide provides comprehensive instructions for setting up the necessary IAM permissions to deploy the MBTI Travel Web Frontend to AWS.

## 🚨 Current Issue

The deployment failed because your current AWS role `AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5` doesn't have CloudFront permissions. You need additional permissions to deploy the frontend infrastructure.

## 📋 Required Permissions

The deployment requires the following AWS service permissions:

### Core Services
- **CloudFormation**: Create and manage infrastructure stacks
- **S3**: Create buckets and manage static website hosting
- **CloudFront**: Create distributions and origin access identities
- **IAM**: Create service roles for the application

### Optional Services (for advanced features)
- **Route 53**: Custom domain DNS management
- **Certificate Manager**: SSL/TLS certificates
- **STS**: Identity and access management

## 🛠️ Setup Options

### Option 1: Quick Setup - Attach Policy to Current Role (Recommended)

This is the fastest way to get deployment working with your current SSO role.

```bash
# Navigate to the frontend directory
cd mbti-travel-web-frontend

# Check current permissions
node scripts/setup-iam.js

# Attach deployment policy to your current role
node scripts/setup-iam.js --role=AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5
```

**Note**: You'll need IAM admin permissions to attach policies to roles. If this fails, use Option 2 or 3.

### Option 2: Create Dedicated IAM User

Create a dedicated IAM user with deployment permissions:

```bash
# Create IAM user with deployment permissions
node scripts/setup-iam.js --create-user --user=mbti-travel-deployer

# The script will output AWS credentials - save them securely!
```

### Option 3: Manual Policy Attachment (AWS Console)

If you prefer using the AWS Console or need an admin to do this:

1. **Open AWS IAM Console**
2. **Go to Policies → Create Policy**
3. **Copy the policy from** `infrastructure/iam-policies.json`
4. **Name it**: `MBTITravelFrontendDeploymentPolicy`
5. **Attach to your role/user**

### Option 4: CloudFormation Stack Deployment

Deploy the complete IAM setup using CloudFormation:

```bash
# Deploy IAM infrastructure
aws cloudformation create-stack \
  --stack-name mbti-travel-frontend-iam \
  --template-body file://infrastructure/iam-setup.yml \
  --parameters ParameterKey=CreateUser,ParameterValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

## 📝 Detailed Permission Breakdown

### CloudFormation Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudformation:CreateStack",
    "cloudformation:UpdateStack",
    "cloudformation:DeleteStack",
    "cloudformation:DescribeStacks",
    "cloudformation:DescribeStackEvents",
    "cloudformation:ValidateTemplate"
  ],
  "Resource": "arn:aws:cloudformation:*:*:stack/mbti-travel-frontend-*/*"
}
```

### S3 Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:CreateBucket",
    "s3:DeleteBucket",
    "s3:GetBucketPolicy",
    "s3:PutBucketPolicy",
    "s3:PutBucketWebsite",
    "s3:PutBucketPublicAccessBlock",
    "s3:ListBucket",
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject"
  ],
  "Resource": [
    "arn:aws:s3:::mbti-travel-frontend-*",
    "arn:aws:s3:::mbti-travel-frontend-*/*"
  ]
}
```

### CloudFront Permissions (Missing from your current role)
```json
{
  "Effect": "Allow",
  "Action": [
    "cloudfront:CreateDistribution",
    "cloudfront:GetDistribution",
    "cloudfront:UpdateDistribution",
    "cloudfront:DeleteDistribution",
    "cloudfront:CreateInvalidation",
    "cloudfront:CreateCloudFrontOriginAccessIdentity",
    "cloudfront:GetCloudFrontOriginAccessIdentity",
    "cloudfront:DeleteCloudFrontOriginAccessIdentity"
  ],
  "Resource": "*"
}
```

### IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "iam:CreateRole",
    "iam:GetRole",
    "iam:DeleteRole",
    "iam:PutRolePolicy",
    "iam:PassRole"
  ],
  "Resource": "arn:aws:iam::*:role/GitHubActions-MBTITravel-*"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Access Denied" for CloudFront Operations
**Error**: `User is not authorized to perform: cloudfront:CreateCloudFrontOriginAccessIdentity`

**Solution**: Your role needs CloudFront permissions. Use Option 1 above.

#### 2. "Cannot Attach Policy to Role"
**Error**: `User is not authorized to perform: iam:AttachRolePolicy`

**Solution**: You need IAM admin permissions. Ask your AWS administrator or use Option 2.

#### 3. "Stack Already Exists"
**Error**: `Stack mbti-travel-frontend-staging already exists`

**Solution**: Delete the failed stack first:
```bash
aws cloudformation delete-stack --stack-name mbti-travel-frontend-staging
aws cloudformation wait stack-delete-complete --stack-name mbti-travel-frontend-staging
```

#### 4. "Invalid Parameter Value"
**Error**: Parameter validation errors in CloudFormation

**Solution**: Check the CloudFormation template syntax:
```bash
aws cloudformation validate-template --template-body file://infrastructure/cloudformation.yml
```

### Debug Commands

```bash
# Check current AWS identity
aws sts get-caller-identity

# List attached policies for your role
aws iam list-attached-role-policies --role-name AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5

# Test CloudFront access
aws cloudfront list-distributions --max-items 1

# Check CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_FAILED ROLLBACK_COMPLETE

# Get stack failure details
aws cloudformation describe-stack-events --stack-name mbti-travel-frontend-staging --query "StackEvents[?ResourceStatus=='CREATE_FAILED']"
```

## 🚀 Quick Recovery Steps

To get your deployment working immediately:

### Step 1: Clean Up Failed Stack
```bash
cd mbti-travel-web-frontend
aws cloudformation delete-stack --stack-name mbti-travel-frontend-staging --region us-east-1
```

### Step 2: Set Up Permissions
```bash
# Check what permissions you have
node scripts/setup-iam.js

# If you have IAM permissions, attach the policy
node scripts/setup-iam.js --role=AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5

# OR create a new user if you don't have IAM permissions
node scripts/setup-iam.js --create-user
```

### Step 3: Deploy Infrastructure
```bash
# Deploy infrastructure with new permissions
npm run deploy:infrastructure:staging
```

### Step 4: Build and Deploy Application
```bash
# Build the application
npm run build:staging

# Deploy to AWS
npm run deploy:staging
```

## 🔐 Security Best Practices

### Principle of Least Privilege
The provided IAM policy follows the principle of least privilege:
- Permissions are scoped to specific resources where possible
- Only necessary actions are granted
- Resources are limited to the MBTI Travel project

### Credential Management
- **Never commit AWS credentials to version control**
- Use environment variables or AWS credential files
- Rotate credentials regularly
- Use IAM roles instead of users when possible

### GitHub Actions Security
For CI/CD, use OIDC instead of long-lived credentials:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActions-MBTITravel-Deployment
    aws-region: us-east-1
```

## 📞 Getting Help

### If You're Stuck
1. **Check the error message** in CloudFormation events
2. **Verify permissions** using the debug commands above
3. **Contact your AWS administrator** if you need IAM permissions
4. **Use the manual setup** if automated scripts fail

### Common Support Scenarios

#### Scenario 1: You're a Developer
- Use Option 2 (Create IAM User) for development
- Get AWS credentials from your admin
- Use the provided policy document

#### Scenario 2: You're an AWS Administrator
- Review the IAM policy in `infrastructure/iam-policies.json`
- Attach the policy to the appropriate role/user
- Consider using the CloudFormation template for consistency

#### Scenario 3: You're in a Corporate Environment
- Work with your security team to review permissions
- Use the principle of least privilege
- Consider using AWS Organizations SCPs for additional security

## 📋 Checklist

Before proceeding with deployment, ensure:

- [ ] AWS CLI is configured and working
- [ ] You have the necessary IAM permissions
- [ ] CloudFormation can create stacks in your account
- [ ] S3 bucket creation is allowed
- [ ] CloudFront operations are permitted
- [ ] You understand the security implications

## 🎯 Next Steps

Once IAM permissions are set up:

1. **Clean up any failed stacks**
2. **Deploy infrastructure**: `npm run deploy:infrastructure:staging`
3. **Build application**: `npm run build:staging`
4. **Deploy application**: `npm run deploy:staging`
5. **Validate deployment**: `npm run validate:deployment staging`

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Account**: 209803798463  
**Region**: us-east-1