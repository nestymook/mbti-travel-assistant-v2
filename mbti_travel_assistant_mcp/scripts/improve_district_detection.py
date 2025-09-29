#!/usr/bin/env python3
"""
Improve District Detection for Unknown_District Files

This script improves the district detection logic for files that were 
categorized as Unknown_District in the previous reorganization.
"""

import boto3
import os
import re
from typing import Dict, List, Optional
from pathlib import Path

class ImprovedDistrictDetector:
    """Improved district detection for problematic files."""
    
    def __init__(self):
        # Enhanced attraction-district mappings based on the reorganization output
        self.enhanced_mappings = {
            # University and Academic Institutions
            "art_museum_the_chinese_university_of_hong_kong": "Sha_Tin",  # CUHK is in Sha Tin
            "hong_kong_heritage_museum": "Sha_Tin",  # Located in Sha Tin
            "hong_kong_science_and_technology_parks_corporation": "Sha_Tin",  # Science Park in Sha Tin
            "hong_kong_institute_of_education_for_sustainable_development": "Tai_Po",  # EdUHK in Tai Po
            "hong_kong_museum_of_education": "Tai_Po",  # Also in Tai Po area
            
            # Sports and Recreation
            "blue_sky_sports_club_sha_ha_center": "Sha_Tin",  # Sha Ha is in Sha Tin area
            
            # Nature Trails and Parks
            "pineapple_dam_nature_trail": "Tai_Po",  # Pineapple Dam is in Tai Po
            "sai_kung": "Sai_Kung",  # Sai Kung is its own district
            "tai_mo_shan": "Tai_Po",  # Tai Mo Shan Country Park spans Tai Po area
        }
        
        # District name standardization
        self.district_standards = {
            "sha_tin": "Sha_Tin",
            "shatin": "Sha_Tin", 
            "tai_po": "Tai_Po",
            "taipo": "Tai_Po",
            "sai_kung": "Sai_Kung",
            "saikung": "Sai_Kung",
            "new_territories": "New_Territories_General"
        }
    
    def detect_district_from_filename(self, filename: str) -> Optional[str]:
        """Enhanced district detection from filename."""
        
        # Remove MBTI prefix and get attraction name
        if '_' in filename:
            parts = filename.split('_')
            attraction_name = '_'.join(parts[1:]).lower()
        else:
            attraction_name = filename.lower()
        
        # Remove file extension
        attraction_name = attraction_name.replace('.md', '').replace('.txt', '')
        
        # Check enhanced mappings
        for key, district in self.enhanced_mappings.items():
            if key in attraction_name or attraction_name in key:
                return district
        
        # Check for district names in the attraction name
        for key, district in self.district_standards.items():
            if key in attraction_name:
                return district
        
        return None
    
    def analyze_unknown_district_files(self) -> Dict[str, str]:
        """Analyze the files that were categorized as Unknown_District."""
        
        # Files that were categorized as Unknown_District from the reorganization output
        unknown_files = [
            "ESTJ_Art_Museum_The_Chinese_University_of_Hong_Kong.md",
            "ESTJ_Hong_Kong_Heritage_Museum.md", 
            "INTJ_Art_Museum_The_Chinese_University_of_Hong_Kong.md",
            "INTJ_Hong_Kong_Heritage_Museum.md",
            "INTJ_Hong_Kong_Science_and_Technology_Parks_Corporation.md",
            "INTP_Hong_Kong_Institute_of_Education_for_Sustainable_Development.md",
            "ISFP_Art_Museum_The_Chinese_University_of_Hong_Kong.md",
            "ISFP_Blue_Sky_Sports_Club_Sha_Ha_Center.md",
            "ISTJ_Hong_Kong_Museum_of_Education.md",
            "ISTJ_Pineapple_Dam_Nature_Trail.md",
            "ISTP_Sai_Kung.md",
            "ISTP_Tai_Mo_Shan.md"
        ]
        
        print("🔍 Analyzing Unknown_District Files with Enhanced Detection")
        print("=" * 60)
        
        improved_mappings = {}
        
        for filename in unknown_files:
            detected_district = self.detect_district_from_filename(filename)
            
            if detected_district:
                improved_mappings[filename] = detected_district
                print(f"✅ {filename} → {detected_district}")
            else:
                improved_mappings[filename] = "New_Territories_General"  # Default fallback
                print(f"⚠️ {filename} → New_Territories_General (fallback)")
        
        return improved_mappings
    
    def generate_corrected_structure(self) -> Dict[str, List[str]]:
        """Generate corrected district structure."""
        
        improved_mappings = self.analyze_unknown_district_files()
        
        # Group by district
        district_structure = {}
        
        for filename, district in improved_mappings.items():
            if district not in district_structure:
                district_structure[district] = []
            district_structure[district].append(filename)
        
        print(f"\n📊 Corrected District Structure:")
        for district, files in sorted(district_structure.items()):
            print(f"   {district}: {len(files)} files")
            for file in files:
                print(f"     - {file}")
        
        return district_structure
    
    def create_updated_reorganization_script(self):
        """Create an updated reorganization script with improved district detection."""
        
        print(f"\n🔧 Creating Updated Reorganization Script...")
        
        # Read the original script
        original_script_path = "mbti_travel_assistant_mcp/scripts/reorganize_by_district.py"
        
        try:
            with open(original_script_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Create improved version with enhanced mappings
            improved_content = original_content.replace(
                '# Known attraction-district mappings',
                '''# Enhanced attraction-district mappings (improved version)
        attraction_districts = {
            # Central District
            "central_market": "Central_District",
            "soho_and_central_art_galleries": "Central_District",
            "tai_kwun": "Central_District",
            "pmq_police_married_quarters": "Central_District",
            
            # Tsim Sha Tsui
            "hong_kong_cultural_centre": "Tsim_Sha_Tsui",
            "hong_kong_museum_of_art": "Tsim_Sha_Tsui",
            "m+": "Tsim_Sha_Tsui",
            "hong_kong_palace_museum": "Tsim_Sha_Tsui",
            
            # Other Districts
            "pacific_place_rooftop_garden": "Admiralty",
            "hong_kong_house_of_stories": "Wan_Chai",
            "man_mo_temple": "Sheung_Wan",
            "po_lin_monastery": "Lantau_Island",
            "broadway_cinematheque": "Yau_Ma_Tei",
            
            # Enhanced mappings for previously unknown districts
            "art_museum_the_chinese_university_of_hong_kong": "Sha_Tin",
            "hong_kong_heritage_museum": "Sha_Tin",
            "hong_kong_science_and_technology_parks_corporation": "Sha_Tin", 
            "hong_kong_institute_of_education_for_sustainable_development": "Tai_Po",
            "hong_kong_museum_of_education": "Tai_Po",
            "blue_sky_sports_club_sha_ha_center": "Sha_Tin",
            "pineapple_dam_nature_trail": "Tai_Po",
            "sai_kung": "Sai_Kung",
            "tai_mo_shan": "Tai_Po"
        }
        
        # Known attraction-district mappings'''
            )
            
            # Save improved script
            improved_script_path = "mbti_travel_assistant_mcp/scripts/reorganize_by_district_improved.py"
            with open(improved_script_path, 'w', encoding='utf-8') as f:
                f.write(improved_content)
            
            print(f"✅ Created improved script: {improved_script_path}")
            
        except Exception as e:
            print(f"❌ Error creating improved script: {e}")

def main():
    """Main execution."""
    
    print("🎯 Improving District Detection for Unknown_District Files")
    print("=" * 60)
    
    detector = ImprovedDistrictDetector()
    
    # Analyze unknown district files
    improved_mappings = detector.analyze_unknown_district_files()
    
    # Generate corrected structure
    district_structure = detector.generate_corrected_structure()
    
    # Create updated script
    detector.create_updated_reorganization_script()
    
    print(f"\n🎉 District Detection Improvement Complete!")
    print(f"📋 Summary:")
    print(f"   - Analyzed 12 Unknown_District files")
    print(f"   - Mapped to {len(district_structure)} districts:")
    for district, files in sorted(district_structure.items()):
        print(f"     • {district}: {len(files)} files")
    
    print(f"\n📝 Recommendations:")
    print("1. Use the improved reorganization script for better district detection")
    print("2. The enhanced mappings cover university locations, nature trails, and sports facilities")
    print("3. New districts added: Sha_Tin, Tai_Po, Sai_Kung, New_Territories_General")
    print("4. All previously unknown files now have proper district assignments")

if __name__ == "__main__":
    main()