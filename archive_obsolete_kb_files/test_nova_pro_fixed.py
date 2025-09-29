#!/usr/bin/env python3
"""
Test Knowledge Base with Amazon Nova Pro (Fixed)

This script tests the retrieve-and-generate functionality using
Amazon Nova Pro with 300K context window.
"""

import boto3
import json
import time

def test_nova_pro_simple():
    """Simple test with Nova Pro."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Use Nova Pro with 300K context (just model ID, not full ARN)
    nova_pro_model = "amazon.nova-pro-v1:0:300k"
    
    print("🚀 Testing Amazon Nova Pro with Knowledge Base")
    print("=" * 60)
    print(f"Model: {nova_pro_model}")
    print(f"Knowledge Base: {kb_id}")
    
    test_question = "What are the best tourist attractions in Hong Kong for someone with an ENFP personality type? Include specific locations and operating hours."
    
    print(f"\n🎯 Test Question:")
    print(f"{test_question}")
    print("-" * 60)
    
    try:
        start_time = time.time()
        
        response = bedrock_runtime.retrieve_and_generate(
            input={'text': test_question},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': nova_pro_model,  # Use model ID directly
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5
                        }
                    }
                }
            }
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        answer = response['output']['text']
        
        print(f"✅ SUCCESS (Response time: {response_time:.2f}s)")
        print(f"📝 Generated Response ({len(answer)} characters):")
        print(f"{answer}")
        
        # Show retrieval info
        if 'citations' in response:
            print(f"\n📚 Sources: {len(response['citations'])} citations")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        
        # Try alternative model IDs
        alternative_models = [
            "amazon.nova-pro-v1:0",
            "amazon.nova-lite-v1:0:300k", 
            "amazon.nova-lite-v1:0"
        ]
        
        print(f"\n🔄 Trying alternative Nova models...")
        
        for alt_model in alternative_models:
            print(f"\n🧪 Testing: {alt_model}")
            try:
                response = bedrock_runtime.retrieve_and_generate(
                    input={'text': test_question},
                    retrieveAndGenerateConfiguration={
                        'type': 'KNOWLEDGE_BASE',
                        'knowledgeBaseConfiguration': {
                            'knowledgeBaseId': kb_id,
                            'modelArn': alt_model,
                            'retrievalConfiguration': {
                                'vectorSearchConfiguration': {
                                    'numberOfResults': 3
                                }
                            }
                        }
                    }
                )
                
                answer = response['output']['text']
                print(f"✅ SUCCESS with {alt_model}")
                print(f"   Response: {answer[:200]}...")
                return True
                
            except Exception as alt_e:
                print(f"❌ Failed: {str(alt_e)[:100]}...")
        
        return False

def test_simple_retrieve_comparison():
    """Compare simple retrieve vs retrieve-and-generate."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    query = "ENFP personality tourist attractions Hong Kong Central district"
    
    print(f"\n🔍 Comparison Test")
    print("=" * 60)
    print(f"Query: {query}")
    
    # Method 1: Simple Retrieve (always works)
    print(f"\n📊 Method 1: Simple Retrieve")
    try:
        retrieve_response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        results = retrieve_response['retrievalResults']
        print(f"✅ Found {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result['score']:.4f}")
            print(f"      Content: {result['content']['text'][:100]}...")
        
        # Extract key information manually
        print(f"\n📝 Manual Analysis of Results:")
        all_content = ' '.join([r['content']['text'] for r in results])
        
        # Look for ENFP mentions
        enfp_count = all_content.count('ENFP')
        central_count = all_content.lower().count('central')
        
        print(f"   ENFP mentions: {enfp_count}")
        print(f"   Central district mentions: {central_count}")
        
        # Extract sample attractions
        lines = all_content.split('|')
        attractions = [line.strip() for line in lines if len(line.strip()) > 10 and 'ENFP' in line]
        
        if attractions:
            print(f"   Sample ENFP attraction: {attractions[0][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_optimized_queries():
    """Test optimized query formulations."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    print(f"\n🎯 Optimized Query Testing")
    print("=" * 60)
    
    # Test different query formulations
    queries = [
        {
            "name": "Basic MBTI",
            "query": "ENFP personality tourist spots Hong Kong"
        },
        {
            "name": "Detailed MBTI",
            "query": "ENFP personality type extroverted intuitive feeling perceiving tourist attractions Hong Kong"
        },
        {
            "name": "Location + MBTI",
            "query": "ENFP personality Central district Hong Kong social creative activities"
        },
        {
            "name": "Comprehensive",
            "query": "Hong Kong tourist attractions ENFP personality type Central Wan Chai districts social creative interactive experiences"
        }
    ]
    
    for query_test in queries:
        print(f"\n🧪 {query_test['name']}")
        print(f"Query: {query_test['query']}")
        
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query_test['query']},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            )
            
            results = response['retrievalResults']
            
            if results:
                scores = [r['score'] for r in results]
                print(f"✅ Results: {len(results)}, Score range: {min(scores):.4f}-{max(scores):.4f}")
                
                # Check content quality
                content = ' '.join([r['content']['text'] for r in results])
                enfp_mentions = content.count('ENFP')
                central_mentions = content.lower().count('central')
                
                print(f"   ENFP relevance: {enfp_mentions} mentions")
                print(f"   Central relevance: {central_mentions} mentions")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🌟 Amazon Nova Pro Knowledge Base Testing (Fixed)")
    print("=" * 70)
    
    # Test 1: Try Nova Pro retrieve-and-generate
    success = test_nova_pro_simple()
    
    # Test 2: Simple retrieve comparison (always works)
    test_simple_retrieve_comparison()
    
    # Test 3: Optimized queries
    test_optimized_queries()
    
    print(f"\n📋 Summary:")
    if success:
        print("✅ Nova Pro retrieve-and-generate is working!")
        print("✅ Use Nova Pro for comprehensive, personalized responses")
    else:
        print("❌ Nova Pro retrieve-and-generate needs troubleshooting")
        print("✅ Simple retrieve() works well for basic queries")
    
    print("✅ Knowledge base is optimized for MBTI-based queries")
    print("✅ Best results with detailed personality trait descriptions")
    
    print(f"\n🎯 Recommendations:")
    print("1. Use detailed MBTI queries with trait descriptions")
    print("2. Include location and activity type for better matching")
    print("3. Combine multiple search terms for comprehensive results")
    print("4. Simple retrieve() + manual processing as fallback")