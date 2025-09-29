#!/usr/bin/env python3
"""
Test querying the knowledge base after successful sync
"""

import boto3
import json

def test_knowledge_base_query():
    """Test querying the knowledge base."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    try:
        print("Testing knowledge base query...")
        
        # Test query
        query = "What tourist spots are available in Hong Kong?"
        
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        print(f"✓ Query: {query}")
        print(f"✓ Results found: {len(response['retrievalResults'])}")
        
        for i, result in enumerate(response['retrievalResults'][:3]):
            print(f"\n--- Result {i+1} ---")
            print(f"Score: {result['score']:.4f}")
            print(f"Content: {result['content']['text'][:200]}...")
            if 'location' in result:
                print(f"Source: {result['location']['s3Location']['uri']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error querying knowledge base: {str(e)}")
        return False

if __name__ == "__main__":
    test_knowledge_base_query()