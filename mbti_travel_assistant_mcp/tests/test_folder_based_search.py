#!/usr/bin/env python3
"""
Test Folder-Based Search Strategies for Hierarchical Knowledge Base

This script tests advanced folder-based search strategies using the new hierarchical structure:
District → MBTI Type → Attraction Files
"""

import boto3
import json
import time
from typing import Dict, List, Any

class FolderBasedSearchTester:
    """Test folder-based search strategies for hierarchical knowledge base."""
    
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
        
        # District structure
        self.districts = [
            "Central_District", "Tsim_Sha_Tsui", "Admiralty", 
            "Sheung_Wan", "Lantau_Island", "Yau_Ma_Tei", "Wan_Chai"
        ]
    
    def test_folder_based_strategies(self) -> Dict[str, Any]:
        """Test various folder-based search strategies."""
        
        print("🎯 Testing Folder-Based Search Strategies")
        print("=" * 60)
        print("Target: Hierarchical structure District/MBTI_Type/Attraction.md")
        
        # Folder-based search strategies
        folder_strategies = {
            "folder_path_search": """SEARCH INSTRUCTION: Find all files in folders with path pattern "*/INFJ/*".

Look for files located in any district folder under the INFJ subfolder.

Examples of target paths:
- Central_District/INFJ/Central_Market.md
- Tsim_Sha_Tsui/INFJ/M+.md
- Admiralty/INFJ/Pacific_Place_Rooftop_Garden.md

Return information from ALL files found in INFJ folders across all districts.""",

            "hierarchical_directory_search": """SEARCH INSTRUCTION: Navigate to INFJ directories within each district folder.

Search in this hierarchical structure:
- Central_District/INFJ/
- Tsim_Sha_Tsui/INFJ/
- Admiralty/INFJ/
- Sheung_Wan/INFJ/
- Lantau_Island/INFJ/
- Yau_Ma_Tei/INFJ/
- Wan_Chai/INFJ/

Extract all attraction files from these INFJ subdirectories.""",

            "wildcard_folder_search": """SEARCH INSTRUCTION: Use wildcard pattern to find INFJ files.

Search pattern: */INFJ/*.md

This should match:
- Any_District/INFJ/Any_Attraction.md

Return all attractions from files matching this folder pattern.""",

            "explicit_district_infj_search": """SEARCH INSTRUCTION: Find files in these specific INFJ folder paths:

1. Central_District/INFJ/ (Central Market, SoHo galleries, Tai Kwun, PMQ)
2. Tsim_Sha_Tsui/INFJ/ (Cultural Centre, Museum of Art, M+, Palace Museum)
3. Admiralty/INFJ/ (Pacific Place Rooftop Garden)
4. Sheung_Wan/INFJ/ (Man Mo Temple)
5. Lantau_Island/INFJ/ (Po Lin Monastery)
6. Yau_Ma_Tei/INFJ/ (Broadway Cinematheque)
7. Wan_Chai/INFJ/ (Hong Kong House of Stories)

Extract all attraction information from these INFJ directories.""",

            "directory_traversal_search": """SEARCH INSTRUCTION: Perform directory traversal to find INFJ content.

ALGORITHM:
1. List all district directories
2. For each district, navigate to INFJ subdirectory
3. Extract all .md files from INFJ folders
4. Return complete attraction information

TARGET STRUCTURE:
District_Name/
  └── INFJ/
      ├── Attraction1.md
      ├── Attraction2.md
      └── Attraction3.md

Find ALL attractions in ALL district INFJ folders.""",

            "filesystem_based_query": """SEARCH INSTRUCTION: Treat the knowledge base as a filesystem.

FILESYSTEM QUERY: find . -path "*/INFJ/*.md" -type f

This command should locate all markdown files in INFJ subdirectories across all district folders.

Return the content of all files found by this filesystem search.""",

            "nested_folder_extraction": """SEARCH INSTRUCTION: Extract files from nested INFJ folders.

FOLDER STRUCTURE TARGET:
Level 1: District folders (Central_District, Tsim_Sha_Tsui, etc.)
Level 2: MBTI folders (INFJ, ENFP, INTJ, etc.)
Level 3: Attraction files (.md files)

EXTRACTION TASK: Get all Level 3 files where Level 2 = "INFJ"

Return complete information from all extracted INFJ attraction files."""
        }
        
        results = {}
        
        for strategy_name, query in folder_strategies.items():
            print(f"\n🔍 Testing Strategy: {strategy_name}")
            print("-" * 50)
            
            result = self.test_query(query, strategy_name)
            
            if 'error' not in result:
                analysis = self.analyze_response(result)
                results[strategy_name] = {
                    'result': result,
                    'analysis': analysis
                }
                
                print(f"\n📊 {strategy_name} Results:")
                print(f"   Attractions found: {analysis['attractions_mentioned']}/13 ({analysis['completeness_rate']:.1f}%)")
                print(f"   Folder references: {analysis['folder_references']}")
                print(f"   District coverage: {analysis['district_coverage']}/7")
                print(f"   Response time: {analysis['response_time']:.2f}s")
                print(f"   Folder focus score: {analysis['folder_focus_score']:.1f}%")
            else:
                results[strategy_name] = result
                print(f"❌ {strategy_name} failed: {result['error']}")
        
        return results
    
    def test_query(self, query: str, strategy_name: str) -> Dict[str, Any]:
        """Test a single folder-based query strategy."""
        
        print(f"🔍 Query length: {len(query)} characters")
        print(f"⏳ Calling retrieve-and-generate...")
        
        try:
            start_time = time.time()
            
            response = self.bedrock_runtime.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': self.model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 30  # Maximum allowed
                            }
                        }
                    }
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"✅ Response received in {response_time:.2f} seconds")
            
            # Extract response
            generated_text = response['output']['text']
            citations = response.get('citations', [])
            
            print(f"📊 Response length: {len(generated_text)} characters")
            print(f"📚 Citations: {len(citations)} sources")
            
            return {
                'model': 'nova-pro',
                'model_arn': self.model_arn,
                'response_time': response_time,
                'generated_text': generated_text,
                'citations': citations,
                'query': query,
                'strategy': strategy_name
            }
            
        except Exception as e:
            print(f"❌ Error with {strategy_name}: {e}")
            return {'error': str(e), 'model': 'nova-pro', 'strategy': strategy_name}
    
    def analyze_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the response for folder-based search effectiveness."""
        
        if 'error' in result:
            return {'analysis': 'error', 'details': result['error']}
        
        generated_text = result['generated_text']
        citations = result['citations']
        
        # Count mentioned attractions
        mentioned_attractions = []
        for expected in self.expected_infj_attractions:
            if expected.lower() in generated_text.lower():
                mentioned_attractions.append(expected)
        
        # Analyze citations for folder structure
        cited_files = set()
        folder_structured_files = 0
        districts_covered = set()
        
        for citation in citations:
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        cited_files.add(filename)
                        
                        # Check if file follows new folder structure
                        if '/' in uri and 'INFJ' in uri:
                            folder_structured_files += 1
                            # Extract district from path
                            path_parts = uri.split('/')
                            if len(path_parts) >= 3:
                                district = path_parts[-3]  # District/INFJ/File.md
                                districts_covered.add(district)
        
        # Check for folder-related language
        folder_keywords = [
            'folder', 'directory', 'path', 'subfolder', 'structure',
            'INFJ/', '/INFJ/', 'district', 'Central_District', 'Tsim_Sha_Tsui',
            'hierarchical', 'nested', 'filesystem', 'traversal'
        ]
        
        folder_references = sum(1 for keyword in folder_keywords if keyword.lower() in generated_text.lower())
        
        # Calculate folder focus score
        folder_focus_score = 0
        if folder_references > 0:
            total_words = len(generated_text.split())
            folder_focus_score = (folder_references / max(total_words / 100, 1)) * 100
            folder_focus_score = min(folder_focus_score, 100)  # Cap at 100%
        
        analysis = {
            'attractions_mentioned': len(mentioned_attractions),
            'expected_attractions': len(self.expected_infj_attractions),
            'completeness_rate': len(mentioned_attractions) / len(self.expected_infj_attractions) * 100,
            'files_cited': len(cited_files),
            'folder_structured_files': folder_structured_files,
            'folder_structure_rate': folder_structured_files / max(len(cited_files), 1) * 100,
            'districts_covered': districts_covered,
            'district_coverage': len(districts_covered),
            'folder_references': folder_references,
            'folder_focus_score': folder_focus_score,
            'response_quality': self._calculate_quality(len(mentioned_attractions), folder_focus_score),
            'mentioned_attractions': mentioned_attractions,
            'cited_files': list(cited_files),
            'response_time': result.get('response_time', 0)
        }
        
        return analysis
    
    def _calculate_quality(self, attractions_found: int, folder_score: float) -> str:
        """Calculate overall quality rating."""
        attraction_score = attractions_found / 13 * 100
        
        # Weight: 70% completeness + 30% folder focus
        combined_score = (attraction_score * 0.7) + (folder_score * 0.3)
        
        if combined_score >= 80:
            return 'high'
        elif combined_score >= 60:
            return 'medium'
        else:
            return 'low'
    
    def export_results(self, results: Dict[str, Any], filename: str = "folder_based_search_results.json"):
        """Export test results to JSON."""
        
        # Prepare export data
        export_data = {
            'test_timestamp': __import__('datetime').datetime.now().isoformat(),
            'test_type': 'folder_based_search',
            'structure': 'District/MBTI_Type/Attraction.md',
            'knowledge_base_id': self.kb_id,
            'model': 'amazon.nova-pro-v1:0',
            'expected_infj_attractions': self.expected_infj_attractions,
            'target_districts': self.districts,
            'strategies_tested': list(results.keys()),
            'results': {}
        }
        
        for strategy_name, strategy_result in results.items():
            if 'analysis' in strategy_result:
                export_data['results'][strategy_name] = {
                    'completeness_rate': strategy_result['analysis']['completeness_rate'],
                    'folder_structure_rate': strategy_result['analysis']['folder_structure_rate'],
                    'district_coverage': strategy_result['analysis']['district_coverage'],
                    'folder_focus_score': strategy_result['analysis']['folder_focus_score'],
                    'folder_references': strategy_result['analysis']['folder_references'],
                    'response_time': strategy_result['analysis']['response_time'],
                    'quality': strategy_result['analysis']['response_quality'],
                    'attractions_found': strategy_result['analysis']['mentioned_attractions'],
                    'districts_covered': list(strategy_result['analysis']['districts_covered'])
                }
            else:
                export_data['results'][strategy_name] = {'error': strategy_result.get('error', 'Unknown error')}
        
        # Save to file
        filepath = f"data/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results exported to: {filepath}")

def main():
    """Main test execution."""
    
    print("🎯 Folder-Based Search Strategy Testing")
    print("=" * 60)
    print("Testing hierarchical folder structure: District → MBTI Type → Files")
    print("Target: Find all INFJ attractions across all district folders")
    
    # Initialize tester
    tester = FolderBasedSearchTester()
    
    # Test folder-based strategies
    results = tester.test_folder_based_strategies()
    
    # Export results
    tester.export_results(results)
    
    # Find best folder-based strategy
    best_strategy = None
    best_score = 0
    
    print(f"\n🎉 Folder-Based Strategy Comparison:")
    print("=" * 70)
    print(f"{'Strategy':<30} {'Attractions':<12} {'Districts':<10} {'Folder Focus':<12} {'Quality'}")
    print("-" * 70)
    
    valid_results = {k: v for k, v in results.items() if 'analysis' in v}
    
    for strategy_name, strategy_result in valid_results.items():
        analysis = strategy_result['analysis']
        completeness = analysis['completeness_rate']
        district_coverage = analysis['district_coverage']
        folder_focus = analysis['folder_focus_score']
        
        # Combined score: 50% completeness + 30% district coverage + 20% folder focus
        combined_score = (completeness * 0.5) + (district_coverage/7 * 100 * 0.3) + (folder_focus * 0.2)
        
        quality = analysis['response_quality']
        
        print(f"{strategy_name:<30} {analysis['attractions_mentioned']:>2}/13 ({completeness:>4.1f}%) {district_coverage:>1}/7 ({district_coverage/7*100:>4.1f}%) {folder_focus:>8.1f}% {quality:>8}")
        
        if combined_score > best_score:
            best_score = combined_score
            best_strategy = strategy_name
    
    if best_strategy:
        best_data = valid_results[best_strategy]['analysis']
        print(f"\n🏆 Best Folder-Based Strategy: {best_strategy}")
        print(f"   Combined Score: {best_score:.1f}/100")
        print(f"   Completeness: {best_data['completeness_rate']:.1f}%")
        print(f"   District Coverage: {best_data['district_coverage']}/7 districts")
        print(f"   Folder Focus: {best_data['folder_focus_score']:.1f}%")
        print(f"   Districts Found: {', '.join(best_data['districts_covered'])}")
    
    print(f"\n📋 Key Findings:")
    print("- Folder-based search can improve organization and targeting")
    print("- Hierarchical structure enables district-specific searches")
    print("- Path-based queries may work better than semantic searches")
    print("- District coverage indicates comprehensive search effectiveness")
    
    print(f"\n📋 Test completed! Check results in data/folder_based_search_results.json")

if __name__ == "__main__":
    main()