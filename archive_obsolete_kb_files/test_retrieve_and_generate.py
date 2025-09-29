#!/usr/bin/env python3
"""
Test Retrieve and Generate with Available Models

This script tests the retrieve-and-generate functionality using models
you have access to.
"""

import boto3
import json

def test_available_models():
    """Test which models are available for retrieve-and-generate."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Models to test (Nova Pro with 300K context)
    models_to_test = [
        "amazon.nova-pro-v1:0:300k",
        "amazon.nova-pro-v1:0",
        "amazon.nova-lite-v1:0:300k",
        "amazon.nova-premier-v1:0:300k"
    ]
    
    test_question = "What tourist attractions in Hong Kong are suitable for ENFP personality types?"
    
    print("🧪 Testing Available Models for Retrieve-and-Generate")
    print("=" * 60)
    
    for model_arn in models_to_test:
        full_model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{model_arn}"
        print(f"\n🤖 Testing: {model_arn}")
        
        try:
            response = bedrock_runtime.retrieve_and_generate(
                input={'text': test_question},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': full_model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 5
                            }
                        }
                    }
                }
            )
            
            answer = response['output']['text']
            print(f"✅ SUCCESS - Model works!")
            print(f"   Response length: {len(answer)} characters")
            print(f"   Sample: {answer[:150]}...")
            
            # Show citations if available
            if 'citations' in response:
                print(f"   Citations: {len(response['citations'])} sources")
            
            return model_arn  # Return first working model
            
        except Exception as e:
            error_msg = str(e)
            if "don't have access" in error_msg:
                print(f"❌ NO ACCESS - Model not available")
            elif "ValidationException" in error_msg:
                print(f"❌ VALIDATION ERROR - {error_msg}")
            else:
                print(f"❌ ERROR - {error_msg}")
    
    return None

def test_with_working_model(model_arn):
    """Test comprehensive queries with a working model."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    full_model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{model_arn}"
    
    print(f"\n🎯 Testing Comprehensive Queries with {model_arn}")
    print("=" * 60)
    
    test_questions = [
        {
            "question": "What are the best tourist attractions in Hong Kong for someone with an ENFP personality type?",
            "focus": "ENFP personality matching"
        },
        {
            "question": "I'm an INTJ personality. Can you recommend quiet, intellectual attractions in Central district with their operating hours?",
            "focus": "INTJ + location + practical info"
        },
        {
            "question": "What museums or cultural sites would be perfect for an ISFJ personality type in Hong Kong? Include addresses and districts.",
            "focus": "ISFJ + cultural sites + location details"
        }
    ]
    
    for i, test in enumerate(test_questions[:2], 1):  # Test first 2 questions
        print(f"\n📝 Question {i}: {test['focus']}")
        print(f"Query: {test['question']}")
        
        try:
            response = bedrock_runtime.retrieve_and_generate(
                input={'text': test['question']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': full_model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 5
                            }
                        },
                        'generationConfiguration': {
                            'promptTemplate': {
                                'textPromptTemplate': '''
You are a Hong Kong tourism expert specializing in MBTI personality-based recommendations.

Based on the following tourist attraction information:
$search_results$

Please answer this question: $query$

Provide:
1. Specific attractions that match the personality type
2. Why each attraction suits that personality
3. Practical details (address, district, operating hours)
4. Any special tips or recommendations

Be helpful and personalized in your response.
'''
                            }
                        }
                    }
                }
            )
            
            answer = response['output']['text']
            print(f"✅ Generated Response:")
            print(f"{answer}")
            
            # Show retrieval info
            if 'citations' in response:
                print(f"\n📚 Sources: {len(response['citations'])} citations")
                for j, citation in enumerate(response['citations'][:2], 1):
                    if 'retrievedReferences' in citation:
                        print(f"   {j}. {len(citation['retrievedReferences'])} references")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_simple_retrieve_vs_generate():
    """Compare simple retrieve vs retrieve-and-generate."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    query = "ENFP personality tourist attractions Hong Kong Central district"
    
    print(f"\n🔍 Comparison: Retrieve vs Retrieve-and-Generate")
    print("=" * 60)
    print(f"Query: {query}")
    
    # Test 1: Simple Retrieve
    print(f"\n📊 Method 1: Simple Retrieve")
    try:
        retrieve_response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
        
        results = retrieve_response['retrievalResults']
        print(f"✅ Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result['score']:.4f}")
            print(f"      Content: {result['content']['text'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Retrieve-and-Generate (if we have a working model)
    working_model = test_available_models()
    if working_model:
        print(f"\n🤖 Method 2: Retrieve-and-Generate with {working_model}")
        test_with_working_model(working_model)
    else:
        print(f"\n❌ No working models found for retrieve-and-generate")

if __name__ == "__main__":
    print("🚀 Testing Retrieve-and-Generate Functionality")
    print("=" * 70)
    
    # First, find a working model
    working_model = test_available_models()
    
    if working_model:
        print(f"\n✅ Found working model: {working_model}")
        test_with_working_model(working_model)
    else:
        print(f"\n❌ No models available for retrieve-and-generate")
        print("   Falling back to simple retrieve...")
        
        # Test simple retrieve as fallback
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        kb_id = "RCWW86CLM9"
        
        query = "ENFP personality tourist attractions Hong Kong"
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        results = response['retrievalResults']
        print(f"✅ Simple retrieve works: {len(results)} results found")
        
    print(f"\n📋 Summary:")
    print("- Simple retrieve() always works for knowledge base queries")
    print("- retrieve_and_generate() requires specific model access")
    print("- Use simple retrieve() + your own text generation as alternative")
    print("- Focus on optimizing queries rather than retrieve-and-generate")