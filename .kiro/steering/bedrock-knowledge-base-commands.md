# Bedrock Knowledge Base Management Commands

This document contains all the essential commands for managing Amazon Bedrock Knowledge Bases with S3 vectors storage.

## Current Knowledge Base Configuration

### Active Knowledge Base
- **Knowledge Base ID**: `RCWW86CLM9`
- **Name**: `RestaurantKnowledgeBase-20250929-081808`
- **Storage Type**: S3 Vectors
- **Data Bucket**: `mbti-knowledgebase-209803798463-us-east-1`
- **Vector Bucket**: `restaurant-vectors-209803798463-20250929-081808`
- **Vector Index**: `restaurant-index`
- **Data Source ID**: `RQPU9JWBU8`
- **IAM Role**: `arn:aws:iam::209803798463:role/RestaurantKBRole-20250929-081808`

### Current User Role and Permissions
- **User Role**: `arn:aws:sts::209803798463:assumed-role/AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5/nestymook`
- **Account ID**: `209803798463`
- **Region**: `us-east-1`

#### Attached AWS Managed Policies
- `AmazonEC2ContainerRegistryFullAccess`
- `AmazonSSMFullAccess`
- `IAMFullAccess`
- `AmazonSNSFullAccess`
- `AmazonS3FullAccess`
- `CloudWatchFullAccessV2`
- `AmazonBedrockFullAccess` ✅ (Includes S3 vectors permissions)
- `AmazonDynamoDBFullAccess_v2`
- `AWSCloudFormationFullAccess`
- `AWSLambda_FullAccess`

#### Required Permissions for Knowledge Base Operations
The following permissions are **REQUIRED** and currently **GRANTED** through `AmazonBedrockFullAccess`:

**S3 Vectors Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3vectors:CreateVectorBucket",
                "s3vectors:CreateIndex",
                "s3vectors:ListVectorBuckets",
                "s3vectors:ListIndexes",
                "s3vectors:GetVectorBucket",
                "s3vectors:GetIndex",
                "s3vectors:PutVectorBucketPolicy",
                "s3vectors:GetVectorBucketPolicy",
                "s3vectors:PutVectors",
                "s3vectors:GetVectors",
                "s3vectors:ListVectors",
                "s3vectors:QueryVectors"
            ],
            "Resource": "*"
        }
    ]
}
```

**Bedrock Knowledge Base Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateKnowledgeBase",
                "bedrock:GetKnowledgeBase",
                "bedrock:ListKnowledgeBases",
                "bedrock:UpdateKnowledgeBase",
                "bedrock:DeleteKnowledgeBase",
                "bedrock:CreateDataSource",
                "bedrock:GetDataSource",
                "bedrock:ListDataSources",
                "bedrock:UpdateDataSource",
                "bedrock:DeleteDataSource",
                "bedrock:StartIngestionJob",
                "bedrock:GetIngestionJob",
                "bedrock:ListIngestionJobs",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

**Bedrock Agent Runtime Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent-runtime:Retrieve",
                "bedrock-agent-runtime:RetrieveAndGenerate"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Knowledge Base Service Role Permissions
The knowledge base service role `RestaurantKBRole-20250929-081808` has these permissions:

**S3 Access Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
                "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1/*"
            ]
        }
    ]
}
```

**S3 Vectors Access Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3vectors:*"
            ],
            "Resource": "*"
        }
    ]
}
```

**Bedrock Model Access Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
                "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
            ]
        }
    ]
}
```

## Knowledge Base Management Commands

### Get Knowledge Base Details
```bash
aws bedrock-agent get-knowledge-base --knowledge-base-id RCWW86CLM9 --region us-east-1
```

### List All Knowledge Bases
```bash
aws bedrock-agent list-knowledge-bases --region us-east-1
```

### Update Knowledge Base
```bash
aws bedrock-agent update-knowledge-base \
    --knowledge-base-id RCWW86CLM9 \
    --name "Updated Knowledge Base Name" \
    --description "Updated description" \
    --region us-east-1
```

## Data Source Management Commands

