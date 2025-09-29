"""Session assignment logic engine for MBTI Travel Assistant.

This module implements the core session assignment logic with strict business rules
for assigning tourist spots to morning/afternoon/night sessions across a 3-day itinerary.
Follows PEP8 style guidelines and implements requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7.
"""

import logging
from datetime import datetime
from typing import List, Set, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from ..models.tourist_spot_models import TouristSpot, SessionType


class AssignmentPriority(Enum):
    """Priority levels for session assignment."""
    MBTI_MATCH_SAME_DISTRICT = 1
    MBTI_MATCH_SAME_AREA = 2
    MBTI_MATCH_ANY_LOCATION = 3
    NON_MBTI_SAME_DISTRICT = 4
    NON_MBTI_SAME_AREA = 5
    NON_MBTI_ANY_LOCATION = 6


@dataclass
class AssignmentContext:
    """Context information for session assignment.
    
    Attributes:
        day_number: Day number (1, 2, or 3)
        session_type: Type of session being assigned
        morning_spot: Morning session spot for district/area reference
        afternoon_spot: Afternoon session spot for district/area reference
        used_spots: Set of already assigned tourist spot IDs
        mbti_personality: MBTI personality type for matching
    """
    day_number: int
    session_type: SessionType
    morning_spot: Optional[TouristSpot] = None
    afternoon_spot: Optional[TouristSpot] = None
    used_spots: Optional[Set[str]] = None
    mbti_personality: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.used_spots is None:
            self.used_spots = set()


@dataclass
class AssignmentResult:
    """Result of a session assignment attempt.
    
    Attributes:
        tourist_spot: Assigned tourist spot (None if assignment failed)
        assignment_priority: Priority level used for assignment
        mbti_match: Whether the assigned spot matches MBTI personality
        district_match: Whether the assigned spot matches target district
        area_match: Whether the assigned spot matches target area
        assignment_notes: Additional notes about the assignment
        fallback_used: Whether fallback assignment logic was used
    """
    tourist_spot: Optional[TouristSpot] = None
    assignment_priority: Optional[AssignmentPriority] = None
    mbti_match: bool = False
    district_match: bool = False
    area_match: bool = False
    assignment_notes: str = ""
    fallback_used: bool = False


