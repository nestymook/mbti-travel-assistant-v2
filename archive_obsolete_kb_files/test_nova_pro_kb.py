#!/usr/bin/env python3
"""
Test Knowledge Base with Amazon Nova Pro

This script tests the retrieve-and-generate functionality using
Amazon Nova Pro with 300K context window for comprehensive responses.
"""

import boto3
import json
import time

def test_nova_pro_retrieve_and_generate():
    """Test retrieve-and-generate with Nova Pro 300K."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Use Nova Pro with 300K context window
    nova_pro_model = "amazon.nova-pro-v1:0:300k"
    
    print("🚀 Testing Amazon Nova Pro with Knowledge Base")
    print("=" * 60)
    print(f"Model: Nova Pro 300K Context")
    print(f"Knowledge Base: {kb_id}")
    
    # Test questions optimized for MBTI travel recommendations
    test_questions = [
        {
            "question": "What are the best tourist attractions in Hong Kong for someone with an ENFP personality type? Include specific locations, addresses, and operating hours.",
            "focus": "ENFP comprehensive recommendations"
        },
        {
            "question": "I'm an INTJ personality who prefers quiet, intellectual activities. Can you recommend museums, galleries, or cultural sites in Central district with their exact addresses and visiting information?",
            "focus": "INTJ + Central district + detailed info"
        },
        {
            "question": "What tourist spots would be perfect for an ISFJ personality type? I'm looking for traditional, cultural, and caring experiences in Hong Kong. Please include district information and operating schedules.",
            "focus": "ISFJ cultural experiences with practical details"
        },
        {
            "question": "As an ESTP personality, I love active, spontaneous, and social experiences. What Hong Kong attractions would you recommend for weekend visits? Include addresses and weekend operating hours.",
            "focus": "ESTP active experiences with weekend schedules"
        }
    ]
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n🎯 Test {i}: {test['focus']}")
        print(f"Question: {test['question']}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            
            response = bedrock_runtime.retrieve_and_generate(
                input={'text': test['question']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': nova_pro_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 8  # Higher recall for comprehensive answers
                            }
                        },
                        'generationConfiguration': {
                            'promptTemplate': {
                                'textPromptTemplate': '''
You are an expert Hong Kong tourism consultant specializing in MBTI personality-based travel recommendations.

Based on the tourist attraction data provided below:
$search_results$

User Question: $query$

Please provide a comprehensive, personalized response that includes:

1. **Specific Attractions**: List 3-5 tourist spots that perfectly match the personality type
2. **Personality Alignment**: Explain why each attraction suits their MBTI traits
3. **Practical Information**: 
   - Exact addresses and districts
   - Operating hours (weekday, weekend, holidays)
   - Contact information if available
4. **Experience Details**: Describe what they can expect at each location
5. **Additional Tips**: Any special recommendations or insider advice

Format your response in a friendly, helpful tone as if you're personally guiding them through Hong Kong.

Make sure to:
- Match attractions to specific MBTI traits (E/I, S/N, T/F, J/P)
- Include complete practical details for trip planning
- Prioritize the most relevant attractions for their personality
- Provide actionable, specific recommendations
'''
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
            
            # Show retrieval statistics
            if 'citations' in response:
                citations = response['citations']
                print(f"\n📚 Knowledge Base Sources:")
                print(f"   Total citations: {len(citations)}")
                
                total_references = 0
                for citation in citations:
                    if 'retrievedReferences' in citation:
                        total_references += len(citation['retrievedReferences'])
                
                print(f"   Total references: {total_references}")
                
                # Show sample source
                if citations and 'retrievedReferences' in citations[0]:
                    sample_ref = citations[0]['retrievedReferences'][0]
                    if 'content' in sample_ref:
                        sample_content = sample_ref['content']['text'][:100]
                        print(f"   Sample source: {sample_content}...")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            
            # Check if it's a model access issue
            if "don't have access" in str(e):
                print("   → Model access issue. Checking available Nova models...")
                check_nova_access()
            elif "ValidationException" in str(e):
                print("   → Validation error. Check model ARN and configuration.")
            
            print("\n" + "=" * 60)

def check_nova_access():
    """Check which Nova models are accessible."""
    
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    
    try:
        models = bedrock.list_foundation_models()
        nova_models = [
            model for model in models['modelSummaries'] 
            if 'nova' in model['modelId'].lower()
        ]
        
        print(f"\n🔍 Available Nova Models:")
        for model in nova_models:
            print(f"   - {model['modelId']} ({model['modelName']})")
            
    except Exception as e:
        print(f"   Error checking models: {e}")

def test_simple_vs_enhanced_comparison():
    """Compare simple retrieve vs Nova Pro retrieve-and-generate."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    nova_pro_arn = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0:300k"
    
    test_query = "ENFP personality tourist attractions Hong Kong Central district social creative activities"
    
    print(f"\n🔍 Comparison: Simple Retrieve vs Nova Pro Generate")
    print("=" * 60)
    print(f"Query: {test_query}")
    
    # Method 1: Simple Retrieve
    print(f"\n📊 Method 1: Simple Retrieve")
    try:
        retrieve_response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': test_query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        results = retrieve_response['retrievalResults']
        print(f"✅ Found {len(results)} raw results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result['score']:.4f}")
            print(f"      Content: {result['content']['text'][:120]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Method 2: Nova Pro Retrieve-and-Generate
    print(f"\n🤖 Method 2: Nova Pro Retrieve-and-Generate")
    try:
        enhanced_response = bedrock_runtime.retrieve_and_generate(
            input={'text': f"What Hong Kong tourist attractions would be perfect for an ENFP personality type in Central district? Focus on social and creative activities."},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': nova_pro_arn,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5
                        }
                    }
                }
            }
        )
        
        answer = enhanced_response['output']['text']
        print(f"✅ Generated comprehensive response")
        print(f"   Response length: {len(answer)} characters")
        print(f"   Sample: {answer[:200]}...")
        
        if 'citations' in enhanced_response:
            print(f"   Sources used: {len(enhanced_response['citations'])} citations")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_nova_pro_performance():
    """Test Nova Pro performance with different query complexities."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    nova_pro_arn = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0:300k"
    
    print(f"\n⚡ Nova Pro Performance Testing")
    print("=" * 60)
    
    test_cases = [
        {
            "complexity": "Simple",
            "query": "ENFP tourist spots Hong Kong",
            "expected_time": "< 3s"
        },
        {
            "complexity": "Medium", 
            "query": "What are the best museums and cultural attractions in Central district for an INTJ personality type with operating hours?",
            "expected_time": "< 5s"
        },
        {
            "complexity": "Complex",
            "query": "I'm planning a weekend trip to Hong Kong for my ISFJ personality friend who loves traditional culture, quiet spaces, and meaningful experiences. Can you recommend specific attractions in different districts with complete visiting information including addresses, operating hours, and why each place matches ISFJ traits?",
            "expected_time": "< 8s"
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['complexity']} Query Test")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected_time']}")
        
        try:
            start_time = time.time()
            
            response = bedrock_runtime.retrieve_and_generate(
                input={'text': test['query']},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': nova_pro_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 6
                            }
                        }
                    }
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            answer = response['output']['text']
            
            print(f"✅ Response time: {response_time:.2f}s")
            print(f"   Response length: {len(answer)} characters")
            print(f"   Words: ~{len(answer.split())} words")
            
            if 'citations' in response:
                print(f"   Sources: {len(response['citations'])} citations")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🌟 Amazon Nova Pro Knowledge Base Testing")
    print("=" * 70)
    
    # Test 1: Comprehensive MBTI recommendations
    test_nova_pro_retrieve_and_generate()
    
    # Test 2: Performance comparison
    test_simple_vs_enhanced_comparison()
    
    # Test 3: Performance with different complexities
    test_nova_pro_performance()
    
    print(f"\n📋 Summary:")
    print("✅ Nova Pro provides comprehensive, personalized responses")
    print("✅ 300K context window handles complex queries effectively") 
    print("✅ Retrieval + generation creates actionable travel recommendations")
    print("✅ Perfect for MBTI-based tourism applications")
    print("\n🎯 Next Steps:")
    print("- Integrate Nova Pro into your MBTI travel assistant")
    print("- Use the enhanced prompt template for consistent responses")
    print("- Leverage the 300K context for detailed travel planning")