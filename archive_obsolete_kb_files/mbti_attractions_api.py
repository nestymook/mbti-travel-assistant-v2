#!/usr/bin/env python3
"""
MBTI Tourist Attractions API

Clean interface for getting tourist attractions based on MBTI personality types
using the Nova Pro knowledge base implementation.
"""

import json
from typing import Dict, List, Optional
from improved_mbti_attractions_list import ImprovedMBTIExtractor, TouristAttraction

class MBTIAttractionsAPI:
    """Clean API for MBTI-based tourist attraction recommendations."""
    
    def __init__(self):
        self.extractor = ImprovedMBTIExtractor()
        
        # Load the generated report for quick access
        try:
            with open('mbti_attractions_report_20250929_153601.json', 'r', encoding='utf-8') as f:
                self.cached_data = json.load(f)
        except FileNotFoundError:
            self.cached_data = {}
    
    def get_attractions(self, mbti_type: str, use_cache: bool = True) -> List[Dict]:
        """
        Get tourist attractions for a specific MBTI type.
        
        Args:
            mbti_type: MBTI personality type (e.g., 'ENFP', 'INTJ')
            use_cache: Whether to use cached data or fetch fresh data
            
        Returns:
            List of attraction dictionaries with structured data
        """
        
        mbti_type = mbti_type.upper()
        
        if use_cache and mbti_type in self.cached_data:
            return self.cached_data[mbti_type]
        
        # Fetch fresh data
        attractions = self.extractor.get_attractions_for_mbti(mbti_type)
        return [attr.to_dict() for attr in attractions]
    
    def get_attractions_by_district(self, mbti_type: str, district: str) -> List[Dict]:
        """Get attractions for MBTI type filtered by district."""
        
        attractions = self.get_attractions(mbti_type)
        
        district_lower = district.lower()
        filtered = []
        
        for attr in attractions:
            if district_lower in attr['district'].lower():
                filtered.append(attr)
        
        return filtered
    
    def get_top_attractions(self, mbti_type: str, limit: int = 5) -> List[Dict]:
        """Get top N attractions for MBTI type by relevance score."""
        
        attractions = self.get_attractions(mbti_type)
        
        # Sort by relevance score (descending)
        sorted_attractions = sorted(attractions, key=lambda x: x['relevance_score'], reverse=True)
        
        return sorted_attractions[:limit]
    
    def search_attractions(self, mbti_type: str, keyword: str) -> List[Dict]:
        """Search attractions by keyword in name or description."""
        
        attractions = self.get_attractions(mbti_type)
        keyword_lower = keyword.lower()
        
        matching = []
        
        for attr in attractions:
            if (keyword_lower in attr['name'].lower() or 
                keyword_lower in attr['description'].lower()):
                matching.append(attr)
        
        return matching
    
    def get_attractions_summary(self, mbti_type: str) -> Dict:
        """Get summary statistics for MBTI type attractions."""
        
        attractions = self.get_attractions(mbti_type)
        
        if not attractions:
            return {
                'mbti_type': mbti_type,
                'total_attractions': 0,
                'districts': [],
                'avg_score': 0,
                'top_attraction': None
            }
        
        # Calculate statistics
        districts = list(set(attr['district'] for attr in attractions))
        scores = [attr['relevance_score'] for attr in attractions]
        avg_score = sum(scores) / len(scores)
        top_attraction = max(attractions, key=lambda x: x['relevance_score'])
        
        return {
            'mbti_type': mbti_type,
            'total_attractions': len(attractions),
            'districts': districts,
            'avg_score': round(avg_score, 4),
            'top_attraction': top_attraction['name'],
            'score_range': {
                'min': round(min(scores), 4),
                'max': round(max(scores), 4)
            }
        }
    
    def get_all_mbti_summary(self) -> Dict:
        """Get summary for all MBTI types."""
        
        all_types = ['ENFP', 'INTJ', 'ISFJ', 'ESTP', 'INFP', 'ENTJ', 'ISFP', 'ENTP', 
                    'ISTJ', 'ESFJ', 'INFJ', 'ESTJ', 'ISTP', 'ESFP', 'INTP', 'ENFJ']
        
        summary = {}
        
        for mbti_type in all_types:
            if mbti_type in self.cached_data:
                summary[mbti_type] = self.get_attractions_summary(mbti_type)
        
        return summary
    
    def format_attraction_for_display(self, attraction: Dict) -> str:
        """Format attraction data for human-readable display."""
        
        formatted = f"""
🎯 **{attraction['name']}** ({attraction['mbti_type']})
📍 Address: {attraction['address']}
🏙️ District: {attraction['district']}
📝 Description: {attraction['description']}
⏰ Hours: {attraction['operating_hours']['weekday']}
⭐ Relevance Score: {attraction['relevance_score']:.4f}
"""
        
        if attraction['remarks']:
            formatted += f"💡 Remarks: {attraction['remarks']}\n"
        
        return formatted.strip()

