#!/usr/bin/env python3
"""
MBTI Prompts with Filtering Test
Uses the generated MBTI prompt files to search the knowledge base and filter results
according to specific test cases for all MBTI personality types.
"""

import boto3
import json
import time
import os
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
from mbti_prompt_loader import MBTIPromptLoader

class MBTIPromptsFilteredTester:
    def __init__(self):
        self.knowledge_base_id = "1FJ1VHU5OW"
        self.region = "us-east-1"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        # Update prompt loader to use new location
        prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'mbti_prompts')
        self.prompt_loader = MBTIPromptLoader(prompts_dir=prompts_dir)
        self.discovered_documents = {}
        self.current_mbti_type = None  # Track current MBTI type being tested
    
    def get_available_mbti_types(self) -> List[str]:
        """Get all available MBTI types from the prompt files directory."""
        prompt_dir = os.path.join(os.path.dirname(__file__), '..', 'mbti_prompts')
        mbti_types = []
        
        if os.path.exists(prompt_dir):
            for filename in os.listdir(prompt_dir):
                if filename.endswith('.json') and filename != 'README.md':
                    mbti_type = filename.replace('.json', '')
                    mbti_types.append(mbti_type)
        
        return sorted(mbti_types)
    
    def search_with_mbti_prompts(self, mbti_type: str, use_optimized: bool = True) -> List[Dict[str, Any]]:
        """Search using MBTI-specific prompts from the prompt files."""
        
        self.current_mbti_type = mbti_type  # Set current MBTI type
        print(f"🔍 SEARCHING WITH {mbti_type} PROMPTS")
        print("=" * 60)
        
        # Get queries for the personality type
        if use_optimized:
            queries = self.prompt_loader.get_optimized_queries(mbti_type)
            print(f"Using {len(queries)} optimized queries for {mbti_type}")
        else:
            queries = self.prompt_loader.get_all_queries(mbti_type)
            print(f"Using all {len(queries)} queries for {mbti_type}")
        
        # Get personality info
        personality_info = self.prompt_loader.get_personality_info(mbti_type)
        print(f"Personality: {personality_info['description']}")
        
        all_results = []
        seen_uris = set()
        
        for i, query in enumerate(queries, 1):
            try:
                print(f"   Query {i:2d}/{len(queries)}: '{query[:50]}{'...' if len(query) > 50 else ''}'")
                
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
                new_count = 0
                
                for result in results:
                    uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
                    
                    # Check if this is the target MBTI type and we haven't seen it
                    if uri and f'{mbti_type}_' in uri and uri not in seen_uris:
                        seen_uris.add(uri)
                        all_results.append(result)
                        new_count += 1
                
                print(f"      📊 Found {len(results)} results | New {mbti_type}: {new_count} | Total: {len(all_results)}")
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
        
        print(f"\n✅ Discovery complete: Found {len(all_results)} unique {mbti_type} documents")
        return all_results
    
    def extract_structured_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from a search result."""
        
        content = result.get('content', {}).get('text', '')
        s3_uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
        score = result.get('score', 0.0)
        
        # Initialize structured data
        data = {
            'name': 'Unknown',
            'mbti_type': 'Unknown',
            'description': '',
            'address': '',
            'district': '',
            'area': '',
            'operating_hours': {},
            'contact': '',
            's3_uri': s3_uri,
            'filename': s3_uri.split('/')[-1] if s3_uri else 'Unknown',
            'score': score
        }
        
        # Parse content
        lines = content.split('\r\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('# '):
                data['name'] = line[2:].strip()
            elif '**Type:** ' in line:
                try:
                    data['mbti_type'] = line.split('**Type:** ')[1].split(' ')[0].strip()
                except:
                    pass
            elif '**Description:** ' in line:
                try:
                    data['description'] = line.split('**Description:** ')[1].strip()
                except:
                    pass
            elif '**Address:** ' in line:
                try:
                    data['address'] = line.split('**Address:** ')[1].strip()
                except:
                    pass
            elif '**District:** ' in line:
                try:
                    data['district'] = line.split('**District:** ')[1].strip()
                except:
                    pass
            elif '**Area:** ' in line:
                try:
                    data['area'] = line.split('**Area:** ')[1].strip()
                except:
                    pass
            elif '**Contact/Remarks:** ' in line:
                try:
                    data['contact'] = line.split('**Contact/Remarks:** ')[1].strip()
                except:
                    pass
            elif '**Weekdays (Mon-Fri):** ' in line:
                try:
                    data['operating_hours']['weekdays'] = line.split('**Weekdays (Mon-Fri):** ')[1].strip()
                except:
                    pass
            elif '**Weekends (Sat-Sun):** ' in line:
                try:
                    data['operating_hours']['weekends'] = line.split('**Weekends (Sat-Sun):** ')[1].strip()
                except:
                    pass
        
        # Extract area and district from S3 path if missing
        if s3_uri and (not data['area'] or not data['district']):
            path_parts = s3_uri.split('/')
            if len(path_parts) >= 4:
                if not data['area']:
                    area_mapping = {
                        'hong_kong_island': 'Hong Kong Island',
                        'kowloon': 'Kowloon',
                        'new_territories': 'New Territories',
                        'islands': 'Islands'
                    }
                    area_key = path_parts[2]
                    data['area'] = area_mapping.get(area_key, area_key.replace('_', ' ').title())
                
                if not data['district']:
                    data['district'] = path_parts[3].replace('_', ' ').title()
        
        return data
    
    def filter_by_test_criteria(self, records: List[Dict[str, Any]], test_case: str) -> List[Dict[str, Any]]:
        """Filter records according to test case criteria."""
        
        filtered_records = []
        
        for record in records:
            # All test cases require filename to start with current MBTI type
            if not record['filename'].startswith(f'{self.current_mbti_type}_'):
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
    
    def display_test_results(self, records: List[Dict[str, Any]], test_case_name: str):
        """Display filtered test results in a structured format."""
        
        print(f"\n🎯 {test_case_name}")
        print("=" * 80)
        
        if not records:
            print("❌ No records found matching the criteria.")
            return
        
        print(f"✅ Found {len(records)} {self.current_mbti_type} attractions matching criteria:")
        
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
                
                # Sort by relevance score
                sorted_attractions = sorted(attractions, key=lambda x: x['score'], reverse=True)
                
                for i, attraction in enumerate(sorted_attractions, 1):
                    print(f"    {i}. 🎯 {attraction['name']}")
                    print(f"       📄 File: {attraction['filename']}")
                    print(f"       📊 Score: {attraction['score']:.4f}")
                    if attraction['description']:
                        print(f"       📝 Description: {attraction['description']}")
                    if attraction['address']:
                        print(f"       📍 Address: {attraction['address']}")
                    
                    # Operating hours
                    if attraction['operating_hours']:
                        hours_parts = []
                        if 'weekdays' in attraction['operating_hours']:
                            hours_parts.append(f"Weekdays: {attraction['operating_hours']['weekdays']}")
                        if 'weekends' in attraction['operating_hours']:
                            hours_parts.append(f"Weekends: {attraction['operating_hours']['weekends']}")
                        if hours_parts:
                            print(f"       ⏰ Hours: {' | '.join(hours_parts)}")
                    
                    if attraction['contact']:
                        print(f"       📞 Contact: {attraction['contact']}")
                    
                    print()
    
    def run_comprehensive_test(self):
        """Run comprehensive test using MBTI prompts with filtering."""
        
        print("🚀 MBTI PROMPTS WITH FILTERING TEST")
        print("Testing all available MBTI personality types with comprehensive discovery")
        print("=" * 80)
        
        start_time = time.time()
        
        # Get all available MBTI types from the prompt files
        available_types = self.get_available_mbti_types()
        print(f"📋 Available MBTI types: {', '.join(available_types)}")
        
        # Test each MBTI type
        all_results = {}
        for mbti_type in available_types:
            print(f"\n🎯 TESTING {mbti_type} PERSONALITY TYPE")
            print("=" * 60)
            
            # Step 1: Use MBTI prompts to discover documents for this type
            mbti_results = self.search_with_mbti_prompts(mbti_type, use_optimized=True)
        
            # Step 2: Extract structured data
            print(f"\n📋 EXTRACTING STRUCTURED DATA FOR {mbti_type}...")
            structured_records = []
            for result in mbti_results:
                try:
                    record = self.extract_structured_data(result)
                    structured_records.append(record)
                except Exception as e:
                    print(f"⚠️  Error extracting record: {str(e)}")
            
            print(f"✅ Extracted {len(structured_records)} structured {mbti_type} records")
        
            # Step 3: Apply test case filters and display results
            
            # Test Case 1: All Areas, All Districts, MBTI files
            test1_records = self.filter_by_test_criteria(structured_records, "test_case_1")
            self.display_test_results(test1_records, f"TEST CASE 1: All Areas, All Districts, Files starting with {mbti_type}")
            
            # Test Case 2: All Areas, Central Districts, MBTI files
            test2_records = self.filter_by_test_criteria(structured_records, "test_case_2")
            self.display_test_results(test2_records, f"TEST CASE 2: All Areas, Central Districts, Files starting with {mbti_type}")
        
            # Test Case 3: Hong Kong Island Area, All Districts, MBTI files
            test3_records = self.filter_by_test_criteria(structured_records, "test_case_3")
            self.display_test_results(test3_records, f"TEST CASE 3: Hong Kong Island Area, All Districts, Files starting with {mbti_type}")
            
            # Store results for this MBTI type
            all_results[mbti_type] = {
                'total_documents': len(structured_records),
                'test_case_1': len(test1_records),
                'test_case_2': len(test2_records),
                'test_case_3': len(test3_records),
                'records': structured_records
            }
        
        # Summary
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total Execution Time: {total_time} seconds")
        print(f"🔍 MBTI Types Tested: {len(available_types)}")
        print(f"📋 Results by MBTI Type:")
        
        for mbti_type, results in all_results.items():
            print(f"   {mbti_type}: {results['total_documents']} documents found")
            print(f"      Test Case 1: {results['test_case_1']} records")
            print(f"      Test Case 2: {results['test_case_2']} records") 
            print(f"      Test Case 3: {results['test_case_3']} records")
        
        # Show summary of most effective MBTI types
        print(f"\n🎯 MBTI Type Effectiveness Summary:")
        sorted_results = sorted(all_results.items(), key=lambda x: x[1]['total_documents'], reverse=True)
        for mbti_type, results in sorted_results[:5]:  # Top 5
            mbti_info = self.prompt_loader.get_personality_info(mbti_type)
            print(f"   {mbti_type}: {results['total_documents']} documents - {mbti_info['description']}")
        
        # Save results for all MBTI types
        self.save_comprehensive_test_results(all_results, total_time)
        
        return {
            'all_results': all_results,
            'total_time': total_time,
            'test3_records': test3_records,
            'execution_time': total_time
        }
    
    def save_comprehensive_test_results(self, all_results, total_time):
        """Save comprehensive test results for all MBTI types to JSON file."""
        
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
        
        filename = f"comprehensive_mbti_test_results_{int(time.time())}.json"
        
        output_data = {
            'test_suite': 'Comprehensive MBTI Prompts with Filtering Test',
            'knowledge_base_id': self.knowledge_base_id,
            'total_execution_time': total_time,
            'mbti_types_tested': list(all_results.keys()),
            'total_mbti_types': len(all_results),
                    'count': len(test3_records),
            'results_by_mbti_type': {}
        }
        
        # Add results for each MBTI type
        for mbti_type, results in all_results.items():
            output_data['results_by_mbti_type'][mbti_type] = {
                'total_documents': results['total_documents'],
                'test_cases': {
                    'test_case_1': {
                        'description': f'All Areas, All Districts, Files starting with {mbti_type}',
                        'count': results['test_case_1']
                    },
                    'test_case_2': {
                        'description': f'All Areas, Central Districts, Files starting with {mbti_type}',
                        'count': results['test_case_2']
                    },
                    'test_case_3': {
                        'description': f'Hong Kong Island Area, All Districts, Files starting with {mbti_type}',
                        'count': results['test_case_3']
                    }
                },
                'all_records': [record_to_dict(r) for r in results['records']]
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive results saved to: {filename}")

def main():
    tester = MBTIPromptsFilteredTester()
    results = tester.run_comprehensive_test()
    
    print(f"\n🎉 COMPREHENSIVE MBTI PROMPTS FILTERED SEARCH COMPLETE!")
    print(f"Successfully tested {len(results['all_results'])} MBTI personality types")
    
    total_documents = sum(r['total_documents'] for r in results['all_results'].values())
    print(f"Total documents discovered across all MBTI types: {total_documents}")
    print(f"Total execution time: {results['total_time']} seconds")

if __name__ == "__main__":
    main()