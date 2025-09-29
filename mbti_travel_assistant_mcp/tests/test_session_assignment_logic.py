"""Tests for session assignment logic engine.

This module contains comprehensive tests for the session assignment logic,
district and area matching, and uniqueness constraint enforcement.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Set, Dict, Any

from ..services.session_assignment_logic import (
    SessionAssignmentLogic,
    DistrictAreaMatcher,
    LocationOptimizer,
    UniquenessConstraintEnforcer,
    ItineraryUniquenessValidator,
    AssignmentContext,
    AssignmentResult,
    AssignmentPriority
)
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from ..models.itinerary_models import MainItinerary, DayItinerary, SessionAssignment


class TestSessionAssignmentLogic:
    """Test cases for SessionAssignmentLogic class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_logic = SessionAssignmentLogic()
        
        # Create test tourist spots
        self.test_spots = self._create_test_spots()
        self.mbti_personality = "INFJ"

    def _create_test_spots(self) -> List[TouristSpot]:
        """Create test tourist spots for testing."""
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
        
        # Non-INFJ spots
        for i in range(3):
            operating_hours = TouristSpotOperatingHours(
                monday="10:00-22:00",
                tuesday="10:00-22:00",
                wednesday="10:00-22:00",
                thursday="10:00-22:00",
                friday="10:00-22:00",
                saturday="10:00-22:00",
                sunday="10:00-22:00"
            )
            
            spot = TouristSpot(
                id=f"non_infj_spot_{i}",
                name=f"Non-INFJ Spot {i}",
                address=f"Non-INFJ Address {i}",
                district="Tsim Sha Tsui",
                area="Kowloon",
                location_category="Entertainment",
                description=f"Test non-INFJ spot {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=["ESTP", "ENFP"],
                keywords=["active", "social", "vibrant"]
            )
            spots.append(spot)
        
        return spots

    def test_assign_morning_session_success(self):
        """Test successful morning session assignment."""
        used_spots = set()
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is True
        assert result.assignment_priority == AssignmentPriority.MBTI_MATCH_ANY_LOCATION
        assert result.fallback_used is False
        assert result.tourist_spot.matches_mbti_personality(self.mbti_personality)

    def test_assign_morning_session_with_used_spots(self):
        """Test morning session assignment with some spots already used."""
        # Mark first 3 INFJ spots as used
        used_spots = {f"infj_spot_{i}" for i in range(3)}
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.tourist_spot.id not in used_spots
        assert result.mbti_match is True

    def test_assign_afternoon_session_same_district(self):
        """Test afternoon session assignment with same district priority."""
        used_spots = set()
        
        # First assign morning session
        morning_result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        used_spots.add(morning_result.tourist_spot.id)
        
        # Then assign afternoon session
        afternoon_result = self.session_logic.assign_afternoon_session(
            self.test_spots, used_spots, morning_result.tourist_spot, self.mbti_personality, 1
        )
        
        assert afternoon_result.tourist_spot is not None
        assert afternoon_result.tourist_spot.id not in used_spots
        assert afternoon_result.mbti_match is True
        
        # Should prefer same district if available
        if afternoon_result.district_match:
            assert afternoon_result.tourist_spot.district == morning_result.tourist_spot.district

    def test_assign_night_session_location_priority(self):
        """Test night session assignment with location priority."""
        used_spots = set()
        
        # Assign morning and afternoon sessions
        morning_result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        used_spots.add(morning_result.tourist_spot.id)
        
        afternoon_result = self.session_logic.assign_afternoon_session(
            self.test_spots, used_spots, morning_result.tourist_spot, self.mbti_personality, 1
        )
        used_spots.add(afternoon_result.tourist_spot.id)
        
        # Assign night session
        night_result = self.session_logic.assign_night_session(
            self.test_spots, used_spots, morning_result.tourist_spot,
            afternoon_result.tourist_spot, self.mbti_personality, 1
        )
        
        assert night_result.tourist_spot is not None
        assert night_result.tourist_spot.id not in used_spots
        assert night_result.mbti_match is True

    def test_fallback_assignment_when_mbti_exhausted(self):
        """Test fallback assignment when MBTI spots are exhausted."""
        # Mark all INFJ spots as used
        used_spots = {f"infj_spot_{i}" for i in range(5)}
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is False
        assert result.fallback_used is True
        assert result.assignment_priority in [
            AssignmentPriority.NON_MBTI_SAME_DISTRICT,
            AssignmentPriority.NON_MBTI_SAME_AREA,
            AssignmentPriority.NON_MBTI_ANY_LOCATION
        ]

    def test_validate_session_assignment(self):
        """Test session assignment validation."""
        spot = self.test_spots[0]  # INFJ spot with 09:00-18:00 hours
        
        # Should be valid for morning and afternoon sessions
        morning_errors = self.session_logic.validate_session_assignment(
            spot, SessionType.MORNING
        )
        assert len(morning_errors) == 0
        
        afternoon_errors = self.session_logic.validate_session_assignment(
            spot, SessionType.AFTERNOON
        )
        assert len(afternoon_errors) == 0

    def test_get_assignment_statistics(self):
        """Test assignment statistics generation."""
        # Create some assignment results
        results = []
        
        for i in range(3):
            result = AssignmentResult(
                tourist_spot=self.test_spots[i],
                assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
                mbti_match=True,
                district_match=i == 0,
                area_match=True,
                fallback_used=False
            )
            results.append(result)
        
        stats = self.session_logic.get_assignment_statistics(results)
        
        assert stats['total_assignments'] == 3
        assert stats['successful_assignments'] == 3
        assert stats['success_rate'] == 1.0
        assert stats['mbti_matches'] == 3
        assert stats['mbti_match_rate'] == 1.0
        assert stats['district_matches'] == 1
        assert stats['area_matches'] == 3


