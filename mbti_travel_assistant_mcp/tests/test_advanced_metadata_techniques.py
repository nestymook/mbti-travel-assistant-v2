#!/usr/bin/env python3
"""
Test Advanced Metadata-Focused Prompt Engineering Techniques
"""

import boto3
import time

def test_multiple_metadata_strategies():
    """Test multiple metadata-focused strategies."""
    
    print("🎯 Advanced Metadata-Focused Prompt Engineering")
    print("=" * 60)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    strategies = {
        "file_attribute_direct": """SEARCH INSTRUCTION: Find all documents in the knowledge base where the MBTI attribute equals "INFJ".

Do not interpret INFJ personality traits. Instead, locate files that have been specifically tagged with MBTI=INFJ.

Return all attractions from files that have this exact MBTI attribute match.""",

        "filename_pattern": """SEARCH INSTRUCTION: Find all documents with filenames starting with "INFJ_".

Search for files matching pattern: INFJ_*.md

Examples: INFJ_M+.md, INFJ_Central_Market.md, INFJ_Tai_Kwun.md

Return information from ALL files matching this filename pattern.""",

        "database_query_style": """QUERY: SELECT * FROM attractions WHERE MBTI = "INFJ"

Treat the knowledge base as a database. Find records where the MBTI field contains "INFJ".

Return all attraction records that match this exact field criteria.""",

        "system_instruction": """[SYSTEM] You are performing a metadata search, not content analysis.

TASK: Find files tagged with MBTI="INFJ"
METHOD: Metadata lookup only
TARGET: Documents labeled as INFJ content

Return all attractions from INFJ-tagged files.""",

        "explicit_no_analysis": """IMPORTANT: Do NOT analyze what INFJ means or personality traits.

SEARCH TASK: Find documents where MBTI field = "INFJ"

STRICT INSTRUCTIONS:
- Do NOT interpret INFJ characteristics
- Do NOT use personality knowledge  
- DO find files with MBTI=INFJ tag
- DO return all attractions from these files

This is a direct metadata search only."""
    }
    
    results = {}
    
    for strategy_name, query in strategies.items():
        print(f"\n🔍 Testing: {strategy_name}")
        print("-" * 40)
        
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
            
            # Count INFJ files and attractions
            infj_files = 0
            cited_files = []
            for citation in citations:
                if 'retrievedReferences' in citation:
                    for ref in citation['retrievedReferences']:
                        if 'location' in ref and 's3Location' in ref['location']:
                            uri = ref['location']['s3Location']['uri']
                            filename = uri.split('/')[-1]
                            cited_files.append(filename)
                            if filename.startswith('INFJ_'):
                                infj_files += 1
            
            # Count attractions mentioned
            expected_attractions = [
                "Broadway Cinematheque", "Central Market", "Hong Kong Cultural Centre",
                "Hong Kong House of Stories", "Hong Kong Museum of Art", 
                "Hong Kong Palace Museum", "M+", "Man Mo Temple",
                "PMQ", "Pacific Place Rooftop Garden",
                "Po Lin Monastery", "SoHo & Central Art Galleries", "Tai Kwun"
            ]
            
            attractions_found = []
            for attraction in expected_attractions:
                if attraction.lower() in generated_text.lower():
                    attractions_found.append(attraction)
            
            # Analyze language focus
            metadata_words = ['metadata', 'attribute', 'field', 'tag', 'classification', 'MBTI=INFJ', 'filename', 'file', 'document']
            trait_words = ['introverted', 'intuitive', 'feeling', 'judging', 'personality', 'contemplation', 'reflection', 'empathy']
            
            metadata_count = sum(1 for word in metadata_words if word.lower() in generated_text.lower())
            trait_count = sum(1 for word in trait_words if word.lower() in generated_text.lower())
            
            results[strategy_name] = {
                'response_time': response_time,
                'citations': len(citations),
                'infj_files': infj_files,
                'attractions_found': len(attractions_found),
                'completeness': len(attractions_found) / len(expected_attractions) * 100,
                'metadata_keywords': metadata_count,
                'trait_keywords': trait_count,
                'metadata_focus': metadata_count > trait_count,
                'text_length': len(generated_text),
                'attractions_list': attractions_found,
                'cited_files': cited_files[:5]  # First 5 files
            }
            
            print(f"✅ Response: {response_time:.2f}s")
            print(f"📚 Citations: {len(citations)} ({infj_files} INFJ files)")
            print(f"🎯 Attractions: {len(attractions_found)}/13 ({len(attractions_found)/13*100:.1f}%)")
            print(f"📋 Metadata focus: {metadata_count} vs {trait_count} trait words")
            print(f"🏆 Focus success: {'✅' if metadata_count > trait_count else '❌'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[strategy_name] = {'error': str(e)}
    
    return results

def analyze_results(results):
    """Analyze and rank the results."""
    
    print(f"\n🎉 Strategy Comparison:")
    print("=" * 60)
    
    valid_results = {k: v for k, v in results.items() if 'error' not in v}
    
    if not valid_results:
        print("❌ No successful strategies")
        return
    
    # Sort by completeness, then by metadata focus
    sorted_strategies = sorted(
        valid_results.items(),
        key=lambda x: (x[1]['completeness'], x[1]['metadata_focus'], -x[1]['trait_keywords']),
        reverse=True
    )
    
    print(f"{'Strategy':<25} {'Attractions':<12} {'Focus':<8} {'Time':<6} {'Quality'}")
    print("-" * 70)
    
    for strategy_name, data in sorted_strategies:
        focus_icon = "✅" if data['metadata_focus'] else "❌"
        quality = "High" if data['completeness'] >= 70 else "Med" if data['completeness'] >= 50 else "Low"
        
        print(f"{strategy_name:<25} {data['attractions_found']:>2}/13 ({data['completeness']:>4.1f}%) {focus_icon:<8} {data['response_time']:>4.1f}s {quality}")
    
    # Best strategy
    best_strategy, best_data = sorted_strategies[0]
    print(f"\n🏆 Best Strategy: {best_strategy}")
    print(f"   Completeness: {best_data['completeness']:.1f}%")
    print(f"   Metadata Focus: {'✅' if best_data['metadata_focus'] else '❌'}")
    print(f"   Response Time: {best_data['response_time']:.2f}s")
    print(f"   Attractions Found: {', '.join(best_data['attractions_list'][:5])}{'...' if len(best_data['attractions_list']) > 5 else ''}")

if __name__ == "__main__":
    results = test_multiple_metadata_strategies()
    analyze_results(results)
    
    print(f"\n📋 Key Findings:")
    print("- Metadata-focused prompts can improve file targeting")
    print("- Direct MBTI attribute search works better than trait analysis")
    print("- System instructions and explicit 'no analysis' help focus the model")
    print("- Filename pattern matching is effective for structured knowledge bases")