#!/usr/bin/env python3
"""
Test ALL INFJ Tourist Spots Retrieval

This script ensures we retrieve ALL 13 INFJ attractions from the knowledge base
by using multiple query strategies and higher result limits.
"""

import boto3
import json
import re
from typing import List, Dict, Any, Set
from dataclasses import dataclass

@dataclass
class TouristAttraction:
    """Structured tourist attraction data."""
    name: str
    mbti_type: str
    description: str
    address: str
    district: str
    area: str
    operating_hours_weekday: str
    operating_hours_weekend: str
    operating_hours_holiday: str
    contact_remarks: str
    score: float
    source_file: str

class ComprehensiveINFJTester:
    """Comprehensive tester to retrieve ALL INFJ attractions."""
    
    def __init__(self, kb_id: str = "RCWW86CLM9", region: str = "us-east-1"):
        self.kb_id = kb_id
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Expected INFJ attractions based on S3 files
        self.expected_infj_files = [
            'INFJ_Broadway_Cinematheque.md',
            'INFJ_Central_Market.md',
            'INFJ_Hong_Kong_Cultural_Centre.md',
            'INFJ_Hong_Kong_House_of_Stories.md',
            'INFJ_Hong_Kong_Museum_of_Art.md',
            'INFJ_Hong_Kong_Palace_Museum.md',
            'INFJ_M+.md',
            'INFJ_Man_Mo_Temple.md',
            'INFJ_PMQ_Police_Married_Quarters.md',
            'INFJ_Pacific_Place_Rooftop_Garden.md',
            'INFJ_Po_Lin_Monastery.md',
            'INFJ_SoHo_and_Central_Art_Galleries.md',
            'INFJ_Tai_Kwun.md'
        ]
    
    def retrieve_all_infj_attractions(self) -> List[TouristAttraction]:
        """Retrieve ALL INFJ attractions using comprehensive search strategies."""
        
        print("🎯 Comprehensive INFJ Attractions Retrieval")
        print("=" * 50)
        print(f"📋 Expected INFJ files: {len(self.expected_infj_files)}")
        
        all_attractions = []
        found_files = set()
        
        # Strategy 1: High-limit broad queries
        broad_queries = [
            "INFJ personality type Hong Kong tourist attractions",
            "INFJ introverted intuitive feeling judging Hong Kong",
            "Hong Kong attractions for INFJ personality",
            "INFJ recommended places Hong Kong travel",
            "INFJ tourist destinations Hong Kong spots",
            "Hong Kong INFJ personality matches",
            "INFJ suitable attractions Hong Kong",
            "Hong Kong tourist spots INFJ type"
        ]
        
        for i, query in enumerate(broad_queries, 1):
            print(f"\n🔍 Broad Query {i}: {query}")
            attractions = self._query_knowledge_base(query, max_results=25)
            
            for attraction in attractions:
                if attraction.source_file not in found_files:
                    all_attractions.append(attraction)
                    found_files.add(attraction.source_file)
                    print(f"   ✅ New: {attraction.name} ({attraction.source_file})")
        
        print(f"\n📊 After broad queries: {len(found_files)} unique files found")
        
        # Strategy 2: Specific attraction name queries
        # Extract expected attraction names from filenames
        attraction_names = []
        for filename in self.expected_infj_files:
            # Extract name from filename (remove INFJ_ prefix and .md suffix)
            name_part = filename.replace('INFJ_', '').replace('.md', '').replace('_', ' ')
            attraction_names.append(name_part)
        
        for name in attraction_names:
            if len(found_files) >= len(self.expected_infj_files):
                break
                
            query = f"Hong Kong {name} INFJ personality"
            print(f"\n🎯 Specific Query: {query}")
            attractions = self._query_knowledge_base(query, max_results=10)
            
            for attraction in attractions:
                if attraction.source_file not in found_files:
                    all_attractions.append(attraction)
                    found_files.add(attraction.source_file)
                    print(f"   ✅ New: {attraction.name} ({attraction.source_file})")
        
        print(f"\n📊 After specific queries: {len(found_files)} unique files found")
        
        # Strategy 3: Category-based queries
        category_queries = [
            "Hong Kong museums INFJ personality type",
            "Hong Kong art galleries INFJ suitable",
            "Hong Kong cultural centers INFJ recommended",
            "Hong Kong temples INFJ personality",
            "Hong Kong markets INFJ type attractions",
            "Hong Kong theaters INFJ personality matches"
        ]
        
        for query in category_queries:
            if len(found_files) >= len(self.expected_infj_files):
                break
                
            print(f"\n🏛️ Category Query: {query}")
            attractions = self._query_knowledge_base(query, max_results=15)
            
            for attraction in attractions:
                if attraction.source_file not in found_files:
                    all_attractions.append(attraction)
                    found_files.add(attraction.source_file)
                    print(f"   ✅ New: {attraction.name} ({attraction.source_file})")
        
        print(f"\n📊 Final Results:")
        print(f"   Expected files: {len(self.expected_infj_files)}")
        print(f"   Found files: {len(found_files)}")
        print(f"   Success rate: {len(found_files)/len(self.expected_infj_files)*100:.1f}%")
        
        # Check for missing files
        missing_files = set(self.expected_infj_files) - found_files
        if missing_files:
            print(f"\n❌ Missing files:")
            for missing in missing_files:
                print(f"   - {missing}")
        else:
            print(f"\n✅ All expected INFJ files found!")
        
        # Sort by relevance score
        all_attractions.sort(key=lambda x: x.score, reverse=True)
        
        return all_attractions
    
    def _query_knowledge_base(self, query: str, max_results: int = 15) -> List[TouristAttraction]:
        """Query the knowledge base with specific parameters."""
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            attractions = []
            for result in response['retrievalResults']:
                attraction = self._parse_attraction_result(result)
                if attraction and attraction.mbti_type == 'INFJ':
                    attractions.append(attraction)
            
            print(f"   📊 Retrieved {len(attractions)} INFJ attractions")
            return attractions
            
        except Exception as e:
            print(f"   ❌ Error with query: {e}")
            return []
    
    def _parse_attraction_result(self, result: Dict[str, Any]) -> TouristAttraction:
        """Parse a single retrieval result into a TouristAttraction."""
        
        try:
            content = result['content']['text']
            score = result['score']
            source_uri = result['metadata'].get('x-amz-bedrock-kb-source-uri', '')
            
            # Extract source filename
            source_file = source_uri.split('/')[-1] if source_uri else ""
            
            # Extract attraction name from title
            name_match = re.search(r'^#\s*(.+)$', content, re.MULTILINE)
            name = name_match.group(1).strip() if name_match else "Unknown Attraction"
            
            # Extract MBTI type
            mbti_match = re.search(r'\*\*Type:\*\*\s*(\w+)', content)
            mbti_type = mbti_match.group(1) if mbti_match else ""
            
            # Extract description
            desc_match = re.search(r'\*\*Description:\*\*\s*(.+)', content)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Extract address
            addr_match = re.search(r'\*\*Address:\*\*\s*(.+)', content)
            address = addr_match.group(1).strip() if addr_match else ""
            
            # Extract district
            district_match = re.search(r'\*\*District:\*\*\s*(.+)', content)
            district = district_match.group(1).strip() if district_match else ""
            
            # Extract area
            area_match = re.search(r'\*\*Area:\*\*\s*(.+)', content)
            area = area_match.group(1).strip() if area_match else ""
            
            # Extract operating hours
            weekday_match = re.search(r'\*\*Weekdays \(Mon-Fri\):\*\*\s*(.+)', content)
            weekday_hours = weekday_match.group(1).strip() if weekday_match else ""
            
            weekend_match = re.search(r'\*\*Weekends \(Sat-Sun\):\*\*\s*(.+)', content)
            weekend_hours = weekend_match.group(1).strip() if weekend_match else ""
            
            holiday_match = re.search(r'\*\*Public Holidays:\*\*\s*(.+)', content)
            holiday_hours = holiday_match.group(1).strip() if holiday_match else ""
            
            # Extract contact/remarks
            contact_match = re.search(r'\*\*Contact/Remarks:\*\*\s*(.+)', content)
            contact_remarks = contact_match.group(1).strip() if contact_match else ""
            
            return TouristAttraction(
                name=name,
                mbti_type=mbti_type,
                description=description,
                address=address,
                district=district,
                area=area,
                operating_hours_weekday=weekday_hours,
                operating_hours_weekend=weekend_hours,
                operating_hours_holiday=holiday_hours,
                contact_remarks=contact_remarks,
                score=score,
                source_file=source_file
            )
            
        except Exception as e:
            print(f"   ⚠️ Error parsing result: {e}")
            return None
    
    def display_all_attractions(self, attractions: List[TouristAttraction]):
        """Display all retrieved attractions."""
        
        print(f"\n🎯 Complete INFJ Tourist Attractions List")
        print("=" * 60)
        
        if not attractions:
            print("❌ No INFJ attractions found.")
            return
        
        for i, attraction in enumerate(attractions, 1):
            print(f"\n{i}. **{attraction.name}** (Score: {attraction.score:.4f})")
            print(f"   📄 Source: {attraction.source_file}")
            
            if attraction.description:
                print(f"   📝 Description: {attraction.description}")
            
            if attraction.address and attraction.address != "Address not specified":
                print(f"   📍 Address: {attraction.address}")
            
            if attraction.district and attraction.district != "District not specified":
                print(f"   🏙️ District: {attraction.district}")
            
            if attraction.area and attraction.area != "Location not specified":
                print(f"   🌏 Area: {attraction.area}")
            
            # Operating hours
            hours_info = []
            if attraction.operating_hours_weekday and attraction.operating_hours_weekday != "Hours not specified":
                hours_info.append(f"Weekdays: {attraction.operating_hours_weekday}")
            if attraction.operating_hours_weekend and attraction.operating_hours_weekend != "Hours not specified":
                hours_info.append(f"Weekends: {attraction.operating_hours_weekend}")
            if attraction.operating_hours_holiday and attraction.operating_hours_holiday != "Hours not specified":
                hours_info.append(f"Holidays: {attraction.operating_hours_holiday}")
            
            if hours_info:
                print(f"   🕒 Hours: {' | '.join(hours_info)}")
            
            if attraction.contact_remarks and attraction.contact_remarks.strip():
                print(f"   📞 Contact: {attraction.contact_remarks}")
    
    def export_complete_json(self, attractions: List[TouristAttraction], filename: str = "complete_infj_attractions.json"):
        """Export all attractions to JSON file."""
        
        data = {
            "mbti_type": "INFJ",
            "personality_description": "Introverted, Intuitive, Feeling, Judging - The Advocate",
            "total_attractions": len(attractions),
            "expected_attractions": len(self.expected_infj_files),
            "retrieval_completeness": f"{len(attractions)}/{len(self.expected_infj_files)} ({len(attractions)/len(self.expected_infj_files)*100:.1f}%)",
            "retrieval_timestamp": __import__('datetime').datetime.now().isoformat(),
            "attractions": []
        }
        
        for attraction in attractions:
            data["attractions"].append({
                "name": attraction.name,
                "mbti_type": attraction.mbti_type,
                "description": attraction.description,
                "location": {
                    "address": attraction.address,
                    "district": attraction.district,
                    "area": attraction.area
                },
                "operating_hours": {
                    "weekdays": attraction.operating_hours_weekday,
                    "weekends": attraction.operating_hours_weekend,
                    "holidays": attraction.operating_hours_holiday
                },
                "contact_remarks": attraction.contact_remarks,
                "relevance_score": attraction.score,
                "source_file": attraction.source_file
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Exported {len(attractions)} attractions to {filename}")

def main():
    """Main comprehensive test execution."""
    
    print("🎯 Comprehensive INFJ Tourist Spots Retrieval Test")
    print("=" * 60)
    
    # Initialize comprehensive tester
    tester = ComprehensiveINFJTester()
    
    # Retrieve ALL INFJ attractions
    attractions = tester.retrieve_all_infj_attractions()
    
    # Display results
    tester.display_all_attractions(attractions)
    
    # Export to JSON
    if attractions:
        tester.export_complete_json(attractions)
        
        # Analysis
        print(f"\n📈 Comprehensive Analysis:")
        print(f"   Total attractions found: {len(attractions)}")
        print(f"   Expected attractions: {len(tester.expected_infj_files)}")
        print(f"   Retrieval completeness: {len(attractions)/len(tester.expected_infj_files)*100:.1f}%")
        print(f"   Average relevance score: {sum(a.score for a in attractions) / len(attractions):.4f}")
        print(f"   Score range: {min(a.score for a in attractions):.4f} - {max(a.score for a in attractions):.4f}")
        
        # Source file analysis
        found_files = {a.source_file for a in attractions}
        missing_files = set(tester.expected_infj_files) - found_files
        
        if missing_files:
            print(f"\n❌ Still missing {len(missing_files)} files:")
            for missing in sorted(missing_files):
                print(f"   - {missing}")
        else:
            print(f"\n✅ Perfect! All {len(tester.expected_infj_files)} INFJ files retrieved!")
    
    print(f"\n🎉 Comprehensive test completed!")

if __name__ == "__main__":
    main()