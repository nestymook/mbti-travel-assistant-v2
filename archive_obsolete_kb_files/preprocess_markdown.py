#!/usr/bin/env python3
"""
Markdown Preprocessor for S3 Vectors Knowledge Base

This script downloads the current markdown file from S3, analyzes its structure,
and creates an optimized version for better knowledge base performance.
"""

import boto3
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class MarkdownPreprocessor:
    """Preprocess markdown files for optimal knowledge base performance."""
    
    def __init__(self, bucket_name: str = "mbti-knowledgebase-209803798463-us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        
        # MBTI personality descriptions for context
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
        
        # Hong Kong districts for validation
        self.hk_districts = [
            'Central', 'Wan Chai', 'Causeway Bay', 'Admiralty', 'Sheung Wan',
            'Tsim Sha Tsui', 'Mong Kok', 'Yau Ma Tei', 'Jordan', 'Hung Hom',
            'Sha Tin', 'Tai Po', 'Tuen Mun', 'Yuen Long', 'Kwun Tong',
            'Wong Tai Sin', 'Sham Shui Po', 'Kowloon City', 'Eastern',
            'Southern', 'Western', 'Islands', 'North', 'Sai Kung'
        ]
    
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
    
    def analyze_current_structure(self, content: str) -> Dict:
        """Analyze the current markdown structure."""
        
        print("🔍 Analyzing current markdown structure...")
        
        lines = content.split('\n')
        
        analysis = {
            'total_lines': len(lines),
            'headers': [],
            'table_rows': [],
            'mbti_types_found': set(),
            'districts_found': set(),
            'attractions_count': 0,
            'empty_lines': 0,
            'table_structure': {}
        }
        
        current_section = None
        table_headers = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                analysis['empty_lines'] += 1
                continue
            
            # Check for headers
            if line.startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('#').strip()
                analysis['headers'].append({
                    'level': header_level,
                    'text': header_text,
                    'line': i + 1
                })
                current_section = header_text
            
            # Check for table rows
            elif '|' in line:
                parts = [part.strip() for part in line.split('|')]
                
                # Check if this is a header row
                if 'Tourist Spot' in line or 'MBTI' in line:
                    table_headers = parts
                    analysis['table_structure']['headers'] = table_headers
                
                # Check if this is a data row
                elif len(parts) >= 5:
                    analysis['table_rows'].append({
                        'line': i + 1,
                        'parts': parts,
                        'section': current_section
                    })
                    
                    # Extract MBTI types
                    for part in parts:
                        if part in self.mbti_descriptions:
                            analysis['mbti_types_found'].add(part)
                    
                    # Extract districts
                    for part in parts:
                        for district in self.hk_districts:
                            if district.lower() in part.lower():
                                analysis['districts_found'].add(district)
                    
                    # Count as attraction if it has meaningful content
                    if any(len(part) > 5 for part in parts):
                        analysis['attractions_count'] += 1
        
        analysis['mbti_types_found'] = list(analysis['mbti_types_found'])
        analysis['districts_found'] = list(analysis['districts_found'])
        
        print(f"📊 Analysis Results:")
        print(f"   Total lines: {analysis['total_lines']}")
        print(f"   Headers: {len(analysis['headers'])}")
        print(f"   Table rows: {len(analysis['table_rows'])}")
        print(f"   Attractions: {analysis['attractions_count']}")
        print(f"   MBTI types: {len(analysis['mbti_types_found'])}")
        print(f"   Districts: {len(analysis['districts_found'])}")
        
        return analysis
    
    def create_optimized_markdown(self, content: str, analysis: Dict) -> str:
        """Create an optimized version of the markdown."""
        
        print("🔧 Creating optimized markdown...")
        
        # Parse the original content
        attractions_by_mbti = self._parse_attractions_by_mbti(content)
        
        # Build optimized markdown
        optimized_content = []
        
        # Add title and introduction
        optimized_content.extend([
            "# Hong Kong Tourist Attractions by MBTI Personality Type",
            "",
            "This guide matches Hong Kong tourist attractions to MBTI personality types, helping travelers find experiences that align with their preferences and characteristics.",
            "",
            "## How to Use This Guide",
            "",
            "Each attraction is categorized by MBTI personality type and includes:",
            "- **Attraction Name**: The official name of the tourist spot",
            "- **MBTI Match**: Which personality type this attraction best suits",
            "- **Description**: What makes this attraction special and why it matches the personality type",
            "- **Location Details**: Full address and district information",
            "- **Operating Hours**: Weekday, weekend, and holiday schedules",
            "- **Additional Information**: Contact details, special notes, and tips",
            "",
            "---",
            ""
        ])
        
        # Add MBTI type sections
        for mbti_type in sorted(attractions_by_mbti.keys()):
            attractions = attractions_by_mbti[mbti_type]
            
            if not attractions:
                continue
            
            # Add MBTI section header with description
            optimized_content.extend([
                f"## {mbti_type} Personality Type",
                "",
                f"**{self.mbti_descriptions.get(mbti_type, 'Personality type description')}**",
                "",
                f"Perfect attractions for {mbti_type} personalities who value {self._get_mbti_values(mbti_type)}.",
                "",
                f"### Recommended Attractions for {mbti_type}",
                ""
            ])
            
            # Add attractions for this MBTI type
            for i, attraction in enumerate(attractions, 1):
                optimized_content.extend([
                    f"#### {i}. {attraction['name']}",
                    "",
                    f"**MBTI Match**: {mbti_type} - {self._explain_mbti_match(mbti_type, attraction)}",
                    "",
                    f"**Description**: {attraction['description']}",
                    "",
                    f"**Location**:",
                    f"- Address: {attraction['address']}",
                    f"- District: {attraction['district']}",
                    f"- Area: {attraction.get('location', 'Hong Kong')}",
                    "",
                    f"**Operating Hours**:",
                    f"- Weekdays: {attraction['hours_weekday']}",
                    f"- Weekends: {attraction['hours_weekend']}",
                    f"- Holidays: {attraction['hours_holiday']}",
                    ""
                ])
                
                if attraction.get('remarks'):
                    optimized_content.extend([
                        f"**Additional Information**: {attraction['remarks']}",
                        ""
                    ])
                
                if attraction.get('contact'):
                    optimized_content.extend([
                        f"**Contact**: {attraction['contact']}",
                        ""
                    ])
                
                optimized_content.append("---")
                optimized_content.append("")
        
        # Add district index
        optimized_content.extend([
            "## Quick Reference by District",
            ""
        ])
        
        districts_index = self._create_districts_index(attractions_by_mbti)
        for district, attractions in sorted(districts_index.items()):
            optimized_content.extend([
                f"### {district} District",
                ""
            ])
            
            for attraction in attractions:
                optimized_content.append(f"- **{attraction['name']}** ({attraction['mbti_type']}) - {attraction['description'][:100]}...")
            
            optimized_content.append("")
        
        # Add MBTI quick reference
        optimized_content.extend([
            "## MBTI Personality Types Quick Reference",
            ""
        ])
        
        for mbti_type, description in sorted(self.mbti_descriptions.items()):
            count = len(attractions_by_mbti.get(mbti_type, []))
            optimized_content.append(f"- **{mbti_type}**: {description} ({count} attractions)")
        
        optimized_content.extend([
            "",
            "---",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Total attractions: {sum(len(attractions) for attractions in attractions_by_mbti.values())}*",
            f"*MBTI types covered: {len([k for k, v in attractions_by_mbti.items() if v])}*"
        ])
        
        return '\n'.join(optimized_content)
    
    def _parse_attractions_by_mbti(self, content: str) -> Dict[str, List[Dict]]:
        """Parse attractions and group by MBTI type."""
        
        attractions_by_mbti = {}
        lines = content.split('\n')
        
        for line in lines:
            if '|' in line and len(line.split('|')) >= 8:
                parts = [part.strip() for part in line.split('|')]
                
                # Skip header rows
                if 'Tourist Spot' in line or 'MBTI' in line or '---' in line:
                    continue
                
                # Try to extract attraction data
                attraction = self._extract_attraction_from_parts(parts)
                
                if attraction and attraction['mbti_type']:
                    mbti_type = attraction['mbti_type']
                    
                    if mbti_type not in attractions_by_mbti:
                        attractions_by_mbti[mbti_type] = []
                    
                    attractions_by_mbti[mbti_type].append(attraction)
        
        return attractions_by_mbti
    
    def _extract_attraction_from_parts(self, parts: List[str]) -> Optional[Dict]:
        """Extract attraction data from table parts."""
        
        if len(parts) < 8:
            return None
        
        # Try to identify which part is which based on content
        name = ""
        mbti_type = ""
        description = ""
        address = ""
        district = ""
        location = ""
        hours_weekday = ""
        hours_weekend = ""
        hours_holiday = ""
        remarks = ""
        contact = ""
        
        for part in parts:
            if not part or part in ['', '|']:
                continue
            
            # Check for MBTI type
            if part in self.mbti_descriptions:
                mbti_type = part
            
            # Check for district
            elif any(d.lower() in part.lower() for d in self.hk_districts):
                if not district:
                    district = part
                elif not location:
                    location = part
            
            # Check for time patterns (operating hours)
            elif re.search(r'\d{1,2}:\d{2}|AM|PM|closed', part, re.IGNORECASE):
                if not hours_weekday:
                    hours_weekday = part
                elif not hours_weekend:
                    hours_weekend = part
                else:
                    hours_holiday = part
            
            # Check for address (contains numbers and street indicators)
            elif re.search(r'\d+.*(?:road|street|avenue|drive|lane)', part, re.IGNORECASE):
                address = part
            
            # Check for phone numbers
            elif re.search(r'\+852|\d{4}\s?\d{4}', part):
                contact = part
            
            # Check for attraction name (first meaningful non-MBTI part)
            elif not name and len(part) > 3 and part not in ['Tourist Spot', 'MBTI', 'Description']:
                name = part
            
            # Everything else could be description or remarks
            elif len(part) > 10:
                if not description:
                    description = part
                elif not remarks:
                    remarks = part
        
        if name and mbti_type:
            return {
                'name': name,
                'mbti_type': mbti_type,
                'description': description or f"Tourist attraction in Hong Kong suitable for {mbti_type} personality",
                'address': address or "Address not specified",
                'district': district or "District not specified",
                'location': location or "Hong Kong",
                'hours_weekday': hours_weekday or "Hours not specified",
                'hours_weekend': hours_weekend or hours_weekday or "Hours not specified",
                'hours_holiday': hours_holiday or hours_weekday or "Hours not specified",
                'remarks': remarks,
                'contact': contact
            }
        
        return None
    
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
            'ENFP': 'Appeals to creative and social nature',
            'INTJ': 'Provides intellectual stimulation and strategic thinking opportunities',
            'ISFJ': 'Offers traditional and culturally meaningful experiences',
            'ESTP': 'Provides active and adventurous experiences',
            'INFP': 'Resonates with personal values and authentic experiences',
            'ENTJ': 'Offers leadership opportunities and ambitious experiences',
            'ISFP': 'Provides artistic and flexible experiences',
            'ENTP': 'Stimulates innovation and intellectual curiosity',
            'ISTJ': 'Offers structured and historically significant experiences',
            'ESFJ': 'Provides social and community-oriented experiences',
            'INFJ': 'Offers deep, meaningful, and inspiring experiences',
            'ESTJ': 'Provides organized and achievement-oriented experiences',
            'ISTP': 'Offers hands-on and practical learning opportunities',
            'ESFP': 'Provides fun, social, and spontaneous experiences',
            'INTP': 'Offers theoretical and intellectually challenging experiences',
            'ENFJ': 'Provides inspiring and growth-oriented experiences'
        }
        
        return explanations.get(mbti_type, 'Matches personality preferences')
    
    def _create_districts_index(self, attractions_by_mbti: Dict) -> Dict[str, List[Dict]]:
        """Create an index of attractions by district."""
        
        districts_index = {}
        
        for mbti_type, attractions in attractions_by_mbti.items():
            for attraction in attractions:
                district = attraction['district']
                
                if district not in districts_index:
                    districts_index[district] = []
                
                districts_index[district].append(attraction)
        
        return districts_index
    
    def upload_optimized_markdown(self, content: str, filename: str = "Tourist_Spots_Optimized.markdown") -> bool:
        """Upload the optimized markdown back to S3."""
        
        print(f"📤 Uploading optimized markdown to S3...")
        
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
    
    def save_local_copy(self, content: str, filename: str = "Tourist_Spots_Optimized.markdown") -> bool:
        """Save optimized markdown locally."""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Saved local copy: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving local file: {e}")
            return False