class SessionAssignmentLogic:
    """Core session assignment logic engine.
    
    Implements strict business rules for assigning tourist spots to sessions:
    - Morning sessions: MBTI-matched spots with morning operating hours
    - Afternoon sessions: Same district priority, then same area, with afternoon hours
    - Night sessions: Same district priority, then same area, with night hours
    - Uniqueness constraint: No tourist spot repeated across all 9 sessions
    - Fallback logic: Non-MBTI spots when MBTI spots are exhausted
    """

    def __init__(self):
        """Initialize session assignment logic engine."""
        self.logger = logging.getLogger(__name__)
        
        # Session time ranges for operating hours validation
        self.session_time_ranges = {
            SessionType.MORNING: (7, 0, 11, 59),    # 07:00-11:59
            SessionType.AFTERNOON: (12, 0, 17, 59), # 12:00-17:59
            SessionType.NIGHT: (18, 0, 23, 59)      # 18:00-23:59
        }

    def assign_morning_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign morning session tourist spot with MBTI matching priority.
        
        Priority logic:
        1. MBTI-matched spots with morning operating hours or no operating hours
        2. MBTI-matched spots never assigned before
        3. Random unassigned non-MBTI spots as fallback
        
        Args:
            mbti_spots: List of MBTI-matched tourist spots
            used_spots: Set of already assigned spot IDs
            mbti_personality: MBTI personality type for matching
            day_number: Day number for logging context
            
        Returns:
            AssignmentResult with assigned spot and metadata
        """
        context = AssignmentContext(
            day_number=day_number,
            session_type=SessionType.MORNING,
            used_spots=used_spots,
            mbti_personality=mbti_personality
        )
        
        self.logger.info(
            f"Assigning morning session for day {day_number}, "
            f"MBTI: {mbti_personality}, used spots: {len(used_spots)}"
        )
        
        # Filter available MBTI spots with morning hours
        available_mbti_spots = self._filter_spots_for_session(
            mbti_spots, SessionType.MORNING, used_spots, mbti_personality
        )
        
        if available_mbti_spots:
            selected_spot = available_mbti_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            self.logger.info(
                f"Assigned MBTI-matched morning spot: {selected_spot.name} "
                f"(ID: {selected_spot.id}) for day {day_number}"
            )
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes=f"MBTI-matched morning session for {mbti_personality}",
                fallback_used=False
            )
        
        # Fallback to non-MBTI spots
        self.logger.warning(
            f"No MBTI-matched spots available for morning session day {day_number}, "
            "using fallback assignment"
        )
        
        return self._assign_fallback_spot(context, mbti_spots)

    def assign_afternoon_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        morning_spot: Optional[TouristSpot],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign afternoon session with district/area matching priority.
        
        Priority logic:
        1. Same district as morning spot, MBTI-matched, afternoon hours
        2. Same area as morning spot, MBTI-matched, afternoon hours
        3. Any MBTI-matched spot with afternoon hours
        4. Fallback to non-MBTI spots with same priority order
        
        Args:
            mbti_spots: List of MBTI-matched tourist spots
            used_spots: Set of already assigned spot IDs
            morning_spot: Morning session spot for district matching
            mbti_personality: MBTI personality type for matching
            day_number: Day number for logging context
            
        Returns:
            AssignmentResult with assigned spot and metadata
        """
        context = AssignmentContext(
            day_number=day_number,
            session_type=SessionType.AFTERNOON,
            morning_spot=morning_spot,
            used_spots=used_spots,
            mbti_personality=mbti_personality
        )
        
        target_district = morning_spot.district if morning_spot else None
        target_area = morning_spot.area if morning_spot else None
        
        self.logger.info(
            f"Assigning afternoon session for day {day_number}, "
            f"target district: {target_district}, target area: {target_area}"
        )
        
        # Priority 1: Same district, MBTI-matched
        if target_district:
            same_district_spots = self._filter_spots_for_session_with_location(
                mbti_spots, SessionType.AFTERNOON, used_spots, mbti_personality,
                target_district=target_district
            )
            
            if same_district_spots:
                selected_spot = same_district_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                self.logger.info(
                    f"Assigned same-district afternoon spot: {selected_spot.name} "
                    f"(District: {selected_spot.district}) for day {day_number}"
                )
                
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
            same_area_spots = self._filter_spots_for_session_with_location(
                mbti_spots, SessionType.AFTERNOON, used_spots, mbti_personality,
                target_area=target_area
            )
            
            if same_area_spots:
                selected_spot = same_area_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                self.logger.info(
                    f"Assigned same-area afternoon spot: {selected_spot.name} "
                    f"(Area: {selected_spot.area}) for day {day_number}"
                )
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_AREA,
                    mbti_match=True,
                    area_match=True,
                    assignment_notes=f"Same area ({target_area}) MBTI match",
                    fallback_used=False
                )
        
        # Priority 3: Any MBTI spot with afternoon hours
        available_mbti_spots = self._filter_spots_for_session(
            mbti_spots, SessionType.AFTERNOON, used_spots, mbti_personality
        )
        
        if available_mbti_spots:
            selected_spot = available_mbti_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            self.logger.info(
                f"Assigned any-location afternoon spot: {selected_spot.name} "
                f"for day {day_number}"
            )
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes="MBTI match, any location",
                fallback_used=False
            )
        
        # Fallback to non-MBTI spots
        self.logger.warning(
            f"No MBTI-matched spots available for afternoon session day {day_number}, "
            "using fallback assignment"
        )
        
        return self._assign_fallback_spot(context, mbti_spots)

    def assign_night_session(
        self,
        mbti_spots: List[TouristSpot],
        used_spots: Set[str],
        morning_spot: Optional[TouristSpot],
        afternoon_spot: Optional[TouristSpot],
        mbti_personality: str,
        day_number: int = 1
    ) -> AssignmentResult:
        """Assign night session with district/area matching priority.
        
        Priority logic (same as afternoon but considering both morning and afternoon spots):
        1. Same district as morning or afternoon spot, MBTI-matched, night hours
        2. Same area as morning or afternoon spot, MBTI-matched, night hours
        3. Any MBTI-matched spot with night hours
        4. Fallback to non-MBTI spots with same priority order
        
        Args:
            mbti_spots: List of MBTI-matched tourist spots
            used_spots: Set of already assigned spot IDs
            morning_spot: Morning session spot for district matching
            afternoon_spot: Afternoon session spot for district matching
            mbti_personality: MBTI personality type for matching
            day_number: Day number for logging context
            
        Returns:
            AssignmentResult with assigned spot and metadata
        """
        context = AssignmentContext(
            day_number=day_number,
            session_type=SessionType.NIGHT,
            morning_spot=morning_spot,
            afternoon_spot=afternoon_spot,
            used_spots=used_spots,
            mbti_personality=mbti_personality
        )
        
        # Collect target districts and areas from morning and afternoon spots
        target_districts = []
        target_areas = []
        
        if morning_spot:
            target_districts.append(morning_spot.district)
            target_areas.append(morning_spot.area)
        
        if afternoon_spot:
            target_districts.append(afternoon_spot.district)
            target_areas.append(afternoon_spot.area)
        
        # Remove duplicates while preserving order
        target_districts = list(dict.fromkeys(target_districts))
        target_areas = list(dict.fromkeys(target_areas))
        
        self.logger.info(
            f"Assigning night session for day {day_number}, "
            f"target districts: {target_districts}, target areas: {target_areas}"
        )
        
        # Priority 1: Same district as morning or afternoon spot, MBTI-matched
        for target_district in target_districts:
            same_district_spots = self._filter_spots_for_session_with_location(
                mbti_spots, SessionType.NIGHT, used_spots, mbti_personality,
                target_district=target_district
            )
            
            if same_district_spots:
                selected_spot = same_district_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                self.logger.info(
                    f"Assigned same-district night spot: {selected_spot.name} "
                    f"(District: {selected_spot.district}) for day {day_number}"
                )
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
                    mbti_match=True,
                    district_match=True,
                    assignment_notes=f"Same district ({target_district}) MBTI match",
                    fallback_used=False
                )
        
        # Priority 2: Same area as morning or afternoon spot, MBTI-matched
        for target_area in target_areas:
            same_area_spots = self._filter_spots_for_session_with_location(
                mbti_spots, SessionType.NIGHT, used_spots, mbti_personality,
                target_area=target_area
            )
            
            if same_area_spots:
                selected_spot = same_area_spots[0]
                selected_spot.set_mbti_match_status(mbti_personality)
                
                self.logger.info(
                    f"Assigned same-area night spot: {selected_spot.name} "
                    f"(Area: {selected_spot.area}) for day {day_number}"
                )
                
                return AssignmentResult(
                    tourist_spot=selected_spot,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_AREA,
                    mbti_match=True,
                    area_match=True,
                    assignment_notes=f"Same area ({target_area}) MBTI match",
                    fallback_used=False
                )
        
        # Priority 3: Any MBTI spot with night hours
        available_mbti_spots = self._filter_spots_for_session(
            mbti_spots, SessionType.NIGHT, used_spots, mbti_personality
        )
        
        if available_mbti_spots:
            selected_spot = available_mbti_spots[0]
            selected_spot.set_mbti_match_status(mbti_personality)
            
            self.logger.info(
                f"Assigned any-location night spot: {selected_spot.name} "
                f"for day {day_number}"
            )
            
            return AssignmentResult(
                tourist_spot=selected_spot,
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                assignment_notes="MBTI match, any location",
                fallback_used=False
            )
        
        # Fallback to non-MBTI spots
        self.logger.warning(
            f"No MBTI-matched spots available for night session day {day_number}, "
            "using fallback assignment"
        )
        
        return self._assign_fallback_spot(context, mbti_spots)

    def _filter_spots_for_session(
        self,
        spots: List[TouristSpot],
        session_type: SessionType,
        used_spots: Set[str],
        mbti_personality: str
    ) -> List[TouristSpot]:
        """Filter tourist spots for session based on operating hours and availability.
        
        Args:
            spots: List of tourist spots to filter
            session_type: Type of session (morning, afternoon, night)
            used_spots: Set of already assigned spot IDs
            mbti_personality: MBTI personality type for matching
            
        Returns:
            List of available spots for the session
        """
        available_spots = []
        
        for spot in spots:
            # Skip if already used
            if spot.id in used_spots:
                continue
            
            # Check if spot matches MBTI personality
            if not spot.matches_mbti_personality(mbti_personality):
                continue
            
            # Check if spot is available for the session
            if spot.is_available_for_session(session_type):
                available_spots.append(spot)
        
        return available_spots

    def _filter_spots_for_session_with_location(
        self,
        spots: List[TouristSpot],
        session_type: SessionType,
        used_spots: Set[str],
        mbti_personality: str,
        target_district: Optional[str] = None,
        target_area: Optional[str] = None
    ) -> List[TouristSpot]:
        """Filter spots for session with district/area matching.
        
        Args:
            spots: List of tourist spots to filter
            session_type: Type of session (morning, afternoon, night)
            used_spots: Set of already assigned spot IDs
            mbti_personality: MBTI personality type for matching
            target_district: Target district for matching
            target_area: Target area for matching
            
        Returns:
            List of available spots matching location criteria
        """
        # First filter by session availability
        session_spots = self._filter_spots_for_session(
            spots, session_type, used_spots, mbti_personality
        )
        
        # Then filter by location
        location_matched_spots = []
        
        for spot in session_spots:
            if target_district and spot.matches_district(target_district):
                location_matched_spots.append(spot)
            elif target_area and spot.matches_area(target_area):
                location_matched_spots.append(spot)
        
        return location_matched_spots

    def _assign_fallback_spot(
        self,
        context: AssignmentContext,
        all_spots: List[TouristSpot]
    ) -> AssignmentResult:
        """Assign fallback spot when MBTI spots are exhausted.
        
        Uses same priority logic but with non-MBTI spots:
        1. Same district, non-MBTI, session hours
        2. Same area, non-MBTI, session hours
        3. Any non-MBTI spot with session hours
        
        Args:
            context: Assignment context with session and location info
            all_spots: All available tourist spots (including non-MBTI)
            
        Returns:
            AssignmentResult with fallback assignment
        """
        self.logger.info(
            f"Attempting fallback assignment for {context.session_type.value} "
            f"session day {context.day_number}"
        )
        
        # Get all non-MBTI spots available for the session
        non_mbti_spots = []
        for spot in all_spots:
            if (spot.id not in context.used_spots and
                not spot.matches_mbti_personality(context.mbti_personality) and
                spot.is_available_for_session(context.session_type)):
                non_mbti_spots.append(spot)
        
        if not non_mbti_spots:
            self.logger.error(
                f"No fallback spots available for {context.session_type.value} "
                f"session day {context.day_number}"
            )
            return AssignmentResult(
                assignment_notes="No spots available for assignment",
                fallback_used=True
            )
        
        # Try district matching first
        if context.morning_spot or context.afternoon_spot:
            target_districts = []
            if context.morning_spot:
                target_districts.append(context.morning_spot.district)
            if context.afternoon_spot:
                target_districts.append(context.afternoon_spot.district)
            
            for target_district in target_districts:
                district_spots = [
                    spot for spot in non_mbti_spots
                    if spot.matches_district(target_district)
                ]
                
                if district_spots:
                    selected_spot = district_spots[0]
                    selected_spot.mbti_match = False
                    
                    self.logger.info(
                        f"Assigned fallback district-matched spot: {selected_spot.name} "
                        f"for {context.session_type.value} session day {context.day_number}"
                    )
                    
                    return AssignmentResult(
                        tourist_spot=selected_spot,
                        assignment_priority=AssignmentPriority.NON_MBTI_SAME_DISTRICT,
                        mbti_match=False,
                        district_match=True,
                        assignment_notes=f"Fallback: same district ({target_district})",
                        fallback_used=True
                    )
        
        # Try area matching
        if context.morning_spot or context.afternoon_spot:
            target_areas = []
            if context.morning_spot:
                target_areas.append(context.morning_spot.area)
            if context.afternoon_spot:
                target_areas.append(context.afternoon_spot.area)
            
            for target_area in target_areas:
                area_spots = [
                    spot for spot in non_mbti_spots
                    if spot.matches_area(target_area)
                ]
                
                if area_spots:
                    selected_spot = area_spots[0]
                    selected_spot.mbti_match = False
                    
                    self.logger.info(
                        f"Assigned fallback area-matched spot: {selected_spot.name} "
                        f"for {context.session_type.value} session day {context.day_number}"
                    )
                    
                    return AssignmentResult(
                        tourist_spot=selected_spot,
                        assignment_priority=AssignmentPriority.NON_MBTI_SAME_AREA,
                        mbti_match=False,
                        area_match=True,
                        assignment_notes=f"Fallback: same area ({target_area})",
                        fallback_used=True
                    )
        
        # Assign any available non-MBTI spot
        selected_spot = non_mbti_spots[0]
        selected_spot.mbti_match = False
        
        self.logger.info(
            f"Assigned fallback any-location spot: {selected_spot.name} "
            f"for {context.session_type.value} session day {context.day_number}"
        )
        
        return AssignmentResult(
            tourist_spot=selected_spot,
            assignment_priority=AssignmentPriority.NON_MBTI_ANY_LOCATION,
            mbti_match=False,
            assignment_notes="Fallback: any available location",
            fallback_used=True
        )

    def validate_session_assignment(
        self,
        tourist_spot: TouristSpot,
        session_type: SessionType,
        day_of_week: str = 'monday'
    ) -> List[str]:
        """Validate that a tourist spot assignment meets session requirements.
        
        Args:
            tourist_spot: Tourist spot to validate
            session_type: Session type to validate against
            day_of_week: Day of the week for operating hours check
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate operating hours for session
        if not tourist_spot.is_available_for_session(session_type, day_of_week):
            session_times = {
                SessionType.MORNING: "07:00-11:59",
                SessionType.AFTERNOON: "12:00-17:59",
                SessionType.NIGHT: "18:00-23:59"
            }
            errors.append(
                f"Tourist spot '{tourist_spot.name}' is not available during "
                f"{session_type.value} session ({session_times[session_type]})"
            )
        
        # Validate required fields
        if not tourist_spot.id:
            errors.append("Tourist spot must have a valid ID")
        
        if not tourist_spot.name:
            errors.append("Tourist spot must have a valid name")
        
        if not tourist_spot.district:
            errors.append("Tourist spot must have a valid district")
        
        if not tourist_spot.area:
            errors.append("Tourist spot must have a valid area")
        
        return errors

    def get_assignment_statistics(
        self,
        assignment_results: List[AssignmentResult]
    ) -> Dict[str, Any]:
        """Generate statistics about session assignments.
        
        Args:
            assignment_results: List of assignment results to analyze
            
        Returns:
            Dictionary with assignment statistics
        """
        total_assignments = len(assignment_results)
        successful_assignments = len([r for r in assignment_results if r.tourist_spot])
        mbti_matches = len([r for r in assignment_results if r.mbti_match])
        district_matches = len([r for r in assignment_results if r.district_match])
        area_matches = len([r for r in assignment_results if r.area_match])
        fallback_used = len([r for r in assignment_results if r.fallback_used])
        
        # Count by priority
        priority_counts = {}
        for result in assignment_results:
            if result.assignment_priority:
                priority = result.assignment_priority.name
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            'total_assignments': total_assignments,
            'successful_assignments': successful_assignments,
            'success_rate': successful_assignments / total_assignments if total_assignments > 0 else 0,
            'mbti_matches': mbti_matches,
            'mbti_match_rate': mbti_matches / successful_assignments if successful_assignments > 0 else 0,
            'district_matches': district_matches,
            'area_matches': area_matches,
            'fallback_used': fallback_used,
            'priority_distribution': priority_counts
        }

c
lass DistrictAreaMatcher:
    """Advanced district and area matching logic for session assignments.
    
    Implements sophisticated matching algorithms for afternoon and night sessions
    with fallback logic when district matching fails. Handles same-location
    prioritization across sessions.
    """

    def __init__(self):
        """Initialize district and area matcher."""
        self.logger = logging.getLogger(__name__)
        
        # District hierarchy and relationships (can be extended with real data)
        self.district_relationships = {
            # Central districts
            'Central': ['Admiralty', 'Wan Chai', 'Causeway Bay'],
            'Admiralty': ['Central', 'Wan Chai'],
            'Wan Chai': ['Central', 'Admiralty', 'Causeway Bay'],
            'Causeway Bay': ['Wan Chai', 'Tin Hau'],
            
            # Kowloon districts
            'Tsim Sha Tsui': ['Jordan', 'Yau Ma Tei'],
            'Jordan': ['Tsim Sha Tsui', 'Yau Ma Tei'],
            'Yau Ma Tei': ['Jordan', 'Mong Kok'],
            'Mong Kok': ['Yau Ma Tei', 'Prince Edward'],
            
            # Other areas can be added as needed
        }
        
        # Area to district mapping for fallback logic
        self.area_district_mapping = {
            'Hong Kong Island': ['Central', 'Admiralty', 'Wan Chai', 'Causeway Bay', 'Tin Hau'],
            'Kowloon': ['Tsim Sha Tsui', 'Jordan', 'Yau Ma Tei', 'Mong Kok'],
            'New Territories': ['Sha Tin', 'Tai Po', 'Tuen Mun'],
        }

    def find_best_district_match(
        self,
        available_spots: List[TouristSpot],
        target_districts: List[str],
        session_type: SessionType,
        used_spots: Set[str]
    ) -> Tuple[List[TouristSpot], str]:
        """Find best district match with priority scoring.
        
        Args:
            available_spots: List of available tourist spots
            target_districts: List of target districts in priority order
            session_type: Session type for operating hours validation
            used_spots: Set of already used spot IDs
            
        Returns:
            Tuple of (matching spots, matched district)
        """
        self.logger.debug(
            f"Finding best district match for {session_type.value} session, "
            f"target districts: {target_districts}"
        )
        
        # Try exact district matches first
        for target_district in target_districts:
            exact_matches = []
            
            for spot in available_spots:
                if (spot.id not in used_spots and
                    spot.matches_district(target_district) and
                    spot.is_available_for_session(session_type)):
                    exact_matches.append(spot)
            
            if exact_matches:
                self.logger.debug(
                    f"Found {len(exact_matches)} exact matches for district: {target_district}"
                )
                return exact_matches, target_district
        
        # Try related district matches
        for target_district in target_districts:
            related_districts = self.district_relationships.get(target_district, [])
            
            for related_district in related_districts:
                related_matches = []
                
                for spot in available_spots:
                    if (spot.id not in used_spots and
                        spot.matches_district(related_district) and
                        spot.is_available_for_session(session_type)):
                        related_matches.append(spot)
                
                if related_matches:
                    self.logger.debug(
                        f"Found {len(related_matches)} related matches for district: "
                        f"{related_district} (related to {target_district})"
                    )
                    return related_matches, related_district
        
        return [], ""

    def find_best_area_match(
        self,
        available_spots: List[TouristSpot],
        target_areas: List[str],
        session_type: SessionType,
        used_spots: Set[str]
    ) -> Tuple[List[TouristSpot], str]:
        """Find best area match when district matching fails.
        
        Args:
            available_spots: List of available tourist spots
            target_areas: List of target areas in priority order
            session_type: Session type for operating hours validation
            used_spots: Set of already used spot IDs
            
        Returns:
            Tuple of (matching spots, matched area)
        """
        self.logger.debug(
            f"Finding best area match for {session_type.value} session, "
            f"target areas: {target_areas}"
        )
        
        # Try exact area matches
        for target_area in target_areas:
            area_matches = []
            
            for spot in available_spots:
                if (spot.id not in used_spots and
                    spot.matches_area(target_area) and
                    spot.is_available_for_session(session_type)):
                    area_matches.append(spot)
            
            if area_matches:
                self.logger.debug(
                    f"Found {len(area_matches)} area matches for: {target_area}"
                )
                return area_matches, target_area
        
        # Try districts within the same area
        for target_area in target_areas:
            area_districts = self.area_district_mapping.get(target_area, [])
            
            for district in area_districts:
                district_matches = []
                
                for spot in available_spots:
                    if (spot.id not in used_spots and
                        spot.matches_district(district) and
                        spot.is_available_for_session(session_type)):
                        district_matches.append(spot)
                
                if district_matches:
                    self.logger.debug(
                        f"Found {len(district_matches)} matches in district {district} "
                        f"within area {target_area}"
                    )
                    return district_matches, target_area
        
        return [], ""

    def calculate_location_priority_score(
        self,
        spot: TouristSpot,
        target_districts: List[str],
        target_areas: List[str]
    ) -> int:
        """Calculate priority score for location matching.
        
        Args:
            spot: Tourist spot to score
            target_districts: List of target districts
            target_areas: List of target areas
            
        Returns:
            Priority score (higher is better):
            - 10: Exact district match (first priority)
            - 8: Exact district match (lower priority)
            - 6: Related district match
            - 4: Exact area match
            - 2: Area-related district match
            - 1: No match
        """
        # Check exact district matches
        for i, target_district in enumerate(target_districts):
            if spot.matches_district(target_district):
                return 10 - (i * 2)  # Higher score for earlier districts
        
        # Check related district matches
        for target_district in target_districts:
            related_districts = self.district_relationships.get(target_district, [])
            if spot.district in related_districts:
                return 6
        
        # Check exact area matches
        for target_area in target_areas:
            if spot.matches_area(target_area):
                return 4
        
        # Check area-related district matches
        for target_area in target_areas:
            area_districts = self.area_district_mapping.get(target_area, [])
            if spot.district in area_districts:
                return 2
        
        return 1  # No match

    def get_same_location_spots(
        self,
        available_spots: List[TouristSpot],
        reference_spots: List[TouristSpot],
        session_type: SessionType,
        used_spots: Set[str]
    ) -> List[TouristSpot]:
        """Get spots in the same location as reference spots.
        
        Prioritizes spots that are in the same district or area as any of the
        reference spots (morning and/or afternoon spots).
        
        Args:
            available_spots: List of available tourist spots
            reference_spots: List of reference spots (morning/afternoon)
            session_type: Session type for operating hours validation
            used_spots: Set of already used spot IDs
            
        Returns:
            List of spots in same locations, sorted by priority
        """
        if not reference_spots:
            return []
        
        # Collect target districts and areas from reference spots
        target_districts = []
        target_areas = []
        
        for ref_spot in reference_spots:
            if ref_spot and ref_spot.district:
                target_districts.append(ref_spot.district)
            if ref_spot and ref_spot.area:
                target_areas.append(ref_spot.area)
        
        # Remove duplicates while preserving order
        target_districts = list(dict.fromkeys(target_districts))
        target_areas = list(dict.fromkeys(target_areas))
        
        # Score and sort spots by location priority
        scored_spots = []
        
        for spot in available_spots:
            if (spot.id not in used_spots and
                spot.is_available_for_session(session_type)):
                
                score = self.calculate_location_priority_score(
                    spot, target_districts, target_areas
                )
                
                if score > 1:  # Only include spots with some location match
                    scored_spots.append((spot, score))
        
        # Sort by score (descending) and return spots
        scored_spots.sort(key=lambda x: x[1], reverse=True)
        return [spot for spot, score in scored_spots]

    def validate_district_area_consistency(
        self,
        spots: List[TouristSpot]
    ) -> List[str]:
        """Validate district and area consistency across spots.
        
        Args:
            spots: List of tourist spots to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        if len(spots) < 2:
            return warnings
        
        # Check for district consistency
        districts = [spot.district for spot in spots if spot.district]
        unique_districts = set(districts)
        
        if len(unique_districts) > 2:
            warnings.append(
                f"Multiple districts assigned in same day: {', '.join(unique_districts)}. "
                "Consider grouping spots by location for better travel efficiency."
            )
        
        # Check for area consistency
        areas = [spot.area for spot in spots if spot.area]
        unique_areas = set(areas)
        
        if len(unique_areas) > 1:
            warnings.append(
                f"Multiple areas assigned in same day: {', '.join(unique_areas)}. "
                "This may result in longer travel times between sessions."
            )
        
        return warnings


