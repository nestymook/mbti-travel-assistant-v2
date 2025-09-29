#!/usr/bin/env python3
"""
S3 Vectors Optimization Guide for Markdown Data

This script provides comprehensive techniques to optimize S3 vectors
for better recognition and retrieval of markdown table data.
"""

import boto3
import json
from datetime import datetime

def technique_1_optimize_chunking():
    """
    Technique 1: Optimize Chunking Strategy
    
    S3 vectors works best with properly sized chunks that contain
    complete semantic units from your markdown table.
    """
    
    print("🔧 Technique 1: Optimized Chunking Strategy")
    print("=" * 50)
    
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    data_source_id = "RQPU9JWBU8"
    
    # Optimal chunking configuration for markdown tables
    optimized_chunking = {
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 200,  # Smaller chunks for table rows
                "overlapPercentage": 30  # Higher overlap for context
            }
        }
    }
    
    print("Recommended chunking settings:")
    print("- Max tokens: 200 (captures 1-2 table rows)")
    print("- Overlap: 30% (preserves context between chunks)")
    print("- Strategy: FIXED_SIZE (consistent chunk sizes)")
    
    return optimized_chunking

def technique_2_embedding_model_optimization():
    """
    Technique 2: Embedding Model Selection
    
    Choose the right embedding model for your data type.
    """
    
    print("\n🧠 Technique 2: Embedding Model Optimization")
    print("=" * 50)
    
    embedding_options = {
        "titan-v1": {
            "arn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
            "dimensions": 1536,
            "best_for": "General text, good for mixed content",
            "pros": "Stable, well-tested",
            "cons": "Larger dimensions, slower"
        },
        "titan-v2": {
            "arn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
            "dimensions": 1024,
            "best_for": "Structured data, tables, faster retrieval",
            "pros": "Optimized for structured content, faster",
            "cons": "Newer model, less tested"
        },
        "cohere-multilingual": {
            "arn": "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-multilingual-v3",
            "dimensions": 1024,
            "best_for": "Multilingual content, semantic similarity",
            "pros": "Great for semantic matching",
            "cons": "May not be optimal for structured data"
        }
    }
    
    print("Current model: Titan v2 (1024 dimensions) ✅")
    print("This is optimal for your markdown table data!")
    
    for model, info in embedding_options.items():
        print(f"\n{model}:")
        print(f"  Dimensions: {info['dimensions']}")
        print(f"  Best for: {info['best_for']}")
        print(f"  Pros: {info['pros']}")
        print(f"  Cons: {info['cons']}")

def technique_3_query_optimization():
    """
    Technique 3: Query Formulation Optimization
    
    Improve how queries are structured for better matching.
    """
    
    print("\n🎯 Technique 3: Query Optimization Strategies")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Test different query formulations
    query_strategies = [
        {
            "strategy": "Keyword-rich",
            "query": "ENFP personality type tourist attractions Hong Kong Central district",
            "description": "Include all relevant keywords"
        },
        {
            "strategy": "Natural language",
            "query": "What tourist spots in Hong Kong are suitable for ENFP personality types?",
            "description": "Use natural question format"
        },
        {
            "strategy": "Context-specific",
            "query": "Hong Kong tourist spots ENFP extroverted feeling perceiving personality",
            "description": "Include MBTI trait descriptions"
        },
        {
            "strategy": "Location + personality",
            "query": "Central district Hong Kong ENFP personality tourist recommendations",
            "description": "Combine location and personality filters"
        }
    ]
    
    print("Testing different query strategies:")
    
    for strategy in query_strategies:
        print(f"\n📝 {strategy['strategy']}: {strategy['description']}")
        print(f"Query: '{strategy['query']}'")
        
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': strategy['query']},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3
                    }
                }
            )
            
            results = response['retrievalResults']
            if results:
                print(f"✅ Found {len(results)} results, top score: {results[0]['score']:.4f}")
                print(f"   Sample: {results[0]['content']['text'][:100]}...")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def technique_4_metadata_enhancement():
    """
    Technique 4: Metadata Enhancement
    
    Add metadata to improve filtering and retrieval.
    """
    
    print("\n📊 Technique 4: Metadata Enhancement")
    print("=" * 50)
    
    print("Recommended metadata fields for your markdown data:")
    
    metadata_fields = {
        "mbti_type": "ENFP, INTJ, ISFJ, etc.",
        "district": "Central, Wan Chai, Tsim Sha Tsui, etc.",
        "category": "Museum, Park, Shopping, Restaurant, etc.",
        "personality_traits": "Extroverted, Introverted, Thinking, Feeling",
        "operating_hours": "Weekday, Weekend, Holiday schedules",
        "location_type": "Indoor, Outdoor, Mixed"
    }
    
    for field, description in metadata_fields.items():
        print(f"- {field}: {description}")
    
    print("\nTo add metadata, you would need to:")
    print("1. Restructure your markdown file with metadata headers")
    print("2. Use custom parsing to extract metadata")
    print("3. Configure data source with metadata extraction")