class TestDistrictAreaMatcher:
    """Test cases for DistrictAreaMatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = DistrictAreaMatcher()
        self.test_spots = self._create_test_spots()

    def _create_test_spots(self) -> List[TouristSpot]:
        """Create test spots with different districts and areas."""
        spots = []
        
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui"]
        areas = ["Hong Kong Island", "Kowloon"]
        
        for i, district in enumerate(districts):
            area = areas[0] if i < 3 else areas[1]
            
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
                id=f"spot_{i}",
                name=f"Spot {i}",
                address=f"Address {i}",
                district=district,
                area=area,
                location_category="Attraction",
                description=f"Test spot {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=["INFJ"]
            )
            spots.append(spot)
        
        return spots

    def test_find_best_district_match(self):
        """Test finding best district match."""
        target_districts = ["Central", "Admiralty"]
        used_spots = set()
        
        matches, matched_district = self.matcher.find_best_district_match(
            self.test_spots, target_districts, SessionType.MORNING, used_spots
        )
        
        assert len(matches) > 0
        assert matched_district in target_districts
        assert all(spot.district == matched_district for spot in matches)

    def test_find_best_area_match(self):
        """Test finding best area match."""
        target_areas = ["Hong Kong Island"]
        used_spots = set()
        
        matches, matched_area = self.matcher.find_best_area_match(
            self.test_spots, target_areas, SessionType.MORNING, used_spots
        )
        
        assert len(matches) > 0
        assert matched_area in target_areas
        assert all(spot.area == matched_area for spot in matches)

    def test_calculate_location_priority_score(self):
        """Test location priority score calculation."""
        spot = self.test_spots[0]  # Central district, Hong Kong Island area
        target_districts = ["Central", "Admiralty"]
        target_areas = ["Hong Kong Island"]
        
        score = self.matcher.calculate_location_priority_score(
            spot, target_districts, target_areas
        )
        
        assert score == 10  # Exact match with first district

    def test_get_same_location_spots(self):
        """Test getting spots in same location as reference spots."""
        reference_spots = [self.test_spots[0]]  # Central district spot
        used_spots = set()
        
        same_location_spots = self.matcher.get_same_location_spots(
            self.test_spots, reference_spots, SessionType.AFTERNOON, used_spots
        )
        
        assert len(same_location_spots) > 0
        # Should prioritize spots in same district or area
        assert any(spot.district == "Central" for spot in same_location_spots[:2])

    def test_validate_district_area_consistency(self):
        """Test district and area consistency validation."""
        # Test with spots from different districts
        mixed_spots = [self.test_spots[0], self.test_spots[3]]  # Central and Tsim Sha Tsui
        
        warnings = self.matcher.validate_district_area_consistency(mixed_spots)
        
        assert len(warnings) > 0
        assert any("Multiple areas" in warning for warning in warnings)


class TestUniquenessConstraintEnforcer:
    """Test cases for UniquenessConstraintEnforcer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = UniquenessConstraintEnforcer()
        self.test_spots = self._create_test_spots()

    def _create_test_spots(self) -> List[TouristSpot]:
        """Create test spots for uniqueness testing."""
        spots = []
        
        for i in range(10):
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
                id=f"unique_spot_{i}",
                name=f"Unique Spot {i}",
                address=f"Address {i}",
                district="Central",
                area="Hong Kong Island",
                location_category="Attraction",
                description=f"Test spot {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=["INFJ"]
            )
            spots.append(spot)
        
        return spots

    def test_validate_uniqueness_across_itinerary_valid(self):
        """Test uniqueness validation with valid itinerary."""
        day_assignments = {
            1: {
                'morning': self.test_spots[0],
                'afternoon': self.test_spots[1],
                'night': self.test_spots[2]
            },
            2: {
                'morning': self.test_spots[3],
                'afternoon': self.test_spots[4],
                'night': self.test_spots[5]
            },
            3: {
                'morning': self.test_spots[6],
                'afternoon': self.test_spots[7],
                'night': self.test_spots[8]
            }
        }
        
        errors = self.enforcer.validate_uniqueness_across_itinerary(day_assignments)
        assert len(errors) == 0

    def test_validate_uniqueness_across_itinerary_invalid(self):
        """Test uniqueness validation with duplicate assignments."""
        day_assignments = {
            1: {
                'morning': self.test_spots[0],
                'afternoon': self.test_spots[1],
                'night': self.test_spots[2]
            },
            2: {
                'morning': self.test_spots[0],  # Duplicate!
                'afternoon': self.test_spots[3],
                'night': self.test_spots[4]
            },
            3: {
                'morning': self.test_spots[5],
                'afternoon': self.test_spots[6],
                'night': self.test_spots[7]
            }
        }
        
        errors = self.enforcer.validate_uniqueness_across_itinerary(day_assignments)
        assert len(errors) > 0
        assert "Duplicate assignment" in errors[0]

    def test_track_used_spots_across_days(self):
        """Test tracking used spots across day assignments."""
        existing_assignments = {
            1: {
                'morning': self.test_spots[0],
                'afternoon': self.test_spots[1],
                'night': self.test_spots[2]
            },
            2: {
                'morning': self.test_spots[3],
                'afternoon': None,  # No assignment
                'night': self.test_spots[4]
            }
        }
        
        used_spots = self.enforcer.track_used_spots_across_days(existing_assignments)
        
        expected_used = {'unique_spot_0', 'unique_spot_1', 'unique_spot_2', 'unique_spot_3', 'unique_spot_4'}
        assert used_spots == expected_used

    def test_get_available_spots_for_assignment(self):
        """Test getting available spots for assignment."""
        used_spots = {'unique_spot_0', 'unique_spot_1'}
        
        mbti_spots, non_mbti_spots = self.enforcer.get_available_spots_for_assignment(
            self.test_spots, used_spots, "INFJ", SessionType.MORNING, True
        )
        
        # All test spots are INFJ-matched
        assert len(mbti_spots) == 8  # 10 total - 2 used
        assert len(non_mbti_spots) == 0
        assert all(spot.id not in used_spots for spot in mbti_spots)

    def test_enforce_uniqueness_in_assignment(self):
        """Test enforcing uniqueness in candidate spots."""
        candidate_spots = self.test_spots[:5]
        used_spots = {'unique_spot_1', 'unique_spot_3'}
        
        unique_spots = self.enforcer.enforce_uniqueness_in_assignment(
            candidate_spots, used_spots
        )
        
        assert len(unique_spots) == 3  # 5 candidates - 2 used
        assert all(spot.id not in used_spots for spot in unique_spots)

    def test_generate_uniqueness_report(self):
        """Test generating uniqueness report."""
        day_assignments = {
            1: {
                'morning': self.test_spots[0],
                'afternoon': self.test_spots[1],
                'night': self.test_spots[2]
            },
            2: {
                'morning': self.test_spots[0],  # Duplicate
                'afternoon': self.test_spots[3],
                'night': self.test_spots[4]
            }
        }
        
        report = self.enforcer.generate_uniqueness_report(day_assignments)
        
        assert report['total_sessions'] == 6
        assert report['assigned_sessions'] == 6
        assert report['unique_spots_used'] == 5
        assert report['duplicate_violations'] == 1
        assert report['uniqueness_rate'] < 1.0
        assert len(report['violations']) == 1


