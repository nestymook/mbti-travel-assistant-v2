"""
Intent Analysis System Demo

This script demonstrates the capabilities of the intent analysis system,
showing how it can classify user requests and extract parameters with
context-aware enhancements.
"""

import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the intent analysis components
from services.intent_analyzer import IntentAnalyzer
from services.context_aware_analyzer import ContextAwareAnalyzer
from services.orchestration_types import UserContext, RequestType


async def demo_basic_intent_analysis():
    """Demonstrate basic intent analysis without context."""
    print("=== Basic Intent Analysis Demo ===\n")
    
    analyzer = IntentAnalyzer(enable_context_analysis=True)
    
    test_requests = [
        "Find restaurants in Central district",
        "Search for breakfast places",
        "Recommend the best Italian restaurants for ENFP",
        "Find good lunch spots in Admiralty and recommend the top ones",
        "Analyze restaurant sentiment data"
    ]
    
    for request in test_requests:
        print(f"Request: '{request}'")
        intent = await analyzer.analyze_intent(request)
        
        print(f"  Intent Type: {intent.type.value}")
        print(f"  Confidence: {intent.confidence:.2f}")
        print(f"  Parameters: {intent.parameters}")
        print(f"  Required Capabilities: {intent.required_capabilities}")
        print(f"  Optional Capabilities: {intent.optional_capabilities}")
        print()


async def demo_context_aware_analysis():
    """Demonstrate context-aware intent analysis."""
    print("=== Context-Aware Intent Analysis Demo ===\n")
    
    base_analyzer = IntentAnalyzer(enable_context_analysis=True)
    context_analyzer = ContextAwareAnalyzer(base_analyzer)
    
    # Create a user context with history and MBTI type
    user_context = UserContext(
        user_id="demo_user",
        mbti_type="ENFP",
        conversation_history=[
            "Find restaurants in Central",
            "What about Italian places in Central?",
            "Recommend group-friendly restaurants",
            "Search for lively atmosphere restaurants"
        ],
        preferences={
            'preferred_cuisines': ['Italian', 'Japanese', 'Fusion'],
            'preferred_districts': ['Central', 'Admiralty'],
            'preferred_atmosphere': ['lively', 'social']
        }
    )
    
    test_requests = [
        "Find Italian restaurants",  # Should get MBTI and preference boost
        "Recommend restaurants for a group",  # Should align with ENFP social preference
        "What about Central district?",  # Should get history boost
        "Find innovative fusion places"  # Should align with ENFP exploration tendency
    ]
    
    for request in test_requests:
        print(f"Request: '{request}'")
        
        # Get base analysis
        base_intent = await base_analyzer.analyze_intent(request, user_context)
        
        # Get context-aware analysis
        enhanced_intent = await context_analyzer.analyze_intent_with_context(request, user_context)
        
        print(f"  Base Intent:")
        print(f"    Type: {base_intent.type.value}")
        print(f"    Confidence: {base_intent.confidence:.2f}")
        
        print(f"  Enhanced Intent:")
        print(f"    Type: {enhanced_intent.type.value}")
        print(f"    Confidence: {enhanced_intent.confidence:.2f}")
        print(f"    Parameters: {enhanced_intent.parameters}")
        
        confidence_boost = enhanced_intent.confidence - base_intent.confidence
        print(f"    Confidence Boost: {confidence_boost:+.2f}")
        print()