class LocationOptimizer:
    """Location optimization for session assignments.
    
    Provides advanced optimization algorithms for minimizing travel time
    and maximizing location coherence across sessions.
    """

    def __init__(self):
        """Initialize location optimizer."""
        self.logger = logging.getLogger(__name__)
        self.district_matcher = DistrictAreaMatcher()

    def optimize_session_locations(
        self,
        day_spots: List[TouristSpot],
        session_types: List[SessionType]
    ) -> Dict[str, Any]:
        """Optimize locations for a day's sessions.
        
        Args:
            day_spots: List of spots assigned to the day's sessions
            session_types: List of session types in order
            
        Returns:
            Dictionary with optimization analysis and suggestions
        """
        if len(day_spots) != len(session_types):
            return {'error': 'Mismatch between spots and session types'}
        
        optimization_result = {
            'travel_efficiency_score': 0,
            'location_coherence_score': 0,
            'optimization_suggestions': [],
            'district_distribution': {},
            'area_distribution': {}
        }
        
        # Calculate travel efficiency score
        travel_score = self._calculate_travel_efficiency(day_spots)
        optimization_result['travel_efficiency_score'] = travel_score
        
        # Calculate location coherence score
        coherence_score = self._calculate_location_coherence(day_spots)
        optimization_result['location_coherence_score'] = coherence_score
        
        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(day_spots, session_types)
        optimization_result['optimization_suggestions'] = suggestions
        
        # Analyze district and area distribution
        districts = [spot.district for spot in day_spots if spot.district]
        areas = [spot.area for spot in day_spots if spot.area]
        
        optimization_result['district_distribution'] = {
            district: districts.count(district) for district in set(districts)
        }
        optimization_result['area_distribution'] = {
            area: areas.count(area) for area in set(areas)
        }
        
        return optimization_result

    def _calculate_travel_efficiency(self, spots: List[TouristSpot]) -> float:
        """Calculate travel efficiency score based on location proximity.
        
        Args:
            spots: List of tourist spots
            
        Returns:
            Travel efficiency score (0-100, higher is better)
        """
        if len(spots) < 2:
            return 100.0
        
        # Count same district pairs
        same_district_pairs = 0
        same_area_pairs = 0
        total_pairs = 0
        
        for i in range(len(spots)):
            for j in range(i + 1, len(spots)):
                total_pairs += 1
                
                if spots[i].matches_district(spots[j].district):
                    same_district_pairs += 1
                elif spots[i].matches_area(spots[j].area):
                    same_area_pairs += 1
        
        if total_pairs == 0:
            return 100.0
        
        # Calculate score: same district = 100%, same area = 60%, different = 0%
        district_score = (same_district_pairs / total_pairs) * 100
        area_score = (same_area_pairs / total_pairs) * 60
        
        return min(100.0, district_score + area_score)

    def _calculate_location_coherence(self, spots: List[TouristSpot]) -> float:
        """Calculate location coherence score.
        
        Args:
            spots: List of tourist spots
            
        Returns:
            Location coherence score (0-100, higher is better)
        """
        if len(spots) < 2:
            return 100.0
        
        # Check district coherence
        districts = [spot.district for spot in spots if spot.district]
        unique_districts = len(set(districts))
        
        # Check area coherence
        areas = [spot.area for spot in spots if spot.area]
        unique_areas = len(set(areas))
        
        # Calculate coherence score
        district_coherence = max(0, 100 - (unique_districts - 1) * 30)
        area_coherence = max(0, 100 - (unique_areas - 1) * 20)
        
        return (district_coherence + area_coherence) / 2

    def _generate_optimization_suggestions(
        self,
        spots: List[TouristSpot],
        session_types: List[SessionType]
    ) -> List[str]:
        """Generate optimization suggestions for location assignments.
        
        Args:
            spots: List of tourist spots
            session_types: List of session types
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        if len(spots) < 2:
            return suggestions
        
        # Check for district fragmentation
        districts = [spot.district for spot in spots if spot.district]
        unique_districts = set(districts)
        
        if len(unique_districts) > 2:
            suggestions.append(
                f"Consider consolidating locations: {len(unique_districts)} different districts "
                f"({', '.join(unique_districts)}) may result in excessive travel time."
            )
        
        # Check for area fragmentation
        areas = [spot.area for spot in spots if spot.area]
        unique_areas = set(areas)
        
        if len(unique_areas) > 1:
            suggestions.append(
                f"Multiple areas detected ({', '.join(unique_areas)}). "
                "Consider grouping sessions within the same area for better efficiency."
            )
        
        # Check session-specific suggestions
        for i, (spot, session_type) in enumerate(zip(spots, session_types)):
            if i > 0:  # Compare with previous spot
                prev_spot = spots[i - 1]
                
                if not spot.matches_district(prev_spot.district) and not spot.matches_area(prev_spot.area):
                    suggestions.append(
                        f"{session_type.value.title()} session location ({spot.district}) "
                        f"is far from previous session ({prev_spot.district}). "
                        "Consider alternative spots in the same area."
                    )
        
        return suggestions


class UniquenessConstraintEnforcer:
    """Uniqueness constraint enforcement for tourist spot assignments.
    
    Ensures no tourist spot is repeated across all 9 sessions (3 days × 3 sessions)
    and provides fallback assignment strategies when MBTI spots are exhausted.
    """

    def __init__(self):
        """Initialize uniqueness constraint enforcer."""
        self.logger = logging.getLogger(__name__)

    def validate_uniqueness_across_itinerary(
        self,
        day_assignments: Dict[int, Dict[str, TouristSpot]]
    ) -> List[str]:
        """Validate uniqueness constraint across entire 3-day itinerary.
        
        Args:
            day_assignments: Dictionary mapping day numbers to session assignments
                Format: {1: {'morning': spot1, 'afternoon': spot2, 'night': spot3}, ...}
                
        Returns:
            List of uniqueness violation errors
        """
        errors = []
        used_spot_ids = set()
        duplicate_assignments = []
        
        for day_num, sessions in day_assignments.items():
            for session_type, spot in sessions.items():
                if spot and spot.id:
                    if spot.id in used_spot_ids:
                        duplicate_assignments.append({
                            'spot_id': spot.id,
                            'spot_name': spot.name,
                            'day': day_num,
                            'session': session_type
                        })
                        errors.append(
                            f"Duplicate assignment: Tourist spot '{spot.name}' (ID: {spot.id}) "
                            f"assigned to day {day_num} {session_type} session, "
                            "but already used in another session"
                        )
                    else:
                        used_spot_ids.add(spot.id)
        
        if duplicate_assignments:
            self.logger.error(
                f"Found {len(duplicate_assignments)} uniqueness violations in itinerary"
            )
            
            # Log detailed information about duplicates
            for dup in duplicate_assignments:
                self.logger.error(
                    f"Duplicate: {dup['spot_name']} (ID: {dup['spot_id']}) "
                    f"in day {dup['day']} {dup['session']} session"
                )
        
        return errors

    def track_used_spots_across_days(
        self,
        existing_assignments: Dict[int, Dict[str, TouristSpot]]
    ) -> Set[str]:
        """Track all tourist spots already used across existing day assignments.
        
        Args:
            existing_assignments: Dictionary of existing day assignments
            
        Returns:
            Set of used tourist spot IDs
        """
        used_spots = set()
        
        for day_num, sessions in existing_assignments.items():
            for session_type, spot in sessions.items():
                if spot and spot.id:
                    used_spots.add(spot.id)
                    self.logger.debug(
                        f"Tracking used spot: {spot.name} (ID: {spot.id}) "
                        f"from day {day_num} {session_type} session"
                    )
        
        self.logger.info(f"Tracking {len(used_spots)} used spots across existing assignments")
        return used_spots

    def get_available_spots_for_assignment(
        self,
        all_spots: List[TouristSpot],
        used_spots: Set[str],
        mbti_personality: str,
        session_type: SessionType,
        prefer_mbti: bool = True
    ) -> Tuple[List[TouristSpot], List[TouristSpot]]:
        """Get available spots for assignment, separated by MBTI matching.
        
        Args:
            all_spots: List of all available tourist spots
            used_spots: Set of already used spot IDs
            mbti_personality: MBTI personality type for matching
            session_type: Session type for operating hours validation
            prefer_mbti: Whether to prefer MBTI-matched spots
            
        Returns:
            Tuple of (mbti_matched_spots, non_mbti_spots)
        """
        mbti_spots = []
        non_mbti_spots = []
        
        for spot in all_spots:
            # Skip if already used
            if spot.id in used_spots:
                continue
            
            # Skip if not available for session
            if not spot.is_available_for_session(session_type):
                continue
            
            # Categorize by MBTI matching
            if spot.matches_mbti_personality(mbti_personality):
                mbti_spots.append(spot)
            else:
                non_mbti_spots.append(spot)
        
        self.logger.debug(
            f"Available spots for {session_type.value} session: "
            f"{len(mbti_spots)} MBTI-matched, {len(non_mbti_spots)} non-MBTI"
        )
        
        return mbti_spots, non_mbti_spots

    def enforce_uniqueness_in_assignment(
        self,
        candidate_spots: List[TouristSpot],
        used_spots: Set[str]
    ) -> List[TouristSpot]:
        """Filter candidate spots to enforce uniqueness constraint.
        
        Args:
            candidate_spots: List of candidate tourist spots
            used_spots: Set of already used spot IDs
            
        Returns:
            List of unique candidate spots
        """
        unique_spots = []
        
        for spot in candidate_spots:
            if spot.id not in used_spots:
                unique_spots.append(spot)
            else:
                self.logger.debug(
                    f"Filtered out duplicate spot: {spot.name} (ID: {spot.id})"
                )
        
        self.logger.debug(
            f"Filtered {len(candidate_spots)} candidates to {len(unique_spots)} unique spots"
        )
        
        return unique_spots

    def handle_mbti_exhaustion_fallback(
        self,
        all_spots: List[TouristSpot],
        used_spots: Set[str],
        session_type: SessionType,
        target_districts: List[str] = None,
        target_areas: List[str] = None
    ) -> Optional[TouristSpot]:
        """Handle fallback assignment when MBTI spots are exhausted.
        
        Implements fallback strategy:
        1. Non-MBTI spots in target districts
        2. Non-MBTI spots in target areas
        3. Any available non-MBTI spots
        
        Args:
            all_spots: List of all available tourist spots
            used_spots: Set of already used spot IDs
            session_type: Session type for operating hours validation
            target_districts: List of target districts for location matching
            target_areas: List of target areas for location matching
            
        Returns:
            Selected fallback tourist spot or None if none available
        """
        self.logger.info(
            f"MBTI spots exhausted for {session_type.value} session, "
            "attempting fallback assignment"
        )
        
        # Get all non-MBTI spots available for session
        available_non_mbti_spots = []
        
        for spot in all_spots:
            if (spot.id not in used_spots and
                spot.is_available_for_session(session_type)):
                available_non_mbti_spots.append(spot)
        
        if not available_non_mbti_spots:
            self.logger.error(
                f"No fallback spots available for {session_type.value} session"
            )
            return None
        
        # Priority 1: Target districts
        if target_districts:
            for target_district in target_districts:
                district_spots = [
                    spot for spot in available_non_mbti_spots
                    if spot.matches_district(target_district)
                ]
                
                if district_spots:
                    selected_spot = district_spots[0]
                    selected_spot.mbti_match = False
                    
                    self.logger.info(
                        f"Fallback assignment: {selected_spot.name} "
                        f"(District: {selected_spot.district}) for {session_type.value} session"
                    )
                    return selected_spot
        
        # Priority 2: Target areas
        if target_areas:
            for target_area in target_areas:
                area_spots = [
                    spot for spot in available_non_mbti_spots
                    if spot.matches_area(target_area)
                ]
                
                if area_spots:
                    selected_spot = area_spots[0]
                    selected_spot.mbti_match = False
                    
                    self.logger.info(
                        f"Fallback assignment: {selected_spot.name} "
                        f"(Area: {selected_spot.area}) for {session_type.value} session"
                    )
                    return selected_spot
        
        # Priority 3: Any available spot
        selected_spot = available_non_mbti_spots[0]
        selected_spot.mbti_match = False
        
        self.logger.info(
            f"Fallback assignment: {selected_spot.name} "
            f"(Any location) for {session_type.value} session"
        )
        return selected_spot

    def generate_uniqueness_report(
        self,
        day_assignments: Dict[int, Dict[str, TouristSpot]]
    ) -> Dict[str, Any]:
        """Generate comprehensive uniqueness constraint report.
        
        Args:
            day_assignments: Dictionary of day assignments to analyze
            
        Returns:
            Dictionary with uniqueness analysis and statistics
        """
        report = {
            'total_sessions': 0,
            'assigned_sessions': 0,
            'unique_spots_used': 0,
            'duplicate_violations': 0,
            'uniqueness_rate': 0.0,
            'spot_usage_distribution': {},
            'day_by_day_analysis': {},
            'violations': []
        }
        
        all_assignments = []
        spot_usage_count = {}
        
        # Collect all assignments
        for day_num, sessions in day_assignments.items():
            day_analysis = {
                'total_sessions': len(sessions),
                'assigned_sessions': 0,
                'spots_used': []
            }
            
            for session_type, spot in sessions.items():
                report['total_sessions'] += 1
                
                if spot and spot.id:
                    report['assigned_sessions'] += 1
                    day_analysis['assigned_sessions'] += 1
                    day_analysis['spots_used'].append({
                        'session': session_type,
                        'spot_id': spot.id,
                        'spot_name': spot.name
                    })
                    
                    all_assignments.append({
                        'day': day_num,
                        'session': session_type,
                        'spot_id': spot.id,
                        'spot_name': spot.name
                    })
                    
                    # Count usage
                    spot_usage_count[spot.id] = spot_usage_count.get(spot.id, 0) + 1
            
            report['day_by_day_analysis'][f'day_{day_num}'] = day_analysis
        
        # Analyze uniqueness
        unique_spot_ids = set(assignment['spot_id'] for assignment in all_assignments)
        report['unique_spots_used'] = len(unique_spot_ids)
        
        # Find violations
        violations = []
        for spot_id, usage_count in spot_usage_count.items():
            if usage_count > 1:
                report['duplicate_violations'] += 1
                
                # Find all assignments for this spot
                spot_assignments = [
                    assignment for assignment in all_assignments
                    if assignment['spot_id'] == spot_id
                ]
                
                violations.append({
                    'spot_id': spot_id,
                    'spot_name': spot_assignments[0]['spot_name'],
                    'usage_count': usage_count,
                    'assignments': spot_assignments
                })
        
        report['violations'] = violations
        report['spot_usage_distribution'] = spot_usage_count
        
        # Calculate uniqueness rate
        if report['assigned_sessions'] > 0:
            report['uniqueness_rate'] = (
                (report['assigned_sessions'] - report['duplicate_violations']) /
                report['assigned_sessions']
            )
        
        return report

    def suggest_uniqueness_fixes(
        self,
        violations: List[Dict[str, Any]],
        all_spots: List[TouristSpot],
        mbti_personality: str
    ) -> List[Dict[str, Any]]:
        """Suggest fixes for uniqueness constraint violations.
        
        Args:
            violations: List of uniqueness violations from report
            all_spots: List of all available tourist spots
            mbti_personality: MBTI personality type for suggestions
            
        Returns:
            List of suggested fixes with alternative spots
        """
        suggestions = []
        
        for violation in violations:
            spot_id = violation['spot_id']
            assignments = violation['assignments']
            
            # For each duplicate assignment, suggest alternatives
            for i, assignment in enumerate(assignments[1:], 1):  # Skip first occurrence
                day = assignment['day']
                session = assignment['session']
                session_type = SessionType(session)
                
                # Find alternative spots
                alternative_spots = []
                
                for spot in all_spots:
                    if (spot.id != spot_id and
                        spot.is_available_for_session(session_type)):
                        
                        # Prefer MBTI-matched alternatives
                        if spot.matches_mbti_personality(mbti_personality):
                            alternative_spots.insert(0, spot)  # Add to front
                        else:
                            alternative_spots.append(spot)
                
                suggestion = {
                    'violation_spot_id': spot_id,
                    'violation_spot_name': assignment['spot_name'],
                    'duplicate_assignment': {
                        'day': day,
                        'session': session
                    },
                    'suggested_alternatives': [
                        {
                            'spot_id': alt_spot.id,
                            'spot_name': alt_spot.name,
                            'district': alt_spot.district,
                            'area': alt_spot.area,
                            'mbti_match': alt_spot.matches_mbti_personality(mbti_personality)
                        }
                        for alt_spot in alternative_spots[:5]  # Top 5 alternatives
                    ]
                }
                
                suggestions.append(suggestion)
        
        return suggestions


class ItineraryUniquenessValidator:
    """Complete itinerary uniqueness validation and enforcement.
    
    Provides comprehensive validation and enforcement of uniqueness constraints
    across the entire 3-day itinerary generation process.
    """

    def __init__(self):
        """Initialize itinerary uniqueness validator."""
        self.logger = logging.getLogger(__name__)
        self.uniqueness_enforcer = UniquenessConstraintEnforcer()

    def validate_complete_itinerary_uniqueness(
        self,
        main_itinerary: 'MainItinerary'
    ) -> Dict[str, Any]:
        """Validate uniqueness constraints for complete itinerary.
        
        Args:
            main_itinerary: Complete 3-day itinerary to validate
            
        Returns:
            Dictionary with validation results and detailed analysis
        """
        # Extract day assignments
        day_assignments = {}
        
        for day_num, day_attr in [(1, 'day_1'), (2, 'day_2'), (3, 'day_3')]:
            day_itinerary = getattr(main_itinerary, day_attr)
            day_assignments[day_num] = {}
            
            # Extract session assignments
            for session_type in ['morning', 'afternoon', 'night']:
                session_attr = f'{session_type}_session'
                session_assignment = getattr(day_itinerary, session_attr, None)
                
                if session_assignment and session_assignment.tourist_spot:
                    day_assignments[day_num][session_type] = session_assignment.tourist_spot
                else:
                    day_assignments[day_num][session_type] = None
        
        # Validate uniqueness
        violations = self.uniqueness_enforcer.validate_uniqueness_across_itinerary(
            day_assignments
        )
        
        # Generate comprehensive report
        uniqueness_report = self.uniqueness_enforcer.generate_uniqueness_report(
            day_assignments
        )
        
        validation_result = {
            'is_valid': len(violations) == 0,
            'violation_count': len(violations),
            'violations': violations,
            'uniqueness_report': uniqueness_report,
            'validation_timestamp': datetime.now().isoformat()
        }
        
        if violations:
            self.logger.error(
                f"Itinerary uniqueness validation failed: {len(violations)} violations found"
            )
        else:
            self.logger.info("Itinerary uniqueness validation passed")
        
        return validation_result

    def enforce_uniqueness_during_generation(
        self,
        session_assignment_logic: SessionAssignmentLogic,
        all_spots: List[TouristSpot],
        mbti_personality: str
    ) -> Dict[int, Dict[str, AssignmentResult]]:
        """Enforce uniqueness constraints during itinerary generation.
        
        Args:
            session_assignment_logic: Session assignment logic instance
            all_spots: List of all available tourist spots
            mbti_personality: MBTI personality type
            
        Returns:
            Dictionary with assignment results for all 9 sessions
        """
        assignment_results = {}
        used_spots = set()
        
        # Generate assignments for each day
        for day_num in [1, 2, 3]:
            assignment_results[day_num] = {}
            day_spots = {}
            
            # Morning session
            morning_result = session_assignment_logic.assign_morning_session(
                all_spots, used_spots, mbti_personality, day_num
            )
            assignment_results[day_num]['morning'] = morning_result
            
            if morning_result.tourist_spot:
                used_spots.add(morning_result.tourist_spot.id)
                day_spots['morning'] = morning_result.tourist_spot
            
            # Afternoon session
            afternoon_result = session_assignment_logic.assign_afternoon_session(
                all_spots, used_spots, day_spots.get('morning'), mbti_personality, day_num
            )
            assignment_results[day_num]['afternoon'] = afternoon_result
            
            if afternoon_result.tourist_spot:
                used_spots.add(afternoon_result.tourist_spot.id)
                day_spots['afternoon'] = afternoon_result.tourist_spot
            
            # Night session
            night_result = session_assignment_logic.assign_night_session(
                all_spots, used_spots, day_spots.get('morning'), 
                day_spots.get('afternoon'), mbti_personality, day_num
            )
            assignment_results[day_num]['night'] = night_result
            
            if night_result.tourist_spot:
                used_spots.add(night_result.tourist_spot.id)
        
        self.logger.info(
            f"Generated assignments for 3-day itinerary: {len(used_spots)} unique spots used"
        )
        
        return assignment_results