class TestItineraryUniquenessValidator:
    """Test cases for ItineraryUniquenessValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ItineraryUniquenessValidator()

    def test_enforce_uniqueness_during_generation(self):
        """Test enforcing uniqueness during itinerary generation."""
        # Create mock session assignment logic
        session_logic = Mock(spec=SessionAssignmentLogic)
        
        # Mock assignment results
        def mock_morning_assignment(spots, used_spots, mbti, day):
            available_spots = [s for s in spots if s.id not in used_spots]
            if available_spots:
                return AssignmentResult(
                    tourist_spot=available_spots[0],
                    mbti_match=True,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION
                )
            return AssignmentResult()
        
        def mock_afternoon_assignment(spots, used_spots, morning_spot, mbti, day):
            available_spots = [s for s in spots if s.id not in used_spots]
            if available_spots:
                return AssignmentResult(
                    tourist_spot=available_spots[0],
                    mbti_match=True,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION
                )
            return AssignmentResult()
        
        def mock_night_assignment(spots, used_spots, morning_spot, afternoon_spot, mbti, day):
            available_spots = [s for s in spots if s.id not in used_spots]
            if available_spots:
                return AssignmentResult(
                    tourist_spot=available_spots[0],
                    mbti_match=True,
                    assignment_priority=AssignmentPriority.MBTI_MATCH_ANY_LOCATION
                )
            return AssignmentResult()
        
        session_logic.assign_morning_session.side_effect = mock_morning_assignment
        session_logic.assign_afternoon_session.side_effect = mock_afternoon_assignment
        session_logic.assign_night_session.side_effect = mock_night_assignment
        
        # Create test spots
        test_spots = []
        for i in range(10):
            operating_hours = TouristSpotOperatingHours(monday="09:00-18:00")
            spot = TouristSpot(
                id=f"test_spot_{i}",
                name=f"Test Spot {i}",
                address=f"Address {i}",
                district="Central",
                area="Hong Kong Island",
                location_category="Attraction",
                description=f"Test spot {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=["INFJ"]
            )
            test_spots.append(spot)
        
        # Generate assignments
        assignment_results = self.validator.enforce_uniqueness_during_generation(
            session_logic, test_spots, "INFJ"
        )
        
        # Verify structure
        assert len(assignment_results) == 3  # 3 days
        for day_num in [1, 2, 3]:
            assert day_num in assignment_results
            assert len(assignment_results[day_num]) == 3  # 3 sessions per day
            assert 'morning' in assignment_results[day_num]
            assert 'afternoon' in assignment_results[day_num]
            assert 'night' in assignment_results[day_num]


if __name__ == "__main__":
    pytest.main([__file__])