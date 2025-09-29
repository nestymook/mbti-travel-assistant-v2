#!/usr/bin/env python3
"""
Fix Hong_Kong_Island_General and Kowloon_General Districts

This script fixes the incorrectly categorized attractions that ended up in 
"Hong_Kong_Island_General" and "Kowloon_General" folders by mapping them 
to their proper specific districts based on the attraction names and content.
"""

import os
import shutil
import json
from typing import Dict, List, Tuple
from pathlib import Path

class GeneralDistrictFixer:
    """Fix general district categorizations by mapping to specific districts."""
    
    def __init__(self, base_path: str = "mbti_travel_assistant_mcp/reorganized_kb"):
        self.base_path = Path(base_path)
        
        # Comprehensive attraction to district mapping
        self.attraction_district_mapping = {
            # Hong Kong Island attractions to specific districts
            "Victoria_Peak": "Central_District",  # The Peak is closest to Central
            "Stanley_Village_and_Beach": "Stanley",  # Create Stanley district
            "Ocean_Park": "Aberdeen",  # Ocean Park is in Aberdeen area
            "Pok_Fu_Lam_Country_Park": "Pok_Fu_Lam",  # Create Pok Fu Lam district
            "Repulse_Bay": "Repulse_Bay",  # Create Repulse Bay district
            "Lung_Fu_Shan_Country_Park": "Mid_Levels",  # Create Mid-Levels district
            "Hong_Pak_Country_Trail": "Mid_Levels",  # Also Mid-Levels area
            "Stephen_Hui_Geological_Museum_The_University_of_Hong_Kong": "Pok_Fu_Lam",
            "The_University_of_Hong_Kong_Museum_and_Art_Gallery": "Pok_Fu_Lam",
            "Aberdeen_Fishing_Village": "Aberdeen",
            "Dragon's_Back_Trail": "Shek_O",  # Create Shek O district
            "Sai_Ying_Pun": "Sai_Ying_Pun",  # Create Sai Ying Pun district
            "Stanley_Market": "Stanley",
            
            # Kowloon attractions to specific districts
            "Temple_Street_Night_Market": "Yau_Ma_Tei",  # Temple Street is in Yau Ma Tei/Jordan
            "Chi_Lin_Nunnery_and_Nan_Lian_Garden": "Diamond_Hill",  # Create Diamond Hill district
            "Jao_Tsung-I_Academy": "Lai_Chi_Kok",  # Create Lai Chi Kok district
        }
        
        # New districts to create
        self.new_districts = {
            "Stanley", "Aberdeen", "Pok_Fu_Lam", "Repulse_Bay", 
            "Mid_Levels", "Shek_O", "Sai_Ying_Pun", "Diamond_Hill", "Lai_Chi_Kok"
        }
    
    def analyze_general_folders(self) -> Dict[str, List[str]]:
        """Analyze files in Hong_Kong_Island_General and Kowloon_General folders."""
        
        print("🔍 Analyzing general district folders...")
        
        analysis = {
            "Hong_Kong_Island_General": [],
            "Kowloon_General": []
        }
        
        for folder_name in analysis.keys():
            folder_path = self.base_path / folder_name
            if folder_path.exists():
                files = list(folder_path.glob("*.md"))
                analysis[folder_name] = [f.name for f in files]
                print(f"📁 {folder_name}: {len(files)} files")
                
                # Show sample files
                for file in files[:5]:
                    print(f"   - {file}")
                if len(files) > 5:
                    print(f"   ... and {len(files) - 5} more files")
        
        return analysis
    
    def extract_attraction_name(self, filename: str) -> str:
        """Extract attraction name from filename."""
        
        # Remove .md extension
        base_name = filename.replace('.md', '')
        
        # Pattern: MBTI_District_General_Attraction_Name
        parts = base_name.split('_')
        
        if len(parts) >= 4 and parts[2] == "General":
            # Skip MBTI (0), District (1), "General" (2), take rest as attraction
            attraction_parts = parts[3:]
            return '_'.join(attraction_parts)
        
        return base_name
    
    def create_reorganization_plan(self, analysis: Dict[str, List[str]]) -> Dict[str, Dict[str, str]]:
        """Create a plan for reorganizing files from general folders."""
        
        print("\n📋 Creating reorganization plan...")
        
        reorganization_plan = {}
        
        for general_folder, files in analysis.items():
            reorganization_plan[general_folder] = {}
            
            for filename in files:
                attraction_name = self.extract_attraction_name(filename)
                
                # Get target district from mapping
                target_district = self.attraction_district_mapping.get(
                    attraction_name, 
                    "Unknown_District"
                )
                
                reorganization_plan[general_folder][filename] = target_district
                
                print(f"   📄 {filename}")
                print(f"      🎯 Attraction: {attraction_name}")
                print(f"      📍 Target District: {target_district}")
        
        return reorganization_plan
    
    def create_new_districts(self) -> bool:
        """Create new district folders if they don't exist."""
        
        print("\n📁 Creating new district folders...")
        
        created_count = 0
        
        for district in self.new_districts:
            district_path = self.base_path / district
            if not district_path.exists():
                district_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created: {district}")
                created_count += 1
            else:
                print(f"   📁 Exists: {district}")
        
        print(f"📊 Created {created_count} new district folders")
        return True
    
    def move_files(self, reorganization_plan: Dict[str, Dict[str, str]], dry_run: bool = True) -> bool:
        """Move files from general folders to specific district folders."""
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '🚀 EXECUTING:'} Moving files to correct districts...")
        
        success_count = 0
        error_count = 0
        
        for general_folder, file_mappings in reorganization_plan.items():
            general_path = self.base_path / general_folder
            
            for filename, target_district in file_mappings.items():
                if target_district == "Unknown_District":
                    print(f"   ⚠️ SKIPPING: {filename} (unknown district)")
                    continue
                
                source_path = general_path / filename
                target_path = self.base_path / target_district / filename
                
                try:
                    if dry_run:
                        print(f"   WOULD MOVE: {general_folder}/{filename} → {target_district}/{filename}")
                    else:
                        # Ensure target directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Move file
                        shutil.move(str(source_path), str(target_path))
                        print(f"   ✅ MOVED: {general_folder}/{filename} → {target_district}/{filename}")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"   ❌ ERROR moving {filename}: {e}")
                    error_count += 1
        
        print(f"\n📊 Move Summary:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0
    
    def cleanup_empty_general_folders(self, dry_run: bool = True) -> bool:
        """Remove empty general folders after moving files."""
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '🗑️ EXECUTING:'} Cleaning up empty general folders...")
        
        for folder_name in ["Hong_Kong_Island_General", "Kowloon_General"]:
            folder_path = self.base_path / folder_name
            
            if folder_path.exists():
                files = list(folder_path.glob("*"))
                
                if not files:  # Folder is empty
                    if dry_run:
                        print(f"   WOULD DELETE: {folder_name}/ (empty)")
                    else:
                        folder_path.rmdir()
                        print(f"   ✅ DELETED: {folder_name}/ (empty)")
                else:
                    print(f"   📁 KEEPING: {folder_name}/ ({len(files)} files remaining)")
        
        return True
    
    def verify_reorganization(self) -> bool:
        """Verify the reorganization was successful."""
        
        print("\n🔍 Verifying reorganization...")
        
        # Check if general folders are empty or removed
        general_folders_empty = True
        for folder_name in ["Hong_Kong_Island_General", "Kowloon_General"]:
            folder_path = self.base_path / folder_name
            if folder_path.exists():
                files = list(folder_path.glob("*.md"))
                if files:
                    print(f"   ⚠️ {folder_name} still has {len(files)} files")
                    general_folders_empty = False
                else:
                    print(f"   ✅ {folder_name} is empty")
            else:
                print(f"   ✅ {folder_name} removed")
        
        # Check new districts have files
        new_district_files = 0
        for district in self.new_districts:
            district_path = self.base_path / district
            if district_path.exists():
                files = list(district_path.glob("*.md"))
                if files:
                    print(f"   ✅ {district}: {len(files)} files")
                    new_district_files += len(files)
        
        print(f"\n📊 Verification Summary:")
        print(f"   📁 General folders empty: {'✅' if general_folders_empty else '❌'}")
        print(f"   📄 Files in new districts: {new_district_files}")
        
        return general_folders_empty and new_district_files > 0
    
    def generate_updated_mapping(self) -> Dict[str, str]:
        """Generate updated attraction-to-district mapping for the main script."""
        
        print("\n📝 Generating updated mapping for main reorganization script...")
        
        # Get all current districts
        all_districts = set()
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                all_districts.add(item.name)
        
        # Create comprehensive mapping
        updated_mapping = {}
        
        for district in sorted(all_districts):
            district_path = self.base_path / district
            files = list(district_path.glob("*.md"))
            
            for file in files:
                attraction_name = self.extract_attraction_name(file.name)
                updated_mapping[attraction_name] = district
        
        return updated_mapping

