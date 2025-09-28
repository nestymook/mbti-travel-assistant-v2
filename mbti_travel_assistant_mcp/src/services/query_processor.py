"""
Natural Language Query Processing Pipeline for Restaurant Search

This module provides utilities for processing natural language queries,
extracting intent and parameters, and formatting conversational responses
for the restaurant search conversational agent.

Requirements: 9.1, 11.1, 11.2, 13.1
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from difflib import get_close_matches

from src.models.restaurant_models import Restaurant


@dataclass
class QueryIntent:
    """Represents the extracted intent from a natural language query."""
    intent_type: str  # 'district_search', 'meal_search', 'combined_search', 'general_help'
    districts: List[str]
    meal_types: List[str]
    cuisine_types: List[str]
    confidence: float
    original_query: str


@dataclass
class QueryResponse:
    """Represents a formatted response for a query."""
    response_text: str
    suggested_actions: List[str]
    tool_calls_made: List[Dict[str, Any]]
    error_message: Optional[str] = None


class QueryProcessor:
    """Natural language query processor for restaurant search."""
    
    def __init__(self, district_service=None):
        """Initialize query processor.
        
        Args:
            district_service: District service for validation (optional).
        """
        self.district_service = district_service
        
        # District name mappings for common variations
        self.district_mappings = {
            'central': 'Central district',
            'tst': 'Tsim Sha Tsui',
            'tsim sha tsui': 'Tsim Sha Tsui',
            'causeway': 'Causeway Bay',
            'causeway bay': 'Causeway Bay',
            'wan chai': 'Wan Chai',
            'wanchai': 'Wan Chai',
            'admiralty': 'Admiralty',
            'mong kok': 'Mong Kok',
            'mongkok': 'Mong Kok',
            'yau ma tei': 'Yau Ma Tei',
            'jordan': 'Jordan',
            'sha tin': 'Sha Tin',
            'shatin': 'Sha Tin',
            'tsuen wan': 'Tsuen Wan',
            'tuen mun': 'Tuen Mun',
            'tai po': 'Tai Po',
            'sheung wan': 'Sheung Wan',
            'mid levels': 'Mid-Levels',
            'mid-levels': 'Mid-Levels',
            'happy valley': 'Happy Valley',
            'north point': 'North Point'
        }
        
        # Meal type mappings
        self.meal_mappings = {
            'breakfast': 'breakfast',
            'morning': 'breakfast',
            'brunch': 'breakfast',
            'lunch': 'lunch',
            'afternoon': 'lunch',
            'dinner': 'dinner',
            'evening': 'dinner',
            'supper': 'dinner',
            'night': 'dinner'
        }
        
        # Common cuisine types
        self.cuisine_types = [
            'chinese', 'cantonese', 'dim sum', 'japanese', 'sushi', 'korean',
            'thai', 'vietnamese', 'indian', 'italian', 'french', 'american',
            'western', 'seafood', 'bbq', 'hotpot', 'noodles', 'rice',
            'vegetarian', 'vegan', 'halal', 'cafe', 'dessert', 'bakery'
        ]
        
        # Query pattern regexes
        self.patterns = {
            'district_only': [
                r'restaurants?\s+in\s+([^,]+?)(?:\s|$)',
                r'find\s+(?:places?|restaurants?)\s+in\s+([^,]+?)(?:\s|$)',
                r'what\'?s\s+good\s+in\s+([^,]+?)(?:\s|$)',
                r'([^,]+?)\s+restaurants?(?:\s|$)',
                r'(?:good\s+)?(?:places?|restaurants?)\s+(?:at|in)\s+([^,]+?)(?:\s|$)'
            ],
            'meal_only': [
                r'(\w+)\s+(?:places?|restaurants?|spots?)(?:\s|$)',
                r'where\s+(?:to\s+)?(?:get|find|eat)\s+(\w+)(?:\s|$)',
                r'good\s+(\w+)\s+(?:places?|spots?)(?:\s|$)',
                r'(\w+)\s+food(?:\s|$)'
            ],
            'combined': [
                r'(\w+)\s+(?:places?|restaurants?|spots?)\s+(?:in|at)\s+([^,]+?)(?:\s|$)',
                r'(\w+)\s+in\s+([^,]+?)(?:\s|$)',
                r'find\s+(\w+)\s+restaurants?\s+(?:in|at)\s+([^,]+?)(?:\s|$)',
                r'(?:good\s+)?(\w+)\s+(?:places?|spots?)\s+(?:in|at)\s+([^,]+?)(?:\s|$)'
            ],
            'cuisine_specific': [
                r'(\w+)\s+restaurants?\s+(?:in|at)\s+([^,]+?)(?:\s|$)',
                r'good\s+(\w+)\s+(?:food\s+)?(?:in|at)\s+([^,]+?)(?:\s|$)',
                r'(\w+)\s+(?:places?|food)\s+(?:for\s+)?(\w+)(?:\s|$)'
            ]
        }
    
    def extract_intent(self, query: str) -> QueryIntent:
        """Extract intent and parameters from natural language query.
        
        Args:
            query: Natural language query string.
            
        Returns:
            QueryIntent object with extracted information.
        """
        query_lower = query.lower().strip()
        
        # Initialize intent
        intent = QueryIntent(
            intent_type='general_help',
            districts=[],
            meal_types=[],
            cuisine_types=[],
            confidence=0.0,
            original_query=query
        )
        
        # Extract districts
        districts = self.extract_districts(query_lower)
        intent.districts = districts
        
        # Extract meal types
        meal_types = self.extract_meal_types(query_lower)
        intent.meal_types = meal_types
        
        # Extract cuisine types
        cuisine_types = self.extract_cuisine_types(query_lower)
        intent.cuisine_types = cuisine_types
        
        # Determine intent type and confidence
        if districts and meal_types:
            intent.intent_type = 'combined_search'
            intent.confidence = 0.9
        elif districts:
            intent.intent_type = 'district_search'
            intent.confidence = 0.8
        elif meal_types:
            intent.intent_type = 'meal_search'
            intent.confidence = 0.8
        elif cuisine_types:
            intent.intent_type = 'cuisine_search'
            intent.confidence = 0.7
        elif any(word in query_lower for word in ['help', 'what', 'how', 'can you']):
            intent.intent_type = 'general_help'
            intent.confidence = 0.6
        else:
            # Try pattern matching for better extraction
            intent = self._pattern_based_extraction(query_lower, intent)
        
        return intent
    
    def extract_districts(self, query: str) -> List[str]:
        """Extract district names from query text.
        
        Args:
            query: Query text (should be lowercase).
            
        Returns:
            List of normalized district names.
        """
        districts = []
        
        # Check direct mappings first
        for variant, canonical in self.district_mappings.items():
            if variant in query:
                if canonical not in districts:
                    districts.append(canonical)
        
        # Pattern-based extraction
        for pattern in self.patterns['district_only']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                district = match.strip()
                normalized = self._normalize_district_name(district)
                if normalized and normalized not in districts:
                    districts.append(normalized)
        
        return districts
    
    def extract_meal_types(self, query: str) -> List[str]:
        """Extract meal types from query text.
        
        Args:
            query: Query text (should be lowercase).
            
        Returns:
            List of normalized meal types.
        """
        meal_types = []
        
        # Check direct mappings
        for variant, canonical in self.meal_mappings.items():
            if variant in query:
                if canonical not in meal_types:
                    meal_types.append(canonical)
        
        # Pattern-based extraction
        for pattern in self.patterns['meal_only']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                meal = match.strip().lower()
                if meal in self.meal_mappings:
                    canonical = self.meal_mappings[meal]
                    if canonical not in meal_types:
                        meal_types.append(canonical)
        
        return meal_types
    
    def extract_cuisine_types(self, query: str) -> List[str]:
        """Extract cuisine types from query text.
        
        Args:
            query: Query text (should be lowercase).
            
        Returns:
            List of cuisine types found.
        """
        cuisine_types = []
        
        for cuisine in self.cuisine_types:
            if cuisine in query:
                cuisine_types.append(cuisine)
        
        return cuisine_types
    
    def validate_districts(self, districts: List[str]) -> Tuple[List[str], List[str]]:
        """Validate district names against available districts.
        
        Args:
            districts: List of district names to validate.
            
        Returns:
            Tuple of (valid_districts, invalid_districts).
        """
        if not self.district_service:
            # If no district service, assume all are valid
            return districts, []
        
        valid_districts = []
        invalid_districts = []
        
        for district in districts:
            if self.district_service.validate_district(district):
                valid_districts.append(district)
            else:
                invalid_districts.append(district)
        
        return valid_districts, invalid_districts
    
    def suggest_alternatives(self, invalid_districts: List[str]) -> List[str]:
        """Suggest alternative district names for invalid ones.
        
        Args:
            invalid_districts: List of invalid district names.
            
        Returns:
            List of suggested alternatives.
        """
        suggestions = []
        
        if not self.district_service:
            # Fallback to common districts
            all_districts = list(self.district_mappings.values())
        else:
            all_districts = []
            district_dict = self.district_service.get_all_districts()
            for region_districts in district_dict.values():
                all_districts.extend(region_districts)
        
        # Add district mapping keys for better matching
        all_searchable = all_districts + list(self.district_mappings.keys())
        
        for invalid_district in invalid_districts:
            # Use fuzzy matching to find similar districts
            matches = get_close_matches(
                invalid_district.lower(), 
                [d.lower() for d in all_searchable], 
                n=3, 
                cutoff=0.5  # Lower cutoff for more matches
            )
            
            # Convert back to proper case and canonical form
            for match in matches:
                # Find original case version
                for searchable in all_searchable:
                    if searchable.lower() == match:
                        # If it's a mapping key, get canonical form
                        if searchable in self.district_mappings:
                            canonical = self.district_mappings[searchable]
                            if canonical not in suggestions:
                                suggestions.append(canonical)
                        else:
                            # It's already canonical
                            if searchable not in suggestions:
                                suggestions.append(searchable)
                        break
        
        # If no fuzzy matches, provide some popular districts
        if not suggestions:
            popular_districts = [
                "Central district", "Tsim Sha Tsui", "Causeway Bay", 
                "Wan Chai", "Mong Kok", "Admiralty"
            ]
            suggestions.extend(popular_districts[:3])
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Limit to 5 suggestions
    
    def format_conversational_response(self, 
                                     results: List[Restaurant], 
                                     query_context: Dict[str, Any]) -> QueryResponse:
        """Format restaurant results into conversational response.
        
        Args:
            results: List of restaurant objects.
            query_context: Context about the original query.
            
        Returns:
            QueryResponse with formatted text and suggestions.
        """
        query = query_context.get('original_query', '')
        districts = query_context.get('districts', [])
        meal_types = query_context.get('meal_types', [])
        
        if not results:
            return self._format_no_results_response(query_context)
        
        # Format successful results
        if len(results) == 1:
            return self._format_single_result_response(results[0], query_context)
        else:
            return self._format_multiple_results_response(results, query_context)
    
    def _normalize_district_name(self, district: str) -> Optional[str]:
        """Normalize district name to canonical form.
        
        Args:
            district: Raw district name.
            
        Returns:
            Normalized district name or None if not recognized.
        """
        district_lower = district.lower().strip()
        
        # Check direct mapping
        if district_lower in self.district_mappings:
            return self.district_mappings[district_lower]
        
        # Check if it's already a canonical name
        canonical_districts = set(self.district_mappings.values())
        for canonical in canonical_districts:
            if district_lower == canonical.lower():
                return canonical
        
        # Try fuzzy matching
        all_variants = list(self.district_mappings.keys()) + list(self.district_mappings.values())
        matches = get_close_matches(district_lower, [d.lower() for d in all_variants], n=1, cutoff=0.8)
        
        if matches:
            # Find the original case version
            for variant in all_variants:
                if variant.lower() == matches[0]:
                    if variant in self.district_mappings:
                        return self.district_mappings[variant]
                    else:
                        return variant
        
        return None
    
    def _pattern_based_extraction(self, query: str, intent: QueryIntent) -> QueryIntent:
        """Use pattern matching to extract intent when simple keyword matching fails.
        
        Args:
            query: Query text (lowercase).
            intent: Existing intent object to update.
            
        Returns:
            Updated QueryIntent object.
        """
        # Try combined patterns first
        for pattern in self.patterns['combined']:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:  # meal_type, district
                    meal_type, district = match
                    
                    # Normalize meal type
                    meal_normalized = meal_type.lower().strip()
                    if meal_normalized in self.meal_mappings:
                        canonical_meal = self.meal_mappings[meal_normalized]
                        if canonical_meal not in intent.meal_types:
                            intent.meal_types.append(canonical_meal)
                    
                    # Normalize district
                    district_normalized = self._normalize_district_name(district.strip())
                    if district_normalized and district_normalized not in intent.districts:
                        intent.districts.append(district_normalized)
                    
                    if intent.meal_types and intent.districts:
                        intent.intent_type = 'combined_search'
                        intent.confidence = 0.85
                        return intent
        
        # Try district-only patterns
        if not intent.districts:
            for pattern in self.patterns['district_only']:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    district_normalized = self._normalize_district_name(match.strip())
                    if district_normalized and district_normalized not in intent.districts:
                        intent.districts.append(district_normalized)
        
        # Try meal-only patterns
        if not intent.meal_types:
            for pattern in self.patterns['meal_only']:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    meal_normalized = match.lower().strip()
                    if meal_normalized in self.meal_mappings:
                        canonical_meal = self.meal_mappings[meal_normalized]
                        if canonical_meal not in intent.meal_types:
                            intent.meal_types.append(canonical_meal)
        
        # Update intent type based on what we found
        if intent.districts and intent.meal_types:
            intent.intent_type = 'combined_search'
            intent.confidence = 0.8
        elif intent.districts:
            intent.intent_type = 'district_search'
            intent.confidence = 0.75
        elif intent.meal_types:
            intent.intent_type = 'meal_search'
            intent.confidence = 0.75
        
        return intent
    
    def _format_single_result_response(self, restaurant: Restaurant, query_context: Dict[str, Any]) -> QueryResponse:
        """Format response for single restaurant result.
        
        Args:
            restaurant: Restaurant object.
            query_context: Query context dictionary.
            
        Returns:
            QueryResponse with formatted text.
        """
        # Format operating hours in user-friendly way
        hours_text = self._format_operating_hours(restaurant.operating_hours)
        
        # Format sentiment
        sentiment_text = self._format_sentiment(restaurant.sentiment)
        
        response_text = f"""Here's a great restaurant I found:

