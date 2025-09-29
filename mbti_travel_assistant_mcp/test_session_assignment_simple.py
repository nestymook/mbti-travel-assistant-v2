"""Simple test for session assignment logic without complex dependencies."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from services.session_assignment_logic import SessionAssignmentLogic, AssignmentPriority


def create_test_spots():
    """Create test tourist spots."""
    spots = []
    
    # INFJ-matched spots
    for i in range(5):
        operating_hours = TouristSpotOperatingHours(
            monday="09:00-18:00",
            tuesday="09:00-18:00",
            wednesday="09:00-18:00",
            thursday="09:00-18:00",
            friday="09:00-18:00",
            saturday="10:00-17:00",
            sunday="10:00-17:00"
        )
        
        spot = TouristSpot(
            id=f"infj_spot_{i}",
            name=f"INFJ Spot {i}",
            address=f"Address {i}",
            district="Central" if i < 3 else "Admiralty",
            area="Hong Kong Island",
            location_category="Museum",
            description=f"Test INFJ spot {i}",
            operating_hours=operating_hours,
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            mbti_personality_types=["INFJ"],
            keywords=["quiet", "cultural", "peaceful"]
        )
        spots.append(spot)
    
    return spots


def test_session_assignment_logic():
    """Test the session assignment logic."""
    print("Testing Session Assignment Logic...")
    
    # Create test data
    session_logic = SessionAssignmentLogic()
    test_spots = create_test_spots()
    mbti_personality = "INFJ"
    used_spots = set()
    
    print(f"Created {len(test_spots)} test spots")
    
    # Test morning session assignment
    print("\n1. Testing morning session assignment...")
    morning_result = session_logic.assign_morning_session(
        test_spots, used_spots, mbti_personality, 1
    )
    
    if morning_result.tourist_spot:
        print(f"✓ Morning session assigned: {morning_result.tourist_spot.name}")
        print(f"  - MBTI match: {morning_result.mbti_match}")
        print(f"  - Priority: {morning_result.assignment_priority}")
        print(f"  - Fallback used: {morning_result.fallback_used}")
        used_spots.add(morning_result.tourist_spot.id)
    else:
        print("✗ Morning session assignment failed")
        return False
    
    # Test afternoon session assignment
    print("\n2. Testing afternoon session assignment...")
    afternoon_result = session_logic.assign_afternoon_session(
        test_spots, used_spots, morning_result.tourist_spot, mbti_personality, 1
    )
    
    if afternoon_result.tourist_spot:
        print(f"✓ Afternoon session assigned: {afternoon_result.tourist_spot.name}")
        print(f"  - MBTI match: {afternoon_result.mbti_match}")
        print(f"  - District match: {afternoon_result.district_match}")
        print(f"  - Area match: {afternoon_result.area_match}")
        print(f"  - Priority: {afternoon_result.assignment_priority}")
        used_spots.add(afternoon_result.tourist_spot.id)
    else:
        print("✗ Afternoon session assignment failed")
        return False
    
    # Test night session assignment
    print("\n3. Testing night session assignment...")
    night_result = session_logic.assign_night_session(
        test_spots, used_spots, morning_result.tourist_spot,
        afternoon_result.tourist_spot, mbti_personality, 1
    )
    
    if night_result.tourist_spot:
        print(f"✓ Night session assigned: {night_result.tourist_spot.name}")
        print(f"  - MBTI match: {night_result.mbti_match}")
        print(f"  - District match: {night_result.district_match}")
        print(f"  - Area match: {night_result.area_match}")
        print(f"  - Priority: {night_result.assignment_priority}")
        used_spots.add(night_result.tourist_spot.id)
    else:
        print("✗ Night session assignment failed")
        return False
    
    # Test uniqueness constraint
    print(f"\n4. Testing uniqueness constraint...")
    print(f"Used spots: {used_spots}")
    print(f"Unique spots count: {len(used_spots)}")
    
    if len(used_spots) == 3:
        print("✓ Uniqueness constraint maintained - all spots are unique")
    else:
        print("✗ Uniqueness constraint violated")
        return False
    
    # Test assignment statistics
    print("\n5. Testing assignment statistics...")
    results = [morning_result, afternoon_result, night_result]
    stats = session_logic.get_assignment_statistics(results)
    
    print(f"Assignment statistics:")
    print(f"  - Total assignments: {stats['total_assignments']}")
    print(f"  - Successful assignments: {stats['successful_assignments']}")
    print(f"  - Success rate: {stats['success_rate']:.2%}")
    print(f"  - MBTI matches: {stats['mbti_matches']}")
    print(f"  - MBTI match rate: {stats['mbti_match_rate']:.2%}")
    print(f"  - District matches: {stats['district_matches']}")
    print(f"  - Area matches: {stats['area_matches']}")
    
    if stats['success_rate'] == 1.0 and stats['mbti_match_rate'] == 1.0:
        print("✓ Assignment statistics look good")
    else:
        print("✗ Assignment statistics show issues")
        return False
    
    print("\n✓ All session assignment logic tests passed!")
    return True


def test_fallback_assignment():
    """Test fallback assignment when MBTI spots are exhausted."""
    print("\nTesting Fallback Assignment Logic...")
    
    session_logic = SessionAssignmentLogic()
    test_spots = create_test_spots()
    mbti_personality = "INFJ"
    
    # Mark all INFJ spots as used to force fallback
    used_spots = {f"infj_spot_{i}" for i in range(5)}
    print(f"Marked {len(used_spots)} INFJ spots as used to force fallback")
    
    # Add some non-INFJ spots for fallback
    non_infj_spot = TouristSpot(
        id="non_infj_fallback",
        name="Non-INFJ Fallback Spot",
        address="Fallback Address",
        district="Central",
        area="Hong Kong Island",
        location_category="Entertainment",
        description="Fallback spot for testing",
        operating_hours=TouristSpotOperatingHours(monday="10:00-22:00"),
        operating_days=["daily"],
        mbti_personality_types=["ESTP"],
        keywords=["active", "social"]
    )
    test_spots.append(non_infj_spot)
    
    # Test fallback assignment
    result = session_logic.assign_morning_session(
        test_spots, used_spots, mbti_personality, 1
    )
    
    if result.tourist_spot:
        print(f"✓ Fallback assignment successful: {result.tourist_spot.name}")
        print(f"  - MBTI match: {result.mbti_match}")
        print(f"  - Fallback used: {result.fallback_used}")
        print(f"  - Priority: {result.assignment_priority}")
        
        if not result.mbti_match and result.fallback_used:
            print("✓ Fallback logic working correctly")
            return True
        else:
            print("✗ Fallback logic not working as expected")
            return False
    else:
        print("✗ Fallback assignment failed")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Session Assignment Logic Test Suite")
    print("=" * 60)
    
    try:
        # Run main tests
        main_test_passed = test_session_assignment_logic()
        
        # Run fallback tests
        fallback_test_passed = test_fallback_assignment()
        
        print("\n" + "=" * 60)
        if main_test_passed and fallback_test_passed:
            print("🎉 ALL TESTS PASSED! Session assignment logic is working correctly.")
        else:
            print("❌ SOME TESTS FAILED! Please check the implementation.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()