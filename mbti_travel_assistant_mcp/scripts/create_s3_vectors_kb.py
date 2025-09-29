#!/usr/bin/env python3
"""
Create Bedrock Knowledge Base with S3 Vectors Storage

This script creates a knowledge base using S3 vectors instead of OpenSearch Serverless.
"""

import boto3
import json
import time
from datetime import datetime

def create_s3_vectors_knowledge_base():
    """Create a knowledge base with S3 vectors storage."""
    
    # Initialize clients
    s3vectors = boto3.client('s3vectors', region_name='us-east-1')
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    iam = boto3.client('iam', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # Configuration
    vector_bucket_name = f"restaurant-vectors-{account_id}-{timestamp}"
    index_name = "restaurant-index"
    kb_name = f"RestaurantKnowledgeBase-{timestamp}"
    data_bucket_name = f"mbti-knowledgebase-209803798463-us-east-1"
    role_name = f"RestaurantKBRole-{timestamp}"
    
    try:
        print("Step 1: Created S3 data bucket...")
        # s3.create_bucket(Bucket=data_bucket_name)
        print(f"✓ Created S3 bucket: {data_bucket_name}")
        
        print("Step 2: Creating S3 vector bucket...")
        s3vectors.create_vector_bucket(
            vectorBucketName=vector_bucket_name,
            encryptionConfiguration={'sseType': 'AES256'}
        )
        print(f"✓ Created S3 vector bucket: {vector_bucket_name}")
        
        print("Step 3: Creating vector index...")
        s3vectors.create_index(
            vectorBucketName=vector_bucket_name,
            indexName=index_name,
            dataType='float32',
            dimension=1024,
            distanceMetric='cosine'
        )
        print(f"✓ Created vector index: {index_name}")
        
        print("Step 4: Creating IAM role...")
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{data_bucket_name}",
                        f"arn:aws:s3:::{data_bucket_name}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3vectors:*"
                    ],
                    "Resource": "*"
                },
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
        
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for Bedrock Knowledge Base with S3 vectors"
        )
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="KnowledgeBasePolicy",
            PolicyDocument=json.dumps(role_policy)
        )
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"✓ Created IAM role: {role_arn}")
        
        # Wait for role to propagate
        print("Waiting for IAM role to propagate...")
        time.sleep(10)
        
        print("Step 5: Creating knowledge base...")
        index_arn = f"arn:aws:s3vectors:us-east-1:{account_id}:bucket/{vector_bucket_name}/index/{index_name}"
        
        kb_response = bedrock.create_knowledge_base(
            name=kb_name,
            description="Restaurant knowledge base using S3 vectors",
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0',
                    'embeddingModelConfiguration': {
                        'bedrockEmbeddingModelConfiguration': {
                            'dimensions': 1024
                        }
                    }
                }
            },
            storageConfiguration={
                'type': 'S3_VECTORS',
                's3VectorsConfiguration': {
                    'indexArn': index_arn
                }
            }
        )
        
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        print(f"✓ Created knowledge base: {kb_id}")
        
        print("\n🎉 Success! Knowledge base created with S3 vectors storage.")
        print(f"Knowledge Base ID: {kb_id}")
        print(f"Data Bucket: {data_bucket_name}")
        print(f"Vector Bucket: {vector_bucket_name}")
        print(f"Vector Index: {index_name}")
        
        return {
            'knowledge_base_id': kb_id,
            'data_bucket': data_bucket_name,
            'vector_bucket': vector_bucket_name,
            'index_name': index_name,
            'role_arn': role_arn
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = create_s3_vectors_knowledge_base()
    if result:
        print("\nNext steps:")
        print(f"1. Upload your documents to: s3://{result['data_bucket']}/")
        print("2. Create a data source in the knowledge base")
        print("3. Start an ingestion job to process the documents")