### List Data Sources
```bash
aws bedrock-agent list-data-sources --knowledge-base-id RCWW86CLM9 --region us-east-1
```

### Get Data Source Details
```bash
aws bedrock-agent get-data-source \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --region us-east-1
```

### Create New Data Source
```bash
aws bedrock-agent create-data-source \
    --knowledge-base-id RCWW86CLM9 \
    --name "NewDataSource" \
    --data-source-configuration '{
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
            "inclusionPrefixes": ["documents/"]
        }
    }' \
    --region us-east-1
```

### Update Data Source
```bash
aws bedrock-agent update-data-source \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --name "Updated Data Source Name" \
    --data-source-configuration '{
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
            "inclusionPrefixes": ["Tourist_Spots_With_Hours.markdown", "new-documents/"]
        }
    }' \
    --region us-east-1
```

## Ingestion Job Management Commands

### Start Ingestion Job (CRITICAL for syncing)
```bash
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --region us-east-1
```

### List Ingestion Jobs
```bash
aws bedrock-agent list-ingestion-jobs \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --region us-east-1
```

### Get Ingestion Job Status
```bash
aws bedrock-agent get-ingestion-job \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --ingestion-job-id ASTIVUCSHB \
    --region us-east-1
```

### Monitor Ingestion Job Progress
```bash
# Check status every 30 seconds until complete
while true; do
    STATUS=$(aws bedrock-agent get-ingestion-job \
        --knowledge-base-id RCWW86CLM9 \
        --data-source-id RQPU9JWBU8 \
        --ingestion-job-id ASTIVUCSHB \
        --region us-east-1 \
        --query 'ingestionJob.status' \
        --output text)
    echo "Ingestion Status: $STATUS"
    if [ "$STATUS" = "COMPLETE" ] || [ "$STATUS" = "FAILED" ]; then
        break
    fi
    sleep 30
done
```

## S3 Bucket Management Commands

### List Files in Data Bucket
```bash
aws s3 ls s3://mbti-knowledgebase-209803798463-us-east-1/ --region us-east-1
```

### Upload New Document
```bash
aws s3 cp local-document.txt s3://mbti-knowledgebase-209803798463-us-east-1/ --region us-east-1
```

### Upload Multiple Documents
```bash
aws s3 sync ./documents/ s3://mbti-knowledgebase-209803798463-us-east-1/documents/ --region us-east-1
```

### Download Document
```bash
aws s3 cp s3://mbti-knowledgebase-209803798463-us-east-1/Tourist_Spots_With_Hours.markdown ./downloaded-file.markdown --region us-east-1
```

## S3 Vectors Management Commands

### List Vector Buckets
```bash
aws s3vectors list-vector-buckets --region us-east-1
```

### Get Vector Bucket Details
```bash
aws s3vectors get-vector-bucket \
    --vector-bucket-name restaurant-vectors-209803798463-20250929-081808 \
    --region us-east-1
```

### List Vector Indexes
```bash
aws s3vectors list-indexes \
    --vector-bucket-name restaurant-vectors-209803798463-20250929-081808 \
    --region us-east-1
```

### Get Vector Index Details
```bash
aws s3vectors get-index \
    --vector-bucket-name restaurant-vectors-209803798463-20250929-081808 \
    --index-name restaurant-index \
    --region us-east-1
```

## Knowledge Base Query Commands

### Query Knowledge Base (Retrieve)
```bash
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id RCWW86CLM9 \
    --retrieval-query '{"text": "What tourist spots are available in Hong Kong?"}' \
    --retrieval-configuration '{"vectorSearchConfiguration": {"numberOfResults": 5}}' \
    --region us-east-1
```

### Query Knowledge Base (Retrieve and Generate)
```bash
aws bedrock-agent-runtime retrieve-and-generate \
    --retrieval-query '{"text": "What are the best MBTI-matched tourist spots for an ENFP personality?"}' \
    --retrieve-and-generate-configuration '{
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "RCWW86CLM9",
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        }
    }' \
    --region us-east-1
```

## Troubleshooting Commands

