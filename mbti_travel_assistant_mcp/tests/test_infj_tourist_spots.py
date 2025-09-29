#!/usr/bin/env python3
"""
Test INFJ Tourist Spots Retrieval from Knowledge Base

This script tests the retrieval of INFJ personality type tourist attractions
from the optimized knowledge base with individual attraction files.
"""

import boto3
import json
import re
from typing import List, Dict, Any
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

class INFJTouristSpotTester:
    """Test class for INFJ tourist spot retrieval."""
    
    def __init__(self, kb_id: str = "RCWW86CLM9", region: str = "us-east-1"):
        self.kb_id = kb_id
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
    
    def test_infj_retrieval(self, max_results: int = 15) -> List[TouristAttraction]:
        """Test retrieval of INFJ tourist attractions."""
        
        print("🧪 Testing INFJ Tourist Spots Retrieval")
        print("=" * 50)
        
        # Test different query strategies
        queries = [
            "INFJ personality type tourist attractions Hong Kong",
            "INFJ introverted intuitive feeling judging Hong Kong spots",
            "Hong Kong attractions for INFJ personality",
            "INFJ tourist destinations Hong Kong travel",
            "INFJ recommended places Hong Kong"
        ]
        
        all_attractions = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Query {i}: {query}")
            
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
                
                results = response['retrievalResults']
                print(f"   📊 Retrieved {len(results)} results")
                
                # Parse results
                for result in results:
                    attraction = self._parse_attraction_result(result)
                    if attraction and attraction.mbti_type == 'INFJ':
                        all_attractions.append(attraction)
                        print(f"   ✅ Found: {attraction.name} (Score: {attraction.score:.4f})")
                
            except Exception as e:
                print(f"   ❌ Error with query: {e}")
        
        # Deduplicate attractions by name
        unique_attractions = self._deduplicate_attractions(all_attractions)
        
        print(f"\n📊 Summary:")
        print(f"   Total results found: {len(all_attractions)}")
        print(f"   Unique INFJ attractions: {len(unique_attractions)}")
        
        return unique_attractions
    
    def _parse_attraction_result(self, result: Dict[str, Any]) -> TouristAttraction:
        """Parse a single retrieval result into a TouristAttraction."""
        
        try:
            content = result['content']['text']
            score = result['score']
            source_uri = result['metadata'].get('x-amz-bedrock-kb-source-uri', '')
            
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
            
            # Extract source filename
            source_file = source_uri.split('/')[-1] if source_uri else ""
            
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
    
    def _deduplicate_attractions(self, attractions: List[TouristAttraction]) -> List[TouristAttraction]:
        """Remove duplicate attractions, keeping the highest scored version."""
        
        unique_attractions = {}
        
        for attraction in attractions:
            key = attraction.name.lower().strip()
            
            if key not in unique_attractions or attraction.score > unique_attractions[key].score:
                unique_attractions[key] = attraction
        
        # Sort by score (highest first)
        result = list(unique_attractions.values())
        result.sort(key=lambda x: x.score, reverse=True)
        
        return result
    
    def display_attractions(self, attractions: List[TouristAttraction]):
        """Display the retrieved attractions in a formatted way."""
        
        print(f"\n🎯 INFJ Tourist Attractions in Hong Kong")
        print("=" * 60)
        
        if not attractions:
            print("❌ No INFJ attractions found.")
            return
        
        for i, attraction in enumerate(attractions, 1):
            print(f"\n{i}. **{attraction.name}** (Relevance: {attraction.score:.4f})")
            print(f"   🧠 MBTI Type: {attraction.mbti_type}")
            
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
            
            if attraction.source_file:
                print(f"   📄 Source: {attraction.source_file}")
    
    def export_to_json(self, attractions: List[TouristAttraction], filename: str = "infj_attractions.json"):
        """Export attractions to JSON file."""
        
        data = {
            "mbti_type": "INFJ",
            "personality_description": "Introverted, Intuitive, Feeling, Judging - The Advocate",
            "total_attractions": len(attractions),
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

def test_knowledge_base_status():
    """Test if the knowledge base is ready and accessible."""
    
    print("🔍 Testing Knowledge Base Status")
    print("-" * 30)
    
    try:
        # Test basic connectivity
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        
        # Get knowledge base info
        kb_response = bedrock_agent.get_knowledge_base(knowledgeBaseId='RCWW86CLM9')
        kb_status = kb_response['knowledgeBase']['status']
        print(f"✅ Knowledge Base Status: {kb_status}")
        
        # Get data source info
        ds_response = bedrock_agent.list_data_sources(knowledgeBaseId='RCWW86CLM9')
        data_sources = ds_response['dataSourceSummaries']
        
        for ds in data_sources:
            print(f"✅ Data Source: {ds['name']} - Status: {ds['status']}")
        
        # Check latest ingestion job
        jobs_response = bedrock_agent.list_ingestion_jobs(
            knowledgeBaseId='RCWW86CLM9',
            dataSourceId=data_sources[0]['dataSourceId']
        )
        
        if jobs_response['ingestionJobSummaries']:
            latest_job = jobs_response['ingestionJobSummaries'][0]
            print(f"✅ Latest Ingestion: {latest_job['status']} - {latest_job.get('statistics', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Knowledge Base Error: {e}")
        return False

def main():
    """Main test execution."""
    
    print("🎯 INFJ Tourist Spots Knowledge Base Test")
    print("=" * 60)
    
    # Test knowledge base status first
    if not test_knowledge_base_status():
        print("\n❌ Knowledge base is not ready. Please check the setup.")
        return
    
    # Initialize tester
    tester = INFJTouristSpotTester()
    
    # Retrieve INFJ attractions
    attractions = tester.test_infj_retrieval()
    
    # Display results
    tester.display_attractions(attractions)
    
    # Export to JSON
    if attractions:
        tester.export_to_json(attractions)
        
        # Additional analysis
        print(f"\n📈 Analysis:")
        print(f"   Average relevance score: {sum(a.score for a in attractions) / len(attractions):.4f}")
        print(f"   Score range: {min(a.score for a in attractions):.4f} - {max(a.score for a in attractions):.4f}")
        
        # District distribution
        districts = {}
        for attraction in attractions:
            district = attraction.district if attraction.district != "District not specified" else "Unknown"
            districts[district] = districts.get(district, 0) + 1
        
        print(f"   District distribution: {dict(sorted(districts.items(), key=lambda x: x[1], reverse=True))}")
    
    print(f"\n🎉 Test completed successfully!")

if __name__ == "__main__":
    main()