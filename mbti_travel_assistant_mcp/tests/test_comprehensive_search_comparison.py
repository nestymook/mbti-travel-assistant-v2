#!/usr/bin/env python3
"""
Comprehensive Search Strategy Comparison

This script compares all discovered search strategies:
1. Semantic MBTI trait-based search
2. Filename pattern matching
3. Folder-based search (current structure)
4. Metadata-focused search
"""

import boto3
import json
import time
from typing import Dict, List, Any

class ComprehensiveSearchTester:
    """Compare all search strategies comprehensively."""
    
    def __init__(self, kb_id: str = "RCWW86CLM9", region: str = "us-east-1"):
        self.kb_id = kb_id
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.model_arn = "amazon.nova-pro-v1:0"
        
        # Expected INFJ attractions for validation
        self.expected_infj_attractions = [
            "Broadway Cinematheque", "Central Market", "Hong Kong Cultural Centre",
            "Hong Kong House of Stories", "Hong Kong Museum of Art", 
            "Hong Kong Palace Museum", "M+", "Man Mo Temple",
            "PMQ (Police Married Quarters)", "Pacific Place Rooftop Garden",
            "Po Lin Monastery", "SoHo & Central Art Galleries", "Tai Kwun"
        ]
    
    def test_all_strategies(self) -> Dict[str, Any]:
        """Test all discovered search strategies."""
        
        print("🎯 Comprehensive Search Strategy Comparison")
        print("=" * 60)
        print("Comparing: Semantic, Filename, Folder, and Metadata approaches")
        
        # All discovered strategies
        all_strategies = {
            # 1. Semantic approaches (baseline)
            "semantic_comprehensive": """Search for Hong Kong tourist attractions specifically suitable for INFJ personalities.

INFJ Profile:
- Seek meaningful, authentic experiences with emotional depth
- Prefer quieter venues that allow for contemplation and reflection
- Drawn to artistic, creative, and culturally significant places
- Value spiritual connections and philosophical exploration

Find attractions including museums, art galleries, temples, heritage sites, creative districts, and contemplative spaces.""",

            # 2. Filename pattern approaches (best from previous tests)
            "filename_pattern": """SEARCH INSTRUCTION: Find all documents with filenames starting with "INFJ_".

Search for files matching pattern: INFJ_*.md

Examples: INFJ_M+.md, INFJ_Central_Market.md, INFJ_Tai_Kwun.md

Return information from ALL files matching this filename pattern.""",

            # 3. Current folder structure approaches (best performing)
            "folder_directory_search": """SEARCH INSTRUCTION: Navigate to the mbti_individual directory and extract all INFJ files.

TARGET DIRECTORY: mbti_individual/
FILE PATTERN: INFJ_*.md

Find all attraction files for INFJ personality type in this specific directory.""",

            # 4. Metadata-focused approaches
            "metadata_attribute_search": """SEARCH INSTRUCTION: Find all documents in the knowledge base where the MBTI attribute equals "INFJ".

Do not interpret INFJ personality traits. Instead, locate files that have been specifically tagged with MBTI=INFJ.

Return all attractions from files that have this exact MBTI attribute match.""",

            # 5. Explicit no-analysis approach
            "explicit_no_analysis": """IMPORTANT: Do NOT analyze what INFJ means or personality traits.

SEARCH TASK: Find documents where MBTI field = "INFJ"

STRICT INSTRUCTIONS:
- Do NOT interpret INFJ characteristics
- Do NOT use personality knowledge  
- DO find files with MBTI=INFJ tag
- DO return all attractions from these files

This is a direct metadata search only.""",

            # 6. Hybrid approach combining best techniques
            "hybrid_folder_filename": """SEARCH INSTRUCTION: Find files in the mbti_individual folder with filenames starting with "INFJ_".

COMBINED APPROACH:
1. Navigate to mbti_individual directory
2. Look for files matching pattern INFJ_*.md
3. Extract all attraction information from these files

This combines folder-based targeting with filename pattern matching for maximum precision.""",

            # 7. Database-style query
            "database_query_style": """QUERY: SELECT * FROM attractions WHERE MBTI = "INFJ" AND folder = "mbti_individual"

Treat the knowledge base as a database. Find records in the mbti_individual folder where the MBTI field contains "INFJ".

Return all attraction records that match this exact criteria."""
        }
        
        results = {}
        
        for strategy_name, query in all_strategies.items():
            print(f"\n🔍 Testing Strategy: {strategy_name}")
            print("-" * 50)
            
            result = self.test_query(query, strategy_name)
            
            if 'error' not in result:
                analysis = self.analyze_response(result)
                results[strategy_name] = {
                    'result': result,
                    'analysis': analysis
                }
                
                print(f"✅ {strategy_name}:")
                print(f"   Attractions: {analysis['attractions_mentioned']}/13 ({analysis['completeness_rate']:.1f}%)")
                print(f"   Response time: {analysis['response_time']:.2f}s")
                print(f"   Quality: {analysis['response_quality']}")
            else:
                results[strategy_name] = result
                print(f"❌ {strategy_name} failed: {result['error']}")
        
        return results
    
    def test_query(self, query: str, strategy_name: str) -> Dict[str, Any]:
        """Test a single query strategy."""
        
        try:
            start_time = time.time()
            
            response = self.bedrock_runtime.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.model_arn,
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
            
            return {
                'model': 'nova-pro',
                'response_time': response_time,
                'generated_text': generated_text,
                'citations': citations,
                'query': query,
                'strategy': strategy_name
            }
            
        except Exception as e:
            return {'error': str(e), 'strategy': strategy_name}
    
    def analyze_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response for completeness and effectiveness."""
        
        if 'error' in result:
            return {'analysis': 'error', 'details': result['error']}
        
        generated_text = result['generated_text']
        citations = result['citations']
        
        # Count mentioned attractions
        mentioned_attractions = []
        for expected in self.expected_infj_attractions:
            if expected.lower() in generated_text.lower():
                mentioned_attractions.append(expected)
        
        # Analyze citations
        cited_files = set()
        infj_files = 0
        mbti_individual_files = 0
        
        for citation in citations:
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        cited_files.add(filename)
                        
                        if 'INFJ_' in filename:
                            infj_files += 1
                        if 'mbti_individual' in uri:
                            mbti_individual_files += 1
        
        # Calculate quality score
        completeness_rate = len(mentioned_attractions) / len(self.expected_infj_attractions) * 100
        
        analysis = {
            'attractions_mentioned': len(mentioned_attractions),
            'completeness_rate': completeness_rate,
            'infj_files_cited': infj_files,
            'mbti_individual_files': mbti_individual_files,
            'total_citations': len(citations),
            'response_quality': 'high' if completeness_rate >= 70 else 'medium' if completeness_rate >= 50 else 'low',
            'mentioned_attractions': mentioned_attractions,
            'response_time': result.get('response_time', 0)
        }
        
        return analysis
    
    def export_comprehensive_results(self, results: Dict[str, Any]):
        """Export comprehensive comparison results."""
        
        export_data = {
            'test_timestamp': __import__('datetime').datetime.now().isoformat(),
            'test_type': 'comprehensive_search_comparison',
            'model': 'amazon.nova-pro-v1:0',
            'knowledge_base_id': self.kb_id,
            'expected_infj_attractions': self.expected_infj_attractions,
            'strategies_tested': list(results.keys()),
            'results': {}
        }
        
        for strategy_name, strategy_result in results.items():
            if 'analysis' in strategy_result:
                export_data['results'][strategy_name] = {
                    'completeness_rate': strategy_result['analysis']['completeness_rate'],
                    'response_time': strategy_result['analysis']['response_time'],
                    'quality': strategy_result['analysis']['response_quality'],
                    'attractions_found': strategy_result['analysis']['mentioned_attractions'],
                    'infj_files_cited': strategy_result['analysis']['infj_files_cited'],
                    'total_citations': strategy_result['analysis']['total_citations']
                }
            else:
                export_data['results'][strategy_name] = {'error': strategy_result.get('error', 'Unknown error')}
        
        filepath = "data/comprehensive_search_comparison.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results exported to: {filepath}")

def main():
    """Main comprehensive test execution."""
    
    print("🎯 Comprehensive Search Strategy Comparison")
    print("=" * 60)
    print("Testing ALL discovered approaches to find the ultimate best strategy")
    
    # Initialize tester
    tester = ComprehensiveSearchTester()
    
    # Test all strategies
    results = tester.test_all_strategies()
    
    # Export results
    tester.export_comprehensive_results(results)
    
    # Comprehensive analysis
    print(f"\n🏆 FINAL STRATEGY RANKING:")
    print("=" * 80)
    print(f"{'Rank':<4} {'Strategy':<30} {'Completeness':<12} {'Time':<8} {'Quality':<8} {'Score'}")
    print("-" * 80)
    
    valid_results = {k: v for k, v in results.items() if 'analysis' in v}
    
    # Calculate comprehensive scores
    scored_results = []
    for strategy_name, strategy_result in valid_results.items():
        analysis = strategy_result['analysis']
        
        # Comprehensive scoring: 70% completeness + 20% speed + 10% quality
        completeness_score = analysis['completeness_rate']
        speed_score = max(0, 100 - (analysis['response_time'] * 10))  # Faster = higher score
        quality_score = {'high': 100, 'medium': 70, 'low': 40}[analysis['response_quality']]
        
        total_score = (completeness_score * 0.7) + (speed_score * 0.2) + (quality_score * 0.1)
        
        scored_results.append((strategy_name, analysis, total_score))
    
    # Sort by total score
    scored_results.sort(key=lambda x: x[2], reverse=True)
    
    for rank, (strategy_name, analysis, score) in enumerate(scored_results, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        
        print(f"{medal} {rank:<2} {strategy_name:<30} {analysis['attractions_mentioned']:>2}/13 ({analysis['completeness_rate']:>4.1f}%) {analysis['response_time']:>6.1f}s {analysis['response_quality']:>8} {score:>6.1f}")
    
    # Winner analysis
    if scored_results:
        winner_name, winner_analysis, winner_score = scored_results[0]
        print(f"\n🎉 ULTIMATE WINNER: {winner_name}")
        print(f"   🏆 Overall Score: {winner_score:.1f}/100")
        print(f"   🎯 Completeness: {winner_analysis['completeness_rate']:.1f}% ({winner_analysis['attractions_mentioned']}/13)")
        print(f"   ⚡ Speed: {winner_analysis['response_time']:.2f} seconds")
        print(f"   💎 Quality: {winner_analysis['response_quality']}")
        print(f"   📋 Found: {', '.join(winner_analysis['mentioned_attractions'][:5])}{'...' if len(winner_analysis['mentioned_attractions']) > 5 else ''}")
    
    print(f"\n📊 Key Insights:")
    print("- Folder-based approaches outperform semantic searches")
    print("- Filename patterns provide precise targeting")
    print("- Current mbti_individual/ structure is highly effective")
    print("- Metadata-focused instructions improve accuracy")
    print("- Hybrid approaches may offer best of both worlds")
    
    print(f"\n📋 Test completed! Check comprehensive results in data/")

if __name__ == "__main__":
    main()