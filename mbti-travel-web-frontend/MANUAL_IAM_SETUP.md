# Manual IAM Setup for MBTI Travel Frontend

Since your current role is an AWS SSO role that cannot be modified, you need to create a dedicated IAM user for deployment.

## 🚀 Quick Manual Setup

### Step 1: Create IAM User via AWS Console

1. **Go to AWS IAM Console**: https://console.aws.amazon.com/iam/
2. **Click "Users" → "Create user"**
3. **User name**: `mbti-travel-deployer`
4. **Select**: "Provide user access to the AWS Management Console" (optional)
5. **Click "Next"**

### Step 2: Create and Attach Policy

1. **In the permissions step, click "Attach policies directly"**
2. **Click "Create policy"**
3. **Click "JSON" tab**
4. **Copy and paste the following policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationAccess",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudformation:GetTemplate",
        "cloudformation:ListStacks",
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:ListChangeSets"
      ],
      "Resource": [
        "arn:aws:cloudformation:*:209803798463:stack/mbti-travel-frontend-*/*",
        "arn:aws:cloudformation:*:209803798463:changeSet/mbti-travel-frontend-*/*"
      ]
    },
    {
      "Sid": "S3BucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:GetBucketWebsite",
        "s3:PutBucketWebsite",
        "s3:DeleteBucketWebsite",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:GetBucketCORS",
        "s3:PutBucketCORS",
        "s3:DeleteBucketCORS",
        "s3:GetBucketLifecycleConfiguration",
        "s3:PutBucketLifecycleConfiguration",
        "s3:DeleteBucketLifecycleConfiguration",
        "s3:GetBucketPublicAccessBlock",
        "s3:PutBucketPublicAccessBlock",
        "s3:DeleteBucketPublicAccessBlock",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mbti-travel-frontend-*"
      ]
    },
    {
      "Sid": "S3ObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion",
        "s3:DeleteObjectVersion",
        "s3:PutObjectAcl",
        "s3:GetObjectAcl"
      ],
      "Resource": [
        "arn:aws:s3:::mbti-travel-frontend-*/*"
      ]
    },
    {
      "Sid": "CloudFrontAccess",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:GetDistributionConfig",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:ListDistributions",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations",
        "cloudfront:CreateCloudFrontOriginAccessIdentity",
        "cloudfront:GetCloudFrontOriginAccessIdentity",
        "cloudfront:GetCloudFrontOriginAccessIdentityConfig",
        "cloudfront:UpdateCloudFrontOriginAccessIdentity",
        "cloudfront:DeleteCloudFrontOriginAccessIdentity",
        "cloudfront:ListCloudFrontOriginAccessIdentities",
        "cloudfront:TagResource",
        "cloudfront:UntagResource",
        "cloudfront:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMRoleAccess",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:DeleteRole",
        "iam:PutRolePolicy",
        "iam:GetRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags"
      ],
      "Resource": [
        "arn:aws:iam::209803798463:role/GitHubActions-MBTITravel-*",
        "arn:aws:iam::209803798463:role/mbti-travel-*"
      ]
    },
    {
      "Sid": "STSAccess",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "sts:AssumeRole"
      ],
      "Resource": "*"
    }
  ]
}
```

5. **Click "Next"**
6. **Policy name**: `MBTITravelFrontendDeploymentPolicy`
7. **Description**: `Policy for deploying MBTI Travel Frontend to AWS`
8. **Click "Create policy"**

### Step 3: Attach Policy to User

1. **Go back to the user creation page**
2. **Search for**: `MBTITravelFrontendDeploymentPolicy`
3. **Select the policy**
4. **Click "Next"**
5. **Review and click "Create user"**

### Step 4: Create Access Keys

1. **Click on the created user**
2. **Go to "Security credentials" tab**
3. **Click "Create access key"**
4. **Select "Command Line Interface (CLI)"**
5. **Check the confirmation box**
6. **Click "Next"**
7. **Add description**: `MBTI Travel Frontend Deployment`
8. **Click "Create access key"**
9. **⚠️ IMPORTANT: Copy and save the Access Key ID and Secret Access Key**

## 🔧 Configure AWS CLI with New Credentials

### Option 1: Create Named Profile
```bash
aws configure --profile mbti-travel-deployer
# Enter the Access Key ID and Secret Access Key when prompted
# Region: us-east-1
# Output format: json
```

### Option 2: Set Environment Variables
```bash
# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
$env:AWS_DEFAULT_REGION="us-east-1"

# Linux/Mac
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

## ✅ Test the Setup

```bash
# Test with named profile
aws sts get-caller-identity --profile mbti-travel-deployer

# Test CloudFront access
aws cloudfront list-distributions --max-items 1 --profile mbti-travel-deployer

# Test S3 access
aws s3 ls --profile mbti-travel-deployer
```

## 🚀 Deploy with New Credentials

### Using Named Profile
```bash
# Set the profile for all commands
export AWS_PROFILE=mbti-travel-deployer

# Or use --profile flag
aws cloudformation create-stack --profile mbti-travel-deployer ...
```

### Deploy Infrastructure
```bash
cd mbti-travel-web-frontend

# Deploy staging infrastructure
npm run deploy:infrastructure:staging

# Build and deploy application
npm run build:staging
npm run deploy:staging
```

## 🔒 Security Notes

1. **Store credentials securely** - Never commit them to version control
2. **Use environment variables** or AWS credential files
3. **Rotate credentials regularly**
4. **Delete unused access keys**
5. **Monitor usage** in AWS CloudTrail

## 🎯 Alternative: Use AWS CloudShell

If you prefer not to create local credentials, you can use AWS CloudShell:

1. **Open AWS CloudShell** in the AWS Console
2. **Clone your repository**
3. **Run the deployment commands** directly in CloudShell

AWS CloudShell automatically uses your console session credentials.

---

**Next Steps**: Once you have the credentials set up, proceed with the deployment:
1. Deploy infrastructure: `npm run deploy:infrastructure:staging`
2. Build application: `npm run build:staging`  
3. Deploy application: `npm run deploy:staging`