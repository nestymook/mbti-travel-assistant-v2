#!/usr/bin/env python3
"""
Optimize Knowledge Base for Markdown Data Recognition

This script demonstrates various techniques to improve S3 vectors performance
for markdown files, including chunking strategies and metadata enhancement.
"""

import boto3
import json
from datetime import datetime

def update_data_source_for_markdown():
    """Update data source with optimized configuration for markdown files."""
    
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    data_source_id = "RQPU9JWBU8"
    
    # Optimized configuration for markdown files
    optimized_config = {
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
            "inclusionPrefixes": ["Tourist_Spots_With_Hours.markdown"]
        }
    }
    
    # Advanced chunking configuration for better markdown parsing
    vector_ingestion_config = {
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 300,  # Smaller chunks for better precision
                "overlapPercentage": 20  # 20% overlap for context preservation
            }
        },
        "parsingConfiguration": {
            "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
            "bedrockFoundationModelConfiguration": {
                "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "parsingPrompt": """
You are parsing a markdown file containing Hong Kong tourist spots with MBTI personality mappings.

Please extract and structure the information as follows:
1. Tourist Spot Name
2. MBTI Personality Type
3. Description
4. Address and District
5. Operating Hours
6. Any special remarks

Preserve the relationship between MBTI types and tourist spots for better matching.
Focus on extracting structured data that can be easily searched and matched.
"""
            }
        }
    }
    
    try:
        print("Updating data source with optimized markdown configuration...")
        
        response = bedrock.update_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            name="OptimizedMarkdownDataSource",
            description="Optimized data source for markdown tourist spot data",
            dataSourceConfiguration=optimized_config,
            vectorIngestionConfiguration=vector_ingestion_config
        )
        
        print("✓ Data source updated successfully")
        print(f"Data Source ID: {response['dataSource']['dataSourceId']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating data source: {str(e)}")
        return False

def create_enhanced_markdown_kb():
    """Create a new knowledge base specifically optimized for markdown data."""
    
    s3vectors = boto3.client('s3vectors', region_name='us-east-1')
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    iam = boto3.client('iam', region_name='us-east-1')
    
    account_id = boto3.client('sts').get_caller_identity()['Account']
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # Configuration for markdown-optimized KB
    vector_bucket_name = f"markdown-vectors-{account_id}-{timestamp}"
    index_name = "markdown-optimized-index"
    kb_name = f"MarkdownOptimizedKB-{timestamp}"
    role_name = f"MarkdownKBRole-{timestamp}"
    
    try:
        print("Creating markdown-optimized knowledge base...")
        
        # Create vector bucket with optimized settings
        s3vectors.create_vector_bucket(
            vectorBucketName=vector_bucket_name,
            encryptionConfiguration={'sseType': 'AES256'}
        )
        
        # Create index with optimized dimensions for text similarity
        s3vectors.create_index(
            vectorBucketName=vector_bucket_name,
            indexName=index_name,
            dataType='float32',
            dimension=1024,  # Matches Titan v2 embeddings
            distanceMetric='cosine'  # Best for text similarity
        )
        
        # Create IAM role (reuse existing logic)
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
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [
                        "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
                        "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3vectors:*"],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": [
                        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
                    ]
                }
            ]
        }
        
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for markdown-optimized Bedrock Knowledge Base"
        )
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="MarkdownKBPolicy",
            PolicyDocument=json.dumps(role_policy)
        )
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        
        # Wait for role propagation
        import time
        time.sleep(10)
        
        # Create knowledge base with enhanced configuration
        index_arn = f"arn:aws:s3vectors:us-east-1:{account_id}:bucket/{vector_bucket_name}/index/{index_name}"
        
        kb_response = bedrock.create_knowledge_base(
            name=kb_name,
            description="Markdown-optimized knowledge base for tourist spots",
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
        
        # Create optimized data source
        ds_response = bedrock.create_data_source(
            knowledgeBaseId=kb_id,
            name="MarkdownOptimizedDataSource",
            description="Optimized data source for markdown files",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": "arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1",
                    "inclusionPrefixes": ["Tourist_Spots_With_Hours.markdown"]
                }
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 250,  # Smaller chunks for precision
                        "overlapPercentage": 25  # More overlap for context
                    }
                },
                "parsingConfiguration": {
                    "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
                    "bedrockFoundationModelConfiguration": {
                        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                        "parsingPrompt": """
Extract tourist spot information from this markdown table format:

For each tourist spot, identify:
- Name of the tourist spot
- MBTI personality type it matches
- Description of activities/features
- Full address including district
- Operating hours (weekday, weekend, holiday)
- Any special remarks or notes

Structure the output to preserve the relationship between MBTI types and tourist attractions.
Make each chunk self-contained with complete information about one tourist spot.
"""
                    }
                }
            }
        )
        
        data_source_id = ds_response['dataSource']['dataSourceId']
        
        print(f"✓ Created optimized knowledge base: {kb_id}")
        print(f"✓ Created optimized data source: {data_source_id}")
        
        return {
            'knowledge_base_id': kb_id,
            'data_source_id': data_source_id,
            'vector_bucket': vector_bucket_name,
            'role_arn': role_arn
        }
        
    except Exception as e:
        print(f"❌ Error creating optimized KB: {str(e)}")
        return None

def test_markdown_optimization():
    """Test different query strategies for markdown data."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"  # Use existing KB for now
    
    # Test queries optimized for markdown structure
    test_queries = [
        "ENFP personality tourist spots Hong Kong",
        "What attractions match INTJ personality type?",
        "Tourist spots in Central district for extroverts",
        "Museums and galleries for ISFJ personality",
        "Operating hours for Happy Valley attractions",
        "MBTI personality matching for outdoor activities"
    ]
    
    print("Testing markdown-optimized queries...")
    
    for query in test_queries:
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3,
                        # S3 vectors only supports SEMANTIC search
                    }
                }
            )
            
            print(f"\n🔍 Query: {query}")
            print(f"Results: {len(response['retrievalResults'])}")
            
            for i, result in enumerate(response['retrievalResults'][:2]):
                print(f"  {i+1}. Score: {result['score']:.4f}")
                print(f"     Content: {result['content']['text'][:150]}...")
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {str(e)}")
    
    return True

if __name__ == "__main__":
    print("=== Markdown Optimization for S3 Vectors ===\n")
    
    # Option 1: Update existing data source
    print("1. Updating existing data source...")
    # update_data_source_for_markdown()
    
    # Option 2: Test current setup with optimized queries
    print("\n2. Testing optimized queries...")
    test_markdown_optimization()
    
    # Option 3: Create new optimized KB (uncomment to create)
    # print("\n3. Creating new optimized knowledge base...")
    # result = create_enhanced_markdown_kb()
    # if result:
    #     print(f"New KB ID: {result['knowledge_base_id']}")