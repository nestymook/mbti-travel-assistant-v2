#!/usr/bin/env python3
"""
Analyze Unknown_District files and provide improved mappings
"""

def analyze_unknown_districts():
    """Analyze the files that were categorized as Unknown_District."""
    
    print("🔍 Analyzing Unknown_District Files")
    print("=" * 50)
    
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
    
    # Enhanced mappings based on Hong Kong geography
    enhanced_mappings = {
        # University and Academic (Sha Tin area)
        "ESTJ_Art_Museum_The_Chinese_University_of_Hong_Kong.md": "Sha_Tin",
        "INTJ_Art_Museum_The_Chinese_University_of_Hong_Kong.md": "Sha_Tin", 
        "ISFP_Art_Museum_The_Chinese_University_of_Hong_Kong.md": "Sha_Tin",
        "ESTJ_Hong_Kong_Heritage_Museum.md": "Sha_Tin",
        "INTJ_Hong_Kong_Heritage_Museum.md": "Sha_Tin",
        "INTJ_Hong_Kong_Science_and_Technology_Parks_Corporation.md": "Sha_Tin",
        
        # Education (Tai Po area)
        "INTP_Hong_Kong_Institute_of_Education_for_Sustainable_Development.md": "Tai_Po",
        "ISTJ_Hong_Kong_Museum_of_Education.md": "Tai_Po",
        "ISTJ_Pineapple_Dam_Nature_Trail.md": "Tai_Po",
        "ISTP_Tai_Mo_Shan.md": "Tai_Po",
        
        # Sports and Recreation
        "ISFP_Blue_Sky_Sports_Club_Sha_Ha_Center.md": "Sha_Tin",
        
        # Sai Kung District
        "ISTP_Sai_Kung.md": "Sai_Kung"
    }
    
    print("📋 Improved District Mappings:")
    print("-" * 40)
    
    district_counts = {}
    for filename, district in enhanced_mappings.items():
        mbti_type = filename.split('_')[0]
        attraction = '_'.join(filename.split('_')[1:]).replace('.md', '')
        
        print(f"✅ {mbti_type} - {attraction}")
        print(f"   → {district}")
        
        if district not in district_counts:
            district_counts[district] = 0
        district_counts[district] += 1
    
    print(f"\n📊 New District Distribution:")
    for district, count in sorted(district_counts.items()):
        print(f"   {district}: {count} files")
    
    print(f"\n🎯 Benefits of Improved Mapping:")
    print("✅ No more Unknown_District folder")
    print("✅ Proper geographic organization")
    print("✅ Better search targeting by district")
    print("✅ More accurate location-based queries")
    
    return enhanced_mappings

def create_corrected_district_structure():
    """Show the corrected district structure after improvements."""
    
    print(f"\n🗂️ Corrected District Structure (No Unknown_District)")
    print("=" * 60)
    
    # Original district counts from reorganization
    original_districts = {
        "Admiralty": 3,
        "Causeway_Bay": 6, 
        "Central_District": 42,
        "Hong_Kong_Island_General": 27,
        "Kowloon_General": 8,
        "Lantau_Island": 7,
        "Mong_Kok": 2,
        "Sheung_Wan": 9,
        "Tsim_Sha_Tsui": 52,
        "Wan_Chai": 11,
        "Yau_Ma_Tei": 4
    }
    
    # Add new districts from improved mappings
    new_districts = {
        "Sha_Tin": 7,  # University and heritage locations
        "Tai_Po": 4,   # Education and nature trails
        "Sai_Kung": 1  # Sai Kung district
    }
    
    # Combined structure
    all_districts = {**original_districts, **new_districts}
    
    total_files = sum(all_districts.values())
    
    print(f"📁 Final District Structure ({len(all_districts)} districts, {total_files} files):")
    for district, count in sorted(all_districts.items()):
        print(f"   {district}/: {count} files")
    
    print(f"\n✅ Improvements:")
    print(f"   - Eliminated Unknown_District folder")
    print(f"   - Added 3 new proper districts (Sha_Tin, Tai_Po, Sai_Kung)")
    print(f"   - All 183 files now have proper district assignments")
    print(f"   - Better geographic accuracy for search targeting")

if __name__ == "__main__":
    enhanced_mappings = analyze_unknown_districts()
    create_corrected_district_structure()
    
    print(f"\n📋 Next Steps:")
    print("1. Update the reorganization script with enhanced mappings")
    print("2. Re-run the reorganization with improved district detection")
    print("3. Upload the corrected structure to S3")
    print("4. Test district-based search strategies")
    print("5. Verify improved search performance with proper districts")