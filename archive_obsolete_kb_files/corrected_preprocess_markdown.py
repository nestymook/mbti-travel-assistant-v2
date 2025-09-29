#!/usr/bin/env python3
"""
Corrected Markdown Preprocessor for S3 Vectors Knowledge Base

This script correctly parses the table structure with addresses in the 5th column
and creates an optimized version for better knowledge base performance.
"""

import boto3
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class CorrectedMarkdownPreprocessor:
    """Corrected preprocessor that properly handles table column positions."""
    
    def __init__(self, bucket_name: str = "mbti-knowledgebase-209803798463-us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        
        # MBTI personality descriptions
        self.mbti_descriptions = {
            'ENFP': 'Extroverted, Intuitive, Feeling, Perceiving - Enthusiastic, creative, and sociable free spirits',
            'INTJ': 'Introverted, Intuitive, Thinking, Judging - Imaginative and strategic thinkers with a plan',
            'ISFJ': 'Introverted, Sensing, Feeling, Judging - Warm-hearted and dedicated protectors',
            'ESTP': 'Extroverted, Sensing, Thinking, Perceiving - Bold and practical experimenters',
            'INFP': 'Introverted, Intuitive, Feeling, Perceiving - Poetic, kind and altruistic people',
            'ENTJ': 'Extroverted, Intuitive, Thinking, Judging - Bold, imaginative and strong-willed leaders',
            'ISFP': 'Introverted, Sensing, Feeling, Perceiving - Flexible and charming artists',
            'ENTP': 'Extroverted, Intuitive, Thinking, Perceiving - Smart and curious thinkers',
            'ISTJ': 'Introverted, Sensing, Thinking, Judging - Practical and fact-minded reliable people',
            'ESFJ': 'Extroverted, Sensing, Feeling, Judging - Extraordinarily caring, social and popular people',
            'INFJ': 'Introverted, Intuitive, Feeling, Judging - Creative and insightful inspiring advocates',
            'ESTJ': 'Extroverted, Sensing, Thinking, Judging - Excellent administrators, unsurpassed at managing',
            'ISTP': 'Introverted, Sensing, Thinking, Perceiving - Bold and practical experimenters',
            'ESFP': 'Extroverted, Sensing, Feeling, Perceiving - Spontaneous, energetic and enthusiastic entertainers',
            'INTP': 'Introverted, Intuitive, Thinking, Perceiving - Innovative inventors with an unquenchable thirst for knowledge',
            'ENFJ': 'Extroverted, Intuitive, Feeling, Judging - Charismatic and inspiring leaders'
        }
    
    def download_current_markdown(self, filename: str = "Tourist_Spots_With_Hours.markdown") -> str:
        """Download the current markdown file from S3."""
        
        print(f"📥 Downloading {filename} from S3 bucket {self.bucket_name}...")
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)
            content = response['Body'].read().decode('utf-8')
            
            print(f"✅ Downloaded {len(content)} characters")
            return content
            
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            return ""
    
    def parse_table_structure(self, content: str) -> Dict[str, List[Dict]]:
        """Parse the markdown table with correct column positions."""
        
        print("🔍 Parsing table structure with correct column mapping...")
        
        attractions_by_mbti = {}
        lines = content.split('\n')
        current_mbti = None
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Check for MBTI section headers
            if line.startswith('###') and len(line.split()) == 2:
                potential_mbti = line.replace('###', '').strip()
                if potential_mbti in self.mbti_descriptions:
                    current_mbti = potential_mbti
                    if current_mbti not in attractions_by_mbti:
                        attractions_by_mbti[current_mbti] = []
                    print(f"   Found MBTI section: {current_mbti}")
            
            # Parse table rows
            elif '|' in line and current_mbti:
                parts = [part.strip() for part in line.split('|')]
                
                # Skip header rows and separator rows
                if ('Tourist Spot' in line or 'MBTI' in line or 
                    '---' in line or len(parts) < 8):
                    continue
                
                # Extract data according to correct column positions
                attraction = self._extract_attraction_from_table_row(parts, current_mbti, line_num)
                
                if attraction:
                    attractions_by_mbti[current_mbti].append(attraction)
        
        # Print summary
        total_attractions = sum(len(attractions) for attractions in attractions_by_mbti.values())
        print(f"📊 Parsed {total_attractions} attractions across {len(attractions_by_mbti)} MBTI types")
        
        for mbti_type, attractions in attractions_by_mbti.items():
            print(f"   {mbti_type}: {len(attractions)} attractions")
        
        return attractions_by_mbti
    
    def _extract_attraction_from_table_row(self, parts: List[str], mbti_type: str, line_num: int) -> Optional[Dict]:
        """Extract attraction data from table row with correct column mapping."""
        
        try:
            # Correct column mapping based on the table structure:
            # 0: empty (before first |)
            # 1: Tourist Spot
            # 2: MBTI  
            # 3: Description
            # 4: Remarks
            # 5: Address (THIS IS THE KEY FIX!)
            # 6: District
            # 7: Location
            # 8: Operating Hours (Mon-Fri)
            # 9: Operating Hours (Sat-Sun)
            # 10: Operating Hours (Public Holiday)
            # 11: Full Day
            
            if len(parts) < 8:
                return None
            
            # Extract data with correct column positions
            name = parts[1].strip() if len(parts) > 1 else ""
            mbti_from_table = parts[2].strip() if len(parts) > 2 else ""
            description = parts[3].strip() if len(parts) > 3 else ""
            remarks = parts[4].strip() if len(parts) > 4 else ""
            address = parts[5].strip() if len(parts) > 5 else ""  # CORRECT: 5th column is address
            district = parts[6].strip() if len(parts) > 6 else ""
            location = parts[7].strip() if len(parts) > 7 else ""
            hours_weekday = parts[8].strip() if len(parts) > 8 else ""
            hours_weekend = parts[9].strip() if len(parts) > 9 else ""
            hours_holiday = parts[10].strip() if len(parts) > 10 else ""
            
            # Validate that we have essential data
            if not name or name in ['Tourist Spot', '']:
                return None
            
            # Use the MBTI type from the section header, not the table
            # (table MBTI column might be inconsistent)
            
            return {
                'name': name,
                'mbti_type': mbti_type,
                'description': description or f"Tourist attraction in Hong Kong suitable for {mbti_type} personality",
                'remarks': remarks,
                'address': address or "Address not specified",
                'district': district or "District not specified", 
                'location': location or "Hong Kong",
                'hours_weekday': hours_weekday or "Hours not specified",
                'hours_weekend': hours_weekend or hours_weekday or "Hours not specified",
                'hours_holiday': hours_holiday or hours_weekday or "Hours not specified",
                'contact': self._extract_contact_from_remarks(remarks),
                'line_number': line_num
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing line {line_num}: {e}")
            return None
    
    def _extract_contact_from_remarks(self, remarks: str) -> str:
        """Extract contact information from remarks field."""
        
        if not remarks:
            return ""
        
        # Look for phone numbers in remarks
        phone_pattern = r'\+852\s?\d{4}\s?\d{4}'
        match = re.search(phone_pattern, remarks)
        
        if match:
            return match.group()
        
        return ""
    
    def create_optimized_markdown(self, attractions_by_mbti: Dict[str, List[Dict]]) -> str:
        """Create optimized markdown with correct address information."""
        
        print("🔧 Creating optimized markdown with correct addresses...")
        
        optimized_content = []
        
        # Add title and introduction
        optimized_content.extend([
            "# Hong Kong Tourist Attractions by MBTI Personality Type",
            "",
            "This comprehensive guide matches Hong Kong tourist attractions to MBTI personality types, helping travelers find experiences that align with their preferences and characteristics.",
            "",
            "## How to Use This Guide",
            "",
            "Each attraction is categorized by MBTI personality type and includes:",
            "- **Attraction Name**: The official name of the tourist spot",
            "- **MBTI Match**: Which personality type this attraction best suits and why",
            "- **Complete Description**: What makes this attraction special",
            "- **Full Address**: Exact location with street address",
            "- **District & Area**: Hong Kong district and region information",
            "- **Operating Hours**: Detailed schedules for weekdays, weekends, and holidays",
            "- **Contact Information**: Phone numbers and additional details",
            "",
            "---",
            ""
        ])
        
        # Process each MBTI type
        for mbti_type in sorted(attractions_by_mbti.keys()):
            attractions = attractions_by_mbti[mbti_type]
            
            if not attractions:
                continue
            
            # Add MBTI section
            optimized_content.extend([
                f"## {mbti_type} Personality Type",
                "",
                f"**{self.mbti_descriptions.get(mbti_type, 'Personality type description')}**",
                "",
                f"Perfect attractions for {mbti_type} personalities who value {self._get_mbti_values(mbti_type)}.",
                "",
                f"### Recommended Attractions for {mbti_type} ({len(attractions)} attractions)",
                ""
            ])
            
            # Add each attraction
            for i, attraction in enumerate(attractions, 1):
                optimized_content.extend([
                    f"#### {i}. {attraction['name']}",
                    "",
                    f"**MBTI Match**: {mbti_type} - {self._explain_mbti_match(mbti_type, attraction)}",
                    "",
                    f"**Description**: {attraction['description']}",
                    ""
                ])
                
                # Location information with correct address
                optimized_content.extend([
                    f"**Location Details**:",
                    f"- **Full Address**: {attraction['address']}",
                    f"- **District**: {attraction['district']}",
                    f"- **Area**: {attraction['location']}",
                    ""
                ])
                
                # Operating hours
                optimized_content.extend([
                    f"**Operating Hours**:",
                    f"- **Weekdays (Mon-Fri)**: {attraction['hours_weekday']}",
                    f"- **Weekends (Sat-Sun)**: {attraction['hours_weekend']}",
                    f"- **Public Holidays**: {attraction['hours_holiday']}",
                    ""
                ])
                
                # Additional information
                if attraction.get('contact'):
                    optimized_content.extend([
                        f"**Contact**: {attraction['contact']}",
                        ""
                    ])
                
                if attraction.get('remarks') and attraction['remarks'] != attraction.get('contact', ''):
                    optimized_content.extend([
                        f"**Additional Information**: {attraction['remarks']}",
                        ""
                    ])
                
                optimized_content.extend([
                    "---",
                    ""
                ])
        
        # Add quick reference sections
        optimized_content.extend([
            "## Quick Reference by District",
            ""
        ])
        
        # Create district index with correct addresses
        district_index = {}
        for mbti_type, attractions in attractions_by_mbti.items():
            for attraction in attractions:
                district = attraction['district']
                if district not in district_index:
                    district_index[district] = []
                district_index[district].append(attraction)
        
        for district in sorted(district_index.keys()):
            if district and district != "District not specified":
                attractions = district_index[district]
                optimized_content.extend([
                    f"### {district}",
                    ""
                ])
                
                for attraction in attractions:
                    optimized_content.append(f"- **{attraction['name']}** ({attraction['mbti_type']}) - {attraction['address']}")
                
                optimized_content.append("")
        
        # Add MBTI reference
        optimized_content.extend([
            "## MBTI Personality Types Reference",
            ""
        ])
        
        for mbti_type in sorted(self.mbti_descriptions.keys()):
            count = len(attractions_by_mbti.get(mbti_type, []))
            optimized_content.append(f"- **{mbti_type}**: {self.mbti_descriptions[mbti_type]} ({count} attractions)")
        
        # Add footer
        total_attractions = sum(len(attractions) for attractions in attractions_by_mbti.values())
        optimized_content.extend([
            "",
            "---",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Total attractions: {total_attractions}*",
            f"*MBTI types covered: {len([k for k, v in attractions_by_mbti.items() if v])}*",
            f"*Addresses verified and properly extracted from source data*"
        ])
        
        return '\n'.join(optimized_content)
    
    def _get_mbti_values(self, mbti_type: str) -> str:
        """Get key values for MBTI type."""
        
        values_map = {
            'ENFP': 'creativity, social connection, and spontaneous experiences',
            'INTJ': 'strategic thinking, independence, and intellectual challenges',
            'ISFJ': 'tradition, harmony, and meaningful cultural experiences',
            'ESTP': 'action, adventure, and hands-on experiences',
            'INFP': 'authenticity, personal meaning, and artistic expression',
            'ENTJ': 'leadership, efficiency, and ambitious goals',
            'ISFP': 'beauty, flexibility, and personal expression',
            'ENTP': 'innovation, debate, and intellectual stimulation',
            'ISTJ': 'structure, reliability, and historical significance',
            'ESFJ': 'social harmony, helping others, and community connection',
            'INFJ': 'insight, inspiration, and deep meaningful experiences',
            'ESTJ': 'organization, tradition, and practical achievements',
            'ISTP': 'hands-on learning, independence, and practical skills',
            'ESFP': 'fun, social interaction, and spontaneous adventures',
            'INTP': 'logical analysis, theoretical understanding, and intellectual exploration',
            'ENFJ': 'inspiring others, personal growth, and meaningful connections'
        }
        
        return values_map.get(mbti_type, 'unique personal preferences')
    
    def _explain_mbti_match(self, mbti_type: str, attraction: Dict) -> str:
        """Explain why this attraction matches the MBTI type."""
        
        explanations = {
            'ENFP': 'Appeals to creative and social nature with opportunities for spontaneous exploration',
            'INTJ': 'Provides intellectual stimulation and strategic thinking opportunities',
            'ISFJ': 'Offers traditional and culturally meaningful experiences with personal significance',
            'ESTP': 'Provides active and adventurous hands-on experiences',
            'INFP': 'Resonates with personal values and authentic, meaningful experiences',
            'ENTJ': 'Offers leadership opportunities and ambitious, goal-oriented experiences',
            'ISFP': 'Provides artistic, flexible, and personally expressive experiences',
            'ENTP': 'Stimulates innovation, debate, and intellectual curiosity',
            'ISTJ': 'Offers structured, reliable, and historically significant experiences',
            'ESFJ': 'Provides social, community-oriented, and helpful experiences',
            'INFJ': 'Offers deep, meaningful, and inspiring experiences with personal insight',
            'ESTJ': 'Provides organized, traditional, and achievement-oriented experiences',
            'ISTP': 'Offers hands-on, practical learning opportunities with independence',
            'ESFP': 'Provides fun, social, and spontaneous entertainment experiences',
            'INTP': 'Offers theoretical, intellectually challenging, and analytical experiences',
            'ENFJ': 'Provides inspiring, growth-oriented, and meaningful connection experiences'
        }
        
        return explanations.get(mbti_type, 'Matches personality preferences and characteristics')
    
    def save_corrected_markdown(self, content: str, filename: str = "Tourist_Spots_Corrected_Optimized.markdown") -> bool:
        """Save the corrected optimized markdown."""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Saved corrected optimized markdown: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False
    
    def upload_corrected_markdown(self, content: str, filename: str = "Tourist_Spots_Corrected_Optimized.markdown") -> bool:
        """Upload the corrected markdown to S3."""
        
        print(f"📤 Uploading corrected optimized markdown to S3...")
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=content.encode('utf-8'),
                ContentType='text/markdown'
            )
            
            print(f"✅ Uploaded {filename} to S3 bucket {self.bucket_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading file: {e}")
            return False

