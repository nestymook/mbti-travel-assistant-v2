#!/usr/bin/env python3
"""
MBTI Prompt Loader Utility
Demonstrates how to load and use the MBTI personality type prompt files for multi-prompt discovery.
"""

import json
import os
from typing import Dict, List, Any

class MBTIPromptLoader:
    """Utility class for loading and managing MBTI personality type prompts."""
    
    def __init__(self, prompts_dir: str = "mbti_prompts"):
        self.prompts_directory = prompts_dir
        self.all_prompts = {}
        self.load_all_prompts()
    
    def load_all_prompts(self):
        """Load all MBTI personality type prompt files."""
        if not os.path.exists(self.prompts_directory):
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_directory}")
        
        for filename in os.listdir(self.prompts_directory):
            if filename.endswith('.json'):
                mbti_type = filename.replace('.json', '')
                filepath = os.path.join(self.prompts_directory, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.all_prompts[mbti_type] = json.load(f)
                    print(f"✅ Loaded prompts for {mbti_type}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {str(e)}")
        
        print(f"\n📊 Total MBTI types loaded: {len(self.all_prompts)}")
    
    def get_personality_prompts(self, mbti_type: str) -> Dict[str, Any]:
        """Get prompts for a specific MBTI personality type."""
        mbti_type = mbti_type.upper()
        if mbti_type not in self.all_prompts:
            available_types = list(self.all_prompts.keys())
            raise ValueError(f"MBTI type '{mbti_type}' not found. Available types: {available_types}")
        
        return self.all_prompts[mbti_type]
    
    def get_all_queries(self, mbti_type: str) -> List[str]:
        """Get all search queries for a specific MBTI type."""
        prompts = self.get_personality_prompts(mbti_type)
        all_queries = []
        
        for category, queries in prompts['search_strategies'].items():
            all_queries.extend(queries)
        
        return all_queries
    
    def get_optimized_queries(self, mbti_type: str) -> List[str]:
        """Get optimized queries prioritizing best-performing categories."""
        prompts = self.get_personality_prompts(mbti_type)
        strategies = prompts['search_strategies']
        optimization = prompts['optimization_notes']
        
        best_categories = optimization.get('best_performing_categories', [])
        recommended_count = optimization.get('recommended_query_count', 15)
        
        # Start with best-performing categories
        optimized_queries = []
        for category in best_categories:
            if category in strategies:
                optimized_queries.extend(strategies[category])
        
        # Add queries from other categories to reach recommended count
        for category, queries in strategies.items():
            if category not in best_categories:
                remaining_slots = recommended_count - len(optimized_queries)
                if remaining_slots <= 0:
                    break
                optimized_queries.extend(queries[:min(remaining_slots, 3)])
        
        return optimized_queries[:recommended_count]
    
    def get_category_queries(self, mbti_type: str, category: str) -> List[str]:
        """Get queries for a specific category of a MBTI type."""
        prompts = self.get_personality_prompts(mbti_type)
        strategies = prompts['search_strategies']
        
        if category not in strategies:
            available_categories = list(strategies.keys())
            raise ValueError(f"Category '{category}' not found for {mbti_type}. Available: {available_categories}")
        
        return strategies[category]
    
    def get_personality_info(self, mbti_type: str) -> Dict[str, Any]:
        """Get personality information and traits."""
        prompts = self.get_personality_prompts(mbti_type)
        return {
            'type': prompts['personality_type'],
            'description': prompts['description'],
            'core_traits': prompts['core_traits'],
            'preferred_activities': prompts['preferred_activities'],
            'optimization_notes': prompts['optimization_notes']
        }
    
    def list_available_types(self) -> List[str]:
        """List all available MBTI personality types."""
        return sorted(list(self.all_prompts.keys()))
    
    def list_categories(self, mbti_type: str) -> List[str]:
        """List all available search categories for a MBTI type."""
        prompts = self.get_personality_prompts(mbti_type)
        return list(prompts['search_strategies'].keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded prompts."""
        stats = {
            'total_types': len(self.all_prompts),
            'total_queries': 0,
            'categories_per_type': {},
            'queries_per_type': {},
            'average_queries_per_type': 0
        }
        
        for mbti_type, prompts in self.all_prompts.items():
            strategies = prompts['search_strategies']
            type_query_count = sum(len(queries) for queries in strategies.values())
            
            stats['categories_per_type'][mbti_type] = len(strategies)
            stats['queries_per_type'][mbti_type] = type_query_count
            stats['total_queries'] += type_query_count
        
        if stats['total_types'] > 0:
            stats['average_queries_per_type'] = stats['total_queries'] / stats['total_types']
        
        return stats
    
    def demonstrate_usage(self):
        """Demonstrate various usage patterns."""
        print("🚀 MBTI PROMPT LOADER DEMONSTRATION")
        print("=" * 60)
        
        # Show available types
        available_types = self.list_available_types()
        print(f"📋 Available MBTI Types ({len(available_types)}):")
        for i, mbti_type in enumerate(available_types, 1):
            print(f"   {i:2d}. {mbti_type}")
        
        # Show statistics
        stats = self.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"   Total Types: {stats['total_types']}")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Average Queries per Type: {stats['average_queries_per_type']:.1f}")
        
        # Demonstrate with INFJ
        print(f"\n🎯 INFJ Example:")
        infj_info = self.get_personality_info('INFJ')
        print(f"   Description: {infj_info['description']}")
        print(f"   Core Traits: {', '.join(infj_info['core_traits'][:5])}...")
        
        # Show categories
        categories = self.list_categories('INFJ')
        print(f"   Categories ({len(categories)}): {', '.join(categories)}")
        
        # Show optimized queries
        optimized_queries = self.get_optimized_queries('INFJ')
        print(f"   Optimized Queries ({len(optimized_queries)}):")
        for i, query in enumerate(optimized_queries[:5], 1):
            print(f"      {i}. {query}")
        if len(optimized_queries) > 5:
            print(f"      ... and {len(optimized_queries) - 5} more")
        
        # Show category example
        print(f"\n🔍 Trait-Based Queries for INFJ:")
        trait_queries = self.get_category_queries('INFJ', 'trait_based_queries')
        for i, query in enumerate(trait_queries[:3], 1):
            print(f"   {i}. {query}")
        
        print(f"\n✅ Demonstration complete!")

def main():
    """Main demonstration function."""
    try:
        # Initialize the prompt loader
        loader = MBTIPromptLoader()
        
        # Run demonstration
        loader.demonstrate_usage()
        
        # Example usage patterns
        print(f"\n" + "=" * 60)
        print("💡 USAGE EXAMPLES")
        print("=" * 60)
        
        print("# Load prompts for specific type:")
        print("loader = MBTIPromptLoader()")
        print("enfp_queries = loader.get_all_queries('ENFP')")
        print("print(f'ENFP has {len(enfp_queries)} total queries')")
        
        print("\n# Get optimized queries:")
        print("optimized = loader.get_optimized_queries('INTJ')")
        print("print(f'Using {len(optimized)} optimized queries for INTJ')")
        
        print("\n# Get specific category:")
        print("activity_queries = loader.get_category_queries('ESTP', 'activity_focused_queries')")
        print("print(f'ESTP activity queries: {activity_queries}')")
        
        print("\n# Get personality information:")
        print("info = loader.get_personality_info('ISFP')")
        print("print(f'ISFP: {info[\"description\"]}')")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()