#!/usr/bin/env python3
"""
Reorganize Knowledge Base with Hierarchical Folder Structure

This script reorganizes the knowledge base files into a hierarchical structure:
District → MBTI Type → Attraction Files

Structure:
- Central_District/
  - INFJ/
    - Central_Market.md
    - SoHo_and_Central_Art_Galleries.md
    - Tai_Kwun.md
  - ENFP/
    - Central_Market.md
    - ...
- Tsim_Sha_Tsui/
  - INFJ/
    - Hong_Kong_Cultural_Centre.md
    - Hong_Kong_Museum_of_Art.md
    - M+.md
    - Hong_Kong_Palace_Museum.md
  - ENFP/
    - ...
"""

import boto3
import json
import time
from typing import Dict, List, Tuple

class KnowledgeBaseReorganizer:
    """Reorganize knowledge base with hierarchical folder structure."""
    
    def __init__(self, bucket_name: str = "mbti-knowledgebase-209803798463-us-east-1", region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        
        # District mapping for attractions
        self.attraction_districts = {
            # Central District
            "Central_Market": "Central_District",
            "SoHo_and_Central_Art_Galleries": "Central_District", 
            "Tai_Kwun": "Central_District",
            "PMQ_Police_Married_Quarters": "Central_District",
            "Hong_Kong_House_of_Stories": "Wan_Chai",
            
            # Tsim Sha Tsui
            "Hong_Kong_Cultural_Centre": "Tsim_Sha_Tsui",
            "Hong_Kong_Museum_of_Art": "Tsim_Sha_Tsui",
            "M+": "Tsim_Sha_Tsui",
            "Hong_Kong_Palace_Museum": "Tsim_Sha_Tsui",
            
            # Admiralty
            "Pacific_Place_Rooftop_Garden": "Admiralty",
            
            # Sheung Wan
            "Man_Mo_Temple": "Sheung_Wan",
            
            # Lantau Island
            "Po_Lin_Monastery": "Lantau_Island",
            
            # Yau Ma Tei
            "Broadway_Cinematheque": "Yau_Ma_Tei"
        }
        
        # MBTI types to organize
        self.mbti_types = [
            "INFJ", "INFP", "ENFJ", "ENFP", 
            "INTJ", "INTP", "ENTJ", "ENTP",
            "ISFJ", "ISFP", "ESFJ", "ESFP",
            "ISTJ", "ISTP", "ESTJ", "ESTP"
        ]
    
    def list_current_files(self) -> List[str]:
        """List all current files in the knowledge base bucket."""
        
        print("📋 Listing current files in knowledge base...")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                print("❌ No files found in bucket")
                return []
            
            files = [obj['Key'] for obj in response['Contents']]
            print(f"✅ Found {len(files)} files")
            
            # Show current structure
            print("\n📁 Current file structure:")
            for file in sorted(files)[:20]:  # Show first 20 files
                print(f"   {file}")
            if len(files) > 20:
                print(f"   ... and {len(files) - 20} more files")
            
            return files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def parse_filename(self, filename: str) -> Tuple[str, str, str]:
        """Parse filename to extract MBTI type, attraction name, and district."""
        
        # Remove .md extension
        base_name = filename.replace('.md', '').replace('.txt', '')
        
        # Extract MBTI type (first 4 characters)
        if '_' in base_name and len(base_name.split('_')[0]) == 4:
            mbti_type = base_name.split('_')[0]
            attraction_name = '_'.join(base_name.split('_')[1:])
        else:
            # Fallback for files without MBTI prefix
            mbti_type = "UNKNOWN"
            attraction_name = base_name
        
        # Get district from mapping
        district = self.attraction_districts.get(attraction_name, "Unknown_District")
        
        return mbti_type, attraction_name, district
    
    def create_new_structure_plan(self, files: List[str]) -> Dict[str, List[str]]:
        """Create a plan for the new folder structure."""
        
        print("\n🗂️ Creating reorganization plan...")
        
        structure_plan = {}
        
        for file in files:
            if not file.endswith(('.md', '.txt')):
                continue
                
            mbti_type, attraction_name, district = self.parse_filename(file)
            
            # Create new path: District/MBTI_Type/Attraction.md
            new_path = f"{district}/{mbti_type}/{attraction_name}.md"
            
            if new_path not in structure_plan:
                structure_plan[new_path] = []
            structure_plan[new_path].append(file)
        
        # Display plan
        print(f"\n📊 Reorganization Plan ({len(structure_plan)} new locations):")
        
        districts = {}
        for new_path in structure_plan.keys():
            district = new_path.split('/')[0]
            if district not in districts:
                districts[district] = {}
            
            mbti_type = new_path.split('/')[1]
            if mbti_type not in districts[district]:
                districts[district][mbti_type] = 0
            districts[district][mbti_type] += 1
        
        for district, mbti_counts in sorted(districts.items()):
            print(f"\n📁 {district}/")
            for mbti_type, count in sorted(mbti_counts.items()):
                print(f"   └── {mbti_type}/ ({count} files)")
        
        return structure_plan
    
    def copy_files_to_new_structure(self, structure_plan: Dict[str, List[str]], dry_run: bool = True) -> bool:
        """Copy files to new folder structure."""
        
        print(f"\n{'🔍 DRY RUN:' if dry_run else '🚀 EXECUTING:'} Reorganizing files...")
        
        success_count = 0
        error_count = 0
        
        for new_path, old_files in structure_plan.items():
            for old_file in old_files:
                try:
                    if dry_run:
                        print(f"   WOULD COPY: {old_file} → {new_path}")
                    else:
                        # Copy file to new location
                        copy_source = {'Bucket': self.bucket_name, 'Key': old_file}
                        self.s3_client.copy_object(
                            CopySource=copy_source,
                            Bucket=self.bucket_name,
                            Key=new_path
                        )
                        print(f"   ✅ COPIED: {old_file} → {new_path}")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"   ❌ ERROR copying {old_file}: {e}")
                    error_count += 1
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0
    
    def cleanup_old_files(self, old_files: List[str], dry_run: bool = True) -> bool:
        """Remove old files after successful reorganization."""
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would delete {len(old_files)} old files")
            return True
        
        print(f"\n🗑️ Cleaning up {len(old_files)} old files...")
        
        success_count = 0
        error_count = 0
        
        for file in old_files:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file)
                print(f"   ✅ DELETED: {file}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ ERROR deleting {file}: {e}")
                error_count += 1
        
        print(f"\n📊 Cleanup Summary:")
        print(f"   ✅ Deleted: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return error_count == 0
    
    def verify_new_structure(self) -> bool:
        """Verify the new folder structure is correct."""
        
        print("\n🔍 Verifying new folder structure...")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                print("❌ No files found after reorganization")
                return False
            
            files = [obj['Key'] for obj in response['Contents']]
            
            # Analyze new structure
            districts = {}
            for file in files:
                if '/' in file:  # New structured files
                    parts = file.split('/')
                    if len(parts) >= 3:  # District/MBTI/File.md
                        district = parts[0]
                        mbti_type = parts[1]
                        
                        if district not in districts:
                            districts[district] = {}
                        if mbti_type not in districts[district]:
                            districts[district][mbti_type] = 0
                        districts[district][mbti_type] += 1
            
            print(f"✅ New structure verified:")
            print(f"   📁 Districts: {len(districts)}")
            
            total_files = 0
            for district, mbti_counts in sorted(districts.items()):
                district_total = sum(mbti_counts.values())
                total_files += district_total
                print(f"   📁 {district}: {len(mbti_counts)} MBTI types, {district_total} files")
            
            print(f"   📄 Total organized files: {total_files}")
            
            return len(districts) > 0 and total_files > 0
            
        except Exception as e:
            print(f"❌ Error verifying structure: {e}")
            return False

def main():
    """Main reorganization process."""
    
    print("🎯 Knowledge Base Hierarchical Reorganization")
    print("=" * 60)
    print("Creating structure: District → MBTI Type → Attraction Files")
    
    # Initialize reorganizer
    reorganizer = KnowledgeBaseReorganizer()
    
    # Step 1: List current files
    current_files = reorganizer.list_current_files()
    if not current_files:
        print("❌ No files to reorganize")
        return
    
    # Step 2: Create reorganization plan
    structure_plan = reorganizer.create_new_structure_plan(current_files)
    if not structure_plan:
        print("❌ Could not create reorganization plan")
        return
    
    # Step 3: Dry run first
    print(f"\n" + "="*60)
    print("🔍 PERFORMING DRY RUN FIRST")
    success = reorganizer.copy_files_to_new_structure(structure_plan, dry_run=True)
    
    if not success:
        print("❌ Dry run failed, aborting reorganization")
        return
    
    # Step 4: Ask for confirmation
    print(f"\n" + "="*60)
    response = input("🤔 Proceed with actual reorganization? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Reorganization cancelled by user")
        return
    
    # Step 5: Execute reorganization
    print(f"\n" + "="*60)
    print("🚀 EXECUTING REORGANIZATION")
    success = reorganizer.copy_files_to_new_structure(structure_plan, dry_run=False)
    
    if not success:
        print("❌ Reorganization failed")
        return
    
    # Step 6: Verify new structure
    if reorganizer.verify_new_structure():
        print("✅ New structure verified successfully")
        
        # Step 7: Cleanup old files (optional)
        cleanup_response = input("🗑️ Delete old files? (yes/no): ").lower().strip()
        if cleanup_response == 'yes':
            old_files = [f for f in current_files if not any(f.startswith(d) for d in ['Central_District/', 'Tsim_Sha_Tsui/', 'Admiralty/', 'Sheung_Wan/', 'Lantau_Island/', 'Yau_Ma_Tei/', 'Wan_Chai/'])]
            reorganizer.cleanup_old_files(old_files, dry_run=False)
    else:
        print("❌ Structure verification failed")
    
    print(f"\n🎉 Reorganization complete!")
    print("Next steps:")
    print("1. Run ingestion job to update knowledge base index")
    print("2. Test folder-based search strategies")
    print("3. Verify improved search performance")

if __name__ == "__main__":
    main()