#!/usr/bin/env python3
"""
Filename-Based Search Validation

This script tests the knowledge base search functionality by directly targeting
specific INFJ filenames to validate precise file retrieval.

Test Cases:
1. Direct INFJ filename searches
2. Wildcard INFJ* pattern searches
3. Specific file targeting with folder context
"""

import boto3
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

class FilenameBasedSearchValidator:
    """Validate filename-based search functionality."""
    
    def __init__(self):
        self.region = "us-east-1"
        self.knowledge_base_id = "RCWW86CLM9"
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        # Expected INFJ files from the knowledge base
        self.expected_infj_files = [
            "INFJ_M+.md",
            "INFJ_Central_Market.md", 
            "INFJ_Tai_Kwun.md",
            "INFJ_Hong_Kong_Cultural_Centre.md",
            "INFJ_Broadway_Cinematheque.md",
            "INFJ_Po_Lin_Monastery.md",
            "INFJ_Pacific_Place_Rooftop_Garden.md",
            "INFJ_Man_Mo_Temple.md",
            "INFJ_PMQ_Police_Married_Quarters.md",
            "INFJ_Hong_Kong_House_of_Stories.md",
            "INFJ_SoHo_and_Central_Art_Galleries.md",
            "INFJ_Hong_Kong_Museum_of_Art.md",
            "INFJ_Hong_Kong_Palace_Museum.md"
        ]
        
        # Test cases with direct filename targeting
        self.test_cases = [
            {
                "name": "Direct INFJ Filename Search",
                "query": "INFJ_M+ INFJ_Central_Market INFJ_Tai_Kwun INFJ_Hong_Kong_Cultural_Centre INFJ_Broadway_Cinematheque",
                "expected_count": 5,
                "target_files": ["INFJ_M+.md", "INFJ_Central_Market.md", "INFJ_Tai_Kwun.md", "INFJ_Hong_Kong_Cultural_Centre.md", "INFJ_Broadway_Cinematheque.md"]
            },
            {
                "name": "INFJ Wildcard Pattern Search",
                "query": "filename starts with INFJ_ pattern INFJ*.md files",
                "expected_count": 13,
                "target_files": self.expected_infj_files
            },
            {
                "name": "Specific INFJ Files with Folder Context",
                "query": "INFJ_Central_Market in central_district INFJ_M+ in tsim_sha_tsui INFJ_Pacific_Place_Rooftop_Garden in admiralty",
                "expected_count": 3,
                "target_files": ["INFJ_Central_Market.md", "INFJ_M+.md", "INFJ_Pacific_Place_Rooftop_Garden.md"]
            },
            {
                "name": "Hong Kong Island INFJ Files",
                "query": "INFJ_Pacific_Place_Rooftop_Garden INFJ_Central_Market INFJ_SoHo_and_Central_Art_Galleries INFJ_Tai_Kwun INFJ_Man_Mo_Temple INFJ_PMQ_Police_Married_Quarters INFJ_Hong_Kong_House_of_Stories hong_kong_island",
                "expected_count": 7,
                "target_files": ["INFJ_Pacific_Place_Rooftop_Garden.md", "INFJ_Central_Market.md", "INFJ_SoHo_and_Central_Art_Galleries.md", "INFJ_Tai_Kwun.md", "INFJ_Man_Mo_Temple.md", "INFJ_PMQ_Police_Married_Quarters.md", "INFJ_Hong_Kong_House_of_Stories.md"]
            },
            {
                "name": "Kowloon INFJ Files",
                "query": "INFJ_M+ INFJ_Hong_Kong_Cultural_Centre INFJ_Hong_Kong_Museum_of_Art INFJ_Hong_Kong_Palace_Museum INFJ_Broadway_Cinematheque kowloon",
                "expected_count": 5,
                "target_files": ["INFJ_M+.md", "INFJ_Hong_Kong_Cultural_Centre.md", "INFJ_Hong_Kong_Museum_of_Art.md", "INFJ_Hong_Kong_Palace_Museum.md", "INFJ_Broadway_Cinematheque.md"]
            }
        ]
    
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
    
    def analyze_filename_results(self, results: List[Dict], target_files: List[str]) -> Dict:
        """Analyze search results focusing on filename matching."""
        
        analysis = {
            "total_results": len(results),
            "infj_results": [],
            "non_infj_results": [],
            "target_files_found": [],
            "target_files_missing": [],
            "unexpected_infj_files": []
        }
        
        target_filenames = set(target_files)
        
        for result in results:
            # Extract filename from S3 URI
            s3_uri = result['location']['s3Location']['uri']
            filename = s3_uri.split('/')[-1]
            
            # Extract folder path
            path_parts = s3_uri.split('/')
            folder_path = f"{path_parts[-3]}/{path_parts[-2]}" if len(path_parts) >= 3 else "unknown"
            
            # Check if this is an INFJ file
            if filename.startswith('INFJ_'):
                file_info = {
                    "filename": filename,
                    "folder_path": folder_path,
                    "score": result['score'],
                    "is_target": filename in target_filenames
                }
                
                analysis["infj_results"].append(file_info)
                
                # Track target vs unexpected
                if filename in target_filenames:
                    analysis["target_files_found"].append(filename)
                else:
                    analysis["unexpected_infj_files"].append(filename)
            else:
                analysis["non_infj_results"].append({
                    "filename": filename,
                    "folder_path": folder_path,
                    "score": result['score']
                })
        
        # Find missing target files
        found_filenames = set([f["filename"] for f in analysis["infj_results"]])
        analysis["target_files_missing"] = list(target_filenames - found_filenames)
        
        return analysis
    
    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single filename-based test case."""
        
        print(f"\n🧪 Running Test Case: {test_case['name']}")
        print(f"   Query: {test_case['query']}")
        print(f"   Expected Count: {test_case['expected_count']}")
        print(f"   Target Files: {len(test_case['target_files'])}")
        
        # Execute query
        results = self.execute_knowledge_base_query(test_case['query'])
        
        if not results:
            print("   ❌ No results returned from knowledge base")
            return {"success": False, "error": "No results returned"}
        
        # Analyze results with filename focus
        analysis = self.analyze_filename_results(results, test_case['target_files'])
        
        # Calculate metrics
        infj_count = len(analysis["infj_results"])
        target_found = len(analysis["target_files_found"])
        expected_count = test_case['expected_count']
        
        filename_accuracy = (target_found / expected_count * 100) if expected_count > 0 else 0
        precision = (infj_count / len(results) * 100) if results else 0
        recall = (target_found / len(test_case['target_files']) * 100) if test_case['target_files'] else 0
        
        print(f"   📊 Results: {len(results)} total, {infj_count} INFJ files")
        print(f"   🎯 Filename Accuracy: {filename_accuracy:.1f}% ({target_found}/{expected_count} target files found)")
        print(f"   🎯 Precision: {precision:.1f}% ({infj_count}/{len(results)} results are INFJ)")
        print(f"   🎯 Recall: {recall:.1f}% ({target_found}/{len(test_case['target_files'])} target files retrieved)")
        
        # Show target files found
        if analysis["target_files_found"]:
            print(f"   ✅ Target Files Found ({len(analysis['target_files_found'])}):")
            for filename in analysis["target_files_found"][:5]:
                print(f"      ✅ {filename}")
            if len(analysis["target_files_found"]) > 5:
                print(f"      ... and {len(analysis['target_files_found']) - 5} more")
        
        # Show missing target files
        if analysis["target_files_missing"]:
            print(f"   ❌ Missing Target Files ({len(analysis['target_files_missing'])}):")
            for filename in analysis["target_files_missing"][:3]:
                print(f"      ❌ {filename}")
            if len(analysis["target_files_missing"]) > 3:
                print(f"      ... and {len(analysis['target_files_missing']) - 3} more")
        
        # Show top results with filename focus
        print(f"   📄 Top Results:")
        for i, result in enumerate(results[:5], 1):
            s3_uri = result['location']['s3Location']['uri']
            filename = s3_uri.split('/')[-1]
            folder_path = f"{s3_uri.split('/')[-3]}/{s3_uri.split('/')[-2]}" if len(s3_uri.split('/')) >= 3 else "unknown"
            score = result['score']
            is_infj = filename.startswith('INFJ_')
            is_target = filename in test_case['target_files']
            
            if is_infj and is_target:
                status = "✅ TARGET"
            elif is_infj:
                status = "⚠️ INFJ (not target)"
            else:
                status = "❌ Not INFJ"
            
            print(f"      {i}. {filename} ({folder_path}) - Score: {score:.3f} {status}")
        
        return {
            "success": True,
            "test_case": test_case['name'],
            "total_results": len(results),
            "infj_results": infj_count,
            "target_found": target_found,
            "expected_count": expected_count,
            "filename_accuracy": filename_accuracy,
            "precision": precision,
            "recall": recall,
            "target_files_found": analysis["target_files_found"],
            "target_files_missing": analysis["target_files_missing"],
            "unexpected_infj_files": analysis["unexpected_infj_files"]
        }
    
    def run_all_tests(self) -> Dict:
        """Run all test cases and generate comprehensive report."""
        
        print("🎯 Filename-Based Search Validation Tests")
        print("="*70)
        print("Testing knowledge base search with direct INFJ filename targeting")
        print("to validate precise file retrieval capabilities")
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
        print("📊 FILENAME-BASED SEARCH SUMMARY")
        print("="*70)
        
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results if r.get("success", False)])
        
        avg_filename_accuracy = sum([r.get("filename_accuracy", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_precision = sum([r.get("precision", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        avg_recall = sum([r.get("recall", 0) for r in test_results]) / total_tests if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Performance:")
        print(f"   ✅ Tests Passed: {successful_tests}/{total_tests}")
        print(f"   📊 Average Filename Accuracy: {avg_filename_accuracy:.1f}%")
        print(f"   📊 Average Precision: {avg_precision:.1f}%")
        print(f"   📊 Average Recall: {avg_recall:.1f}%")
        
        print(f"\n📋 Individual Test Results:")
        for result in test_results:
            if result.get("success"):
                name = result["test_case"]
                filename_accuracy = result["filename_accuracy"]
                precision = result["precision"]
                recall = result["recall"]
                
                status = "✅ EXCELLENT" if filename_accuracy >= 90 else "⚠️ GOOD" if filename_accuracy >= 70 else "❌ NEEDS IMPROVEMENT"
                print(f"   {status} {name}")
                print(f"      Filename: {filename_accuracy:.1f}%, Precision: {precision:.1f}%, Recall: {recall:.1f}%")
        
        # Show overall filename targeting performance
        total_target_found = sum([len(r.get("target_files_found", [])) for r in test_results if r.get("success")])
        total_expected = sum([r.get("expected_count", 0) for r in test_results if r.get("success")])
        overall_filename_accuracy = (total_target_found / total_expected * 100) if total_expected > 0 else 0
        
        print(f"\n📁 Overall Filename Targeting:")
        print(f"   🎯 Total Target Files Found: {total_target_found}/{total_expected}")
        print(f"   🎯 Overall Filename Accuracy: {overall_filename_accuracy:.1f}%")
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "avg_filename_accuracy": avg_filename_accuracy,
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "overall_filename_accuracy": overall_filename_accuracy,
            "total_target_found": total_target_found,
            "total_expected": total_expected,
            "test_results": test_results
        }
        
        return summary
    
    def save_test_results(self, test_results: List[Dict], summary: Dict) -> None:
        """Save test results to file."""
        
        output_file = Path("mbti_travel_assistant_mcp/tests/filename_based_search_results.json")
        
        full_report = {
            "summary": summary,
            "detailed_results": test_results,
            "expected_infj_files": self.expected_infj_files
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")

def main():
    """Main execution function."""
    
    validator = FilenameBasedSearchValidator()
    summary = validator.run_all_tests()
    
    print(f"\n🎉 Filename-Based Search Validation Complete!")
    
    if summary["avg_filename_accuracy"] >= 90:
        print("✅ EXCELLENT: Filename-based search is performing exceptionally well!")
    elif summary["avg_filename_accuracy"] >= 70:
        print("⚠️ GOOD: Filename-based search is performing well with room for improvement")
    else:
        print("❌ NEEDS IMPROVEMENT: Filename-based search requires optimization")
    
    print(f"\nNext steps:")
    print(f"1. Review filename targeting patterns")
    print(f"2. Optimize queries for better file specificity")
    print(f"3. Consider filename-based indexing improvements")

if __name__ == "__main__":
    main()