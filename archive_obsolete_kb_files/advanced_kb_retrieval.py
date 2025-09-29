#!/usr/bin/env python3
"""
Advanced Knowledge Base Retrieval Strategies for Markdown Data

This script demonstrates advanced retrieval techniques to improve
recognition and matching of markdown table data.
"""

import boto3
import json
from typing import List, Dict, Any

def hybrid_search_query(query: str, kb_id: str = "RCWW86CLM9") -> List[Dict]:
    """Perform hybrid search combining semantic and keyword matching."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    try:
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 10,
                    'overrideSearchType': 'HYBRID'  # Combines vector + keyword search
                }
            }
        )
        return response['retrievalResults']
    except Exception as e:
        print(f"Error in hybrid search: {e}")
        return []

def semantic_search_query(query: str, kb_id: str = "RCWW86CLM9") -> List[Dict]:
    """Perform pure semantic vector search."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    try:
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 10,
                    'overrideSearchType': 'SEMANTIC'  # Pure vector search
                }
            }
        )
        return response['retrievalResults']
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []

def enhanced_query_with_context(query: str, kb_id: str = "RCWW86CLM9") -> str:
    """Use retrieve-and-generate for enhanced responses with context."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    try:
        response = bedrock_runtime.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kb_id,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            'numberOfResults': 5,
                            'overrideSearchType': 'HYBRID'
                        }
                    },
                    'generationConfiguration': {
                        'promptTemplate': {
                            'textPromptTemplate': '''
You are a Hong Kong tourism expert specializing in MBTI personality-based recommendations.

Based on the following context about tourist spots and their MBTI personality matches:

$search_results$

Please answer this question: $query$

Guidelines:
1. Focus on the MBTI personality type mentioned in the query
2. Include specific details like addresses, operating hours, and districts
3. Explain why each spot matches the personality type
4. Provide practical visiting information
5. If multiple spots match, rank them by relevance

Answer:'''
                        }
                    }
                }
            }
        )
        return response['output']['text']
    except Exception as e:
        print(f"Error in enhanced query: {e}")
        return ""

def multi_strategy_search(query: str) -> Dict[str, Any]:
    """Compare different search strategies for the same query."""
    
    print(f"\n🔍 Multi-Strategy Search for: '{query}'")
    print("=" * 60)
    
    results = {}
    
    # Strategy 1: Hybrid Search
    print("\n📊 Strategy 1: Hybrid Search (Semantic + Keyword)")
    hybrid_results = hybrid_search_query(query)
    results['hybrid'] = hybrid_results
    
    if hybrid_results:
        for i, result in enumerate(hybrid_results[:3]):
            print(f"  {i+1}. Score: {result['score']:.4f}")
            print(f"     Content: {result['content']['text'][:120]}...")
    else:
        print("  No results found")
    
    # Strategy 2: Pure Semantic Search
    print("\n🧠 Strategy 2: Pure Semantic Search")
    semantic_results = semantic_search_query(query)
    results['semantic'] = semantic_results
    
    if semantic_results:
        for i, result in enumerate(semantic_results[:3]):
            print(f"  {i+1}. Score: {result['score']:.4f}")
            print(f"     Content: {result['content']['text'][:120]}...")
    else:
        print("  No results found")
    
    # Strategy 3: Enhanced Generation
    print("\n✨ Strategy 3: Retrieve and Generate")
    enhanced_response = enhanced_query_with_context(query)
    results['enhanced'] = enhanced_response
    
    if enhanced_response:
        print(f"  Generated Response: {enhanced_response[:200]}...")
    else:
        print("  No response generated")
    
    return results

def test_mbti_specific_queries():
    """Test queries specifically designed for MBTI-tourist spot matching."""
    
    mbti_queries = [
        # Specific MBTI type queries
        "What tourist spots in Hong Kong are perfect for ENFP personality types?",
        "Show me INTJ-friendly attractions with quiet environments",
        "ESFJ personality tourist recommendations in Central district",
        "Museums and cultural sites for ISFP personalities",
        
        # Activity-based queries with MBTI context
        "Outdoor adventure activities for extroverted personalities",
        "Quiet contemplative spaces for introverted MBTI types",
        "Social gathering places for feeling personality types",
        "Analytical and educational attractions for thinking types",
        
        # Location + MBTI queries
        "Central district attractions for ENFJ personalities",
        "Wan Chai area spots suitable for ISTP personality",
        "Tsim Sha Tsui cultural sites for INFP types",
        
        # Time-based queries
        "Evening activities for ESTP personalities",
        "Morning attractions suitable for ISFJ types",
        "Weekend spots for ENTP personality types"
    ]
    
    print("🎯 Testing MBTI-Specific Queries")
    print("=" * 50)
    
    for query in mbti_queries[:3]:  # Test first 3 queries
        multi_strategy_search(query)
        print("\n" + "-" * 60)

def optimize_query_formulation():
    """Demonstrate how to formulate better queries for markdown table data."""
    
    print("\n📝 Query Optimization Techniques")
    print("=" * 40)
    
    # Original vs Optimized queries
    query_pairs = [
        {
            "original": "ENFP spots",
            "optimized": "Tourist attractions in Hong Kong that match ENFP personality type with social and creative activities"
        },
        {
            "original": "Central district",
            "optimized": "Tourist spots located in Central district Hong Kong with operating hours and MBTI personality matches"
        },
        {
            "original": "Museums",
            "optimized": "Museums and cultural attractions in Hong Kong suitable for different MBTI personality types"
        }
    ]
    
    for pair in query_pairs:
        print(f"\n🔄 Original: '{pair['original']}'")
        print(f"✅ Optimized: '{pair['optimized']}'")
        
        # Test both queries
        print("\nOriginal Query Results:")
        orig_results = hybrid_search_query(pair['original'])
        if orig_results:
            print(f"  Found {len(orig_results)} results, top score: {orig_results[0]['score']:.4f}")
        else:
            print("  No results")
        
        print("\nOptimized Query Results:")
        opt_results = hybrid_search_query(pair['optimized'])
        if opt_results:
            print(f"  Found {len(opt_results)} results, top score: {opt_results[0]['score']:.4f}")
        else:
            print("  No results")
        
        print("-" * 40)

def analyze_current_kb_performance():
    """Analyze current knowledge base performance with markdown data."""
    
    print("\n📈 Current Knowledge Base Performance Analysis")
    print("=" * 50)
    
    # Test various query types
    test_cases = [
        {
            "category": "MBTI Direct Match",
            "query": "ENFP personality tourist spots",
            "expected": "Should find spots specifically tagged for ENFP"
        },
        {
            "category": "Location-based",
            "query": "Central district attractions",
            "expected": "Should find spots in Central district"
        },
        {
            "category": "Activity-based",
            "query": "Museums and galleries",
            "expected": "Should find cultural attractions"
        },
        {
            "category": "Time-based",
            "query": "Operating hours weekend",
            "expected": "Should find spots with weekend hours info"
        },
        {
            "category": "Combined Query",
            "query": "ISFJ personality Central district museums weekend hours",
            "expected": "Should find specific matches combining all criteria"
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['category']}")
        print(f"Query: '{test['query']}'")
        print(f"Expected: {test['expected']}")
        
        results = hybrid_search_query(test['query'])
        
        if results:
            print(f"✅ Found {len(results)} results")
            print(f"   Top score: {results[0]['score']:.4f}")
            print(f"   Sample: {results[0]['content']['text'][:100]}...")
            
            # Check if results contain expected keywords
            content = ' '.join([r['content']['text'] for r in results[:3]])
            keywords = test['query'].lower().split()
            found_keywords = [kw for kw in keywords if kw in content.lower()]
            print(f"   Keywords found: {found_keywords}")
        else:
            print("❌ No results found")

if __name__ == "__main__":
    print("🚀 Advanced Knowledge Base Retrieval Testing")
    print("=" * 60)
    
    # 1. Analyze current performance
    analyze_current_kb_performance()
    
    # 2. Test MBTI-specific queries
    test_mbti_specific_queries()
    
    # 3. Demonstrate query optimization
    optimize_query_formulation()
    
    print("\n✅ Analysis complete!")
    print("\nRecommendations:")
    print("1. Use hybrid search for better keyword + semantic matching")
    print("2. Include specific MBTI types and location names in queries")
    print("3. Use retrieve-and-generate for comprehensive responses")
    print("4. Consider smaller chunk sizes for more precise matching")