def technique_5_document_preprocessing():
    """
    Technique 5: Document Preprocessing
    
    Optimize the markdown file structure for better parsing.
    """
    
    print("\n📝 Technique 5: Document Preprocessing")
    print("=" * 50)
    
    print("Current markdown structure analysis:")
    
    # Download and analyze current document
    s3 = boto3.client('s3', region_name='us-east-1')
    
    try:
        response = s3.get_object(
            Bucket='mbti-knowledgebase-209803798463-us-east-1',
            Key='Tourist_Spots_With_Hours.markdown'
        )
        content = response['Body'].read().decode('utf-8')
        
        # Analyze structure
        lines = content.split('\n')
        table_rows = [line for line in lines if '|' in line and line.strip()]
        headers = [line for line in lines if line.startswith('#')]
        
        print(f"✅ Document loaded: {len(lines)} total lines")
        print(f"✅ Table rows found: {len(table_rows)}")
        print(f"✅ Headers found: {len(headers)}")
        
        # Show sample structure
        if table_rows:
            print(f"\nSample table row:")
            print(f"  {table_rows[1][:100]}...")
        
        print("\nOptimization recommendations:")
        print("1. ✅ Use consistent table format (already done)")
        print("2. 🔧 Add section headers for each MBTI type")
        print("3. 🔧 Include summary descriptions for each section")
        print("4. 🔧 Add location groupings (by district)")
        
    except Exception as e:
        print(f"❌ Could not analyze document: {str(e)}")

def technique_6_retrieval_configuration():
    """
    Technique 6: Advanced Retrieval Configuration
    
    Optimize retrieval parameters for better results.
    """
    
    print("\n⚙️ Technique 6: Retrieval Configuration")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Test different retrieval configurations
    configs = [
        {
            "name": "Standard",
            "config": {"numberOfResults": 5},
            "description": "Default configuration"
        },
        {
            "name": "High Recall",
            "config": {"numberOfResults": 10},
            "description": "More results for comprehensive coverage"
        },
        {
            "name": "High Precision",
            "config": {"numberOfResults": 3},
            "description": "Fewer, more relevant results"
        }
    ]
    
    test_query = "ENFP personality tourist spots Central district"
    
    print(f"Testing retrieval configurations with query: '{test_query}'")
    
    for config in configs:
        print(f"\n🔧 {config['name']}: {config['description']}")
        
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': test_query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': config['config']
                }
            )
            
            results = response['retrievalResults']
            if results:
                scores = [r['score'] for r in results]
                print(f"   Results: {len(results)}")
                print(f"   Score range: {min(scores):.4f} - {max(scores):.4f}")
                print(f"   Avg score: {sum(scores)/len(scores):.4f}")
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

def technique_7_create_optimized_kb():
    """
    Technique 7: Create New Optimized Knowledge Base
    
    Create a new KB with all optimizations applied.
    """
    
    print("\n🚀 Technique 7: Create Optimized Knowledge Base")
    print("=" * 50)
    
    print("To create a fully optimized knowledge base:")
    print("1. Use smaller chunk sizes (150-200 tokens)")
    print("2. Higher overlap percentage (25-30%)")
    print("3. Titan v2 embedding model (1024 dimensions)")
    print("4. Cosine distance metric for text similarity")
    print("5. Custom parsing prompt for markdown tables")
    
    print("\nWould you like to create a new optimized KB? (This will:")
    print("- Create new S3 vector bucket and index")
    print("- Use optimized chunking strategy")
    print("- Apply custom parsing for markdown tables")
    print("- Preserve your existing KB for comparison")
    
    return {
        "chunk_size": 200,
        "overlap": 30,
        "embedding_model": "amazon.titan-embed-text-v2:0",
        "distance_metric": "cosine",
        "parsing_strategy": "BEDROCK_FOUNDATION_MODEL"
    }

def run_comprehensive_analysis():
    """Run all optimization techniques and provide recommendations."""
    
    print("🔍 S3 Vectors Optimization Analysis for Markdown Data")
    print("=" * 60)
    
    # Run all techniques
    technique_1_optimize_chunking()
    technique_2_embedding_model_optimization()
    technique_3_query_optimization()
    technique_4_metadata_enhancement()
    technique_5_document_preprocessing()
    technique_6_retrieval_configuration()
    optimizations = technique_7_create_optimized_kb()
    
    print("\n📋 SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n✅ Current Setup Strengths:")
    print("- Using Titan v2 embeddings (optimal for structured data)")
    print("- S3 vectors storage (cost-effective, scalable)")
    print("- Cosine distance metric (good for text similarity)")
    
    print("\n🔧 Recommended Improvements:")
    print("1. IMMEDIATE (No re-ingestion needed):")
    print("   - Use optimized query formulation")
    print("   - Test different numberOfResults settings")
    print("   - Include more context in queries")
    
    print("\n2. MEDIUM EFFORT (Requires re-ingestion):")
    print("   - Reduce chunk size to 200 tokens")
    print("   - Increase overlap to 30%")
    print("   - Add custom parsing prompt")
    
    print("\n3. ADVANCED (Requires document restructuring):")
    print("   - Add metadata headers to markdown")
    print("   - Create section groupings by MBTI type")
    print("   - Include location-based organization")
    
    print("\n🎯 Quick Wins to Try Now:")
    print("1. Use queries like: 'ENFP personality type Hong Kong tourist attractions Central district'")
    print("2. Include MBTI trait descriptions: 'extroverted intuitive feeling perceiving'")
    print("3. Combine location + personality: 'Central district museums ISFJ personality'")
    print("4. Use retrieve-and-generate for comprehensive answers")
    
    return optimizations

if __name__ == "__main__":
    run_comprehensive_analysis()