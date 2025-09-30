#!/usr/bin/env python3
"""
Analyze price range patterns in Hong Kong Island restaurant data.
"""

import json
import os
from collections import Counter
from pathlib import Path

def analyze_price_ranges():
    """Analyze all price ranges in Hong Kong Island restaurant data."""
    
    # Path to Hong Kong Island restaurant data
    data_dir = Path("config/restaurants/hong-kong-island")
    
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        return
    
    price_ranges = []
    district_price_analysis = {}
    total_restaurants = 0
    
    # Process each district file
    for json_file in data_dir.glob("*.json"):
        district_name = json_file.stem.replace("-", " ").title()
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            restaurants = data.get('restaurants', [])
            district_prices = []
            
            for restaurant in restaurants:
                price_range = restaurant.get('priceRange', 'Not specified')
                price_ranges.append(price_range)
                district_prices.append(price_range)
                total_restaurants += 1
            
            # Analyze district-specific price patterns
            district_price_analysis[district_name] = {
                'count': len(restaurants),
                'price_distribution': Counter(district_prices)
            }
            
            print(f"Processed {district_name}: {len(restaurants)} restaurants")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Overall analysis
    price_counter = Counter(price_ranges)
    
    print("\n" + "="*60)
    print("HONG KONG ISLAND RESTAURANT PRICE RANGE ANALYSIS")
    print("="*60)
    
    print(f"\nTotal Restaurants Analyzed: {total_restaurants}")
    print(f"Total Districts: {len(district_price_analysis)}")
    
    print("\n" + "-"*40)
    print("UNIQUE PRICE RANGES IDENTIFIED:")
    print("-"*40)
    
    # Sort price ranges logically
    price_order = [
        "Below $50",
        "$51-100", 
        "$101-200",
        "$201-400",
        "$401-800",
        "Above $801",
        "Not specified"
    ]
    
    for i, price_range in enumerate(price_order, 1):
        count = price_counter.get(price_range, 0)
        percentage = (count / total_restaurants * 100) if total_restaurants > 0 else 0
        print(f"{i}. {price_range:<15} | {count:>4} restaurants ({percentage:>5.1f}%)")
    
    print("\n" + "-"*40)
    print("DISTRICT-WISE PRICE DISTRIBUTION:")
    print("-"*40)
    
    for district, analysis in sorted(district_price_analysis.items()):
        print(f"\n{district} ({analysis['count']} restaurants):")
        
        # Sort by price range order
        for price_range in price_order:
            count = analysis['price_distribution'].get(price_range, 0)
            if count > 0:
                percentage = (count / analysis['count'] * 100)
                print(f"  {price_range:<15} | {count:>3} ({percentage:>5.1f}%)")
    
    print("\n" + "-"*40)
    print("PRICE RANGE DEFINITIONS (HKD):")
    print("-"*40)
    print("Below $50       | Budget-friendly, street food, casual dining")
    print("$51-100         | Affordable dining, local restaurants")
    print("$101-200        | Mid-range dining, popular restaurants")
    print("$201-400        | Upper mid-range, quality dining")
    print("$401-800        | Premium dining, upscale restaurants")
    print("Above $801      | Fine dining, luxury establishments")
    print("Not specified   | Price information unavailable")
    
    # Additional insights
    print("\n" + "-"*40)
    print("KEY INSIGHTS:")
    print("-"*40)
    
    # Most common price range
    most_common = price_counter.most_common(1)[0] if price_counter else ("None", 0)
    print(f"• Most common price range: {most_common[0]} ({most_common[1]} restaurants)")
    
    # Budget vs Premium analysis
    budget_ranges = ["Below $50", "$51-100"]
    premium_ranges = ["$401-800", "Above $801"]
    
    budget_count = sum(price_counter.get(pr, 0) for pr in budget_ranges)
    premium_count = sum(price_counter.get(pr, 0) for pr in premium_ranges)
    
    budget_pct = (budget_count / total_restaurants * 100) if total_restaurants > 0 else 0
    premium_pct = (premium_count / total_restaurants * 100) if total_restaurants > 0 else 0
    
    print(f"• Budget dining (≤$100): {budget_count} restaurants ({budget_pct:.1f}%)")
    print(f"• Premium dining (≥$401): {premium_count} restaurants ({premium_pct:.1f}%)")
    
    # Districts with most premium restaurants
    premium_districts = []
    for district, analysis in district_price_analysis.items():
        premium_in_district = sum(analysis['price_distribution'].get(pr, 0) for pr in premium_ranges)
        if premium_in_district > 0:
            premium_pct_district = (premium_in_district / analysis['count'] * 100)
            premium_districts.append((district, premium_in_district, premium_pct_district))
    
    premium_districts.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\n• Districts with highest premium dining concentration:")
    for district, count, pct in premium_districts[:5]:
        print(f"  - {district}: {count} premium restaurants ({pct:.1f}%)")

if __name__ == "__main__":
    analyze_price_ranges()