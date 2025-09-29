#!/usr/bin/env python3
"""
Knowledge Base Response Analysis Tool
Provides detailed analysis of what the knowledge base returns and explains the results.
"""

import boto3
import json
from typing import Dict, List, Any

class KnowledgeBaseAnalyzer:
    def __init__(self):
        self.knowledge_base_id = "1FJ1VHU5OW"
        self.region = "us-east-1"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
    
    def analyze_single_query(self, query: str, max_results: int = 20):
        """Analyze a single query in detail."""
        print(f"🔍 ANALYZING QUERY: '{query}'")
        print("=" * 80)
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = response.get('retrievalResults', [])
            
            print(f"📊 RESPONSE SUMMARY:")
            print(f"   Total Results Returned: {len(results)}")
            print(f"   Max Results Requested: {max_results}")
            print(f"   Knowledge Base ID: {self.knowledge_base_id}")
            
            # Analyze why we get exactly the number we requested
            self.explain_result_count(len(results), max_results)
            
            # Analyze content types and MBTI matches
            self.analyze_content_types(results)
            
            # Show sample document content
            self.show_sample_documents(results[:3])
            
            # Analyze geographic distribution
            self.analyze_geographic_distribution(results)
            
            # Analyze scoring patterns
            self.analyze_scoring_patterns(results)
            
            return results
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return []
    
    def explain_result_count(self, actual_results: int, requested_results: int):
        """Explain why we get the number of results we do."""
        print(f"\n🤔 WHY DO WE GET {actual_results} RESULTS?")
        
        if actual_results == requested_results:
            print(f"   ✅ We requested {requested_results} results and got exactly {actual_results}")
            print(f"   📝 This means the knowledge base has AT LEAST {actual_results} documents")
            print(f"   🔍 The vector search found enough relevant documents to fill our request")
            print(f"   ⚙️  Bedrock returns up to the 'numberOfResults' limit we specified")
        elif actual_results < requested_results:
            print(f"   📉 We requested {requested_results} but only got {actual_results}")
            print(f"   📝 This means the knowledge base only has {actual_results} documents total")
            print(f"   🔍 OR the vector search couldn't find more relevant documents")
        else:
            print(f"   ⚠️  Unexpected: Got more results than requested!")
    
    def analyze_content_types(self, results: List[Dict]):
        """Analyze what types of content are returned."""
        print(f"\n📋 CONTENT TYPE ANALYSIS:")
        
        mbti_types = {}
        infj_count = 0
        total_docs = len(results)
        
        for result in results:
            content = result.get('content', {}).get('text', '')
            
            # Count INFJ matches
            if 'INFJ' in content:
                infj_count += 1
            
            # Extract MBTI type from content
            if '**Type:** ' in content:
                try:
                    mbti_type = content.split('**Type:** ')[1].split(' ')[0].strip()
                    mbti_types[mbti_type] = mbti_types.get(mbti_type, 0) + 1
                except:
                    pass
        
        print(f"   📊 Total Documents: {total_docs}")
        print(f"   🎯 INFJ Matches: {infj_count} ({infj_count/total_docs*100:.1f}%)")
        
        print(f"\n   🏷️  MBTI Type Distribution:")
        for mbti_type, count in sorted(mbti_types.items()):
            percentage = (count / total_docs) * 100
            print(f"      {mbti_type}: {count} documents ({percentage:.1f}%)")
        
        print(f"\n❓ WHAT ARE 'INFJ MATCHES'?")
        print(f"   📝 INFJ Matches = Documents that contain the text 'INFJ' in their content")
        print(f"   🎯 These are attractions specifically recommended for INFJ personality types")
        print(f"   📊 Out of {total_docs} results, {infj_count} are specifically for INFJ personalities")
        print(f"   🔍 The other {total_docs - infj_count} documents are for other MBTI types but still relevant to the query")
    
    def show_sample_documents(self, results: List[Dict]):
        """Show sample document content to understand what's returned."""
        print(f"\n📄 SAMPLE DOCUMENT CONTENT:")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0)
            s3_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
            
            # Extract attraction name
            attraction_name = "Unknown"
            if '# ' in content:
                attraction_name = content.split('# ')[1].split('\r\n')[0].strip()
            
            # Extract MBTI type
            mbti_type = "Unknown"
            if '**Type:** ' in content:
                try:
                    mbti_type = content.split('**Type:** ')[1].split(' ')[0].strip()
                except:
                    pass
            
            print(f"\n   📄 Document {i}: {attraction_name}")
            print(f"      🎯 MBTI Type: {mbti_type}")
            print(f"      📊 Relevance Score: {score:.4f}")
            print(f"      📍 S3 Location: {s3_uri.split('/')[-1] if s3_uri else 'Unknown'}")
            
            # Show first few lines of content
            content_lines = content.split('\r\n')[:6]
            print(f"      📝 Content Preview:")
            for line in content_lines:
                if line.strip():
                    print(f"         {line[:80]}{'...' if len(line) > 80 else ''}")
    
    def analyze_geographic_distribution(self, results: List[Dict]):
        """Analyze geographic distribution of results."""
        print(f"\n🗺️  GEOGRAPHIC DISTRIBUTION:")
        
        areas = {}
        districts = {}
        
        for result in results:
            s3_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
            
            # Extract area from S3 path
            if 'hong_kong_island' in s3_uri:
                area = 'Hong Kong Island'
            elif 'kowloon' in s3_uri:
                area = 'Kowloon'
            elif 'new_territories' in s3_uri:
                area = 'New Territories'
            elif 'islands' in s3_uri:
                area = 'Islands'
            else:
                area = 'Unknown'
            
            areas[area] = areas.get(area, 0) + 1
            
            # Extract district from S3 path
            path_parts = s3_uri.split('/')
            if len(path_parts) >= 4:
                district = path_parts[3].replace('_', ' ').title()
                districts[district] = districts.get(district, 0) + 1
        
        print(f"   🏝️  Areas Covered:")
        for area, count in sorted(areas.items()):
            percentage = (count / len(results)) * 100
            print(f"      {area}: {count} documents ({percentage:.1f}%)")
        
        print(f"\n   🏘️  Top Districts:")
        sorted_districts = sorted(districts.items(), key=lambda x: x[1], reverse=True)[:10]
        for district, count in sorted_districts:
            percentage = (count / len(results)) * 100
            print(f"      {district}: {count} documents ({percentage:.1f}%)")
    
    def analyze_scoring_patterns(self, results: List[Dict]):
        """Analyze the scoring patterns to understand relevance."""
        print(f"\n📊 SCORING PATTERN ANALYSIS:")
        
        scores = [result.get('score', 0) for result in results]
        
        if scores:
            min_score = min(scores)
            max_score = max(scores)
            avg_score = sum(scores) / len(scores)
            
            print(f"   📈 Score Range: {min_score:.4f} to {max_score:.4f}")
            print(f"   📊 Average Score: {avg_score:.4f}")
            print(f"   📉 Score Drop: {max_score - min_score:.4f}")
            
            # Analyze score distribution
            high_scores = [s for s in scores if s >= 0.6]
            medium_scores = [s for s in scores if 0.4 <= s < 0.6]
            low_scores = [s for s in scores if s < 0.4]
            
            print(f"\n   🎯 Score Distribution:")
            print(f"      High Relevance (≥0.6): {len(high_scores)} documents")
            print(f"      Medium Relevance (0.4-0.6): {len(medium_scores)} documents")
            print(f"      Lower Relevance (<0.4): {len(low_scores)} documents")
            
            print(f"\n❓ WHAT DO SCORES MEAN?")
            print(f"   📝 Scores represent semantic similarity between query and document")
            print(f"   🎯 Higher scores = more relevant to your search query")
            print(f"   🔍 Scores range from 0.0 (no similarity) to 1.0 (perfect match)")
            print(f"   ⚙️  Bedrock uses vector embeddings to calculate these scores")
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis with different queries."""
        print("🚀 KNOWLEDGE BASE RESPONSE ANALYSIS")
        print("=" * 80)
        
        # Test different result limits to show the pattern
        print("\n🧪 TESTING DIFFERENT RESULT LIMITS:")
        test_query = "INFJ personality attractions"
        
        for limit in [5, 10, 20, 50, 100]:
            try:
                response = self.bedrock_runtime.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': test_query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': limit
                        }
                    }
                )
                actual_results = len(response.get('retrievalResults', []))
                print(f"   Requested: {limit:3d} → Got: {actual_results:3d} results")
            except Exception as e:
                print(f"   Requested: {limit:3d} → Error: {str(e)}")
        
        print(f"\n" + "=" * 80)
        
        # Detailed analysis of one query
        self.analyze_single_query("INFJ personality type attractions recommendations", 20)

def main():
    analyzer = KnowledgeBaseAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()