#!/usr/bin/env python3
"""
Test Foundation Model Integration with INFJ Knowledge Base

This script tests using a foundation model to interact with the knowledge base
and retrieve all 13 INFJ tourist spots through natural language conversation.
"""

import boto3
import json
import time
from typing import Dict, List, Any

class FoundationModelKBTester:
    """Test foundation model integration with knowledge base."""
    
    def __init__(self, kb_id: str = "RCWW86CLM9", region: str = "us-east-1"):
        self.kb_id = kb_id
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Available foundation models for testing - Focus on Nova Pro
        self.models = {
            "nova-pro": "amazon.nova-pro-v1:0",
            "nova-lite": "amazon.nova-lite-v1:0"
        }
        
        # Expected INFJ attractions for validation
        self.expected_infj_attractions = [
            "Broadway Cinematheque", "Central Market", "Hong Kong Cultural Centre",
            "Hong Kong House of Stories", "Hong Kong Museum of Art", 
            "Hong Kong Palace Museum", "M+", "Man Mo Temple",
            "PMQ (Police Married Quarters)", "Pacific Place Rooftop Garden",
            "Po Lin Monastery", "SoHo & Central Art Galleries", "Tai Kwun"
        ]
    
    def test_retrieve_and_generate(self, model_name: str = "nova-pro") -> Dict[str, Any]:
        """Test retrieve-and-generate with foundation model."""
        
        model_arn = self.models.get(model_name)
        if not model_arn:
            print(f"❌ Unknown model: {model_name}")
            return {}
        
        print(f"🤖 Testing Foundation Model: {model_name}")
        print(f"📋 Model ARN: {model_arn}")
        print("=" * 60)
        
        # Comprehensive query to get all INFJ attractions
        query = """Please provide a complete list of ALL Hong Kong tourist attractions that are specifically recommended for INFJ personality types. 

For each attraction, include:
1. Attraction name
2. Why it's suitable for INFJ personality
3. Full address
4. District and area
5. Operating hours
6. Contact information

I need the complete list - there should be around 13 attractions total. Please be comprehensive and don't miss any INFJ-suitable attractions."""
        
        try:
            print(f"🔍 Query: {query[:100]}...")
            print(f"⏳ Calling retrieve-and-generate...")
            
            start_time = time.time()
            
            response = self.bedrock_runtime.retrieve_and_generate(
                input={
                    'text': query
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 25  # High limit to get all results
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
                'model': model_name,
                'model_arn': model_arn,
                'response_time': response_time,
                'generated_text': generated_text,
                'citations': citations,
                'query': query
            }
            
        except Exception as e:
            print(f"❌ Error with {model_name}: {e}")
            return {'error': str(e), 'model': model_name}
    
    def analyze_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the foundation model response for completeness."""
        
        if 'error' in result:
            return {'analysis': 'error', 'details': result['error']}
        
        generated_text = result['generated_text']
        citations = result['citations']
        
        print(f"\n📝 Foundation Model Response Analysis")
        print("=" * 50)
        
        # Count mentioned attractions
        mentioned_attractions = []
        for expected in self.expected_infj_attractions:
            if expected.lower() in generated_text.lower():
                mentioned_attractions.append(expected)
        
        print(f"🎯 Attractions mentioned: {len(mentioned_attractions)}/13")
        
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
        
        print(f"📚 INFJ files cited: {len(cited_files)}/13")
        
        # Check for specific INFJ characteristics
        infj_keywords = [
            'introverted', 'intuitive', 'feeling', 'judging',
            'empathy', 'vision', 'meaningful', 'deep', 'reflection',
            'spiritual', 'artistic', 'cultural', 'contemplation'
        ]
        
        keyword_matches = sum(1 for keyword in infj_keywords if keyword in generated_text.lower())
        
        print(f"🧠 INFJ keywords found: {keyword_matches}/{len(infj_keywords)}")
        
        # Display the response
        print(f"\n🤖 Foundation Model Response:")
        print("-" * 40)
        print(generated_text)
        print("-" * 40)
        
        # Display citations
        print(f"\n📚 Citations ({len(citations)} total):")
        for i, citation in enumerate(citations, 1):
            if 'retrievedReferences' in citation:
                print(f"   Citation {i}:")
                for ref in citation['retrievedReferences']:
                    if 'location' in ref and 's3Location' in ref['location']:
                        uri = ref['location']['s3Location']['uri']
                        filename = uri.split('/')[-1]
                        print(f"     - {filename}")
        
        analysis = {
            'attractions_mentioned': len(mentioned_attractions),
            'expected_attractions': len(self.expected_infj_attractions),
            'completeness_rate': len(mentioned_attractions) / len(self.expected_infj_attractions) * 100,
            'files_cited': len(cited_files),
            'expected_files': 13,
            'citation_rate': len(cited_files) / 13 * 100,
            'infj_keyword_matches': keyword_matches,
            'response_quality': 'high' if len(mentioned_attractions) >= 10 else 'medium' if len(mentioned_attractions) >= 7 else 'low',
            'mentioned_attractions': mentioned_attractions,
            'cited_files': list(cited_files),
            'response_time': result.get('response_time', 0)
        }
        
        return analysis
    
    def test_improved_prompts(self) -> Dict[str, Any]:
        """Test different prompt strategies to improve retrieval completeness."""
        
        print("🧪 Testing Improved Prompt Strategies for Complete Retrieval")
        print("=" * 70)
        
        # Strategy 1: Explicit mention of missing attractions
        prompt_strategies = {
            "explicit_list": """I need information about ALL 13 Hong Kong tourist attractions specifically recommended for INFJ personality types. Please search for and provide details about each of these attractions:

1. Broadway Cinematheque
2. Central Market  
3. Hong Kong Cultural Centre
4. Hong Kong House of Stories
5. Hong Kong Museum of Art
6. Hong Kong Palace Museum
7. M+
8. Man Mo Temple
9. PMQ (Police Married Quarters)
10. Pacific Place Rooftop Garden
11. Po Lin Monastery
12. SoHo & Central Art Galleries
13. Tai Kwun

For each attraction found, include:
- Why it's suitable for INFJ personality traits (introverted, intuitive, feeling, judging)
- Full address and district
- Operating hours and contact information
- Specific INFJ-relevant features (contemplative spaces, artistic elements, cultural depth, etc.)

Please search thoroughly and provide information for ALL 13 attractions.""",

            "infj_keywords": """Find ALL Hong Kong tourist attractions perfect for INFJ personalities who value:
- Deep contemplation and reflection
- Artistic and cultural experiences  
- Spiritual and meaningful connections
- Quiet, introspective environments
- Creative inspiration and vision
- Empathetic and emotional resonance
- Historical and cultural depth
- Authentic, non-commercial experiences

Search for attractions including museums, art galleries, temples, cultural centers, creative spaces, rooftop gardens, monasteries, heritage sites, and cinematheques that match INFJ traits.

I need the complete list of approximately 13 INFJ-suitable attractions with full details for each.""",

            "comprehensive_search": """Perform an exhaustive search for Hong Kong tourist attractions specifically curated for INFJ personality types. 

INFJ characteristics to match:
- Introverted: Prefer quieter, less crowded spaces
- Intuitive: Drawn to symbolic, artistic, and visionary experiences  
- Feeling: Seek emotional depth and meaningful connections
- Judging: Appreciate structured, purposeful visits

Search categories:
- Art museums and galleries (M+, Hong Kong Museum of Art, etc.)
- Cultural heritage sites (Tai Kwun, Man Mo Temple, etc.)
- Creative districts (SoHo galleries, PMQ, etc.)
- Spiritual locations (Po Lin Monastery, temples)
- Contemplative spaces (rooftop gardens, quiet cultural centers)
- Independent cinemas and cultural venues
- Interactive cultural experiences

Provide ALL attractions found (target: 13 total) with complete information including addresses, hours, and INFJ relevance.""",

            "detailed_infj_focus": """Search for Hong Kong attractions perfect for INFJ personalities who are:

INTROVERTED - seeking peaceful, contemplative environments away from crowds
INTUITIVE - drawn to symbolic meaning, artistic vision, and creative inspiration  
FEELING - valuing emotional depth, empathy, and meaningful human connections
JUDGING - preferring structured experiences with clear purpose and significance

Find attractions that offer:
- Quiet reflection spaces (temples, monasteries, rooftop gardens)
- Deep cultural meaning (heritage sites, traditional architecture)
- Artistic inspiration (museums, galleries, creative districts)
- Spiritual connection (religious sites, meditation spaces)
- Authentic experiences (local culture, traditional crafts)
- Educational depth (history, philosophy, cultural learning)

Include museums, art galleries, cultural centers, temples, monasteries, heritage sites, creative quarters, independent cinemas, and contemplative gardens. Provide complete details for each attraction found."""
        }
        
        results = {}
        
        for strategy_name, query in prompt_strategies.items():
            print(f"\n🎯 Testing Strategy: {strategy_name}")
            print("-" * 50)
            
            result = self.test_retrieve_and_generate_with_query(query, strategy_name)
            
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
            else:
                results[strategy_name] = result
                print(f"❌ {strategy_name} failed: {result['error']}")
        
        return results
    
    def test_sequential_queries(self) -> Dict[str, Any]:
        """Test multiple sequential queries to find missing attractions."""
        
        print("🔍 Testing Sequential Query Strategy")
        print("=" * 50)
        
        # Found attractions from previous tests
        found_attractions = {
            "Central Market", "Hong Kong Cultural Centre", "Hong Kong Museum of Art",
            "Hong Kong Palace Museum", "M+", "SoHo & Central Art Galleries", "Tai Kwun"
        }
        
        # Missing attractions to search for specifically
        missing_attractions = [
            "Broadway Cinematheque", "Hong Kong House of Stories", "Man Mo Temple",
            "PMQ (Police Married Quarters)", "Pacific Place Rooftop Garden", "Po Lin Monastery"
        ]
        
        # Targeted queries for missing attractions
        targeted_queries = [
            "Find Hong Kong independent cinemas and cultural film venues suitable for INFJ personalities, especially Broadway Cinematheque and similar contemplative movie experiences.",
            
            "Search for Hong Kong storytelling venues, narrative museums, and cultural houses that offer deep emotional experiences for INFJ personalities, including Hong Kong House of Stories.",
            
            "Find traditional Hong Kong temples and spiritual sites perfect for INFJ contemplation and reflection, especially Man Mo Temple and similar sacred spaces.",
            
            "Search for Hong Kong creative quarters, artist studios, and cultural heritage buildings like PMQ (Police Married Quarters) that inspire INFJ creativity.",
            
            "Find quiet rooftop gardens, contemplative outdoor spaces, and peaceful retreats in Hong Kong suitable for INFJ reflection, including Pacific Place Rooftop Garden.",
            
            "Search for Hong Kong monasteries, Buddhist temples, and spiritual retreat centers perfect for INFJ meditation and inner peace, especially Po Lin Monastery."
        ]
        
        all_results = {}
        combined_attractions = set(found_attractions)
        
        for i, query in enumerate(targeted_queries, 1):
            print(f"\n🎯 Sequential Query {i}/6")
            print(f"Target: {missing_attractions[i-1] if i <= len(missing_attractions) else 'General search'}")
            
            result = self.test_retrieve_and_generate_with_query(query, f"sequential_{i}")
            
            if 'error' not in result:
                analysis = self.analyze_response(result)
                all_results[f"sequential_{i}"] = {
                    'result': result,
                    'analysis': analysis
                }
                
                # Track newly found attractions
                new_attractions = set(analysis['mentioned_attractions']) - combined_attractions
                combined_attractions.update(analysis['mentioned_attractions'])
                
                print(f"   New attractions found: {len(new_attractions)}")
                if new_attractions:
                    print(f"   → {', '.join(new_attractions)}")
            else:
                print(f"   ❌ Query failed: {result['error']}")
        
        # Summary of sequential approach
        total_found = len(combined_attractions)
        print(f"\n📊 Sequential Query Summary:")
        print(f"   Total unique attractions found: {total_found}/13 ({total_found/13*100:.1f}%)")
        print(f"   Combined attractions: {', '.join(sorted(combined_attractions))}")
        
        return {
            'sequential_results': all_results,
            'combined_attractions': list(combined_attractions),
            'total_found': total_found,
            'completeness_rate': total_found/13*100
        }
    
    def test_retrieve_and_generate_with_query(self, query: str, strategy_name: str) -> Dict[str, Any]:
        """Test retrieve-and-generate with a specific query."""
        
        model_name = "nova-pro"
        model_arn = self.models.get(model_name)
        
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
                        'modelArn': model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': 30  # Maximum allowed limit
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
                'model': model_name,
                'model_arn': model_arn,
                'response_time': response_time,
                'generated_text': generated_text,
                'citations': citations,
                'query': query,
                'strategy': strategy_name
            }
            
        except Exception as e:
            print(f"❌ Error with {strategy_name}: {e}")
            return {'error': str(e), 'model': model_name, 'strategy': strategy_name}

    def test_nova_pro_model(self) -> Dict[str, Any]:
        """Test Amazon Nova Pro foundation model."""
        
        print("🧪 Testing Amazon Nova Pro Foundation Model")
        print("=" * 60)
        
        results = {}
        
        # Test only Nova Pro models
        test_models = ["nova-pro"]
        
        for model_name in test_models:
            print(f"\n🤖 Testing {model_name}...")
            
            # Get response
            result = self.test_retrieve_and_generate(model_name)
            
            if 'error' not in result:
                # Analyze response
                analysis = self.analyze_response(result)
                results[model_name] = {
                    'result': result,
                    'analysis': analysis
                }
                
                print(f"\n📊 {model_name} Results:")
                print(f"   Attractions found: {analysis['attractions_mentioned']}/13 ({analysis['completeness_rate']:.1f}%)")
                print(f"   Files cited: {analysis['files_cited']}/13 ({analysis['citation_rate']:.1f}%)")
                print(f"   Response time: {analysis['response_time']:.2f}s")
                print(f"   Quality: {analysis['response_quality']}")
            else:
                results[model_name] = result
                print(f"❌ {model_name} failed: {result['error']}")
        
        return results
    
    def export_results(self, results: Dict[str, Any], filename: str = "foundation_model_test_results.json"):
        """Export test results to JSON."""
        
        # Prepare export data
        export_data = {
            'test_timestamp': __import__('datetime').datetime.now().isoformat(),
            'knowledge_base_id': self.kb_id,
            'expected_infj_attractions': self.expected_infj_attractions,
            'models_tested': list(results.keys()),
            'results': {}
        }
        
        for model_name, model_result in results.items():
            if 'analysis' in model_result:
                export_data['results'][model_name] = {
                    'completeness_rate': model_result['analysis']['completeness_rate'],
                    'citation_rate': model_result['analysis']['citation_rate'],
                    'response_time': model_result['analysis']['response_time'],
                    'quality': model_result['analysis']['response_quality'],
                    'attractions_found': model_result['analysis']['mentioned_attractions'],
                    'files_cited': model_result['analysis']['cited_files']
                }
            else:
                export_data['results'][model_name] = {'error': model_result.get('error', 'Unknown error')}
        
        # Save to file
        filepath = f"data/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results exported to: {filepath}")

def main():
    """Main test execution."""
    
    print("🎯 Foundation Model Knowledge Base Integration Test")
    print("=" * 60)
    print("Testing Amazon Nova Pro's ability to retrieve all 13 INFJ attractions")
    
    # Initialize tester
    tester = FoundationModelKBTester()
    
    # Test original prompt
    print("🔄 Testing Original Prompt Strategy")
    original_results = tester.test_nova_pro_model()
    
    # Test improved prompts
    print("\n" + "="*70)
    print("🚀 Testing Improved Prompt Strategies")
    improved_results = tester.test_improved_prompts()
    
    # Test sequential queries
    print("\n" + "="*70)
    print("🎯 Testing Sequential Query Strategy")
    sequential_results = tester.test_sequential_queries()
    
    # Combine results
    all_results = {**original_results, **improved_results}
    if 'sequential_results' in sequential_results:
        all_results.update(sequential_results['sequential_results'])
    
    # Export results
    tester.export_results(all_results, "improved_prompt_test_results.json")
    
    # Summary
    print(f"\n🎉 Prompt Strategy Comparison Summary:")
    print("=" * 50)
    
    best_strategy = None
    best_completeness = 0
    
    for strategy_name, strategy_result in all_results.items():
        if 'analysis' in strategy_result:
            analysis = strategy_result['analysis']
            completeness = analysis['completeness_rate']
            
            print(f"🎯 {strategy_name}:")
            print(f"   Attractions: {analysis['attractions_mentioned']}/13 ({completeness:.1f}%)")
            print(f"   Citations: {analysis['files_cited']}/13 ({analysis['citation_rate']:.1f}%)")
            print(f"   Quality: {analysis['response_quality']}")
            print(f"   Time: {analysis['response_time']:.2f}s")
            
            if completeness > best_completeness:
                best_completeness = completeness
                best_strategy = strategy_name
        else:
            print(f"❌ {strategy_name}: Failed")
    
    if best_strategy:
        print(f"\n🏆 Best Strategy: {best_strategy} ({best_completeness:.1f}% completeness)")
    else:
        print(f"\n⚠️ No strategy achieved better results")
    
    print(f"\n📋 Test completed! Check results in data/")

if __name__ == "__main__":
    main()