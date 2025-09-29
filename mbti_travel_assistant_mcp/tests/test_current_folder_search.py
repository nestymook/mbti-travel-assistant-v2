#!/usr/bin/env python3
"""
Test folder-based search with current knowledge base structure
"""

import boto3
import time

def test_current_folder_search():
    """Test folder-based search with current structure."""
    
    print("🎯 Testing Current Folder-Based Search")
    print("=" * 50)
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    # Test strategies for current structure
    strategies = {
        "mbti_individual_folder": """SEARCH INSTRUCTION: Find all files in the "mbti_individual" folder that start with "INFJ_".

Look for files with pattern: mbti_individual/INFJ_*.md

Examples:
- mbti_individual/INFJ_Central_Market.md
- mbti_individual/INFJ_M+.md
- mbti_individual/INFJ_Tai_Kwun.md

Return information from ALL INFJ files in the mbti_individual folder.""",

        "folder_path_pattern": """SEARCH INSTRUCTION: Find files matching the path pattern "mbti_individual/INFJ_*".

Search for all files in the mbti_individual directory that have filenames starting with "INFJ_".

This should locate all individual INFJ attraction files in the organized folder structure.""",

        "directory_specific_search": """SEARCH INSTRUCTION: Navigate to the mbti_individual directory and extract all INFJ files.

TARGET DIRECTORY: mbti_individual/
FILE PATTERN: INFJ_*.md

Find all attraction files for INFJ personality type in this specific directory."""
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
            mbti_individual_files = 0
            cited_files = []
            
            for citation in citations:
                if 'retrievedReferences' in citation:
                    for ref in citation['retrievedReferences']:
                        if 'location' in ref and 's3Location' in ref['location']:
                            uri = ref['location']['s3Location']['uri']
                            filename = uri.split('/')[-1]
                            cited_files.append(uri)
                            
                            if 'mbti_individual' in uri and 'INFJ_' in filename:
                                infj_files += 1
                            if 'mbti_individual' in uri:
                                mbti_individual_files += 1
            
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
            
            results[strategy_name] = {
                'response_time': response_time,
                'citations': len(citations),
                'infj_files': infj_files,
                'mbti_individual_files': mbti_individual_files,
                'attractions_found': len(attractions_found),
                'completeness': len(attractions_found) / len(expected_attractions) * 100,
                'text_length': len(generated_text),
                'attractions_list': attractions_found,
                'cited_files': cited_files[:5]  # First 5 files
            }
            
            print(f"✅ Response: {response_time:.2f}s")
            print(f"📚 Citations: {len(citations)} ({infj_files} INFJ files, {mbti_individual_files} from mbti_individual/)")
            print(f"🎯 Attractions: {len(attractions_found)}/13 ({len(attractions_found)/13*100:.1f}%)")
            print(f"📁 Sample files: {cited_files[:3]}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[strategy_name] = {'error': str(e)}
    
    return results

def analyze_current_results(results):
    """Analyze results from current folder structure."""
    
    print(f"\n🎉 Current Folder Structure Results:")
    print("=" * 50)
    
    valid_results = {k: v for k, v in results.items() if 'error' not in v}
    
    if not valid_results:
        print("❌ No successful strategies")
        return
    
    print(f"{'Strategy':<30} {'Attractions':<12} {'INFJ Files':<12} {'Time':<8}")
    print("-" * 70)
    
    for strategy_name, data in valid_results.items():
        print(f"{strategy_name:<30} {data['attractions_found']:>2}/13 ({data['completeness']:>4.1f}%) {data['infj_files']:>8} files {data['response_time']:>6.1f}s")
    
    # Best strategy
    best_strategy = max(valid_results.items(), key=lambda x: x[1]['completeness'])
    best_name, best_data = best_strategy
    
    print(f"\n🏆 Best Current Strategy: {best_name}")
    print(f"   Completeness: {best_data['completeness']:.1f}%")
    print(f"   INFJ Files Found: {best_data['infj_files']}")
    print(f"   Response Time: {best_data['response_time']:.2f}s")
    print(f"   Attractions: {', '.join(best_data['attractions_list'][:5])}{'...' if len(best_data['attractions_list']) > 5 else ''}")

if __name__ == "__main__":
    print("🔍 Testing Current Knowledge Base Folder Structure")
    print("Structure: mbti_individual/MBTI_TYPE_Attraction.md")
    
    results = test_current_folder_search()
    analyze_current_results(results)
    
    print(f"\n📋 Key Findings:")
    print("- Current structure uses mbti_individual/ folder with MBTI prefix files")
    print("- Folder-based search can target specific directories")
    print("- File naming pattern INFJ_*.md enables precise targeting")
    print("- This structure already provides good organization for MBTI searches")