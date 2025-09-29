#!/usr/bin/env python3
"""
Enhanced Hierarchical Search Validation

This script tests the knowledge base search functionality with folder-aware queries
that specifically target the hierarchical structure organization.

Test Cases:
1. Folder-specific INFJ searches
2. Area-based filtering with folder paths
3. District-specific searches using folder structure
4. Cross-area searches with explicit folder targeting
"""

import boto3
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

class EnhancedHierarchicalSearchValidator:
    """Validate hierarchical search functionality with folder-aware queries."""
    
    def __init__(self):
        self.region = "us-east-1"
        self.knowledge_base_id = "RCWW86CLM9"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        # Load expected results
        self.expected_results = self.load_expected_results()
        
        # Enhanced test cases with folder-specific queries
        self.test_cases = [
            {
                "name": "INFJ Files in Hong Kong Island Folder",
                "query": "INFJ files located in hong_kong_island folder structure admiralty central_district sheung_wan wan_chai",
                "expected_count": 7,
                "folder_focus": "hong_kong_island",
                "expected_folders": ["admiralty", "central_district", "sheung_wan", "wan_chai"]
            },
            {
                "name": "INFJ Files in Kowloon Folder",
                "query": "INFJ files located in kowloon folder structure tsim_sha_tsui yau_ma_tei",
                "expected_count": 4,
                "folder_focus": "kowloon",
                "expected_folders": ["tsim_sha_tsui", "yau_ma_tei"]
            },
            {
                "name": "INFJ Files in Central District Folder",
                "query": "INFJ files in central_district folder hong_kong_island/central_district path",
                "expected_count": 3,
                "folder_focus": "central_district",
                "expected_folders": ["central_district"]
            },
            {
                "name": "INFJ Files in Tsim Sha Tsui Folder",
                "query": "INFJ files in tsim_sha_tsui folder kowloon/tsim_sha_tsui path",
                "expected_count": 4,
                "folder_focus": "tsim_sha_tsui",
                "expected_folders": ["tsim_sha_tsui"]
            },
            {
                "name": "All INFJ Files with Folder Structure",
                "query": "INFJ files across all folders hong_kong_island kowloon islands new_territories folder structure",
                "expected_count": 13,
                "folder_focus": "all",
                "expected_folders": ["hong_kong_island", "kowloon", "islands", "new_territories"]
            }
        ]
    
    def load_expected_results(self) -> Dict:
        """Load expected results from analysis file."""
        
        results_file = Path("mbti_travel_assistant_mcp/tests/infj_expected_results.json")
        
        if not results_file.exists():
            print(f"❌ Expected results file not found: {results_file}")
            return {"summary": {"test_case_1_count": 0, "test_case_2_count": 0, "test_case_3_count": 0}}
        
        with open(results_file, 'r') as f:
            return json.load(f)
    
    def execute_knowledge_base_query(self, query: str, max_results: int = 25) -> List[Dict]:
        """Execute a query against the knowledge base."""
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {'numberOfResults': max_results}
                }
            )
            
            return response['retrievalResults']
            
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return []
    
    def analyze_folder_based_results(self, results: List[Dict], test_case: Dict) -> Dict:
        """Analyze search results with focus on folder structure."""
        
        analysis = {
            "total_results": len(results),
            "infj_results": [],
            "non_infj_results": [],
            "folder_distribution": {},
            "expected_folders_found": [],
            "unexpected_folders": []
        }
        
        expected_folders = test_case.get("expected_folders", [])
        
        for result in results:
            # Extract folder path from S3 URI
            s3_uri = result['location']['s3Location']['uri']
            path_parts = s3_uri.split('/')
            filename = path_parts[-1]
            
            # Extract area and district from path
            if len(path_parts) >= 3:
                area = path_parts[-3]
                district = path_parts[-2]
                folder_path = f"{area}/{district}"
            else:
                area = "unknown"
                district = "unknown"
                folder_path = "unknown/unknown"
            
            # Check if this is an INFJ file
            if filename.startswith('INFJ_'):
                analysis["infj_results"].append({
                    "filename": filename,
                    "area": area,
                    "district": district,
                    "folder_path": folder_path,
                    "score": result['score']
                })
                
                # Track folder distribution
                if folder_path not in analysis["folder_distribution"]:
                    analysis["folder_distribution"][folder_path] = 0
                analysis["folder_distribution"][folder_path] += 1
                
                # Check if folder is expected
                if area in expected_folders or district in expected_folders:
                    if area not in analysis["expected_folders_found"]:
                        analysis["expected_folders_found"].append(area)
                    if district not in analysis["expected_folders_found"]:
                        analysis["expected_folders_found"].append(district)
                else:
                    if area not in analysis["unexpected_folders"]:
                        analysis["unexpected_folders"].append(area)
                    if district not in analysis["unexpected_folders"]:
                        analysis["unexpected_folders"].append(district)
            else:
                analysis["non_infj_results"].append({
                    "filename": filename,
                    "area": area,
                    "district": district,
                    "folder_path": folder_path,
                    "score": result['score']
                })
        
        return analysis
    
    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case with folder-aware analysis."""
        
        print(f"\n🧪 Running Test Case: {test_case['name']}")
        print(f"   Query: {test_case['query']}")
        print(f"   Expected Count: {test_case['expected_count']}")
        print(f"   Target Folders: {test_case['expected_folders']}")
        
        # Execute query
        results = self.execute_knowledge_base_query(test_case['query'])
        
        if not results:
            print("   ❌ No results returned from knowledge base")
            return {"success": False, "error": "No results returned"}
        
        # Analyze results with folder focus
        analysis = self.analyze_folder_based_results(results, test_case)
        
        # Calculate metrics
        infj_count = len(analysis["infj_results"])
        expected_count = test_case['expected_count']
        
        accuracy = (infj_count / expected_count * 100) if expected_count > 0 else 0
        precision = (infj_count / len(results) * 100) if results else 0
        folder_accuracy = len(analysis["expected_folders_found"]) / len(test_case['expected_folders']) * 100 if test_case['expected_folders'] else 100
        
        print(f"   📊 Results: {len(results)} total, {infj_count} INFJ files")
        print(f"   🎯 INFJ Accuracy: {accuracy:.1f}% ({infj_count}/{expected_count})")
        print(f"   🎯 Precision: {precision:.1f}% ({infj_count}/{len(results)} results are INFJ)")
        print(f"   📁 Folder Accuracy: {folder_accuracy:.1f}% ({len(analysis['expected_folders_found'])}/{len(test_case['expected_folders'])} expected folders)")
        
        # Show folder distribution
        print(f"   📁 Folder Distribution:")
        for folder_path, count in sorted(analysis["folder_distribution"].items()):
            print(f"      {folder_path}: {count} files")
        
        # Show top results with folder info
        print(f"   📄 Top Results:")
        for i, result in enumerate(results[:5], 1):
            s3_uri = result['location']['s3Location']['uri']
            path_parts = s3_uri.split('/')
            filename = path_parts[-1]
            folder_path = f"{path_parts[-3]}/{path_parts[-2]}" if len(path_parts) >= 3 else "unknown"
            score = result['score']
            is_infj = filename.startswith('INFJ_')
            
            status = "✅ INFJ" if is_infj else "❌ Not INFJ"
            print(f"      {i}. {filename} ({folder_path}) - Score: {score:.3f} {status}")
        
        return {
            "success": True,
            "test_case": test_case['name'],
            "total_results": len(results),
            "infj_results": infj_count,
            "expected_count": expected_count,
            "accuracy": accuracy,
            "precision": precision,
            "folder_accuracy": folder_accuracy,
            "folder_distribution": analysis["folder_distribution"],
            "expected_folders_found": analysis["expected_folders_found"],
            "unexpected_folders": analysis["unexpected_folders"]
        }
    
    def run_all_tests(self) -> Dict:
        """Run all test cases and generate comprehensive report."""
        
        print("🎯 Enhanced Hierarchical Search Validation Tests")
        print("="*70)
        print("Testing knowledge base search with folder-aware queries")
        print("targeting specific hierarchical structure paths")
        print()
        
        test_results = []
        
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            test_results.append(result)
            time.sleep(2)  # Brief pause between tests
        
        # Generate summary report
        summary = self.generate_summary_report(test_results)
        
        # Save detailed results
        self.save_test_results(test_results, summary)
        
        return summary
    
    def generate_summary_report(self, test_results: List[Dict]) -> Dict:
        """Generate summary report of all test results."""
        
        print(f"\n" + "="*70)
        print("📊 ENHANCED HIERARCHICAL SEARCH SUMMARY")
        print("="*70)
        
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.get("success", False)])
        
        avg_accuracy = sum([r.get("accuracy", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_precision = sum([r.get("precision", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_folder_accuracy = sum([r.get("folder_accuracy", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Performance:")
        print(f"   ✅ Tests Passed: {successful_tests}/{total_tests}")
        print(f"   📊 Average INFJ Accuracy: {avg_accuracy:.1f}%")
        print(f"   📊 Average Precision: {avg_precision:.1f}%")
        print(f"   📁 Average Folder Accuracy: {avg_folder_accuracy:.1f}%")
        
        print(f"\n📋 Individual Test Results:")
        for result in test_results:
            if result.get("success"):
                name = result["test_case"]
                accuracy = result["accuracy"]
                precision = result["precision"]
                folder_accuracy = result["folder_accuracy"]
                
                status = "✅ EXCELLENT" if accuracy >= 80 and folder_accuracy >= 80 else "⚠️ GOOD" if accuracy >= 60 else "❌ NEEDS IMPROVEMENT"
                print(f"   {status} {name}")
                print(f"      INFJ: {accuracy:.1f}%, Precision: {precision:.1f}%, Folders: {folder_accuracy:.1f}%")
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "avg_accuracy": avg_accuracy,
            "avg_precision": avg_precision,
            "avg_folder_accuracy": avg_folder_accuracy,
            "test_results": test_results
        }
        
        return summary
    
    def save_test_results(self, test_results: List[Dict], summary: Dict) -> None:
        """Save test results to file."""
        
        output_file = Path("mbti_travel_assistant_mcp/tests/enhanced_hierarchical_search_results.json")
        
        full_report = {
            "summary": summary,
            "detailed_results": test_results,
            "folder_structure_analysis": {
                "areas": ["hong_kong_island", "kowloon", "islands", "new_territories"],
                "districts_tested": [
                    "admiralty", "central_district", "sheung_wan", "wan_chai",
                    "tsim_sha_tsui", "yau_ma_tei", "lantau"
                ]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")

def main():
    """Main execution function."""
    
    validator = EnhancedHierarchicalSearchValidator()
    summary = validator.run_all_tests()
    
    print(f"\n🎉 Enhanced Hierarchical Search Validation Complete!")
    
    if summary["avg_accuracy"] >= 80 and summary["avg_folder_accuracy"] >= 80:
        print("✅ EXCELLENT: Folder-aware search is performing exceptionally well!")
    elif summary["avg_accuracy"] >= 60 and summary["avg_folder_accuracy"] >= 60:
        print("⚠️ GOOD: Folder-aware search is performing well with room for improvement")
    else:
        print("❌ NEEDS IMPROVEMENT: Folder-aware search requires optimization")
    
    print(f"\nNext steps:")
    print(f"1. Review folder distribution patterns")
    print(f"2. Optimize queries for better folder targeting")
    print(f"3. Consider additional folder-specific keywords")

if __name__ == "__main__":
    main()