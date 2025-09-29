#!/usr/bin/env python3
"""
Improved MBTI Tourist Attractions List Generator

This script extracts structured tourist attraction data for specific MBTI types
with better parsing of the markdown table format.
"""

import boto3
import json
import re
from typing import Dict, List, Optional, Tuple
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
    score: float
    
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
            'relevance_score': self.score
        }

class ImprovedMBTIExtractor:
    """Improved extractor for MBTI tourist attractions."""
    
    def __init__(self):
        self.kb = NovaProKnowledgeBase()
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Known Hong Kong districts for validation
        self.hk_districts = {
            'central', 'wan chai', 'causeway bay', 'admiralty', 'sheung wan',
            'tsim sha tsui', 'mong kok', 'yau ma tei', 'jordan', 'hung hom',
            'sha tin', 'tai po', 'tuen mun', 'yuen long', 'kwun tong',
            'wong tai sin', 'sham shui po', 'kowloon city', 'eastern',
            'southern', 'western', 'islands', 'north', 'sai kung'
        }
    
    def get_attractions_for_mbti(self, mbti_type: str, max_results: int = 10) -> List[TouristAttraction]:
        """Get structured list of attractions for specific MBTI type."""
        
        print(f"🔍 Extracting attractions for {mbti_type} personality type...")
        
        # Get raw data with multiple query strategies
        all_raw_data = []
        
        # Strategy 1: Direct MBTI query
        raw_data_1 = self._get_raw_data_with_query(f"{mbti_type} personality tourist attractions Hong Kong")
        all_raw_data.extend(raw_data_1)
        
        # Strategy 2: MBTI + traits query
        traits = self.kb.mbti_traits.get(mbti_type, '')
        raw_data_2 = self._get_raw_data_with_query(f"{mbti_type} {traits} Hong Kong tourist spots")
        all_raw_data.extend(raw_data_2)
        
        # Strategy 3: Broader search
        raw_data_3 = self._get_raw_data_with_query(f"Hong Kong tourist attractions {mbti_type}")
        all_raw_data.extend(raw_data_3)
        
        print(f"📊 Retrieved {len(all_raw_data)} raw data points")
        
        # Parse and structure the data
        attractions = self._parse_all_attractions(all_raw_data, mbti_type)
        
        # Deduplicate and rank
        unique_attractions = self._deduplicate_and_rank(attractions)
        
        return unique_attractions[:max_results]
    
    def _get_raw_data_with_query(self, query: str) -> List[Dict]:
        """Get raw data for a specific query."""
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 8
                    }
                }
            )
            
            return response['retrievalResults']
            
        except Exception as e:
            print(f"⚠️ Error with query '{query}': {e}")
            return []
    
    def _parse_all_attractions(self, raw_data: List[Dict], mbti_type: str) -> List[TouristAttraction]:
        """Parse all raw data into structured attractions."""
        
        attractions = []
        
        for item in raw_data:
            content = item['content']['text']
            score = item['score']
            
            # Try different parsing strategies
            parsed_attractions = self._parse_table_content(content, mbti_type, score)
            attractions.extend(parsed_attractions)
        
        return attractions
    
    def _parse_table_content(self, content: str, mbti_type: str, score: float) -> List[TouristAttraction]:
        """Parse table-formatted content into attractions."""
        
        attractions = []
        
        try:
            # Split content into lines and look for table rows
            lines = content.split('\n')
            
            for line in lines:
                if '|' in line and len(line.split('|')) >= 5:
                    # This looks like a table row
                    attraction = self._parse_table_row(line, mbti_type, score)
                    if attraction:
                        attractions.append(attraction)
            
            # If no table rows found, try parsing as continuous text
            if not attractions:
                attraction = self._parse_continuous_text(content, mbti_type, score)
                if attraction:
                    attractions.append(attraction)
        
        except Exception as e:
            print(f"⚠️ Error parsing content: {e}")
        
        return attractions
    
    def _parse_table_row(self, row: str, mbti_type: str, score: float) -> Optional[TouristAttraction]:
        """Parse a single table row into an attraction."""
        
        try:
            # Split by | and clean up
            parts = [part.strip() for part in row.split('|')]
            
            # Filter out empty parts and common headers
            filtered_parts = []
            for part in parts:
                if part and part not in ['', 'Tourist Spot', 'MBTI', 'Description', 'Remarks', 'Address', 'District', 'Location', 'Operating Hours (Mon-Fri)', 'Operating Hours (Sat-Sun)', 'Operating Hours (Public Holiday)', 'Full Day']:
                    filtered_parts.append(part)
            
            if len(filtered_parts) < 3:
                return None
            
            # Try to identify components
            name = ""
            description = ""
            address = ""
            district = ""
            hours_weekday = ""
            hours_weekend = ""
            hours_holiday = ""
            remarks = ""
            found_mbti = ""
            
            for part in filtered_parts:
                part_lower = part.lower()
                
                # Check if this part contains the MBTI type
                if mbti_type.lower() in part_lower:
                    found_mbti = mbti_type
                
                # Identify attraction name (usually first meaningful part)
                elif not name and self._is_likely_attraction_name(part):
                    name = part
                
                # Identify district
                elif self._is_hong_kong_district(part):
                    district = part
                
                # Identify address
                elif self._is_likely_address(part):
                    address = part
                
                # Identify operating hours
                elif self._is_likely_operating_hours(part):
                    if not hours_weekday:
                        hours_weekday = part
                    elif not hours_weekend:
                        hours_weekend = part
                    else:
                        hours_holiday = part
                
                # Everything else could be description or remarks
                elif len(part) > 10 and not description:
                    description = part
                elif len(part) > 5 and not remarks:
                    remarks = part
            
            # Only create attraction if we have a name and it matches the MBTI type
            if name and (found_mbti or mbti_type.lower() in row.lower()):
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
                    score=score
                )
        
        except Exception as e:
            print(f"⚠️ Error parsing table row: {e}")
        
        return None
    
    def _parse_continuous_text(self, content: str, mbti_type: str, score: float) -> Optional[TouristAttraction]:
        """Parse continuous text content."""
        
        # Look for attraction names in the content
        lines = content.split('\n')
        
        for line in lines:
            if mbti_type in line and len(line) > 20:
                # Try to extract attraction name from this line
                words = line.split()
                
                # Look for capitalized words that might be attraction names
                potential_names = []
                for i, word in enumerate(words):
                    if word.istitle() and len(word) > 3:
                        # Check if next few words are also capitalized (compound name)
                        name_parts = [word]
                        for j in range(i+1, min(i+4, len(words))):
                            if words[j].istitle() or words[j] in ['of', 'and', 'the']:
                                name_parts.append(words[j])
                            else:
                                break
                        
                        potential_name = ' '.join(name_parts)
                        if len(potential_name) > 5:
                            potential_names.append(potential_name)
                
                if potential_names:
                    # Use the longest potential name
                    name = max(potential_names, key=len)
                    
                    return TouristAttraction(
                        name=name,
                        mbti_type=mbti_type,
                        description=line[:100] + "..." if len(line) > 100 else line,
                        address="Address not specified",
                        district="District not specified",
                        operating_hours_weekday="Hours not specified",
                        operating_hours_weekend="Hours not specified",
                        operating_hours_holiday="Hours not specified",
                        remarks="",
                        score=score
                    )
        
        return None
    
    def _is_likely_attraction_name(self, text: str) -> bool:
        """Check if text is likely an attraction name."""
        if len(text) < 3 or len(text) > 80:
            return False
        
        # Common attraction keywords
        attraction_keywords = [
            'museum', 'temple', 'park', 'market', 'center', 'centre', 'gallery',
            'tower', 'building', 'plaza', 'square', 'hall', 'house', 'palace',
            'garden', 'beach', 'bay', 'island', 'peak', 'hill', 'bridge'
        ]
        
        text_lower = text.lower()
        
        # Check for attraction keywords or proper noun format
        has_keywords = any(keyword in text_lower for keyword in attraction_keywords)
        is_proper_noun = text.istitle() or any(word.istitle() for word in text.split())
        
        return has_keywords or is_proper_noun
    
    def _is_hong_kong_district(self, text: str) -> bool:
        """Check if text is a Hong Kong district."""
        text_lower = text.lower().strip()
        
        # Direct match
        if text_lower in self.hk_districts:
            return True
        
        # Partial match
        for district in self.hk_districts:
            if district in text_lower or text_lower in district:
                return True
        
        return False
    
    def _is_likely_address(self, text: str) -> bool:
        """Check if text looks like an address."""
        if len(text) < 10:
            return False
        
        address_keywords = [
            'road', 'street', 'avenue', 'drive', 'lane', 'path', 'way',
            'floor', 'building', 'tower', 'plaza', 'square', 'centre', 'center'
        ]
        
        text_lower = text.lower()
        
        # Check for address keywords and numbers
        has_keywords = any(keyword in text_lower for keyword in address_keywords)
        has_numbers = any(char.isdigit() for char in text)
        
        return has_keywords and has_numbers
    
    def _is_likely_operating_hours(self, text: str) -> bool:
        """Check if text looks like operating hours."""
        if len(text) < 4:
            return False
        
        time_patterns = [
            r'\d{1,2}:\d{2}',  # 10:00
            r'\d{1,2}\s*(AM|PM)',  # 10 AM
            r'closed',
            r'open',
            r'24/7',
            r'daily'
        ]
        
        text_lower = text.lower()
        
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in time_patterns)
    
    def _deduplicate_and_rank(self, attractions: List[TouristAttraction]) -> List[TouristAttraction]:
        """Remove duplicates and rank by relevance."""
        
        # Group by similar names
        unique_attractions = {}
        
        for attraction in attractions:
            # Create a key for deduplication
            key = attraction.name.lower().strip()
            
            # If we haven't seen this attraction or this one has a better score
            if key not in unique_attractions or attraction.score > unique_attractions[key].score:
                unique_attractions[key] = attraction
        
        # Convert back to list and sort by score
        result = list(unique_attractions.values())
        result.sort(key=lambda x: x.score, reverse=True)
        
        return result