def main():
    """Main preprocessing workflow."""
    
    print("🚀 Markdown Preprocessing for S3 Vectors Knowledge Base")
    print("=" * 60)
    
    preprocessor = MarkdownPreprocessor()
    
    # Step 1: Download current markdown
    current_content = preprocessor.download_current_markdown()
    
    if not current_content:
        print("❌ Failed to download current markdown. Exiting.")
        return
    
    # Step 2: Analyze current structure
    analysis = preprocessor.analyze_current_structure(current_content)
    
    # Step 3: Create optimized version
    optimized_content = preprocessor.create_optimized_markdown(current_content, analysis)
    
    # Step 4: Save locally
    preprocessor.save_local_copy(optimized_content)
    
    # Step 5: Upload to S3 (optional)
    upload_choice = input("\n📤 Upload optimized version to S3? (y/n): ").strip().lower()
    
    if upload_choice == 'y':
        success = preprocessor.upload_optimized_markdown(optimized_content)
        
        if success:
            print("\n✅ Preprocessing complete! Optimized markdown is ready.")
            print("\n📋 Next Steps:")
            print("1. Update your knowledge base data source to use the optimized file")
            print("2. Start a new ingestion job to process the optimized content")
            print("3. Test queries to see improved performance")
        else:
            print("\n⚠️ Upload failed, but local copy is available.")
    else:
        print("\n💾 Optimized markdown saved locally only.")
    
    # Step 6: Show improvement summary
    print(f"\n📊 Optimization Summary:")
    print(f"   Original size: {len(current_content):,} characters")
    print(f"   Optimized size: {len(optimized_content):,} characters")
    print(f"   Size change: {((len(optimized_content) - len(current_content)) / len(current_content) * 100):+.1f}%")
    print(f"   MBTI types: {len(analysis['mbti_types_found'])}")
    print(f"   Attractions: {analysis['attractions_count']}")
    print(f"   Districts: {len(analysis['districts_found'])}")

if __name__ == "__main__":
    main()