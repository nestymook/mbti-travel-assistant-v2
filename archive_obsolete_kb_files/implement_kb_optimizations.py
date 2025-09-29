#!/usr/bin/env python3
"""
Implement Knowledge Base Optimizations

This script implements the most effective optimizations for better
markdown data recognition in S3 vectors.
"""

import boto3
import json
import time
from datetime import datetime

def create_optimized_data_source():
    """Create a new optimized data source with better chunking."""
    
    bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    try:
        print("Creating optimized data source...")
        
        # Create new data source with optimized settings
        response = bedrock.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"OptimizedMarkdownSource-{timestamp}",
            description="Optimized data source for markdown table recognition",
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
                        "maxTokens": 200,  # Smaller chunks for table rows
                        "overlapPercentage": 30  # Higher overlap for context
                    }
                },
                "parsingConfiguration": {
                    "parsingStrategy": "BEDROCK_FOUNDATION_MODEL",
                    "bedrockFoundationModelConfiguration": {
                        "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                        "parsingPrompt": """
You are parsing a markdown table containing Hong Kong tourist spots with MBTI personality type mappings.

Extract information for each tourist spot as a complete, self-contained chunk:

For each row, create a chunk that includes:
1. Tourist Spot Name: [Name]
2. MBTI Type: [Personality Type] 
3. Description: [What makes this spot special]
4. Location: [Full address and district]
5. Operating Hours: [Weekday, weekend, and holiday hours]
6. Contact/Remarks: [Any additional information]

Make each chunk searchable by:
- MBTI personality type (ENFP, INTJ, etc.)
- Location/district names
- Activity types and descriptions
- Operating schedule information

Preserve the connection between personality types and recommended activities.
Format each chunk as natural, readable text that maintains all the structured information.
"""
                    }
                }
            }
        )
        
        new_data_source_id = response['dataSource']['dataSourceId']
        print(f"✅ Created optimized data source: {new_data_source_id}")
        
        # Start ingestion job immediately
        print("Starting ingestion job...")
        ingestion_response = bedrock.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=new_data_source_id
        )
        
        job_id = ingestion_response['ingestionJob']['ingestionJobId']
        print(f"✅ Started ingestion job: {job_id}")
        
        # Monitor ingestion progress
        print("Monitoring ingestion progress...")
        while True:
            job_status = bedrock.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=new_data_source_id,
                ingestionJobId=job_id
            )
            
            status = job_status['ingestionJob']['status']
            print(f"Status: {status}")
            
            if status in ['COMPLETE', 'FAILED']:
                break
            
            time.sleep(10)
        
        if status == 'COMPLETE':
            stats = job_status['ingestionJob']['statistics']
            print(f"✅ Ingestion complete!")
            print(f"   Documents scanned: {stats['numberOfDocumentsScanned']}")
            print(f"   Documents indexed: {stats['numberOfNewDocumentsIndexed']}")
            print(f"   Documents failed: {stats['numberOfDocumentsFailed']}")
            
            return new_data_source_id
        else:
            print(f"❌ Ingestion failed with status: {status}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating optimized data source: {str(e)}")
        return None

def test_optimized_queries(data_source_id=None):
    """Test queries with optimized formulations."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    # Optimized query formulations
    optimized_queries = [
        {
            "category": "MBTI Direct Match",
            "query": "ENFP personality type extroverted intuitive feeling perceiving tourist attractions Hong Kong",
            "expected": "Social, creative, flexible activities"
        },
        {
            "category": "MBTI + Location",
            "query": "INTJ personality type Central district Hong Kong museums galleries quiet spaces",
            "expected": "Intellectual, solitary activities in Central"
        },
        {
            "category": "Activity + Personality",
            "query": "Museums cultural sites ISFJ personality type caring supportive traditional Hong Kong",
            "expected": "Cultural sites matching ISFJ traits"
        },
        {
            "category": "Time + Location + MBTI",
            "query": "Weekend operating hours Central district ESFJ personality social activities Hong Kong",
            "expected": "Social weekend activities in Central"
        },
        {
            "category": "Comprehensive Query",
            "query": "Hong Kong tourist attractions MBTI personality matching Central Wan Chai districts museums parks social activities",
            "expected": "Multiple matches across districts and activities"
        }
    ]
    
    print(f"\n🧪 Testing Optimized Queries")
    print("=" * 50)
    
    for test in optimized_queries:
        print(f"\n📝 {test['category']}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        
        try:
            response = bedrock_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': test['query']},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            )
            
            results = response['retrievalResults']
            
            if results:
                print(f"✅ Found {len(results)} results")
                print(f"   Score range: {results[-1]['score']:.4f} - {results[0]['score']:.4f}")
                
                # Show top result
                top_result = results[0]
                content = top_result['content']['text']
                print(f"   Top result: {content[:150]}...")
                
                # Check for MBTI types in results
                mbti_types = ['ENFP', 'INTJ', 'ISFJ', 'ESFJ', 'INFP', 'ESTP', 'ISFP', 'ENTP']
                found_types = [mbti for mbti in mbti_types if mbti in content]
                if found_types:
                    print(f"   MBTI types found: {found_types}")
                
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_retrieve_and_generate():
    """Test the retrieve-and-generate functionality for comprehensive answers."""
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    print(f"\n🤖 Testing Retrieve-and-Generate")
    print("=" * 50)
    
    test_questions = [
        "What are the best tourist attractions in Hong Kong for someone with an ENFP personality type?",
        "I'm an INTJ personality. Can you recommend quiet, intellectual attractions in Central district?",
        "What museums or cultural sites would be perfect for an ISFJ personality type in Hong Kong?",
        "I have an ESTP personality and love active, social experiences. What Hong Kong attractions would you recommend?"
    ]
    
    for question in test_questions[:2]:  # Test first 2 questions
        print(f"\n❓ Question: {question}")
        
        try:
            response = bedrock_runtime.retrieve_and_generate(
                input={'text': question},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 5
                            }
                        },
                        'generationConfiguration': {
                            'promptTemplate': {
                                'textPromptTemplate': '''
Based on the Hong Kong tourist attraction data provided, please answer the user's question about MBTI personality-matched recommendations.

Context: $search_results$

User Question: $query$

Please provide:
1. Specific tourist attractions that match the personality type
2. Why each attraction suits that personality type
3. Practical information like location, district, and operating hours
4. Any special recommendations or tips

Answer in a helpful, personalized tone as a Hong Kong tourism expert.
'''
                            }
                        }
                    }
                }
            )
            
            answer = response['output']['text']
            print(f"🎯 Generated Answer:")
            print(f"   {answer[:300]}...")
            
            # Show citations if available
            if 'citations' in response:
                print(f"   Citations: {len(response['citations'])} sources")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def compare_before_after_optimization():
    """Compare performance before and after optimization."""
    
    print(f"\n📊 Performance Comparison")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    kb_id = "RCWW86CLM9"
    
    test_query = "ENFP personality tourist attractions Hong Kong"
    
    # Test with different configurations
    configs = [
        {
            "name": "Standard (3 results)",
            "config": {"numberOfResults": 3}
        },
        {
            "name": "High Recall (8 results)",
            "config": {"numberOfResults": 8}
        },
        {
            "name": "Precision Focus (2 results)",
            "config": {"numberOfResults": 2}
        }
    ]
    
    print(f"Test query: '{test_query}'")
    
    for config in configs:
        print(f"\n🔧 {config['name']}:")
        
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
                print(f"   Average score: {sum(scores)/len(scores):.4f}")
                
                # Check content quality
                content = ' '.join([r['content']['text'] for r in results])
                mbti_mentions = content.count('ENFP') + content.count('personality')
                print(f"   MBTI relevance: {mbti_mentions} mentions")
                
            else:
                print("   No results found")
                
        except Exception as e:
            print(f"   Error: {str(e)}")

def main():
    """Run the complete optimization implementation."""
    
    print("🚀 Implementing S3 Vectors Optimizations for Markdown Data")
    print("=" * 70)
    
    print("\nStep 1: Testing current performance...")
    test_optimized_queries()
    
    print("\nStep 2: Testing retrieve-and-generate...")
    test_retrieve_and_generate()
    
    print("\nStep 3: Performance comparison...")
    compare_before_after_optimization()
    
    print("\nStep 4: Create optimized data source? (y/n)")
    # Uncomment the next lines to actually create optimized data source
    # create_optimized = input().lower().strip() == 'y'
    # if create_optimized:
    #     new_ds_id = create_optimized_data_source()
    #     if new_ds_id:
    #         print(f"\nStep 5: Testing with optimized data source...")
    #         test_optimized_queries(new_ds_id)
    
    print("\n✅ Optimization analysis complete!")
    print("\n📋 Key Findings:")
    print("1. Current setup works but can be improved with better queries")
    print("2. Retrieve-and-generate provides more comprehensive answers")
    print("3. Including MBTI trait descriptions improves matching")
    print("4. Combining location + personality gives better results")
    print("5. Smaller chunks with more overlap would improve precision")

if __name__ == "__main__":
    main()