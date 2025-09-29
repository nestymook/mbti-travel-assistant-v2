#!/usr/bin/env python3
"""
Test Realistic MBTI-Based Search Strategies

This script tests realistic approaches for MBTI personality-based attraction discovery,
excluding the unrealistic explicit naming approach.
"""

import boto3
import json
import time
from typing import Dict, List, Any

class RealisticMBTISearchTester:
    """Test realistic MBTI-based search strategies."""
    
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
    
    def test_realistic_strategies(self) -> Dict[str, Any]:
        """Test realistic MBTI-based search strategies."""
        
        print("🎯 Testing Realistic MBTI-Based Search Strategies")
        print("=" * 60)
        print("Focus: Strategies that work without knowing attraction names beforehand")
        
        # Realistic search strategies that users would actually use
        realistic_strategies = {
            "mbti_traits_focused": """Find Hong Kong tourist attractions perfect for INFJ personality types.

INFJ characteristics:
- INTROVERTED: Prefer quiet, peaceful environments over crowded tourist spots
- INTUITIVE: Drawn to meaningful, symbolic experiences with deeper significance  
- FEELING: Value emotional connections and empathetic experiences
- JUDGING: Appreciate structured, purposeful visits with clear cultural value

Find attractions that offer contemplative spaces, artistic inspiration, cultural depth, spiritual connections, and authentic local experiences. Include museums, galleries, temples, heritage sites, and creative districts.

Provide detailed information for each attraction including why it suits INFJ traits.""",

            "experience_categories": """Search for Hong Kong attractions in these categories that suit contemplative, artistic personalities:

1. Art Museums & Galleries - for creative inspiration and reflection
2. Cultural Heritage Sites - for historical depth and meaning
3. Spiritual & Religious Sites - for contemplation and inner peace
4. Creative Districts & Studios - for artistic exploration
5. Quiet Gardens & Rooftops - for peaceful reflection
6. Independent Cinemas - for thoughtful film experiences
7. Cultural Centers - for meaningful performances and exhibitions

Focus on venues that offer depth, authenticity, and opportunities for quiet reflection rather than commercial tourist attractions.""",

            "personality_keywords": """Find Hong Kong attractions for people who enjoy:
- Quiet contemplation and deep thinking
- Artistic and creative experiences
- Cultural learning and historical exploration
- Spiritual and meaningful connections
- Authentic, non-touristy experiences
- Beautiful, inspiring environments
- Opportunities for reflection and introspection

Search for museums, art spaces, temples, cultural sites, gardens, and creative venues that provide these experiences.""",

            "anti_crowd_focus": """Find Hong Kong attractions suitable for introverted travelers who prefer:
- Less crowded, peaceful environments
- Meaningful cultural experiences over entertainment
- Places for quiet reflection and contemplation
- Artistic and creative inspiration
- Authentic local culture and history
- Spiritual or philosophical depth
- Beautiful, serene settings

Avoid busy tourist traps and focus on contemplative, culturally rich venues.""",

            "comprehensive_mbti": """Search for Hong Kong tourist attractions specifically suitable for INFJ personalities.

INFJ Profile:
- Seek meaningful, authentic experiences with emotional depth
- Prefer quieter venues that allow for contemplation and reflection
- Drawn to artistic, creative, and culturally significant places
- Value spiritual connections and philosophical exploration
- Appreciate historical context and cultural learning
- Enjoy beautiful, inspiring environments that spark imagination

Find attractions including:
- Museums and art galleries with thought-provoking collections
- Historic temples and spiritual sites for reflection
- Cultural heritage locations with deep significance
- Creative districts and artistic communities
- Peaceful gardens and contemplative spaces
- Independent cultural venues and cinemas

Provide complete details explaining INFJ suitability for each location."""
        }
        
        results = {}
        
        for strategy_name, query in realistic_strategies.items():
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
                print(f"   Quality: {analysis['response_quality']}")
                print(f"   Found: {', '.join(analysis['mentioned_attractions'][:5])}{'...' if len(analysis['mentioned_attractions']) > 5 else ''}")
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
        """Analyze the response for completeness and quality."""
        
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
        for citation in citations:
            if 'retrievedReferences' in citation:
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        if filename.startswith('INFJ_'):
                            cited_files.add(filename)
        
        # Check for INFJ keywords
        infj_keywords = [
            'introverted', 'intuitive', 'feeling', 'judging',
            'empathy', 'vision', 'meaningful', 'deep', 'reflection',
            'spiritual', 'artistic', 'cultural', 'contemplation',
            'quiet', 'peaceful', 'authentic', 'creative'
        ]
        
        keyword_matches = sum(1 for keyword in infj_keywords if keyword in generated_text.lower())
        
        analysis = {
            'attractions_mentioned': len(mentioned_attractions),
            'expected_attractions': len(self.expected_infj_attractions),
            'completeness_rate': len(mentioned_attractions) / len(self.expected_infj_attractions) * 100,
            'files_cited': len(cited_files),
            'expected_files': 13,
            'citation_rate': len(cited_files) / 13 * 100,
            'infj_keyword_matches': keyword_matches,
            'keyword_density': keyword_matches / len(infj_keywords) * 100,
            'response_quality': self._calculate_quality(len(mentioned_attractions), keyword_matches),
            'mentioned_attractions': mentioned_attractions,
            'cited_files': list(cited_files),
            'response_time': result.get('response_time', 0)
        }
        
        return analysis
    
    def _calculate_quality(self, attractions_found: int, keyword_matches: int) -> str:
        """Calculate overall quality rating."""
        attraction_score = attractions_found / 13 * 100
        keyword_score = keyword_matches / 17 * 100  # 17 total keywords
        
        combined_score = (attraction_score * 0.7) + (keyword_score * 0.3)
        
        if combined_score >= 70:
            return 'high'
        elif combined_score >= 50:
            return 'medium'
        else:
            return 'low'
    
    def export_results(self, results: Dict[str, Any], filename: str = "realistic_mbti_search_results.json"):
        """Export test results to JSON."""
        
        # Prepare export data
        export_data = {
            'test_timestamp': __import__('datetime').datetime.now().isoformat(),
            'test_type': 'realistic_mbti_search',
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
                    'keyword_density': strategy_result['analysis']['keyword_density'],
                    'response_time': strategy_result['analysis']['response_time'],
                    'quality': strategy_result['analysis']['response_quality'],
                    'attractions_found': strategy_result['analysis']['mentioned_attractions'],
                    'files_cited': strategy_result['analysis']['cited_files'],
                    'infj_keyword_matches': strategy_result['analysis']['infj_keyword_matches']
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
    
    print("🎯 Realistic MBTI-Based Search Strategy Testing")
    print("=" * 60)
    print("Testing strategies that work without knowing attraction names beforehand")
    print("Focus: Real-world user scenarios for INFJ personality type discovery")
    
    # Initialize tester
    tester = RealisticMBTISearchTester()
    
    # Test realistic strategies
    results = tester.test_realistic_strategies()
    
    # Export results
    tester.export_results(results)
    
    # Find best realistic strategy
    best_strategy = None
    best_score = 0
    
    print(f"\n🎉 Realistic Strategy Comparison:")
    print("=" * 50)
    
    for strategy_name, strategy_result in results.items():
        if 'analysis' in strategy_result:
            analysis = strategy_result['analysis']
            completeness = analysis['completeness_rate']
            keyword_density = analysis['keyword_density']
            
            # Combined score: 70% completeness + 30% keyword relevance
            combined_score = (completeness * 0.7) + (keyword_density * 0.3)
            
            print(f"🎯 {strategy_name}:")
            print(f"   Attractions: {analysis['attractions_mentioned']}/13 ({completeness:.1f}%)")
            print(f"   INFJ Keywords: {analysis['infj_keyword_matches']}/17 ({keyword_density:.1f}%)")
            print(f"   Combined Score: {combined_score:.1f}")
            print(f"   Quality: {analysis['response_quality']}")
            print(f"   Time: {analysis['response_time']:.2f}s")
            
            if combined_score > best_score:
                best_score = combined_score
                best_strategy = strategy_name
        else:
            print(f"❌ {strategy_name}: Failed")
    
    if best_strategy:
        print(f"\n🏆 Best Realistic Strategy: {best_strategy}")
        print(f"   Combined Score: {best_score:.1f}/100")
        print(f"   This strategy should be used for production MBTI-based searches")
    
    print(f"\n📋 Test completed! Check results in data/realistic_mbti_search_results.json")

if __name__ == "__main__":
    main()