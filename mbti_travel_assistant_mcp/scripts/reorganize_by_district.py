#!/usr/bin/env python3
"""
Reorganize Knowledge Base Files by District

This script:
1. Downloads all files from S3 mbti_individual folder
2. Reads each MD file to extract district information
3. Creates district-based folder structure
4. Reorganizes files as <MBTI>_<District>_<Tourist_Spot>.md
5. Uploads the reorganized structure back to S3
"""

import boto3
import os
import re
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class DistrictReorganizer:
    """Reorganize knowledge base files by district."""
    
    def __init__(self, bucket_name: str = "mbti-knowledgebase-209803798463-us-east-1", region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
        # Local directories for processing
        self.download_dir = Path("mbti_travel_assistant_mcp/temp_kb_files")
        self.reorganized_dir = Path("mbti_travel_assistant_mcp/reorganized_kb")
        
        # Create directories
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.reorganized_dir.mkdir(parents=True, exist_ok=True)
        
        # District mapping and normalization
        self.district_mapping = {
            # Common variations to standardized names
            "central": "Central_District",
            "central district": "Central_District", 
            "central, hong kong": "Central_District",
            "tsim sha tsui": "Tsim_Sha_Tsui",
            "tsim sha tsui, kowloon": "Tsim_Sha_Tsui",
            "admiralty": "Admiralty",
            "wan chai": "Wan_Chai",
            "sheung wan": "Sheung_Wan",
            "lantau island": "Lantau_Island",
            "yau ma tei": "Yau_Ma_Tei",
            "mong kok": "Mong_Kok",
            "causeway bay": "Causeway_Bay",
            "kowloon": "Kowloon_General",
            "hong kong island": "Hong_Kong_Island_General"
        }
        
        self.file_analysis = {}
    
    def download_mbti_individual_files(self) -> List[str]:
        """Download all files from mbti_individual folder."""
        
        print("📥 Downloading files from S3 mbti_individual folder...")
        
        try:
            # List objects in mbti_individual folder
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="mbti_individual/"
            )
            
            if 'Contents' not in response:
                print("❌ No files found in mbti_individual folder")
                return []
            
            downloaded_files = []
            
            for obj in response['Contents']:
                key = obj['Key']
                filename = key.split('/')[-1]
                
                # Only download .md files
                if not filename.endswith('.md'):
                    continue
                
                local_path = self.download_dir / filename
                
                print(f"   Downloading: {key}")
                self.s3_client.download_file(self.bucket_name, key, str(local_path))
                downloaded_files.append(str(local_path))
            
            print(f"✅ Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error downloading files: {e}")
            return []
    
    def extract_district_from_file(self, file_path: str) -> Optional[str]:
        """Extract district information from MD file content."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for district patterns in the content
            district_patterns = [
                r'District[:\s]+([^,\n]+)',
                r'Location[:\s]+([^,\n]+)',
                r'Address[:\s]+([^,\n]+)',
                r'Area[:\s]+([^,\n]+)',
                r'Region[:\s]+([^,\n]+)'
            ]
            
            for pattern in district_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    district_text = matches[0].strip()
                    
                    # Normalize district name
                    normalized = self.normalize_district_name(district_text)
                    if normalized:
                        return normalized
            
            # If no explicit district found, try to infer from attraction name
            filename = Path(file_path).stem
            if '_' in filename:
                attraction_name = '_'.join(filename.split('_')[1:])  # Remove MBTI prefix
                inferred_district = self.infer_district_from_attraction(attraction_name)
                if inferred_district:
                    return inferred_district
            
            return "Unknown_District"
            
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            return "Unknown_District"
    
    def normalize_district_name(self, district_text: str) -> Optional[str]:
        """Normalize district name to standard format."""
        
        district_lower = district_text.lower().strip()
        
        # Direct mapping
        if district_lower in self.district_mapping:
            return self.district_mapping[district_lower]
        
        # Partial matching
        for key, value in self.district_mapping.items():
            if key in district_lower or district_lower in key:
                return value
        
        # Extract key district names
        if 'central' in district_lower:
            return "Central_District"
        elif 'tsim sha tsui' in district_lower or 'tst' in district_lower:
            return "Tsim_Sha_Tsui"
        elif 'admiralty' in district_lower:
            return "Admiralty"
        elif 'wan chai' in district_lower:
            return "Wan_Chai"
        elif 'sheung wan' in district_lower:
            return "Sheung_Wan"
        elif 'lantau' in district_lower:
            return "Lantau_Island"
        elif 'yau ma tei' in district_lower:
            return "Yau_Ma_Tei"
        elif 'mong kok' in district_lower:
            return "Mong_Kok"
        elif 'causeway bay' in district_lower:
            return "Causeway_Bay"
        
        return None
    
    def infer_district_from_attraction(self, attraction_name: str) -> Optional[str]:
        """Infer district from attraction name using known mappings."""
        
        # Known attraction-district mappings
        attraction_districts = {
            "central_market": "Central_District",
            "soho_and_central_art_galleries": "Central_District",
            "tai_kwun": "Central_District",
            "pmq_police_married_quarters": "Central_District",
            "hong_kong_cultural_centre": "Tsim_Sha_Tsui",
            "hong_kong_museum_of_art": "Tsim_Sha_Tsui",
            "m+": "Tsim_Sha_Tsui",
            "hong_kong_palace_museum": "Tsim_Sha_Tsui",
            "pacific_place_rooftop_garden": "Admiralty",
            "hong_kong_house_of_stories": "Wan_Chai",
            "man_mo_temple": "Sheung_Wan",
            "po_lin_monastery": "Lantau_Island",
            "broadway_cinematheque": "Yau_Ma_Tei"
        }
        
        attraction_lower = attraction_name.lower()
        
        for key, district in attraction_districts.items():
            if key in attraction_lower or attraction_lower in key:
                return district
        
        return None
    
    def analyze_all_files(self, file_paths: List[str]) -> Dict[str, Dict]:
        """Analyze all downloaded files to extract district information."""
        
        print("\n🔍 Analyzing files to extract district information...")
        
        analysis_results = {}
        district_counts = {}
        
        for file_path in file_paths:
            filename = Path(file_path).stem
            
            # Extract MBTI type and attraction name
            if '_' in filename:
                parts = filename.split('_')
                mbti_type = parts[0]
                attraction_name = '_'.join(parts[1:])
            else:
                mbti_type = "UNKNOWN"
                attraction_name = filename
            
            # Extract district
            district = self.extract_district_from_file(file_path)
            
            analysis_results[filename] = {
                'original_path': file_path,
                'mbti_type': mbti_type,
                'attraction_name': attraction_name,
                'district': district,
                'new_filename': f"{mbti_type}_{district}_{attraction_name}.md"
            }
            
            # Count districts
            if district not in district_counts:
                district_counts[district] = 0
            district_counts[district] += 1
            
            print(f"   {filename} → {district} ({mbti_type})")
        
        print(f"\n📊 District Analysis:")
        for district, count in sorted(district_counts.items()):
            print(f"   {district}: {count} files")
        
        self.file_analysis = analysis_results
        return analysis_results
    
    def create_district_structure(self, analysis: Dict[str, Dict]) -> bool:
        """Create district-based folder structure and reorganize files."""
        
        print(f"\n🗂️ Creating district-based folder structure...")
        
        try:
            # Group files by district
            districts = {}
            for filename, info in analysis.items():
                district = info['district']
                if district not in districts:
                    districts[district] = []
                districts[district].append(info)
            
            # Create district folders and copy files
            for district, files in districts.items():
                district_dir = self.reorganized_dir / district
                district_dir.mkdir(exist_ok=True)
                
                print(f"\n📁 Creating {district}/ ({len(files)} files)")
                
                for file_info in files:
                    original_path = Path(file_info['original_path'])
                    new_filename = file_info['new_filename']
                    new_path = district_dir / new_filename
                    
                    # Copy file with new name
                    with open(original_path, 'r', encoding='utf-8') as src:
                        content = src.read()
                    
                    with open(new_path, 'w', encoding='utf-8') as dst:
                        dst.write(content)
                    
                    print(f"   ✅ {original_path.name} → {district}/{new_filename}")
            
            print(f"\n✅ Created {len(districts)} district folders")
            return True
            
        except Exception as e:
            print(f"❌ Error creating district structure: {e}")
            return False
    
    def upload_reorganized_structure(self, dry_run: bool = True) -> bool:
        """Upload the reorganized structure back to S3."""
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '🚀 UPLOADING:'} Reorganized structure to S3...")
        
        try:
            upload_count = 0
            
            for district_dir in self.reorganized_dir.iterdir():
                if not district_dir.is_dir():
                    continue
                
                district_name = district_dir.name
                print(f"\n📁 Processing {district_name}/")
                
                for file_path in district_dir.glob("*.md"):
                    s3_key = f"districts/{district_name}/{file_path.name}"
                    
                    if dry_run:
                        print(f"   WOULD UPLOAD: {file_path.name} → {s3_key}")
                    else:
                        self.s3_client.upload_file(str(file_path), self.bucket_name, s3_key)
                        print(f"   ✅ UPLOADED: {file_path.name} → {s3_key}")
                    
                    upload_count += 1
            
            print(f"\n📊 {'Would upload' if dry_run else 'Uploaded'} {upload_count} files")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading files: {e}")
            return False
    
    def generate_reorganization_report(self) -> str:
        """Generate a detailed reorganization report."""
        
        report_path = "mbti_travel_assistant_mcp/data/district_reorganization_report.json"
        
        report_data = {
            'reorganization_timestamp': __import__('datetime').datetime.now().isoformat(),
            'total_files_processed': len(self.file_analysis),
            'districts_created': len(set(info['district'] for info in self.file_analysis.values())),
            'file_mappings': self.file_analysis,
            'district_summary': {}
        }
        
        # Create district summary
        for filename, info in self.file_analysis.items():
            district = info['district']
            if district not in report_data['district_summary']:
                report_data['district_summary'][district] = {
                    'file_count': 0,
                    'mbti_types': set(),
                    'attractions': []
                }
            
            report_data['district_summary'][district]['file_count'] += 1
            report_data['district_summary'][district]['mbti_types'].add(info['mbti_type'])
            report_data['district_summary'][district]['attractions'].append(info['attraction_name'])
        
        # Convert sets to lists for JSON serialization
        for district_info in report_data['district_summary'].values():
            district_info['mbti_types'] = list(district_info['mbti_types'])
        
        # Save report
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Reorganization report saved to: {report_path}")
        return report_path
    
    def cleanup_temp_files(self):
        """Clean up temporary downloaded files."""
        
        print(f"\n🧹 Cleaning up temporary files...")
        
        try:
            import shutil
            if self.download_dir.exists():
                shutil.rmtree(self.download_dir)
                print(f"   ✅ Removed {self.download_dir}")
            
            if self.reorganized_dir.exists():
                shutil.rmtree(self.reorganized_dir)
                print(f"   ✅ Removed {self.reorganized_dir}")
                
        except Exception as e:
            print(f"   ⚠️ Error cleaning up: {e}")

def main():
    """Main reorganization process."""
    
    print("🎯 Knowledge Base District-Based Reorganization")
    print("=" * 60)
    print("Process: Download → Analyze → Reorganize → Upload")
    
    # Initialize reorganizer
    reorganizer = DistrictReorganizer()
    
    try:
        # Step 1: Download files
        downloaded_files = reorganizer.download_mbti_individual_files()
        if not downloaded_files:
            print("❌ No files to process")
            return
        
        # Step 2: Analyze files for district information
        analysis = reorganizer.analyze_all_files(downloaded_files)
        if not analysis:
            print("❌ Failed to analyze files")
            return
        
        # Step 3: Create district-based structure
        success = reorganizer.create_district_structure(analysis)
        if not success:
            print("❌ Failed to create district structure")
            return
        
        # Step 4: Generate report
        report_path = reorganizer.generate_reorganization_report()
        
        # Step 5: Dry run upload
        print(f"\n" + "="*60)
        print("🔍 PERFORMING DRY RUN UPLOAD")
        reorganizer.upload_reorganized_structure(dry_run=True)
        
        # Step 6: Ask for confirmation
        print(f"\n" + "="*60)
        response = input("🤔 Proceed with actual upload to S3? (yes/no): ").lower().strip()
        
        if response == 'yes':
            print(f"\n🚀 UPLOADING TO S3")
            success = reorganizer.upload_reorganized_structure(dry_run=False)
            
            if success:
                print("✅ Upload completed successfully!")
                
                # Ask about cleanup
                cleanup_response = input("🧹 Clean up temporary files? (yes/no): ").lower().strip()
                if cleanup_response == 'yes':
                    reorganizer.cleanup_temp_files()
            else:
                print("❌ Upload failed")
        else:
            print("❌ Upload cancelled by user")
        
        print(f"\n🎉 District reorganization process completed!")
        print(f"📋 Check report: {report_path}")
        print("\nNext steps:")
        print("1. Run knowledge base ingestion job")
        print("2. Test district-based search strategies")
        print("3. Verify improved search performance")
        
    except Exception as e:
        print(f"❌ Reorganization failed: {e}")
    finally:
        # Always offer cleanup
        cleanup_response = input("\n🧹 Clean up temporary files? (yes/no): ").lower().strip()
        if cleanup_response == 'yes':
            reorganizer.cleanup_temp_files()

if __name__ == "__main__":
    main()