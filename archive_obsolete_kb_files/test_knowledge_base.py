#!/usr/bin/env python3
"""
Test the created S3 vectors knowledge base
"""

import boto3
import json

def test_knowledge_base():
    """Test the knowledge base functionality."""
    
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    try:
        print("Testing knowledge base...")
        
        # Get knowledge base details
        kb_response = bedrock.get_knowledge_base(knowledgeBaseId=kb_id)
        kb = kb_response['knowledgeBase']
        
        print(f"✓ Knowledge Base Name: {kb['name']}")
        print(f"✓ Status: {kb['status']}")
        print(f"✓ Storage Type: {kb['storageConfiguration']['type']}")
        print(f"✓ Embedding Model: {kb['knowledgeBaseConfiguration']['vectorKnowledgeBaseConfiguration']['embeddingModelArn']}")
        
        # List data sources
        ds_response = bedrock.list_data_sources(knowledgeBaseId=kb_id)
        data_sources = ds_response['dataSourceSummaries']
        
        print(f"✓ Data Sources: {len(data_sources)}")
        
        if len(data_sources) == 0:
            print("\n📝 To use this knowledge base:")
            print("1. Create a data source:")
            print(f"   aws bedrock-agent create-data-source --knowledge-base-id {kb_id} --name 'RestaurantData' --data-source-configuration '{{\"type\":\"S3\",\"s3Configuration\":{{\"bucketArn\":\"arn:aws:s3:::mbti-knowledgebase-209803798463-us-east-1\"}}}}'")
            print("2. Upload documents to the S3 bucket")
            print("3. Start an ingestion job")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing knowledge base: {str(e)}")
        return False

if __name__ == "__main__":
    test_knowledge_base()