def test_mbti_extraction(mbti_type: str):
    """Test the extraction for a specific MBTI type."""
    
    extractor = ImprovedMBTIExtractor()
    
    print(f"🧪 Testing extraction for {mbti_type}")
    print("=" * 50)
    
    attractions = extractor.get_attractions_for_mbti(mbti_type)
    
    if attractions:
        print(f"✅ Found {len(attractions)} attractions for {mbti_type}:")
        print()
        
        for i, attr in enumerate(attractions, 1):
            print(f"{i}. **{attr.name}** (Score: {attr.score:.4f})")
            print(f"   MBTI Type: {attr.mbti_type}")
            print(f"   Description: {attr.description}")
            print(f"   Address: {attr.address}")
            print(f"   District: {attr.district}")
            print(f"   Operating Hours: {attr.operating_hours_weekday}")
            if attr.remarks:
                print(f"   Remarks: {attr.remarks}")
            print()
    else:
        print(f"❌ No attractions found for {mbti_type}")
    
    return attractions

def generate_json_report(mbti_types: List[str]):
    """Generate JSON report for multiple MBTI types."""
    
    extractor = ImprovedMBTIExtractor()
    
    print("📊 Generating comprehensive MBTI attractions report...")
    
    all_results = {}
    
    for mbti_type in mbti_types:
        print(f"\n🔍 Processing {mbti_type}...")
        attractions = extractor.get_attractions_for_mbti(mbti_type)
        all_results[mbti_type] = [attr.to_dict() for attr in attractions]
        print(f"   Found {len(attractions)} attractions")
    
    # Save to JSON file
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"mbti_attractions_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Report saved to: {filename}")
    return all_results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mbti_type = sys.argv[1].upper()
        
        if mbti_type == 'REPORT':
            # Generate report for all major MBTI types
            major_types = ['ENFP', 'INTJ', 'ISFJ', 'ESTP', 'INFP', 'ENTJ', 'ISFP', 'ENTP']
            generate_json_report(major_types)
        else:
            # Test single MBTI type
            test_mbti_extraction(mbti_type)
    else:
        # Interactive mode
        print("🎯 MBTI Tourist Attractions Extractor")
        print("Usage: python improved_mbti_attractions_list.py [MBTI_TYPE]")
        print("Example: python improved_mbti_attractions_list.py ENFP")
        print("Or: python improved_mbti_attractions_list.py REPORT")
        
        # Default test
        test_mbti_extraction('ENFP')