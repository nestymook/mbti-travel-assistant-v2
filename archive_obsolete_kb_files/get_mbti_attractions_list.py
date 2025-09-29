#!/usr/bin/env python3
"""
MBTI Tourist Attractions List Generator

This script uses the Nova Pro knowledge base implementation to generate
structured lists of tourist attractions for specific MBTI personality types.
"""

import boto3
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from final_nova_pro_kb_implementation import NovaProKnowledgeBase

@dataclass
class TouristAttraction:
    """Structured tourist attraction data."""
    name: str
    mbti_type: str
    description: str
    address: str
    district: str
    operating_hours_weekday: str
    operating_hours_weekend: str
    operating_hours_holiday: str
    remarks: str
    personality_alignment: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'mbti_type': self.mbti_type,
            'description': self.description,
            'address': self.address,
            'district': self.district,
            'operating_hours': {
                'weekday': self.operating_hours_weekday,
                'weekend': self.operating_hours_weekend,
                'holiday': self.operating_hours_holiday
            },
            'remarks': self.remarks,
            'personality_alignment': self.personality_alignment
        }

class MBTIAttractionsExtractor:
    """Extract and structure MBTI-based tourist attractions."""
    
    def __init__(self):
        self.kb = NovaProKnowledgeBase()
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
    def get_attractions_for_mbti(self, mbti_type: str, location: Optional[str] = None) -> List[TouristAttraction]:
        """Get structured list of attractions for specific MBTI type."""
        
        print(f"🔍 Extracting attractions for {mbti_type} personality type...")
        
        # First, get raw data using simple retrieve for better data extraction
        raw_attractions = self._get_raw_attractions_data(mbti_type, location)
        
        # Then get Nova Pro enhanced descriptions
        enhanced_info = self._get_enhanced_descriptions(mbti_type, location)
        
        # Combine and structure the data
        structured_attractions = self._structure_attractions_data(raw_attractions, enhanced_info, mbti_type)
        
        return structured_attractions
    
    def _get_raw_attractions_data(self, mbti_type: str, location: Optional[str]) -> List[Dict]:
        """Get raw attraction data using simple retrieve."""
        
        # Build query for raw data extraction
        query_parts = [mbti_type, "personality", "tourist attractions Hong Kong"]
        if location:
            query_parts.append(f"{location} district")
        
        query = " ".join(query_parts)
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10  # Get more raw data
                    }
                }
            )
            
            return response['retrievalResults']
            
        except Exception as e:
            print(f"❌ Error getting raw data: {e}")
            return []
    
    def _get_enhanced_descriptions(self, mbti_type: str, location: Optional[str]) -> str:
        """Get enhanced descriptions using Nova Pro."""
        
        result = self.kb.get_mbti_recommendations(
            mbti_type=mbti_type,
            location=location,
            activity_type="detailed attraction information"
        )
        
        if result['success']:
            return result['response']
        else:
            return ""
    
    def _structure_attractions_data(self, raw_data: List[Dict], enhanced_info: str, mbti_type: str) -> List[TouristAttraction]:
        """Structure raw data into TouristAttraction objects."""
        
        attractions = []
        
        for item in raw_data:
            content = item['content']['text']
            score = item['score']
            
            # Parse table-like data
            attraction = self._parse_attraction_from_content(content, mbti_type, enhanced_info)
            
            if attraction:
                attractions.append(attraction)
        
        # Remove duplicates and sort by relevance
        unique_attractions = self._deduplicate_attractions(attractions)
        
        return unique_attractions[:10]  # Return top 10
    
    def _parse_attraction_from_content(self, content: str, mbti_type: str, enhanced_info: str) -> Optional[TouristAttraction]:
        """Parse attraction data from content string."""
        
        try:
            # Handle table format with | separators
            if '|' in content:
                parts = [part.strip() for part in content.split('|')]
                
                # Find the attraction name and details
                name = ""
                description = ""
                address = ""
                district = ""
                hours_weekday = ""
                hours_weekend = ""
                hours_holiday = ""
                remarks = ""
                
                # Parse based on table structure
                for i, part in enumerate(parts):
                    if part and len(part) > 2:
                        # Try to identify what each part represents
                        if self._looks_like_attraction_name(part):
                            name = part
                        elif self._looks_like_address(part):
                            address = part
                        elif self._looks_like_district(part):
                            district = part
                        elif self._looks_like_time(part):
                            if not hours_weekday:
                                hours_weekday = part
                            elif not hours_weekend:
                                hours_weekend = part
                            else:
                                hours_holiday = part
                        elif self._looks_like_description(part):
                            description = part
                        elif part not in [mbti_type, "Tourist Spot", "MBTI", "Description", "Remarks", "Address", "District", "Location"]:
                            if not remarks:
                                remarks = part
                
                # Get personality alignment from enhanced info
                personality_alignment = self._extract_personality_alignment(name, enhanced_info, mbti_type)
                
                if name and name != "Tourist Spot":
                    return TouristAttraction(
                        name=name,
                        mbti_type=mbti_type,
                        description=description or "Tourist attraction in Hong Kong",
                        address=address or "Address not specified",
                        district=district or "District not specified",
                        operating_hours_weekday=hours_weekday or "Hours not specified",
                        operating_hours_weekend=hours_weekend or hours_weekday or "Hours not specified",
                        operating_hours_holiday=hours_holiday or hours_weekday or "Hours not specified",
                        remarks=remarks or "",
                        personality_alignment=personality_alignment
                    )
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error parsing content: {e}")
            return None
    
    def _looks_like_attraction_name(self, text: str) -> bool:
        """Check if text looks like an attraction name."""
        if len(text) < 3 or len(text) > 100:
            return False
        
        # Common attraction indicators
        attraction_keywords = ['museum', 'temple', 'park', 'market', 'center', 'centre', 'gallery', 'tower', 'building', 'plaza', 'square']
        text_lower = text.lower()
        
        return any(keyword in text_lower for keyword in attraction_keywords) or text.istitle()
    
    def _looks_like_address(self, text: str) -> bool:
        """Check if text looks like an address."""
        address_indicators = ['road', 'street', 'avenue', 'drive', 'lane', 'central', 'wan chai', 'tsim sha tsui']
        text_lower = text.lower()
        
        return any(indicator in text_lower for indicator in address_indicators) and len(text) > 10
    
    def _looks_like_district(self, text: str) -> bool:
        """Check if text looks like a district name."""
        districts = ['central', 'wan chai', 'tsim sha tsui', 'causeway bay', 'admiralty', 'sheung wan', 'mong kok', 'yau ma tei', 'jordan', 'kowloon', 'hong kong island', 'new territories']
        text_lower = text.lower()
        
        return any(district in text_lower for district in districts)
    
    def _looks_like_time(self, text: str) -> bool:
        """Check if text looks like operating hours."""
        time_patterns = [r'\d{1,2}:\d{2}', r'\d{1,2}\s*(AM|PM)', r'closed', r'open']
        text_lower = text.lower()
        
        return any(re.search(pattern, text_lower) for pattern in time_patterns)
    
    def _looks_like_description(self, text: str) -> bool:
        """Check if text looks like a description."""
        return len(text) > 20 and len(text) < 200 and not self._looks_like_address(text) and not self._looks_like_time(text)
    
    def _extract_personality_alignment(self, attraction_name: str, enhanced_info: str, mbti_type: str) -> str:
        """Extract personality alignment explanation from enhanced info."""
        
        if not enhanced_info or not attraction_name:
            return f"Suitable for {mbti_type} personality traits"
        
        # Look for explanations about this specific attraction
        lines = enhanced_info.split('\n')
        
        for i, line in enumerate(lines):
            if attraction_name.lower() in line.lower():
                # Look for alignment explanation in nearby lines
                for j in range(max(0, i-2), min(len(lines), i+5)):
                    if 'alignment' in lines[j].lower() or 'mbti' in lines[j].lower() or mbti_type in lines[j]:
                        return lines[j].strip()
        
        return f"Matches {mbti_type} preferences for {self.kb.mbti_traits.get(mbti_type, 'unique characteristics')}"
    
    def _deduplicate_attractions(self, attractions: List[TouristAttraction]) -> List[TouristAttraction]:
        """Remove duplicate attractions based on name similarity."""
        
        unique_attractions = []
        seen_names = set()
        
        for attraction in attractions:
            name_key = attraction.name.lower().strip()
            
            if name_key not in seen_names and len(name_key) > 2:
                seen_names.add(name_key)
                unique_attractions.append(attraction)
        
        return unique_attractions

