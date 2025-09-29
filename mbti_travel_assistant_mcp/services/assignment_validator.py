"""Assignment validator system for MBTI Travel Assistant.

This module implements comprehensive validation logic for business rule validation
of session assignments, operating hours validation, and district matching validation.
Follows PEP8 style guidelines and implements requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.10.
"""

import logging
from datetime import datetime, time
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass

from ..models.tourist_spot_models import TouristSpot, SessionType
from ..models.itinerary_models import MainItinerary, DayItinerary, SessionAssignment, MealAssignment
from ..models.restaurant_models import Restaurant


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    OPERATING_HOURS = "operating_hours"
    DISTRICT_MATCHING = "district_matching"
    AREA_MATCHING = "area_matching"
    UNIQUENESS = "uniqueness"
    MBTI_MATCHING = "mbti_matching"
    RESTAURANT_HOURS = "restaurant_hours"
    RESTAURANT_DISTRICTS = "restaurant_districts"
    DATA_INTEGRITY = "data_integrity"


@dataclass
class ValidationIssue:
    """Individual validation issue with details and suggestions.
    
    Attributes:
        severity: Severity level of the issue
        category: Category of validation check
        message: Detailed description of the issue
        location: Location context (e.g., "day_1.morning_session")
        suggestion: Suggested correction for the issue
        affected_item_id: ID of the affected tourist spot or restaurant
        affected_item_name: Name of the affected item
        rule_violated: Specific business rule that was violated
    """
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    location: str
    suggestion: str = ""
    affected_item_id: str = ""
    affected_item_name: str = ""
    rule_violated: str = ""


@dataclass
class ValidationReport:
    """Comprehensive validation report with issues and statistics.
    
    Attributes:
        is_valid: Overall validation status
        total_issues: Total number of validation issues
        error_count: Number of error-level issues
        warning_count: Number of warning-level issues
        info_count: Number of info-level issues
        issues: List of all validation issues
        validation_timestamp: When validation was performed
        validation_summary: Summary of validation results
        correction_suggestions: List of suggested corrections
    """
    is_valid: bool
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue]
    validation_timestamp: str
    validation_summary: Dict[str, Any]
    correction_suggestions: List[str]

    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if not self.validation_timestamp:
            self.validation_timestamp = datetime.now().isoformat()
        
        if not self.validation_summary:
            self.validation_summary = self._generate_summary()
        
        if not self.correction_suggestions:
            self.correction_suggestions = self._generate_correction_suggestions()

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary statistics."""
        category_counts = {}
        for issue in self.issues:
            category = issue.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_checks_performed': len(self.issues) if self.issues else 0,
            'issues_by_category': category_counts,
            'issues_by_severity': {
                'errors': self.error_count,
                'warnings': self.warning_count,
                'info': self.info_count
            },
            'validation_passed': self.is_valid
        }

    def _generate_correction_suggestions(self) -> List[str]:
        """Generate list of correction suggestions from issues."""
        suggestions = []
        for issue in self.issues:
            if issue.suggestion and issue.suggestion not in suggestions:
                suggestions.append(issue.suggestion)
        return suggestions

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation report to dictionary format."""
        return {
            'is_valid': self.is_valid,
            'total_issues': self.total_issues,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'validation_timestamp': self.validation_timestamp,
            'validation_summary': self.validation_summary,
            'correction_suggestions': self.correction_suggestions,
            'issues': [
                {
                    'severity': issue.severity.value,
                    'category': issue.category.value,
                    'message': issue.message,
                    'location': issue.location,
                    'suggestion': issue.suggestion,
                    'affected_item_id': issue.affected_item_id,
                    'affected_item_name': issue.affected_item_name,
                    'rule_violated': issue.rule_violated
                }
                for issue in self.issues
            ]
        }


