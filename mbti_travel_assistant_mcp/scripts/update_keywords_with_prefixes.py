#!/usr/bin/env python3
"""
Update Keywords with District and Area Prefixes

This script adds "District:" and "Area:" prefixes to the existing keywords
in all files under temp_kb_files directory for better semantic search.

Target format:
- District values get "District:" prefix
- Area values get "Area:" prefix  
- All other keywords remain unchanged
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class KeywordPrefixUpdater:
    """Update keywords with semantic prefixes for better search performance."""
    
    def __init__(self, base_path: str = "mbti_travel_assistant_mcp/temp_kb_files"):
        self.base_path = Path(base_path)
        
        # Known districts that should get "District:" prefix
        self.districts = {
            "Central District", "Tsim Sha Tsui", "Causeway Bay", "Wan Chai", 
            "Admiralty", "Sheung Wan", "Mong Kok", "Yau Ma Tei", "Lantau Island",
            "Stanley", "Aberdeen", "Pok Fu Lam", "Repulse Bay", "Mid Levels",
            "Shek O", "Sai Ying Pun", "Diamond Hill", "Lai Chi Kok", "Jordan",
            "The Peak", "Kowloon City", "Sha Tin", "Tai Po", "Tuen Mun"
        }
        
        # Known areas that should get "Area:" prefix
        self.areas = {
            "Hong Kong Island", "Kowloon", "New Territories", "Lantau Island"
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
    
    def update_keywords_line(self, keywords_line: str, district: str, area: str) -> str:
        """Update the keywords line with District: and Area: prefixes."""
        
        # Split keywords by comma
        keywords = [k.strip() for k in keywords_line.split(',')]
        updated_keywords = []
        
        for keyword in keywords:
            # Skip empty keywords
            if not keyword:
                continue
                
            # Check if this keyword matches a district
            if district and keyword == district:
                updated_keywords.append(f"District: {keyword}")
            # Check if this keyword matches an area
            elif area and keyword == area:
                updated_keywords.append(f"Area: {keyword}")
            # Keep all other keywords as-is
            else:
                updated_keywords.append(keyword)
        
        return ', '.join(updated_keywords)
    
    def update_file_keywords(self, file_path: Path) -> bool:
        """Update keywords in a single file."""
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract district and area from location section
            district, area = self.extract_location_info(content)
            
            # Find and update keywords section
            keywords_pattern = r'(## Keywords\s*\n)([^\n]+)'
            keywords_match = re.search(keywords_pattern, content)
            
            if not keywords_match:
                print(f"   ⚠️ No keywords section found in {file_path.name}")
                return False
            
            # Get current keywords line
            current_keywords = keywords_match.group(2)
            
            # Update keywords with prefixes
            updated_keywords = self.update_keywords_line(current_keywords, district, area)
            
            # Check if any changes were made
            if current_keywords == updated_keywords:
                print(f"   ✅ {file_path.name} - No changes needed")
                return True
            
            # Replace keywords in content
            updated_content = content.replace(
                keywords_match.group(0),
                f"{keywords_match.group(1)}{updated_keywords}"
            )
            
            # Write updated content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"   ✅ {file_path.name} - Updated keywords")
            print(f"      Before: {current_keywords}")
            print(f"      After:  {updated_keywords}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error updating {file_path.name}: {e}")
            return False
    
    def update_all_files(self, dry_run: bool = True) -> Dict[str, int]:
        """Update keywords in all files in the temp_kb_files directory."""
        
        print(f"🎯 {'DRY RUN: ' if dry_run else ''}Updating Keywords with District and Area Prefixes")
        print("=" * 70)
        
        if not self.base_path.exists():
            print(f"❌ Directory not found: {self.base_path}")
            return {"error": 1}
        
        # Get all .md files
        md_files = list(self.base_path.glob("*.md"))
        
        if not md_files:
            print(f"❌ No .md files found in {self.base_path}")
            return {"error": 1}
        
        print(f"📁 Found {len(md_files)} files to process")
        print()
        
        results = {"success": 0, "error": 0, "no_change": 0}
        
        for file_path in sorted(md_files):
            if dry_run:
                print(f"   🔍 WOULD UPDATE: {file_path.name}")
                results["success"] += 1
            else:
                success = self.update_file_keywords(file_path)
                if success:
                    results["success"] += 1
                else:
                    results["error"] += 1
        
        print()
        print("📊 Update Summary:")
        print(f"   ✅ Successful: {results['success']}")
        print(f"   ❌ Errors: {results['error']}")
        
        return results
    
    def preview_changes(self, limit: int = 5) -> None:
        """Preview what changes would be made to the first few files."""
        
        print("🔍 Preview of Changes (First 5 files)")
        print("=" * 50)
        
        md_files = list(self.base_path.glob("*.md"))[:limit]
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                district, area = self.extract_location_info(content)
                
                keywords_match = re.search(r'## Keywords\s*\n([^\n]+)', content)
                if keywords_match:
                    current_keywords = keywords_match.group(1)
                    updated_keywords = self.update_keywords_line(current_keywords, district, area)
                    
                    print(f"\n📄 {file_path.name}")
                    print(f"   District: {district}")
                    print(f"   Area: {area}")
                    print(f"   Before: {current_keywords}")
                    print(f"   After:  {updated_keywords}")
                    
                    if current_keywords != updated_keywords:
                        print("   🔄 WILL BE UPDATED")
                    else:
                        print("   ✅ NO CHANGE NEEDED")
                
            except Exception as e:
                print(f"   ❌ Error previewing {file_path.name}: {e}")

def main():
    """Main execution function."""
    
    print("🚀 Starting keyword prefix updater...")
    
    # Initialize updater with correct path
    updater = KeywordPrefixUpdater("mbti_travel_assistant_mcp/temp_kb_files")
    
    print(f"📁 Looking for files in: {updater.base_path}")
    print(f"📁 Path exists: {updater.base_path.exists()}")
    
    # Preview changes first
    updater.preview_changes()
    
    print("\n" + "="*70)
    
    # Dry run
    print("🔍 PERFORMING DRY RUN")
    results = updater.update_all_files(dry_run=True)
    
    if results.get("error", 0) > 0:
        print("❌ Errors detected in dry run, aborting")
        return
    
    # Ask for confirmation
    print("\n" + "="*70)
    response = input("🤔 Proceed with updating keywords? (yes/no): ").lower().strip()
    
    if response != 'yes':
        print("❌ Update cancelled by user")
        return
    
    # Execute updates
    print("\n" + "="*70)
    print("🚀 EXECUTING KEYWORD UPDATES")
    results = updater.update_all_files(dry_run=False)
    
    if results["success"] > 0:
        print(f"\n🎉 Successfully updated {results['success']} files!")
        print("\nNext steps:")
        print("1. Review the updated files")
        print("2. Upload to S3 knowledge base if satisfied")
        print("3. Run ingestion job to update vectors")
    else:
        print("❌ No files were updated")

if __name__ == "__main__":
    main()