def generate_mbti_attractions_report(mbti_types: List[str], output_format: str = 'json') -> None:
    """Generate comprehensive attractions report for multiple MBTI types."""
    
    extractor = MBTIAttractionsExtractor()
    
    print("🌟 MBTI Tourist Attractions Report Generator")
    print("=" * 60)
    
    all_results = {}
    
    for mbti_type in mbti_types:
        print(f"\n🎯 Processing {mbti_type} personality type...")
        
        attractions = extractor.get_attractions_for_mbti(mbti_type)
        
        print(f"✅ Found {len(attractions)} attractions for {mbti_type}")
        
        # Convert to dictionaries for JSON serialization
        attractions_data = [attr.to_dict() for attr in attractions]
        all_results[mbti_type] = attractions_data
        
        # Print summary
        if attractions:
            print(f"   Top attraction: {attractions[0].name}")
            print(f"   District: {attractions[0].district}")
    
    # Save results
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format.lower() == 'json':
        filename = f"mbti_attractions_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {filename}")
    
    elif output_format.lower() == 'markdown':
        filename = f"mbti_attractions_{timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# MBTI Tourist Attractions in Hong Kong\n\n")
            
            for mbti_type, attractions in all_results.items():
                f.write(f"## {mbti_type} Personality Type\n\n")
                
                for attr in attractions:
                    f.write(f"### {attr['name']}\n")
                    f.write(f"- **Description**: {attr['description']}\n")
                    f.write(f"- **Address**: {attr['address']}\n")
                    f.write(f"- **District**: {attr['district']}\n")
                    f.write(f"- **Operating Hours**: {attr['operating_hours']['weekday']}\n")
                    f.write(f"- **Personality Alignment**: {attr['personality_alignment']}\n\n")
        
        print(f"\n💾 Markdown report saved to: {filename}")
    
    return all_results