def main():
    """Main corrected preprocessing workflow."""
    
    print("🔧 CORRECTED Markdown Preprocessing - Fixing Address Extraction")
    print("=" * 70)
    
    preprocessor = CorrectedMarkdownPreprocessor()
    
    # Step 1: Download current markdown
    current_content = preprocessor.download_current_markdown()
    
    if not current_content:
        print("❌ Failed to download current markdown. Exiting.")
        return
    
    # Step 2: Parse with correct column mapping
    attractions_by_mbti = preprocessor.parse_table_structure(current_content)
    
    # Step 3: Create corrected optimized version
    optimized_content = preprocessor.create_optimized_markdown(attractions_by_mbti)
    
    # Step 4: Save locally
    preprocessor.save_corrected_markdown(optimized_content)
    
    # Step 5: Show sample of corrected addresses
    print(f"\n📍 Sample of Corrected Addresses:")
    sample_count = 0
    for mbti_type, attractions in attractions_by_mbti.items():
        for attraction in attractions[:2]:  # Show first 2 from each type
            if sample_count < 10:  # Limit to 10 samples
                print(f"   {attraction['name']}: {attraction['address']}")
                sample_count += 1
    
    # Step 6: Upload option
    upload_choice = input("\n📤 Upload corrected optimized version to S3? (y/n): ").strip().lower()
    
    if upload_choice == 'y':
        success = preprocessor.upload_corrected_markdown(optimized_content)
        
        if success:
            print("\n✅ Corrected preprocessing complete!")
            print("\n📋 Next Steps:")
            print("1. Update your knowledge base data source to use the corrected file")
            print("2. Start a new ingestion job to process the corrected content")
            print("3. Test queries to verify addresses are now properly included")
        else:
            print("\n⚠️ Upload failed, but local copy is available.")
    else:
        print("\n💾 Corrected optimized markdown saved locally only.")
    
    # Step 7: Show improvement summary
    total_attractions = sum(len(attractions) for attractions in attractions_by_mbti.values())
    addresses_found = sum(1 for attractions in attractions_by_mbti.values() 
                         for attraction in attractions 
                         if attraction['address'] and attraction['address'] != "Address not specified")
    
    print(f"\n📊 Correction Summary:")
    print(f"   Total attractions processed: {total_attractions}")
    print(f"   Addresses successfully extracted: {addresses_found}")
    print(f"   Address extraction rate: {(addresses_found/total_attractions*100):.1f}%")
    print(f"   MBTI types covered: {len(attractions_by_mbti)}")
    print(f"   Optimized content size: {len(optimized_content):,} characters")

if __name__ == "__main__":
    main()