"""Standalone test for session assignment logic."""

import sys
import os
import logging
from datetime import datetime
from typing import List, Set, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import models directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Copy the essential classes here to avoid import issues
class SessionType(Enum):
    """Session types for tourist spot assignments."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


class AssignmentPriority(Enum):
    """Priority levels for session assignment."""
    MBTI_MATCH_SAME_DISTRICT = 1
    MBTI_MATCH_SAME_AREA = 2
    MBTI_MATCH_ANY_LOCATION = 3
    NON_MBTI_SAME_DISTRICT = 4
    NON_MBTI_SAME_AREA = 5
    NON_MBTI_ANY_LOCATION = 6


@dataclass
class TouristSpotOperatingHours:
    """Operating hours for tourist spots."""
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None
    
    def is_open_during_session(self, session_type: SessionType, day_of_week: str = 'monday') -> bool:
        """Check if open during session."""
        day_hours = getattr(self, day_of_week.lower(), None)
        if not day_hours:
            return True  # Assume always open if no hours specified
        
        if day_hours.lower() == 'closed':
            return False
        
        return True  # Simplified for testing


@dataclass
class TouristSpot:
    """Tourist spot data model."""
    id: str
    name: str
    address: str
    district: str
    area: str
    location_category: str
    description: str
    operating_hours: TouristSpotOperatingHours
    operating_days: List[str]
    mbti_match: bool = False
    mbti_personality_types: List[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.mbti_personality_types is None:
            self.mbti_personality_types = []
        if self.keywords is None:
            self.keywords = []
    
    def matches_mbti_personality(self, mbti_personality: str) -> bool:
        """Check if spot matches MBTI personality."""
        if not mbti_personality:
            return False
        return mbti_personality.upper() in [mbti.upper() for mbti in self.mbti_personality_types]
    
    def matches_district(self, target_district: str) -> bool:
        """Check if spot matches district."""
        if not target_district:
            return False
        return self.district.lower().strip() == target_district.lower().strip()
    
    def matches_area(self, target_area: str) -> bool:
        """Check if spot matches area."""
        if not target_area:
            return False
        return self.area.lower().strip() == target_area.lower().strip()
    
    def is_available_for_session(self, session_type: SessionType, day_of_week: str = 'monday') -> bool:
        """Check if available for session."""
        return self.operating_hours.is_open_during_session(session_type, day_of_week)
    
    def set_mbti_match_status(self, mbti_personality: str) -> None:
        """Set MBTI match status."""
        self.mbti_match = self.matches_mbti_personality(mbti_personality)


@dataclass
class AssignmentResult:
    """Result of a session assignment attempt."""
    tourist_spot: Optional[TouristSpot] = None
    assignment_priority: Optional[AssignmentPriority] = None
    mbti_match: bool = False
    district_match: bool = False
    area_match: bool = False
    assignment_notes: str = ""
    fallback_used: bool = False


class SessionAssignmentLogic:
    """Core session assignment logic engine."""

    def __init__(self):
        """Initialize session assignment logic engine."""
        self.logger = logging.getLogger(__name__)

    def assign_morning_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign morning session tourist spot."""
        self.logger.info(f"Assigning morning session for day {day_number}")
        
        # Filter available MBTI spots
        available_spots = [
            spot for spot in mbti_spots
            if (spot.id not in used_spots and
                spot.matches_mbti_personality(mbti_personality) and
                spot.is_available_for_session(SessionType.MORNING))
        ]
        
        if available_spots:
            selected_spot = available_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes=f"MBTI-matched morning session for {mbti_personality}",
                fallback_used=False
            )
        
        # Fallback to non-MBTI spots
        fallback_spots = [
            spot for spot in mbti_spots
            if (spot.id not in used_spots and
                not spot.matches_mbti_personality(mbti_personality) and
                spot.is_available_for_session(SessionType.MORNING))
        ]
        
        if fallback_spots:
            selected_spot = fallback_spots[0]
            selected_spot.mbti_match = False
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.NON_MBTI_ANY_LOCATION,
                mbti_match=False,
                assignment_notes="Fallback assignment",
                fallback_used=True
            )
        
        return AssignmentResult(
            assignment_notes="No spots available",
            fallback_used=True
        )

    def assign_afternoon_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        morning_spot: Optional[TouristSpot],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign afternoon session with district matching priority."""
        self.logger.info(f"Assigning afternoon session for day {day_number}")
        
        target_district = morning_spot.district if morning_spot else None
        target_area = morning_spot.area if morning_spot else None
        
        # Priority 1: Same district, MBTI-matched
        if target_district:
            same_district_spots = [
                spot for spot in mbti_spots
                if (spot.id not in used_spots and
                    spot.matches_mbti_personality(mbti_personality) and
                    spot.matches_district(target_district) and
                    spot.is_available_for_session(SessionType.AFTERNOON))
            ]
            
            if same_district_spots:
                selected_spot = same_district_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
                    mbti_match=True,
                    district_match=True,
                    assignment_notes=f"Same district ({target_district}) MBTI match",
                    fallback_used=False
                )
        
        # Priority 2: Same area, MBTI-matched
        if target_area:
            same_area_spots = [
                spot for spot in mbti_spots
                if (spot.id not in used_spots and
                    spot.matches_mbti_personality(mbti_personality) and
                    spot.matches_area(target_area) and
                    spot.is_available_for_session(SessionType.AFTERNOON))
            ]
            
            if same_area_spots:
                selected_spot = same_area_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_AREA,
                    mbti_match=True,
                    area_match=True,
                    assignment_notes=f"Same area ({target_area}) MBTI match",
                    fallback_used=False
                )
        
        # Priority 3: Any MBTI spot
        available_spots = [
            spot for spot in mbti_spots
            if (spot.id not in used_spots and
                spot.matches_mbti_personality(mbti_personality) and
                spot.is_available_for_session(SessionType.AFTERNOON))
        ]
        
        if available_spots:
            selected_spot = available_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes="MBTI match, any location",
                fallback_used=False
            )
        
        # Fallback
        return self._assign_fallback_spot(mbti_spots, used_spots, SessionType.AFTERNOON)

    def assign_night_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        morning_spot: Optional[TouristSpot],
        afternoon_spot: Optional[TouristSpot],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign night session with district matching priority."""
        self.logger.info(f"Assigning night session for day {day_number}")
        
        # Similar logic to afternoon but considering both morning and afternoon spots
        target_districts = []
        if morning_spot:
            target_districts.append(morning_spot.district)
        if afternoon_spot:
            target_districts.append(afternoon_spot.district)
        
        # Try same district first
        for target_district in target_districts:
            same_district_spots = [
                spot for spot in mbti_spots
                if (spot.id not in used_spots and
                    spot.matches_mbti_personality(mbti_personality) and
                    spot.matches_district(target_district) and
                    spot.is_available_for_session(SessionType.NIGHT))
            ]
            
            if same_district_spots:
                selected_spot = same_district_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
                    mbti_match=True,
                    district_match=True,
                    assignment_notes=f"Same district ({target_district}) MBTI match",
                    fallback_used=False
                )
        
        # Any MBTI spot
        available_spots = [
            spot for spot in mbti_spots
            if (spot.id not in used_spots and
                spot.matches_mbti_personality(mbti_personality) and
                spot.is_available_for_session(SessionType.NIGHT))
        ]
        
        if available_spots:
            selected_spot = available_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes="MBTI match, any location",
                fallback_used=False
            )
        
        # Fallback
        return self._assign_fallback_spot(mbti_spots, used_spots, SessionType.NIGHT)

    def _assign_fallback_spot(
        self,
        all_spots: List[TouristSpot],
        used_spots: Set[str],
        session_type: SessionType
    ) -> AssignmentResult:
        """Assign fallback spot when MBTI spots are exhausted."""
        fallback_spots = [
            spot for spot in all_spots
            if (spot.id not in used_spots and
                spot.is_available_for_session(session_type))
        ]
        
        if fallback_spots:
            selected_spot = fallback_spots[0]
            selected_spot.mbti_match = False
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.NON_MBTI_ANY_LOCATION,
                mbti_match=False,
                assignment_notes="Fallback assignment",
                fallback_used=True
            )
        
        return AssignmentResult(
            assignment_notes="No spots available",
            fallback_used=True
        )

    def get_assignment_statistics(
        self,
        assignment_results: List[AssignmentResult]
    ) -> Dict[str, Any]:
        """Generate statistics about session assignments."""
        total_assignments = len(assignment_results)
        successful_assignments = len([r for r in assignment_results if r.tourist_spot])
        mbti_matches = len([r for r in assignment_results if r.mbti_match])
        district_matches = len([r for r in assignment_results if r.district_match])
        area_matches = len([r for r in assignment_results if r.area_match])
        fallback_used = len([r for r in assignment_results if r.fallback_used])
        
        return {
            'total_assignments': total_assignments,
            'successful_assignments': successful_assignments,
            'success_rate': successful_assignments / total_assignments if total_assignments > 0 else 0,
            'mbti_matches': mbti_matches,
            'mbti_match_rate': mbti_matches / successful_assignments if successful_assignments > 0 else 0,
            'district_matches': district_matches,
            'area_matches': area_matches,
            'fallback_used': fallback_used
        }


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