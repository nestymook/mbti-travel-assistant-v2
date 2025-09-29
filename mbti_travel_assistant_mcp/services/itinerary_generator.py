"""Itinerary generator orchestrator for MBTI Travel Assistant.

This module implements the main itinerary generation logic that orchestrates
the complete 3-day itinerary creation process. It coordinates session assignments,
restaurant assignments, candidate list generation, and validation.
Follows PEP8 style guidelines and implements requirements 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.9, 4.10, 7.6.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass

from ..models.tourist_spot_models import TouristSpot, SessionType
from ..models.restaurant_models import Restaurant
from ..models.itinerary_models import (
    MainItinerary, DayItinerary, SessionAssignment, MealAssignment, CandidateLists
)
from ..models.mbti_request_response_models import ItineraryResponse, ItineraryMetadata
from .session_assignment_logic import SessionAssignmentLogic, AssignmentResult
from .mcp_client_manager import MCPClientManager
from .assignment_validator import AssignmentValidator, ValidationReport
from .nova_pro_knowledge_base_client import NovaProKnowledgeBaseClient
from .error_handler import ErrorHandler, SystemErrorType
from .performance_monitor import performance_monitor, MetricType
from .system_resilience import SystemResilienceService, DegradationConfig, CacheConfig
from .comprehensive_error_monitor import ComprehensiveErrorMonitor, MonitoringConfig


@dataclass
class ItineraryGenerationContext:
    """Context information for itinerary generation.
    
    Attributes:
        mbti_personality: MBTI personality type for matching
        start_date: Optional start date for the itinerary
        user_preferences: Optional user preferences
        generation_id: Unique identifier for this generation request
        request_timestamp: When the generation was requested
    """
    mbti_personality: str
    start_date: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    generation_id: Optional[str] = None
    request_timestamp: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if not self.generation_id:
            self.generation_id = f"itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not self.request_timestamp:
            self.request_timestamp = datetime.now().isoformat()


@dataclass
class ItineraryGenerationResult:
    """Result of itinerary generation process.
    
    Attributes:
        main_itinerary: Generated 3-day itinerary
        candidate_lists: Alternative options for tourist spots and restaurants
        validation_report: Validation results for the generated itinerary
        generation_metadata: Metadata about the generation process
        processing_time_ms: Total processing time in milliseconds
        success: Whether generation was successful
        error_details: Error details if generation failed
    """
    main_itinerary: Optional[MainItinerary] = None
    candidate_lists: Optional[CandidateLists] = None
    validation_report: Optional[ValidationReport] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: float = 0.0
    success: bool = False
    error_details: Optional[Dict[str, Any]] = None


class ItineraryGenerator:
    """Main itinerary generation orchestrator.
    
    Orchestrates the complete 3-day itinerary generation process:
    1. Retrieves MBTI-matched tourist spots from knowledge base
    2. Generates 3-day session assignments using strict business rules
    3. Assigns restaurants for each meal using MCP clients
    4. Generates candidate lists for alternative options
    5. Validates all assignments against business rules
    6. Handles errors and provides fallback strategies
    
    Implements requirements:
    - 2.1, 2.2, 2.3: 3-day structure generation with session assignments
    - 4.1, 4.2, 4.3: Candidate list generation
    - 4.9, 4.10, 7.6: Validation and error handling
    """

    def __init__(self):
        """Initialize itinerary generator with required services."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize core services
        self.nova_client = NovaProKnowledgeBaseClient()
        self.session_assigner = SessionAssignmentLogic()
        self.mcp_client = MCPClientManager()
        self.validator = AssignmentValidator()
        self.error_handler = ErrorHandler()
        
        # Initialize resilience services
        self.resilience_service = SystemResilienceService(
            degradation_config=DegradationConfig(
                error_threshold=3,
                error_window_minutes=5,
                recovery_threshold=2,
                enable_circuit_breaker=True
            ),
            cache_config=CacheConfig(
                max_size_mb=50,
                default_ttl_seconds=300,
                strategy="hybrid"
            )
        )
        
        self.error_monitor = ComprehensiveErrorMonitor(
            config=MonitoringConfig(
                error_rate_threshold=15.0,
                response_time_threshold_ms=10000.0,
                enable_alerting=True
            )
        )
        
        # Generation statistics
        self.total_generations = 0
        self.successful_generations = 0
        self.failed_generations = 0
        
        self.logger.info("Initialized ItineraryGenerator with all required services and resilience features")
    
    async def start(self):
        """Start the itinerary generator and resilience services."""
        await self.resilience_service.start()
        await self.error_monitor.start()
        self.logger.info("Itinerary generator and resilience services started")
    
    async def stop(self):
        """Stop the itinerary generator and resilience services."""
        await self.resilience_service.stop()
        await self.error_monitor.stop()
        self.logger.info("Itinerary generator and resilience services stopped")

    async def generate_complete_itinerary(
        self, 
        mbti_personality: str,
        start_date: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ItineraryGenerationResult:
        """Generate complete 3-day itinerary with tourist spots and restaurants.
        
        This is the main orchestration method that coordinates all aspects of
        itinerary generation including session assignments, restaurant assignments,
        candidate generation, and validation.
        
        Args:
            mbti_personality: 4-character MBTI code (e.g., "INFJ", "ENFP")
            start_date: Optional start date for the itinerary
            user_preferences: Optional user preferences for customization
            
        Returns:
            ItineraryGenerationResult with complete itinerary and metadata
        """
        start_time = datetime.now()
        
        # Create generation context
        context = ItineraryGenerationContext(
            mbti_personality=mbti_personality.upper(),
            start_date=start_date,
            user_preferences=user_preferences or {}
        )
        
        self.logger.info(
            f"Starting complete itinerary generation for MBTI: {context.mbti_personality}, "
            f"generation_id: {context.generation_id}"
        )
        
        try:
            # Track generation attempt
            self.total_generations += 1
            performance_monitor.record_metric(MetricType.COUNTER, "itinerary_generation_attempts", 1)
            
            # Generate cache key for this request
            cache_key = f"itinerary_{context.mbti_personality}_{start_date or 'no_date'}"
            
            # Step 1: Validate MBTI personality format
            if not self._validate_mbti_format(context.mbti_personality):
                raise ValueError(f"Invalid MBTI personality format: {context.mbti_personality}")
            
            # Step 2: Get MBTI-matched tourist spots from knowledge base with resilience
            self.logger.info(f"Retrieving MBTI-matched tourist spots for {context.mbti_personality}")
            
            async def get_tourist_spots():
                return await self._get_mbti_tourist_spots(context)
            
            async def fallback_tourist_spots():
                self.logger.warning("Using fallback tourist spots due to knowledge base failure")
                return await self._get_fallback_tourist_spots(context)
            
            mbti_query_results = await self.resilience_service.execute_with_resilience(
                service_name="knowledge_base",
                operation=get_tourist_spots,
                fallback_operation=fallback_tourist_spots,
                cache_key=f"tourist_spots_{context.mbti_personality}",
                cache_ttl=600  # 10 minutes
            )
            
            # Extract tourist spots from query results
            mbti_tourist_spots = [result.tourist_spot for result in mbti_query_results] if mbti_query_results else []
            
            if not mbti_tourist_spots:
                self.logger.warning(f"No MBTI-matched tourist spots found for {context.mbti_personality}")
                # Continue with empty list - fallback logic will handle this
            
            # Step 3: Generate main 3-day itinerary structure
            self.logger.info("Generating main 3-day itinerary structure")
            main_itinerary = await self._generate_main_itinerary(context, mbti_tourist_spots)
            
            # Step 4: Assign restaurants for each meal with resilience
            self.logger.info("Assigning restaurants to itinerary")
            
            async def assign_restaurants():
                return await self._assign_restaurants_to_itinerary(main_itinerary)
            
            async def fallback_restaurants():
                self.logger.warning("Using fallback restaurant assignment")
                return await self._assign_fallback_restaurants(main_itinerary)
            
            await self.resilience_service.execute_with_resilience(
                service_name="restaurant_assignment",
                operation=assign_restaurants,
                fallback_operation=fallback_restaurants,
                cache_key=f"restaurants_{context.mbti_personality}_{hash(str(main_itinerary))}",
                cache_ttl=300  # 5 minutes
            )
            
            # Step 5: Generate candidate lists
            self.logger.info("Generating candidate lists")
            candidate_lists = await self._generate_candidate_lists(
                main_itinerary, mbti_tourist_spots, context
            )
            
            # Step 6: Validate complete itinerary
            self.logger.info("Validating complete itinerary")
            validation_report = self.validator.validate_complete_itinerary(main_itinerary)
            
            # Step 7: Handle validation failures if needed
            if not validation_report.is_valid:
                self.logger.warning(
                    f"Validation failed with {validation_report.error_count} errors. "
                    "Attempting corrections."
                )
                await self._handle_validation_failures(main_itinerary, validation_report)
                
                # Re-validate after corrections
                validation_report = self.validator.validate_complete_itinerary(main_itinerary)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Generate metadata
            generation_metadata = self._generate_metadata(
                context, main_itinerary, candidate_lists, validation_report, processing_time_ms
            )
            
            # Track successful generation
            self.successful_generations += 1
            performance_monitor.record_metric(MetricType.COUNTER, "itinerary_generation_success", 1)
            performance_monitor.record_metric(MetricType.HISTOGRAM, "itinerary_generation_time_ms", processing_time_ms)
            
            # Log performance metric
            await self.error_monitor.log_performance_metric(
                service_name="itinerary_generator",
                operation_name="generate_complete_itinerary",
                response_time_ms=processing_time_ms,
                success=True
            )
            
            self.logger.info(
                f"Successfully generated itinerary for {context.mbti_personality} "
                f"in {processing_time_ms:.2f}ms (generation_id: {context.generation_id})"
            )
            
            return ItineraryGenerationResult(
                main_itinerary=main_itinerary,
                candidate_lists=candidate_lists,
                validation_report=validation_report,
                generation_metadata=generation_metadata,
                processing_time_ms=processing_time_ms,
                success=True
            )
            
        except Exception as e:
            # Handle generation failure
            end_time = datetime.now()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            self.failed_generations += 1
            performance_monitor.record_metric(MetricType.COUNTER, "itinerary_generation_failure", 1)
            
            # Log error with comprehensive monitoring
            await self.error_monitor.log_error(
                service_name="itinerary_generator",
                operation_name="generate_complete_itinerary",
                error=e,
                context={
                    "mbti_personality": context.mbti_personality,
                    "start_date": context.start_date,
                    "user_preferences": context.user_preferences
                },
                correlation_id=context.generation_id,
                response_time_ms=processing_time_ms
            )
            
            # Also use existing error handler for response formatting
            error_details = self.error_handler.handle_error(
                e, context.generation_id, {"operation": "itinerary_generation"}
            )
            
            self.logger.error(
                f"Failed to generate itinerary for {context.mbti_personality}: {e} "
                f"(generation_id: {context.generation_id})"
            )
            
            return ItineraryGenerationResult(
                processing_time_ms=processing_time_ms,
                success=False,
                error_details=error_details
            )

    async def _get_mbti_tourist_spots(
        self, 
        context: ItineraryGenerationContext
    ) -> List:
        """Retrieve MBTI-matched tourist spots from knowledge base.
        
        Args:
            context: Generation context with MBTI personality
            
        Returns:
            List of QueryResult objects with MBTI-matched tourist spots
        """
        try:
            query_results = await self.nova_client.query_mbti_tourist_spots(
                context.mbti_personality
            )
            
            self.logger.info(
                f"Retrieved {len(query_results)} MBTI-matched tourist spots "
                f"for {context.mbti_personality}"
            )
            
            return query_results
            
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve MBTI tourist spots for {context.mbti_personality}: {e}"
            )
            # Return empty list to allow fallback logic to handle
            return []

    async def _generate_main_itinerary(
        self,
        context: ItineraryGenerationContext,
        mbti_tourist_spots: List[TouristSpot]
    ) -> MainItinerary:
        """Generate main 3-day itinerary with session assignments.
        
        Implements requirements 2.1, 2.2, 2.3:
        - Creates exactly 3 days with morning/afternoon/night sessions
        - Applies strict session assignment logic
        - Ensures no tourist spot repetition across all sessions
        
        Args:
            context: Generation context
            mbti_tourist_spots: List of MBTI-matched tourist spots
            
        Returns:
            MainItinerary with session assignments
        """
        # Initialize day itineraries
        day_1 = DayItinerary(day_number=1)
        day_2 = DayItinerary(day_number=2)
        day_3 = DayItinerary(day_number=3)
        
        # Set dates if start_date provided
        if context.start_date:
            try:
                start_date = datetime.fromisoformat(context.start_date.replace('Z', '+00:00'))
                day_1.date = start_date.date().isoformat()
                day_2.date = (start_date + timedelta(days=1)).date().isoformat()
                day_3.date = (start_date + timedelta(days=2)).date().isoformat()
            except ValueError:
                self.logger.warning(f"Invalid start_date format: {context.start_date}")
        
        # Track used tourist spots across all days
        used_spots: Set[str] = set()
        
        # Generate session assignments for each day
        days = [(day_1, 1), (day_2, 2), (day_3, 3)]
        
        for day_itinerary, day_number in days:
            self.logger.debug(f"Generating session assignments for day {day_number}")
            
            # Morning session assignment
            morning_result = self.session_assigner.assign_morning_session(
                mbti_tourist_spots, used_spots, context.mbti_personality, day_number
            )
            
            if morning_result.tourist_spot:
                day_itinerary.morning_session = SessionAssignment(
                    session_type="morning",
                    tourist_spot=morning_result.tourist_spot,
                    start_time="09:00",
                    end_time="11:30",
                    notes=morning_result.assignment_notes
                )
                used_spots.add(morning_result.tourist_spot.id)
                
                self.logger.debug(
                    f"Assigned morning session for day {day_number}: "
                    f"{morning_result.tourist_spot.name}"
                )
            
            # Afternoon session assignment
            afternoon_result = self.session_assigner.assign_afternoon_session(
                mbti_tourist_spots,
                used_spots,
                morning_result.tourist_spot,
                context.mbti_personality,
                day_number
            )
            
            if afternoon_result.tourist_spot:
                day_itinerary.afternoon_session = SessionAssignment(
                    session_type="afternoon",
                    tourist_spot=afternoon_result.tourist_spot,
                    start_time="13:00",
                    end_time="16:30",
                    notes=afternoon_result.assignment_notes
                )
                used_spots.add(afternoon_result.tourist_spot.id)
                
                self.logger.debug(
                    f"Assigned afternoon session for day {day_number}: "
                    f"{afternoon_result.tourist_spot.name}"
                )
            
            # Night session assignment
            night_result = self.session_assigner.assign_night_session(
                mbti_tourist_spots,
                used_spots,
                morning_result.tourist_spot,
                afternoon_result.tourist_spot,
                context.mbti_personality,
                day_number
            )
            
            if night_result.tourist_spot:
                day_itinerary.night_session = SessionAssignment(
                    session_type="night",
                    tourist_spot=night_result.tourist_spot,
                    start_time="18:30",
                    end_time="21:00",
                    notes=night_result.assignment_notes
                )
                used_spots.add(night_result.tourist_spot.id)
                
                self.logger.debug(
                    f"Assigned night session for day {day_number}: "
                    f"{night_result.tourist_spot.name}"
                )
        
        # Create main itinerary
        main_itinerary = MainItinerary(
            mbti_personality=context.mbti_personality,
            day_1=day_1,
            day_2=day_2,
            day_3=day_3,
            created_at=context.request_timestamp,
            itinerary_notes=f"3-day itinerary generated for {context.mbti_personality} personality type"
        )
        
        self.logger.info(
            f"Generated main itinerary structure with {len(used_spots)} unique tourist spots"
        )
        
        return main_itinerary

    async def _assign_restaurants_to_itinerary(self, itinerary: MainItinerary) -> None:
        """Assign restaurants for each meal in the itinerary.
        
        Coordinates with MCP client manager to retrieve restaurant data
        and assign appropriate restaurants for breakfast, lunch, and dinner
        based on district matching and operating hours.
        
        Args:
            itinerary: MainItinerary to assign restaurants to
        """
        self.logger.info("Starting restaurant assignment process")
        
        # Track used restaurants across all meals
        used_restaurants: Set[str] = set()
        
        # Process each day
        days = [
            (itinerary.day_1, "day_1"),
            (itinerary.day_2, "day_2"),
            (itinerary.day_3, "day_3")
        ]
        
        for day_itinerary, day_name in days:
            self.logger.debug(f"Assigning restaurants for {day_name}")
            
            # Get districts from tourist spots for this day
            morning_district = None
            afternoon_district = None
            night_district = None
            
            if day_itinerary.morning_session and day_itinerary.morning_session.tourist_spot:
                morning_district = day_itinerary.morning_session.tourist_spot.district
            
            if day_itinerary.afternoon_session and day_itinerary.afternoon_session.tourist_spot:
                afternoon_district = day_itinerary.afternoon_session.tourist_spot.district
            
            if day_itinerary.night_session and day_itinerary.night_session.tourist_spot:
                night_district = day_itinerary.night_session.tourist_spot.district
            
            # Assign breakfast (based on morning district)
            if morning_district:
                breakfast_restaurant = await self._assign_meal_restaurant(
                    "breakfast", morning_district, used_restaurants
                )
                
                if breakfast_restaurant:
                    day_itinerary.breakfast = MealAssignment(
                        meal_type="breakfast",
                        restaurant=breakfast_restaurant,
                        meal_time="08:30",
                        notes=f"Breakfast near {morning_district}"
                    )
                    used_restaurants.add(breakfast_restaurant.id)
            
            # Assign lunch (based on morning or afternoon district)
            lunch_district = afternoon_district or morning_district
            if lunch_district:
                lunch_restaurant = await self._assign_meal_restaurant(
                    "lunch", lunch_district, used_restaurants
                )
                
                if lunch_restaurant:
                    day_itinerary.lunch = MealAssignment(
                        meal_type="lunch",
                        restaurant=lunch_restaurant,
                        meal_time="12:30",
                        notes=f"Lunch near {lunch_district}"
                    )
                    used_restaurants.add(lunch_restaurant.id)
            
            # Assign dinner (based on night, afternoon, or morning district)
            dinner_district = night_district or afternoon_district or morning_district
            if dinner_district:
                dinner_restaurant = await self._assign_meal_restaurant(
                    "dinner", dinner_district, used_restaurants
                )
                
                if dinner_restaurant:
                    day_itinerary.dinner = MealAssignment(
                        meal_type="dinner",
                        restaurant=dinner_restaurant,
                        meal_time="19:30",
                        notes=f"Dinner near {dinner_district}"
                    )
                    used_restaurants.add(dinner_restaurant.id)
        
        self.logger.info(
            f"Completed restaurant assignment with {len(used_restaurants)} unique restaurants"
        )

    async def _assign_meal_restaurant(
        self,
        meal_type: str,
        district: str,
        used_restaurants: Set[str]
    ) -> Optional[Restaurant]:
        """Assign restaurant for a specific meal type and district.
        
        Args:
            meal_type: Type of meal (breakfast, lunch, dinner)
            district: Target district for restaurant search
            used_restaurants: Set of already used restaurant IDs
            
        Returns:
            Restaurant assignment or None if not found
        """
        try:
            # Search for restaurants by meal type and district
            restaurants = await self.mcp_client.search_restaurants(
                district=district,
                meal_type=meal_type
            )
            
            if not restaurants:
                self.logger.warning(
                    f"No {meal_type} restaurants found in {district} district"
                )
                return None
            
            # Filter out already used restaurants
            available_restaurants = [
                restaurant for restaurant in restaurants
                if restaurant.id not in used_restaurants
            ]
            
            if not available_restaurants:
                self.logger.warning(
                    f"No unused {meal_type} restaurants available in {district} district"
                )
                # Return first restaurant as fallback (allowing duplicates if necessary)
                return restaurants[0] if restaurants else None
            
            # Get restaurant recommendations
            try:
                recommendation_result = await self.mcp_client.get_restaurant_recommendations(
                    available_restaurants
                )
                
                if recommendation_result and recommendation_result.get('recommendation'):
                    recommended_restaurant = recommendation_result['recommendation']
                    self.logger.debug(
                        f"Selected recommended {meal_type} restaurant: "
                        f"{recommended_restaurant.name} in {district}"
                    )
                    return recommended_restaurant
                
            except Exception as e:
                self.logger.warning(f"Failed to get restaurant recommendations: {e}")
            
            # Fallback to first available restaurant
            selected_restaurant = available_restaurants[0]
            self.logger.debug(
                f"Selected fallback {meal_type} restaurant: "
                f"{selected_restaurant.name} in {district}"
            )
            return selected_restaurant
            
        except Exception as e:
            self.logger.error(
                f"Failed to assign {meal_type} restaurant in {district}: {e}"
            )
            return None

    def _validate_mbti_format(self, mbti_personality: str) -> bool:
        """Validate MBTI personality format.
        
        Args:
            mbti_personality: MBTI personality string to validate
            
        Returns:
            True if valid MBTI format, False otherwise
        """
        if not mbti_personality or len(mbti_personality) != 4:
            return False
        
        valid_mbti_types = {
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        }
        
        return mbti_personality.upper() in valid_mbti_types

    def _generate_metadata(
        self,
        context: ItineraryGenerationContext,
        main_itinerary: MainItinerary,
        candidate_lists: CandidateLists,
        validation_report: ValidationReport,
        processing_time_ms: float
    ) -> Dict[str, Any]:
        """Generate comprehensive metadata for the itinerary generation.
        
        Args:
            context: Generation context
            main_itinerary: Generated main itinerary
            candidate_lists: Generated candidate lists
            validation_report: Validation results
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Dictionary with generation metadata
        """
        # Count assignments
        total_tourist_spots = len(main_itinerary.get_all_tourist_spots())
        total_restaurants = len(main_itinerary.get_all_restaurants())
        
        # Count candidates
        candidate_counts = candidate_lists.get_total_candidate_count()
        
        # Generation statistics
        generation_stats = {
            'total_generations': self.total_generations,
            'successful_generations': self.successful_generations,
            'failed_generations': self.failed_generations,
            'success_rate': self.successful_generations / self.total_generations if self.total_generations > 0 else 0
        }
        
        return {
            'generation_id': context.generation_id,
            'mbti_personality': context.mbti_personality,
            'generation_timestamp': context.request_timestamp,
            'processing_time_ms': processing_time_ms,
            'total_spots_assigned': total_tourist_spots,
            'total_restaurants_assigned': total_restaurants,
            'candidate_tourist_spots_count': candidate_counts['tourist_spots'],
            'candidate_restaurants_count': candidate_counts['restaurants'],
            'validation_status': 'passed' if validation_report.is_valid else 'failed',
            'validation_errors': validation_report.error_count,
            'validation_warnings': validation_report.warning_count,
            'generation_statistics': generation_stats,
            'itinerary_completeness': main_itinerary.is_complete(),
            'start_date': context.start_date,
            'user_preferences': context.user_preferences
        }

    async def _generate_candidate_lists(
        self,
        main_itinerary: MainItinerary,
        mbti_tourist_spots: List[TouristSpot],
        context: ItineraryGenerationContext
    ) -> CandidateLists:
        """Generate candidate lists for tourist spots and restaurants.
        
        Implements requirements 4.1, 4.2, 4.3:
        - Identifies unassigned tourist spots matching Areas or Locations for each day
        - Creates restaurant candidate lists for each meal
        - Marks MBTI_match for candidate tourist spots
        
        Args:
            main_itinerary: Main itinerary with assigned spots and restaurants
            mbti_tourist_spots: Original list of MBTI-matched tourist spots
            context: Generation context
            
        Returns:
            CandidateLists with alternative options
        """
        self.logger.info("Generating candidate lists for alternative options")
        
        # Initialize candidate lists structure
        candidate_lists = CandidateLists(
            candidate_tourist_spots={
                'day_1': [],
                'day_2': [],
                'day_3': []
            },
            candidate_restaurants={
                'day_1': {'breakfast': [], 'lunch': [], 'dinner': []},
                'day_2': {'breakfast': [], 'lunch': [], 'dinner': []},
                'day_3': {'breakfast': [], 'lunch': [], 'dinner': []}
            }
        )
        
        # Get all assigned tourist spots and restaurants
        assigned_tourist_spots = set(spot.id for spot in main_itinerary.get_all_tourist_spots())
        assigned_restaurants = set(restaurant.id for restaurant in main_itinerary.get_all_restaurants())
        
        # Generate tourist spot candidates for each day
        days = [
            (main_itinerary.day_1, 'day_1'),
            (main_itinerary.day_2, 'day_2'),
            (main_itinerary.day_3, 'day_3')
        ]
        
        for day_itinerary, day_key in days:
            await self._generate_tourist_spot_candidates_for_day(
                day_itinerary, day_key, mbti_tourist_spots, 
                assigned_tourist_spots, candidate_lists, context
            )
        
        # Generate restaurant candidates for each day and meal
        for day_itinerary, day_key in days:
            await self._generate_restaurant_candidates_for_day(
                day_itinerary, day_key, assigned_restaurants, candidate_lists
            )
        
        # Add generation metadata
        candidate_lists.generation_metadata = {
            'generation_id': context.generation_id,
            'mbti_personality': context.mbti_personality,
            'generation_timestamp': datetime.now().isoformat(),
            'total_assigned_spots': len(assigned_tourist_spots),
            'total_assigned_restaurants': len(assigned_restaurants),
            'candidate_generation_method': 'district_area_matching'
        }
        
        total_candidates = candidate_lists.get_total_candidate_count()
        self.logger.info(
            f"Generated candidate lists: {total_candidates['tourist_spots']} tourist spots, "
            f"{total_candidates['restaurants']} restaurants"
        )
        
        return candidate_lists

    async def _generate_tourist_spot_candidates_for_day(
        self,
        day_itinerary: DayItinerary,
        day_key: str,
        mbti_tourist_spots: List[TouristSpot],
        assigned_tourist_spots: Set[str],
        candidate_lists: CandidateLists,
        context: ItineraryGenerationContext
    ) -> None:
        """Generate tourist spot candidates for a specific day.
        
        Args:
            day_itinerary: Day itinerary to generate candidates for
            day_key: Day identifier (day_1, day_2, day_3)
            mbti_tourist_spots: Original MBTI-matched tourist spots
            assigned_tourist_spots: Set of already assigned spot IDs
            candidate_lists: Candidate lists to populate
            context: Generation context
        """
        # Collect districts and areas from assigned spots for this day
        target_districts = set()
        target_areas = set()
        
        sessions = [
            day_itinerary.morning_session,
            day_itinerary.afternoon_session,
            day_itinerary.night_session
        ]
        
        for session in sessions:
            if session and session.tourist_spot:
                if session.tourist_spot.district:
                    target_districts.add(session.tourist_spot.district)
                if session.tourist_spot.area:
                    target_areas.add(session.tourist_spot.area)
        
        # Find MBTI-matched candidates
        mbti_candidates = []
        for spot in mbti_tourist_spots:
            if (spot.id not in assigned_tourist_spots and
                spot.matches_mbti_personality(context.mbti_personality)):
                
                # Check if spot matches target districts or areas
                district_match = any(spot.matches_district(district) for district in target_districts)
                area_match = any(spot.matches_area(area) for area in target_areas)
                
                if district_match or area_match or not target_districts:
                    # Mark MBTI match status
                    spot.set_mbti_match_status(context.mbti_personality)
                    mbti_candidates.append(spot)
        
        # Add MBTI candidates (limit to reasonable number)
        mbti_candidates = mbti_candidates[:10]  # Limit to top 10 MBTI candidates
        for candidate in mbti_candidates:
            candidate_lists.add_tourist_spot_candidate(day_key, candidate)
        
        # Find additional non-MBTI candidates if needed
        if len(mbti_candidates) < 5:  # Add non-MBTI candidates if we have fewer than 5 MBTI ones
            try:
                # Get additional tourist spots from knowledge base
                additional_spots = await self._get_additional_tourist_spots_for_areas(
                    target_districts, target_areas, assigned_tourist_spots
                )
                
                # Add non-MBTI candidates (mark as non-MBTI match)
                non_mbti_candidates = additional_spots[:5]  # Limit to 5 additional
                for candidate in non_mbti_candidates:
                    candidate.mbti_match = False
                    candidate_lists.add_tourist_spot_candidate(day_key, candidate)
                    
            except Exception as e:
                self.logger.warning(f"Failed to get additional tourist spots for {day_key}: {e}")
        
        self.logger.debug(
            f"Generated {len(candidate_lists.candidate_tourist_spots[day_key])} "
            f"tourist spot candidates for {day_key}"
        )

    async def _generate_restaurant_candidates_for_day(
        self,
        day_itinerary: DayItinerary,
        day_key: str,
        assigned_restaurants: Set[str],
        candidate_lists: CandidateLists
    ) -> None:
        """Generate restaurant candidates for a specific day.
        
        Args:
            day_itinerary: Day itinerary to generate candidates for
            day_key: Day identifier (day_1, day_2, day_3)
            assigned_restaurants: Set of already assigned restaurant IDs
            candidate_lists: Candidate lists to populate
        """
        # Get districts from tourist spots for this day
        districts = set()
        
        sessions = [
            day_itinerary.morning_session,
            day_itinerary.afternoon_session,
            day_itinerary.night_session
        ]
        
        for session in sessions:
            if session and session.tourist_spot and session.tourist_spot.district:
                districts.add(session.tourist_spot.district)
        
        if not districts:
            self.logger.warning(f"No districts found for restaurant candidates on {day_key}")
            return
        
        # Generate candidates for each meal type
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            try:
                # Search for restaurants in relevant districts
                meal_candidates = []
                
                for district in districts:
                    try:
                        restaurants = await self.mcp_client.search_restaurants(
                            district=district,
                            meal_type=meal_type
                        )
                        
                        # Filter out assigned restaurants
                        available_restaurants = [
                            restaurant for restaurant in restaurants
                            if restaurant.id not in assigned_restaurants
                        ]
                        
                        meal_candidates.extend(available_restaurants)
                        
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to search {meal_type} restaurants in {district}: {e}"
                        )
                
                # Remove duplicates and limit candidates
                unique_candidates = []
                seen_ids = set()
                
                for restaurant in meal_candidates:
                    if restaurant.id not in seen_ids:
                        unique_candidates.append(restaurant)
                        seen_ids.add(restaurant.id)
                        
                        if len(unique_candidates) >= 5:  # Limit to 5 candidates per meal
                            break
                
                # Add candidates to the list
                for candidate in unique_candidates:
                    candidate_lists.add_restaurant_candidate(day_key, meal_type, candidate)
                
                self.logger.debug(
                    f"Generated {len(unique_candidates)} {meal_type} candidates for {day_key}"
                )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to generate {meal_type} candidates for {day_key}: {e}"
                )

    async def _get_additional_tourist_spots_for_areas(
        self,
        target_districts: Set[str],
        target_areas: Set[str],
        assigned_tourist_spots: Set[str]
    ) -> List[TouristSpot]:
        """Get additional tourist spots for specific districts and areas.
        
        Args:
            target_districts: Set of target districts
            target_areas: Set of target areas
            assigned_tourist_spots: Set of already assigned spot IDs
            
        Returns:
            List of additional tourist spots
        """
        try:
            # Use a generic query to get more tourist spots
            # This could be enhanced to query by specific districts/areas
            additional_spots = await self.nova_client.query_tourist_spots_by_location(
                districts=list(target_districts),
                areas=list(target_areas)
            )
            
            # Filter out assigned spots
            available_spots = [
                spot for spot in additional_spots
                if spot.id not in assigned_tourist_spots
            ]
            
            return available_spots
            
        except Exception as e:
            self.logger.warning(f"Failed to get additional tourist spots: {e}")
            return []

    async def _handle_validation_failures(
        self,
        main_itinerary: MainItinerary,
        validation_report: ValidationReport
    ) -> None:
        """Handle validation failures and attempt corrections.
        
        Implements requirements 4.9, 4.10:
        - Handles validation failure scenarios
        - Attempts automatic corrections where possible
        - Logs detailed error information
        
        Args:
            main_itinerary: Main itinerary with validation issues
            validation_report: Validation report with identified issues
        """
        self.logger.warning(
            f"Handling {validation_report.error_count} validation errors and "
            f"{validation_report.warning_count} warnings"
        )
        
        # Log all validation issues for debugging
        for issue in validation_report.issues:
            if issue.severity.value == 'error':
                self.logger.error(
                    f"Validation error in {issue.location}: {issue.message}"
                )
            elif issue.severity.value == 'warning':
                self.logger.warning(
                    f"Validation warning in {issue.location}: {issue.message}"
                )
        
        # Attempt automatic corrections for specific error types
        corrections_attempted = 0
        
        for issue in validation_report.issues:
            if issue.severity.value == 'error':
                try:
                    if issue.category.value == 'operating_hours':
                        # Attempt to fix operating hours issues
                        if await self._attempt_operating_hours_correction(main_itinerary, issue):
                            corrections_attempted += 1
                    
                    elif issue.category.value == 'uniqueness':
                        # Attempt to fix uniqueness violations
                        if await self._attempt_uniqueness_correction(main_itinerary, issue):
                            corrections_attempted += 1
                    
                    elif issue.category.value == 'data_integrity':
                        # Attempt to fix data integrity issues
                        if await self._attempt_data_integrity_correction(main_itinerary, issue):
                            corrections_attempted += 1
                            
                except Exception as e:
                    self.logger.error(f"Failed to correct validation issue: {e}")
        
        self.logger.info(f"Attempted {corrections_attempted} automatic corrections")

    async def _attempt_operating_hours_correction(
        self,
        main_itinerary: MainItinerary,
        issue
    ) -> bool:
        """Attempt to correct operating hours validation issues.
        
        Args:
            main_itinerary: Main itinerary to correct
            issue: Validation issue to address
            
        Returns:
            True if correction was attempted, False otherwise
        """
        # This is a placeholder for operating hours correction logic
        # In a full implementation, this would attempt to replace the problematic
        # tourist spot with one that has appropriate operating hours
        
        self.logger.debug(f"Attempting operating hours correction for: {issue.location}")
        
        # For now, just log the attempt
        return False

    async def _attempt_uniqueness_correction(
        self,
        main_itinerary: MainItinerary,
        issue
    ) -> bool:
        """Attempt to correct uniqueness validation issues.
        
        Args:
            main_itinerary: Main itinerary to correct
            issue: Validation issue to address
            
        Returns:
            True if correction was attempted, False otherwise
        """
        # This is a placeholder for uniqueness correction logic
        # In a full implementation, this would attempt to replace duplicate
        # assignments with alternative options
        
        self.logger.debug(f"Attempting uniqueness correction for: {issue.location}")
        
        # For now, just log the attempt
        return False

    async def _attempt_data_integrity_correction(
        self,
        main_itinerary: MainItinerary,
        issue
    ) -> bool:
        """Attempt to correct data integrity validation issues.
        
        Args:
            main_itinerary: Main itinerary to correct
            issue: Validation issue to address
            
        Returns:
            True if correction was attempted, False otherwise
        """
        # This is a placeholder for data integrity correction logic
        # In a full implementation, this would attempt to fix missing or
        # invalid data fields
        
        self.logger.debug(f"Attempting data integrity correction for: {issue.location}")
        
        # For now, just log the attempt
        return False

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get current generation statistics.
        
        Returns:
            Dictionary with generation statistics
        """
        return {
            'total_generations': self.total_generations,
            'successful_generations': self.successful_generations,
            'failed_generations': self.failed_generations,
            'success_rate': self.successful_generations / self.total_generations if self.total_generations > 0 else 0,
            'current_timestamp': datetime.now().isoformat()
        }
    
    async def _get_fallback_tourist_spots(self, context: ItineraryGenerationContext) -> List:
        """Get fallback tourist spots when knowledge base fails.
        
        Args:
            context: Generation context
            
        Returns:
            List of fallback query results
        """
        try:
            # Log fallback activation
            await self.error_monitor.log_error(
                service_name="knowledge_base",
                operation_name="get_mbti_tourist_spots",
                error=Exception("Knowledge base fallback activated"),
                context={"mbti_personality": context.mbti_personality}
            )
            
            # Try to get generic tourist spots without MBTI matching
            fallback_spots = await self.nova_client.query_tourist_spots_by_location(
                districts=["Central district", "Admiralty", "Causeway Bay"],
                max_results=20
            )
            
            # Convert to query result format
            from .nova_pro_knowledge_base_client import QueryResult, QueryStrategy
            
            fallback_results = []
            for spot in fallback_spots:
                # Mark as non-MBTI match since these are fallback
                spot.mbti_match = False
                
                result = QueryResult(
                    tourist_spot=spot,
                    relevance_score=0.5,  # Lower score for fallback
                    s3_uri="fallback://tourist_spot",
                    query_used="FALLBACK: Generic tourist spots",
                    strategy=QueryStrategy.LOCATION_FOCUSED
                )
                fallback_results.append(result)
            
            self.logger.info(
                f"Fallback tourist spots retrieved: {len(fallback_results)} spots"
            )
            
            return fallback_results
            
        except Exception as e:
            self.logger.error(f"Fallback tourist spots failed: {e}")
            return []
    
    async def _assign_fallback_restaurants(self, main_itinerary: MainItinerary) -> None:
        """Assign fallback restaurants when MCP services fail.
        
        Args:
            main_itinerary: Main itinerary to assign fallback restaurants to
        """
        try:
            # Log fallback activation
            await self.error_monitor.log_error(
                service_name="restaurant_assignment",
                operation_name="assign_restaurants",
                error=Exception("Restaurant assignment fallback activated"),
                context={"itinerary_id": main_itinerary.generation_id}
            )
            
            # Create placeholder restaurants for each meal
            days = [
                (main_itinerary.day_1, "day_1"),
                (main_itinerary.day_2, "day_2"),
                (main_itinerary.day_3, "day_3")
            ]
            
            for day_itinerary, day_name in days:
                # Create fallback restaurants
                fallback_breakfast = Restaurant(
                    id=f"fallback_breakfast_{day_name}",
                    name=f"Local Breakfast Spot - {day_name.replace('_', ' ').title()}",
                    address="To be determined",
                    district="Central district",
                    operating_hours="06:00-11:00",
                    meal_types=["breakfast"],
                    cuisine_type="Local",
                    description="Fallback breakfast option - please verify availability"
                )
                
                fallback_lunch = Restaurant(
                    id=f"fallback_lunch_{day_name}",
                    name=f"Local Lunch Restaurant - {day_name.replace('_', ' ').title()}",
                    address="To be determined",
                    district="Central district",
                    operating_hours="11:30-17:00",
                    meal_types=["lunch"],
                    cuisine_type="Local",
                    description="Fallback lunch option - please verify availability"
                )
                
                fallback_dinner = Restaurant(
                    id=f"fallback_dinner_{day_name}",
                    name=f"Local Dinner Restaurant - {day_name.replace('_', ' ').title()}",
                    address="To be determined",
                    district="Central district",
                    operating_hours="17:30-22:00",
                    meal_types=["dinner"],
                    cuisine_type="Local",
                    description="Fallback dinner option - please verify availability"
                )
                
                # Assign fallback restaurants
                day_itinerary.breakfast = MealAssignment(
                    meal_type="breakfast",
                    restaurant=fallback_breakfast,
                    scheduled_time="08:00",
                    notes="Fallback assignment - please verify restaurant availability"
                )
                
                day_itinerary.lunch = MealAssignment(
                    meal_type="lunch",
                    restaurant=fallback_lunch,
                    scheduled_time="12:30",
                    notes="Fallback assignment - please verify restaurant availability"
                )
                
                day_itinerary.dinner = MealAssignment(
                    meal_type="dinner",
                    restaurant=fallback_dinner,
                    scheduled_time="19:00",
                    notes="Fallback assignment - please verify restaurant availability"
                )
            
            self.logger.info("Fallback restaurants assigned to all days")
            
        except Exception as e:
            self.logger.error(f"Fallback restaurant assignment failed: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information.
        
        Returns:
            Dictionary with system health data
        """
        return {
            'itinerary_generator': {
                'total_generations': self.total_generations,
                'successful_generations': self.successful_generations,
                'failed_generations': self.failed_generations,
                'success_rate': self.successful_generations / self.total_generations if self.total_generations > 0 else 0
            },
            'resilience_service': self.resilience_service.get_system_health(),
            'error_monitor': self.error_monitor.get_error_summary(),
            'knowledge_base_client': self.nova_client.get_error_metrics(),
            'timestamp': datetime.now().isoformat()
        }