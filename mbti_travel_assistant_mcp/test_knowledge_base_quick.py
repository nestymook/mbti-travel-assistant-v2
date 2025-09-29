#!/usr/bin/env python3
"""
Quick Knowledge Base Test Script
Provides fast validation of the OpenSearch Knowledge Base functionality.
"""

import boto3
import json
import time
import sys
from typing import Dict, List, Any

class QuickKnowledgeBaseTester:
    def __init__(self):
        self.knowledge_base_id = "1FJ1VHU5OW"
        self.region = "us-east-1"
        self.client = boto3.client('bedrock-agent-runtime', region_name=self.region)
    
    def test_connectivity(self) -> bool:
        """Test basic Knowledge Base connectivity."""
        print("🔍 Testing Knowledge Base connectivity...")
        
        try:
            response = self.client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': 'test connectivity'},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {'numberOfResults': 1}
                }
            )
            print("✅ Knowledge Base is accessible")
            return True
        except Exception as e:
            print(f"❌ Knowledge Base connection failed: {str(e)}")
            return False
    
    def test_mbti_queries(self) -> Dict[str, Any]:
        """Test MBTI-specific queries."""
        print("\n🧠 Testing MBTI personality type queries...")
        
        test_queries = {
            'INFJ': 'INFJ quiet contemplative places Hong Kong',
            'ENTJ': 'ENTJ business leadership venues Central District',
            'ISFP': 'ISFP artistic creative galleries museums',
            'INTJ': 'INTJ strategic analytical intellectual spaces'
        }
        
        results = {}
        
        for mbti_type, query in test_queries.items():
            print(f"  Testing {mbti_type}...")
            
            start_time = time.time()
            
            try:
                response = self.client.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {'numberOfResults': 10}
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Count MBTI-matching results
                total_results = len(response['retrievalResults'])
                matching_results = sum(
                    1 for result in response['retrievalResults']
                    if result['location']['s3Location']['uri'].split('/')[-1].startswith(f'{mbti_type}_')
                )
                
                accuracy = (matching_results / total_results * 100) if total_results > 0 else 0
                avg_score = sum(r['score'] for r in response['retrievalResults']) / total_results if total_results > 0 else 0
                
                results[mbti_type] = {
                    'total_results': total_results,
                    'matching_results': matching_results,
                    'accuracy': accuracy,
                    'avg_score': avg_score,
                    'response_time': response_time,
                    'status': 'success'
                }
                
                print(f"    ✅ {total_results} results, {matching_results} matching ({accuracy:.1f}%), {response_time:.2f}s")
                
            except Exception as e:
                results[mbti_type] = {
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    ❌ Failed: {str(e)}")
        
        return results
    
    def test_geographic_queries(self) -> Dict[str, Any]:
        """Test geographic filtering."""
        print("\n🗺️  Testing geographic queries...")
        
        geo_queries = {
            'Central District': 'Central District business venues Hong Kong',
            'Tsim Sha Tsui': 'Tsim Sha Tsui museums cultural attractions',
            'Hong Kong Island': 'Hong Kong Island tourist attractions',
            'Kowloon': 'Kowloon area attractions Hong Kong'
        }
        
        results = {}
        
        for location, query in geo_queries.items():
            print(f"  Testing {location}...")
            
            try:
                response = self.client.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {'numberOfResults': 10}
                    }
                )
                
                total_results = len(response['retrievalResults'])
                avg_score = sum(r['score'] for r in response['retrievalResults']) / total_results if total_results > 0 else 0
                
                results[location] = {
                    'total_results': total_results,
                    'avg_score': avg_score,
                    'top_results': [
                        {
                            'filename': result['location']['s3Location']['uri'].split('/')[-1],
                            'score': result['score']
                        }
                        for result in response['retrievalResults'][:3]
                    ]
                }
                
                print(f"    ✅ {total_results} results, avg score: {avg_score:.4f}")
                
            except Exception as e:
                results[location] = {'error': str(e)}
                print(f"    ❌ Failed: {str(e)}")
        
        return results
    
    def test_performance(self) -> Dict[str, float]:
        """Test Knowledge Base performance."""
        print("\n⚡ Testing performance...")
        
        test_queries = [
            "museums Hong Kong cultural attractions",
            "temples spiritual places Hong Kong",
            "business districts financial centers",
            "art galleries creative spaces",
            "peaceful quiet contemplative venues"
        ]
        
        response_times = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"  Query {i}/{len(test_queries)}...")
            
            start_time = time.time()
            
            try:
                response = self.client.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {'numberOfResults': 5}
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                print(f"    ✅ {response_time:.2f}s ({len(response['retrievalResults'])} results)")
                
            except Exception as e:
                print(f"    ❌ Failed: {str(e)}")
        
        if response_times:
            performance_stats = {
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'total_queries': len(response_times)
            }
            
            print(f"  📊 Average: {performance_stats['avg_response_time']:.2f}s")
            print(f"  📊 Range: {performance_stats['min_response_time']:.2f}s - {performance_stats['max_response_time']:.2f}s")
            
            return performance_stats
        else:
            return {'error': 'No successful queries'}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("🚀 QUICK KNOWLEDGE BASE TEST")
        print("=" * 50)
        
        start_time = time.time()
        
        # Test connectivity
        connectivity_ok = self.test_connectivity()
        
        if not connectivity_ok:
            return {
                'status': 'failed',
                'error': 'Knowledge Base connectivity failed',
                'timestamp': time.time()
            }
        
        # Run all tests
        mbti_results = self.test_mbti_queries()
        geo_results = self.test_geographic_queries()
        performance_results = self.test_performance()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Compile results
        results = {
            'status': 'completed',
            'timestamp': time.time(),
            'total_execution_time': total_time,
            'knowledge_base_id': self.knowledge_base_id,
            'tests': {
                'connectivity': {'status': 'passed'},
                'mbti_queries': mbti_results,
                'geographic_queries': geo_results,
                'performance': performance_results
            }
        }
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"🔗 Knowledge Base ID: {self.knowledge_base_id}")
        
        # MBTI test summary
        mbti_success = sum(1 for r in mbti_results.values() if r.get('status') == 'success')
        print(f"🧠 MBTI tests: {mbti_success}/{len(mbti_results)} passed")
        
        # Geographic test summary
        geo_success = sum(1 for r in geo_results.values() if 'error' not in r)
        print(f"🗺️  Geographic tests: {geo_success}/{len(geo_results)} passed")
        
        # Performance summary
        if 'avg_response_time' in performance_results:
            print(f"⚡ Average response time: {performance_results['avg_response_time']:.2f}s")
        
        # Overall status
        overall_success = connectivity_ok and mbti_success > 0 and geo_success > 0
        status_emoji = "✅" if overall_success else "❌"
        print(f"\n{status_emoji} Overall status: {'PASSED' if overall_success else 'FAILED'}")
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"quick_kb_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function to run quick Knowledge Base test."""
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = 'all'
    
    tester = QuickKnowledgeBaseTester()
    
    if test_type == 'connectivity':
        tester.test_connectivity()
    elif test_type == 'mbti':
        results = tester.test_mbti_queries()
        print(f"\nMBTI test completed. Results: {json.dumps(results, indent=2)}")
    elif test_type == 'geographic':
        results = tester.test_geographic_queries()
        print(f"\nGeographic test completed. Results: {json.dumps(results, indent=2)}")
    elif test_type == 'performance':
        results = tester.test_performance()
        print(f"\nPerformance test completed. Results: {json.dumps(results, indent=2)}")
    else:
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        tester.save_results(results)

if __name__ == "__main__":
    main()