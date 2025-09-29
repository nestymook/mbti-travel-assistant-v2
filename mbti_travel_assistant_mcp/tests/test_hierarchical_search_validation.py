#!/usr/bin/env python3
"""
Test Hierarchical Search Validation

This script tests the knowledge base search functionality with the new
hierarchical structure and optimized keywords to validate search accuracy.

Test Cases:
1. All Areas, All Districts, INFJ files (Expected: 13 files)
2. All Areas, Central Districts, INFJ files (Expected: 3 files)  
3. Hong Kong Island Area, All Districts, INFJ files (Expected: 7 files)
"""

import boto3
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

class HierarchicalSearchValidator:
    """Validate hierarchical search functionality."""
    
    def __init__(self):
        self.region = "us-east-1"
        self.knowledge_base_id = "RCWW86CLM9"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        # Load expected results
        self.expected_results = self.load_expected_results()
        
        # Test cases with specific INFJ filename targeting
        self.test_cases = [
            {
                "name": "All Areas, All Districts, INFJ",
                "query": "files starting with INFJ_",
                "expected_count": self.expected_results["summary"]["test_case_1_count"],
                "expected_files": self.expected_results["all_areas_all_districts"],
                "search_terms": ["INFJ_", "filename"]
            },
            {
                "name": "All Areas, Central Districts, INFJ", 
                "query": "files starting with INFJ_ in *\central_district folder. Ensure all files starting with INFJ_",
                "expected_count": self.expected_results["summary"]["test_case_2_count"],
                "expected_files": self.expected_results["all_areas_central_districts"],
                "search_terms": ["INFJ_", "central_district", "filename"]
            },
            {
                "name": "Hong Kong Island Area, All Districts, INFJ",
                "query": "files starting with INFJ_ in hong_kong_island folder",
                "expected_count": self.expected_results["summary"]["test_case_3_count"],
                "expected_files": self.expected_results["hong_kong_island_all_districts"],
                "search_terms": ["INFJ_", "hong_kong_island", "filename"]
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
    
    def execute_knowledge_base_query(self, query: str, max_results: int = 20) -> List[Dict]:
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
    
    def analyze_search_results(self, results: List[Dict], expected_files: List[Dict]) -> Dict:
        """Analyze search results against expected files."""
        
        analysis = {
            "total_results": len(results),
            "infj_results": [],
            "non_infj_results": [],
            "expected_found": [],
            "expected_missing": [],
            "unexpected_results": []
        }
        
        # Extract expected filenames for comparison
        expected_filenames = set([f["filename"] for f in expected_files])
        expected_s3_paths = set([f["s3_path"] for f in expected_files])
        
        for result in results:
            # Extract filename from S3 URI
            s3_uri = result['location']['s3Location']['uri']
            filename = s3_uri.split('/')[-1]
            s3_path = '/'.join(s3_uri.split('/')[-3:])  # area/district/filename
            
            # Check if this is an INFJ file
            if filename.startswith('INFJ_'):
                analysis["infj_results"].append({
                    "filename": filename,
                    "s3_path": s3_path,
                    "score": result['score'],
                    "expected": filename in expected_filenames
                })
                
                # Track if this was expected
                if filename in expected_filenames:
                    analysis["expected_found"].append(filename)
                else:
                    analysis["unexpected_results"].append(filename)
            else:
                analysis["non_infj_results"].append({
                    "filename": filename,
                    "s3_path": s3_path,
                    "score": result['score']
                })
        
        # Find missing expected files
        found_filenames = set([r["filename"] for r in analysis["infj_results"]])
        analysis["expected_missing"] = list(expected_filenames - found_filenames)
        
        return analysis
    
    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case."""
        
        print(f"\n🧪 Running Test Case: {test_case['name']}")
        print(f"   Query: {test_case['query']}")
        print(f"   Expected Count: {test_case['expected_count']}")
        
        # Execute query
        results = self.execute_knowledge_base_query(test_case['query'])
        
        if not results:
            print("   ❌ No results returned from knowledge base")
            return {"success": False, "error": "No results returned"}
        
        # Analyze results
        analysis = self.analyze_search_results(results, test_case['expected_files'])
        
        # Calculate accuracy metrics
        infj_count = len(analysis["infj_results"])
        expected_count = test_case['expected_count']
        found_expected = len(analysis["expected_found"])
        
        accuracy = (found_expected / expected_count * 100) if expected_count > 0 else 0
        precision = (infj_count / len(results) * 100) if results else 0
        recall = (found_expected / expected_count * 100) if expected_count > 0 else 0
        
        print(f"   📊 Results: {len(results)} total, {infj_count} INFJ files")
        print(f"   🎯 Accuracy: {accuracy:.1f}% ({found_expected}/{expected_count} expected files found)")
        print(f"   🎯 Precision: {precision:.1f}% ({infj_count}/{len(results)} results are INFJ)")
        print(f"   🎯 Recall: {recall:.1f}% ({found_expected}/{expected_count} expected files retrieved)")
        
        # Show top results
        print(f"   📄 Top Results:")
        for i, result in enumerate(results[:5], 1):
            filename = result['location']['s3Location']['uri'].split('/')[-1]
            score = result['score']
            is_infj = filename.startswith('INFJ_')
            expected = filename in [f["filename"] for f in test_case['expected_files']]
            
            status = "✅ Expected" if (is_infj and expected) else "⚠️ Unexpected" if is_infj else "❌ Wrong Type"
            print(f"      {i}. {filename} (Score: {score:.3f}) {status}")
        
        # Show missing expected files
        if analysis["expected_missing"]:
            print(f"   ⚠️ Missing Expected Files ({len(analysis['expected_missing'])}):")
            for missing in analysis["expected_missing"][:3]:
                print(f"      - {missing}")
            if len(analysis["expected_missing"]) > 3:
                print(f"      ... and {len(analysis['expected_missing']) - 3} more")
        
        return {
            "success": True,
            "test_case": test_case['name'],
            "total_results": len(results),
            "infj_results": infj_count,
            "expected_count": expected_count,
            "found_expected": found_expected,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "analysis": analysis
        }
    
    def run_all_tests(self) -> Dict:
        """Run all test cases and generate comprehensive report."""
        
        print("🎯 Hierarchical Search Validation Tests")
        print("="*70)
        print("Testing knowledge base search with new hierarchical structure")
        print("and optimized keywords (MBTI:, District:, Area: prefixes)")
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
        print("📊 HIERARCHICAL SEARCH VALIDATION SUMMARY")
        print("="*70)
        
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.get("success", False)])
        
        avg_accuracy = sum([r.get("accuracy", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_precision = sum([r.get("precision", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_recall = sum([r.get("recall", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Performance:")
        print(f"   ✅ Tests Passed: {successful_tests}/{total_tests}")
        print(f"   📊 Average Accuracy: {avg_accuracy:.1f}%")
        print(f"   📊 Average Precision: {avg_precision:.1f}%")
        print(f"   📊 Average Recall: {avg_recall:.1f}%")
        
        print(f"\n📋 Individual Test Results:")
        for result in test_results:
            if result.get("success"):
                name = result["test_case"]
                accuracy = result["accuracy"]
                precision = result["precision"]
                recall = result["recall"]
                
                status = "✅ EXCELLENT" if accuracy >= 90 else "⚠️ GOOD" if accuracy >= 70 else "❌ NEEDS IMPROVEMENT"
                print(f"   {status} {name}")
                print(f"      Accuracy: {accuracy:.1f}%, Precision: {precision:.1f}%, Recall: {recall:.1f}%")
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "avg_accuracy": avg_accuracy,
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "test_results": test_results
        }
        
        return summary
    
    def save_test_results(self, test_results: List[Dict], summary: Dict) -> None:
        """Save test results to file."""
        
        output_file = Path("mbti_travel_assistant_mcp/tests/hierarchical_search_test_results.json")
        
        full_report = {
            "summary": summary,
            "detailed_results": test_results,
            "expected_counts": {
                "test_case_1": self.expected_results["summary"]["test_case_1_count"],
                "test_case_2": self.expected_results["summary"]["test_case_2_count"],
                "test_case_3": self.expected_results["summary"]["test_case_3_count"]
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")

def main():
    """Main execution function."""
    
    validator = HierarchicalSearchValidator()
    summary = validator.run_all_tests()
    
    print(f"\n🎉 Hierarchical Search Validation Complete!")
    
    if summary["avg_accuracy"] >= 90:
        print("✅ EXCELLENT: Knowledge base search is performing exceptionally well!")
    elif summary["avg_accuracy"] >= 70:
        print("⚠️ GOOD: Knowledge base search is performing well with room for improvement")
    else:
        print("❌ NEEDS IMPROVEMENT: Knowledge base search requires optimization")
    
    print(f"\nNext steps:")
    print(f"1. Review detailed test results")
    print(f"2. Optimize queries that performed poorly")
    print(f"3. Consider additional keyword enhancements")

if __name__ == "__main__":
    main()