def main():
    """Main reorganization process."""
    
    print("🎯 Fix Hong Kong Island General and Kowloon General Districts")
    print("=" * 70)
    
    # Initialize fixer
    fixer = GeneralDistrictFixer()
    
    # Step 1: Analyze current general folders
    analysis = fixer.analyze_general_folders()
    
    total_files = sum(len(files) for files in analysis.values())
    if total_files == 0:
        print("✅ No files found in general folders - nothing to fix!")
        return
    
    print(f"\n📊 Found {total_files} files to reorganize")
    
    # Step 2: Create reorganization plan
    reorganization_plan = fixer.create_reorganization_plan(analysis)
    
    # Step 3: Create new district folders
    fixer.create_new_districts()
    
    # Step 4: Dry run first
    print(f"\n" + "="*70)
    print("🔍 PERFORMING DRY RUN FIRST")
    success = fixer.move_files(reorganization_plan, dry_run=True)
    
    if not success:
        print("❌ Dry run failed, aborting reorganization")
        return
    
    # Step 5: Ask for confirmation
    print(f"\n" + "="*70)
    response = input("🤔 Proceed with actual reorganization? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Reorganization cancelled by user")
        return
    
    # Step 6: Execute reorganization
    print(f"\n" + "="*70)
    print("🚀 EXECUTING REORGANIZATION")
    success = fixer.move_files(reorganization_plan, dry_run=False)
    
    if not success:
        print("❌ Reorganization failed")
        return
    
    # Step 7: Cleanup empty folders
    fixer.cleanup_empty_general_folders(dry_run=False)
    
    # Step 8: Verify reorganization
    if fixer.verify_reorganization():
        print("✅ Reorganization verified successfully")
        
        # Step 9: Generate updated mapping
        updated_mapping = fixer.generate_updated_mapping()
        
        # Save updated mapping to file
        mapping_file = Path("mbti_travel_assistant_mcp/scripts/updated_attraction_mapping.json")
        with open(mapping_file, 'w') as f:
            json.dump(updated_mapping, f, indent=2, sort_keys=True)
        
        print(f"📄 Updated mapping saved to: {mapping_file}")
        
    else:
        print("❌ Reorganization verification failed")
    
    print(f"\n🎉 General district fix complete!")
    print("Next steps:")
    print("1. Update the main reorganization script with new mappings")
    print("2. Upload reorganized files to S3 knowledge base")
    print("3. Run ingestion job to update knowledge base index")

if __name__ == "__main__":
    main()