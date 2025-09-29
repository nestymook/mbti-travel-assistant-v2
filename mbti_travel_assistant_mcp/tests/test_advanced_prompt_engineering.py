#!/usr/bin/env python3
"""
Test Advanced Prompt Engineering Techniques for Knowledge Base Search

This script tests advanced prompt engineering techniques to instruct the foundation model
to focus on finding files with specific metadata/attributes rather than semantic matching.
"""

import boto3
import json
import time
from typing import Dict, List, Any

class AdvancedPromptEngineeringTester:
    """Test advanced prompt engineering techniques for precise knowledge base search."""
    
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
    
    def test_metadata_focused_strategies(self) -> Dict[str, Any]:
        """Test prompt strategies that focus on metadata/file attributes."""
        
        print("🎯 Testing Advanced Prompt Engineering for Metadata-Focused Search")
        print("=" * 70)
        print("Goal: Find files with MBTI=INFJ attribute, not semantic INFJ matching")
        
        # Advanced prompt engineering strategies
        metadata_strategies = {
            "file_attribute_search": """SEARCH INSTRUCTION: Find all documents in the knowledge base where the MBTI attribute equals "INFJ".

Do not interpret or analyze INFJ personality traits. Instead, locate files that have been specifically tagged or labeled with MBTI=INFJ.

Look for documents with:
- MBTI field = INFJ
- MBTI attribute = INFJ  
- MBTI tag = INFJ
- MBTI classification = INFJ

Return all attractions from files that have this exact MBTI attribute match.""",

            "filename_pattern_search": """SEARCH INSTRUCTION: Find all documents in the knowledge base with filenames that start with "INFJ_".

Search for files matching the pattern: INFJ_*.md or INFJ_*.txt

Do not search by content or personality traits. Focus on finding files where the filename begins with "INFJ_" followed by attraction names.

Examples of target files:
- INFJ_M+.md
- INFJ_Central_Market.md  
- INFJ_Hong_Kong_Cultural_Centre.md

Return information from ALL files matching this filename pattern.""",

            "explicit_file_targeting": """SEARCH INSTRUCTION: Retrieve information from documents that are specifically categorized for INFJ personality type.

Target files with these exact identifiers:
- File category: INFJ
- Document type: INFJ attractions
- Classification: INFJ-specific content
- Metadata tag: INFJ

Do not use semantic analysis of INFJ traits. Instead, find documents that have been explicitly labeled or categorized as INFJ content.

Return all tourist attractions from these INFJ-categorized documents.""",

            "structured_data_query": """SEARCH INSTRUCTION: Query the knowledge base for structured data where MBTI field contains "INFJ".

Treat this as a database query: SELECT * FROM attractions WHERE MBTI = "INFJ"

Look for:
- Structured records with MBTI column = INFJ
- Data entries tagged with MBTI: INFJ
- Attraction records classified as INFJ type
- Documents with MBTI metadata = INFJ

Return all attractions that match this exact MBTI field criteria, not personality trait analysis.""",

            "document_classification_search": """SEARCH INSTRUCTION: Find all documents classified under the INFJ category in the knowledge base.

Search criteria:
- Document classification = INFJ
- Content category = INFJ attractions
- File type = INFJ personality matches
- Document label = INFJ-suitable venues

This is a classification-based search, not a content analysis. Find documents that have been pre-classified or pre-tagged as INFJ content.

Return complete information from all INFJ-classified documents.""",

            "direct_metadata_instruction": """IMPORTANT: This is a METADATA SEARCH, not content analysis.

SEARCH TASK: Find documents where MBTI metadata field = "INFJ"

INSTRUCTIONS:
1. Do NOT analyze INFJ personality traits
2. Do NOT interpret what INFJ means
3. DO search for files tagged with MBTI=INFJ
4. DO look for documents labeled as INFJ content
5. DO find files categorized under INFJ classification

QUERY: Retrieve all tourist attractions from documents that have MBTI metadata set to "INFJ".

This is a direct metadata lookup, not semantic matching.""",

            "system_instruction_approach": """[SYSTEM INSTRUCTION] 
You are performing a metadata-based search in a knowledge base.

TASK: Find files with attribute MBTI="INFJ"
METHOD: Metadata lookup, not content interpretation
TARGET: Documents tagged/labeled/classified as INFJ

Do not use your knowledge of INFJ personality traits. Instead, search for documents that have been explicitly marked with MBTI=INFJ in their metadata, filename, or classification.

Return all attractions from files that match this exact metadata criteria."""
        }
        
        results = {}
        
        for strategy_name, query in metadata_strategies.items():
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
                print(f"   Files cited: {analysis['files_cited']}/13 ({analysis['citation_rate']:.1f}%)")
                print(f"   Response time: {analysis['response_time']:.2f}s")
                print(f"   Metadata focus score: {analysis['metadata_focus_score']:.1f}%")
                print(f"   Found: {', '.join(analysis['mentioned_attractions'][:3])}{'...' if len(analysis['mentioned_attractions']) > 3 else ''}")
            else:
                results[strategy_name] = result
                print(f"❌ {strategy_name} failed: {result['error']}")
        
        return results
    
    def test_query(self, query: str, strategy_name: str) -> Dict[str, Any]:
        """Test a single query strategy."""
        
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
        """Analyze the response for metadata focus and completeness."""
        
        if 'error' in result:
            return {'analysis': 'error', 'details': result['error']}
        
        generated_text = result['generated_text']
        citations = result['citations']
        
        # Count mentioned attractions
        mentioned_attractions = []
        for expected in self.expected_infj_attractions:
            if expected.lower() in generated_text.lower():
                mentioned_attractions.append(expected)
        
        # Analyze citations for INFJ files
        cited_files = set()
        infj_files_cited = 0
        for citation in citations:
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        cited_files.add(filename)
                        if filename.startswith('INFJ_'):
                            infj_files_cited += 1
        
        # Check for metadata-focused language
        metadata_keywords = [
            'metadata', 'attribute', 'field', 'tag', 'classification', 
            'category', 'label', 'filename', 'file', 'document type',
            'MBTI=INFJ', 'MBTI field', 'MBTI attribute', 'INFJ_'
        ]
        
        metadata_matches = sum(1 for keyword in metadata_keywords if keyword.lower() in generated_text.lower())
        
        # Check for personality trait language (should be minimal for metadata focus)
        trait_keywords = [
            'introverted', 'intuitive', 'feeling', 'judging',
            'personality', 'traits', 'characteristics', 'empathy',
            'vision', 'meaningful', 'contemplation', 'reflection'
        ]
        
        trait_matches = sum(1 for keyword in trait_keywords if keyword.lower() in generated_text.lower())
        
        # Calculate metadata focus score (high metadata keywords, low trait keywords)
        metadata_focus_score = 0
        if metadata_matches > 0:
            metadata_focus_score = (metadata_matches / (metadata_matches + trait_matches + 1)) * 100
        
        analysis = {
            'attractions_mentioned': len(mentioned_attractions),
            'expected_attractions': len(self.expected_infj_attractions),
            'completeness_rate': len(mentioned_attractions) / len(self.expected_infj_attractions) * 100,
            'files_cited': len(cited_files),
            'infj_files_cited': infj_files_cited,
            'citation_rate': infj_files_cited / 13 * 100,
            'metadata_keywords': metadata_matches,
            'trait_keywords': trait_matches,
            'metadata_focus_score': metadata_focus_score,
            'response_quality': self._calculate_quality(len(mentioned_attractions), metadata_focus_score),
            'mentioned_attractions': mentioned_attractions,
            'cited_files': list(cited_files),
            'response_time': result.get('response_time', 0)
        }
        
        return analysis
    
    def _calculate_quality(self, attractions_found: int, metadata_score: float) -> str:
        """Calculate overall quality rating."""
        attraction_score = attractions_found / 13 * 100
        
        # Weight: 60% completeness + 40% metadata focus
        combined_score = (attraction_score * 0.6) + (metadata_score * 0.4)
        
        if combined_score >= 70:
            return 'high'
        elif combined_score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def export_results(self, results: Dict[str, Any], filename: str = "advanced_prompt_engineering_results.json"):
        """Export test results to JSON."""
        
        # Prepare export data
        export_data = {
            'test_timestamp': __import__('datetime').datetime.now().isoformat(),
            'test_type': 'advanced_prompt_engineering',
            'focus': 'metadata_based_search',
            'knowledge_base_id': self.kb_id,
            'model': 'amazon.nova-pro-v1:0',
            'expected_infj_attractions': self.expected_infj_attractions,
            'strategies_tested': list(results.keys()),
            'results': {}
        }
        
        for strategy_name, strategy_result in results.items():
            if 'analysis' in strategy_result:
                export_data['results'][strategy_name] = {
                    'completeness_rate': strategy_result['analysis']['completeness_rate'],
                    'citation_rate': strategy_result['analysis']['citation_rate'],
                    'metadata_focus_score': strategy_result['analysis']['metadata_focus_score'],
                    'metadata_keywords': strategy_result['analysis']['metadata_keywords'],
                    'trait_keywords': strategy_result['analysis']['trait_keywords'],
                    'response_time': strategy_result['analysis']['response_time'],
                    'quality': strategy_result['analysis']['response_quality'],
                    'attractions_found': strategy_result['analysis']['mentioned_attractions'],
                    'infj_files_cited': strategy_result['analysis']['infj_files_cited']
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
    
    print("🎯 Advanced Prompt Engineering for Metadata-Focused Search")
    print("=" * 70)
    print("Testing techniques to make the model focus on file attributes (MBTI=INFJ)")
    print("rather than semantic understanding of INFJ personality traits")
    
    # Initialize tester
    tester = AdvancedPromptEngineeringTester()
    
    # Test metadata-focused strategies
    results = tester.test_metadata_focused_strategies()
    
    # Export results
    tester.export_results(results)
    
    # Find best metadata-focused strategy
    best_strategy = None
    best_metadata_score = 0
    best_completeness = 0
    
    print(f"\n🎉 Advanced Prompt Engineering Results:")
    print("=" * 50)
    print("Ranking by metadata focus (less personality trait analysis)")
    
    for strategy_name, strategy_result in results.items():
        if 'analysis' in strategy_result:
            analysis = strategy_result['analysis']
            completeness = analysis['completeness_rate']
            metadata_score = analysis['metadata_focus_score']
            
            print(f"🎯 {strategy_name}:")
            print(f"   Attractions: {analysis['attractions_mentioned']}/13 ({completeness:.1f}%)")
            print(f"   Metadata Focus: {metadata_score:.1f}% (higher = better)")
            print(f"   Metadata Keywords: {analysis['metadata_keywords']}")
            print(f"   Trait Keywords: {analysis['trait_keywords']} (lower = better)")
            print(f"   Quality: {analysis['response_quality']}")
            print(f"   Time: {analysis['response_time']:.2f}s")
            
            # Find best strategy (prioritize metadata focus, then completeness)
            if metadata_score > best_metadata_score or (metadata_score == best_metadata_score and completeness > best_completeness):
                best_metadata_score = metadata_score
                best_completeness = completeness
                best_strategy = strategy_name
        else:
            print(f"❌ {strategy_name}: Failed")
    
    if best_strategy:
        print(f"\n🏆 Best Metadata-Focused Strategy: {best_strategy}")
        print(f"   Metadata Focus Score: {best_metadata_score:.1f}%")
        print(f"   Completeness: {best_completeness:.1f}%")
        print(f"   This strategy best focuses on file attributes rather than semantic matching")
    
    print(f"\n📋 Test completed! Check results in data/advanced_prompt_engineering_results.json")

if __name__ == "__main__":
    main()