def demo_api_usage():
    """Demonstrate API usage with examples."""
    
    api = MBTIAttractionsAPI()
    
    print("🌟 MBTI Tourist Attractions API Demo")
    print("=" * 50)
    
    # Example 1: Get attractions for ENFP
    print("\n🎯 Example 1: Get attractions for ENFP")
    enfp_attractions = api.get_attractions('ENFP')
    print(f"Found {len(enfp_attractions)} attractions for ENFP")
    
    if enfp_attractions:
        print("\nTop attraction:")
        print(api.format_attraction_for_display(enfp_attractions[0]))
    
    # Example 2: Get top attractions for INTJ
    print("\n🎯 Example 2: Top 3 attractions for INTJ")
    intj_top = api.get_top_attractions('INTJ', limit=3)
    
    for i, attr in enumerate(intj_top, 1):
        print(f"\n{i}. {attr['name']} (Score: {attr['relevance_score']:.4f})")
        print(f"   District: {attr['district']}")
        print(f"   Description: {attr['description'][:100]}...")
    
    # Example 3: Search attractions
    print("\n🎯 Example 3: Search for 'museum' attractions")
    museum_attractions = []
    
    for mbti_type in ['INTJ', 'ISFJ', 'INFP']:
        results = api.search_attractions(mbti_type, 'museum')
        museum_attractions.extend(results)
    
    print(f"Found {len(museum_attractions)} museum-related attractions")
    
    # Example 4: Get summary statistics
    print("\n🎯 Example 4: Summary statistics")
    summary = api.get_attractions_summary('INTJ')
    
    print(f"INTJ Summary:")
    print(f"  Total attractions: {summary['total_attractions']}")
    print(f"  Districts covered: {', '.join(summary['districts'])}")
    print(f"  Average relevance score: {summary['avg_score']}")
    print(f"  Top attraction: {summary['top_attraction']}")
    
    # Example 5: All MBTI types overview
    print("\n🎯 Example 5: All MBTI types overview")
    all_summary = api.get_all_mbti_summary()
    
    print("MBTI Type | Attractions | Top Score | Districts")
    print("-" * 50)
    
    for mbti_type, data in all_summary.items():
        districts_count = len(data['districts'])
        max_score = data['score_range']['max'] if data['total_attractions'] > 0 else 0
        
        print(f"{mbti_type:8} | {data['total_attractions']:11} | {max_score:9.4f} | {districts_count}")

def interactive_lookup():
    """Interactive attraction lookup."""
    
    api = MBTIAttractionsAPI()
    
    print("🔍 Interactive MBTI Attractions Lookup")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Get attractions for MBTI type")
        print("2. Search attractions by keyword")
        print("3. Get attractions by district")
        print("4. Get summary for MBTI type")
        print("5. Quit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            mbti_type = input("Enter MBTI type (e.g., ENFP): ").strip().upper()
            attractions = api.get_attractions(mbti_type)
            
            if attractions:
                print(f"\n✅ Found {len(attractions)} attractions for {mbti_type}:")
                for attr in attractions:
                    print(api.format_attraction_for_display(attr))
                    print("-" * 40)
            else:
                print(f"❌ No attractions found for {mbti_type}")
        
        elif choice == '2':
            mbti_type = input("Enter MBTI type: ").strip().upper()
            keyword = input("Enter search keyword: ").strip()
            
            results = api.search_attractions(mbti_type, keyword)
            
            if results:
                print(f"\n✅ Found {len(results)} attractions matching '{keyword}':")
                for attr in results:
                    print(f"- {attr['name']} ({attr['district']})")
            else:
                print(f"❌ No attractions found matching '{keyword}'")
        
        elif choice == '3':
            mbti_type = input("Enter MBTI type: ").strip().upper()
            district = input("Enter district: ").strip()
            
            results = api.get_attractions_by_district(mbti_type, district)
            
            if results:
                print(f"\n✅ Found {len(results)} attractions in {district}:")
                for attr in results:
                    print(f"- {attr['name']}")
            else:
                print(f"❌ No attractions found in {district}")
        
        elif choice == '4':
            mbti_type = input("Enter MBTI type: ").strip().upper()
            summary = api.get_attractions_summary(mbti_type)
            
            print(f"\n📊 Summary for {mbti_type}:")
            print(f"Total attractions: {summary['total_attractions']}")
            print(f"Districts: {', '.join(summary['districts'])}")
            print(f"Average score: {summary['avg_score']}")
            if summary['top_attraction']:
                print(f"Top attraction: {summary['top_attraction']}")
        
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'demo':
        demo_api_usage()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == 'interactive':
        interactive_lookup()
    else:
        print("🎯 MBTI Tourist Attractions API")
        print("Usage:")
        print("  python mbti_attractions_api.py demo       # Run demo")
        print("  python mbti_attractions_api.py interactive # Interactive mode")
        print("\nOr import as module:")
        print("  from mbti_attractions_api import MBTIAttractionsAPI")
        print("  api = MBTIAttractionsAPI()")
        print("  attractions = api.get_attractions('ENFP')")
        
        # Quick demo
        demo_api_usage()