**{restaurant.name}** - {restaurant.address}
- Cuisine: {', '.join(restaurant.meal_type)}
- District: {restaurant.district}
- Price Range: {restaurant.price_range}
- Hours: {hours_text}
- Rating: {sentiment_text}

Would you like to see more options in this area or search for something else?"""
        
        suggestions = [
            f"Find more restaurants in {restaurant.district}",
            "Search in a different district",
            "Look for different cuisine types"
        ]
        
        return QueryResponse(
            response_text=response_text,
            suggested_actions=suggestions,
            tool_calls_made=query_context.get('tool_calls', [])
        )
    
    def _format_multiple_results_response(self, restaurants: List[Restaurant], query_context: Dict[str, Any]) -> QueryResponse:
        """Format response for multiple restaurant results.
        
        Args:
            restaurants: List of restaurant objects.
            query_context: Query context dictionary.
            
        Returns:
            QueryResponse with formatted text.
        """
        districts = query_context.get('districts', [])
        meal_types = query_context.get('meal_types', [])
        
        # Create context description
        context_parts = []
        if districts:
            context_parts.append(f"in {', '.join(districts)}")
        if meal_types:
            context_parts.append(f"for {', '.join(meal_types)}")
        
        context_text = " ".join(context_parts) if context_parts else ""
        
        response_text = f"I found {len(restaurants)} restaurants{' ' + context_text if context_text else ''}:\n\n"
        
        # Show first 5 restaurants with details
        for i, restaurant in enumerate(restaurants[:5], 1):
            hours_text = self._format_operating_hours_brief(restaurant.operating_hours)
            response_text += f"{i}. **{restaurant.name}** ({restaurant.district})\n"
            response_text += f"   - {', '.join(restaurant.meal_type)} | {restaurant.price_range}\n"
            response_text += f"   - {restaurant.address}\n"
            response_text += f"   - Hours: {hours_text}\n\n"
        
        if len(restaurants) > 5:
            response_text += f"...and {len(restaurants) - 5} more restaurants.\n\n"
        
        response_text += "Would you like more details about any of these restaurants or refine your search?"
        
        suggestions = [
            "Get details about a specific restaurant",
            "Search in a different area",
            "Try different meal times",
            "Look for specific cuisine types"
        ]
        
        return QueryResponse(
            response_text=response_text,
            suggested_actions=suggestions,
            tool_calls_made=query_context.get('tool_calls', [])
        )
    
    def _format_no_results_response(self, query_context: Dict[str, Any]) -> QueryResponse:
        """Format response when no results are found.
        
        Args:
            query_context: Query context dictionary.
            
        Returns:
            QueryResponse with helpful suggestions.
        """
        districts = query_context.get('districts', [])
        meal_types = query_context.get('meal_types', [])
        
        response_text = "I couldn't find any restaurants matching your criteria.\n\n"
        
        suggestions = []
        
        if districts:
            response_text += f"No restaurants found in {', '.join(districts)}.\n"
            suggestions.extend([
                "Try nearby districts",
                "Search across all districts"
            ])
        
        if meal_types:
            response_text += f"No restaurants found for {', '.join(meal_types)}.\n"
            suggestions.extend([
                "Try different meal times",
                "Search without meal time restrictions"
            ])
        
        if not districts and not meal_types:
            response_text += "Your search didn't match any restaurants.\n"
            suggestions.extend([
                "Try searching by district (e.g., 'Central district')",
                "Try searching by meal type (e.g., 'breakfast places')",
                "Ask for help with search options"
            ])
        
        response_text += "\nYou might want to try:\n"
        for i, suggestion in enumerate(suggestions[:3], 1):
            response_text += f"{i}. {suggestion}\n"
        
        response_text += "\nWhat would you like to search for instead?"
        
        return QueryResponse(
            response_text=response_text,
            suggested_actions=suggestions,
            tool_calls_made=query_context.get('tool_calls', []),
            error_message="No results found"
        )
    
    def _format_operating_hours(self, operating_hours) -> str:
        """Format operating hours in user-friendly way.
        
        Args:
            operating_hours: OperatingHours object.
            
        Returns:
            Formatted hours string.
        """
        try:
            hours_parts = []
            
            if operating_hours.mon_fri:
                hours_parts.append(f"Mon-Fri: {', '.join(operating_hours.mon_fri)}")
            
            if operating_hours.sat_sun:
                hours_parts.append(f"Sat-Sun: {', '.join(operating_hours.sat_sun)}")
            
            if operating_hours.public_holiday:
                hours_parts.append(f"Holidays: {', '.join(operating_hours.public_holiday)}")
            
            return " | ".join(hours_parts) if hours_parts else "Hours not available"
            
        except Exception:
            return "Hours not available"
    
    def _format_operating_hours_brief(self, operating_hours) -> str:
        """Format operating hours in brief format.
        
        Args:
            operating_hours: OperatingHours object.
            
        Returns:
            Brief formatted hours string.
        """
        try:
            if operating_hours.mon_fri:
                return operating_hours.mon_fri[0]  # Show first time range
            elif operating_hours.sat_sun:
                return operating_hours.sat_sun[0]
            else:
                return "See details"
        except Exception:
            return "Hours vary"
    
    def _format_sentiment(self, sentiment) -> str:
        """Format sentiment data in user-friendly way.
        
        Args:
            sentiment: Sentiment object.
            
        Returns:
            Formatted sentiment string.
        """
        try:
            total = sentiment.likes + sentiment.dislikes + sentiment.neutral
            if total == 0:
                return "No ratings yet"
            
            like_pct = (sentiment.likes / total) * 100
            
            if like_pct >= 80:
                return f"Highly rated ({sentiment.likes} likes)"
            elif like_pct >= 60:
                return f"Well rated ({sentiment.likes} likes)"
            elif like_pct >= 40:
                return f"Mixed reviews ({sentiment.likes} likes, {sentiment.dislikes} dislikes)"
            else:
                return f"Lower rated ({sentiment.likes} likes, {sentiment.dislikes} dislikes)"
                
        except Exception:
            return "Rating not available"


def create_query_processor(district_service=None) -> QueryProcessor:
    """Factory function to create a QueryProcessor instance.
    
    Args:
        district_service: Optional district service for validation.
        
    Returns:
        QueryProcessor instance.
    """
    return QueryProcessor(district_service=district_service)


# Example usage and testing functions
def test_query_processing():
    """Test the query processing functionality with sample queries."""
    processor = QueryProcessor()
    
    test_queries = [
        "Find restaurants in Central district",
        "Breakfast places in Tsim Sha Tsui",
        "Good dinner spots",
        "Lunch restaurants in Causeway Bay",
        "Chinese food in Central",
        "What's good in TST?",
        "Morning places",
        "Dinner in Wan Chai",
        "Help me find restaurants"
    ]
    
    print("🧪 Testing Query Processing Pipeline\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        intent = processor.extract_intent(query)
        
        print(f"  Intent Type: {intent.intent_type}")
        print(f"  Districts: {intent.districts}")
        print(f"  Meal Types: {intent.meal_types}")
        print(f"  Cuisine Types: {intent.cuisine_types}")
        print(f"  Confidence: {intent.confidence:.2f}")
        print()


if __name__ == "__main__":
    test_query_processing()