### Check Knowledge Base Status
```bash
aws bedrock-agent get-knowledge-base \
    --knowledge-base-id RCWW86CLM9 \
    --region us-east-1 \
    --query 'knowledgeBase.status' \
    --output text
```

### Check Last Ingestion Job Status
```bash
aws bedrock-agent list-ingestion-jobs \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --region us-east-1 \
    --query 'ingestionJobSummaries[0].status' \
    --output text
```

### Verify IAM Role Permissions
```bash
aws iam get-role --role-name RestaurantKBRole-20250929-081808
aws iam list-role-policies --role-name RestaurantKBRole-20250929-081808
```

### Test S3 Access
```bash
aws s3 ls s3://mbti-knowledgebase-209803798463-us-east-1/ --region us-east-1
```

### Test S3 Vectors Access
```bash
aws s3vectors list-vector-buckets --region us-east-1
```

## Common Workflows

### Adding New Documents Workflow
1. Upload documents to S3:
   ```bash
   aws s3 cp new-document.pdf s3://mbti-knowledgebase-209803798463-us-east-1/
   ```

2. Start ingestion job:
   ```bash
   aws bedrock-agent start-ingestion-job \
       --knowledge-base-id RCWW86CLM9 \
       --data-source-id RQPU9JWBU8 \
       --region us-east-1
   ```

3. Monitor progress:
   ```bash
   aws bedrock-agent list-ingestion-jobs \
       --knowledge-base-id RCWW86CLM9 \
       --data-source-id RQPU9JWBU8 \
       --region us-east-1
   ```

### Updating Existing Documents Workflow
1. Replace document in S3:
   ```bash
   aws s3 cp updated-document.pdf s3://mbti-knowledgebase-209803798463-us-east-1/document.pdf
   ```

2. Start new ingestion job (this will update the vectors):
   ```bash
   aws bedrock-agent start-ingestion-job \
       --knowledge-base-id RCWW86CLM9 \
       --data-source-id RQPU9JWBU8 \
       --region us-east-1
   ```

### Complete Sync Workflow
1. Check current status:
   ```bash
   aws bedrock-agent get-knowledge-base --knowledge-base-id RCWW86CLM9 --region us-east-1
   ```

2. List data sources:
   ```bash
   aws bedrock-agent list-data-sources --knowledge-base-id RCWW86CLM9 --region us-east-1
   ```

3. Start ingestion:
   ```bash
   aws bedrock-agent start-ingestion-job \
       --knowledge-base-id RCWW86CLM9 \
       --data-source-id RQPU9JWBU8 \
       --region us-east-1
   ```

4. Monitor until complete:
   ```bash
   aws bedrock-agent get-ingestion-job \
       --knowledge-base-id RCWW86CLM9 \
       --data-source-id RQPU9JWBU8 \
       --ingestion-job-id <JOB_ID> \
       --region us-east-1
   ```

5. Test query:
   ```bash
   aws bedrock-agent-runtime retrieve \
       --knowledge-base-id RCWW86CLM9 \
       --retrieval-query '{"text": "test query"}' \
       --region us-east-1
   ```

## Python Scripts for Automation

### Quick Ingestion Script
```python
import boto3

def start_ingestion():
    client = boto3.client('bedrock-agent', region_name='us-east-1')
    response = client.start_ingestion_job(
        knowledgeBaseId='RCWW86CLM9',
        dataSourceId='RQPU9JWBU8'
    )
    return response['ingestionJob']['ingestionJobId']

job_id = start_ingestion()
print(f"Started ingestion job: {job_id}")
```

### Query Knowledge Base Script
```python
import boto3

def query_kb(query_text):
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    response = client.retrieve(
        knowledgeBaseId='RCWW86CLM9',
        retrievalQuery={'text': query_text},
        retrievalConfiguration={
            'vectorSearchConfiguration': {'numberOfResults': 5}
        }
    )
    return response['retrievalResults']

results = query_kb("What tourist spots are available?")
for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Content: {result['content']['text'][:200]}...")
```

## Permission Verification Commands

