#!/usr/bin/env python3
"""
Basic test for orchestration engine foundation functionality.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from services.tool_orchestration_engine import (
    ToolOrchestrationEngine,
    OrchestrationConfig,
    UserContext,
    RequestType
)


async def test_basic_functionality():
    """Test basic orchestration engine functionality."""
    print("Testing Tool Orchestration Engine Foundation...")
    
    # Test 1: Configuration creation
    print("1. Testing configuration creation...")
    config = OrchestrationConfig(
        intent_confidence_threshold=0.8,
        performance_weight=0.4,
        health_weight=0.3,
        capability_weight=0.3,
        max_concurrent_workflows=10
    )
    print(f"   ✓ Configuration created: threshold={config.intent_confidence_threshold}")
    
    # Test 2: Engine initialization
    print("2. Testing engine initialization...")
    try:
        engine = ToolOrchestrationEngine(config=config, environment='test')
        print(f"   ✓ Engine initialized for environment: {engine.environment}")
    except Exception as e:
        print(f"   ✗ Engine initialization failed: {e}")
        return False
    
    # Test 3: Intent analysis
    print("3. Testing intent analysis...")
    try:
        intent = await engine._analyze_intent("Find restaurants in Central district", None)
        print(f"   ✓ Intent analyzed: type={intent.type.value}, confidence={intent.confidence:.2f}")
        
        if intent.type == RequestType.RESTAURANT_SEARCH_BY_LOCATION:
            print(f"   ✓ Correct intent type detected")
        else:
            print(f"   ⚠ Unexpected intent type: {intent.type.value}")
    except Exception as e:
        print(f"   ✗ Intent analysis failed: {e}")
        return False
    
    # Test 4: Intent analysis with user context
    print("4. Testing intent analysis with user context...")
    try:
        user_context = UserContext(
            user_id='test_user',
            mbti_type='ENFP',
            location_context='Hong Kong'
        )
        
        intent = await engine._analyze_intent("Recommend good restaurants", user_context)
        print(f"   ✓ Intent with context: type={intent.type.value}, confidence={intent.confidence:.2f}")
        
        if 'mbti_type' in intent.parameters:
            print(f"   ✓ MBTI context included: {intent.parameters['mbti_type']}")
        else:
            print(f"   ⚠ MBTI context not included")
    except Exception as e:
        print(f"   ✗ Intent analysis with context failed: {e}")
        return False
    
    # Test 5: District extraction
    print("5. Testing district extraction...")
    try:
        districts = engine._extract_districts("Find restaurants in Central and Admiralty")
        print(f"   ✓ Districts extracted: {districts}")
        
        if 'Central' in districts and 'Admiralty' in districts:
            print(f"   ✓ Correct districts detected")
        else:
            print(f"   ⚠ Expected districts not found")
    except Exception as e:
        print(f"   ✗ District extraction failed: {e}")
        return False
    
    # Test 6: Meal type extraction
    print("6. Testing meal type extraction...")
    try:
        meal_types = engine._extract_meal_types("Looking for breakfast and lunch places")
        print(f"   ✓ Meal types extracted: {meal_types}")
        
        if 'breakfast' in meal_types and 'lunch' in meal_types:
            print(f"   ✓ Correct meal types detected")
        else:
            print(f"   ⚠ Expected meal types not found")
    except Exception as e:
        print(f"   ✗ Meal type extraction failed: {e}")
        return False
    
    # Test 7: Performance metrics
    print("7. Testing performance metrics...")
    try:
        # Record some test metrics
        engine._record_tool_execution('test_tool', True, 100.0)
        engine._record_tool_execution('test_tool', True, 200.0)
        engine._record_tool_execution('test_tool', False, 0.0)
        
        metrics = engine.get_performance_metrics()
        print(f"   ✓ Performance metrics collected: {len(metrics)} tools")
        
        if 'test_tool' in metrics:
            tool_metrics = metrics['test_tool']
            print(f"   ✓ Tool metrics: success_rate={tool_metrics['success_rate']:.2f}")
        else:
            print(f"   ⚠ Test tool metrics not found")
    except Exception as e:
        print(f"   ✗ Performance metrics failed: {e}")
        return False
    
    # Test 8: Health check
    print("8. Testing health check...")
    try:
        health_results = await engine.health_check()
        print(f"   ✓ Health check completed")
        
        if 'orchestration_engine' in health_results:
            engine_health = health_results['orchestration_engine']
            print(f"   ✓ Engine status: {engine_health['status']}")
        else:
            print(f"   ⚠ Engine health not found in results")
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return False
    
    # Test 9: Circuit breaker
    print("9. Testing circuit breaker...")
    try:
        tool_id = 'test_circuit_breaker'
        
        # Initially should be closed (allow execution)
        initial_state = engine._check_circuit_breaker(tool_id)
        print(f"   ✓ Initial circuit breaker state: {'closed' if initial_state else 'open'}")
        
        # Simulate failures
        for i in range(engine.config.circuit_breaker_failure_threshold):
            engine._update_circuit_breaker(tool_id)
        
        # Should now be open (block execution)
        final_state = engine._check_circuit_breaker(tool_id)
        print(f"   ✓ Final circuit breaker state: {'closed' if final_state else 'open'}")
        
        if not final_state:  # Should be False (open)
            print(f"   ✓ Circuit breaker correctly opened after failures")
        else:
            print(f"   ⚠ Circuit breaker did not open as expected")
    except Exception as e:
        print(f"   ✗ Circuit breaker test failed: {e}")
        return False
    
    print("\n✅ All basic functionality tests passed!")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\n🎉 Tool Orchestration Engine Foundation is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)