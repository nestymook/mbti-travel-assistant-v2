#!/usr/bin/env python3
"""
Reorganize Files by Area and District Structure

This script reorganizes all files in temp_kb_files into a hierarchical structure:
Area → District → Files

Example:
- kowloon/tsim_sha_tsui/ENFJ_Avenue_of_Stars.md
- hong_kong_island/central_district/INFJ_Central_Market.md
- new_territories/sha_tin/INTJ_Art_Museum_The_Chinese_University_of_Hong_Kong.md
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

class AreaDistrictReorganizer:
    """Reorganize files by area and district structure."""
    
    def __init__(self, source_path: str = "mbti_travel_assistant_mcp/temp_kb_files"):
        self.source_path = Path(source_path)
        self.target_path = Path("mbti_travel_assistant_mcp/organized_kb")
        
        # Area name normalization (for folder names)
        self.area_mapping = {
            "Hong Kong Island": "hong_kong_island",
            "Kowloon": "kowloon", 
            "New Territories": "new_territories",
            "Islands": "islands",
            "Lantau": "islands"  # Lantau is part of Islands district
        }
        
        # District name normalization (for folder names)
        self.district_mapping = {
            "Central District": "central_district",
            "Tsim Sha Tsui": "tsim_sha_tsui",
            "Causeway Bay": "causeway_bay",
            "Wan Chai": "wan_chai",
            "Admiralty": "admiralty",
            "Sheung Wan": "sheung_wan",
            "Mong Kok": "mong_kok",
            "Yau Ma Tei": "yau_ma_tei",
            "The Peak": "the_peak",
            "Stanley": "stanley",
            "Aberdeen": "aberdeen",
            "Pok Fu Lam": "pok_fu_lam",
            "Repulse Bay": "repulse_bay",
            "Mid-Levels": "mid_levels",
            "Shek O": "shek_o",
            "Sai Ying Pun": "sai_ying_pun",
            "Western District": "western_district",
            "Quarry Bay": "quarry_bay",
            "Wong Chuk Hang": "wong_chuk_hang",
            "Wong Tai Sin": "wong_tai_sin",
            "Diamond Hill": "diamond_hill",
            "Jordan": "jordan",
            "Sham Shui Po": "sham_shui_po",
            "Lai Chi Kok": "lai_chi_kok",
            "Sha Tin": "sha_tin",
            "Tai Po": "tai_po",
            "Tsuen Wan": "tsuen_wan",
            "Sai Kung": "sai_kung",
            "Lantau": "lantau",
            "Location": "unknown_location"  # Handle edge cases
        }
    
    def extract_location_info(self, content: str) -> Tuple[str, str]:
        """Extract district and area from the Location Information section."""
        
        district = ""
        area = ""
        
        # Find Location Information section
        location_match = re.search(r'## Location Information.*?(?=##|$)', content, re.DOTALL)
        if location_match:
            location_section = location_match.group(0)
            
            # Extract District
            district_match = re.search(r'\*\*District:\*\*\s*([^\n]+)', location_section)
            if district_match:
                district = district_match.group(1).strip()
            
            # Extract Area
            area_match = re.search(r'\*\*Area:\*\*\s*([^\n]+)', location_section)
            if area_match:
                area = area_match.group(1).strip()
        
        return district, area
    
    def normalize_name(self, name: str, mapping: Dict[str, str]) -> str:
        """Normalize area/district name for folder structure."""
        
        # Direct mapping
        if name in mapping:
            return mapping[name]
        
        # Fallback: convert to lowercase with underscores
        normalized = name.lower().replace(' ', '_').replace('-', '_')
        normalized = re.sub(r'[^\w_]', '', normalized)  # Remove special characters
        
        return normalized or "unknown"
    
    def create_folder_structure(self, files_info: List[Tuple[Path, str, str]]) -> Dict[str, List[Path]]:
        """Create the folder structure mapping."""
        
        structure = {}
        
        for file_path, district, area in files_info:
            # Normalize area and district names
            area_folder = self.normalize_name(area, self.area_mapping)
            district_folder = self.normalize_name(district, self.district_mapping)
            
            # Create folder path
            folder_path = f"{area_folder}/{district_folder}"
            
            if folder_path not in structure:
                structure[folder_path] = []
            
            structure[folder_path].append(file_path)
        
        return structure
    
    def analyze_files(self) -> List[Tuple[Path, str, str]]:
        """Analyze all files and extract location information."""
        
        print("🔍 Analyzing files for location information...")
        
        if not self.source_path.exists():
            print(f"❌ Source directory not found: {self.source_path}")
            return []
        
        md_files = list(self.source_path.glob("*.md"))
        files_info = []
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                district, area = self.extract_location_info(content)
                files_info.append((file_path, district, area))
                
            except Exception as e:
                print(f"   ⚠️ Error reading {file_path.name}: {e}")
                files_info.append((file_path, "Unknown", "Unknown"))
        
        print(f"✅ Analyzed {len(files_info)} files")
        return files_info
    
    def preview_structure(self, structure: Dict[str, List[Path]]) -> None:
        """Preview the folder structure that will be created."""
        
        print("\n📁 Folder Structure Preview:")
        print("=" * 50)
        
        total_files = 0
        for folder_path, files in sorted(structure.items()):
            area, district = folder_path.split('/')
            print(f"\n📂 {area}/")
            print(f"   └── 📂 {district}/ ({len(files)} files)")
            
            # Show first few files as examples
            for file in files[:3]:
                print(f"       └── 📄 {file.name}")
            if len(files) > 3:
                print(f"       └── ... and {len(files) - 3} more files")
            
            total_files += len(files)
        
        print(f"\n📊 Summary:")
        print(f"   📂 Total folders: {len(structure)}")
        print(f"   📄 Total files: {total_files}")
    
    def create_directories(self, structure: Dict[str, List[Path]]) -> bool:
        """Create the directory structure."""
        
        print("\n📁 Creating directory structure...")
        
        try:
            # Create base target directory
            self.target_path.mkdir(parents=True, exist_ok=True)
            
            # Create all subdirectories
            for folder_path in structure.keys():
                full_path = self.target_path / folder_path
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created: {folder_path}/")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating directories: {e}")
            return False
    
    def move_files(self, structure: Dict[str, List[Path]], dry_run: bool = True) -> bool:
        """Move files to their new locations."""
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '🚀 EXECUTING:'} Moving files to new structure...")
        
        success_count = 0
        error_count = 0
        
        for folder_path, files in structure.items():
            target_folder = self.target_path / folder_path
            
            for file_path in files:
                target_file = target_folder / file_path.name
                
                try:
                    if dry_run:
                        print(f"   WOULD MOVE: {file_path.name} → {folder_path}/{file_path.name}")
                    else:
                        shutil.copy2(file_path, target_file)
                        print(f"   ✅ MOVED: {file_path.name} → {folder_path}/{file_path.name}")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"   ❌ ERROR moving {file_path.name}: {e}")
                    error_count += 1
        
        print(f"\n📊 Move Summary:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0
    
    def verify_structure(self) -> bool:
        """Verify the new structure was created correctly."""
        
        print("\n🔍 Verifying new structure...")
        
        if not self.target_path.exists():
            print("❌ Target directory does not exist")
            return False
        
        # Count files in new structure
        total_files = 0
        area_count = 0
        district_count = 0
        
        for area_dir in self.target_path.iterdir():
            if area_dir.is_dir():
                area_count += 1
                print(f"📂 {area_dir.name}/")
                
                for district_dir in area_dir.iterdir():
                    if district_dir.is_dir():
                        district_count += 1
                        files = list(district_dir.glob("*.md"))
                        total_files += len(files)
                        print(f"   └── 📂 {district_dir.name}/ ({len(files)} files)")
        
        print(f"\n📊 Verification Summary:")
        print(f"   📂 Areas: {area_count}")
        print(f"   📂 Districts: {district_count}")
        print(f"   📄 Total files: {total_files}")
        
        return total_files > 0
    
    def reorganize(self, dry_run: bool = True) -> bool:
        """Main reorganization process."""
        
        print("🎯 Reorganizing Files by Area and District Structure")
        print("=" * 60)
        
        # Step 1: Analyze files
        files_info = self.analyze_files()
        if not files_info:
            print("❌ No files to reorganize")
            return False
        
        # Step 2: Create folder structure mapping
        structure = self.create_folder_structure(files_info)
        
        # Step 3: Preview structure
        self.preview_structure(structure)
        
        if dry_run:
            print(f"\n🔍 DRY RUN COMPLETE")
            return True
        
        # Step 4: Create directories
        if not self.create_directories(structure):
            return False
        
        # Step 5: Move files
        if not self.move_files(structure, dry_run=False):
            return False
        
        # Step 6: Verify structure
        return self.verify_structure()

def main():
    """Main execution function."""
    
    # Initialize reorganizer
    reorganizer = AreaDistrictReorganizer()
    
    # Dry run first
    print("🔍 PERFORMING DRY RUN")
    success = reorganizer.reorganize(dry_run=True)
    
    if not success:
        print("❌ Dry run failed, aborting reorganization")
        return
    
    # Ask for confirmation
    print("\n" + "="*60)
    response = input("🤔 Proceed with actual reorganization? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Reorganization cancelled by user")
        return
    
    # Execute reorganization
    print("\n" + "="*60)
    print("🚀 EXECUTING REORGANIZATION")
    success = reorganizer.reorganize(dry_run=False)
    
    if success:
        print(f"\n🎉 Reorganization complete!")
        print("Files are now organized in: mbti_travel_assistant_mcp/organized_kb/")
        print("\nStructure:")
        print("  area_name/")
        print("    └── district_name/")
        print("        └── MBTI_Attraction_Name.md")
        print("\nNext steps:")
        print("1. Review the organized structure")
        print("2. Upload to S3 knowledge base if satisfied")
        print("3. Run ingestion job to update vectors")
    else:
        print("❌ Reorganization failed")

if __name__ == "__main__":
    main()