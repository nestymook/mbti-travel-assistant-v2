#!/usr/bin/env python3
"""
Analyze INFJ Files in Organized Knowledge Base

This script analyzes the organized_kb folder structure to count INFJ files
for different search scenarios and creates expected results for testing.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

class INFJFileAnalyzer:
    """Analyze INFJ files in the organized knowledge base structure."""
    
    def __init__(self, base_path: str = "mbti_travel_assistant_mcp/organized_kb"):
        self.base_path = Path(base_path)
    
    def analyze_infj_files(self) -> Dict[str, any]:
        """Analyze INFJ files across different search scenarios."""
        
        print("🔍 Analyzing INFJ files in organized knowledge base...")
        
        if not self.base_path.exists():
            print(f"❌ Path not found: {self.base_path}")
            return {}
        
        results = {
            "all_areas_all_districts": [],
            "all_areas_central_districts": [],
            "hong_kong_island_all_districts": [],
            "summary": {}
        }
        
        # Walk through all areas and districts
        for area_dir in self.base_path.iterdir():
            if not area_dir.is_dir():
                continue
                
            area_name = area_dir.name
            print(f"\n📂 Analyzing area: {area_name}")
            
            for district_dir in area_dir.iterdir():
                if not district_dir.is_dir():
                    continue
                    
                district_name = district_dir.name
                print(f"   📂 District: {district_name}")
                
                # Find INFJ files in this district
                infj_files = list(district_dir.glob("INFJ_*.md"))
                
                for infj_file in infj_files:
                    file_info = {
                        "area": area_name,
                        "district": district_name,
                        "filename": infj_file.name,
                        "full_path": str(infj_file.relative_to(self.base_path)),
                        "s3_path": f"{area_name}/{district_name}/{infj_file.name}"
                    }
                    
                    # Test Case 1: All Areas, All Districts
                    results["all_areas_all_districts"].append(file_info)
                    
                    # Test Case 2: All Areas, Central Districts only
                    if "central" in district_name.lower():
                        results["all_areas_central_districts"].append(file_info)
                    
                    # Test Case 3: Hong Kong Island Area, All Districts
                    if area_name == "hong_kong_island":
                        results["hong_kong_island_all_districts"].append(file_info)
                    
                    print(f"      📄 {infj_file.name}")
        
        # Generate summary
        results["summary"] = {
            "test_case_1_count": len(results["all_areas_all_districts"]),
            "test_case_2_count": len(results["all_areas_central_districts"]),
            "test_case_3_count": len(results["hong_kong_island_all_districts"]),
            "areas_analyzed": list(set([f["area"] for f in results["all_areas_all_districts"]])),
            "districts_with_infj": list(set([f"{f['area']}/{f['district']}" for f in results["all_areas_all_districts"]]))
        }
        
        return results
    
    def print_analysis_results(self, results: Dict[str, any]) -> None:
        """Print detailed analysis results."""
        
        print("\n" + "="*70)
        print("📊 INFJ File Analysis Results")
        print("="*70)
        
        summary = results["summary"]
        
        print(f"\n🎯 Test Case Expected Counts:")
        print(f"   1️⃣ All Areas, All Districts: {summary['test_case_1_count']} files")
        print(f"   2️⃣ All Areas, Central Districts: {summary['test_case_2_count']} files")
        print(f"   3️⃣ Hong Kong Island, All Districts: {summary['test_case_3_count']} files")
        
        print(f"\n📂 Areas with INFJ files: {len(summary['areas_analyzed'])}")
        for area in sorted(summary['areas_analyzed']):
            area_count = len([f for f in results["all_areas_all_districts"] if f["area"] == area])
            print(f"   - {area}: {area_count} files")
        
        print(f"\n📍 Districts with INFJ files: {len(summary['districts_with_infj'])}")
        for district in sorted(summary['districts_with_infj']):
            district_count = len([f for f in results["all_areas_all_districts"] if f"{f['area']}/{f['district']}" == district])
            print(f"   - {district}: {district_count} files")
        
        # Detailed breakdown for each test case
        print(f"\n📋 Test Case 1 - All Areas, All Districts ({summary['test_case_1_count']} files):")
        for file_info in sorted(results["all_areas_all_districts"], key=lambda x: x["s3_path"]):
            print(f"   📄 {file_info['s3_path']}")
        
        print(f"\n📋 Test Case 2 - All Areas, Central Districts ({summary['test_case_2_count']} files):")
        for file_info in sorted(results["all_areas_central_districts"], key=lambda x: x["s3_path"]):
            print(f"   📄 {file_info['s3_path']}")
        
        print(f"\n📋 Test Case 3 - Hong Kong Island, All Districts ({summary['test_case_3_count']} files):")
        for file_info in sorted(results["hong_kong_island_all_districts"], key=lambda x: x["s3_path"]):
            print(f"   📄 {file_info['s3_path']}")

def main():
    """Main execution function."""
    
    analyzer = INFJFileAnalyzer()
    results = analyzer.analyze_infj_files()
    
    if results:
        analyzer.print_analysis_results(results)
        
        # Save results to JSON for test script
        import json
        output_file = Path("mbti_travel_assistant_mcp/tests/infj_expected_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    main()