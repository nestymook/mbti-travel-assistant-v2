"""Itinerary structure models for MBTI Travel Assistant.

This module contains dataclass models for 3-day itinerary structure,
including day itineraries, main itinerary, and candidate lists.
Follows PEP8 style guidelines and supports BedrockAgentCore runtime patterns.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

from .tourist_spot_models import TouristSpot
from .restaurant_models import Restaurant


@dataclass
class SessionAssignment:
    """Individual session assignment within a day.
    
    Attributes:
        session_type: Type of session (morning, afternoon, night)
        tourist_spot: Assigned tourist spot for this session
        start_time: Suggested start time for the session
        end_time: Suggested end time for the session
        notes: Additional notes about the session
    """
    session_type: str
    tourist_spot: Optional[TouristSpot] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionAssignment':
        """Create SessionAssignment from dictionary data.
        
        Args:
            data: Dictionary containing session assignment data
            
        Returns:
            SessionAssignment instance
        """
        tourist_spot = None
        if data.get('tourist_spot'):
            tourist_spot = TouristSpot.from_dict(data['tourist_spot'])
        
        return cls(
            session_type=data.get('session_type', ''),
            tourist_spot=tourist_spot,
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            notes=data.get('notes')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of session assignment
        """
        result = {
            'session_type': self.session_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'notes': self.notes
        }
        
        if self.tourist_spot:
            result['tourist_spot'] = self.tourist_spot.to_dict()
        
        return result

    def validate(self) -> List[str]:
        """Validate session assignment data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate session_type
        valid_session_types = ['morning', 'afternoon', 'night']
        if not isinstance(self.session_type, str):
            errors.append("session_type must be a string")
        elif self.session_type.lower() not in valid_session_types:
            errors.append(
                f"session_type must be one of: {', '.join(valid_session_types)}"
            )
        
        # Validate tourist_spot if present
        if self.tourist_spot and not isinstance(self.tourist_spot, TouristSpot):
            errors.append("tourist_spot must be a TouristSpot object")
        elif self.tourist_spot:
            spot_errors = self.tourist_spot.validate()
            errors.extend([f"tourist_spot.{error}" for error in spot_errors])
        
        # Validate time format if provided
        time_pattern = r'^\d{2}:\d{2}$'
        import re
        
        if self.start_time and not re.match(time_pattern, self.start_time):
            errors.append("start_time must be in HH:MM format")
        
        if self.end_time and not re.match(time_pattern, self.end_time):
            errors.append("end_time must be in HH:MM format")
        
        return errors


@dataclass
class MealAssignment:
    """Individual meal assignment within a day.
    
    Attributes:
        meal_type: Type of meal (breakfast, lunch, dinner)
        restaurant: Assigned restaurant for this meal
        meal_time: Suggested meal time
        notes: Additional notes about the meal
    """
    meal_type: str
    restaurant: Optional[Restaurant] = None
    meal_time: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MealAssignment':
        """Create MealAssignment from dictionary data.
        
        Args:
            data: Dictionary containing meal assignment data
            
        Returns:
            MealAssignment instance
        """
        restaurant = None
        if data.get('restaurant'):
            restaurant = Restaurant.from_dict(data['restaurant'])
        
        return cls(
            meal_type=data.get('meal_type', ''),
            restaurant=restaurant,
            meal_time=data.get('meal_time'),
            notes=data.get('notes')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of meal assignment
        """
        result = {
            'meal_type': self.meal_type,
            'meal_time': self.meal_time,
            'notes': self.notes
        }
        
        if self.restaurant:
            result['restaurant'] = self.restaurant.to_dict()
        
        return result

    def validate(self) -> List[str]:
        """Validate meal assignment data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate meal_type
        valid_meal_types = ['breakfast', 'lunch', 'dinner']
        if not isinstance(self.meal_type, str):
            errors.append("meal_type must be a string")
        elif self.meal_type.lower() not in valid_meal_types:
            errors.append(
                f"meal_type must be one of: {', '.join(valid_meal_types)}"
            )
        
        # Validate restaurant if present
        if self.restaurant and not isinstance(self.restaurant, Restaurant):
            errors.append("restaurant must be a Restaurant object")
        elif self.restaurant:
            restaurant_errors = self.restaurant.validate()
            errors.extend([f"restaurant.{error}" for error in restaurant_errors])
        
        # Validate meal_time format if provided
        time_pattern = r'^\d{2}:\d{2}$'
        import re
        
        if self.meal_time and not re.match(time_pattern, self.meal_time):
            errors.append("meal_time must be in HH:MM format")
        
        return errors


@dataclass
class DayItinerary:
    """Single day itinerary structure with sessions and meals.
    
    Attributes:
        day_number: Day number (1, 2, or 3)
        date: Date for this day (optional)
        morning_session: Morning session assignment
        afternoon_session: Afternoon session assignment
        night_session: Night session assignment
        breakfast: Breakfast meal assignment
        lunch: Lunch meal assignment
        dinner: Dinner meal assignment
        daily_notes: Additional notes for the entire day
    """
    day_number: int
    date: Optional[str] = None
    morning_session: Optional[SessionAssignment] = None
    afternoon_session: Optional[SessionAssignment] = None
    night_session: Optional[SessionAssignment] = None
    breakfast: Optional[MealAssignment] = None
    lunch: Optional[MealAssignment] = None
    dinner: Optional[MealAssignment] = None
    daily_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DayItinerary':
        """Create DayItinerary from dictionary data.
        
        Args:
            data: Dictionary containing day itinerary data
            
        Returns:
            DayItinerary instance
        """
        # Parse session assignments
        morning_session = None
        if data.get('morning_session'):
            morning_session = SessionAssignment.from_dict(data['morning_session'])
        
        afternoon_session = None
        if data.get('afternoon_session'):
            afternoon_session = SessionAssignment.from_dict(data['afternoon_session'])
        
        night_session = None
        if data.get('night_session'):
            night_session = SessionAssignment.from_dict(data['night_session'])
        
        # Parse meal assignments
        breakfast = None
        if data.get('breakfast'):
            breakfast = MealAssignment.from_dict(data['breakfast'])
        
        lunch = None
        if data.get('lunch'):
            lunch = MealAssignment.from_dict(data['lunch'])
        
        dinner = None
        if data.get('dinner'):
            dinner = MealAssignment.from_dict(data['dinner'])
        
        return cls(
            day_number=data.get('day_number', 1),
            date=data.get('date'),
            morning_session=morning_session,
            afternoon_session=afternoon_session,
            night_session=night_session,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            daily_notes=data.get('daily_notes')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of day itinerary
        """
        result = {
            'day_number': self.day_number,
            'date': self.date,
            'daily_notes': self.daily_notes
        }
        
        # Add session assignments
        if self.morning_session:
            result['morning_session'] = self.morning_session.to_dict()
        
        if self.afternoon_session:
            result['afternoon_session'] = self.afternoon_session.to_dict()
        
        if self.night_session:
            result['night_session'] = self.night_session.to_dict()
        
        # Add meal assignments
        if self.breakfast:
            result['breakfast'] = self.breakfast.to_dict()
        
        if self.lunch:
            result['lunch'] = self.lunch.to_dict()
        
        if self.dinner:
            result['dinner'] = self.dinner.to_dict()
        
        return result

    def validate(self) -> List[str]:
        """Validate day itinerary data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate day_number
        if not isinstance(self.day_number, int):
            errors.append("day_number must be an integer")
        elif self.day_number < 1 or self.day_number > 3:
            errors.append("day_number must be 1, 2, or 3")
        
        # Validate date format if provided
        if self.date:
            if not isinstance(self.date, str):
                errors.append("date must be a string")
            else:
                # Try to parse date to validate format
                try:
                    datetime.fromisoformat(self.date.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("date must be in ISO format (YYYY-MM-DD)")
        
        # Validate session assignments
        sessions = [
            ('morning_session', self.morning_session),
            ('afternoon_session', self.afternoon_session),
            ('night_session', self.night_session)
        ]
        
        for session_name, session in sessions:
            if session and not isinstance(session, SessionAssignment):
                errors.append(f"{session_name} must be a SessionAssignment object")
            elif session:
                session_errors = session.validate()
                errors.extend([f"{session_name}.{error}" for error in session_errors])
        
        # Validate meal assignments
        meals = [
            ('breakfast', self.breakfast),
            ('lunch', self.lunch),
            ('dinner', self.dinner)
        ]
        
        for meal_name, meal in meals:
            if meal and not isinstance(meal, MealAssignment):
                errors.append(f"{meal_name} must be a MealAssignment object")
            elif meal:
                meal_errors = meal.validate()
                errors.extend([f"{meal_name}.{error}" for error in meal_errors])
        
        return errors

    def get_assigned_tourist_spots(self) -> List[TouristSpot]:
        """Get all tourist spots assigned to this day.
        
        Returns:
            List of tourist spots assigned to sessions
        """
        spots = []
        
        sessions = [self.morning_session, self.afternoon_session, self.night_session]
        for session in sessions:
            if session and session.tourist_spot:
                spots.append(session.tourist_spot)
        
        return spots

    def get_assigned_restaurants(self) -> List[Restaurant]:
        """Get all restaurants assigned to this day.
        
        Returns:
            List of restaurants assigned to meals
        """
        restaurants = []
        
        meals = [self.breakfast, self.lunch, self.dinner]
        for meal in meals:
            if meal and meal.restaurant:
                restaurants.append(meal.restaurant)
        
        return restaurants

    def has_complete_assignments(self) -> bool:
        """Check if day has complete session and meal assignments.
        
        Returns:
            True if all sessions and meals are assigned
        """
        sessions_complete = (
            self.morning_session and self.morning_session.tourist_spot and
            self.afternoon_session and self.afternoon_session.tourist_spot and
            self.night_session and self.night_session.tourist_spot
        )
        
        meals_complete = (
            self.breakfast and self.breakfast.restaurant and
            self.lunch and self.lunch.restaurant and
            self.dinner and self.dinner.restaurant
        )
        
        return sessions_complete and meals_complete


@dataclass
class MainItinerary:
    """Complete 3-day itinerary structure.
    
    Attributes:
        mbti_personality: MBTI personality type for this itinerary
        day_1: Day 1 itinerary
        day_2: Day 2 itinerary
        day_3: Day 3 itinerary
        itinerary_notes: Overall notes for the entire itinerary
        created_at: Timestamp when itinerary was created
        version: Version of the itinerary
    """
    mbti_personality: str
    day_1: DayItinerary
    day_2: DayItinerary
    day_3: DayItinerary
    itinerary_notes: Optional[str] = None
    created_at: Optional[str] = None
    version: str = "1.0"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainItinerary':
        """Create MainItinerary from dictionary data.
        
        Args:
            data: Dictionary containing main itinerary data
            
        Returns:
            MainItinerary instance
        """
        return cls(
            mbti_personality=data.get('mbti_personality', ''),
            day_1=DayItinerary.from_dict(data.get('day_1', {})),
            day_2=DayItinerary.from_dict(data.get('day_2', {})),
            day_3=DayItinerary.from_dict(data.get('day_3', {})),
            itinerary_notes=data.get('itinerary_notes'),
            created_at=data.get('created_at'),
            version=data.get('version', '1.0')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of main itinerary
        """
        return {
            'mbti_personality': self.mbti_personality,
            'day_1': self.day_1.to_dict(),
            'day_2': self.day_2.to_dict(),
            'day_3': self.day_3.to_dict(),
            'itinerary_notes': self.itinerary_notes,
            'created_at': self.created_at,
            'version': self.version
        }

    def to_json(self) -> str:
        """Convert main itinerary to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate(self) -> List[str]:
        """Validate main itinerary data.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate MBTI personality
        if not isinstance(self.mbti_personality, str):
            errors.append("mbti_personality must be a string")
        elif len(self.mbti_personality.strip()) != 4:
            errors.append("mbti_personality must be a 4-character MBTI code")
        else:
            valid_mbti_types = {
                'INTJ', 'INTP', 'ENTJ', 'ENTP',
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                'ISTP', 'ISFP', 'ESTP', 'ESFP'
            }
            if self.mbti_personality.upper() not in valid_mbti_types:
                errors.append(f"mbti_personality invalid MBTI type: '{self.mbti_personality}'")
        
        # Validate day itineraries
        days = [
            ('day_1', self.day_1),
            ('day_2', self.day_2),
            ('day_3', self.day_3)
        ]
        
        for day_name, day_itinerary in days:
            if not isinstance(day_itinerary, DayItinerary):
                errors.append(f"{day_name} must be a DayItinerary object")
            else:
                day_errors = day_itinerary.validate()
                errors.extend([f"{day_name}.{error}" for error in day_errors])
        
        # Validate version
        if not isinstance(self.version, str):
            errors.append("version must be a string")
        elif len(self.version.strip()) == 0:
            errors.append("version cannot be empty")
        
        # Validate created_at format if provided
        if self.created_at:
            if not isinstance(self.created_at, str):
                errors.append("created_at must be a string")
            else:
                try:
                    datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("created_at must be in ISO format")
        
        return errors

    def get_all_tourist_spots(self) -> List[TouristSpot]:
        """Get all tourist spots from the entire 3-day itinerary.
        
        Returns:
            List of all assigned tourist spots
        """
        all_spots = []
        
        for day in [self.day_1, self.day_2, self.day_3]:
            all_spots.extend(day.get_assigned_tourist_spots())
        
        return all_spots

    def get_all_restaurants(self) -> List[Restaurant]:
        """Get all restaurants from the entire 3-day itinerary.
        
        Returns:
            List of all assigned restaurants
        """
        all_restaurants = []
        
        for day in [self.day_1, self.day_2, self.day_3]:
            all_restaurants.extend(day.get_assigned_restaurants())
        
        return all_restaurants

    def validate_uniqueness_constraints(self) -> List[str]:
        """Validate that no tourist spots or restaurants are repeated.
        
        Returns:
            List of uniqueness violation errors
        """
        errors = []
        
        # Check tourist spot uniqueness
        all_spots = self.get_all_tourist_spots()
        spot_ids = [spot.id for spot in all_spots if spot.id]
        
        if len(spot_ids) != len(set(spot_ids)):
            duplicate_ids = [spot_id for spot_id in set(spot_ids) if spot_ids.count(spot_id) > 1]
            errors.append(f"Duplicate tourist spots found: {', '.join(duplicate_ids)}")
        
        # Check restaurant uniqueness
        all_restaurants = self.get_all_restaurants()
        restaurant_ids = [restaurant.id for restaurant in all_restaurants if restaurant.id]
        
        if len(restaurant_ids) != len(set(restaurant_ids)):
            duplicate_ids = [rest_id for rest_id in set(restaurant_ids) if restaurant_ids.count(rest_id) > 1]
            errors.append(f"Duplicate restaurants found: {', '.join(duplicate_ids)}")
        
        return errors

    def is_complete(self) -> bool:
        """Check if itinerary has complete assignments for all days.
        
        Returns:
            True if all days have complete assignments
        """
        return (
            self.day_1.has_complete_assignments() and
            self.day_2.has_complete_assignments() and
            self.day_3.has_complete_assignments()
        )