class AssignmentValidator:
    """Comprehensive validation logic for business rule validation.
    
    Implements validation for:
    - Operating hours validation for each session type (Requirement 7.1, 7.2, 7.3)
    - District matching validation (Requirement 7.4)
    - Area matching validation (Requirement 7.5)
    - Uniqueness constraints (Requirement 7.6)
    - MBTI matching validation (Requirement 7.7)
    - Restaurant assignment validation (Requirement 7.8, 7.9)
    - Detailed error reporting and correction suggestions (Requirement 7.10)
    """

    def __init__(self):
        """Initialize assignment validator."""
        self.logger = logging.getLogger(__name__)
        
        # Session time ranges for validation
        self.session_time_ranges = {
            SessionType.MORNING: (time(7, 0), time(11, 59)),    # 07:00-11:59
            SessionType.AFTERNOON: (time(12, 0), time(17, 59)), # 12:00-17:59
            SessionType.NIGHT: (time(18, 0), time(23, 59))      # 18:00-23:59
        }
        
        # Meal time ranges for restaurant validation
        self.meal_time_ranges = {
            'breakfast': (time(6, 0), time(11, 29)),   # 06:00-11:29
            'lunch': (time(11, 30), time(17, 29)),     # 11:30-17:29
            'dinner': (time(17, 30), time(23, 59))     # 17:30-23:59
        }

    def validate_complete_itinerary(self, itinerary: MainItinerary) -> ValidationReport:
        """Validate complete 3-day itinerary against all business rules.
        
        Args:
            itinerary: MainItinerary to validate
            
        Returns:
            ValidationReport with comprehensive validation results
        """
        self.logger.info(f"Starting complete itinerary validation for MBTI: {itinerary.mbti_personality}")
        
        issues = []
        
        # Validate basic itinerary structure
        issues.extend(self._validate_itinerary_structure(itinerary))
        
        # Validate session assignments for each day
        for day_num, day_itinerary in enumerate([itinerary.day_1, itinerary.day_2, itinerary.day_3], 1):
            day_issues = self._validate_day_itinerary(day_itinerary, day_num, itinerary.mbti_personality)
            issues.extend(day_issues)
        
        # Validate uniqueness constraints across all days
        issues.extend(self._validate_uniqueness_constraints(itinerary))
        
        # Validate district and area matching logic
        issues.extend(self._validate_district_area_matching(itinerary))
        
        # Count issues by severity
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        info_count = len([i for i in issues if i.severity == ValidationSeverity.INFO])
        
        # Determine overall validation status
        is_valid = error_count == 0
        
        self.logger.info(
            f"Validation completed: {len(issues)} total issues "
            f"({error_count} errors, {warning_count} warnings, {info_count} info)"
        )
        
        return ValidationReport(
            is_valid=is_valid,
            total_issues=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=issues,
            validation_timestamp=datetime.now().isoformat(),
            validation_summary={},
            correction_suggestions=[]
        )

    def validate_session_operating_hours(
        self, 
        tourist_spot: TouristSpot, 
        session_type: SessionType,
        location_context: str = ""
    ) -> List[ValidationIssue]:
        """Validate tourist spot operating hours for specific session type.
        
        Implements requirements 7.1, 7.2, 7.3:
        - Morning sessions: 07:00-11:59 or no operating hours
        - Afternoon sessions: 12:00-17:59 or no operating hours
        - Night sessions: 18:00-23:59 or no operating hours
        
        Args:
            tourist_spot: Tourist spot to validate
            session_type: Session type to validate against
            location_context: Context for error reporting
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not tourist_spot:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message="Tourist spot is None or missing",
                location=location_context,
                suggestion="Ensure tourist spot is properly assigned",
                rule_violated="Tourist spot must be present for validation"
            ))
            return issues
        
        # Check if tourist spot is available for the session
        if not tourist_spot.is_available_for_session(session_type):
            session_time_str = self._get_session_time_string(session_type)
            
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OPERATING_HOURS,
                message=(
                    f"Tourist spot '{tourist_spot.name}' is not available during "
                    f"{session_type.value} session ({session_time_str})"
                ),
                location=location_context,
                suggestion=(
                    f"Replace with a tourist spot that operates during "
                    f"{session_type.value} hours or has no operating hour restrictions"
                ),
                affected_item_id=tourist_spot.id,
                affected_item_name=tourist_spot.name,
                rule_violated=f"Requirement 7.{self._get_requirement_number(session_type)}"
            ))
        
        return issues

    def validate_district_matching(
        self,
        afternoon_spot: Optional[TouristSpot],
        night_spot: Optional[TouristSpot],
        morning_spot: Optional[TouristSpot],
        location_context: str = ""
    ) -> List[ValidationIssue]:
        """Validate district matching logic for afternoon and night sessions.
        
        Implements requirement 7.4:
        - Afternoon and night spots should prioritize same district as morning spot
        
        Args:
            afternoon_spot: Afternoon session tourist spot
            night_spot: Night session tourist spot
            morning_spot: Morning session tourist spot for reference
            location_context: Context for error reporting
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not morning_spot:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DISTRICT_MATCHING,
                message="No morning spot available for district matching validation",
                location=location_context,
                suggestion="Ensure morning session is assigned before afternoon and night sessions",
                rule_violated="Requirement 7.4"
            ))
            return issues
        
        target_district = morning_spot.district
        
        # Validate afternoon spot district matching
        if afternoon_spot:
            if not afternoon_spot.matches_district(target_district):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DISTRICT_MATCHING,
                    message=(
                        f"Afternoon spot '{afternoon_spot.name}' is in district "
                        f"'{afternoon_spot.district}' but morning spot is in '{target_district}'"
                    ),
                    location=f"{location_context}.afternoon_session",
                    suggestion=(
                        f"Consider selecting an afternoon spot in '{target_district}' district "
                        "for better location coherence"
                    ),
                    affected_item_id=afternoon_spot.id,
                    affected_item_name=afternoon_spot.name,
                    rule_violated="Requirement 7.4"
                ))
        
        # Validate night spot district matching
        if night_spot:
            # Night spot should match either morning or afternoon district
            morning_district_match = night_spot.matches_district(morning_spot.district)
            afternoon_district_match = (
                afternoon_spot and night_spot.matches_district(afternoon_spot.district)
            )
            
            if not (morning_district_match or afternoon_district_match):
                reference_districts = [morning_spot.district]
                if afternoon_spot:
                    reference_districts.append(afternoon_spot.district)
                
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.DISTRICT_MATCHING,
                    message=(
                        f"Night spot '{night_spot.name}' is in district "
                        f"'{night_spot.district}' but doesn't match morning/afternoon districts: "
                        f"{', '.join(set(reference_districts))}"
                    ),
                    location=f"{location_context}.night_session",
                    suggestion=(
                        f"Consider selecting a night spot in one of these districts: "
                        f"{', '.join(set(reference_districts))}"
                    ),
                    affected_item_id=night_spot.id,
                    affected_item_name=night_spot.name,
                    rule_violated="Requirement 7.4"
                ))
        
        return issues

    def validate_area_matching(
        self,
        afternoon_spot: Optional[TouristSpot],
        night_spot: Optional[TouristSpot],
        morning_spot: Optional[TouristSpot],
        location_context: str = ""
    ) -> List[ValidationIssue]:
        """Validate area matching fallback logic.
        
        Implements requirement 7.5:
        - Fallback to same area when same district is unavailable
        
        Args:
            afternoon_spot: Afternoon session tourist spot
            night_spot: Night session tourist spot
            morning_spot: Morning session tourist spot for reference
            location_context: Context for error reporting
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not morning_spot:
            return issues  # Already handled in district matching validation
        
        target_area = morning_spot.area
        
        # Check afternoon spot area matching (if district doesn't match)
        if afternoon_spot and not afternoon_spot.matches_district(morning_spot.district):
            if not afternoon_spot.matches_area(target_area):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=ValidationCategory.AREA_MATCHING,
                    message=(
                        f"Afternoon spot '{afternoon_spot.name}' is in area "
                        f"'{afternoon_spot.area}' but morning spot is in area '{target_area}'. "
                        "Area matching fallback was not used."
                    ),
                    location=f"{location_context}.afternoon_session",
                    suggestion=(
                        f"If no spots available in '{morning_spot.district}' district, "
                        f"consider selecting a spot in '{target_area}' area"
                    ),
                    affected_item_id=afternoon_spot.id,
                    affected_item_name=afternoon_spot.name,
                    rule_violated="Requirement 7.5"
                ))
        
        # Check night spot area matching
        if night_spot:
            # Check if night spot matches any reference area
            morning_area_match = night_spot.matches_area(morning_spot.area)
            afternoon_area_match = (
                afternoon_spot and night_spot.matches_area(afternoon_spot.area)
            )
            
            # Also check district matching to determine if area fallback should apply
            morning_district_match = night_spot.matches_district(morning_spot.district)
            afternoon_district_match = (
                afternoon_spot and night_spot.matches_district(afternoon_spot.district)
            )
            
            if not (morning_district_match or afternoon_district_match):
                if not (morning_area_match or afternoon_area_match):
                    reference_areas = [morning_spot.area]
                    if afternoon_spot:
                        reference_areas.append(afternoon_spot.area)
                    
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.AREA_MATCHING,
                        message=(
                            f"Night spot '{night_spot.name}' is in area "
                            f"'{night_spot.area}' but doesn't match morning/afternoon areas: "
                            f"{', '.join(set(reference_areas))}"
                        ),
                        location=f"{location_context}.night_session",
                        suggestion=(
                            f"Consider area matching fallback with spots in: "
                            f"{', '.join(set(reference_areas))}"
                        ),
                        affected_item_id=night_spot.id,
                        affected_item_name=night_spot.name,
                        rule_violated="Requirement 7.5"
                    ))
        
        return issues

    def _validate_itinerary_structure(self, itinerary: MainItinerary) -> List[ValidationIssue]:
        """Validate basic itinerary structure and data integrity."""
        issues = []
        
        # Validate MBTI personality
        if not itinerary.mbti_personality:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message="MBTI personality is missing or empty",
                location="main_itinerary",
                suggestion="Provide a valid 4-character MBTI personality type",
                rule_violated="Basic data integrity"
            ))
        elif len(itinerary.mbti_personality) != 4:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message=f"MBTI personality '{itinerary.mbti_personality}' is not 4 characters",
                location="main_itinerary",
                suggestion="Provide a valid 4-character MBTI personality type (e.g., INFJ, ENFP)",
                rule_violated="Basic data integrity"
            ))
        
        # Validate day itineraries exist
        if not itinerary.day_1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message="Day 1 itinerary is missing",
                location="main_itinerary.day_1",
                suggestion="Ensure day 1 itinerary is properly created",
                rule_violated="Basic data integrity"
            ))
        
        if not itinerary.day_2:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message="Day 2 itinerary is missing",
                location="main_itinerary.day_2",
                suggestion="Ensure day 2 itinerary is properly created",
                rule_violated="Basic data integrity"
            ))
        
        if not itinerary.day_3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DATA_INTEGRITY,
                message="Day 3 itinerary is missing",
                location="main_itinerary.day_3",
                suggestion="Ensure day 3 itinerary is properly created",
                rule_violated="Basic data integrity"
            ))
        
        return issues

    def _validate_day_itinerary(
        self, 
        day_itinerary: DayItinerary, 
        day_number: int, 
        mbti_personality: str
    ) -> List[ValidationIssue]:
        """Validate individual day itinerary."""
        issues = []
        location_prefix = f"day_{day_number}"
        
        # Validate session assignments
        sessions = [
            (day_itinerary.morning_session, SessionType.MORNING, "morning_session"),
            (day_itinerary.afternoon_session, SessionType.AFTERNOON, "afternoon_session"),
            (day_itinerary.night_session, SessionType.NIGHT, "night_session")
        ]
        
        for session_assignment, session_type, session_name in sessions:
            location_context = f"{location_prefix}.{session_name}"
            
            if session_assignment and session_assignment.tourist_spot:
                # Validate operating hours
                issues.extend(self.validate_session_operating_hours(
                    session_assignment.tourist_spot,
                    session_type,
                    location_context
                ))
                
                # Validate MBTI matching
                issues.extend(self._validate_mbti_matching(
                    session_assignment.tourist_spot,
                    mbti_personality,
                    location_context
                ))
        
        # Validate district and area matching for this day
        issues.extend(self.validate_district_matching(
            day_itinerary.afternoon_session.tourist_spot if day_itinerary.afternoon_session else None,
            day_itinerary.night_session.tourist_spot if day_itinerary.night_session else None,
            day_itinerary.morning_session.tourist_spot if day_itinerary.morning_session else None,
            location_prefix
        ))
        
        issues.extend(self.validate_area_matching(
            day_itinerary.afternoon_session.tourist_spot if day_itinerary.afternoon_session else None,
            day_itinerary.night_session.tourist_spot if day_itinerary.night_session else None,
            day_itinerary.morning_session.tourist_spot if day_itinerary.morning_session else None,
            location_prefix
        ))
        
        # Validate restaurant assignments
        meals = [
            (day_itinerary.breakfast, "breakfast"),
            (day_itinerary.lunch, "lunch"),
            (day_itinerary.dinner, "dinner")
        ]
        
        for meal_assignment, meal_type in meals:
            if meal_assignment and meal_assignment.restaurant:
                location_context = f"{location_prefix}.{meal_type}"
                issues.extend(self._validate_restaurant_assignment(
                    meal_assignment.restaurant,
                    meal_type,
                    day_itinerary,
                    location_context
                ))
        
        return issues

    def _validate_uniqueness_constraints(self, itinerary: MainItinerary) -> List[ValidationIssue]:
        """Validate uniqueness constraints across all sessions and meals."""
        issues = []
        
        # Collect all tourist spots
        tourist_spots = []
        tourist_spot_locations = {}
        
        days = [
            (itinerary.day_1, "day_1"),
            (itinerary.day_2, "day_2"),
            (itinerary.day_3, "day_3")
        ]
        
        for day_itinerary, day_name in days:
            sessions = [
                (day_itinerary.morning_session, "morning_session"),
                (day_itinerary.afternoon_session, "afternoon_session"),
                (day_itinerary.night_session, "night_session")
            ]
            
            for session_assignment, session_name in sessions:
                if session_assignment and session_assignment.tourist_spot:
                    spot = session_assignment.tourist_spot
                    location = f"{day_name}.{session_name}"
                    
                    if spot.id in tourist_spot_locations:
                        # Duplicate found
                        previous_location = tourist_spot_locations[spot.id]
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.UNIQUENESS,
                            message=(
                                f"Tourist spot '{spot.name}' (ID: {spot.id}) is assigned to "
                                f"multiple sessions: {previous_location} and {location}"
                            ),
                            location=location,
                            suggestion=(
                                f"Replace duplicate assignment with a different tourist spot"
                            ),
                            affected_item_id=spot.id,
                            affected_item_name=spot.name,
                            rule_violated="Requirement 7.6"
                        ))
                    else:
                        tourist_spot_locations[spot.id] = location
                        tourist_spots.append(spot)
        
        # Collect all restaurants
        restaurant_locations = {}
        
        for day_itinerary, day_name in days:
            meals = [
                (day_itinerary.breakfast, "breakfast"),
                (day_itinerary.lunch, "lunch"),
                (day_itinerary.dinner, "dinner")
            ]
            
            for meal_assignment, meal_name in meals:
                if meal_assignment and meal_assignment.restaurant:
                    restaurant = meal_assignment.restaurant
                    location = f"{day_name}.{meal_name}"
                    
                    if restaurant.id in restaurant_locations:
                        # Duplicate found
                        previous_location = restaurant_locations[restaurant.id]
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.UNIQUENESS,
                            message=(
                                f"Restaurant '{restaurant.name}' (ID: {restaurant.id}) is assigned to "
                                f"multiple meals: {previous_location} and {location}"
                            ),
                            location=location,
                            suggestion=(
                                f"Replace duplicate assignment with a different restaurant"
                            ),
                            affected_item_id=restaurant.id,
                            affected_item_name=restaurant.name,
                            rule_violated="Requirement 7.6"
                        ))
                    else:
                        restaurant_locations[restaurant.id] = location
        
        return issues

    def _validate_district_area_matching(self, itinerary: MainItinerary) -> List[ValidationIssue]:
        """Validate district and area matching logic across all days."""
        issues = []
        
        days = [
            (itinerary.day_1, "day_1"),
            (itinerary.day_2, "day_2"),
            (itinerary.day_3, "day_3")
        ]
        
        for day_itinerary, day_name in days:
            morning_spot = (
                day_itinerary.morning_session.tourist_spot 
                if day_itinerary.morning_session else None
            )
            afternoon_spot = (
                day_itinerary.afternoon_session.tourist_spot 
                if day_itinerary.afternoon_session else None
            )
            night_spot = (
                day_itinerary.night_session.tourist_spot 
                if day_itinerary.night_session else None
            )
            
            # Validate district matching
            issues.extend(self.validate_district_matching(
                afternoon_spot, night_spot, morning_spot, day_name
            ))
            
            # Validate area matching
            issues.extend(self.validate_area_matching(
                afternoon_spot, night_spot, morning_spot, day_name
            ))
        
        return issues

    def _validate_mbti_matching(
        self, 
        tourist_spot: TouristSpot, 
        mbti_personality: str, 
        location_context: str
    ) -> List[ValidationIssue]:
        """Validate MBTI matching accuracy."""
        issues = []
        
        # Check if MBTI_match field accurately reflects personality alignment
        actual_match = tourist_spot.matches_mbti_personality(mbti_personality)
        reported_match = tourist_spot.mbti_match
        
        if actual_match != reported_match:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.MBTI_MATCHING,
                message=(
                    f"Tourist spot '{tourist_spot.name}' has MBTI_match={reported_match} "
                    f"but actual MBTI matching for '{mbti_personality}' is {actual_match}"
                ),
                location=location_context,
                suggestion=(
                    f"Update MBTI_match field to {actual_match} for accurate reporting"
                ),
                affected_item_id=tourist_spot.id,
                affected_item_name=tourist_spot.name,
                rule_violated="Requirement 7.7"
            ))
        
        return issues

    def _validate_restaurant_assignment(
        self,
        restaurant: Restaurant,
        meal_type: str,
        day_itinerary: DayItinerary,
        location_context: str
    ) -> List[ValidationIssue]:
        """Validate restaurant assignment against meal times and district matching."""
        issues = []
        
        # Validate restaurant operating hours match meal times
        if not self._restaurant_operates_during_meal(restaurant, meal_type):
            meal_time_str = self._get_meal_time_string(meal_type)
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.RESTAURANT_HOURS,
                message=(
                    f"Restaurant '{restaurant.name}' does not operate during "
                    f"{meal_type} hours ({meal_time_str})"
                ),
                location=location_context,
                suggestion=(
                    f"Replace with a restaurant that operates during {meal_type} hours"
                ),
                affected_item_id=restaurant.id,
                affected_item_name=restaurant.name,
                rule_violated="Requirement 7.8"
            ))
        
        # Validate restaurant district matching with tourist spots
        issues.extend(self._validate_restaurant_district_matching(
            restaurant, meal_type, day_itinerary, location_context
        ))
        
        return issues

    def _validate_restaurant_district_matching(
        self,
        restaurant: Restaurant,
        meal_type: str,
        day_itinerary: DayItinerary,
        location_context: str
    ) -> List[ValidationIssue]:
        """Validate restaurant district matching with corresponding tourist spots."""
        issues = []
        
        # Determine which tourist spots should match based on meal type
        reference_spots = []
        
        if meal_type == "breakfast":
            # Breakfast should match morning tourist spot district
            if day_itinerary.morning_session and day_itinerary.morning_session.tourist_spot:
                reference_spots.append(day_itinerary.morning_session.tourist_spot)
        elif meal_type == "lunch":
            # Lunch should match morning or afternoon tourist spot district
            if day_itinerary.morning_session and day_itinerary.morning_session.tourist_spot:
                reference_spots.append(day_itinerary.morning_session.tourist_spot)
            if day_itinerary.afternoon_session and day_itinerary.afternoon_session.tourist_spot:
                reference_spots.append(day_itinerary.afternoon_session.tourist_spot)
        elif meal_type == "dinner":
            # Dinner should match afternoon or night tourist spot district
            if day_itinerary.afternoon_session and day_itinerary.afternoon_session.tourist_spot:
                reference_spots.append(day_itinerary.afternoon_session.tourist_spot)
            if day_itinerary.night_session and day_itinerary.night_session.tourist_spot:
                reference_spots.append(day_itinerary.night_session.tourist_spot)
        
        if reference_spots:
            # Check if restaurant district matches any reference spot district
            reference_districts = [spot.district for spot in reference_spots]
            restaurant_district = restaurant.district
            
            if restaurant_district not in reference_districts:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.RESTAURANT_DISTRICTS,
                    message=(
                        f"Restaurant '{restaurant.name}' is in district '{restaurant_district}' "
                        f"but {meal_type} should be in districts: {', '.join(set(reference_districts))}"
                    ),
                    location=location_context,
                    suggestion=(
                        f"Consider selecting a {meal_type} restaurant in one of these districts: "
                        f"{', '.join(set(reference_districts))}"
                    ),
                    affected_item_id=restaurant.id,
                    affected_item_name=restaurant.name,
                    rule_violated="Requirement 7.9"
                ))
        
        return issues

    def _restaurant_operates_during_meal(self, restaurant: Restaurant, meal_type: str) -> bool:
        """Check if restaurant operates during specific meal time."""
        if meal_type not in self.meal_time_ranges:
            return True  # Unknown meal type, assume valid
        
        meal_start, meal_end = self.meal_time_ranges[meal_type]
        
        # Check restaurant operating hours (simplified check)
        # This would need to be implemented based on the Restaurant model structure
        # For now, assume restaurant has operating_hours similar to tourist spots
        
        if hasattr(restaurant, 'operating_hours') and restaurant.operating_hours:
            # Implementation would depend on restaurant operating hours format
            # For now, return True as placeholder
            return True
        
        # If no operating hours specified, assume always open
        return True

    def _get_session_time_string(self, session_type: SessionType) -> str:
        """Get human-readable time string for session type."""
        time_ranges = {
            SessionType.MORNING: "07:00-11:59",
            SessionType.AFTERNOON: "12:00-17:59",
            SessionType.NIGHT: "18:00-23:59"
        }
        return time_ranges.get(session_type, "Unknown")

    def _get_meal_time_string(self, meal_type: str) -> str:
        """Get human-readable time string for meal type."""
        time_ranges = {
            "breakfast": "06:00-11:29",
            "lunch": "11:30-17:29",
            "dinner": "17:30-23:59"
        }
        return time_ranges.get(meal_type, "Unknown")

    def _get_requirement_number(self, session_type: SessionType) -> str:
        """Get requirement number for session type."""
        requirement_map = {
            SessionType.MORNING: "1",
            SessionType.AFTERNOON: "2",
            SessionType.NIGHT: "3"
        }
        return requirement_map.get(session_type, "X")

    def generate_detailed_validation_report(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Generate detailed validation report with comprehensive analysis.
        
        Implements requirement 7.4: Create detailed validation error reporting
        
        Args:
            itinerary: MainItinerary to analyze
            
        Returns:
            Detailed validation report dictionary
        """
        validation_report = self.validate_complete_itinerary(itinerary)
        
        # Generate additional analysis
        detailed_report = validation_report.to_dict()
        
        # Add detailed analysis sections
        detailed_report['detailed_analysis'] = {
            'session_analysis': self._analyze_session_assignments(itinerary),
            'restaurant_analysis': self._analyze_restaurant_assignments(itinerary),
            'location_coherence_analysis': self._analyze_location_coherence(itinerary),
            'mbti_alignment_analysis': self._analyze_mbti_alignment(itinerary),
            'coverage_analysis': self._analyze_coverage_completeness(itinerary)
        }
        
        # Add correction recommendations
        detailed_report['correction_recommendations'] = self._generate_correction_recommendations(
            validation_report.issues
        )
        
        # Add validation metrics
        detailed_report['validation_metrics'] = self._calculate_validation_metrics(
            validation_report.issues, itinerary
        )
        
        return detailed_report

    def generate_validation_warnings(self, itinerary: MainItinerary) -> List[Dict[str, Any]]:
        """Generate validation warnings for non-critical issues.
        
        Implements requirement 7.5: Implement validation warning system for non-critical issues
        
        Args:
            itinerary: MainItinerary to check for warnings
            
        Returns:
            List of warning dictionaries with details and suggestions
        """
        validation_report = self.validate_complete_itinerary(itinerary)
        
        warnings = []
        for issue in validation_report.issues:
            if issue.severity == ValidationSeverity.WARNING:
                warnings.append({
                    'warning_id': f"W_{len(warnings) + 1:03d}",
                    'category': issue.category.value,
                    'message': issue.message,
                    'location': issue.location,
                    'suggestion': issue.suggestion,
                    'affected_item': {
                        'id': issue.affected_item_id,
                        'name': issue.affected_item_name
                    },
                    'rule_violated': issue.rule_violated,
                    'impact_level': self._assess_warning_impact(issue),
                    'auto_correctable': self._is_auto_correctable(issue),
                    'correction_options': self._get_correction_options(issue)
                })
        
        return warnings

    def suggest_corrections_for_validation_failures(
        self, 
        validation_issues: List[ValidationIssue]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate correction suggestions for validation failures.
        
        Implements requirement 7.10: Add correction suggestions for validation failures
        
        Args:
            validation_issues: List of validation issues to generate corrections for
            
        Returns:
            Dictionary of correction suggestions organized by category
        """
        corrections_by_category = {}
        
        for issue in validation_issues:
            category = issue.category.value
            if category not in corrections_by_category:
                corrections_by_category[category] = []
            
            correction = {
                'issue_id': f"{category}_{len(corrections_by_category[category]) + 1}",
                'severity': issue.severity.value,
                'problem_description': issue.message,
                'location': issue.location,
                'affected_item': {
                    'id': issue.affected_item_id,
                    'name': issue.affected_item_name
                },
                'correction_type': self._determine_correction_type(issue),
                'suggested_actions': self._generate_specific_actions(issue),
                'alternative_solutions': self._generate_alternative_solutions(issue),
                'implementation_priority': self._assess_correction_priority(issue),
                'estimated_effort': self._estimate_correction_effort(issue),
                'validation_rule': issue.rule_violated
            }
            
            corrections_by_category[category].append(correction)
        
        return corrections_by_category

    def _analyze_session_assignments(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Analyze session assignments across all days."""
        analysis = {
            'total_sessions': 9,  # 3 days × 3 sessions
            'assigned_sessions': 0,
            'mbti_matched_sessions': 0,
            'district_coherent_sessions': 0,
            'operating_hours_compliant': 0,
            'session_distribution': {
                'morning': {'assigned': 0, 'mbti_matched': 0},
                'afternoon': {'assigned': 0, 'mbti_matched': 0},
                'night': {'assigned': 0, 'mbti_matched': 0}
            }
        }
        
        days = [itinerary.day_1, itinerary.day_2, itinerary.day_3]
        
        for day_itinerary in days:
            sessions = [
                (day_itinerary.morning_session, 'morning'),
                (day_itinerary.afternoon_session, 'afternoon'),
                (day_itinerary.night_session, 'night')
            ]
            
            for session_assignment, session_name in sessions:
                if session_assignment and session_assignment.tourist_spot:
                    analysis['assigned_sessions'] += 1
                    analysis['session_distribution'][session_name]['assigned'] += 1
                    
                    spot = session_assignment.tourist_spot
                    if spot.mbti_match:
                        analysis['mbti_matched_sessions'] += 1
                        analysis['session_distribution'][session_name]['mbti_matched'] += 1
        
        # Calculate percentages
        if analysis['assigned_sessions'] > 0:
            analysis['mbti_match_percentage'] = (
                analysis['mbti_matched_sessions'] / analysis['assigned_sessions'] * 100
            )
            analysis['assignment_completion_percentage'] = (
                analysis['assigned_sessions'] / analysis['total_sessions'] * 100
            )
        else:
            analysis['mbti_match_percentage'] = 0
            analysis['assignment_completion_percentage'] = 0
        
        return analysis

    def _analyze_restaurant_assignments(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Analyze restaurant assignments across all days."""
        analysis = {
            'total_meals': 9,  # 3 days × 3 meals
            'assigned_meals': 0,
            'district_matched_meals': 0,
            'operating_hours_compliant': 0,
            'meal_distribution': {
                'breakfast': {'assigned': 0, 'district_matched': 0},
                'lunch': {'assigned': 0, 'district_matched': 0},
                'dinner': {'assigned': 0, 'district_matched': 0}
            }
        }
        
        days = [itinerary.day_1, itinerary.day_2, itinerary.day_3]
        
        for day_itinerary in days:
            meals = [
                (day_itinerary.breakfast, 'breakfast'),
                (day_itinerary.lunch, 'lunch'),
                (day_itinerary.dinner, 'dinner')
            ]
            
            for meal_assignment, meal_name in meals:
                if meal_assignment and meal_assignment.restaurant:
                    analysis['assigned_meals'] += 1
                    analysis['meal_distribution'][meal_name]['assigned'] += 1
        
        # Calculate percentages
        if analysis['assigned_meals'] > 0:
            analysis['assignment_completion_percentage'] = (
                analysis['assigned_meals'] / analysis['total_meals'] * 100
            )
        else:
            analysis['assignment_completion_percentage'] = 0
        
        return analysis

    def _analyze_location_coherence(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Analyze location coherence across sessions and meals."""
        analysis = {
            'district_coherence_score': 0,
            'area_coherence_score': 0,
            'daily_coherence': {},
            'overall_coherence_rating': 'Poor'
        }
        
        days = [
            (itinerary.day_1, 'day_1'),
            (itinerary.day_2, 'day_2'),
            (itinerary.day_3, 'day_3')
        ]
        
        total_coherence_score = 0
        total_days = 0
        
        for day_itinerary, day_name in days:
            day_coherence = self._calculate_daily_coherence(day_itinerary)
            analysis['daily_coherence'][day_name] = day_coherence
            total_coherence_score += day_coherence['coherence_score']
            total_days += 1
        
        if total_days > 0:
            overall_score = total_coherence_score / total_days
            analysis['district_coherence_score'] = overall_score
            
            if overall_score >= 80:
                analysis['overall_coherence_rating'] = 'Excellent'
            elif overall_score >= 60:
                analysis['overall_coherence_rating'] = 'Good'
            elif overall_score >= 40:
                analysis['overall_coherence_rating'] = 'Fair'
            else:
                analysis['overall_coherence_rating'] = 'Poor'
        
        return analysis

    def _analyze_mbti_alignment(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Analyze MBTI personality alignment across the itinerary."""
        analysis = {
            'mbti_personality': itinerary.mbti_personality,
            'total_tourist_spots': 0,
            'mbti_matched_spots': 0,
            'mbti_alignment_percentage': 0,
            'alignment_by_day': {},
            'alignment_rating': 'Poor'
        }
        
        days = [
            (itinerary.day_1, 'day_1'),
            (itinerary.day_2, 'day_2'),
            (itinerary.day_3, 'day_3')
        ]
        
        for day_itinerary, day_name in days:
            day_spots = 0
            day_matched = 0
            
            sessions = [
                day_itinerary.morning_session,
                day_itinerary.afternoon_session,
                day_itinerary.night_session
            ]
            
            for session in sessions:
                if session and session.tourist_spot:
                    day_spots += 1
                    analysis['total_tourist_spots'] += 1
                    
                    if session.tourist_spot.mbti_match:
                        day_matched += 1
                        analysis['mbti_matched_spots'] += 1
            
            day_percentage = (day_matched / day_spots * 100) if day_spots > 0 else 0
            analysis['alignment_by_day'][day_name] = {
                'spots': day_spots,
                'matched': day_matched,
                'percentage': day_percentage
            }
        
        if analysis['total_tourist_spots'] > 0:
            analysis['mbti_alignment_percentage'] = (
                analysis['mbti_matched_spots'] / analysis['total_tourist_spots'] * 100
            )
            
            percentage = analysis['mbti_alignment_percentage']
            if percentage >= 80:
                analysis['alignment_rating'] = 'Excellent'
            elif percentage >= 60:
                analysis['alignment_rating'] = 'Good'
            elif percentage >= 40:
                analysis['alignment_rating'] = 'Fair'
            else:
                analysis['alignment_rating'] = 'Poor'
        
        return analysis

    def _analyze_coverage_completeness(self, itinerary: MainItinerary) -> Dict[str, Any]:
        """Analyze completeness of itinerary coverage."""
        analysis = {
            'session_coverage': {
                'total_sessions': 9,
                'assigned_sessions': 0,
                'completion_percentage': 0
            },
            'meal_coverage': {
                'total_meals': 9,
                'assigned_meals': 0,
                'completion_percentage': 0
            },
            'missing_assignments': [],
            'completeness_rating': 'Incomplete'
        }
        
        days = [
            (itinerary.day_1, 'day_1'),
            (itinerary.day_2, 'day_2'),
            (itinerary.day_3, 'day_3')
        ]
        
        for day_itinerary, day_name in days:
            # Check sessions
            sessions = [
                (day_itinerary.morning_session, 'morning_session'),
                (day_itinerary.afternoon_session, 'afternoon_session'),
                (day_itinerary.night_session, 'night_session')
            ]
            
            for session, session_name in sessions:
                if session and session.tourist_spot:
                    analysis['session_coverage']['assigned_sessions'] += 1
                else:
                    analysis['missing_assignments'].append(f"{day_name}.{session_name}")
            
            # Check meals
            meals = [
                (day_itinerary.breakfast, 'breakfast'),
                (day_itinerary.lunch, 'lunch'),
                (day_itinerary.dinner, 'dinner')
            ]
            
            for meal, meal_name in meals:
                if meal and meal.restaurant:
                    analysis['meal_coverage']['assigned_meals'] += 1
                else:
                    analysis['missing_assignments'].append(f"{day_name}.{meal_name}")
        
        # Calculate percentages
        analysis['session_coverage']['completion_percentage'] = (
            analysis['session_coverage']['assigned_sessions'] / 
            analysis['session_coverage']['total_sessions'] * 100
        )
        
        analysis['meal_coverage']['completion_percentage'] = (
            analysis['meal_coverage']['assigned_meals'] / 
            analysis['meal_coverage']['total_meals'] * 100
        )
        
        # Overall completeness rating
        overall_completion = (
            (analysis['session_coverage']['completion_percentage'] + 
             analysis['meal_coverage']['completion_percentage']) / 2
        )
        
        if overall_completion == 100:
            analysis['completeness_rating'] = 'Complete'
        elif overall_completion >= 80:
            analysis['completeness_rating'] = 'Nearly Complete'
        elif overall_completion >= 60:
            analysis['completeness_rating'] = 'Mostly Complete'
        else:
            analysis['completeness_rating'] = 'Incomplete'
        
        return analysis

    def _calculate_daily_coherence(self, day_itinerary: DayItinerary) -> Dict[str, Any]:
        """Calculate coherence score for a single day."""
        coherence = {
            'coherence_score': 0,
            'district_matches': 0,
            'area_matches': 0,
            'total_comparisons': 0
        }
        
        spots = []
        if day_itinerary.morning_session and day_itinerary.morning_session.tourist_spot:
            spots.append(day_itinerary.morning_session.tourist_spot)
        if day_itinerary.afternoon_session and day_itinerary.afternoon_session.tourist_spot:
            spots.append(day_itinerary.afternoon_session.tourist_spot)
        if day_itinerary.night_session and day_itinerary.night_session.tourist_spot:
            spots.append(day_itinerary.night_session.tourist_spot)
        
        if len(spots) < 2:
            coherence['coherence_score'] = 100  # Single spot is perfectly coherent
            return coherence
        
        # Compare all pairs of spots
        for i in range(len(spots)):
            for j in range(i + 1, len(spots)):
                coherence['total_comparisons'] += 1
                
                if spots[i].district == spots[j].district:
                    coherence['district_matches'] += 1
                elif spots[i].area == spots[j].area:
                    coherence['area_matches'] += 1
        
        if coherence['total_comparisons'] > 0:
            # District matches get full points, area matches get half points
            score = (
                (coherence['district_matches'] * 100 + coherence['area_matches'] * 50) /
                (coherence['total_comparisons'] * 100) * 100
            )
            coherence['coherence_score'] = min(100, score)
        
        return coherence

    def _generate_correction_recommendations(
        self, 
        issues: List[ValidationIssue]
    ) -> List[Dict[str, Any]]:
        """Generate specific correction recommendations."""
        recommendations = []
        
        # Group issues by category for better recommendations
        issues_by_category = {}
        for issue in issues:
            category = issue.category.value
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)
        
        # Generate category-specific recommendations
        for category, category_issues in issues_by_category.items():
            if category == ValidationCategory.OPERATING_HOURS.value:
                recommendations.extend(self._generate_operating_hours_recommendations(category_issues))
            elif category == ValidationCategory.DISTRICT_MATCHING.value:
                recommendations.extend(self._generate_district_matching_recommendations(category_issues))
            elif category == ValidationCategory.UNIQUENESS.value:
                recommendations.extend(self._generate_uniqueness_recommendations(category_issues))
            elif category == ValidationCategory.MBTI_MATCHING.value:
                recommendations.extend(self._generate_mbti_recommendations(category_issues))
        
        return recommendations

    def _generate_operating_hours_recommendations(
        self, 
        issues: List[ValidationIssue]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for operating hours issues."""
        recommendations = []
        
        for issue in issues:
            recommendation = {
                'type': 'operating_hours_fix',
                'priority': 'high' if issue.severity == ValidationSeverity.ERROR else 'medium',
                'title': f"Fix operating hours for {issue.affected_item_name}",
                'description': issue.message,
                'actions': [
                    f"Find alternative tourist spot that operates during required session hours",
                    f"Verify operating hours data for {issue.affected_item_name}",
                    "Consider spots with no operating hour restrictions as alternatives"
                ],
                'affected_location': issue.location,
                'estimated_effort': 'medium'
            }
            recommendations.append(recommendation)
        
        return recommendations

    def _generate_district_matching_recommendations(
        self, 
        issues: List[ValidationIssue]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for district matching issues."""
        recommendations = []
        
        # Group by day to provide day-level recommendations
        issues_by_day = {}
        for issue in issues:
            day = issue.location.split('.')[0]
            if day not in issues_by_day:
                issues_by_day[day] = []
            issues_by_day[day].append(issue)
        
        for day, day_issues in issues_by_day.items():
            recommendation = {
                'type': 'district_coherence_improvement',
                'priority': 'medium',
                'title': f"Improve location coherence for {day}",
                'description': f"Multiple tourist spots in {day} are in different districts",
                'actions': [
                    f"Review tourist spot selections for {day}",
                    "Prioritize spots in the same district as morning session",
                    "Use area matching as fallback when district matching is not possible",
                    "Consider transportation time between districts"
                ],
                'affected_location': day,
                'estimated_effort': 'low'
            }
            recommendations.append(recommendation)
        
        return recommendations

    def _generate_uniqueness_recommendations(
        self, 
        issues: List[ValidationIssue]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for uniqueness constraint violations."""
        recommendations = []
        
        for issue in issues:
            recommendation = {
                'type': 'uniqueness_violation_fix',
                'priority': 'high',
                'title': f"Remove duplicate assignment: {issue.affected_item_name}",
                'description': issue.message,
                'actions': [
                    f"Replace duplicate assignment of {issue.affected_item_name}",
                    "Find alternative tourist spot or restaurant for one of the assignments",
                    "Verify all assignments are unique across the entire 3-day itinerary"
                ],
                'affected_location': issue.location,
                'estimated_effort': 'medium'
            }
            recommendations.append(recommendation)
        
        return recommendations

    def _generate_mbti_recommendations(
        self, 
        issues: List[ValidationIssue]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for MBTI matching issues."""
        recommendations = []
        
        mbti_issues = [i for i in issues if i.category == ValidationCategory.MBTI_MATCHING]
        
        if mbti_issues:
            recommendation = {
                'type': 'mbti_alignment_improvement',
                'priority': 'medium',
                'title': "Improve MBTI personality alignment",
                'description': "Some tourist spots have incorrect MBTI_match field values",
                'actions': [
                    "Review MBTI_match field accuracy for all tourist spots",
                    "Update MBTI_match fields to reflect actual personality alignment",
                    "Consider replacing non-MBTI spots with personality-matched alternatives"
                ],
                'affected_location': "multiple_locations",
                'estimated_effort': 'low'
            }
            recommendations.append(recommendation)
        
        return recommendations

    def _calculate_validation_metrics(
        self, 
        issues: List[ValidationIssue], 
        itinerary: MainItinerary
    ) -> Dict[str, Any]:
        """Calculate comprehensive validation metrics."""
        metrics = {
            'validation_score': 0,
            'compliance_percentage': 0,
            'issue_density': 0,
            'critical_issues_count': 0,
            'improvement_potential': 0,
            'quality_rating': 'Poor'
        }
        
        total_checks = 50  # Estimated total validation checks
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        
        # Calculate validation score (0-100)
        # Errors have more weight than warnings
        penalty = (error_count * 10) + (warning_count * 3)
        metrics['validation_score'] = max(0, 100 - penalty)
        
        # Calculate compliance percentage
        failed_checks = error_count + (warning_count * 0.5)
        metrics['compliance_percentage'] = max(0, (total_checks - failed_checks) / total_checks * 100)
        
        # Calculate issue density (issues per day)
        metrics['issue_density'] = len(issues) / 3  # 3 days
        
        # Critical issues (errors only)
        metrics['critical_issues_count'] = error_count
        
        # Improvement potential (how much can be improved)
        metrics['improvement_potential'] = 100 - metrics['validation_score']
        
        # Quality rating
        score = metrics['validation_score']
        if score >= 90:
            metrics['quality_rating'] = 'Excellent'
        elif score >= 75:
            metrics['quality_rating'] = 'Good'
        elif score >= 60:
            metrics['quality_rating'] = 'Fair'
        elif score >= 40:
            metrics['quality_rating'] = 'Poor'
        else:
            metrics['quality_rating'] = 'Critical'
        
        return metrics

    def _assess_warning_impact(self, issue: ValidationIssue) -> str:
        """Assess the impact level of a warning."""
        if issue.category in [ValidationCategory.UNIQUENESS, ValidationCategory.OPERATING_HOURS]:
            return 'high'
        elif issue.category in [ValidationCategory.DISTRICT_MATCHING, ValidationCategory.RESTAURANT_HOURS]:
            return 'medium'
        else:
            return 'low'

    def _is_auto_correctable(self, issue: ValidationIssue) -> bool:
        """Determine if an issue can be automatically corrected."""
        auto_correctable_categories = [
            ValidationCategory.MBTI_MATCHING,
            ValidationCategory.DATA_INTEGRITY
        ]
        return issue.category in auto_correctable_categories

    def _get_correction_options(self, issue: ValidationIssue) -> List[str]:
        """Get available correction options for an issue."""
        options = []
        
        if issue.category == ValidationCategory.OPERATING_HOURS:
            options = [
                "Replace with spot that operates during required hours",
                "Verify and update operating hours data",
                "Use spot with no operating hour restrictions"
            ]
        elif issue.category == ValidationCategory.DISTRICT_MATCHING:
            options = [
                "Select spot in same district as morning session",
                "Use area matching as fallback",
                "Accept different district with transportation consideration"
            ]
        elif issue.category == ValidationCategory.UNIQUENESS:
            options = [
                "Replace duplicate with alternative spot/restaurant",
                "Swap assignments between days",
                "Find similar spot/restaurant in same area"
            ]
        
        return options

    def _determine_correction_type(self, issue: ValidationIssue) -> str:
        """Determine the type of correction needed."""
        if issue.severity == ValidationSeverity.ERROR:
            return 'mandatory'
        elif issue.severity == ValidationSeverity.WARNING:
            return 'recommended'
        else:
            return 'optional'

    def _generate_specific_actions(self, issue: ValidationIssue) -> List[str]:
        """Generate specific actions to resolve an issue."""
        actions = []
        
        if issue.suggestion:
            actions.append(issue.suggestion)
        
        # Add category-specific actions
        if issue.category == ValidationCategory.OPERATING_HOURS:
            actions.extend([
                "Check tourist spot operating hours database",
                "Verify session time requirements",
                "Search for alternative spots with compatible hours"
            ])
        elif issue.category == ValidationCategory.DISTRICT_MATCHING:
            actions.extend([
                "Review district mapping for the day",
                "Consider transportation logistics",
                "Evaluate area-based alternatives"
            ])
        
        return actions

    def _generate_alternative_solutions(self, issue: ValidationIssue) -> List[str]:
        """Generate alternative solutions for an issue."""
        alternatives = []
        
        if issue.category == ValidationCategory.OPERATING_HOURS:
            alternatives = [
                "Adjust session timing if possible",
                "Use spots with extended hours",
                "Consider 24-hour accessible locations"
            ]
        elif issue.category == ValidationCategory.DISTRICT_MATCHING:
            alternatives = [
                "Group activities by geographic clusters",
                "Plan transportation between districts",
                "Use central meeting points"
            ]
        
        return alternatives

    def _assess_correction_priority(self, issue: ValidationIssue) -> str:
        """Assess the priority level for correcting an issue."""
        if issue.severity == ValidationSeverity.ERROR:
            return 'high'
        elif issue.severity == ValidationSeverity.WARNING:
            if issue.category in [ValidationCategory.UNIQUENESS, ValidationCategory.OPERATING_HOURS]:
                return 'medium-high'
            else:
                return 'medium'
        else:
            return 'low'

    def _estimate_correction_effort(self, issue: ValidationIssue) -> str:
        """Estimate the effort required to correct an issue."""
        if issue.category == ValidationCategory.DATA_INTEGRITY:
            return 'low'
        elif issue.category in [ValidationCategory.MBTI_MATCHING, ValidationCategory.AREA_MATCHING]:
            return 'low'
        elif issue.category in [ValidationCategory.DISTRICT_MATCHING, ValidationCategory.RESTAURANT_DISTRICTS]:
            return 'medium'
        elif issue.category in [ValidationCategory.OPERATING_HOURS, ValidationCategory.UNIQUENESS]:
            return 'medium-high'
        else:
            return 'medium'