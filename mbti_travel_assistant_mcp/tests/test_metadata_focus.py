#!/usr/bin/env python3
"""
Simple test for metadata-focused prompt engineering
"""

import boto3
import time

def test_metadata_prompt():
    """Test a single metadata-focused prompt."""
    
    print("🎯 Testing Metadata-Focused Prompt Engineering")
    print("=" * 50)
    
    # Initialize Bedrock client
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    # Metadata-focused prompt
    query = """SEARCH INSTRUCTION: Find all documents in the knowledge base where the MBTI attribute equals "INFJ".

Do not interpret or analyze INFJ personality traits. Instead, locate files that have been specifically tagged or labeled with MBTI=INFJ.

Look for documents with:
- MBTI field = INFJ
- MBTI attribute = INFJ  
- MBTI tag = INFJ
- MBTI classification = INFJ

Return all attractions from files that have this exact MBTI attribute match."""
    
    print("🔍 Testing metadata-focused query...")
    print(f"Query: {query[:100]}...")
    
    try:
        start_time = time.time()
        
        response = bedrock_runtime.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': 'RCWW86CLM9',
                    'modelArn': 'amazon.nova-pro-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 30
                        }
                    }
                }
            }
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        generated_text = response['output']['text']
        citations = response.get('citations', [])
        
        print(f"✅ Response received in {response_time:.2f} seconds")
        print(f"📊 Response length: {len(generated_text)} characters")
        print(f"📚 Citations: {len(citations)} sources")
        
        # Count INFJ files in citations
        infj_files = 0
        for citation in citations:
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        if filename.startswith('INFJ_'):
                            infj_files += 1
        
        print(f"🎯 INFJ files cited: {infj_files}")
        
        # Check for metadata vs trait language
        metadata_words = ['metadata', 'attribute', 'field', 'tag', 'classification', 'MBTI=INFJ']
        trait_words = ['introverted', 'intuitive', 'feeling', 'judging', 'personality', 'contemplation']
        
        metadata_count = sum(1 for word in metadata_words if word.lower() in generated_text.lower())
        trait_count = sum(1 for word in trait_words if word.lower() in generated_text.lower())
        
        print(f"📋 Metadata keywords: {metadata_count}")
        print(f"🧠 Trait keywords: {trait_count}")
        
        print(f"\n🤖 Response preview:")
        print("-" * 40)
        print(generated_text[:500] + "..." if len(generated_text) > 500 else generated_text)
        print("-" * 40)
        
        return {
            'response_time': response_time,
            'citations': len(citations),
            'infj_files': infj_files,
            'metadata_keywords': metadata_count,
            'trait_keywords': trait_count,
            'text': generated_text
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    result = test_metadata_prompt()
    
    if 'error' not in result:
        print(f"\n🎉 Test Summary:")
        print(f"   Response time: {result['response_time']:.2f}s")
        print(f"   Citations: {result['citations']}")
        print(f"   INFJ files: {result['infj_files']}")
        print(f"   Metadata focus: {result['metadata_keywords']} keywords")
        print(f"   Trait analysis: {result['trait_keywords']} keywords")
        
        if result['metadata_keywords'] > result['trait_keywords']:
            print("✅ SUCCESS: Model focused more on metadata than traits")
        else:
            print("⚠️ Model still using trait-based analysis")
    else:
        print(f"❌ Test failed: {result['error']}")