@dataclass
class CandidateLists:
    """Candidate lists for alternative tourist spots and restaurants.
    
    Attributes:
        candidate_tourist_spots: Candidate tourist spots organized by day
        candidate_restaurants: Candidate restaurants organized by day and meal
        generation_metadata: Metadata about candidate generation
    """
    candidate_tourist_spots: Dict[str, List[TouristSpot]]
    candidate_restaurants: Dict[str, Dict[str, List[Restaurant]]]
    generation_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.generation_metadata is None:
            self.generation_metadata = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CandidateLists':
        """Create CandidateLists from dictionary data.
        
        Args:
            data: Dictionary containing candidate lists data
            
        Returns:
            CandidateLists instance
        """
        # Parse candidate tourist spots
        candidate_tourist_spots = {}
        tourist_spots_data = data.get('candidate_tourist_spots', {})
        
        for day, spots_list in tourist_spots_data.items():
            candidate_tourist_spots[day] = [
                TouristSpot.from_dict(spot_data) for spot_data in spots_list
            ]
        
        # Parse candidate restaurants
        candidate_restaurants = {}
        restaurants_data = data.get('candidate_restaurants', {})
        
        for day, meals_dict in restaurants_data.items():
            candidate_restaurants[day] = {}
            for meal, restaurants_list in meals_dict.items():
                candidate_restaurants[day][meal] = [
                    Restaurant.from_dict(restaurant_data) for restaurant_data in restaurants_list
                ]
        
        return cls(
            candidate_tourist_spots=candidate_tourist_spots,
            candidate_restaurants=candidate_restaurants,
            generation_metadata=data.get('generation_metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization.
        
        Returns:
            Dictionary representation of candidate lists
        """
        # Convert tourist spots
        tourist_spots_dict = {}
        for day, spots_list in self.candidate_tourist_spots.items():
            tourist_spots_dict[day] = [spot.to_dict() for spot in spots_list]
        
        # Convert restaurants
        restaurants_dict = {}
        for day, meals_dict in self.candidate_restaurants.items():
            restaurants_dict[day] = {}
            for meal, restaurants_list in meals_dict.items():
                restaurants_dict[day][meal] = [restaurant.to_dict() for restaurant in restaurants_list]
        
        return {
            'candidate_tourist_spots': tourist_spots_dict,
            'candidate_restaurants': restaurants_dict,
            'generation_metadata': self.generation_metadata
        }

    def to_json(self) -> str:
        """Convert candidate lists to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate(self) -> List[str]:
        """Validate candidate lists data structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate candidate_tourist_spots structure
        if not isinstance(self.candidate_tourist_spots, dict):
            errors.append("candidate_tourist_spots must be a dictionary")
        else:
            valid_days = ['day_1', 'day_2', 'day_3']
            for day, spots_list in self.candidate_tourist_spots.items():
                if day not in valid_days:
                    errors.append(f"candidate_tourist_spots invalid day key: '{day}'")
                
                if not isinstance(spots_list, list):
                    errors.append(f"candidate_tourist_spots['{day}'] must be a list")
                else:
                    for i, spot in enumerate(spots_list):
                        if not isinstance(spot, TouristSpot):
                            errors.append(f"candidate_tourist_spots['{day}'][{i}] must be a TouristSpot object")
        
        # Validate candidate_restaurants structure
        if not isinstance(self.candidate_restaurants, dict):
            errors.append("candidate_restaurants must be a dictionary")
        else:
            valid_days = ['day_1', 'day_2', 'day_3']
            valid_meals = ['breakfast', 'lunch', 'dinner']
            
            for day, meals_dict in self.candidate_restaurants.items():
                if day not in valid_days:
                    errors.append(f"candidate_restaurants invalid day key: '{day}'")
                
                if not isinstance(meals_dict, dict):
                    errors.append(f"candidate_restaurants['{day}'] must be a dictionary")
                else:
                    for meal, restaurants_list in meals_dict.items():
                        if meal not in valid_meals:
                            errors.append(f"candidate_restaurants['{day}'] invalid meal key: '{meal}'")
                        
                        if not isinstance(restaurants_list, list):
                            errors.append(f"candidate_restaurants['{day}']['{meal}'] must be a list")
                        else:
                            for i, restaurant in enumerate(restaurants_list):
                                if not isinstance(restaurant, Restaurant):
                                    errors.append(
                                        f"candidate_restaurants['{day}']['{meal}'][{i}] "
                                        "must be a Restaurant object"
                                    )
        
        # Validate generation_metadata
        if not isinstance(self.generation_metadata, dict):
            errors.append("generation_metadata must be a dictionary")
        
        return errors

    def add_tourist_spot_candidate(self, day: str, tourist_spot: TouristSpot) -> None:
        """Add tourist spot candidate for a specific day.
        
        Args:
            day: Day identifier (day_1, day_2, day_3)
            tourist_spot: TouristSpot to add as candidate
        """
        if day not in self.candidate_tourist_spots:
            self.candidate_tourist_spots[day] = []
        
        # Avoid duplicates
        existing_ids = [spot.id for spot in self.candidate_tourist_spots[day]]
        if tourist_spot.id not in existing_ids:
            self.candidate_tourist_spots[day].append(tourist_spot)

    def add_restaurant_candidate(self, day: str, meal: str, restaurant: Restaurant) -> None:
        """Add restaurant candidate for a specific day and meal.
        
        Args:
            day: Day identifier (day_1, day_2, day_3)
            meal: Meal identifier (breakfast, lunch, dinner)
            restaurant: Restaurant to add as candidate
        """
        if day not in self.candidate_restaurants:
            self.candidate_restaurants[day] = {}
        
        if meal not in self.candidate_restaurants[day]:
            self.candidate_restaurants[day][meal] = []
        
        # Avoid duplicates
        existing_ids = [rest.id for rest in self.candidate_restaurants[day][meal]]
        if restaurant.id not in existing_ids:
            self.candidate_restaurants[day][meal].append(restaurant)

    def get_total_candidate_count(self) -> Dict[str, int]:
        """Get total count of candidates by type.
        
        Returns:
            Dictionary with counts for tourist_spots and restaurants
        """
        tourist_spots_count = sum(
            len(spots_list) for spots_list in self.candidate_tourist_spots.values()
        )
        
        restaurants_count = sum(
            len(restaurants_list)
            for meals_dict in self.candidate_restaurants.values()
            for restaurants_list in meals_dict.values()
        )
        
        return {
            'tourist_spots': tourist_spots_count,
            'restaurants': restaurants_count
        }