#!/usr/bin/env python3
"""
Single MBTI Type Test
Tests a specific MBTI personality type with comprehensive discovery and filtering.
"""

import boto3
import json
import time
import os
import sys
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
from mbti_prompt_loader import MBTIPromptLoader

class SingleMBTITester:
    def __init__(self, mbti_type: str = "ENTJ"):
        self.knowledge_base_id = "1FJ1VHU5OW"
        self.region = "us-east-1"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'mbti_prompts')
        self.prompt_loader = MBTIPromptLoader(prompts_dir=prompts_dir)
        self.discovered_documents = {}
        self.mbti_type = mbti_type
    
    def search_with_mbti_prompts(self, use_optimized: bool = True) -> List[Dict[str, Any]]:
        """Search using MBTI-specific prompts from the prompt files."""
        
        print(f"🔍 SEARCHING WITH {self.mbti_type} PROMPTS")
        print("=" * 60)
        
        # Get queries for the personality type
        if use_optimized:
            queries = self.prompt_loader.get_optimized_queries(self.mbti_type)
        else:
            queries = self.prompt_loader.get_basic_queries(self.mbti_type)
        
        personality_info = self.prompt_loader.get_personality_info(self.mbti_type)
        print(f"Using {len(queries)} optimized queries for {self.mbti_type}")
        print(f"Personality: {personality_info['description']}")
        
        all_results = []
        unique_documents = set()
        
        for i, query in enumerate(queries, 1):
            print(f"   Query {i:2d}/{len(queries)}: '{query}'")
            
            try:
                response = self.bedrock_runtime.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': 30
                        }
                    }
                )
                
                results = response.get('retrievalResults', [])
                new_documents = 0
                
                for result in results:
                    s3_uri = result['location']['s3Location']['uri']
                    if s3_uri not in unique_documents:
                        # Only include documents that start with the MBTI type
                        filename = s3_uri.split('/')[-1]
                        if filename.startswith(f'{self.mbti_type}_'):
                            unique_documents.add(s3_uri)
                            all_results.append(result)
                            new_documents += 1
                
                print(f"      📊 Found {len(results)} results | New {self.mbti_type}: {new_documents} | Total: {len(all_results)}")
                
            except Exception as e:
                print(f"      ❌ Error with query: {str(e)}")
        
        print(f"✅ Discovery complete: Found {len(all_results)} unique {self.mbti_type} documents")
        return all_results
    
    def extract_structured_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from a knowledge base result."""
        
        s3_uri = result['location']['s3Location']['uri']
        filename = s3_uri.split('/')[-1]
        content = result['content']['text']
        score = result['score']
        
        # Initialize data structure
        data = {
            'name': '',
            'mbti_type': self.mbti_type,
            'description': '',
            'address': '',
            'district': '',
            'area': '',
            'operating_hours': '',
            'contact': '',
            's3_uri': s3_uri,
            'filename': filename,
            'score': score
        }
        
        # Extract name from filename (remove MBTI prefix and .md extension)
        if filename.startswith(f'{self.mbti_type}_') and filename.endswith('.md'):
            name_part = filename[len(f'{self.mbti_type}_'):-3]  # Remove prefix and .md
            data['name'] = name_part.replace('_', ' ').replace('-', ' ')
        
        # Parse content for structured information
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('**Address:**'):
                data['address'] = line.replace('**Address:**', '').strip()
            elif line.startswith('**Hours:**'):
                data['operating_hours'] = line.replace('**Hours:**', '').strip()
            elif line.startswith('**Contact:**'):
                data['contact'] = line.replace('**Contact:**', '').strip()
            elif not data['description'] and len(line) > 20 and not line.startswith('**'):
                data['description'] = line
        
        # Extract area and district from S3 URI path
        path_parts = s3_uri.split('/')
        if len(path_parts) >= 4:
            # Expected format: s3://bucket/area/district/filename
            if len(path_parts) >= 5:
                data['area'] = path_parts[3].replace('_', ' ').title()
                data['district'] = path_parts[4].replace('_', ' ').title()
            else:
                # Fallback: try to extract from path
                if 'Hong_Kong_Island' in s3_uri:
                    data['area'] = 'Hong Kong Island'
                elif 'Kowloon' in s3_uri:
                    data['area'] = 'Kowloon'
                elif 'New_Territories' in s3_uri:
                    data['area'] = 'New Territories'
                
                # Extract district from remaining path
                if len(path_parts) >= 4:
                    data['district'] = path_parts[3].replace('_', ' ').title()
        
        return data
    
    def filter_by_test_criteria(self, records: List[Dict[str, Any]], test_case: str) -> List[Dict[str, Any]]:
        """Filter records according to test case criteria."""
        
        filtered_records = []
        
        for record in records:
            # All test cases require filename to start with current MBTI type
            if not record['filename'].startswith(f'{self.mbti_type}_'):
                continue
            
            # Apply specific test case filters
            if test_case == "test_case_1":
                # Test Case 1: All Areas, All Districts, MBTI files
                filtered_records.append(record)
                
            elif test_case == "test_case_2":
                # Test Case 2: All Areas, Central Districts, MBTI files
                if 'central' in record['district'].lower():
                    filtered_records.append(record)
                    
            elif test_case == "test_case_3":
                # Test Case 3: Hong Kong Island Area, All Districts, MBTI files
                if 'hong kong island' in record['area'].lower():
                    filtered_records.append(record)
        
        return filtered_records
    
    def display_test_results(self, records: List[Dict[str, Any]], title: str):
        """Display test results in organized format."""
        
        print(f"\n🎯 {title}")
        print("=" * 80)
        
        print(f"✅ Found {len(records)} {self.mbti_type} attractions matching criteria:")
        
        # Group by area
        area_groups = {}
        for record in records:
            area = record['area']
            if area not in area_groups:
                area_groups[area] = {}
            
            district = record['district']
            if district not in area_groups[area]:
                area_groups[area][district] = []
            
            area_groups[area][district].append(record)
        
        # Display organized results
        for area, districts in sorted(area_groups.items()):
            print(f"\n🏝️  {area} ({sum(len(attractions) for attractions in districts.values())} attractions)")
            print("-" * 60)
            
            for district, attractions in sorted(districts.items()):
                print(f"  📍 {district}:")
                for j, attraction in enumerate(attractions, 1):
                    print(f"    {j}. 🎯 {attraction['name']}")
                    print(f"       📄 File: {attraction['filename']}")
                    print(f"       📊 Score: {attraction['score']:.4f}")
                    if attraction['description']:
                        print(f"       📝 Description: {attraction['description']}")
                    if attraction['address']:
                        print(f"       📍 Address: {attraction['address']}")
                    if attraction['operating_hours']:
                        print(f"       ⏰ Hours: {attraction['operating_hours']}")
                    if attraction['contact']:
                        print(f"       📞 Contact: {attraction['contact']}")
    
    def run_test(self):
        """Run comprehensive test for the specified MBTI type."""
        
        print("🚀 SINGLE MBTI TYPE TEST")
        print(f"Testing {self.mbti_type} personality type with comprehensive discovery")
        print("=" * 80)
        
        start_time = time.time()
        
        # Step 1: Use MBTI prompts to discover documents for this type
        mbti_results = self.search_with_mbti_prompts(use_optimized=True)
        
        # Step 2: Extract structured data
        print(f"\n📋 EXTRACTING STRUCTURED DATA FOR {self.mbti_type}...")
        structured_records = []
        for result in mbti_results:
            try:
                record = self.extract_structured_data(result)
                structured_records.append(record)
            except Exception as e:
                print(f"⚠️  Error extracting record: {str(e)}")
        
        print(f"✅ Extracted {len(structured_records)} structured {self.mbti_type} records")
        
        # Step 3: Apply test case filters and display results
        
        # Test Case 1: All Areas, All Districts, MBTI files
        test1_records = self.filter_by_test_criteria(structured_records, "test_case_1")
        self.display_test_results(test1_records, f"TEST CASE 1: All Areas, All Districts, Files starting with {self.mbti_type}")
        
        # Test Case 2: All Areas, Central Districts, MBTI files
        test2_records = self.filter_by_test_criteria(structured_records, "test_case_2")
        self.display_test_results(test2_records, f"TEST CASE 2: All Areas, Central Districts, Files starting with {self.mbti_type}")
        
        # Test Case 3: Hong Kong Island Area, All Districts, MBTI files
        test3_records = self.filter_by_test_criteria(structured_records, "test_case_3")
        self.display_test_results(test3_records, f"TEST CASE 3: Hong Kong Island Area, All Districts, Files starting with {self.mbti_type}")
        
        # Summary
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total Execution Time: {total_time} seconds")
        print(f"🔍 {self.mbti_type} Documents Discovered: {len(structured_records)}")
        print(f"📋 Test Case Results:")
        print(f"   Test Case 1 (All Areas, All Districts): {len(test1_records)} records")
        print(f"   Test Case 2 (All Areas, Central Districts): {len(test2_records)} records")
        print(f"   Test Case 3 (Hong Kong Island, All Districts): {len(test3_records)} records")
        
        # Show prompt effectiveness
        mbti_info = self.prompt_loader.get_personality_info(self.mbti_type)
        print(f"\n🎯 {self.mbti_type} Prompt Effectiveness:")
        print(f"   Personality: {mbti_info['description']}")
        print(f"   Core Traits: {', '.join(mbti_info['core_traits'])}")
        print(f"   Expected Coverage: {mbti_info['optimization_notes']['expected_coverage']}")
        print(f"   Actual Documents Found: {len(structured_records)}")
        
        # Save results
        self.save_test_results(structured_records, test1_records, test2_records, test3_records, total_time)
        
        return {
            'mbti_type': self.mbti_type,
            'total_documents': len(structured_records),
            'test_case_1': len(test1_records),
            'test_case_2': len(test2_records),
            'test_case_3': len(test3_records),
            'execution_time': total_time,
            'all_records': structured_records
        }
    
    def save_test_results(self, all_records, test1_records, test2_records, test3_records, total_time):
        """Save test results to JSON file."""
        
        def record_to_dict(record):
            return {
                'name': record['name'],
                'mbti_type': record['mbti_type'],
                'description': record['description'],
                'address': record['address'],
                'district': record['district'],
                'area': record['area'],
                'operating_hours': record['operating_hours'],
                'contact': record['contact'],
                's3_uri': record['s3_uri'],
                'filename': record['filename'],
                'score': record['score']
            }
        
        filename = f"{self.mbti_type.lower()}_test_results_{int(time.time())}.json"
        
        output_data = {
            'test_suite': f'Single MBTI Type Test - {self.mbti_type}',
            'knowledge_base_id': self.knowledge_base_id,
            'mbti_type_tested': self.mbti_type,
            'total_execution_time': total_time,
            'total_documents_discovered': len(all_records),
            'test_cases': {
                'test_case_1': {
                    'description': f'All Areas, All Districts, Files starting with {self.mbti_type}',
                    'count': len(test1_records),
                    'records': [record_to_dict(r) for r in test1_records]
                },
                'test_case_2': {
                    'description': f'All Areas, Central Districts, Files starting with {self.mbti_type}',
                    'count': len(test2_records),
                    'records': [record_to_dict(r) for r in test2_records]
                },
                'test_case_3': {
                    'description': f'Hong Kong Island Area, All Districts, Files starting with {self.mbti_type}',
                    'count': len(test3_records),
                    'records': [record_to_dict(r) for r in test3_records]
                }
            },
            'prompt_source': f'../mbti_prompts/{self.mbti_type}.json',
            'all_records': [record_to_dict(r) for r in all_records]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {filename}")

def main():
    # Get MBTI type from command line argument or default to ENTJ
    mbti_type = sys.argv[1] if len(sys.argv) > 1 else "ENTJ"
    
    tester = SingleMBTITester(mbti_type=mbti_type)
    results = tester.run_test()
    
    print(f"\n🎉 {mbti_type} TEST COMPLETE!")
    print(f"Successfully discovered and filtered {results['total_documents']} {mbti_type} attractions")
    print(f"Execution time: {results['execution_time']} seconds")

if __name__ == "__main__":
    main()