### Check Current User Permissions
```bash
# Get current user identity
aws sts get-caller-identity

# List attached policies for your SSO role
aws iam list-attached-role-policies --role-name AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5

# Test S3 vectors access
aws s3vectors list-vector-buckets --region us-east-1

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test knowledge base access
aws bedrock-agent list-knowledge-bases --region us-east-1
```

### Verify Knowledge Base Service Role
```bash
# Get service role details
aws iam get-role --role-name RestaurantKBRole-20250929-081808

# List service role policies
aws iam list-role-policies --role-name RestaurantKBRole-20250929-081808

# Get specific policy document
aws iam get-role-policy --role-name RestaurantKBRole-20250929-081808 --policy-name KnowledgeBasePolicy
```

### Test Permissions
```bash
# Test S3 bucket access
aws s3 ls s3://mbti-knowledgebase-209803798463-us-east-1/ --region us-east-1

# Test vector bucket access
aws s3vectors get-vector-bucket --vector-bucket-name restaurant-vectors-209803798463-20250929-081808 --region us-east-1

# Test knowledge base query
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id RCWW86CLM9 \
    --retrieval-query '{"text": "test"}' \
    --region us-east-1
```

## Permission Troubleshooting

### Common Permission Issues and Solutions

#### Issue: "User is not authorized to perform s3vectors:CreateVectorBucket"
**Solution**: Ensure `AmazonBedrockFullAccess` policy is attached to your role
```bash
aws iam attach-role-policy \
    --role-name AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5 \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

#### Issue: "User is not authorized to perform aoss:ListCollections"
**Solution**: Add OpenSearch Serverless permissions (if using OpenSearch instead of S3 vectors)
```bash
aws iam attach-role-policy \
    --role-name AWSReservedSSO_RestaurantCrawlerFullAccess_37749380ed19e3d5 \
    --policy-arn arn:aws:iam::aws:policy/AmazonOpenSearchServerlessFullAccess
```

#### Issue: "Access Denied" when querying knowledge base
**Solution**: Verify the knowledge base service role has proper permissions
```bash
# Check if service role exists and has correct policies
aws iam get-role --role-name RestaurantKBRole-20250929-081808
aws iam list-role-policies --role-name RestaurantKBRole-20250929-081808
```

#### Issue: "Token has expired and refresh failed"
**Solution**: Refresh AWS SSO credentials
```bash
aws sso login
```

### Minimum Required Policies for Knowledge Base Operations

If you need to create a minimal permission set, these are the essential policies:

1. **AmazonBedrockFullAccess** (includes S3 vectors)
2. **AmazonS3FullAccess** (for data bucket access)
3. **IAMFullAccess** (for creating service roles)

### Custom Policy for Knowledge Base Operations
If you prefer a custom policy instead of managed policies:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "bedrock-agent:*",
                "bedrock-agent-runtime:*",
                "s3vectors:*",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject",
                "s3:CreateBucket",
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
```

## Important Notes

1. **Always start an ingestion job** after uploading new documents to S3
2. **Monitor ingestion job status** before querying the knowledge base
3. **Use the correct region** (us-east-1) for all commands
4. **Check IAM permissions** if commands fail
5. **Ingestion jobs are required** for the knowledge base to sync with S3 changes
6. **Your current role has all required permissions** through `AmazonBedrockFullAccess`
7. **S3 vectors permissions are included** in the Bedrock managed policy

## Emergency Recovery Commands

### Delete and Recreate Knowledge Base
```bash
# Delete knowledge base (use with caution)
aws bedrock-agent delete-knowledge-base --knowledge-base-id RCWW86CLM9 --region us-east-1

# Recreate using the Python script
python create_s3_vectors_kb.py
```

### Force Resync All Documents
```bash
# Start fresh ingestion job
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id RCWW86CLM9 \
    --data-source-id RQPU9JWBU8 \
    --region us-east-1
```

---

**Last Updated**: September 29, 2025  
**Knowledge Base ID**: RCWW86CLM9  
**Data Source ID**: RQPU9JWBU8  
**Region**: us-east-1