def interactive_mbti_lookup():
    """Interactive script for looking up attractions by MBTI type."""
    
    extractor = MBTIAttractionsExtractor()
    
    print("🎯 Interactive MBTI Tourist Attractions Lookup")
    print("=" * 50)
    
    while True:
        print(f"\nAvailable MBTI types:")
        mbti_types = list(extractor.kb.mbti_traits.keys())
        for i, mbti in enumerate(mbti_types, 1):
            print(f"{i:2d}. {mbti} - {extractor.kb.mbti_traits[mbti][:50]}...")
        
        print(f"\nEnter MBTI type (or 'quit' to exit):")
        user_input = input("> ").strip().upper()
        
        if user_input.lower() == 'quit':
            break
        
        if user_input in mbti_types:
            print(f"\n🔍 Getting attractions for {user_input}...")
            
            attractions = extractor.get_attractions_for_mbti(user_input)
            
            if attractions:
                print(f"\n✅ Found {len(attractions)} attractions for {user_input}:")
                print("-" * 50)
                
                for i, attr in enumerate(attractions, 1):
                    print(f"{i}. **{attr.name}**")
                    print(f"   District: {attr.district}")
                    print(f"   Description: {attr.description}")
                    print(f"   Address: {attr.address}")
                    print(f"   Hours: {attr.operating_hours_weekday}")
                    print(f"   Why it fits {user_input}: {attr.personality_alignment}")
                    print()
            else:
                print(f"❌ No attractions found for {user_input}")
        else:
            print(f"❌ Invalid MBTI type. Please choose from the list above.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        mbti_type = sys.argv[1].upper()
        
        if mbti_type == 'REPORT':
            # Generate full report
            all_mbti_types = ['ENFP', 'INTJ', 'ISFJ', 'ESTP', 'INFP', 'ENTJ', 'ISFP', 'ENTP']
            generate_mbti_attractions_report(all_mbti_types, 'json')
        else:
            # Single MBTI type lookup
            extractor = MBTIAttractionsExtractor()
            attractions = extractor.get_attractions_for_mbti(mbti_type)
            
            print(f"\n🎯 Attractions for {mbti_type}:")
            for attr in attractions:
                print(f"- {attr.name} ({attr.district})")
    else:
        # Interactive mode
        interactive_mbti_lookup()