async def demo_mbti_personality_influence():
    """Demonstrate how different MBTI types influence analysis."""
    print("=== MBTI Personality Influence Demo ===\n")
    
    base_analyzer = IntentAnalyzer(enable_context_analysis=True)
    context_analyzer = ContextAwareAnalyzer(base_analyzer)
    
    mbti_types = ["ENFP", "INTJ", "ESFJ", "ISTP"]
    request = "Recommend restaurants for dinner"
    
    for mbti_type in mbti_types:
        context = UserContext(
            user_id=f"user_{mbti_type.lower()}",
            mbti_type=mbti_type
        )
        
        intent = await context_analyzer.analyze_intent_with_context(request, context)
        
        print(f"MBTI Type: {mbti_type}")
        print(f"  Intent Type: {intent.type.value}")
        print(f"  Confidence: {intent.confidence:.2f}")
        
        # Show MBTI-specific parameters
        mbti_params = {k: v for k, v in intent.parameters.items() 
                      if 'mbti' in k.lower() or k in ['exploration_tendency', 'social_preference']}
        if mbti_params:
            print(f"  MBTI Parameters: {mbti_params}")
        print()


async def demo_conversation_pattern_analysis():
    """Demonstrate conversation pattern recognition."""
    print("=== Conversation Pattern Analysis Demo ===\n")
    
    base_analyzer = IntentAnalyzer(enable_context_analysis=True)
    context_analyzer = ContextAwareAnalyzer(base_analyzer)
    
    # Create context with repetitive patterns
    context = UserContext(
        user_id="pattern_user",
        conversation_history=[
            "Find restaurants in Central",
            "Search Central district restaurants",
            "What's good in Central?",
            "Find breakfast places",
            "Looking for breakfast restaurants",
            "Where can I get breakfast?",
            "Recommend Italian cuisine",
            "Find Italian restaurants"
        ]
    )
    
    patterns = context_analyzer.analyze_conversation_history(context)
    
    print("Detected Conversation Patterns:")
    for pattern in patterns:
        print(f"  Pattern Type: {pattern.pattern_type}")
        print(f"  Frequency: {pattern.frequency}")
        print(f"  Confidence: {pattern.confidence:.2f}")
        print(f"  Parameters: {pattern.parameters}")
        print()
    
    # Test how patterns influence new requests
    test_request = "Find restaurants"  # Ambiguous request
    intent = await context_analyzer.analyze_intent_with_context(test_request, context)
    
    print(f"Ambiguous Request Analysis: '{test_request}'")
    print(f"  Resolved Intent Type: {intent.type.value}")
    print(f"  Confidence: {intent.confidence:.2f}")
    print(f"  Parameters: {intent.parameters}")


async def demo_parameter_extraction():
    """Demonstrate parameter extraction capabilities."""
    print("=== Parameter Extraction Demo ===\n")
    
    analyzer = IntentAnalyzer(enable_context_analysis=True)
    
    test_cases = [
        {
            'request': "Find Italian restaurants in Central and Admiralty for 4 people",
            'expected_params': ['districts', 'cuisine_type', 'group_size']
        },
        {
            'request': "Recommend breakfast places for ENFP personality type under $50",
            'expected_params': ['meal_types', 'mbti_type', 'price_range']
        },
        {
            'request': "Search for quiet, intimate Chinese restaurants in Mid-Levels",
            'expected_params': ['districts', 'cuisine_type', 'atmosphere']
        }
    ]
    
    for case in test_cases:
        request = case['request']
        print(f"Request: '{request}'")
        
        intent = await analyzer.analyze_intent(request)
        
        print(f"  Extracted Parameters:")
        for param, value in intent.parameters.items():
            print(f"    {param}: {value}")
        
        # Check if expected parameters were found
        found_params = set(intent.parameters.keys())
        expected_params = set(case['expected_params'])
        
        print(f"  Expected: {expected_params}")
        print(f"  Found: {found_params}")
        print(f"  Match Rate: {len(found_params & expected_params) / len(expected_params):.1%}")
        print()


async def main():
    """Run all demo scenarios."""
    print("Intent Analysis System Demo")
    print("=" * 50)
    print()
    
    try:
        await demo_basic_intent_analysis()
        await demo_context_aware_analysis()
        await demo_mbti_personality_influence()
        await demo_conversation_pattern_analysis()
        await demo_parameter_extraction()
        
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())